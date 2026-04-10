# Sec (Security Skill) 구현 계획

## 개요

Arch 스킬의 산출물(아키텍처 결정, 컴포넌트 구조, 기술 스택, 다이어그램)과 Impl 스킬의 산출물(구현 맵, 코드 구조, 구현 결정, 구현 가이드)을 입력으로 받아, **보안 취약점 분석, 위협 모델링, 보안 코드 리뷰, 표준 준수 검증**을 수행하는 스킬입니다.

Impl이 "설계를 코드로 어떻게 구현할 것인가"를 실행하고, QA가 "기능적으로 올바른가"를 검증했다면, Security는 "그 설계와 구현이 **보안적으로 안전한가**"를 검증합니다. 이 과정에서 **Arch의 컴포넌트 구조를 신뢰 경계와 공격 표면의 근거로, Impl의 구현 맵을 코드 레벨 취약점 탐지의 근거로** 사용하며, 모든 보안 산출물은 원천 아키텍처 결정과 요구사항까지 역추적 가능합니다.

위협 모델링은 아키텍처 레벨의 도메인 지식이 필요하므로 **대화형 모델**을 채택하고, 코드 레벨 감사와 컴플라이언스 검증은 선행 산출물에서 기계적으로 도출 가능하므로 **자동 실행 + 예외 에스컬레이션** 모델을 채택합니다.

### 전통적 보안 vs AI 컨텍스트 보안

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

## 목표 구조

```
security/
├── skills.yaml
├── agents/
│   ├── threat-model.md
│   ├── audit.md
│   ├── review.md
│   └── compliance.md
├── prompts/
│   ├── threat-model.md
│   ├── audit.md
│   ├── review.md
│   └── compliance.md
└── examples/
    ├── threat-model-input.md
    ├── threat-model-output.md
    ├── audit-input.md
    ├── audit-output.md
    ├── review-input.md
    ├── review-output.md
    ├── compliance-input.md
    └── compliance-output.md
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

### 1단계: 스킬 메타데이터 정의 (`skills.yaml`)

- 스킬 이름, 버전, 설명
- 에이전트 목록 및 각 에이전트의 역할 정의
- **입력 스키마**:
  - Arch 산출물 4섹션 (`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`) 소비 계약
  - Impl 산출물 4섹션 (`implementation_map`, `code_structure`, `implementation_decisions`, `implementation_guide`) 소비 계약
  - RE 간접 참조 경로 (`re_refs`, `constraint_ref` 경유)
- **출력 스키마**: 4섹션 (`threat_model`, `vulnerability_report`, `security_recommendations`, `compliance_report`) 산출물 계약
  - 각 섹션의 필드 정의 및 필수/선택 여부 명시
  - 후속 스킬 연계를 위한 출력 계약(contract) 명세
- **적응적 깊이 설정**: Arch/Impl 모드에 따른 경량/중량 모드 기준 및 전환 규칙
- 지원 보안 표준 목록 (OWASP Top 10, OWASP ASVS, CWE, CVSS, PCI DSS, GDPR, HIPAA)
- 심각도 분류 체계 (CVSS v3.1 기반)
- **에스컬레이션 조건 정의**: critical/high 취약점 발견 시, 아키텍처 레벨 보안 결함 시 사용자 에스컬레이션 조건
- 의존성 정보 (선행: `arch`, `impl`, RE 간접 참조, 후속 소비자: `devops`, `qa`, `impl`)

### 2단계: 에이전트 시스템 프롬프트 작성 (`agents/`)

#### `threat-model.md` — 위협 모델링 에이전트

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

#### `audit.md` — 보안 감사 에이전트

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

#### `review.md` — 보안 코드 리뷰 에이전트

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

#### `compliance.md` — 컴플라이언스 에이전트

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

### 3단계: 프롬프트 템플릿 작성 (`prompts/`)

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
- Chain of Thought 가이드라인
- Few-shot 예시 포함

### 4단계: 입출력 예시 작성 (`examples/`)

각 에이전트별 대표적인 입출력 쌍을 작성합니다:
- **Arch 경량 출력 → Security 경량 분석** 예시 (단일 웹 API의 OWASP Top 10 감사)
- **Arch 중량 출력 → Security 중량 분석** 예시 (마이크로서비스 아키텍처의 전체 STRIDE 위협 모델링)
- 도메인 맥락 대화를 통한 데이터 민감도 분류 예시
- REST API 위협 모델링 예시 (STRIDE + DREAD + 공격 트리)
- 인증 모듈 보안 코드 리뷰 예시 (JWT 검증 로직)
- 의존성 CVE 스캔 결과 예시 (패치 가용/불가용 케이스)
- OWASP ASVS 레벨 2 컴플라이언스 검증 예시
- **에스컬레이션 예시**: CVSS 9.8 SQL 인젝션 발견 시 긴급 에스컬레이션
- **정상 완료 예시**: 에스컬레이션 없이 전체 자동 분석 후 보안 리포트 제시

## 핵심 설계 원칙

1. **Arch/Impl 산출물 기반 (Arch/Impl-Driven)**: 모든 보안 분석은 Arch의 4섹션과 Impl의 4섹션 산출물에 근거하며, `arch_refs`/`impl_refs`/`re_refs`로 추적성을 유지. 신뢰 경계는 `component_structure`에서, 공격 표면은 `interfaces`에서, 코드 취약점은 `implementation_map`에서 도출
2. **심층 방어 (Defense in Depth)**: 단일 계층이 아닌 다계층 보안 관점. 아키텍처 레벨(threat-model) → 코드 패턴 레벨(audit) → 로직 레벨(review) → 표준 준수 레벨(compliance)의 4단계 검증으로 각 계층이 놓칠 수 있는 이슈를 후속 계층이 보완
3. **대화형 + 자동 실행 혼합 모델**: threat-model은 도메인 맥락(데이터 민감도, 위협 행위자, 규제 범위)이 필요하므로 **대화형**. audit/review/compliance는 선행 산출물에서 기계적 도출이 가능하므로 **자동 실행 + 예외 에스컬레이션**. critical 취약점과 규제 미준수만 에스컬레이션
4. **표준 기반 (Standards-Based)**: CWE로 취약점 분류, CVSS v3.1로 심각도 평가, STRIDE/DREAD로 위협 분석, OWASP ASVS로 컴플라이언스 검증 — 업계 표준 참조 체계를 일관되게 사용하여 산출물의 객관성과 비교 가능성 확보
5. **적응적 깊이 (Adaptive Depth)**: Arch/Impl 모드에 연동하여 경량(OWASP Top 10 체크리스트 + 핵심 위협)/중량(전체 STRIDE + ASVS 레벨별 + CVSS 상세 평가) 모드 자동 전환. 간단한 시스템에 과잉 분석을 적용하지 않고, 복잡한 시스템에 과소 분석을 적용하지 않음
6. **에이전트 역할 분리**: audit은 **코드 패턴 매칭 기반** 취약점 탐지 (SAST 영역), review는 **보안 로직 정확성** 검증 (수동 리뷰 영역), compliance는 **표준 항목 매핑** (감사 영역). 세 에이전트의 관점이 다르므로 상호 보완적이며, 중복이 아닌 다층 방어를 구현
7. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **위협 모델 / 취약점 보고서 / 보안 권고 / 컴플라이언스 리포트** 4섹션으로 고정하여, 후속 스킬(`devops`, `qa`, `impl`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
