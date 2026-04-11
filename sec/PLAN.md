# Sec (Security) Skill 구현 계획

## 개요

Arch 스킬의 산출물(아키텍처 결정, 컴포넌트 구조, 기술 스택, 다이어그램)과 Impl 스킬의 산출물(구현 맵, 코드 구조, 구현 결정, 구현 가이드)을 입력으로 받아, **보안 위협 모델링·취약점 감사·보안 코드 리뷰·컴플라이언스 검증**을 수행하는 스킬입니다.

Impl이 "설계를 코드로 어떻게 구현할 것인가"를 실행하고 QA가 "기능적으로 올바른가"를 검증했다면, Sec는 "그 설계와 구현이 **보안적으로 안전한가**"를 검증합니다. 이 과정에서 **Arch의 컴포넌트 구조를 신뢰 경계와 공격 표면의 근거로, Impl의 구현 맵을 코드 레벨 취약점 탐지의 근거로** 사용하며, 모든 보안 산출물은 원천 아키텍처 결정과 요구사항(RE)까지 역추적 가능합니다.

위협 모델링은 아키텍처 레벨의 도메인 지식이 필요하므로 **대화형 모델**을 채택하고, 코드 레벨 감사·리뷰·컴플라이언스 검증은 선행 산출물에서 기계적으로 도출 가능하므로 **자동 실행 + 예외 에스컬레이션** 모델을 채택합니다.

### 전통적 보안 vs AI 컨텍스트 보안

| 구분 | 전통적 보안 | AI 컨텍스트 보안 |
|------|------------|-----------------|
| 수행자 | 전담 보안 팀 (보안 엔지니어, 펜테스터) | 개발자가 AI에게 보안 분석과 검증을 위임 |
| 입력 | 설계 문서, 코드, 인터뷰, 침투 테스트 | **Arch/Impl 스킬의 구조화된 산출물** (추적성 내장) |
| 위협 모델링 | 화이트보드 세션, 수작업 DFD | **Arch 컴포넌트 구조 → 신뢰 경계/데이터 흐름 자동 도출** + 도메인 맥락 대화 |
| 취약점 탐지 | SAST/DAST 도구 + 수동 리뷰 | **Impl 코드 구조 기반 체계적 정적 분석** + CWE 분류 자동화 |
| 보안 리뷰 | 리뷰어 경험에 의존, 체크리스트 편차 큼 | **Arch 결정 + 위협 모델 기반 체계적 리뷰** — 무엇을 검증할지 자동 도출 |
| 컴플라이언스 | 감사 시점에 수동 체크리스트 점검 | **코드 + 설정 + 위협 분석 결과를 표준 항목에 자동 매핑** |
| 추적성 | 취약점 리포트와 설계/요구사항 간 수동 연결 | **`re_refs`/`arch_refs`/`impl_refs`로 자동 추적** |
| 산출물 | PDF 보안 리포트 | **후속 스킬이 소비 가능한 구조화된 4섹션 산출물** |
| 주기 | 릴리스 직전 또는 감사 시점 | **Arch/Impl 산출물이 갱신될 때마다 수시로** |

## 선행 스킬 산출물 소비 계약

Sec 스킬은 Arch와 Impl 두 스킬의 산출물을 직접 소비하고, RE는 Arch 산출물의 참조(`re_refs`, `constraint_ref`)를 통해 간접 소비합니다.

### Arch 산출물 소비 매핑

| Arch 산출물 섹션 | 주요 필드 | Sec에서의 소비 방법 |
|-----------------|-----------|------------------------|
| **아키텍처 결정** | `id`, `decision`, `trade_offs`, `re_refs` | `decision`에서 보안 함의 도출 (예: 마이크로서비스 → 서비스 간 인증 필요, 이벤트 드리븐 → 메시지 무결성 검증 필요). `trade_offs`에서 보안이 희생된 결정 식별. `re_refs`로 RE까지 추적성 유지 |
| **컴포넌트 구조** | `id`, `name`, `type`, `interfaces`, `dependencies` | `type`으로 신뢰 경계 식별 (`gateway` = 외부 경계, `service` = 내부 경계, `store` = 데이터 경계). `interfaces`로 공격 표면(attack surface) 도출. `dependencies`로 데이터 흐름 경로 및 권한 전파 경로 매핑 |
| **기술 스택** | `category`, `choice`, `constraint_ref` | `choice`로 기술별 알려진 취약점 패턴 매핑 (예: Express → prototype pollution, Django → CSRF 토큰 검증). `constraint_ref`로 RE 규제 제약(GDPR, HIPAA 등) 확인하여 컴플라이언스 검증 대상 결정 |
| **다이어그램** | `type`, `code` | `c4-container`로 시스템 경계와 외부 액터 식별 → 위협 모델 DFD 기초. `data-flow`로 민감 데이터 흐름 경로 추적. `sequence`로 인증/인가 흐름의 보안 검증 지점 도출 |

### Impl 산출물 소비 매핑

| Impl 산출물 섹션 | 주요 필드 | Sec에서의 소비 방법 |
|-----------------|-----------|------------------------|
| **구현 맵** | `id`, `component_ref`, `module_path`, `interfaces_implemented`, `re_refs` | `module_path`로 보안 감사 대상 파일 범위 결정. `interfaces_implemented`로 API 엔드포인트별 보안 검증 대상 식별. `component_ref`로 Arch 컴포넌트 보안 요구사항과 매핑 |
| **코드 구조** | `directory_layout`, `module_dependencies`, `external_dependencies`, `environment_config` | `external_dependencies`로 알려진 CVE 취약점 스캔 대상 식별. `environment_config`로 시크릿/크리덴셜 관리 상태 점검. `module_dependencies`로 권한 경계 위반 여부 확인 |
| **구현 결정** | `id`, `decision`, `pattern_applied`, `arch_refs`, `re_refs` | `pattern_applied`로 패턴별 보안 검증 포인트 결정 (예: Repository 패턴 → SQL 인젝션 방어 확인, Strategy 패턴 → 전략 교체 시 권한 검증). `decision`에서 보안 관련 구현 결정의 적절성 검토 |
| **구현 가이드** | `setup_steps`, `build_commands`, `environment_config`, `conventions` | `environment_config`로 시크릿 관리 방식 검증 (하드코딩, 환경 변수, 시크릿 매니저). `build_commands`로 빌드 파이프라인 보안 검증 지점 식별 |

### RE 산출물 간접 참조

Sec는 RE 산출물을 직접 소비하지 않으나, Arch 산출물의 `re_refs`와 `constraint_ref`를 통해 간접 참조합니다.

| RE 산출물 | 간접 참조 경로 | Sec에서의 영향 |
|-----------|---------------|-------------------|
| **요구사항 명세** | Arch `component_structure.re_refs` → `FR-xxx`, `NFR-xxx` | NFR 중 보안 관련 요구사항(`NFR-security`)의 구현 충족 여부 검증 |
| **제약 조건** | Arch `technology_stack.constraint_ref` → `CON-xxx` | `type: regulatory` 제약(GDPR, HIPAA, PCI DSS 등)을 컴플라이언스 검증 대상 표준으로 사용. `hard` 제약은 비협상 보안 요구사항으로 고정 |
| **품질 속성 우선순위** | Arch `architecture_decisions.re_refs` → `QA:security` | `priority`로 보안의 전체 우선순위 파악. `metric`(예: "모든 API 인증 필수", "민감 데이터 AES-256 암호화")을 보안 검증 기준으로 사용. `trade_off_notes`로 보안이 다른 속성과 트레이드오프된 지점 식별 |

### 추적성 체인 (RE → Arch → Impl → Sec)

Sec는 RE → Arch → Impl → Sec로 이어지는 추적성 체인에서 **보안 관점의 검증 지점**입니다.

```
RE:spec 산출물                Arch 산출물              Impl 산출물              Sec 산출물
┌──────────────┐        ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ NFR-security │──re──  │ AD-001       │──arch──│ IDR-001      │──impl──│ TM-001       │
│  metric:     │  refs  │  decision:   │  _refs │  pattern:    │  _refs │  threats     │
│  "인증 필수" │        │  "JWT 기반"  │        │  "미들웨어"  │        │  mitigations │
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

### 적응적 깊이

Arch/Impl의 출력 밀도에 연동하여 Sec의 산출물 수준을 자동 조절합니다.

| Arch/Impl 모드 | 판별 기준 | Sec 모드 | 산출물 수준 |
|---------------|-----------|--------------|------------|
| 경량 | Arch 컴포넌트 ≤ 3개, 단일 서비스, 외부 인터페이스 ≤ 2개 | 경량 | OWASP Top 10 체크리스트 기반 감사 + 핵심 위협 요약(STRIDE 경량 적용) + 의존성 CVE 스캔 + 인라인 보안 가이드 |
| 중량 | Arch 컴포넌트 > 3개 또는 서비스 간 통신 존재 또는 외부 인터페이스 > 2개 | 중량 | 전체 STRIDE 위협 모델링 + DREAD 우선순위 + 컴포넌트별 정적 분석 + CWE 분류 취약점 리포트 + CVSS 심각도 평가 + OWASP ASVS 레벨별 컴플라이언스 리포트 + 보안 아키텍처 권고 |

## 최종 산출물 구조

Sec 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. 설계/구현의 보안 검증까지를 범위로 하며, 침투 테스트(DAST)나 런타임 보안 모니터링은 후속 스킬(`devops`)의 영역입니다.

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

위협 모델 보조 산출물:

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

### 3. 보안 권고 (Security Advisory)

발견된 위협과 취약점에 대한 우선순위화된 조치 가이드를 구조화합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `SR-001`) |
| `title` | 권고 제목 |
| `category` | 권고 유형 (`architecture` / `code` / `configuration` / `dependency` / `process`) |
| `priority` | 조치 우선순위 (1이 가장 높음) — 위험 수준, 수정 난이도, 영향 범위 종합 |
| `description` | 권고 상세 설명 |
| `current_state` | 현재 상태 (어떤 문제가 있는지) |
| `recommended_action` | 권장 조치 (구체적 코드/설정/아키텍처 변경) |
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
| `findings` | 항목별 검증 결과 — 각 항목: `requirement_id`, `title`, `status`, `evidence`, `gap_description`, `remediation` |
| `gap_summary` | 갭 요약 — 미준수 항목을 심각도별로 그룹화 |
| `remediation_roadmap` | 개선 로드맵 — 우선순위별 개선 항목, 예상 노력 |
| `constraint_refs` | 근거가 된 RE 제약 조건 ID (`CON-xxx` 등) |
| `threat_refs` | 관련 위협 모델 ID (`TM-xxx`) |
| `vuln_refs` | 관련 취약점 ID (`VA-xxx`) |

### 산출물 파일 구성: 메타데이터 + 문서 분리

위 4섹션의 산출물은 **메타데이터 파일과 문서 markdown 파일을 분리**하여 저장합니다. 메타데이터는 구조화된 상태/추적 정보를 담고, markdown은 사람이 읽을 서술형 본문을 담습니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 파일 | **YAML** (`*.meta.yaml`) | 진행 상태, 승인 상태, 추적성(refs), 4섹션의 구조화 필드 저장. 스크립트가 읽고 쓰는 단일 진실 공급원(SSoT) |
| 문서 파일 | Markdown (`*.md`) | 위협 설명, 공격 시나리오, 수정 제안, 갭 서술 등 사람이 읽는 분석 본문 |

**YAML을 채택한 이유**:

- **주석 지원**: 감사자가 필드 의도를 인라인 주석으로 바로 이해할 수 있어 감사 검토 단계의 컨텍스트 전달이 용이
- **사람이 읽기 쉬움**: 들여쓰기 기반 구조로 별도 렌더러 없이 그대로 검토 가능 — 보안 산출물처럼 사용자가 직접 검토하는 문서에 적합
- **블록 스칼라 친화성**: 긴 `evidence`/`remediation` 스니펫을 자연스럽게 표현 가능
- **스크립트 파싱 용이**: PyYAML 등 표준 라이브러리로 손쉽게 로드/덤프 가능

특히 **컴플라이언스 리포트**는 본질적으로 표준 항목 ID 기준의 구조화된 체크리스트(`requirement_id` × `status` × `evidence`)이므로 YAML 친화성이 매우 높습니다.

### 메타데이터 스키마 (공통 필드)

각 산출물 메타데이터 파일은 4섹션의 구조화 필드 외에 다음 공통 필드를 포함합니다.

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 고유 식별자 (예: `SEC-threat-model-001`) |
| `phase` | 현재 단계 (`draft` / `in_review` / `revising` / `approved` / `rejected` / `archived`) |
| `progress` | 진행률 정보 (`section_completed`, `section_total`, `percent`) |
| `approval.state` | 승인 상태 (`pending` / `approved` / `rejected` / `conditionally_approved`) |
| `approval.approver` | 승인자 식별자 (사용자명/역할) |
| `approval.approved_at` | 승인 시각 (ISO 8601) |
| `approval.conditions` | 조건부 승인 시 조건 목록 |
| `approval.rationale` | 승인/반려/리스크 수용 사유 (감사 증적의 핵심) |
| `upstream_refs` | 상위 산출물 ID 목록 (`re_refs`, `arch_refs`, `impl_refs`) |
| `downstream_refs` | 이 산출물을 소비하는 후속 산출물 ID 목록 (`devops`, `qa`, `impl` 등) |
| `cross_refs` | 섹션 간 cross-refs (`threat_refs`, `vuln_refs`) |
| `document_path` | 짝을 이루는 markdown 문서의 상대 경로 |
| `updated_at` | 최종 수정 시각 (스크립트가 자동 기록) |

**감사 추적성(Audit Trail) 강조**: 보안 산출물은 사후 감사·규제 증적 요구가 매우 강한 영역입니다. `approval.state` / `approver` / `approved_at` / `rationale`는 단순한 워크플로 필드가 아니라, **누가 언제 어떤 근거로 위험을 수용(accept)하거나 대응 전략을 승인했는지에 대한 감사 증적**으로 활용됩니다. 특히 `mitigation_status: accepted`(리스크 수용), `hard` 규제 제약에 대한 `conditionally_approved`, critical 취약점에 대한 사용자 에스컬레이션 결과 등은 모두 이 필드에 기록되어, 추후 침해 사고 조사나 규제 감사 시 의사결정의 정합성을 입증하는 근거가 됩니다.

### 스크립트 기반 메타데이터 조작 (필수)

에이전트는 **YAML 메타데이터 파일을 직접 편집하지 않습니다**. 모든 상태 갱신은 `${CLAUDE_SKILL_DIR}/scripts/` 디렉토리의 스크립트 커맨드를 통해서만 수행하며, 이는 다음을 보장합니다.

- 스키마 검증 (잘못된 phase 값, 누락 필드 차단)
- `updated_at` 등 자동 필드의 일관된 갱신
- 추적성 ref의 양방향 무결성 (upstream/downstream 동기화)
- 승인 상태 전이 규칙 적용 (예: `draft → approved` 직행 금지)
- 감사 증적의 원자적 기록 (`approval.approver`, `approval.rationale`, `${CLAUDE_SESSION_ID}`)

핵심 스크립트:

| 스크립트 커맨드 | 용도 |
|----------------|------|
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section <name> --id <id>` | 메타데이터 + markdown 템플릿 쌍을 새로 생성 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase <id> <phase>` | 진행 단계 전이 (전이 규칙 검증 포함) |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py set-progress <id> --completed N --total M` | 진행률 갱신 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | 추적성 ref 추가 (양방향 무결성 유지) |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py show <id>` | 메타데이터 + 문서 합쳐 조회 |
| `${CLAUDE_SKILL_DIR}/scripts/approval.py request <id>` | 승인 요청 상태로 전환 |
| `${CLAUDE_SKILL_DIR}/scripts/approval.py approve <id> --approver <name> --rationale ...` | 승인 처리 및 감사 증적 기록 |
| `${CLAUDE_SKILL_DIR}/scripts/approval.py reject <id> --approver <name> --rationale ...` | 반려 처리 |
| `${CLAUDE_SKILL_DIR}/scripts/approval.py accept-risk <id> --approver <name> --rationale ...` | 리스크 수용 기록 (감사 증적의 핵심 케이스) |
| `${CLAUDE_SKILL_DIR}/scripts/validate.py [<id>]` | 스키마/추적성 검증 |
| `${CLAUDE_SKILL_DIR}/scripts/report.py summary` | 4섹션 메타데이터 종합 상태 리포트 (SKILL.md 동적 컨텍스트 주입용) |

### 문서 템플릿 (`assets/templates/`)

markdown 문서 또한 자유 양식이 아니라, `assets/templates/` 디렉토리에 4섹션별 템플릿을 사전에 정의합니다. `artifact.py init` 실행 시 해당 템플릿이 복사되어 **섹션 헤더, 플레이스홀더, RE/Arch/Impl 참조 위치가 채워진 골격**이 생성되며, 에이전트는 이 골격 안의 플레이스홀더를 채우는 방식으로 본문을 작성합니다.

| 템플릿 파일 | 대상 섹션 |
|------------|----------|
| `assets/templates/threat-model.md.tmpl` | 위협 모델 (위협 개요·공격 벡터·공격 트리(Mermaid)·대응 전략·리스크 수용 근거) |
| `assets/templates/vulnerability-report.md.tmpl` | 취약점 보고서 (취약점 설명·위치·재현 절차(PoC)·수정 제안·의존성 취약점 상세) |
| `assets/templates/security-advisory.md.tmpl` | 보안 권고 (현재 상태·권장 조치·대안·트레이드오프) |
| `assets/templates/compliance-report.md.tmpl` | 컴플라이언스 리포트 (표준 개요·항목별 증적·갭 서술·개선 로드맵) |
| `assets/templates/*.meta.yaml.tmpl` | 각 섹션 메타데이터의 초기 골격 (`phase: draft`, `approval.state: pending` 등) |

### 후속 스킬 연계

```
sec 산출물 구조:
┌─────────────────────────────────────────┐
│  위협 모델 (Threat Model)               │──→ devops:strategy (보안 관점 배포 제약)
│  - TM-001: STRIDE 위협 목록             │──→ devops:monitor (보안 모니터링 지표)
│  - 신뢰 경계, 데이터 흐름 분류           │──→ qa:strategy (보안 테스트 시나리오 도출)
├─────────────────────────────────────────┤
│  취약점 보고서 (Vulnerability Report)   │──→ impl:refactor (취약점 코드 수정 대상)
│  - VA-001: CWE-89, CVSS 9.8             │──→ devops:pipeline (보안 스캔 게이트)
│  - 의존성 CVE, 코드 취약점              │──→ qa:generate (보안 회귀 테스트 대상)
├─────────────────────────────────────────┤
│  보안 권고 (Security Advisory)          │──→ arch:review (아키텍처 레벨 보안 개선)
│  - SR-001: 아키텍처/코드/설정 권고      │──→ impl:refactor (코드 레벨 보안 개선)
│  - 우선순위별 조치 가이드                │──→ devops:iac (인프라 보안 설정)
├─────────────────────────────────────────┤
│  컴플라이언스 리포트 (Compliance Report)│──→ devops:log (로깅 컴플라이언스 요구)
│  - CR-001: OWASP ASVS L2 partial        │──→ devops:pipeline (컴플라이언스 게이트)
│  - 표준별 준수/미준수, 갭 분석          │──→ 외부 컴플라이언스 감사 (감사 증적)
└─────────────────────────────────────────┘
```

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점은 `sec/SKILL.md`이며, `skills.yaml`, `agents/`, `prompts/` 디렉토리는 사용하지 않습니다. 상세 행동 규칙과 단계별 가이드는 `references/`에, 템플릿은 `assets/`에 분리합니다.

```
sec/
├── SKILL.md                              # 필수 진입점 (YAML frontmatter + 4단계 워크플로우 요약, 500줄 이내)
├── scripts/
│   ├── artifact.py                       # 메타데이터 init/set-phase/set-progress/link/show
│   ├── approval.py                       # 승인/반려/리스크 수용 (감사 증적 기록)
│   ├── validate.py                       # 스키마/추적성 무결성 검증
│   └── report.py                         # 4섹션 종합 상태 리포트 (동적 컨텍스트 주입용)
├── assets/
│   └── templates/
│       ├── threat-model.md.tmpl
│       ├── threat-model.meta.yaml.tmpl
│       ├── vulnerability-report.md.tmpl
│       ├── vulnerability-report.meta.yaml.tmpl
│       ├── security-advisory.md.tmpl
│       ├── security-advisory.meta.yaml.tmpl
│       ├── compliance-report.md.tmpl
│       ├── compliance-report.meta.yaml.tmpl
│       └── dfd-template.mmd              # 위협 모델용 DFD 템플릿
└── references/
    ├── workflow/
    │   ├── threat-model.md               # 위협 모델링 단계 상세 행동 규칙 (on-demand 로드)
    │   ├── audit.md                      # 감사 단계 상세 행동 규칙
    │   ├── review.md                     # 보안 코드 리뷰 단계 상세 행동 규칙
    │   └── compliance.md                 # 컴플라이언스 단계 상세 행동 규칙
    ├── contracts/
    │   ├── arch-input-contract.md        # Arch 4섹션 소비 계약
    │   ├── impl-input-contract.md        # Impl 4섹션 소비 계약
    │   └── downstream-contract.md        # devops/qa/impl 소비 계약
    ├── schemas/
    │   ├── meta-schema.md                # 메타데이터 공통 필드 설명
    │   └── section-schemas.md            # 4섹션 필드 명세
    ├── adaptive-depth.md                 # 경량/중량 분기 규칙
    ├── escalation-protocol.md            # critical 취약점 / 규제 미준수 에스컬레이션 절차
    ├── standards/
    │   ├── owasp-top-10-2021.md          # A01~A10 탐지 패턴
    │   ├── stride-dread-guide.md         # STRIDE 카테고리 + DREAD 채점 가이드
    │   ├── cwe-catalog.md                # 자주 쓰는 CWE ID와 분류 규칙
    │   ├── cvss-v3.1-scoring.md          # CVSS v3.1 기본 점수 산정 가이드
    │   ├── asvs.md                       # OWASP ASVS L1/L2/L3 항목 카탈로그
    │   ├── pci-dss.md                    # PCI DSS 코드 레벨 요구사항
    │   ├── gdpr.md                       # GDPR 코드 레벨 요구사항
    │   └── hipaa.md                      # HIPAA 코드 레벨 요구사항
    └── examples/
        ├── light/
        │   ├── threat-model-input.md
        │   ├── threat-model-output.md
        │   └── threat-model-output.meta.yaml
        └── heavy/
            ├── threat-model-input.md
            ├── threat-model-output.md
            ├── threat-model-output.meta.yaml
            ├── vulnerability-report-output.md
            ├── security-advisory-output.md
            └── compliance-report-output.md
```

요점:
- `SKILL.md`가 유일한 필수 진입점이며, 4개의 워크플로우 단계(threat-model/audit/review/compliance)는 **동일 SKILL.md 안에 짧게 요약**하고, 상세 규칙은 `references/workflow/*.md`로 분리하여 **on-demand 로드**합니다.
- `templates/` 대신 표준 명칭인 `assets/templates/`, `examples/` 대신 `references/examples/`를 사용합니다.
- `skills.yaml`, `agents/`, `prompts/`는 폐기합니다.
- 보안 표준 카탈로그(OWASP/STRIDE/CWE/CVSS/ASVS/PCI/GDPR/HIPAA)는 `references/standards/` 하위에 통합 배치합니다.

## sec vs sec-record 분리 (읽기 전용 vs 쓰기 전용)

Sec 스킬은 본질적으로 **읽기 위주(read-only) 분석**입니다. 그러나 메타데이터 갱신·승인 기록·리스크 수용·감사 증적 기록 같은 민감 액션은 권한과 책임이 명확해야 합니다. 이를 위해 두 개의 별도 스킬로 분리합니다.

| 스킬 | 역할 | `allowed-tools` | 호출 방식 |
|------|------|----------------|---------|
| `sec` (메인, 읽기 전용) | 위협 모델링 · 감사 · 리뷰 · 컴플라이언스 분석 | `Read Grep Glob` | 사용자 또는 모델 호출 |
| `sec-record` (쓰기 전용 보조 스킬) | 메타데이터/승인 상태/감사 증적 기록 | `Read` + `Bash(python3 ${CLAUDE_SKILL_DIR}/../sec/scripts/artifact.py:*)` `Bash(python3 .../approval.py:*)` `Bash(python3 .../validate.py:*)` `Bash(python3 .../report.py:*)` | **`disable-model-invocation: true`** — 사용자 명시 호출만 가능 |

**분리의 근거**:

- 메인 `sec`에서 어떠한 `Bash`/`Edit`/`Write`도 허용하지 않으면, 임의 명령 실행 경로와 메타데이터 무단 수정이 원천적으로 차단됩니다.
- `sec-record`는 `disable-model-invocation: true`로 모델 자율 호출을 차단하고, **사용자가 명시적으로 호출**해야만 메타데이터/승인 상태가 변경됩니다. 리스크 수용·critical 결정 같은 감사 증적 작업이 모델 단독 결정으로 일어나지 않도록 보장합니다.
- `sec-record`의 `Bash`는 일반 셸이 아닌 명시적 prefix 화이트리스트(`Bash(python3 .../approval.py:*)` 등)만 허용하여 임의 명령 실행 경로를 차단합니다.
- 두 스킬은 동일한 `sec/scripts/` 디렉토리를 공유합니다(`sec-record`는 `${CLAUDE_SKILL_DIR}/../sec/scripts/`로 참조).

## 워크플로우 단계 (SKILL.md 내부 단일 진입점)

표준 스킬 모델을 따르기 위해, 기존에 "4개의 내부 에이전트"로 구상했던 threat-model/audit/review/compliance는 **별도의 시스템 프롬프트 파일이 아니라**, SKILL.md가 순차적으로 수행하는 **4개의 워크플로우 단계**로 재정의합니다. 각 단계의 상세 행동 규칙은 `references/workflow/*.md`에 분리되어 필요 시점에 Read로 로드됩니다.

```
Arch 산출물 (4섹션) + Impl 산출물 (4섹션) + RE 간접 참조
    │
    ▼
[Stage 1] threat-model ─────────────────────────────┐
    │  references/workflow/threat-model.md 로드      │
    │  (Arch 컴포넌트 → 신뢰 경계 도출 → STRIDE 위협 │
    │   식별 → 도메인 맥락 대화 → 대응 전략 →        │
    │   사용자 확인)                                  │
    │                                                │
    ├──→ [Stage 2] audit                             │
    │    references/workflow/audit.md 로드           │
    │    (Impl 코드 → OWASP Top 10 정적 분석 →       │
    │     CWE 분류 → CVSS 점수 → 의존성 CVE 스캔)    │
    │         │                                      │
    │         ▼                                      │
    ├──→ [Stage 3] review                            │
    │    references/workflow/review.md 로드          │
    │    (위협 + 취약점 기반 보안 로직 심층 리뷰 →    │
    │     인증/인가/입력 검증/세션 관리 검증)         │
    │                                                │
    ▼                                                │
[Stage 4] compliance ◄───────────────────────────────┘
    references/workflow/compliance.md 로드
    (앞 3단계 결과를 OWASP ASVS / PCI DSS / GDPR /
     HIPAA 등 표준 항목에 매핑하여 준수 검증 +
     통합 보안 권고 생성)
```

### `references/workflow/threat-model.md` — 위협 모델링 단계 상세 규칙

- **역할**: Arch 산출물을 기반으로 사용자와의 대화를 통해 아키텍처 레벨 위협을 식별하고 대응 전략을 수립
- **핵심 역량**:
  - **Arch 산출물 → 보안 모델 변환**:
    - `component_structure.type` → 신뢰 경계 자동 도출 (`gateway` = 외부↔내부 경계, `store` = 데이터 경계, `queue` = 비동기 경계)
    - `component_structure.interfaces` → 공격 표면(attack surface) 카탈로그 생성
    - `component_structure.dependencies` → 데이터 흐름 경로 및 권한 전파 경로 매핑
    - `diagrams.c4-container` → DFD(Data Flow Diagram) 기초 자동 생성
    - `diagrams.sequence` → 인증/인가 흐름의 보안 검증 지점 도출
    - `architecture_decisions.decision` → 보안 함의 분석 (예: "이벤트 드리븐" → 메시지 위변조 위협)
  - **도메인 맥락 대화**: Arch에서 드러나지 않는 보안 맥락을 사용자에게 능동적으로 질문 — 데이터 민감도 분류(PII/PHI/금융), 사용자/역할 권한 모델, 외부 연동 시스템의 신뢰 수준, 규제 준수 요구사항의 구체적 범위, 위협 행위자 프로파일
  - **STRIDE 방법론 적용**: 각 컴포넌트/데이터 흐름/신뢰 경계에 대해 6가지 위협 카테고리 체계적 분석
  - **DREAD 기반 위험 우선순위 평가**
  - **대응 전략 수립**: 위협별 대응 전략을 사용자에게 제시하고 확인 (완화, 전가, 수용, 회피)
  - **공격 트리 생성**: 주요 위협에 대한 공격 트리를 Mermaid로 생성
- **입력**: Arch 산출물 (`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`)
- **출력**: 위협 모델(신뢰 경계, 데이터 흐름 보안 분류, 위협 목록, DREAD 점수, 대응 전략) + 공격 트리 + 보안 관점 DFD
- **상호작용 모델**: Arch 산출물 수신 → 신뢰 경계/공격 표면 자동 도출 → 도메인 맥락 질문 → 사용자 응답 → STRIDE 위협 분석 초안 제시 → 사용자 확인 (특히 데이터 민감도, 위협 행위자) → 대응 전략 제시 → 사용자 확인 (리스크 수용 여부) → 확정

### `references/workflow/audit.md` — 감사 단계 상세 규칙

- **역할**: Impl 산출물을 기반으로 코드 보안 취약점을 **자동으로** 정적 분석하고, 의존성 취약점을 스캔
- **핵심 역량**:
  - **Impl 산출물 → 감사 범위 결정**:
    - `implementation_map.module_path` → 감사 대상 파일 목록
    - `implementation_map.interfaces_implemented` → API 엔드포인트별 감사 (입력 검증, 인증 여부)
    - `code_structure.external_dependencies` → 알려진 CVE 취약점 스캔 대상
    - `code_structure.environment_config` → 시크릿/크리덴셜 노출 점검
    - `implementation_decisions.pattern_applied` → 패턴별 알려진 보안 약점 점검
  - **threat-model 연동**: 식별된 고위험 컴포넌트/데이터 흐름에 감사 우선순위 부여
  - **OWASP Top 10 취약점 탐지** (A01 Broken Access Control ~ A10 SSRF)
  - **CWE 기반 분류**: 모든 발견 사항을 CWE ID로 분류
  - **CVSS v3.1 점수 산정**: 각 취약점의 기본 점수(Base Score) 산정
  - **하드코딩된 시크릿/크리덴셜 탐지**: API 키, 비밀번호, 토큰, 인증서 등
  - **의존성 취약점 분석**: `external_dependencies`에서 알려진 CVE 매핑, 패치 가용 여부 확인
- **입력**: Impl 산출물 (`implementation_map`, `code_structure`, `implementation_decisions`) + threat-model 산출물 (감사 우선순위)
- **출력**: 취약점 보고서 (CWE ID, OWASP 분류, CVSS 점수, 위치, 재현 시나리오, 수정 제안) + 의존성 취약점 목록 + 시크릿 노출 목록
- **상호작용 모델**: 자동 실행. 사용자 개입 없음
- **에스컬레이션 조건**: CVSS 9.0 이상의 critical 취약점 발견 시 즉시 사용자에게 에스컬레이션. 패치가 존재하지 않는 zero-day의 경우 대안(대체 라이브러리, 워크어라운드)을 제시하고 사용자에게 선택 요청

### `references/workflow/review.md` — 보안 코드 리뷰 단계 상세 규칙

- **역할**: threat-model의 위협과 audit의 취약점을 기반으로, **보안 로직의 정확성**을 심층 리뷰. audit이 패턴 매칭으로 탐지할 수 없는 **로직 레벨 보안 이슈**에 집중
- **핵심 역량**:
  - **threat-model 연동 리뷰**: 위협 모델의 각 대응 전략(`mitigation`)이 코드에 올바르게 구현되었는지 검증
    - `TM-001: Spoofing → JWT 검증` → JWT 검증 로직의 완전성 확인 (알고리즘 고정, 만료 검증, 서명 검증)
    - `TM-003: Information Disclosure → 데이터 암호화` → 암호화 적용 범위와 알고리즘 적절성 확인
  - **인증/인가 로직 검증 (AuthN/AuthZ)**: 인증 흐름 완전성, 인가 모델 정확성, 세션 관리 보안, 비밀번호 정책/저장 방식
  - **입력 검증 및 새니타이징 검증**: 외부 입력 검증 지점, 화이트리스트 vs 블랙리스트, 출력 인코딩(XSS), 파라미터화된 쿼리(SQL 인젝션)
  - **에러 핸들링의 정보 노출 방지**
  - **보안 헤더 및 CORS 설정 검증**: CSP, HSTS, X-Frame-Options
  - **암호화 사용 적절성**: 알고리즘 선택, 키 길이, IV/nonce 재사용
- **입력**: Impl 코드 + threat-model 산출물 + audit 산출물 + Arch 산출물 (`interfaces`, `component_structure`)
- **출력**: 보안 리뷰 리포트 (로직 레벨 이슈, 대응 전략 구현 검증 결과, 라인별 피드백) + 대응 전략 구현 매트릭스
- **상호작용 모델**: 자동 수행, 결과 보고
- **에스컬레이션 조건**: `risk_level: critical` 위협의 대응 전략이 코드에서 미구현/불완전 구현인 경우 사용자에게 에스컬레이션. 아키텍처 레벨 보안 결함 발견 시 `arch:review`로의 피드백과 함께 에스컬레이션

### `references/workflow/compliance.md` — 컴플라이언스 단계 상세 규칙

- **역할**: 앞 3단계 결과를 보안 표준 항목에 매핑하여 준수 상태를 **자동으로** 검증하고, 통합 보안 권고를 생성
- **핵심 역량**:
  - **표준별 자동 매핑**: threat-model 위협/대응 전략 → ASVS 설계 요구사항 / audit 취약점 → ASVS 구현 요구사항 / review 로직 검증 결과 → ASVS 검증 요구사항
  - **OWASP ASVS 레벨별 검증**: L1(자동화 가능 기본), L2(표준 권장), L3(금융/의료/정부). 적용 레벨은 RE `constraints`의 규제 요구사항에서 자동 결정
  - **PCI DSS 코드 레벨 요구사항 검증**: 카드 데이터 처리 시 — 암호화, 접근 제어, 로깅, 키 관리
  - **GDPR 코드 레벨 요구사항 검증**: 동의 관리, 데이터 최소화, 삭제 권리, 데이터 이동권
  - **HIPAA 코드 레벨 요구사항 검증**: PHI 암호화, 접근 감사, 무결성 검증
  - **통합 보안 권고 생성**: threat-model 대응 전략 + audit 수정 제안 + review 피드백 + compliance 갭을 종합하여 우선순위화
  - **갭 분석 리포트**: 표준별 준수/미준수 항목 집계, 심각도별 그룹화, 개선 로드맵
- **입력**: threat-model + audit + review 산출물 + RE `constraints`(간접) + Arch `technology_stack`
- **출력**: 컴플라이언스 리포트 + 통합 보안 권고 목록
- **상호작용 모델**: 자동 매핑 → 자동 판정 → 통합 보안 권고 생성 → **최종 보안 리포트를 사용자에게 제시** (Sec 파이프라인의 정규 사용자 접점)
- **에스컬레이션 조건**: RE `constraints`의 `hard` 규제 제약(PCI DSS, HIPAA 등)에 대해 `non_compliant` 판정 시 즉시 사용자에게 에스컬레이션. 규제 미준수는 법적 리스크이므로 자동 수용 불가

## 구현 단계

### 1단계: `SKILL.md` 작성 (필수 진입점 + frontmatter)

표준에서 메타데이터의 단일 출처는 `sec/SKILL.md`의 YAML frontmatter입니다. `skills.yaml`은 표준 사양에 존재하지 않으므로 사용하지 않습니다. Claude Code Skill 표준에 따라 frontmatter는 `name`과 `description`만 필수로 두고, 나머지 옵션 필드는 기본 동작으로 스킬 목적을 달성할 수 없음이 입증된 경우에만 추가합니다.

**권장 frontmatter 초안 (메인 `sec`)**:

```yaml
---
name: sec
description: Arch/Impl 산출물을 입력으로 받아 STRIDE 위협 모델·CWE/CVSS 취약점 보고서·보안 권고·OWASP ASVS/PCI DSS/GDPR/HIPAA 컴플라이언스 리포트 4섹션 산출물을 생성하고, scripts/로 메타데이터·감사 증적을 관리한다. 아키텍처/구현 산출물 완료 후 STRIDE 위협 모델링, CWE/CVSS 취약점 스캔, OWASP ASVS/PCI DSS/GDPR/HIPAA 컴플라이언스 검증이 필요할 때 사용.
allowed-tools: Read Grep Glob
disable-model-invocation: true
---
```

**설계 원칙**:

- **`name`**: 스킬 디렉토리명과 일치시켜 `sec`로 고정합니다 (lowercase/digits/hyphens 규칙). 표준에서 요구하는 두 필수 필드 중 하나입니다.
- **`description` 작성 규칙 (자동 호출 품질 결정)**: 첫 200자 안에 *무엇을 하는가*("Arch/Impl 산출물 → Sec 4섹션 산출물 생성")와 *언제 사용하는가*("STRIDE 위협 모델링 / CWE·CVSS 취약점 스캔 / ASVS·PCI·GDPR·HIPAA 컴플라이언스 검증")를 모두 포함합니다. 250자 경계에서 잘릴 수 있음을 가정하여 핵심 키워드를 앞에 배치합니다.
- **옵션 필드의 정당화된 추가** (표준 동작으로 목적을 달성할 수 없는 구체적 사유가 있는 경우만):
  - **`allowed-tools: Read Grep Glob`** — 보안 분석은 본질적으로 읽기 위주이고, 메인 `sec`가 임의 명령 실행 경로와 메타데이터 무단 수정을 가질 수 없음. `Bash`/`Edit`/`Write`는 명시적으로 미허용.
  - **`disable-model-invocation: true`** — 규제 의사결정(리스크 수용, 컴플라이언스 판정) 영역이므로 모델이 체인 내부에서 자율적으로 임의 호출하는 것을 차단. 사용자가 명시적으로 호출해야만 실행됨.
- 그 외 옵션 필드(`argument-hint`, `effort`, `model`, `paths`, `hooks`, `context` 등)는 기본값으로 두고 추가하지 않습니다.

**SKILL.md 본문 구성 (500줄 이내)**:

1. 스킬 개요 (Arch+Impl 4섹션 → Sec 4섹션)
2. 입력/출력 계약 요약 (상세는 `references/contracts/*.md`로 분리)
3. 적응적 깊이 분기 로직 (Arch/Impl 모드 판별 → 경량/중량 모드 결정)
4. 4단계 워크플로우 요약 (threat-model → audit → review → compliance)
   - 각 단계는 **상세 규칙을 `references/workflow/<stage>.md`에서 로드**하도록 명시
   - 예: "감사 시 `${CLAUDE_SKILL_DIR}/references/workflow/audit.md`를 Read로 로드한 뒤 지시를 따른다"
5. 스크립트 호출 규약: 모든 메타데이터 조작은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py`·`approval.py`·`validate.py`·`report.py`를 통해서만 수행. 메인 `sec`는 직접 호출 권한이 없으므로 사용자에게 `sec-record` 호출을 명시적으로 안내
6. 시작 시 현재 상태 주입: SKILL.md 상단에서 `` !`python3 ${CLAUDE_SKILL_DIR}/scripts/report.py summary` ``를 사용해 현재 4섹션 산출물 상태·승인·갭 요약을 동적 컨텍스트로 주입
7. 에스컬레이션 안내: critical 취약점·규제 미준수 발견 시 분석을 중단하고 사용자 결정을 요청하는 절차를 본문에 요약 (상세는 `references/escalation-protocol.md`)
8. 의존성 정보(선행: `arch`, `impl`, RE 간접; 후속: `devops`, `qa`, `impl`)는 frontmatter가 아니라 본문 또는 `references/contracts/downstream-contract.md`에 기술

**치환자 활용**:

- 모든 스크립트 경로는 `${CLAUDE_SKILL_DIR}/scripts/...`로 작성하여 사용자 호출 위치에 관계없이 동작하도록 합니다.
- `$ARGUMENTS`는 `--mode lightweight|heavy`, `--standard owasp-asvs-l2|pci-dss|gdpr|hipaa` 같은 인자를 받는 데 사용합니다.
- `${CLAUDE_SESSION_ID}`는 감사 증적 기록 시 세션 식별자로 `approval.py`에 전달합니다.

**문서 길이 관리**:

- `SKILL.md`는 500줄 이내를 유지합니다.
- 초과 위험이 있는 상세 내용(전통적 보안 비교, 표준 카탈로그, 입력 매핑 표 등)은 모두 `references/` 하위로 분리하고, SKILL.md는 "언제 어떤 reference를 로드할지"만 명시합니다.

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

기존 PLAN의 "4개 내부 에이전트" 개념은 표준 스킬 모델과 직접 매핑되지 않습니다. 대신 각 단계의 상세 행동 규칙을 `references/workflow/`에 markdown 파일로 분리하고, SKILL.md가 단계 진입 시 on-demand로 Read합니다. 4개 파일(`threat-model.md`, `audit.md`, `review.md`, `compliance.md`)의 구조와 내용은 위 "워크플로우 단계" 섹션에 명세된 대로 작성합니다.

각 워크플로우 파일은 다음 공통 운영 규칙을 반복 명시합니다:

- **메인 `sec`는 읽기 전용**: `*.meta.yaml`/`*.md`를 직접 생성·수정하지 않습니다.
- **쓰기는 `sec-record`에 위임**: 메타데이터 생성·상태 전이·승인·리스크 수용·감사 증적 기록이 필요한 경우, 사용자에게 필요한 작업을 설명하고 **사용자가 명시적으로 `sec-record` 스킬을 호출**하도록 안내합니다.
- **상태 전이 시점 명시**: 초안 완료 시 사용자에게 "다음 명령으로 `in_review`로 전이해 주세요: `/sec-record set-phase --id TM-001 --phase in_review`"와 같이 구체적인 호출 예시를 제공
- **리스크 수용/critical 에스컬레이션은 감사 증적**: `mitigation_status: accepted` 처리나 critical 취약점에 대한 사용자 결정은 반드시 `approval.py accept-risk` 또는 `approval.py approve --rationale ...`로 기록되도록 안내. 감사 증적에는 `${CLAUDE_SESSION_ID}`와 `approval.approver`, `approval.rationale`이 필수로 포함

### 3단계: 참조 문서 작성 (`references/`)

프롬프트 템플릿을 별도 `prompts/` 디렉토리로 분리하던 기존 계획은 폐기하고, 모든 가이드 문서를 표준 `references/` 디렉토리로 통합합니다. SKILL.md가 필요한 시점에 해당 파일을 Read합니다.

- `references/workflow/*.md` (4개): 단계별 상세 행동 규칙 — 2단계에서 작성
- `references/contracts/arch-input-contract.md`: Arch 4섹션 → Sec 입력 파싱 가이드 (component → 신뢰 경계, interface → 공격 표면, tech-stack → 알려진 취약점 패턴, diagram → DFD 기초)
- `references/contracts/impl-input-contract.md`: Impl 4섹션 → Sec 입력 파싱 가이드 (module_path → 감사 대상, external_dependencies → CVE 스캔, environment_config → 시크릿 점검)
- `references/contracts/downstream-contract.md`: 후속 스킬(`devops`, `qa`, `impl`) 소비 계약
- `references/schemas/meta-schema.md`: 메타데이터 공통 필드(`artifact_id`, `phase`, `approval`, `upstream_refs`, `downstream_refs`, `cross_refs` 등) 명세
- `references/schemas/section-schemas.md`: 4섹션(`threat-model`, `vulnerability-report`, `security-advisory`, `compliance-report`) 필드 명세
- `references/adaptive-depth.md`: 경량/중량 모드 판별 규칙과 모드별 스킵 단계 정의
- `references/escalation-protocol.md`: critical 취약점·규제 미준수 발견 시 에스컬레이션 절차 (메인 에이전트 분석 중단 → 사용자 직접 질문 → 사용자 답변 후 `sec-record` 위임 → 감사 증적 기록)
- `references/standards/`: 보안 표준 카탈로그
  - `owasp-top-10-2021.md`: A01~A10 탐지 패턴 및 코드 패턴
  - `stride-dread-guide.md`: STRIDE 6 카테고리 정의 + DREAD 채점 가이드
  - `cwe-catalog.md`: 자주 쓰는 CWE ID와 분류 규칙
  - `cvss-v3.1-scoring.md`: CVSS v3.1 기본 점수 산정 가이드 (벡터/복잡도/권한/영향)
  - `asvs.md`: OWASP ASVS L1/L2/L3 항목 카탈로그 (적용 레벨 자동 결정 규칙 포함)
  - `pci-dss.md`, `gdpr.md`, `hipaa.md`: 코드 레벨 요구사항 카탈로그
- `references/examples/` 하위: Arch 산출물 → 신뢰 경계 도출 예시, STRIDE 적용 예시, CWE 분류 예시, ASVS 매핑 예시

**스크립트 호출 규약 배치**: "에이전트가 YAML을 직접 편집하지 않고 `scripts/` 커맨드만 호출한다"는 행동 규약은 `references/workflow/*.md`에 반복 명시하고, 각 단계(초안 → 리뷰 → 승인 → 감사 증적 기록)에서 어떤 커맨드를 어떤 순서로 호출해야 하는지 시퀀스로 기술합니다. 메인 `sec`는 직접 호출 권한이 없으므로, 사용자에게 `sec-record`를 통한 호출 예시를 안내하는 형태로 표현합니다.

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

표준 디렉토리 명칭은 `assets/`입니다(기존 `templates/`는 폐기).

- 4섹션(`threat-model`, `vulnerability-report`, `security-advisory`, `compliance-report`)별 markdown 템플릿(`*.md.tmpl`)을 `assets/templates/`에 작성. 각 템플릿은 섹션 헤더, 표 골격, RE/Arch/Impl 참조 슬롯, 플레이스홀더(`<!-- TODO: ... -->`)를 포함하여 에이전트가 본문만 채우도록 유도
- 각 섹션의 메타데이터 초기 골격(`*.meta.yaml.tmpl`)을 작성. `phase: draft`, `approval.state: pending`, 빈 `upstream_refs`/`downstream_refs`/`cross_refs` 등 기본값을 포함
- `threat-model.md.tmpl`은 STRIDE 카테고리별 슬롯과 Mermaid 코드 펜스(```` ```mermaid ````)로 attack tree/DFD 골격을 미리 배치
- `compliance-report.md.tmpl`은 표준별 항목 체크리스트 골격(`requirement_id` × `status` × `evidence`)을 미리 배치
- `assets/dfd-template.mmd`는 위협 모델용 DFD Mermaid 베이스 템플릿

**적응적 깊이 → 분기 매핑**:

- SKILL.md 본문의 분기 로직에서 `references/adaptive-depth.md`의 판별 기준에 따라 경량 조건이면 STRIDE 일부 카테고리/ASVS 레벨 일부 단계를 스킵합니다.
- 즉 하나의 스킬 안에서 경량/중량 모드를 내부 분기로 처리하며, 스킬 자체를 `sec-light`/`sec-full`로 분할하지 않습니다(단일 진입점 유지).

### 5단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

- `scripts/artifact.py`: `init` / `set-phase` / `set-progress` / `link` / `show` 서브커맨드. `init`는 `${CLAUDE_SKILL_DIR}/assets/templates/`에서 템플릿을 복사해 메타데이터 + markdown 쌍을 생성. 모든 쓰기 커맨드는 `updated_at`을 자동 갱신하고 잘못된 상태 전이를 차단
- `scripts/approval.py`: `request` / `approve` / `reject` / `accept-risk` 서브커맨드. 각 커맨드는 `approval.approver`, `approval.approved_at`, `approval.rationale`, `${CLAUDE_SESSION_ID}`를 메타데이터에 원자적으로 기록하여 **감사 증적**을 남김. `approve`/`reject` 직행 같은 잘못된 전이는 차단
- `scripts/validate.py`: 스키마 검증(필수 필드, enum, 타입) + 참조 무결성 검증(`arch_refs`/`impl_refs`/`re_refs`/`cross_refs` 존재성)
- `scripts/report.py`: 4섹션 메타데이터를 종합하여 `phase`/`approval.state` 요약, 미승인 critical 이슈 목록, 컴플라이언스 갭 집계 출력 (SKILL.md 동적 컨텍스트 주입용)

**스크립트 호출 강제 (다층 방어)**:

행동 규약만으로는 우회될 수 있으므로 다층 방어를 구성합니다.

1. **행동 규약 (가장 약함)**: `references/workflow/*.md` 및 SKILL.md 본문에서 "메타데이터 갱신은 반드시 `${CLAUDE_SKILL_DIR}/scripts/`의 커맨드를 호출한다"를 반복 명시
2. **도구 권한 분리 (중간)**: 메인 `sec`의 `allowed-tools`를 `Read Grep Glob`만으로 고정하여 `Bash`/`Edit`/`Write`를 원천 차단. 메타데이터 쓰기 권한은 별도의 `sec-record` 스킬로 격리
3. **`disable-model-invocation` (강함)**: `sec-record`에 `disable-model-invocation: true`를 적용하여, 모델이 스킬을 자율 호출할 수 없게 하고 **사용자가 명시적으로 호출**해야만 메타데이터/감사 증적이 변경되도록 강제. `sec-record`의 `Bash`는 명시적 prefix 화이트리스트(`Bash(python3 .../approval.py:*)` 등)만 허용
4. **시작 시 상태 주입 (최강)**: SKILL.md 상단에서 `` !`python3 ${CLAUDE_SKILL_DIR}/scripts/report.py summary` ``를 사용해 현재 산출물 상태·추적성 무결성·감사 증적을 동적으로 주입. 이를 통해 에이전트가 자연스럽게 스크립트 기반 흐름을 따르도록 유도

### 6단계: 입출력 예시 작성 (`references/examples/`)

- Arch 경량 출력 → Sec 경량 분석 예시 (단일 웹 API의 OWASP Top 10 감사)
- Arch 중량 출력 → Sec 중량 분석 예시 (마이크로서비스 아키텍처의 전체 STRIDE 위협 모델링)
- 도메인 맥락 대화를 통한 데이터 민감도 분류 예시
- REST API 위협 모델링 예시 (STRIDE + DREAD + 공격 트리 Mermaid)
- 인증 모듈 보안 코드 리뷰 예시 (JWT 검증 로직)
- 의존성 CVE 스캔 결과 예시 (패치 가용/불가용 케이스)
- OWASP ASVS L2 컴플라이언스 검증 예시
- **에스컬레이션 예시**: CVSS 9.8 SQL 인젝션 발견 시 긴급 에스컬레이션 (및 대응하는 `approval.py` 호출 이력)
- **정상 완료 예시**: 에스컬레이션 없이 전체 자동 분석 후 보안 리포트 제시
- **메타데이터 + 문서 쌍 예시**: 각 산출물 예시는 markdown 본문(`*-output.md`)과 그에 대응하는 메타데이터(`*-output.meta.yaml`)를 함께 포함하여, `phase`, `approval`, `upstream_refs`/`downstream_refs`, `cross_refs`가 채워진 실제 모습을 보여줄 것
- **리스크 수용 감사 증적 예시**: `mitigation_status: accepted`인 위협에 대해 `approval.py accept-risk`로 기록된 메타데이터 스냅샷
- **컴플라이언스 체크리스트 YAML 예시**: OWASP ASVS L2의 항목별 `requirement_id`/`status`/`evidence`가 채워진 `CR-xxx.meta.yaml`과 갭 서술이 담긴 `CR-xxx.md`의 쌍

## 핵심 설계 원칙

1. **Arch/Impl 산출물 기반 (Arch/Impl-Driven)**: 모든 보안 분석은 Arch의 4섹션과 Impl의 4섹션 산출물에 근거하며, `arch_refs`/`impl_refs`/`re_refs`로 추적성을 유지. 신뢰 경계는 `component_structure`에서, 공격 표면은 `interfaces`에서, 코드 취약점은 `implementation_map`에서 도출. 설계+구현 이중 검증으로 단일 계층의 사각지대 방지
2. **표준 기반 (Standards-Based)**: STRIDE/DREAD로 위협 분석, CWE로 취약점 분류, CVSS v3.1로 심각도 평가, OWASP Top 10으로 코드 패턴 점검, OWASP ASVS / PCI DSS / GDPR / HIPAA로 컴플라이언스 검증 — 업계 표준 참조 체계를 일관되게 사용하여 산출물의 객관성과 비교 가능성 확보
3. **적응적 깊이 (Adaptive Depth)**: Arch/Impl 모드에 연동하여 경량(OWASP Top 10 체크리스트 + 핵심 위협)/중량(전체 STRIDE + ASVS 레벨별 + CVSS 상세 평가) 모드 자동 전환. 간단한 시스템에 과잉 분석을, 복잡한 시스템에 과소 분석을 적용하지 않음
4. **추적성 (Traceability)**: 모든 보안 산출물은 `re_refs`/`arch_refs`/`impl_refs` 체인을 통해 RE까지 역추적 가능. 섹션 간 `cross_refs`(`threat_refs`/`vuln_refs`)로 위협-취약점-권고-컴플라이언스가 상호 연결되어, "왜 이 권고가 나왔는가"를 원천까지 추적 가능
5. **에스컬레이션 (Escalation)**: critical 취약점(CVSS ≥ 9.0), 규제 미준수(`hard` 제약 위반), `risk_level: critical` 위협의 미구현 대응 전략 발견 시 메인 에이전트가 분석을 중단하고 사용자에게 직접 질문. 사용자 결정 없이는 메타데이터/감사 증적이 변경되지 않음
6. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **위협 모델 / 취약점 보고서 / 보안 권고 / 컴플라이언스 리포트** 4섹션으로 고정하여, 후속 스킬(`devops`, `qa`, `impl`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
7. **메타데이터-문서 분리 및 스크립트 경유 원칙 (Metadata/Document Separation via Scripts)**: 산출물은 YAML 메타데이터 파일과 markdown 문서 파일을 분리하여 관리하고, 메타데이터(진행 상태·승인 상태·감사 증적·추적성 ref)는 에이전트가 직접 편집하지 않고 오직 `${CLAUDE_SKILL_DIR}/scripts/`의 커맨드를 통해서만 갱신. 메인 `sec`는 읽기 전용 권한을 가지며 쓰기는 별도 `sec-record` 스킬로 격리되어 사용자 명시 호출만 가능. markdown 본문은 `assets/templates/`의 사전 정의 템플릿으로 골격을 생성한 뒤 에이전트가 플레이스홀더를 채움으로써, 상태 일관성·서식 표준·감사 증적 무결성을 동시에 보장
