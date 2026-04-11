# QA (Quality Assurance) Skill 구현 계획

## 개요

RE 스킬의 산출물(요구사항 명세, 제약 조건, 품질 속성 우선순위), Arch 스킬의 산출물(아키텍처 결정, 컴포넌트 구조, 기술 스택, 다이어그램), Impl 스킬의 산출물(구현 맵, 코드 구조, 구현 결정, 구현 가이드)을 입력으로 받아, **테스트 전략 수립, 테스트 코드 생성, 품질 검증**을 수행하는 스킬입니다.

Impl이 "설계를 코드로 어떻게 구현할 것인가"를 실행했다면, QA는 "그 구현이 요구사항을 충족하는지 어떻게 검증할 것인가"를 결정하고 실행합니다. 이 과정에서 **RE의 acceptance_criteria를 테스트 케이스의 근거로, Arch의 컴포넌트 경계를 테스트 범위의 근거로, Impl의 구현 맵을 테스트 대상의 근거로** 사용하며, 모든 테스트 산출물은 원천 요구사항까지 역추적 가능합니다. 선행 산출물에서 전략과 범위를 기계적으로 도출하고, **Must 요구사항의 해소 불가능한 커버리지 갭이 발견된 경우에만 사용자에게 에스컬레이션**합니다.

### 전통적 QA vs AI 컨텍스트 QA

| 구분 | 전통적 QA | AI 컨텍스트 QA |
|------|-----------|----------------|
| 수행자 | QA 전담 팀 (테스터, QA 엔지니어) | 개발자가 AI에게 테스트 전략 수립과 생성을 위임 |
| 입력 | 테스트 계획서, 추적 매트릭스 (별도 작성) | **RE/Arch/Impl 스킬의 구조화된 산출물** (추적성 내장) |
| 테스트 설계 | 테스터의 경험과 도메인 지식에 의존 | **RE acceptance_criteria 기반 체계적 도출** + AI 경계값/예외 분석 |
| NFR 검증 | 성능 테스트 팀이 별도로 진행 | **RE quality_attribute_priorities.metric을 테스트 시나리오로 직접 변환** |
| 추적성 | RTM(Requirements Traceability Matrix)을 수동 관리 | **re_refs/arch_refs/impl_refs로 자동 추적** |
| 커버리지 기준 | 코드 커버리지 (라인/분기) 위주 | **요구사항 커버리지 + 코드 커버리지** 이중 기준 |
| 산출물 | 테스트 결과 리포트 | **후속 스킬이 소비 가능한 구조화된 품질 산출물** |

## 선행 스킬 산출물 소비 계약

QA 스킬은 RE, Arch, Impl 세 스킬의 산출물을 모두 소비하는 3-Way 계약을 가집니다. 각 매핑의 상세 파싱 규칙은 `references/contracts/`에 분리하여 보관합니다.

### RE 산출물 소비 매핑

| RE 산출물 섹션 | 주요 필드 | QA에서의 소비 방법 |
|---------------|-----------|-------------------|
| **요구사항 명세** | `id`, `category`, `title`, `acceptance_criteria`, `priority`, `dependencies` | `acceptance_criteria`를 테스트 케이스 도출의 핵심 근거로 사용. `priority`(MoSCoW)로 테스트 우선순위 결정 — Must는 반드시 테스트, Won't는 제외. `dependencies`로 통합 테스트 시나리오 도출 |
| **제약 조건** | `id`, `type`, `flexibility`, `rationale` | `type: regulatory` 제약은 컴플라이언스 테스트 대상으로 분류. `type: technical` 제약(예: 특정 브라우저 지원)은 테스트 환경 매트릭스에 반영. `flexibility: hard` 제약은 필수 검증 대상 |
| **품질 속성 우선순위** | `attribute`, `priority`, `metric`, `trade_off_notes` | `metric`("응답시간 < 200ms", "99.9% 가용성")을 NFR 테스트 시나리오로 직접 변환. `priority` 순서로 NFR 테스트 투자 우선순위 결정. `trade_off_notes`로 테스트 시 허용 범위 판단 |

### Arch 산출물 소비 매핑

| Arch 산출물 섹션 | 주요 필드 | QA에서의 소비 방법 |
|-----------------|-----------|-------------------|
| **아키텍처 결정** | `id`, `decision`, `trade_offs`, `re_refs` | `decision`으로 아키텍처 패턴별 테스트 전략 결정 (예: 이벤트 드리븐 → 비동기 메시지 테스트, 마이크로서비스 → 계약 테스트). `re_refs`로 RE까지 추적성 유지 |
| **컴포넌트 구조** | `id`, `name`, `type`, `interfaces`, `dependencies` | `interfaces`로 통합 테스트 경계 결정 — 컴포넌트 간 인터페이스가 통합 테스트 대상. `dependencies`로 테스트 더블(mock/stub) 전략 결정. `type`에 따라 테스트 방식 분기 (service → API 테스트, store → 데이터 무결성 테스트) |
| **기술 스택** | `category`, `choice`, `decision_ref` | `choice`로 테스트 프레임워크 선택 (TypeScript → Jest/Vitest, Python → pytest, Go → testing). 기술별 테스트 관용구(idiom) 적용 |
| **다이어그램** | `type`, `code` | `sequence` 다이어그램으로 주요 흐름의 E2E 테스트 시나리오 도출. `c4-container`로 통합 테스트 범위 시각 확인 |

### Impl 산출물 소비 매핑

| Impl 산출물 섹션 | 주요 필드 | QA에서의 소비 방법 |
|-----------------|-----------|-------------------|
| **구현 맵** | `id`, `component_ref`, `module_path`, `entry_point`, `interfaces_implemented`, `re_refs` | `module_path`로 테스트 파일 배치 위치 결정. `interfaces_implemented`로 인터페이스 계약 테스트 대상 식별. `re_refs`로 RE 요구사항까지 역추적하여 요구사항 커버리지 매트릭스 생성 |
| **코드 구조** | `directory_layout`, `module_dependencies`, `external_dependencies` | `directory_layout`으로 테스트 디렉토리 구조 결정 (미러링 또는 co-location). `module_dependencies`로 모듈 간 의존성 기반 통합 테스트 순서 결정. `external_dependencies`로 외부 의존성 모킹 대상 식별 |
| **구현 결정** | `id`, `decision`, `pattern_applied`, `arch_refs`, `re_refs` | `pattern_applied`로 패턴별 테스트 전략 결정 (예: Repository 패턴 → 인메모리 구현으로 단위 테스트, Strategy 패턴 → 각 전략별 테스트). `arch_refs`/`re_refs`로 추적성 체인 완성 |
| **구현 가이드** | `setup_steps`, `build_commands`, `run_commands`, `conventions` | `setup_steps`로 테스트 환경 설정 절차 도출. `conventions`로 테스트 코드 컨벤션 일관성 유지 |

### 추적성 체인 (RE → Arch → Impl → QA)

QA는 RE → Arch → Impl → QA로 이어지는 추적성 체인의 최종 검증 지점이며, 이 체인의 무결성을 시각화·강제하는 책임을 가집니다.

```
RE:spec 산출물                    Arch 산출물              Impl 산출물              QA 산출물
┌──────────────┐            ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ FR-001       │───re_refs──│ COMP-001     │──comp──│ IM-001       │──impl──│ TS-001       │
│  acceptance  │            │  interfaces  │  _ref  │  module_path │  _ref  │  test_cases  │
│  _criteria   │            │  dependencies│        │  interfaces  │        │  re_refs     │
│              │            │              │        │  _implemented│        │  arch_refs   │
│ NFR-001      │───re_refs──│ AD-001       │──arch──│ IDR-001      │──impl──│  impl_refs   │
│  (성능)      │            │  decision    │  _refs │  pattern     │  _ref  │              │
│              │            │              │        │  _applied    │        │              │
│ QA:perf      │───re_refs──│ AD-001       │        │              │        │ NFR-TS-001   │
│  metric:     │            │  re_refs     │        │              │        │  metric_ref  │
│  "<200ms"    │            │              │        │              │        │  scenario    │
│              │            │              │        │              │        │  threshold   │
│ CON-001      │───re_refs──│ COMP-001     │        │ IM-001       │        │ ENV-001      │
│  (regulatory)│            │              │        │              │        │  constraint  │
│              │            │              │        │              │        │  _ref        │
└──────────────┘            └──────────────┘        └──────────────┘        └──────────────┘
```

이 체인은 `references/traceability.md`에 상세 명세하며, RTM 산출물에서 1급 시민으로 보존됩니다.

### 적응적 깊이

Impl 모드(→ Arch 모드 → RE 출력 밀도)에 연동하여 QA 산출물 수준을 자동 조절합니다. 판별 기준 상세는 `references/adaptive-depth.md`에 분리합니다.

| Impl 모드 | 판별 기준 | QA 모드 | 산출물 수준 |
|-----------|-----------|---------|------------|
| 경량 | 단일 프로젝트 스캐폴딩 수준 | 경량 | 핵심 기능 단위 테스트 + acceptance_criteria 기반 검증 체크리스트 + 인라인 테스트 가이드 |
| 중량 | 멀티 모듈 프로젝트 수준 | 중량 | 테스트 피라미드 전체 전략 + 컴포넌트별 테스트 스위트 + NFR 테스트 시나리오 + 요구사항 추적 매트릭스(RTM) + 품질 게이트 정의 |

## 최종 산출물 구조

QA 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. 테스트 전략과 테스트 코드, 품질 검증까지를 범위로 하며, 배포 파이프라인의 품질 게이트 설정은 후속 스킬(`deployment`)의 영역입니다.

### 1. 테스트 전략 (Test Strategy)

테스트 범위, 접근 방법, 우선순위를 구조화합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `TSTR-001`) |
| `scope` | 테스트 범위 정의 (포함/제외 대상, 근거) |
| `pyramid` | 테스트 피라미드 비율 (단위/통합/E2E 비율 및 근거) |
| `priority_matrix` | 리스크 기반 테스트 우선순위 매트릭스 (RE `priority` 연동) |
| `nfr_test_plan` | NFR 테스트 계획 (RE `quality_attribute_priorities.metric` 기반) |
| `environment_matrix` | 테스트 환경 매트릭스 (RE `constraints` 기반) |
| `test_double_strategy` | 테스트 더블 전략 (Arch `component_structure.dependencies` 기반) |
| `re_refs` | 근거가 된 RE 산출물 ID 목록 |
| `arch_refs` | 근거가 된 Arch 산출물 ID 목록 |

### 2. 테스트 스위트 (Test Suite)

생성된 테스트 케이스와 테스트 코드를 구조화합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `TS-001`) |
| `type` | 테스트 유형 (`unit` / `integration` / `e2e` / `contract` / `nfr`) |
| `title` | 테스트 스위트 제목 |
| `target_module` | 테스트 대상 모듈 경로 (Impl `implementation_map.module_path` 참조) |
| `test_cases` | 테스트 케이스 목록 (아래 하위 구조) |
| `framework` | 사용 테스트 프레임워크 (Arch `technology_stack` 연동) |
| `re_refs` | 검증 대상 RE 요구사항 ID 목록 (`FR-001`, `NFR-001` 등) |
| `arch_refs` | 관련 Arch 산출물 ID 목록 (`COMP-001`, `AD-001` 등) |
| `impl_refs` | 관련 Impl 산출물 ID 목록 (`IM-001`, `IDR-001` 등) |

테스트 케이스 하위 구조:

| 필드 | 설명 |
|------|------|
| `case_id` | 케이스 식별자 (예: `TS-001-C01`) |
| `description` | 테스트 설명 |
| `given` | 사전 조건 |
| `when` | 실행 조건 |
| `then` | 기대 결과 |
| `technique` | 적용 기법 (`boundary_value` / `equivalence_partition` / `decision_table` / `state_transition` / `property_based`) |
| `acceptance_criteria_ref` | 검증 대상 acceptance_criteria (RE 직접 참조) |

### 3. 요구사항 추적 매트릭스 (RTM)

RE 요구사항 → Arch 컴포넌트 → Impl 모듈 → QA 테스트 간의 추적성을 보장합니다. RTM은 본질적으로 구조화 테이블 데이터이므로, 메타데이터 파일(YAML)에 1급 시민으로 저장됩니다.

| 필드 | 설명 |
|------|------|
| `re_id` | RE 요구사항 ID (`FR-001`, `NFR-001`) |
| `re_title` | 요구사항 제목 |
| `re_priority` | 요구사항 우선순위 (MoSCoW) |
| `arch_refs` | 매핑된 Arch 컴포넌트/결정 ID 목록 |
| `impl_refs` | 매핑된 Impl 모듈/결정 ID 목록 |
| `test_refs` | 매핑된 테스트 스위트/케이스 ID 목록 |
| `coverage_status` | 커버리지 상태 (`covered` / `partial` / `uncovered`) |
| `gap_description` | `uncovered` 또는 `partial`인 경우 누락 사유 |

### 4. 품질 리포트 (Quality Report)

테스트 실행 결과와 품질 지표를 구조화합니다.

| 필드 | 설명 |
|------|------|
| `code_coverage` | 코드 커버리지 (라인, 분기, 경로 — 모듈별) |
| `requirements_coverage` | 요구사항 커버리지 (RTM 기반 — covered/partial/uncovered 비율) |
| `nfr_results` | NFR 테스트 결과 (RE `metric` 대비 실측치) |
| `quality_gate` | 품질 게이트 판정 (`pass` / `fail` — 기준과 실측 포함) |
| `risk_items` | 잔여 리스크 목록 (uncovered 요구사항, 실패 테스트, 미달 NFR) |
| `recommendations` | 개선 권고 사항 |
| `re_refs` | 참조된 RE 산출물 ID 목록 |

품질 게이트 `pass` → 메타데이터 `approval.state: approved`, `fail` → `rejected`(또는 Must 갭 해소 불가 시 `escalated`)로 자동 전이되며, 이 상태가 후속 스킬(`deployment`)의 게이트 입력으로 사용됩니다.

### 산출물 파일 구성: 메타데이터 + 문서 분리

위 4섹션 산출물은 **메타데이터 파일과 문서 markdown 파일을 분리**하여 저장합니다. 메타데이터는 구조화된 상태/추적 정보를 담고, markdown은 사람이 읽을 서술형 본문을 담습니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 파일 | **YAML** (`*.meta.yaml`) | 진행 상태, 승인 상태, 추적성(refs), 4섹션의 구조화 필드(특히 RTM 행) 저장. 스크립트가 읽고 쓰는 단일 진실 공급원(SSoT) |
| 문서 파일 | Markdown (`*.md`) | 테스트 전략 서술, Given-When-Then 케이스, RTM 사람용 뷰, 품질 리포트 해석 본문 |

**YAML을 채택한 이유**:

- **주석 지원**: RTM의 갭 사유나 NFR 결정 근거를 인라인 주석으로 남길 수 있어 사람이 작성/편집 시 맥락 전달이 용이
- **사람이 읽기 쉬움**: 들여쓰기 기반 구조로 JSON 대비 시각적 가독성이 높음 — RE/Arch/Impl/QA 산출물처럼 사용자가 직접 검토하는 문서에 적합
- **스크립트 파싱 용이**: PyYAML/ruamel.yaml로 손쉽게 로드/덤프 가능하며, 키 순서 보존도 지원

### 메타데이터 스키마 (공통 필드)

각 산출물 메타데이터 파일은 4섹션의 구조화 필드 외에 다음 공통 필드를 포함합니다.

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 고유 식별자 (예: `QA-strategy-001`, `QA-suite-001`, `RTM`, `QR-001`) |
| `phase` | 현재 단계 (`draft` / `in_review` / `revising` / `approved` / `superseded`) |
| `progress` | 진행률 정보 (`section_completed`, `section_total`, `percent`) |
| `approval.state` | 승인 상태 (`pending` / `approved` / `rejected` / `changes_requested` / `escalated`) |
| `approval.approver` | 승인자 식별자 (사용자명/역할, 자동 승인의 경우 `auto:gate-evaluator`) |
| `approval.approved_at` | 승인 시각 (ISO 8601) |
| `approval.notes` | 승인/반려 코멘트, 에스컬레이션 메모 |
| `upstream_refs` | 상위 산출물 ID 목록 (RE의 `FR-001`/`NFR-001`/`CON-001`, Arch의 `AD-001`/`COMP-001`, Impl의 `IM-001`/`IDR-001`) |
| `downstream_refs` | 이 산출물을 소비하는 후속 산출물 ID 목록 (`deployment`, `operation`, `security` 등) |
| `document_path` | 짝을 이루는 markdown 문서의 상대 경로 |
| `updated_at` | 최종 수정 시각 |

### 스크립트 기반 메타데이터 조작 (필수)

워크플로우 단계는 **YAML 메타데이터 파일을 직접 편집하지 않습니다**. 모든 상태 갱신은 `${SKILL_DIR}/scripts/artifact.py` 단일 진입점의 서브커맨드를 통해서만 수행하며, 이는 다음을 보장합니다.

- 스키마 검증 (잘못된 phase 값, 누락 필드 차단)
- `updated_at` 등 자동 필드의 일관된 갱신
- 추적성 ref의 양방향 무결성 (upstream/downstream 동기화)
- 승인 상태 전이 규칙 적용 (예: `draft → approved` 직행 금지)
- 품질 게이트 평가 결과의 `approval.state` 자동 반영

핵심 스크립트(예시):

| 스크립트 커맨드 | 용도 |
|----------------|------|
| `python ${SKILL_DIR}/scripts/artifact.py init --kind <kind> --id <id>` | 메타데이터 + markdown 템플릿 쌍을 새로 생성 (`assets/templates/`에서 복사) |
| `python ${SKILL_DIR}/scripts/artifact.py set-phase --id <id> --phase <phase>` | 진행 단계 전이 |
| `python ${SKILL_DIR}/scripts/artifact.py set-progress --id <id> --completed N --total M` | 진행률 갱신 |
| `python ${SKILL_DIR}/scripts/artifact.py approve --id <id> --approver <name> [--notes ...]` | 승인 상태 전이 |
| `python ${SKILL_DIR}/scripts/artifact.py link --id <id> --upstream <ref>` / `--downstream <ref>` | 추적성 ref 추가 |
| `python ${SKILL_DIR}/scripts/artifact.py rtm-upsert --re-id <id> --test-refs <...> --status <covered\|partial\|uncovered>` | RTM 행 삽입/갱신 |
| `python ${SKILL_DIR}/scripts/artifact.py rtm-gap-report` | uncovered/partial 갭을 MoSCoW 우선순위별로 집계 |
| `python ${SKILL_DIR}/scripts/artifact.py gate-evaluate --report <id>` | 품질 게이트 평가 후 `approval.state` 자동 전이 |
| `python ${SKILL_DIR}/scripts/artifact.py show --id <id>` | 메타데이터 조회 (사람이 읽기 좋은 형태) |
| `python ${SKILL_DIR}/scripts/artifact.py validate [<id>]` | 스키마/추적성 검증 |

### 문서 템플릿 (`assets/templates/`)

markdown 문서 또한 자유 양식이 아니라, `assets/templates/` 디렉토리에 4섹션별 템플릿을 사전에 정의합니다. `scripts/artifact.py init` 실행 시 해당 템플릿이 복사되어 **섹션 헤더, 플레이스홀더, RE/Arch/Impl 참조 슬롯이 채워진 골격**이 생성되며, 워크플로우 단계는 이 골격 안의 플레이스홀더를 채우는 방식으로 본문을 작성합니다.

| 템플릿 파일 | 대상 섹션 |
|------------|----------|
| `assets/templates/test-strategy.md.tmpl` | 테스트 전략 (범위·피라미드·NFR 계획 서술) |
| `assets/templates/test-strategy.meta.yaml.tmpl` | 테스트 전략 메타데이터 초기 골격 |
| `assets/templates/test-suite.md.tmpl` | 테스트 스위트 (Given-When-Then 케이스, 설계 기법) |
| `assets/templates/test-suite.meta.yaml.tmpl` | 테스트 스위트 메타데이터 초기 골격 |
| `assets/templates/rtm.md.tmpl` | RTM 사람용 뷰 (메타데이터에서 렌더되는 요약 + 갭 해설) |
| `assets/templates/rtm.meta.yaml.tmpl` | RTM 구조화 데이터(행 배열) 초기 골격 |
| `assets/templates/quality-report.md.tmpl` | 품질 리포트 (실측 해석, 잔여 리스크, 권고) |
| `assets/templates/quality-report.meta.yaml.tmpl` | 품질 리포트 메타데이터(게이트 기준·실측·판정) 초기 골격 |

### 후속 스킬 연계

```
qa 산출물 구조:
┌─────────────────────────────────────────┐
│  테스트 전략 (Test Strategy)             │──→ management:plan (테스트 일정/리소스)
│  - TSTR-001: 테스트 피라미드 비율        │──→ deployment:strategy (배포 전 품질 게이트)
│  - nfr_test_plan                       │──→ operation:slo (SLO 검증 기준)
├─────────────────────────────────────────┤
│  테스트 스위트 (Test Suite)              │──→ impl:refactor (테스트 실패 시 리팩토링 대상)
│  - TS-001: unit (src/auth/)            │──→ security:scan (보안 테스트 케이스 연계)
│  - TS-002: integration (COMP-001↔002)  │──→ deployment:strategy (테스트 자동화 파이프라인)
├─────────────────────────────────────────┤
│  요구사항 추적 매트릭스 (RTM)            │──→ management:plan (커버리지 갭 = 리스크)
│  - FR-001 → COMP-001 → IM-001 → TS-001│──→ re:review (추적성 검증 피드백)
│  - coverage_status: covered/uncovered  │
├─────────────────────────────────────────┤
│  품질 리포트 (Quality Report)           │──→ management:plan (품질 현황 대시보드)
│  - code_coverage, req_coverage         │──→ deployment:strategy (배포 가/부 판정)
│  - nfr_results                         │──→ operation:slo (NFR 실측치 → SLO 기준선)
│  - quality_gate: pass/fail             │──→ operation:runbook (잔여 리스크 운영 대응)
└─────────────────────────────────────────┘
```

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점은 `qa/SKILL.md` 이며, `skills.yaml`, `agents/`, `prompts/` 디렉토리는 사용하지 않습니다. 상세 행동 규칙과 단계별 가이드는 `references/`에, 템플릿은 `assets/`에 분리합니다.

```
qa/
├── SKILL.md                              # 필수 진입점 (YAML frontmatter + 4단계 워크플로우 요약, 500줄 이내)
├── scripts/
│   └── artifact.py                       # 메타데이터 init/set-phase/set-progress/approve/link/rtm-upsert/rtm-gap-report/gate-evaluate/show/validate
├── assets/
│   └── templates/
│       ├── test-strategy.md.tmpl
│       ├── test-strategy.meta.yaml.tmpl
│       ├── test-suite.md.tmpl
│       ├── test-suite.meta.yaml.tmpl
│       ├── rtm.md.tmpl
│       ├── rtm.meta.yaml.tmpl
│       ├── quality-report.md.tmpl
│       └── quality-report.meta.yaml.tmpl
└── references/
    ├── workflow/
    │   ├── strategy.md                   # 전략 단계 상세 행동 규칙 (on-demand 로드)
    │   ├── generate.md                   # 테스트 생성 단계 상세 행동 규칙
    │   ├── review.md                     # 리뷰 단계 상세 행동 규칙
    │   └── report.md                     # 품질 리포트 단계 상세 행동 규칙
    ├── contracts/
    │   ├── re-input-contract.md          # RE 3섹션 소비 계약
    │   ├── arch-input-contract.md        # Arch 4섹션 소비 계약
    │   ├── impl-input-contract.md        # Impl 4섹션 소비 계약
    │   └── downstream-contract.md        # deployment/operation/management/security 소비 계약
    ├── schemas/
    │   ├── meta-schema.md                # 메타데이터 공통 필드 설명
    │   └── section-schemas.md            # 4섹션 필드 명세 (RTM 행 구조 포함)
    ├── adaptive-depth.md                 # 경량/중량 분기 규칙
    ├── traceability.md                   # RE→Arch→Impl→QA 추적 체인 명세
    └── examples/
        ├── light/
        │   ├── strategy-input.md
        │   ├── strategy-output.md
        │   └── strategy-output.meta.yaml
        └── heavy/
            ├── strategy-output.md
            ├── strategy-output.meta.yaml
            ├── suite-output.md
            ├── suite-output.meta.yaml
            ├── rtm-output.md
            ├── rtm-output.meta.yaml
            ├── report-output.md
            └── report-output.meta.yaml
```

요점:
- `SKILL.md`가 유일한 필수 진입점이며, 4개의 워크플로우 단계(strategy/generate/review/report)는 **동일 SKILL.md 안에 짧게 요약**하고, 상세 규칙은 `references/workflow/*.md`로 분리하여 **on-demand 로드**합니다.
- `templates/` 대신 표준 명칭인 `assets/templates/`, `examples/` 대신 `references/examples/`를 사용합니다.
- `skills.yaml`, `agents/`, `prompts/`는 폐기합니다.

## 워크플로우 단계 (SKILL.md 내부 단일 진입점)

표준 스킬 모델을 따르기 위해, 기존에 "4개의 내부 에이전트"로 구상했던 strategy/generate/review/report는 **별도의 시스템 프롬프트 파일이 아니라**, SKILL.md가 순차적으로 수행하는 **4개의 워크플로우 단계**로 재정의합니다. 각 단계의 상세 행동 규칙은 `references/workflow/*.md`에 분리되어 필요 시점에 Read로 로드됩니다.

```
RE:spec 산출물 + Arch 산출물 + Impl 산출물
    │
    ▼
[Stage 1] strategy ─────────────────────────┐
    │  references/workflow/strategy.md 로드 │
    │  (선행 산출물 분석 → MoSCoW 기반       │
    │   테스트 범위 자동 도출 → 전략 확정)    │
    │                                       │
    ▼                                       │
[Stage 2] generate                          │
    │  references/workflow/generate.md 로드 │
    │  (strategy 기반 테스트 코드 일괄 생성  │
    │   → acceptance_criteria 기계적 변환)   │
    │                                       │
    ▼                                       │
[Stage 3] review ◄──────────────────────────┘
    │  references/workflow/review.md 로드
    │  (생성된 테스트 완전성·강도·추적성 리뷰
    │   + RTM 생성 + 커버리지 갭 자동 분류)
    │
    ├── Should/Could 갭 ──→ 자동 수용 (리스크로 기록)
    ├── Must 갭(자동 보완 가능) ──→ generate 재호출
    └── Must 갭(해소 불가) ──→ 사용자 에스컬레이션
    │
    ▼
[Stage 4] report
    references/workflow/report.md 로드
    (품질 리포트 + 게이트 판정 + 잔여 리스크)
```

### `references/workflow/strategy.md` — 전략 수립 상세 규칙

- **역할**: RE/Arch/Impl 산출물을 분석하여 테스트 전략을 자동으로 수립
- **핵심 역량**:
  - **RE 산출물 해석 → 테스트 범위 자동 도출**:
    - `requirements_spec`의 모든 FR/NFR을 테스트 대상으로 등록
    - `acceptance_criteria`의 개수와 복잡도로 테스트 케이스 볼륨 추정
    - `priority`(MoSCoW)로 테스트 우선순위 매트릭스 자동 생성 — Must는 반드시 커버, Should는 가급적 커버, Could/Won't는 자동으로 리스크 수용
    - `constraints`의 `type: regulatory`를 컴플라이언스 테스트 대상으로 분류
    - `quality_attribute_priorities.metric`을 NFR 테스트 계획으로 변환
  - **Arch 산출물 해석 → 테스트 구조 결정**:
    - `component_structure`의 `interfaces`와 `dependencies`로 통합 테스트 경계 결정
    - `architecture_decisions`의 `decision`으로 패턴별 전략 결정 (마이크로서비스 → 계약 테스트, 이벤트 드리븐 → 비동기 메시지 테스트, 레이어드 → 레이어 간 통합 테스트)
    - `technology_stack`으로 테스트 프레임워크 선택
  - **Impl 산출물 해석 → 테스트 대상 매핑**:
    - `implementation_map`으로 테스트 파일 배치 결정 (모듈 경로 미러링)
    - `code_structure.module_dependencies`로 통합 테스트 순서 결정
    - `implementation_decisions.pattern_applied`로 패턴별 전략 결정
  - **테스트 피라미드 비율 자동 결정**: 아키텍처 패턴과 컴포넌트 구조에서 자동 도출
  - **테스트 더블 전략 수립**: 컴포넌트 의존 관계 기반으로 mock/stub/fake/spy 사용 전략 자동 결정
  - **테스트 환경 매트릭스**: RE 제약 조건 기반 환경 조합 자동 결정
  - **품질 게이트 기준 자동 설정**: 합리적 기본값(코드 커버리지 80%, Must 요구사항 커버리지 100%, NFR 메트릭은 RE `metric` 수치)
- **입력**: RE `spec` 산출물 + Arch 산출물 + Impl 산출물
- **출력**: 테스트 전략, 테스트 더블 전략, 테스트 환경 매트릭스, 품질 게이트 기준
- **상호작용 모델**: 선행 산출물 분석 → 전략 자동 수립 → generate 단계로 직접 전이. 사용자 개입 없음

### `references/workflow/generate.md` — 테스트 생성 상세 규칙

- **역할**: 확정된 테스트 전략 기반으로 테스트 코드를 생성하되, 모든 테스트가 RE 요구사항까지 추적 가능하도록 생성
- **핵심 역량**:
  - **acceptance_criteria → 테스트 케이스 변환**: RE의 각 `acceptance_criteria`를 하나 이상의 테스트 케이스로 변환. `acceptance_criteria_ref`로 원천 추적 유지
  - **테스트 설계 기법 적용**: 경계값 분석, 동등 분할, 결정 테이블, 상태 전이, 프로퍼티 기반 테스트
  - **테스트 유형별 생성**:
    - **단위 테스트**: Impl 모듈 단위, 개별 함수/메서드 검증. 테스트 더블 전략 적용
    - **통합 테스트**: Arch `component_structure.interfaces` 기반 컴포넌트 간 검증
    - **E2E 테스트**: Arch `sequence` 다이어그램의 주요 흐름을 시나리오로 변환
    - **계약 테스트**: 마이크로서비스 아키텍처 시 컴포넌트 간 API 계약 검증
    - **NFR 테스트**: RE `quality_attribute_priorities.metric` 기반 성능/부하/스트레스 시나리오
  - **AAA 패턴 준수**: Arrange-Act-Assert 패턴으로 일관된 구조
  - **테스트 코드 컨벤션**: Impl `conventions`에 맞춘 네이밍, 구조 일관성
  - **일괄 생성**: 전체 테스트를 strategy 기반으로 일괄 생성
- **입력**: 테스트 전략 + 테스트 대상 코드 + Impl 산출물 + RE 산출물
- **출력**: 테스트 스위트 목록, 생성된 테스트 코드 파일들, 각 케이스의 `re_refs`/`arch_refs`/`impl_refs`
- **상호작용 모델**: strategy 출력 수신 → 일괄 생성 → review 단계로 직접 전이. 사용자 개입 없음

### `references/workflow/review.md` — 커버리지 검증 상세 규칙

- **역할**: 생성된 테스트의 완전성·강도·추적성을 리뷰하고 RTM을 생성하며, 갭을 자동 분류
- **핵심 역량**:
  - **요구사항 커버리지 검증 (RTM 생성)**:
    - RE의 모든 FR/NFR에 대해 대응 테스트 케이스 존재 여부 확인
    - 각 `acceptance_criteria`가 최소 하나의 테스트 케이스에 매핑되는지 확인
    - `covered`/`partial`/`uncovered` 상태 판정 후 갭 사유 기록
    - Must 요구사항 중 `uncovered`가 있으면 필수 보완 플래그
  - **코드 커버리지 분석**: 라인/분기/경로 커버리지(모듈별), 낮은 모듈과 담당 RE 요구사항 매핑
  - **테스트 강도 평가**: 뮤테이션 관점 평가, 경계값/예외 누락 식별, 약한 assertion 탐지
  - **테스트 코드 품질 리뷰**: 테스트 독립성 위반, flaky 패턴(시간/순서/외부 의존), 유지보수성·가독성
  - **NFR 테스트 검증**: RE `metric` 대비 NFR 시나리오의 충분성 확인
  - **추적성 체인 검증**: 테스트 → Impl → Arch → RE 역추적이 모든 테스트에서 가능한지 확인
- **입력**: 생성된 테스트 코드 + 테스트 전략 + RE/Arch/Impl 산출물
- **출력**: 요구사항 추적 매트릭스(RTM), 테스트 리뷰 리포트, 커버리지 갭 자동 분류
- **상호작용 모델**: 자동 리뷰 → Should/Could/Won't 갭은 자동 수용 → 자동 보완 가능한 Must 갭은 generate 재호출 → 해소 불가 Must 갭만 사용자 에스컬레이션

### `references/workflow/report.md` — 품질 리포트 상세 규칙

- **역할**: 테스트 실행 결과를 수집하고 RE 메트릭 대비 품질 현황을 종합 리포트로 생성
- **핵심 역량**:
  - **코드 커버리지 집계**: 모듈별/컴포넌트별/전체
  - **요구사항 커버리지 집계**: RTM 기반 covered/partial/uncovered 비율
  - **NFR 측정 결과 대비 분석**: RE `quality_attribute_priorities.metric` 대비 실측치 비교 (예: `metric: "응답시간 < 200ms"` → 실측 150ms → Pass)
  - **품질 게이트 판정**: strategy에서 정한 기준 대비 pass/fail 판정. `gate-evaluate` 호출로 메타데이터 `approval.state` 자동 전이
  - **잔여 리스크 식별**: uncovered 요구사항, 실패 테스트, 미달 NFR을 잔여 리스크로 분류
  - **개선 권고**: 리스크 수준에 따른 우선순위화된 개선 권고
- **입력**: 테스트 실행 결과 + RTM + 테스트 전략(품질 게이트 기준) + RE 산출물(metric 기준)
- **출력**: 품질 리포트 (코드 커버리지, 요구사항 커버리지, NFR 결과, 게이트 판정, 잔여 리스크, 권고)
- **상호작용 모델**: 자동 생성 → 최종 품질 리포트를 사용자에게 제시 (QA 파이프라인의 정규 사용자 접점). 후속 스킬(`deployment`)로 게이트 결과 전달

## 구현 단계

### 1단계: `SKILL.md` 작성 (필수 진입점 + frontmatter)

표준에서 메타데이터의 단일 출처는 `qa/SKILL.md`의 YAML frontmatter입니다. `skills.yaml`은 표준 사양에 존재하지 않으므로 사용하지 않습니다. Claude Code Skill 표준에 따라 frontmatter는 `name`과 `description`만 필수로 두고, 나머지 옵션 필드는 기본 동작으로 스킬 목적을 달성할 수 없음이 입증된 경우에만 추가합니다.

**권장 frontmatter 초안**:

```yaml
---
name: qa
description: RE/Arch/Impl 산출물을 입력받아 테스트 전략·테스트 스위트·요구사항 추적 매트릭스(RTM)·품질 리포트 4섹션을 생성하고, scripts/artifact.py로 메타데이터·추적성·품질 게이트를 관리한다. 선행 산출물이 준비된 후 또는 테스트 자동 생성·요구사항 커버리지 검증·품질 게이트 판정이 필요할 때 사용.
---
```

**설계 원칙**:

- **`name`**: 스킬 디렉토리명과 일치시켜 `qa`로 고정합니다.
- **`description` 작성 규칙**: 첫 200자 안에 *무엇을 하는가*("RE/Arch/Impl 3-Way 산출물 → QA 4섹션")와 *언제 사용하는가*("선행 산출물 준비 후 / 테스트 자동 생성 / 요구사항 커버리지 검증 / 품질 게이트 판정 시")를 포함합니다.
- 그 외 옵션 필드는 기본값으로 두며, 표준 동작으로 스킬이 동작 불가능한 경우에만 도입합니다.

**SKILL.md 본문 구성 (500줄 이내)**:

1. 스킬 개요 (RE 3섹션 + Arch 4섹션 + Impl 4섹션 → QA 4섹션)
2. 입력/출력 계약 요약 (상세는 `references/contracts/*.md`로 분리)
3. 적응적 깊이 분기 로직 (Impl 모드 판별 → 경량/중량 결정)
4. 4단계 워크플로우 요약 (strategy → generate → review → report)
   - 각 단계는 **상세 규칙을 `references/workflow/<stage>.md`에서 로드**
   - 예: "review 진입 시 `${SKILL_DIR}/references/workflow/review.md`를 Read로 로드한 뒤 지시를 따른다"
5. 스크립트 호출 규약: 모든 메타데이터 조작은 `${SKILL_DIR}/scripts/artifact.py`를 통해서만 수행
6. 시작 시 현재 상태 주입: SKILL.md 상단에서 `` !`python ${SKILL_DIR}/scripts/artifact.py validate` ``, `` !`python ${SKILL_DIR}/scripts/artifact.py rtm-gap-report` ``로 RTM·추적성 무결성을 동적 컨텍스트로 주입
7. 의존성 정보(선행: `re`/`arch`/`impl`, 후속: `deployment`/`operation`/`management`/`security`)는 frontmatter가 아니라 본문 또는 `references/contracts/downstream-contract.md`에 기술

**치환자 활용**: 모든 스크립트 경로는 `${SKILL_DIR}/scripts/artifact.py`로 작성하여 사용자 호출 위치에 무관하게 동작하도록 합니다. 사용자 인자는 `$ARGUMENTS`로 받아 서브커맨드 인자로 전달합니다.

**문서 길이 관리**: SKILL.md는 500줄 이내를 유지하며, 초과 위험 내용은 모두 `references/` 하위로 분리합니다.

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

기존 PLAN의 "4개 내부 에이전트(strategy/generate/review/report)" 개념은 표준 스킬 모델과 직접 매핑되지 않습니다. 대신 각 단계의 상세 행동 규칙을 `references/workflow/`에 markdown 파일로 분리하고, SKILL.md가 단계 진입 시 on-demand로 Read합니다. 이는 별도의 시스템 프롬프트 파일이나 서브스킬 분할 없이, 단일 진입점을 유지하면서 단계별 로직을 캡슐화하는 표준 호환 방식입니다. (앞 절의 4개 워크플로우 파일 명세 참조)

### 3단계: 참조 문서 작성 (`references/`)

프롬프트 템플릿을 별도 `prompts/` 디렉토리로 분리하던 기존 계획은 폐기하고, 모든 가이드 문서를 표준 `references/` 디렉토리로 통합합니다. SKILL.md가 필요한 시점에 해당 파일을 Read합니다.

- `references/workflow/*.md` (4개): 단계별 상세 행동 규칙 — 2단계에서 작성
- `references/contracts/re-input-contract.md`: RE 3섹션 → QA 입력 파싱 가이드 (`acceptance_criteria` → 테스트 케이스, `metric` → NFR 시나리오, `regulatory` → 컴플라이언스 테스트 등)
- `references/contracts/arch-input-contract.md`: Arch 4섹션 → QA 입력 파싱 가이드 (`interfaces` → 통합 경계, `architecture_decisions` → 패턴별 전략, `technology_stack` → 프레임워크 선택)
- `references/contracts/impl-input-contract.md`: Impl 4섹션 → QA 입력 파싱 가이드 (`module_path` → 테스트 배치, `pattern_applied` → 패턴별 전략, `conventions` → 코드 컨벤션)
- `references/contracts/downstream-contract.md`: 후속 스킬(`deployment`, `operation`, `management`, `security`) 소비 계약
- `references/schemas/meta-schema.md`: 메타데이터 공통 필드 명세
- `references/schemas/section-schemas.md`: 4섹션(`test-strategy`, `test-suite`, `rtm`, `quality-report`) 필드 명세 (RTM 행 구조 포함)
- `references/adaptive-depth.md`: 경량/중량 모드 판별 규칙과 모드별 스킵 단계 정의
- `references/traceability.md`: RE → Arch → Impl → QA 추적성 체인 명세, RTM 생성 규칙, 갭 분석 방법
- `references/examples/` 하위: 입출력 예시(아래 6단계)

**스크립트 호출 규약 배치**: "메타데이터를 직접 편집하지 않고 `${SKILL_DIR}/scripts/artifact.py` 커맨드만 호출한다"는 행동 규약은 `references/workflow/*.md`에 반복 명시하고, 각 단계(strategy → generate → review → report)에서 어떤 커맨드를 어떤 순서로 호출해야 하는지 시퀀스로 기술합니다.

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

표준 디렉토리 명칭은 `assets/`입니다(기존 `templates/`는 폐기).

- 4섹션(`test-strategy`, `test-suite`, `rtm`, `quality-report`)별 markdown 템플릿(`*.md.tmpl`)을 `assets/templates/`에 작성. 각 템플릿은 섹션 헤더, 표 골격, RE/Arch/Impl 참조 슬롯, 플레이스홀더(`<!-- FILL: ... -->`)를 포함하여 워크플로우 단계가 본문만 채우도록 유도
- 각 섹션의 메타데이터 초기 골격(`*.meta.yaml.tmpl`)을 작성. `phase: draft`, `approval.state: pending`, 빈 `upstream_refs`/`downstream_refs` 등 기본값을 포함
- `rtm.meta.yaml.tmpl`은 RTM 행 배열 스키마(`re_id`, `arch_refs`, `impl_refs`, `test_refs`, `coverage_status`, `gap_description`)를 1급 시민으로 정의
- `quality-report.meta.yaml.tmpl`은 `quality_gate`(기준·실측·판정) 구조를 포함하여 `gate-evaluate` 자동 전이의 기반이 되도록 정의

**적응적 깊이 → `effort` 매핑**: frontmatter 기본값을 `effort: high`로 설정하되, SKILL.md 본문의 분기 로직에서 `references/adaptive-depth.md` 기준에 따라 경량 조건이면 review의 일부(예: 뮤테이션 분석)와 report의 트렌드 분석을 스킵합니다. 즉 하나의 스킬 안에서 경량/중량 모드를 내부 분기로 처리하며, 스킬 자체를 분할하지 않습니다(단일 진입점 유지).

**문서 길이 관리**: SKILL.md 500줄 이내를 유지하기 위해, 4단계 워크플로우의 상세 규칙·가이드·예시는 모두 이 단계에서 `references/`로 분리합니다.

### 5단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

- `scripts/artifact.py`를 단일 진입점으로 구현하며, 다음 서브커맨드를 제공:
  - `init` — `assets/templates/`에서 템플릿을 복사해 메타데이터 + markdown 쌍을 생성. 템플릿 경로는 `${SKILL_DIR}/assets/templates/`를 기준으로 해석
  - `set-phase`, `set-progress` — 진행 상태/진행률 갱신
  - `approve` — 승인 상태 전이 (전이 규칙 검증 포함)
  - `link` — `upstream_refs`/`downstream_refs` 추가 및 양방향 무결성 유지
  - `rtm-upsert`, `rtm-gap-report` — RTM 행 삽입/갱신과 MoSCoW별 갭 집계 (RTM 구조화 데이터 특화)
  - `gate-evaluate` — 품질 리포트 메타데이터의 게이트 기준을 평가하여 `approval.state` 자동 전이 (`pass` → `approved`, `fail` → `rejected`, Must 갭 해소 불가 → `escalated`)
  - `show`, `validate` — 조회 및 스키마/추적성 검증
- 모든 쓰기 커맨드는 `updated_at`을 자동 갱신하고, 잘못된 상태 전이/누락 필드를 차단

**스크립트 호출 강제 (다층 방어)**:

행동 규약만으로는 우회될 수 있으므로 다층 방어를 구성합니다.

1. **행동 규약 (가장 약함)**: `references/workflow/*.md` 및 SKILL.md 본문에서 "메타데이터 갱신은 반드시 `${SKILL_DIR}/scripts/artifact.py`를 호출한다"를 반복 명시
2. **도구 권한 (중간)**: frontmatter `allowed-tools` 설계 시 Edit/Write가 필요한 대상은 markdown 본문으로 한정하도록 워크플로우 가이드에서 명시
3. **PreToolUse hooks (가장 강함)**: 가능하다면 `*.meta.yaml`에 대한 Edit/Write 시도를 차단하는 PreToolUse hook을 등록하여, 행동 규약을 우회한 직접 편집을 원천 차단
4. **시작 시 상태 주입**: SKILL.md 상단에서 `` !`python ${SKILL_DIR}/scripts/artifact.py validate` ``와 `` !`python ${SKILL_DIR}/scripts/artifact.py rtm-gap-report` ``를 사용해 현재 산출물 상태·RTM 갭을 동적 컨텍스트로 주입

### 6단계: 입출력 예시 작성 (`references/examples/`)

- RE 경량 출력 → QA 경량 예시 (간단한 CRUD API의 acceptance_criteria 기반 단위 테스트)
- RE 중량 출력 → QA 중량 예시 (분산 시스템의 테스트 피라미드 + NFR + RTM)
- `acceptance_criteria` → 테스트 케이스(Given-When-Then) 변환 예시
- NFR `metric` → 성능 테스트 시나리오 변환 예시
- 아키텍처 패턴별 테스트 전략 예시 (마이크로서비스 계약 테스트 등)
- RTM 생성 및 커버리지 갭 자동 분류 예시 (Must 갭 자동 보완 + Should/Could 자동 수용)
- 에스컬레이션 예시: Must 요구사항 NFR 테스트 인프라 부재 시 사용자 에스컬레이션
- 정상 완료 예시: 에스컬레이션 없이 전체 자동 생성 후 최종 품질 리포트 제시
- 품질 게이트 판정 예시 (pass/fail) — `gate-evaluate` 호출과 `approval.state` 전이가 드러나도록 `quality-report.md`/`quality-report.meta.yaml` 쌍으로 제공
- **메타데이터 + 문서 쌍 예시**: 각 산출물 예시는 markdown 본문(`*-output.md`)과 그에 대응하는 메타데이터(`*-output.meta.yaml`)를 함께 포함하여, `phase`/`approval`/`upstream_refs`/`downstream_refs`가 채워진 실제 모습을 보여줄 것
- **스크립트 호출 트레이스 예시**: `artifact.py init` → 문서 편집 → `rtm-upsert` → `gate-evaluate` 순의 실제 커맨드 시퀀스

## 핵심 설계 원칙

1. **RE/Arch/Impl 산출물 기반 (3-Way Driven)**: 모든 테스트 결정은 RE 3섹션 + Arch 4섹션 + Impl 4섹션 산출물에 근거하며, 임의의 판단이 아닌 구조화된 입력 기반으로 도출. RE `acceptance_criteria`가 테스트의 필요충분 조건
2. **요구사항 추적성 (Requirements Traceability)**: 모든 테스트 케이스는 `re_refs`/`arch_refs`/`impl_refs`로 원천 요구사항까지 역추적 가능. RTM으로 RE → Arch → Impl → QA 전체 체인의 커버리지를 가시화하며, 추적성 무결성은 `${SKILL_DIR}/scripts/artifact.py validate`로 자동 검증
3. **적응적 깊이 (Adaptive Depth)**: Impl 모드(→ Arch 모드 → RE 출력 밀도)에 연동하여 경량(핵심 단위 테스트 + 체크리스트)/중량(전체 피라미드 + NFR + RTM + 게이트) 모드 자동 전환
4. **품질 게이트 (Quality Gate)**: 코드 커버리지·요구사항 커버리지·NFR 실측치를 종합하여 `pass`/`fail` 판정을 내리고, `gate-evaluate`가 메타데이터 `approval.state`를 자동 전이하여 후속 스킬(`deployment`)의 게이트 입력으로 직접 사용
5. **커버리지 기반 피드백 루프 (Coverage Feedback Loop)**: review 단계에서 식별된 Must 커버리지 갭 중 자동 보완이 가능한 항목은 generate 단계를 재호출하여 보완. Should/Could/Won't 갭은 자동 수용하여 잔여 리스크로 기록. 해소 불가 Must 갭만 사용자에게 에스컬레이션
6. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **테스트 전략 / 테스트 스위트 / 요구사항 추적 매트릭스 / 품질 리포트** 4섹션으로 고정하여, 후속 스킬(`deployment`, `operation`, `management`, `security`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
7. **메타데이터-문서 분리 및 스크립트 경유 원칙 (Metadata/Document Separation via Scripts)**: 산출물은 YAML 메타데이터 파일과 markdown 문서 파일을 분리하여 관리하고, 메타데이터(진행 상태·승인 상태·추적성 ref·RTM 행·게이트 판정)는 워크플로우 단계가 직접 편집하지 않고 오직 `${SKILL_DIR}/scripts/artifact.py` 커맨드를 통해서만 갱신. markdown 본문은 `assets/templates/`의 사전 정의 템플릿으로 골격을 생성한 뒤 플레이스홀더를 채움으로써, 상태 일관성과 서식 표준을 동시에 보장
8. **Claude Code Skill 표준 준수 (Standard Compliance)**: 단일 진입점 `SKILL.md` + YAML frontmatter, `scripts/`·`assets/`·`references/`의 표준 디렉토리 명칭, `${SKILL_DIR}`/`$ARGUMENTS` 치환자 활용, `` !`<command>` `` 동적 컨텍스트 주입을 통해 공식 표준(https://code.claude.com/docs/ko/skills)과 완전히 호환
