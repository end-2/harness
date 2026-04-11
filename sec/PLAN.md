# sec (Security Skill) 구현 계획

> **표준 적합성 노트**: 본 스킬은 Claude Code Skill 표준 포맷을 준수합니다. 스킬 이름은 `sec`(lowercase)로 통일하며, 디렉토리도 `sec/`를 사용합니다. 단일 진입점 `sec/SKILL.md`(YAML frontmatter 포함)을 가지며, 상세 참조 자료는 `references/`로 분리하여 SKILL.md를 500행 이내로 유지합니다. 4-에이전트 파이프라인은 **옵션 A**(단일 SKILL.md가 4단계 instruction을 안내하고, audit 단계에서만 `context: fork` sub-agent로 코드 감사 격리)를 채택합니다. 메타데이터/승인 상태를 변경하는 쓰기 경로는 `sec-record`라는 별도 스킬(`disable-model-invocation: true`)로 분리하여, 읽기 전용 분석 스킬 `sec`와 권한을 명확히 분리합니다.

## 개요

Arch 스킬의 산출물(아키텍처 결정, 컴포넌트 구조, 기술 스택, 다이어그램)과 Impl 스킬의 산출물(구현 맵, 코드 구조, 구현 결정, 구현 가이드)을 입력으로 받아, **보안 취약점 분석, 위협 모델링, 보안 코드 리뷰, 표준 준수 검증**을 수행하는 스킬입니다.

Impl이 "설계를 코드로 어떻게 구현할 것인가"를 실행하고, QA가 "기능적으로 올바른가"를 검증했다면, Security는 "그 설계와 구현이 **보안적으로 안전한가**"를 검증합니다. 이 과정에서 **Arch의 컴포넌트 구조를 신뢰 경계와 공격 표면의 근거로, Impl의 구현 맵을 코드 레벨 취약점 탐지의 근거로** 사용하며, 모든 보안 산출물은 원천 아키텍처 결정과 요구사항까지 역추적 가능합니다.

위협 모델링은 아키텍처 레벨의 도메인 지식이 필요하므로 **대화형 모델**을 채택하고, 코드 레벨 감사와 컴플라이언스 검증은 선행 산출물에서 기계적으로 도출 가능하므로 **자동 실행 + 예외 에스컬레이션** 모델을 채택합니다.

## Claude Code Skill 표준 포맷 적합성

### SKILL.md 단일 진입점과 frontmatter

표준에 따라 스킬은 `sec/SKILL.md` 하나의 진입점을 가지며, 파일 최상단에 YAML frontmatter를 둡니다. 4개의 별도 `agents/*.md`를 가정하던 기존 설계는 폐기하고, 단일 SKILL.md 안에서 4단계(threat-model → audit → review → compliance) instruction을 순차적으로 기술합니다.

`sec/SKILL.md` frontmatter 초안 (옵션 A: 읽기 전용 분석 스킬):

```yaml
---
name: sec
description: Audits Arch/Impl outputs for security threats, vulnerabilities, and standards compliance. Use when the user has completed architecture/implementation outputs and needs STRIDE threat modeling, CWE/CVSS vulnerability scanning, or OWASP ASVS/PCI DSS/GDPR/HIPAA compliance verification.
allowed-tools: Read Grep Glob
disable-model-invocation: true
user-invocable: true
argument-hint: "[--mode lightweight|heavy] [--standard owasp-asvs-l2|pci-dss|gdpr|hipaa]"
model: claude-opus-4-6
effort: high
---
```

`description`은 250자 이내에서 "무엇(what) + 언제(when)"을 front-load합니다. `name`은 lowercase/digits/hyphens 규칙을 따라 `sec`로 고정하고 디렉토리도 `sec/`와 일치시킵니다.

### 도구 권한 모델 (`allowed-tools`)

보안 스킬은 본질적으로 **읽기 위주(read-only)** 작업이므로 도구 권한을 최소 범위로 고정합니다.

| 스킬 | 역할 | `allowed-tools` |
|------|------|----------------|
| `sec` (메인, 읽기 전용) | 위협 모델링 · 감사 · 리뷰 · 컴플라이언스 분석 | `Read Grep Glob` |
| `sec` 내부 audit sub-agent (`context: fork`) | 격리된 컨텍스트에서 대규모 코드 정적 분석 | `Read Grep Glob` |
| `sec-record` (별도 쓰기 전용 스킬) | 메타데이터/승인 상태 기록 | `Read Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/artifact.py:*) Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/approval.py:*) Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/validate.py:*) Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/report.py:*)` |

- 메인 `sec`는 어떠한 `Bash`·`Edit`·`Write`도 허용하지 않습니다. 모든 문자열은 Read/Grep/Glob만으로 수집합니다.
- 메타데이터 쓰기 및 감사 증적 기록이 필요한 민감 액션은 `sec-record`라는 별도 스킬로 분리하며, `disable-model-invocation: true`로 모델 자율 호출을 차단하고 **사용자가 명시적으로 호출**해야만 실행되도록 합니다.
- `sec-record`의 `Bash`는 일반 셸이 아닌 명시적 prefix 화이트리스트(`Bash(python3 .../approval.py:*)` 등)만 허용하여, 임의 명령 실행 경로를 차단합니다.

### `disable-model-invocation` 적용

- 메인 `sec`: `disable-model-invocation: true` — 규제 의사결정(리스크 수용, 컴플라이언스 판정)을 다루므로 모델이 자율적으로 체인 내부에서 임의 호출하는 것을 차단합니다. 사용자가 명시적으로 `sec`를 호출해야만 실행됩니다.
- `sec-record`: `disable-model-invocation: true` — `approval.py accept-risk` 같은 감사 증적 변경은 반드시 사용자 의사에 따라 명시적으로만 실행되어야 합니다.

### 4-에이전트 파이프라인의 표준 매핑 결정 — 옵션 A

표준 매핑 옵션 A/B/C 중 **옵션 A**를 채택합니다.

- **옵션 A (채택)**: 단일 `sec/SKILL.md`가 4단계(threat-model → audit → review → compliance)를 순차 instruction으로 안내합니다. 대용량 코드 정적 분석이 필요한 **audit 단계에서만 `context: fork` sub-agent**를 띄워 코드 감사를 메인 컨텍스트에서 격리합니다. 이렇게 하면 메인 컨텍스트는 위협 모델과 컴플라이언스 의사결정에 집중할 수 있고, 대용량 감사 컨텍스트가 메인을 오염시키지 않습니다.
- 옵션 B(4개 별개 스킬)와 옵션 C(모든 단계 분리)는 권한 분리가 더 깨끗하지만 워크플로 결합도가 낮아지고 추적성 체인의 재구성이 복잡해지므로 채택하지 않습니다.

### 동적 컨텍스트 주입과 문자열 치환

- SKILL.md 상단에서 ``!`python3 ${CLAUDE_SKILL_DIR}/scripts/report.py summary` ``를 사용해 현재 4섹션 메타데이터 요약을 동적으로 주입합니다. 에이전트가 매 턴 `report.py`를 호출할 필요 없이 현재 상태를 바로 인지할 수 있습니다. (단, `sec`는 `Bash`를 허용하지 않으므로 이 동적 주입은 SKILL 파서 단의 기능이며, 에이전트 도구 권한과 구분됩니다.)
- `$ARGUMENTS`는 `--mode lightweight|heavy`, `--standard owasp-asvs-l2|pci-dss|gdpr|hipaa` 같은 인자를 받는 데 사용합니다. 예: `$ARGUMENTS[0]`에서 모드 추출.
- `${CLAUDE_SKILL_DIR}`는 `templates/`, `references/`, `scripts/`를 참조할 때 항상 사용하여 위치 독립성을 보장합니다.
- `${CLAUDE_SESSION_ID}`는 감사 증적 기록 시 세션 식별자로 `approval.py`에 전달합니다.

### 에스컬레이션의 표준 매핑

`threat-model`/`audit`/`review`/`compliance` 단계의 에스컬레이션은 다음과 같이 표준 메커니즘에 매핑합니다.

- 사용자 확인이 필요한 경우(critical 취약점 발견, 규제 미준수 판정): 메인 에이전트가 사용자에게 직접 질문하여 답변을 받습니다. 모델 단독 결정은 금지됩니다.
- 리스크 수용(`mitigation_status: accepted`), 승인/반려, 감사 증적 기록 같은 민감 액션: 사용자 답변을 받은 뒤 **별도 스킬 `sec-record`**로 위임합니다. `sec-record`는 `disable-model-invocation: true`이므로 사용자가 명시적으로 호출한 경우에만 실행됩니다.
- critical 취약점 발견 시 메인 `sec`는 즉시 분석을 중단하고 사용자에게 결정을 요청하며, 사용자가 `sec-record`를 호출하기 전까지는 메타데이터에 어떠한 변경도 가해지지 않습니다.

### 문서 분할 — SKILL.md 500행 이내 유지

표준은 SKILL.md를 500행 이내로 유지하고 상세를 supporting files(`references/`, `scripts/`, `templates/`, `assets/`)로 분리할 것을 요구합니다. 본 PLAN의 상세 표와 카탈로그는 구현 시 다음과 같이 `references/`로 이동합니다.

| 현재 PLAN 섹션 | 이동 대상 파일 |
|---------------|---------------|
| "전통적 보안 vs AI 컨텍스트 보안" 비교 표 | `references/traditional-vs-ai-security.md` |
| "Arch 출력 → Security 소비 매핑" / "Impl 출력 → Security 소비 매핑" / "RE 간접 참조" 표 | `references/input-mapping.md` |
| 4섹션(위협 모델/취약점 보고서/보안 권고/컴플라이언스 리포트) 필드 정의 | `references/output-schema.md` |
| OWASP Top 10 매핑 | `references/owasp-top-10-2021.md` |
| STRIDE/DREAD 가이드 | `references/stride-dread-guide.md` |
| CWE 카탈로그 | `references/cwe-catalog.md` |
| CVSS v3.1 채점 가이드 | `references/cvss-v3.1-scoring.md` |
| OWASP ASVS L1/L2/L3 / PCI DSS / GDPR / HIPAA 항목 | `references/standards/` |
| 에스컬레이션 프로토콜 | `references/escalation-protocol.md` |

SKILL.md 본문에는 ① frontmatter, ② 4단계 실행 순서와 진입점 안내, ③ 사용자 확인 지점, ④ 스크립트/스킬 호출 계약, ⑤ `references/` 참조 링크만 남깁니다.

---

### 전통적 보안 vs AI 컨텍스트 보안

> 구현 시 아래 표는 `references/traditional-vs-ai-security.md`로 이동합니다. PLAN 문서에는 맥락 파악용으로만 보존합니다.

| 구분 | 전통적 보안 | AI 컨텍스트 보안 |
|------|------------|-----------------|
| 수행자 | 전담 보안 팀 (보안 엔지니어, 펜테스터) | 개발자가 AI에게 보안 분석과 검증을 위임 |
| 입력 | 설계 문서, 코드, 인터뷰, 침투 테스트 | **Arch/Impl 스킬의 구조화된 산출물** (추적성 내장) |
| 위협 모델링 | 화이트보드 세션, 수작업 DFD | **Arch 컴포넌트 구조 → 신뢰 경계/데이터 흐름 자동 도출** + 도메인 맥락 대화 |
| 취약점 탐지 | SAST/DAST 도구 + 수동 리뷰 | **Impl 코드 구조 기반 체계적 정적 분석** + CWE 분류 자동화 |
| 보안 리뷰 | 리뷰어 경험에 의존, 체크리스트 편차 큼 | **Arch 결정 + 위협 모델 기반 체계적 리뷰** — 무엇을 검증할지 자동 도출 |
| 컴플라이언스 | 감사 시점에 수동 체크리스트 점검 | **코드 + 설정 + 위협 분석 결과를 표준 항목에 자동 매핑** |
| 추적성 | 취약점 리포트와 설계/요구사항 간 수동 연결 | **re_refs/arch_refs/impl_refs로 자동 추적** |
| 산출물 | PDF 보안 리포트 | **후속 스킬이 소비 가능한 구조화된 보안 산출물** |

## 선행 스킬 산출물 소비 계약

Security 스킬은 Arch, Impl 두 스킬의 산출물을 직접 소비하고, RE는 Arch 산출물의 참조(`re_refs`, `constraint_ref`)를 통해 간접 소비합니다.

### Arch 출력 → Security 소비 매핑

| Arch 산출물 섹션 | 주요 필드 | Security에서의 소비 방법 |
|-----------------|-----------|------------------------|
| **아키텍처 결정** | `id`, `decision`, `trade_offs`, `re_refs` | `decision`에서 보안 함의 도출 (예: 마이크로서비스 → 서비스 간 인증 필요, 이벤트 드리븐 → 메시지 무결성 검증 필요). `trade_offs`에서 보안이 희생된 결정 식별. `re_refs`로 RE까지 추적성 유지 |
| **컴포넌트 구조** | `id`, `name`, `type`, `interfaces`, `dependencies` | `type`으로 신뢰 경계 식별 (`gateway` = 외부 경계, `service` = 내부 경계, `store` = 데이터 경계). `interfaces`로 공격 표면(attack surface) 도출. `dependencies`로 데이터 흐름 경로 및 권한 전파 경로 매핑 |
| **기술 스택** | `category`, `choice`, `constraint_ref` | `choice`로 기술별 알려진 취약점 패턴 매핑 (예: Express → prototype pollution, Django → CSRF 토큰 검증). `constraint_ref`로 RE 규제 제약(GDPR, HIPAA 등) 확인하여 컴플라이언스 검증 대상 결정 |
| **다이어그램** | `type`, `code` | `c4-container`로 시스템 경계와 외부 액터 식별 → 위협 모델 DFD 기초. `data-flow`로 민감 데이터 흐름 경로 추적. `sequence`로 인증/인가 흐름의 보안 검증 지점 도출 |

### Impl 출력 → Security 소비 매핑

| Impl 산출물 섹션 | 주요 필드 | Security에서의 소비 방법 |
|-----------------|-----------|------------------------|
| **구현 맵** | `id`, `component_ref`, `module_path`, `interfaces_implemented`, `re_refs` | `module_path`로 보안 감사 대상 파일 범위 결정. `interfaces_implemented`로 API 엔드포인트별 보안 검증 대상 식별. `component_ref`로 Arch 컴포넌트 보안 요구사항과 매핑 |
| **코드 구조** | `directory_layout`, `module_dependencies`, `external_dependencies`, `environment_config` | `external_dependencies`로 알려진 CVE 취약점 스캔 대상 식별. `environment_config`로 시크릿/크리덴셜 관리 상태 점검. `module_dependencies`로 권한 경계 위반 여부 확인 (예: 데이터 접근 모듈이 프레젠테이션 레이어에서 직접 참조) |
| **구현 결정** | `id`, `decision`, `pattern_applied`, `arch_refs`, `re_refs` | `pattern_applied`로 패턴별 보안 검증 포인트 결정 (예: Repository 패턴 → SQL 인젝션 방어 확인, Strategy 패턴 → 전략 교체 시 권한 검증). `decision`에서 보안 관련 구현 결정의 적절성 검토 |
| **구현 가이드** | `setup_steps`, `build_commands`, `environment_config`, `conventions` | `environment_config`로 시크릿 관리 방식 검증 (하드코딩, 환경 변수, 시크릿 매니저). `build_commands`로 빌드 파이프라인 보안 검증 지점 식별 |

### RE 산출물 간접 참조

Security는 RE 산출물을 직접 소비하지 않으나, Arch 산출물의 `re_refs`와 `constraint_ref`를 통해 간접 참조합니다.

| RE 산출물 | 간접 참조 경로 | Security에서의 영향 |
|-----------|---------------|-------------------|
| **요구사항 명세** | Arch `component_structure.re_refs` → `FR-xxx`, `NFR-xxx` | NFR 중 보안 관련 요구사항(`NFR-security`)의 구현 충족 여부 검증 |
| **제약 조건** | Arch `technology_stack.constraint_ref` → `CON-xxx` | `type: regulatory` 제약(GDPR, HIPAA, PCI DSS 등)을 컴플라이언스 검증 대상 표준으로 사용. `hard` 제약은 비협상 보안 요구사항으로 고정 |
| **품질 속성 우선순위** | Arch `architecture_decisions.re_refs` → `QA:security` | `priority`로 보안의 전체 우선순위 파악. `metric`(예: "모든 API 인증 필수", "민감 데이터 AES-256 암호화")을 보안 검증 기준으로 사용. `trade_off_notes`로 보안이 다른 속성과 트레이드오프된 지점 식별 |

### 추적성 체인 (Traceability Chain)

Security는 RE → Arch → Impl → Security로 이어지는 추적성 체인에서 **보안 관점의 검증 지점**입니다.

```
RE:spec 산출물                Arch 산출물              Impl 산출물              Security 산출물
┌──────────────┐        ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ NFR-security │──re──  │ AD-001       │──arch──│ IDR-001      │──impl──│ TM-001       │
│  metric:     │  refs  │  decision:   │  _refs │  pattern:    │  _refs │  threats     │
│  "인증 필수"  │        │  "JWT 기반"  │        │  "미들웨어"   │        │  mitigations │
│              │        │              │        │              │        │              │
│ CON-001      │──re──  │ COMP-001     │──comp──│ IM-001       │──impl──│ VA-001       │
│  type:       │  refs  │  type:       │  _ref  │  module_path │  _refs │  cwe_id      │
│  regulatory  │        │  gateway     │        │  interfaces  │        │  severity    │
│  (GDPR)      │        │  interfaces  │        │              │        │  remediation │
│              │        │              │        │              │        │              │
│ QA:security  │──re──  │ Tech Stack   │        │ ext_deps     │        │ CR-001       │
│  priority: 2 │  refs  │  constraint  │        │  (CVE 스캔)  │        │  standard    │
│              │        │  _ref        │        │              │        │  status      │
└──────────────┘        └──────────────┘        └──────────────┘        └──────────────┘
```

### 적응적 깊이 연동

Arch/Impl 모드에 연동하여 Security의 산출물 수준을 자동 조절합니다.

| Arch/Impl 모드 | 판별 기준 | Security 모드 | 산출물 수준 |
|---------------|-----------|--------------|------------|
| 경량 | Arch 컴포넌트 ≤ 3개, 단일 서비스, 외부 인터페이스 ≤ 2개 | 경량 | OWASP Top 10 체크리스트 기반 감사 + 핵심 위협 요약 (STRIDE 경량 적용) + 의존성 CVE 스캔 + 인라인 보안 가이드 |
| 중량 | Arch 컴포넌트 > 3개 또는 서비스 간 통신 존재 또는 외부 인터페이스 > 2개 | 중량 | 전체 STRIDE 위협 모델링 + DREAD 우선순위 + 컴포넌트별 정적 분석 + CWE 분류 취약점 리포트 + CVSS 심각도 평가 + OWASP ASVS 레벨별 컴플라이언스 리포트 + 보안 아키텍처 권고 |

## 최종 산출물 구조

Security 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. 설계/구현의 보안 검증까지를 범위로 하며, 침투 테스트(DAST)나 런타임 보안 모니터링은 후속 스킬(`devops`)의 영역입니다.

### 1. 위협 모델 (Threat Model)

아키텍처 레벨의 위협 분석과 대응 전략을 구조화합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `TM-001`) |
| `title` | 위협 제목 |
| `stride_category` | STRIDE 분류 (`spoofing` / `tampering` / `repudiation` / `information_disclosure` / `denial_of_service` / `elevation_of_privilege`) |
| `description` | 위협 상세 설명 |
| `attack_vector` | 공격 벡터 (진입점, 경로, 전제 조건) |
| `affected_components` | 영향받는 Arch 컴포넌트 ID 목록 (`COMP-xxx`) |
| `trust_boundary` | 관련 신뢰 경계 (어떤 경계를 넘는 위협인지) |
| `dread_score` | DREAD 점수 (Damage, Reproducibility, Exploitability, Affected Users, Discoverability — 각 1-10) |
| `risk_level` | 위험 수준 (`critical` / `high` / `medium` / `low`) — DREAD 총점 기반 |
| `mitigation` | 대응 전략 (설계 변경, 보안 통제 추가, 리스크 수용 등) |
| `mitigation_status` | 대응 상태 (`mitigated` / `partial` / `accepted` / `unmitigated`) |
| `arch_refs` | 근거가 된 Arch 산출물 ID (`AD-xxx`, `COMP-xxx` 등) |
| `re_refs` | 근거가 된 RE 산출물 ID (`NFR-xxx`, `CON-xxx` 등) |

#### 위협 모델 보조 산출물

| 필드 | 설명 |
|------|------|
| `trust_boundaries` | 신뢰 경계 정의 목록 — 각 항목: `id`, `name`, `description`, `components_inside`, `components_outside` |
| `data_flow_security` | 보안 관점 데이터 흐름 — 각 항목: `id`, `source`, `destination`, `data_classification`(`public`/`internal`/`confidential`/`restricted`), `protection_required`(암호화, 무결성, 접근 제어) |
| `attack_tree` | 주요 위협별 공격 트리 (Mermaid 코드) |

### 2. 취약점 보고서 (Vulnerability Report)

코드 레벨 보안 취약점과 감사 결과를 구조화합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `VA-001`) |
| `title` | 취약점 제목 |
| `cwe_id` | CWE (Common Weakness Enumeration) ID (예: `CWE-89`) |
| `owasp_category` | OWASP Top 10 분류 (예: `A03:2021-Injection`) |
| `severity` | CVSS v3.1 심각도 (`critical` / `high` / `medium` / `low` / `informational`) |
| `cvss_score` | CVSS v3.1 기본 점수 (0.0 - 10.0) |
| `cvss_vector` | CVSS v3.1 벡터 문자열 |
| `location` | 취약점 위치 (파일 경로, 라인 번호, 함수/메서드 이름) |
| `description` | 취약점 상세 설명 |
| `proof_of_concept` | 취약점 재현 시나리오 (공격 벡터, 페이로드 예시) |
| `remediation` | 수정 제안 (코드 변경 사항, 적용할 보안 통제) |
| `remediation_effort` | 수정 난이도 (`trivial` / `moderate` / `significant`) |
| `dependency_vuln` | 의존성 취약점인 경우 — `package`, `version`, `cve_id`, `fixed_version` |
| `impl_refs` | 관련 Impl 산출물 ID (`IM-xxx`, `IDR-xxx` 등) |
| `arch_refs` | 관련 Arch 산출물 ID (`COMP-xxx`, `AD-xxx` 등) |
| `re_refs` | 관련 RE 산출물 ID (`NFR-xxx`, `CON-xxx` 등) |
| `threat_refs` | 관련 위협 모델 ID (`TM-xxx` 등) |

### 3. 보안 권고 (Security Recommendations)

발견된 위협과 취약점에 대한 우선순위화된 조치 가이드를 구조화합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `SR-001`) |
| `title` | 권고 제목 |
| `category` | 권고 유형 (`architecture` / `code` / `configuration` / `dependency` / `process`) |
| `priority` | 조치 우선순위 (1이 가장 높음) — 위험 수준, 수정 난이도, 영향 범위 종합 |
| `description` | 권고 상세 설명 |
| `current_state` | 현재 상태 (어떤 문제가 있는지) |
| `recommended_action` | 권장 조치 (구체적 코드 변경, 설정 변경, 아키텍처 변경) |
| `alternative_actions` | 대안 목록 및 각 대안의 트레이드오프 |
| `affected_components` | 영향받는 컴포넌트 ID 목록 |
| `threat_refs` | 관련 위협 ID (`TM-xxx`) |
| `vuln_refs` | 관련 취약점 ID (`VA-xxx`) |
| `arch_refs` | 관련 Arch 산출물 ID |
| `re_refs` | 관련 RE 산출물 ID |

### 4. 컴플라이언스 리포트 (Compliance Report)

보안 표준별 준수 상태를 구조화합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `CR-001`) |
| `standard` | 적용 표준 (`OWASP-ASVS-L1` / `OWASP-ASVS-L2` / `OWASP-ASVS-L3` / `PCI-DSS` / `GDPR` / `HIPAA`) |
| `version` | 표준 버전 |
| `scope` | 검증 범위 (전체 시스템 / 특정 컴포넌트) |
| `overall_status` | 전체 판정 (`compliant` / `partial` / `non_compliant`) |
| `total_requirements` | 표준의 전체 요구사항 수 |
| `compliant_count` | 준수 항목 수 |
| `non_compliant_count` | 미준수 항목 수 |
| `not_applicable_count` | 해당 없음 항목 수 |
| `findings` | 항목별 검증 결과 — 각 항목: `requirement_id`(표준 항목 ID), `title`, `status`(`compliant`/`non_compliant`/`partial`/`not_applicable`), `evidence`(준수 근거 또는 미준수 사유), `gap_description`(미준수 시 갭 설명), `remediation`(개선 방안) |
| `gap_summary` | 갭 요약 — 미준수 항목을 심각도별로 그룹화 |
| `remediation_roadmap` | 개선 로드맵 — 우선순위별 개선 항목, 예상 노력 |
| `constraint_refs` | 근거가 된 RE 제약 조건 ID (`CON-xxx` 등) |
| `threat_refs` | 관련 위협 모델 ID (`TM-xxx`) |
| `vuln_refs` | 관련 취약점 ID (`VA-xxx`) |

### 후속 스킬 연계

```
security 산출물 구조:
┌─────────────────────────────────────────┐
│  위협 모델 (Threat Model)               │──→ devops:strategy (보안 관점 배포 제약)
│  - TM-001: STRIDE 위협 목록             │──→ devops:monitor (보안 모니터링 지표)
│  - 신뢰 경계, 데이터 흐름 분류           │──→ qa:strategy (보안 테스트 시나리오 도출)
├─────────────────────────────────────────┤
│  취약점 보고서 (Vulnerability Report)   │──→ impl:refactor (취약점 코드 수정 대상)
│  - VA-001: CWE-89, CVSS 9.8            │──→ devops:pipeline (보안 스캔 게이트)
│  - 의존성 CVE, 코드 취약점              │──→ qa:generate (보안 회귀 테스트 대상)
├─────────────────────────────────────────┤
│  보안 권고 (Security Recommendations)   │──→ arch:review (아키텍처 레벨 보안 개선)
│  - SR-001: 아키텍처/코드/설정 권고       │──→ impl:refactor (코드 레벨 보안 개선)
│  - 우선순위별 조치 가이드                │──→ devops:iac (인프라 보안 설정)
├─────────────────────────────────────────┤
│  컴플라이언스 리포트 (Compliance Report)│──→ devops:log (로깅 컴플라이언스 요구)
│  - CR-001: OWASP ASVS L2 partial       │──→ devops:pipeline (컴플라이언스 게이트)
│  - 표준별 준수/미준수, 갭 분석           │
└─────────────────────────────────────────┘
```

### 산출물 파일 형식: 메타데이터 / 문서 분리

Security의 4섹션 산출물은 각각 **메타데이터 파일과 문서 markdown 파일의 쌍**으로 관리합니다. 하나의 파일에 구조화된 필드와 서술형 설명을 혼재시키지 않고, 기계가 다루기 좋은 상태/추적성 정보와 사람이 읽는 분석 서술을 분리합니다.

| 파일 | 형식 | 책임 |
|------|------|------|
| **메타데이터 파일** | YAML (`*.meta.yaml`) | `id`, `phase`, `progress`, `approval`, `*_refs` 등 구조화 필드. 스크립트로만 갱신 |
| **문서 파일** | Markdown (`*.md`) | 위협 설명, 공격 시나리오, 수정 제안, 갭 서술 등 사람이 읽는 분석 본문. 에이전트가 직접 편집 |

YAML을 채택하는 이유는 ① 주석 지원으로 감사자가 필드 의도를 바로 이해할 수 있고, ② 사람이 읽기 쉬워 감사 검토 단계에서 별도 렌더러 없이 그대로 검토 가능하며, ③ 스크립트 파싱이 용이하고, ④ 블록 스칼라로 긴 `evidence`/`remediation` 스니펫을 자연스럽게 표현할 수 있기 때문입니다. JSON은 주석 부재와 가독성 문제로 보안 감사 산출물에는 부적합합니다.

특히 **컴플라이언스 리포트**는 본질적으로 표준 항목 ID 기준의 구조화된 체크리스트(`requirement_id` × `status` × `evidence`)이므로 YAML 친화성이 매우 높아 메타데이터-주도 관리에 가장 적합합니다. 반대로 위협 모델의 공격 시나리오나 취약점의 재현 절차 같은 서술형 내용은 markdown 본문에 배치합니다.

### 메타데이터에 포함되는 필드

4섹션 공통으로 다음 필드를 포함하며, 섹션 고유 필드(예: 위협 모델의 `stride_category`, 취약점 보고서의 `cwe_id`/`cvss_score`)는 각 섹션의 표 정의를 그대로 따릅니다.

| 필드 그룹 | 필드 | 설명 |
|----------|------|------|
| **진행 상태** | `phase` | 현재 단계 (`draft` / `in_review` / `approved` / `rejected` / `archived`) |
|  | `progress` | 섹션 내 완료율 (0-100) 또는 체크리스트 기반 진행도 |
|  | `updated_at` | 마지막 상태 변경 시각 (스크립트가 자동 기록) |
| **승인 상태** | `approval.state` | 승인 상태 (`pending` / `approved` / `rejected` / `conditionally_approved`) |
|  | `approval.approver` | 승인자 식별자 (사용자/역할) |
|  | `approval.approved_at` | 승인 시각 (ISO-8601) |
|  | `approval.conditions` | 조건부 승인 시 조건 목록 |
|  | `approval.rationale` | 승인/반려 사유 |
| **추적성** | `arch_refs`, `impl_refs`, `re_refs` | upstream 참조 (RE/Arch/Impl 산출물 ID) |
|  | `threat_refs`, `vuln_refs` | 섹션 간 cross-refs |
|  | `downstream_consumers` | 이 산출물을 소비할 후속 스킬 식별자 |

**감사 추적성(Audit Trail) 강조**: 보안 산출물은 사후 감사·규제 증적 요구가 매우 강한 영역입니다. 메타데이터의 `approval.state` / `approval.approver` / `approval.approved_at` / `approval.rationale`는 단순한 워크플로 필드가 아니라, **누가 언제 어떤 근거로 위험을 수용(accept)하거나 대응 전략을 승인했는지에 대한 감사 증적**으로 활용됩니다. 특히 `mitigation_status: accepted`(리스크 수용), `hard` 규제 제약에 대한 `conditionally_approved`, critical 취약점에 대한 사용자 에스컬레이션 결과 등은 모두 이 필드에 기록되어, 추후 침해 사고 조사나 규제 감사 시 의사결정의 정합성을 입증하는 근거가 됩니다. 이 때문에 메타데이터는 자유 편집이 아닌 **스크립트 커맨드 경유의 단일 쓰기 경로**로만 변경됩니다.

### 메타데이터 조작 스크립트 (`scripts/`)

에이전트는 YAML/JSON을 직접 편집하지 않으며, 반드시 `scripts/` 디렉토리의 스크립트 커맨드를 통해서만 메타데이터 상태를 갱신합니다. 이는 ① 스키마 검증을 강제하고, ② 승인 이력의 원자성을 보장하며, ③ 감사 증적을 일관된 형식으로 기록하기 위함입니다.

| 스크립트 | 커맨드 예시 | 역할 |
|----------|------------|------|
| `scripts/artifact.py` | `artifact.py init --section threat_model --id TM-001` | 메타데이터 파일과 문서 markdown 파일 쌍을 템플릿에서 생성 |
|  | `artifact.py set-phase --id TM-001 --phase in_review` | 진행 상태 전이 (허용된 전이 규칙 검증 포함) |
|  | `artifact.py set-progress --id TM-001 --progress 60` | 진행률 갱신 |
|  | `artifact.py add-ref --id VA-003 --arch-ref COMP-002` | upstream 참조 추가 |
|  | `artifact.py show --id TM-001` | 메타데이터와 문서를 합쳐 조회 |
| `scripts/approval.py` | `approval.py request --id CR-001` | 승인 요청 상태로 전환 |
|  | `approval.py approve --id CR-001 --approver <user> --rationale ...` | 승인 처리 및 감사 증적 기록 |
|  | `approval.py reject --id CR-001 --approver <user> --rationale ...` | 반려 처리 |
|  | `approval.py accept-risk --id TM-005 --approver <user> --rationale ...` | 리스크 수용 기록 (감사 증적의 핵심 케이스) |
| `scripts/validate.py` | `validate.py --section vulnerability_report` | 메타데이터 스키마/참조 무결성 검증 |
| `scripts/report.py` | `report.py summary` | 4섹션 메타데이터를 종합하여 현재 상태/승인/갭 요약 출력 |

모든 쓰기 커맨드는 `updated_at`을 자동 갱신하고, 상태 전이가 스키마 규칙(예: `draft → in_review → approved`)을 위반하면 실패합니다. 에이전트 프롬프트는 "메타데이터 파일을 직접 수정하지 말 것. 반드시 `scripts/artifact.py` 또는 `scripts/approval.py`를 경유할 것"을 명시합니다.

### 문서 템플릿 (`templates/`)

문서 markdown 파일 또한 `templates/` 디렉토리에 **섹션별 템플릿**을 미리 두고, `scripts/artifact.py init`가 이 템플릿을 렌더링하여 섹션 헤더와 플레이스홀더가 채워진 기본 골격을 생성합니다. 에이전트는 이 골격 위에서 서술 내용을 채우기만 하면 되므로, 섹션 누락이나 포맷 불일치를 방지할 수 있습니다.

| 템플릿 | 생성되는 파일 | 주요 섹션 |
|--------|--------------|----------|
| `templates/threat-model.md.tpl` | `TM-xxx.md` | 위협 개요 · 공격 벡터 · 공격 트리(Mermaid) · 대응 전략 · 리스크 수용 근거 |
| `templates/vulnerability-report.md.tpl` | `VA-xxx.md` | 취약점 설명 · 위치 · 재현 절차(PoC) · 수정 제안 · 의존성 취약점 상세 |
| `templates/security-recommendation.md.tpl` | `SR-xxx.md` | 현재 상태 · 권장 조치 · 대안 · 트레이드오프 |
| `templates/compliance-report.md.tpl` | `CR-xxx.md` | 표준 개요 · 항목별 증적 · 갭 서술 · 개선 로드맵 |
| `templates/*.meta.yaml.tpl` | `*.meta.yaml` | 공통 메타데이터 필드의 초기 스켈레톤 (phase=`draft`, approval.state=`pending`) |

## 목표 구조

Claude Code Skill 표준 디렉토리 레이아웃을 따릅니다. 기존의 `skills.yaml` + `agents/*.md` 구조는 폐기되고 `SKILL.md`(frontmatter 포함) 단일 진입점으로 통합됩니다. 4단계 instruction은 SKILL.md 본문에 순차 기술되며, audit 단계만 `context: fork` sub-agent로 격리됩니다.

```
sec/
├── SKILL.md                              # 단일 진입점. frontmatter + 4단계 instruction (500행 이내)
├── references/
│   ├── traditional-vs-ai-security.md     # 전통적 보안 vs AI 컨텍스트 비교
│   ├── input-mapping.md                  # Arch/Impl/RE 산출물 → Security 입력 매핑
│   ├── output-schema.md                  # 4섹션 필드 정의
│   ├── stride-dread-guide.md             # STRIDE 카테고리 + DREAD 채점 가이드
│   ├── owasp-top-10-2021.md              # A01~A10 탐지 패턴
│   ├── cwe-catalog.md                    # 자주 쓰는 CWE ID와 분류 규칙
│   ├── cvss-v3.1-scoring.md              # CVSS 기본 점수 산정 가이드
│   ├── escalation-protocol.md            # critical/규제 미준수 에스컬레이션 절차
│   └── standards/
│       ├── asvs-l1.yaml
│       ├── asvs-l2.yaml
│       ├── asvs-l3.yaml
│       ├── pci-dss-code.md
│       ├── gdpr-code.md
│       └── hipaa-code.md
├── scripts/
│   ├── artifact.py       # 메타데이터/문서 파일 쌍 생성, phase/progress/refs 갱신
│   ├── approval.py       # 승인/반려/리스크 수용 기록 (감사 증적)
│   ├── validate.py       # 메타데이터 스키마 및 참조 무결성 검증
│   └── report.py         # 4섹션 종합 상태 리포트 (SKILL.md 동적 컨텍스트 주입용)
├── templates/
│   ├── threat-model.md.tpl
│   ├── vulnerability-report.md.tpl
│   ├── security-recommendation.md.tpl
│   ├── compliance-report.md.tpl
│   └── meta.yaml.tpl     # 공통 메타데이터 스켈레톤
├── assets/
│   └── dfd-template.mmd  # 위협 모델용 DFD 템플릿
└── examples/
    ├── lightweight-web-api/
    │   ├── input/                        # Arch/Impl 경량 산출물 샘플
    │   └── output/                       # 4섹션 산출물 (*.meta.yaml + *.md 쌍)
    ├── microservices-stride/
    │   ├── input/
    │   └── output/
    └── escalation-critical-sqli/
        ├── input/
        └── output/                       # CVSS 9.8 에스컬레이션 흐름 예시
```

쓰기 권한이 필요한 민감 경로는 별도 스킬로 분리합니다.

```
sec-record/
└── SKILL.md     # disable-model-invocation: true
                 # allowed-tools: Read
                 #   Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/artifact.py:*)
                 #   Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/approval.py:*)
                 #   Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/validate.py:*)
                 #   Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/report.py:*)
                 # 사용자가 명시적으로 호출했을 때만 메타데이터/승인 상태를 변경
```

## 에이전트 내부 흐름

```
Arch 산출물 (4섹션) + Impl 산출물 (4섹션) + RE 간접 참조
    │
    ▼
security:threat-model ────────────────────────────┐
    │  (Arch 컴포넌트 구조 → 신뢰 경계 도출 →       │
    │   STRIDE 위협 식별 → 도메인 맥락 대화 →        │
    │   대응 전략 수립 → 사용자 확인)                 │
    │                                              │
    ├──→ security:audit                            │
    │    (Impl 코드 → OWASP Top 10 기반 정적 분석   │
    │     → CWE 분류 → CVSS 점수 산정                │
    │     → 의존성 CVE 스캔)                         │
    │         │                                    │
    │         ▼                                    │
    ├──→ security:review                           │
    │    (threat-model 위협 + audit 취약점을         │
    │     기반으로 보안 로직 심층 리뷰                 │
    │     → 인증/인가/입력 검증/세션 관리 검증)        │
    │                                              │
    ▼                                              │
security:compliance ◄──────────────────────────────┘
    │  (threat-model + audit + review 결과를
    │   OWASP ASVS / PCI DSS / GDPR 등
    │   표준 항목에 매핑하여 준수 검증)
    │
    ├── 보안 권고 통합 생성
    │   (위협 대응 + 취약점 수정 + 컴플라이언스 갭
    │    → 우선순위화된 보안 권고 목록)
    │
    ▼
최종 산출물 (4섹션) → 사용자에게 보안 리포트 제시
```

### 에이전트 호출 규칙

- `threat-model`은 항상 최초 진입점. Arch 산출물을 수신하여 아키텍처 레벨 위협 분석을 수행. **도메인 맥락이 필요하므로 사용자와 대화**
- `audit`은 `threat-model` 이후 호출 (병렬 가능하지만, threat-model의 신뢰 경계 정보가 감사 범위 우선순위에 영향). Impl 산출물을 수신하여 코드 레벨 취약점을 자동 탐지
- `review`는 `threat-model` + `audit` 이후 호출. 위협 모델의 대응 전략이 코드에 올바르게 구현되었는지, audit이 발견하지 못한 로직 레벨 보안 이슈가 있는지 심층 리뷰
- `compliance`는 모든 에이전트 완료 후 최종 호출. 세 에이전트의 결과를 표준 항목에 매핑하고, 보안 권고를 통합 생성
- **threat-model은 대화형**, 나머지 에이전트는 **자동 실행**이 기본. 단, 자동 에이전트에서 **해소 불가능한 보안 이슈**가 발견되면 사용자에게 에스컬레이션

## 구현 단계

### 1단계: `SKILL.md` frontmatter 및 진입점 작성

표준 Claude Code Skill 포맷에 따라 `sec/SKILL.md` 상단에 YAML frontmatter(`---` 마커)를 작성하고, 본문에 4단계 instruction 진입점을 기술합니다. 기존 `skills.yaml` 가정은 폐기합니다.

- **frontmatter 필수 필드**:
  - `name: sec` (lowercase/digits/hyphens, ≤64)
  - `description`: 250자 이내, "무엇(what) + 언제(when)" front-load — "Audits Arch/Impl outputs for security threats, vulnerabilities, and standards compliance. Use when the user has completed architecture/implementation outputs and needs STRIDE threat modeling, CWE/CVSS vulnerability scanning, or OWASP ASVS/PCI DSS/GDPR/HIPAA compliance verification."
  - `allowed-tools: Read Grep Glob` — 읽기 전용 분석으로 제한. `Bash`/`Edit`/`Write` 미허용.
  - `disable-model-invocation: true` — 규제 의사결정 영역이므로 모델 자율 호출 차단
  - `user-invocable: true`
  - `argument-hint: "[--mode lightweight|heavy] [--standard owasp-asvs-l2|pci-dss|gdpr|hipaa]"`
  - `model: claude-opus-4-6`
  - `effort: high` (위협 모델링 단계 기준; audit은 sub-agent fork 시 별도 조정 가능)
- **본문 동적 컨텍스트 주입**: SKILL.md 본문 상단에 ``!`python3 ${CLAUDE_SKILL_DIR}/scripts/report.py summary` ``를 사용해 현재 4섹션 메타데이터 요약을 주입
- **문자열 치환 규약 명시**: `$ARGUMENTS`(모드/표준 인자), `${CLAUDE_SKILL_DIR}`(스크립트/템플릿/references 참조), `${CLAUDE_SESSION_ID}`(감사 증적 기록)
- **별도 쓰기 스킬 연계**: 메타데이터 변경이 필요한 시점에 `sec-record` 스킬을 사용자에게 명시적으로 호출하도록 안내
- **입력 스키마**:
  - Arch 산출물 4섹션 (`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`) 소비 계약
  - Impl 산출물 4섹션 (`implementation_map`, `code_structure`, `implementation_decisions`, `implementation_guide`) 소비 계약
  - RE 간접 참조 경로 (`re_refs`, `constraint_ref` 경유)
- **출력 스키마**: 4섹션 (`threat_model`, `vulnerability_report`, `security_recommendations`, `compliance_report`) 산출물 계약
  - 각 섹션의 필드 정의 및 필수/선택 여부 명시
  - 각 섹션의 산출물이 **메타데이터 파일(`*.meta.yaml`) + 문서 markdown 파일(`*.md`)의 쌍**으로 구성됨을 명시
  - 메타데이터 공통 필드 (`phase`, `progress`, `approval.*`, `*_refs`, `updated_at`) 및 섹션 고유 필드 스키마 정의
  - 허용된 `phase` 전이 규칙 (`draft → in_review → approved|rejected`, `approved → archived`)과 `approval.state` 전이 규칙 정의
  - 후속 스킬 연계를 위한 출력 계약(contract) 명세
- **적응적 깊이 설정**: Arch/Impl 모드에 따른 경량/중량 모드 기준 및 전환 규칙
- 지원 보안 표준 목록 (OWASP Top 10, OWASP ASVS, CWE, CVSS, PCI DSS, GDPR, HIPAA)
- 심각도 분류 체계 (CVSS v3.1 기반)
- **에스컬레이션 조건 정의**: critical/high 취약점 발견 시, 아키텍처 레벨 보안 결함 시 사용자 에스컬레이션 조건
- 의존성 정보 (선행: `arch`, `impl`, RE 간접 참조, 후속 소비자: `devops`, `qa`, `impl`)

### 2단계: SKILL.md 본문 — 4단계 instruction 작성

단일 `sec/SKILL.md` 본문에 **threat-model → audit → review → compliance** 4단계를 순차 instruction으로 기술합니다. 각 단계는 다음 구조를 따르며, audit 단계만 `context: fork` sub-agent로 격리됩니다(대용량 코드 정적 분석을 메인 컨텍스트에서 분리). 각 단계의 상세 체크리스트와 매핑 규칙은 `references/`의 해당 파일을 참조하는 방식으로 SKILL.md 본문 행 수를 500행 이내로 억제합니다.

#### 1단계 instruction — 위협 모델링 (threat-model)

- **역할**: Arch 산출물을 기반으로 사용자와의 대화를 통해 아키텍처 레벨 위협을 식별하고 대응 전략을 수립
- **핵심 역량**:
  - **Arch 산출물 → 보안 모델 변환**:
    - `component_structure.type` → 신뢰 경계 자동 도출 (`gateway` = 외부↔내부 경계, `store` = 데이터 경계, `queue` = 비동기 경계)
    - `component_structure.interfaces` → 공격 표면(attack surface) 카탈로그 생성
    - `component_structure.dependencies` → 데이터 흐름 경로 및 권한 전파 경로 매핑
    - `diagrams.c4-container` → DFD(Data Flow Diagram) 기초 자동 생성
    - `diagrams.sequence` → 인증/인가 흐름의 보안 검증 지점 도출
    - `architecture_decisions.decision` → 보안 함의 분석 (예: "이벤트 드리븐" → 메시지 위변조 위협)
  - **도메인 맥락 대화**: Arch에서 드러나지 않는 보안 맥락을 사용자에게 능동적으로 질문
    - 데이터 민감도 분류 (어떤 데이터가 PII/PHI/금융 데이터인지)
    - 사용자/역할 유형 및 권한 모델 (RBAC, ABAC, 다중 테넌시)
    - 외부 연동 시스템의 신뢰 수준
    - 규제 준수 요구사항의 구체적 범위
    - 위협 행위자 프로파일 (내부자, 외부 공격자, 자동화된 봇)
  - **STRIDE 방법론 적용**: 각 컴포넌트/데이터 흐름/신뢰 경계에 대해 6가지 위협 카테고리 체계적 분석
  - **DREAD 기반 위험 우선순위 평가**: 각 위협의 Damage, Reproducibility, Exploitability, Affected Users, Discoverability 점수 산정
  - **대응 전략 수립**: 위협별 대응 전략을 사용자에게 제시하고 확인 (완화, 전가, 수용, 회피)
  - **공격 트리 생성**: 주요 위협에 대한 공격 트리를 Mermaid로 생성
- **입력**: Arch 산출물 (`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`)
- **출력**:
  - 위협 모델 (신뢰 경계, 데이터 흐름 보안 분류, 위협 목록, DREAD 점수, 대응 전략)
  - 공격 트리 (Mermaid 코드)
  - 보안 관점 DFD
- **상호작용 모델**: Arch 산출물 수신 → 신뢰 경계/공격 표면 자동 도출 → 도메인 맥락 질문 → 사용자 응답 → STRIDE 위협 분석 초안 제시 → 사용자 확인 (특히 데이터 민감도, 위협 행위자) → 대응 전략 제시 → 사용자 확인 (리스크 수용 여부) → 확정
- **에스컬레이션 조건**: 없음 — threat-model 자체가 대화형이므로 모든 불확실성은 대화 내에서 해소

#### 2단계 instruction — 보안 감사 (audit, `context: fork` sub-agent)

> audit은 대용량 코드 정적 분석이 필요하므로 `context: fork`로 sub-agent를 띄워 격리된 컨텍스트에서 수행합니다. sub-agent도 `allowed-tools: Read Grep Glob`만 허용하며, 결과(취약점 목록/CWE 분류/CVSS 점수)만 메인 컨텍스트로 반환합니다.


- **역할**: Impl 산출물을 기반으로 코드 보안 취약점을 **자동으로** 정적 분석하고, 의존성 취약점을 스캔
- **핵심 역량**:
  - **Impl 산출물 → 감사 범위 결정**:
    - `implementation_map.module_path` → 감사 대상 파일 목록
    - `implementation_map.interfaces_implemented` → API 엔드포인트별 감사 (입력 검증, 인증 여부)
    - `code_structure.external_dependencies` → 알려진 CVE 취약점 스캔 대상
    - `code_structure.environment_config` → 시크릿/크리덴셜 노출 점검
    - `implementation_decisions.pattern_applied` → 패턴별 알려진 보안 약점 점검
  - **threat-model 연동**: `threat-model`이 식별한 고위험 컴포넌트/데이터 흐름에 감사 우선순위 부여
  - **OWASP Top 10 취약점 탐지**:
    - A01: Broken Access Control — 인가 로직 누락/우회
    - A02: Cryptographic Failures — 취약한 암호화/해싱, 평문 전송
    - A03: Injection — SQL, NoSQL, OS 명령어, LDAP 인젝션
    - A04: Insecure Design — 위협 모델 대응 전략 미구현
    - A05: Security Misconfiguration — 기본 설정, 불필요한 기능 활성화
    - A06: Vulnerable Components — 알려진 CVE가 있는 의존성
    - A07: Authentication Failures — 취약한 인증 메커니즘
    - A08: Data Integrity Failures — 서명/검증 없는 데이터 역직렬화
    - A09: Logging Failures — 보안 이벤트 로깅 누락
    - A10: SSRF — 서버 측 요청 위조
  - **CWE 기반 분류**: 모든 발견 사항을 CWE ID로 분류
  - **CVSS v3.1 점수 산정**: 각 취약점의 기본 점수(Base Score) 산정
  - **하드코딩된 시크릿/크리덴셜 탐지**: API 키, 비밀번호, 토큰, 인증서 등
  - **의존성 취약점 분석**: `external_dependencies`에서 알려진 CVE 매핑, 패치 가용 여부 확인
- **입력**: Impl 산출물 (`implementation_map`, `code_structure`, `implementation_decisions`) + threat-model 산출물 (감사 우선순위)
- **출력**:
  - 취약점 보고서 (CWE ID, OWASP 분류, CVSS 점수, 위치, 재현 시나리오, 수정 제안)
  - 의존성 취약점 목록 (패키지, 버전, CVE ID, 수정 버전)
  - 시크릿 노출 목록 (위치, 유형, 심각도)
- **상호작용 모델**: Impl 산출물 + threat-model 우선순위 수신 → 전체 코드 자동 감사 → 의존성 자동 스캔 → 결과 보고. 사용자 개입 없음
- **에스컬레이션 조건**: CVSS 9.0 이상의 critical 취약점이 발견된 경우, 즉시 사용자에게 에스컬레이션하여 긴급 대응 여부 확인. 의존성 취약점 중 패치가 존재하지 않는 zero-day의 경우 대안(대체 라이브러리, 워크어라운드)을 제시하고 사용자에게 선택 요청

#### 3단계 instruction — 보안 코드 리뷰 (review)

- **역할**: threat-model의 위협과 audit의 취약점을 기반으로, **보안 로직의 정확성**을 심층 리뷰. audit이 패턴 매칭으로 탐지할 수 없는 **로직 레벨 보안 이슈**에 집중
- **핵심 역량**:
  - **threat-model 연동 리뷰**: 위협 모델의 각 대응 전략(`mitigation`)이 코드에 올바르게 구현되었는지 검증
    - `TM-001: Spoofing → JWT 검증` → JWT 검증 로직의 완전성 확인 (알고리즘 고정, 만료 검증, 서명 검증)
    - `TM-003: Information Disclosure → 데이터 암호화` → 암호화 적용 범위와 알고리즘 적절성 확인
  - **인증/인가 로직 검증 (AuthN/AuthZ)**:
    - 인증 흐름의 완전성 (모든 보호 엔드포인트에 인증 적용 여부)
    - 인가 모델의 정확성 (권한 검증 로직, 수직/수평 권한 상승 방어)
    - 세션 관리 보안 (세션 ID 엔트로피, 만료, 고정 공격 방어)
    - 비밀번호 정책 및 저장 방식 (bcrypt/argon2, salt)
  - **입력 검증 및 새니타이징 검증**:
    - 모든 외부 입력 지점에서 검증이 이루어지는지 확인 (Arch `interfaces` 기반)
    - 화이트리스트 vs 블랙리스트 접근법 평가
    - 출력 인코딩 (XSS 방어) 확인
    - 파라미터화된 쿼리 (SQL 인젝션 방어) 확인
  - **에러 핸들링의 정보 노출 방지**: 에러 메시지에 스택 트레이스, 시스템 정보, 데이터베이스 구조 등이 노출되지 않는지 확인
  - **보안 헤더 및 CORS 설정 검증**: CSP, HSTS, X-Frame-Options, CORS 정책의 적절성
  - **암호화 사용 적절성**: 알고리즘 선택, 키 길이, IV/nonce 재사용, 패딩 오라클 가능성
- **입력**: Impl 코드 + threat-model 산출물 (대응 전략 검증 기준) + audit 산출물 (발견된 취약점 컨텍스트) + Arch 산출물 (`interfaces`, `component_structure`)
- **출력**:
  - 보안 리뷰 리포트 (로직 레벨 이슈, 대응 전략 구현 검증 결과, 라인별 피드백, 심각도, 코드 수정 제안)
  - 대응 전략 구현 매트릭스 (threat-model의 각 mitigation이 코드에서 어떻게 구현되었는지 매핑)
- **상호작용 모델**: threat-model + audit + Impl 산출물 수신 → 대응 전략 구현 검증 자동 수행 → 보안 로직 심층 리뷰 자동 수행 → 결과 보고
- **에스컬레이션 조건**: threat-model에서 `risk_level: critical`인 위협의 대응 전략이 코드에서 **미구현 또는 불완전 구현**인 경우, 사용자에게 에스컬레이션. 아키텍처 레벨 보안 결함(인증 체계 자체의 결함 등)이 발견된 경우 `arch:review`로의 피드백과 함께 사용자에게 에스컬레이션

#### 4단계 instruction — 컴플라이언스 (compliance)

- **역할**: threat-model, audit, review 세 에이전트의 결과를 보안 표준 항목에 매핑하여 준수 상태를 **자동으로** 검증하고, 통합 보안 권고를 생성
- **핵심 역량**:
  - **표준별 자동 매핑**:
    - threat-model의 위협/대응 전략 → OWASP ASVS 설계 요구사항 항목에 매핑
    - audit의 취약점 → OWASP ASVS 구현 요구사항 항목에 매핑
    - review의 보안 로직 검증 결과 → OWASP ASVS 검증 요구사항 항목에 매핑
  - **OWASP ASVS (Application Security Verification Standard) 레벨별 검증**:
    - Level 1: 자동화 가능한 기본 보안 검증
    - Level 2: 대부분의 애플리케이션에 권장되는 표준 보안 검증
    - Level 3: 높은 보안이 요구되는 애플리케이션 (금융, 의료, 정부)
    - 적용 레벨은 RE `constraints`의 규제 요구사항에서 자동 결정 (HIPAA/PCI DSS → L3, 일반 → L2, 경량 → L1)
  - **PCI DSS 코드 레벨 요구사항 검증**: 카드 데이터 처리 시 — 암호화, 접근 제어, 로깅, 키 관리
  - **GDPR 코드 레벨 요구사항 검증**: 개인 데이터 처리 시 — 동의 관리, 데이터 최소화, 삭제 권리, 데이터 이동권
  - **HIPAA 코드 레벨 요구사항 검증**: 의료 데이터 처리 시 — PHI 암호화, 접근 감사, 무결성 검증
  - **보안 설정 베스트 프랙티스 검증**: 기술 스택별 보안 설정 가이드라인 대비 검증
  - **통합 보안 권고 생성**: threat-model 대응 전략 + audit 수정 제안 + review 리뷰 피드백 + compliance 갭을 종합하여 **우선순위화된 보안 권고 목록** 생성
  - **갭 분석 리포트**: 표준별 준수/미준수 항목 집계, 미준수 항목의 심각도별 그룹화, 개선 로드맵 생성
- **입력**: threat-model 산출물 + audit 산출물 + review 산출물 + RE `constraints` (간접, 규제 제약) + Arch `technology_stack` (기술별 설정 기준)
- **출력**:
  - 컴플라이언스 리포트 (표준별 준수 상태, 항목별 검증 결과, 갭 분석)
  - 통합 보안 권고 목록 (우선순위, 유형, 조치 방안, 관련 위협/취약점/갭 참조)
- **상호작용 모델**: 세 에이전트 산출물 수신 → 표준별 자동 매핑 → 준수 상태 자동 판정 → 통합 보안 권고 생성 → **최종 보안 리포트를 사용자에게 제시** (Security 파이프라인의 정규 사용자 접점)
- **에스컬레이션 조건**: RE `constraints`에 명시된 `hard` 규제 제약(PCI DSS, HIPAA 등)에 대해 `non_compliant` 판정이 내려진 경우, 즉시 사용자에게 에스컬레이션. 규제 미준수는 법적 리스크이므로 자동 수용 불가

SKILL.md 본문의 4단계 instruction에는 다음 공통 운영 규칙을 포함합니다:
- **메인 `sec`는 읽기 전용**: `allowed-tools: Read Grep Glob`만 보유. `*.meta.yaml`/`*.md`를 직접 생성하거나 수정하지 않습니다.
- **쓰기는 `sec-record`에 위임**: 메타데이터 생성/상태 전이/승인/리스크 수용/감사 증적 기록이 필요한 경우, 사용자에게 필요한 작업을 설명하고 **사용자가 명시적으로 `sec-record` 스킬을 호출**하도록 안내합니다. `sec-record`는 `disable-model-invocation: true`이므로 모델이 자율적으로 호출할 수 없습니다.
- **상태 전이 시점 명시**: 초안 완료 시 사용자에게 "다음 명령으로 `in_review`로 전이해 주세요: `/sec-record set-phase --id TM-001 --phase in_review`"와 같이 구체적인 `sec-record` 호출 예시를 제공
- **리스크 수용/critical 에스컬레이션은 감사 증적**: `mitigation_status: accepted` 처리나 critical 취약점에 대한 사용자 결정은 반드시 `sec-record`의 `approval.py accept-risk` 또는 `approval.py approve --rationale ...`로 기록되도록 안내. 감사 증적에는 `${CLAUDE_SESSION_ID}`와 `approval.approver`, `approval.rationale`이 필수로 포함되어야 함
- **에스컬레이션의 표준 매핑**: critical 취약점이나 규제 미준수가 발견되면 메인 에이전트가 분석을 중단하고 사용자에게 직접 질문하여 결정을 받습니다. 사용자가 답한 뒤에만 `sec-record`를 통해 감사 증적이 기록됩니다. 상세 절차는 `references/escalation-protocol.md` 참조

### 3단계: 메타데이터 스크립트, 문서 템플릿, references 자료 구현 (`scripts/`, `templates/`, `references/`)

SKILL.md 본문 작성보다 먼저 스크립트·템플릿·참조 자료를 고정하여, SKILL.md가 이들을 안정적으로 참조 가능한 상태로 작성되도록 합니다.

- **`references/` 작성**: PLAN 본문에서 SKILL.md로 옮기지 않을 상세 자료를 `references/`에 배치
  - `references/traditional-vs-ai-security.md`
  - `references/input-mapping.md` (Arch/Impl/RE → Security 입력 매핑 표)
  - `references/output-schema.md` (4섹션 필드 정의)
  - `references/stride-dread-guide.md`
  - `references/owasp-top-10-2021.md`
  - `references/cwe-catalog.md`
  - `references/cvss-v3.1-scoring.md`
  - `references/escalation-protocol.md`
  - `references/standards/asvs-l1.yaml`, `asvs-l2.yaml`, `asvs-l3.yaml`, `pci-dss-code.md`, `gdpr-code.md`, `hipaa-code.md`

- **`templates/*.md.tpl` 작성**: 4섹션 각각에 대해 섹션 헤더, 플레이스홀더(`<!-- TODO: ... -->`), 고정 마크다운 포맷을 포함한 문서 템플릿 작성
- **`templates/meta.yaml.tpl` 작성**: 공통 메타데이터 스켈레톤. 생성 시 `phase: draft`, `approval.state: pending`, `updated_at: <생성 시각>`으로 초기화
- **`scripts/artifact.py` 구현**:
  - `init` 서브커맨드: `--section`과 `--id`를 받아 템플릿에서 `*.meta.yaml`와 `*.md` 쌍을 생성
  - `set-phase` / `set-progress` / `add-ref` / `show` 서브커맨드: 허용된 상태 전이 규칙을 enforce하며 갱신
  - 모든 쓰기 작업에서 `updated_at` 자동 기록
- **`scripts/approval.py` 구현**: `request` / `approve` / `reject` / `accept-risk` 서브커맨드. 각 커맨드는 `approval.approver`, `approval.approved_at`, `approval.rationale`를 메타데이터에 원자적으로 기록하여 **감사 증적을 남김**
- **`scripts/validate.py` 구현**: 스키마 검증(필수 필드, enum, 타입) + 참조 무결성 검증(`arch_refs`/`impl_refs`/`re_refs`의 존재성)
- **`scripts/report.py` 구현**: 4섹션 메타데이터를 종합하여 `phase`/`approval.state` 요약, 미승인 critical 이슈 목록, 컴플라이언스 갭 집계 출력

### 4단계: 프롬프트 템플릿 작성 (`prompts/`)

각 에이전트에 대응하는 프롬프트 템플릿을 작성합니다:
- **Arch/Impl 산출물 파싱 가이드**: 두 스킬의 산출물에서 보안 관련 정보를 추출하는 방법
- **신뢰 경계 도출 가이드**: `component_structure.type`과 `dependencies`에서 신뢰 경계를 식별하는 규칙
- **도메인 맥락 질문 가이드**: 어떤 보안 맥락이 부족할 때 어떤 질문을 생성할지 (데이터 민감도, 위협 행위자, 규제 범위)
- **STRIDE 체계적 적용 템플릿**: 컴포넌트/데이터 흐름/신뢰 경계별 STRIDE 분석 구조
- **OWASP Top 10 감사 체크리스트 프롬프트**: 취약점 카테고리별 탐지 패턴 및 코드 패턴
- **CWE 분류 가이드**: 발견 사항을 CWE ID로 매핑하는 규칙
- **CVSS v3.1 점수 산정 가이드**: 공격 벡터, 복잡도, 권한 요구, 영향 범위별 점수 산정
- **보안 코드 리뷰 체크리스트 프롬프트**: 인증/인가/입력 검증/세션 관리/암호화 영역별 검증 항목
- **OWASP ASVS 매핑 가이드**: 각 에이전트 산출물을 ASVS 항목에 매핑하는 규칙
- **에스컬레이션 메시지 형식**: critical 취약점, 규제 미준수 시 사용자에게 전달할 정보 구조
- **스크립트 호출 가이드**: 각 단계별로 호출해야 할 `scripts/artifact.py` / `scripts/approval.py` 커맨드와 인자 예시 (에이전트가 메타데이터를 직접 편집하지 않도록)
- Chain of Thought 가이드라인
- Few-shot 예시 포함

### 5단계: 입출력 예시 작성 (`examples/`)

각 에이전트별 대표적인 입출력 쌍을 작성합니다:
- **Arch 경량 출력 → Security 경량 분석** 예시 (단일 웹 API의 OWASP Top 10 감사)
- **Arch 중량 출력 → Security 중량 분석** 예시 (마이크로서비스 아키텍처의 전체 STRIDE 위협 모델링)
- 도메인 맥락 대화를 통한 데이터 민감도 분류 예시
- REST API 위협 모델링 예시 (STRIDE + DREAD + 공격 트리)
- 인증 모듈 보안 코드 리뷰 예시 (JWT 검증 로직)
- 의존성 CVE 스캔 결과 예시 (패치 가용/불가용 케이스)
- OWASP ASVS 레벨 2 컴플라이언스 검증 예시
- **에스컬레이션 예시**: CVSS 9.8 SQL 인젝션 발견 시 긴급 에스컬레이션 (및 대응하는 `approval.py` 호출 이력)
- **정상 완료 예시**: 에스컬레이션 없이 전체 자동 분석 후 보안 리포트 제시
- **메타데이터/문서 쌍 예시**: 각 에이전트의 출력에 대해 `*.meta.yaml` 파일과 `*.md` 파일을 **모두 포함**. 메타데이터에는 `phase`, `progress`, `approval.state`/`approver`/`approved_at`/`rationale`, `*_refs`가 실제 값으로 채워진 상태로 제시
- **리스크 수용 감사 증적 예시**: `mitigation_status: accepted`인 위협에 대해 `approval.py accept-risk`로 기록된 메타데이터 스냅샷
- **컴플라이언스 체크리스트 YAML 예시**: OWASP ASVS L2의 항목별 `requirement_id`/`status`/`evidence`가 채워진 `CR-xxx.meta.yaml`과 갭 서술이 담긴 `CR-xxx.md`의 쌍

## 핵심 설계 원칙

1. **Arch/Impl 산출물 기반 (Arch/Impl-Driven)**: 모든 보안 분석은 Arch의 4섹션과 Impl의 4섹션 산출물에 근거하며, `arch_refs`/`impl_refs`/`re_refs`로 추적성을 유지. 신뢰 경계는 `component_structure`에서, 공격 표면은 `interfaces`에서, 코드 취약점은 `implementation_map`에서 도출
2. **심층 방어 (Defense in Depth)**: 단일 계층이 아닌 다계층 보안 관점. 아키텍처 레벨(threat-model) → 코드 패턴 레벨(audit) → 로직 레벨(review) → 표준 준수 레벨(compliance)의 4단계 검증으로 각 계층이 놓칠 수 있는 이슈를 후속 계층이 보완
3. **대화형 + 자동 실행 혼합 모델**: threat-model은 도메인 맥락(데이터 민감도, 위협 행위자, 규제 범위)이 필요하므로 **대화형**. audit/review/compliance는 선행 산출물에서 기계적 도출이 가능하므로 **자동 실행 + 예외 에스컬레이션**. critical 취약점과 규제 미준수만 에스컬레이션
4. **표준 기반 (Standards-Based)**: CWE로 취약점 분류, CVSS v3.1로 심각도 평가, STRIDE/DREAD로 위협 분석, OWASP ASVS로 컴플라이언스 검증 — 업계 표준 참조 체계를 일관되게 사용하여 산출물의 객관성과 비교 가능성 확보
5. **적응적 깊이 (Adaptive Depth)**: Arch/Impl 모드에 연동하여 경량(OWASP Top 10 체크리스트 + 핵심 위협)/중량(전체 STRIDE + ASVS 레벨별 + CVSS 상세 평가) 모드 자동 전환. 간단한 시스템에 과잉 분석을 적용하지 않고, 복잡한 시스템에 과소 분석을 적용하지 않음
6. **에이전트 역할 분리**: audit은 **코드 패턴 매칭 기반** 취약점 탐지 (SAST 영역), review는 **보안 로직 정확성** 검증 (수동 리뷰 영역), compliance는 **표준 항목 매핑** (감사 영역). 세 에이전트의 관점이 다르므로 상호 보완적이며, 중복이 아닌 다층 방어를 구현
7. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **위협 모델 / 취약점 보고서 / 보안 권고 / 컴플라이언스 리포트** 4섹션으로 고정하여, 후속 스킬(`devops`, `qa`, `impl`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
8. **메타데이터-문서 분리 및 감사 증적 (Metadata-Document Separation & Audit Trail)**: 모든 산출물은 **구조화 메타데이터 YAML(`*.meta.yaml`)과 서술형 markdown 문서(`*.md`)의 쌍**으로 관리하며, 메타데이터는 에이전트가 직접 편집하지 않고 `scripts/artifact.py`·`scripts/approval.py` 커맨드를 통해서만 갱신. `phase`/`progress`는 진행 상태를, `approval.state`/`approver`/`approved_at`/`rationale`은 **감사 증적**을 담당하여, 리스크 수용·critical 에스컬레이션·규제 미준수 승인 등 모든 보안 의사결정이 사후 감사 시 추적 가능. 문서 또한 `templates/`의 섹션 템플릿에서 골격을 생성한 뒤 에이전트가 서술을 채워 포맷 일관성과 섹션 누락 방지를 동시에 달성
