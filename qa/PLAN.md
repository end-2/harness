# QA (Quality Assurance) Skill 구현 계획

## 개요

RE 스킬의 산출물(요구사항 명세, 제약 조건, 품질 속성 우선순위), Arch 스킬의 산출물(아키텍처 결정, 컴포넌트 구조, 기술 스택, 다이어그램), Impl 스킬의 산출물(구현 맵, 코드 구조, 구현 결정, 구현 가이드)을 입력으로 받아, **테스트 전략 수립, 테스트 코드 생성, 품질 검증**을 수행하는 스킬입니다.

Impl이 "설계를 코드로 어떻게 구현할 것인가"를 실행했다면, QA는 "그 구현이 요구사항을 충족하는지 어떻게 검증할 것인가"를 결정하고 실행합니다. 이 과정에서 **RE의 acceptance_criteria를 테스트 케이스의 근거로, Arch의 컴포넌트 경계를 테스트 범위의 근거로, Impl의 구현 맵을 테스트 대상의 근거로** 사용하며, 모든 테스트 산출물은 원천 요구사항까지 역추적 가능합니다.

RE에서 MoSCoW 우선순위와 acceptance_criteria가 확정되고, Arch에서 컴포넌트 구조와 기술 스택이 결정된 상태이므로, QA는 **자동 실행 + 결과 보고** 모델을 채택합니다. 테스트 전략과 범위는 선행 산출물에서 기계적으로 도출하며, **Must 요구사항의 해소 불가능한 커버리지 갭이 발견된 경우에만 사용자에게 에스컬레이션**합니다.

### 전통적 QA vs AI 컨텍스트 QA

| 구분 | 전통적 QA | AI 컨텍스트 QA |
|------|-----------|----------------|
| 수행자 | QA 전담 팀 (테스터, QA 엔지니어) | 개발자가 AI에게 테스트 전략 수립과 생성을 위임 |
| 입력 | 테스트 계획서, 요구사항 추적 매트릭스 (별도 작성) | **RE/Arch/Impl 스킬의 구조화된 산출물** (추적성 내장) |
| 테스트 설계 | 테스터의 경험과 도메인 지식에 의존 | **RE acceptance_criteria 기반 체계적 도출** + AI 경계값/예외 분석 |
| NFR 검증 | 성능 테스트 팀이 별도로 진행 | **RE quality_attribute_priorities.metric을 테스트 시나리오로 직접 변환** |
| 추적성 | RTM(Requirements Traceability Matrix)을 수동 관리 | **re_refs/arch_refs/impl_refs로 자동 추적** |
| 커버리지 기준 | 코드 커버리지 (라인/분기) 위주 | **요구사항 커버리지 + 코드 커버리지** 이중 기준 |
| 산출물 | 테스트 결과 리포트 | **후속 스킬이 소비 가능한 구조화된 품질 산출물** |

## 선행 스킬 산출물 소비 계약

QA 스킬은 RE, Arch, Impl 세 스킬의 산출물을 모두 소비합니다.

### RE 출력 → QA 소비 매핑

| RE 산출물 섹션 | 주요 필드 | QA에서의 소비 방법 |
|---------------|-----------|-------------------|
| **요구사항 명세** | `id`, `category`, `title`, `acceptance_criteria`, `priority`, `dependencies` | `acceptance_criteria`를 테스트 케이스 도출의 핵심 근거로 사용. `priority`(MoSCoW)로 테스트 우선순위 결정 — Must 요구사항은 반드시 테스트, Won't는 제외. `dependencies`로 통합 테스트 시나리오 도출 |
| **제약 조건** | `id`, `type`, `flexibility`, `rationale` | `type: regulatory` 제약은 컴플라이언스 테스트 대상으로 분류. `type: technical` 제약(예: 특정 브라우저 지원)은 테스트 환경 매트릭스에 반영. `flexibility: hard` 제약은 필수 검증 대상 |
| **품질 속성 우선순위** | `attribute`, `priority`, `metric`, `trade_off_notes` | `metric`("응답시간 < 200ms", "99.9% 가용성")을 NFR 테스트 시나리오로 직접 변환. `priority` 순서로 NFR 테스트 투자 우선순위 결정. `trade_off_notes`로 테스트 시 허용 범위 판단 |

### Arch 출력 → QA 소비 매핑

| Arch 산출물 섹션 | 주요 필드 | QA에서의 소비 방법 |
|-----------------|-----------|-------------------|
| **아키텍처 결정** | `id`, `decision`, `trade_offs`, `re_refs` | `decision`으로 아키텍처 패턴별 테스트 전략 결정 (예: 이벤트 드리븐 → 비동기 메시지 테스트, 마이크로서비스 → 계약 테스트). `re_refs`로 RE까지 추적성 유지 |
| **컴포넌트 구조** | `id`, `name`, `type`, `interfaces`, `dependencies` | `interfaces`로 통합 테스트 경계 결정 — 컴포넌트 간 인터페이스가 통합 테스트 대상. `dependencies`로 테스트 더블(mock/stub) 전략 결정. `type`에 따라 테스트 방식 분기 (service → API 테스트, store → 데이터 무결성 테스트) |
| **기술 스택** | `category`, `choice`, `decision_ref` | `choice`로 테스트 프레임워크 선택 (TypeScript → Jest/Vitest, Python → pytest, Go → testing). 기술별 테스트 관용구(idiom) 적용 |
| **다이어그램** | `type`, `code` | `sequence` 다이어그램으로 주요 흐름의 E2E 테스트 시나리오 도출. `c4-container`로 통합 테스트 범위 시각 확인 |

### Impl 출력 → QA 소비 매핑

| Impl 산출물 섹션 | 주요 필드 | QA에서의 소비 방법 |
|-----------------|-----------|-------------------|
| **구현 맵** | `id`, `component_ref`, `module_path`, `entry_point`, `interfaces_implemented`, `re_refs` | `module_path`로 테스트 파일 배치 위치 결정. `interfaces_implemented`로 인터페이스 계약 테스트 대상 식별. `re_refs`로 RE 요구사항까지 역추적하여 요구사항 커버리지 매트릭스 생성 |
| **코드 구조** | `directory_layout`, `module_dependencies`, `external_dependencies` | `directory_layout`으로 테스트 디렉토리 구조 결정 (미러링 또는 co-location). `module_dependencies`로 모듈 간 의존성 기반 통합 테스트 순서 결정. `external_dependencies`로 외부 의존성 모킹 대상 식별 |
| **구현 결정** | `id`, `decision`, `pattern_applied`, `arch_refs`, `re_refs` | `pattern_applied`로 패턴별 테스트 전략 결정 (예: Repository 패턴 → 인메모리 구현으로 단위 테스트, Strategy 패턴 → 각 전략별 테스트). `arch_refs`/`re_refs`로 추적성 체인 완성 |
| **구현 가이드** | `setup_steps`, `build_commands`, `run_commands`, `conventions` | `setup_steps`로 테스트 환경 설정 절차 도출. `conventions`로 테스트 코드 컨벤션 일관성 유지 |

### 추적성 체인 (Traceability Chain)

QA는 RE → Arch → Impl → QA로 이어지는 추적성 체인의 최종 검증 지점입니다.

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

### 적응적 깊이 연동

Impl 모드(→ Arch 모드 → RE 출력 밀도)에 연동하여 QA의 산출물 수준을 자동 조절합니다.

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

#### 테스트 케이스 하위 구조

| 필드 | 설명 |
|------|------|
| `case_id` | 케이스 식별자 (예: `TS-001-C01`) |
| `description` | 테스트 설명 |
| `given` | 사전 조건 |
| `when` | 실행 조건 |
| `then` | 기대 결과 |
| `technique` | 적용 기법 (`boundary_value` / `equivalence_partition` / `decision_table` / `state_transition` / `property_based`) |
| `acceptance_criteria_ref` | 검증 대상 acceptance_criteria (RE 직접 참조) |

### 3. 요구사항 추적 매트릭스 (Requirements Traceability Matrix)

RE 요구사항 → Arch 컴포넌트 → Impl 모듈 → QA 테스트 간의 추적성을 보장합니다.

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

## 목표 구조

```
qa/
├── skills.yaml
├── agents/
│   ├── strategy.md
│   ├── generate.md
│   ├── review.md
│   └── report.md
├── prompts/
│   ├── strategy.md
│   ├── generate.md
│   ├── review.md
│   └── report.md
└── examples/
    ├── strategy-input.md
    ├── strategy-output.md
    ├── generate-input.md
    ├── generate-output.md
    ├── review-input.md
    ├── review-output.md
    ├── report-input.md
    └── report-output.md
```

## 에이전트 내부 흐름

```
RE:spec 산출물 + Arch 산출물 + Impl 산출물
    │
    ▼
qa:strategy ──────────────────────────────┐
    │  (선행 산출물 분석 → MoSCoW 기반     │
    │   테스트 범위 자동 도출 → 전략 확정)  │
    │                                     │
    ▼                                     │
qa:generate                               │
    │  (strategy 기반 테스트 코드 일괄 생성 │
    │   → acceptance_criteria 기계적 변환)  │
    │                                     │
    ▼                                     │
qa:review ◄───────────────────────────────┘
    │  (생성된 테스트의 완전성/강도 자동 리뷰
    │   + 요구사항 커버리지 검증
    │   + RTM 생성)
    │
    ├── Should/Could 갭 ──→ 자동 수용 (리스크로 기록)
    │
    ├── Must 갭 (자동 보완 가능) ──→ qa:generate (추가 생성)
    │                                   │
    │                                   ▼
    │                              qa:review (재리뷰)
    │
    ├── Must 갭 (해소 불가) ──→ 사용자 에스컬레이션 ⚠️
    │
    ▼
qa:report
    (테스트 실행 결과 + 품질 지표 +
     품질 게이트 판정 + 잔여 리스크)
        │
        ▼
    사용자에게 최종 품질 리포트 제시
```

### 에이전트 호출 규칙

- `strategy`는 항상 최초 진입점. RE/Arch/Impl 산출물을 수신하여 테스트 전략을 자동 수립
- `generate`는 `strategy` 완료 후 자동 호출. `review`에서 Must 커버리지 갭의 자동 보완이 필요한 경우 재호출
- `review`는 `generate` 완료 후 자동 호출. 추가 생성 후 재리뷰로도 자동 호출
- `report`는 `review` 완료 후 자동 호출. 독립적 온디맨드 호출도 가능 (기존 테스트 실행 결과 분석)
- **전체 파이프라인은 사용자 개입 없이 자동 실행**되며, 사용자 접점은 (1) Must 커버리지 갭 에스컬레이션과 (2) 최종 품질 리포트 제시 두 곳뿐

## 구현 단계

### 1단계: 스킬 메타데이터 정의 (`skills.yaml`)

- 스킬 이름, 버전, 설명
- 에이전트 목록 및 각 에이전트의 역할 정의
- **입력 스키마**: 
  - RE `spec` 산출물 3섹션 (`requirements_spec`, `constraints`, `quality_attribute_priorities`) 소비 계약
  - Arch 산출물 4섹션 (`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`) 소비 계약
  - Impl 산출물 4섹션 (`implementation_map`, `code_structure`, `implementation_decisions`, `implementation_guide`) 소비 계약
- **출력 스키마**: 4섹션 (`test_strategy`, `test_suite`, `requirements_traceability_matrix`, `quality_report`) 산출물 계약
  - 각 섹션의 필드 정의 및 필수/선택 여부 명시
  - 후속 스킬 연계를 위한 출력 계약(contract) 명세
- **적응적 깊이 설정**: Impl 모드에 따른 경량/중량 모드 기준 및 전환 규칙
- 지원 테스트 프레임워크 목록 (Jest, Vitest, pytest, JUnit, Go testing, Rust #[test] 등)
- 품질 게이트 기본값 설정 옵션 (사용자 오버라이드 가능)
- **에스컬레이션 조건 정의**: Must 요구사항 커버리지 갭 해소 불가 시 사용자 에스컬레이션 조건 및 판별 기준
- 의존성 정보 (선행: `re`, `arch`, `impl`, 후속 소비자: `deployment`, `operation`, `management`, `security`)

### 2단계: 에이전트 시스템 프롬프트 작성 (`agents/`)

#### `strategy.md` — 테스트 전략 에이전트

- **역할**: RE/Arch/Impl 산출물을 분석하여 테스트 전략을 **자동으로** 수립
- **핵심 역량**:
  - **RE 산출물 해석 → 테스트 범위 자동 도출**:
    - `requirements_spec`의 모든 FR/NFR을 테스트 대상으로 등록
    - `acceptance_criteria`의 개수와 복잡도로 테스트 케이스 볼륨 추정
    - `priority`(MoSCoW)로 테스트 우선순위 매트릭스 자동 생성 — Must는 반드시 커버, Should는 가급적 커버, Could/Won't는 자동으로 리스크 수용
    - `constraints`의 `type: regulatory`를 컴플라이언스 테스트 대상으로 분류
    - `quality_attribute_priorities.metric`을 NFR 테스트 계획으로 변환
  - **Arch 산출물 해석 → 테스트 구조 결정**:
    - `component_structure`의 `interfaces`와 `dependencies`로 통합 테스트 경계 결정
    - `architecture_decisions`의 `decision`으로 아키텍처 패턴별 테스트 전략 결정
      - 마이크로서비스 → 계약 테스트(Contract Test) 포함
      - 이벤트 드리븐 → 비동기 메시지 테스트 포함
      - 레이어드 → 레이어 간 통합 테스트 포함
    - `technology_stack`으로 테스트 프레임워크 선택
  - **Impl 산출물 해석 → 테스트 대상 매핑**:
    - `implementation_map`으로 테스트 파일 배치 결정 (모듈 경로 미러링)
    - `code_structure.module_dependencies`로 통합 테스트 순서 결정
    - `implementation_decisions.pattern_applied`로 패턴별 테스트 전략 결정
  - **테스트 피라미드 비율 자동 결정**: 아키텍처 패턴과 컴포넌트 구조에서 자동 도출 (마이크로서비스 → 계약 테스트 비중 확대, 모놀리식 → 단위 테스트 비중 확대)
  - **테스트 더블 전략 수립**: 컴포넌트 의존 관계 기반으로 mock/stub/fake/spy 사용 전략 자동 결정
  - **테스트 환경 매트릭스**: RE 제약 조건 기반으로 테스트 환경 조합 자동 결정 (브라우저, OS, 디바이스 등)
  - **품질 게이트 기준 자동 설정**: 합리적 기본값 적용 (코드 커버리지 80%, Must 요구사항 커버리지 100%, NFR 메트릭은 RE `metric` 수치 그대로 적용)
- **입력**: RE `spec` 산출물 + Arch 산출물 + Impl 산출물
- **출력**:
  - 테스트 전략 (범위, 피라미드 비율, 우선순위 매트릭스, NFR 테스트 계획)
  - 테스트 더블 전략
  - 테스트 환경 매트릭스
  - 품질 게이트 기준
- **상호작용 모델**: 선행 산출물 분석 → 전략 자동 수립 → `generate`로 직접 전달. 사용자 개입 없음
- **에스컬레이션 조건**: 없음 — 모든 전략 결정은 선행 산출물에서 기계적으로 도출 가능. 품질 게이트 기준은 기본값 적용 (사용자가 사전에 오버라이드 가능)

#### `generate.md` — 테스트 코드 생성 에이전트

- **역할**: 확정된 테스트 전략 기반으로 테스트 코드를 생성하되, 모든 테스트가 RE 요구사항까지 추적 가능하도록 생성
- **핵심 역량**:
  - **acceptance_criteria → 테스트 케이스 변환**: RE의 각 `acceptance_criteria`를 하나 이상의 테스트 케이스로 변환. 변환 시 `acceptance_criteria_ref`로 원천 추적 유지
  - **테스트 설계 기법 적용**:
    - 경계값 분석 (Boundary Value Analysis)
    - 동등 분할 (Equivalence Partitioning)
    - 결정 테이블 (Decision Table)
    - 상태 전이 (State Transition)
    - 프로퍼티 기반 테스트 (Property-Based Testing)
  - **테스트 유형별 생성**:
    - **단위 테스트**: Impl 모듈 단위, 개별 함수/메서드 검증. 테스트 더블 전략에 따른 mock/stub 적용
    - **통합 테스트**: Arch 컴포넌트 간 인터페이스 검증. `component_structure.interfaces` 기반
    - **E2E 테스트**: Arch `sequence` 다이어그램의 주요 흐름을 시나리오로 변환
    - **계약 테스트**: 마이크로서비스 아키텍처 시 컴포넌트 간 API 계약 검증
    - **NFR 테스트**: RE `quality_attribute_priorities.metric` 기반 성능/부하/스트레스 테스트 시나리오
  - **AAA 패턴 준수**: Arrange-Act-Assert 패턴으로 일관된 테스트 구조
  - **테스트 코드 컨벤션**: Impl `conventions`에 맞춘 네이밍, 구조 일관성
  - **일괄 생성**: 전체 테스트를 strategy 기반으로 일괄 생성. 커버리지 충분성은 `review` 에이전트가 자동 검증
- **입력**: 테스트 전략 + 테스트 대상 코드 + Impl 산출물 (모듈 매핑) + RE 산출물 (acceptance_criteria)
- **출력**:
  - 테스트 스위트 목록 (유형, 대상 모듈, 테스트 케이스, 추적 참조)
  - 생성된 테스트 코드 파일들
  - 각 테스트 케이스의 `re_refs`, `arch_refs`, `impl_refs`
- **상호작용 모델**: strategy 수신 → 전체 테스트 일괄 생성 → `review`로 직접 전달. 사용자 개입 없음

#### `review.md` — 테스트 리뷰 에이전트

- **역할**: 생성된 테스트의 완전성, 강도, 추적성을 리뷰하고, 요구사항 추적 매트릭스(RTM)를 생성
- **핵심 역량**:
  - **요구사항 커버리지 검증 (RTM 생성)**:
    - RE의 모든 FR/NFR에 대해 대응하는 테스트 케이스가 존재하는지 확인
    - 각 `acceptance_criteria`가 최소 하나의 테스트 케이스에 매핑되는지 확인
    - `covered`/`partial`/`uncovered` 상태를 판정하고, 갭 사유를 기록
    - Must 요구사항 중 `uncovered`가 있으면 **필수 보완** 플래그
  - **코드 커버리지 분석**:
    - 라인, 분기, 경로 커버리지 분석 (모듈별)
    - 커버리지가 낮은 모듈과 해당 모듈이 담당하는 RE 요구사항 매핑
  - **테스트 강도 평가**:
    - 뮤테이션 테스트 관점에서 테스트가 실제 버그를 잡을 수 있는지 평가
    - 경계값/예외 케이스 누락 식별
    - 하드코딩된 기대값, 의미 없는 assertion 등 약한 테스트 탐지
  - **테스트 코드 품질 리뷰**:
    - 테스트 간 결합도 (테스트 독립성 위반 여부)
    - 불안정한 테스트(flaky test) 패턴 탐지 (시간 의존, 순서 의존, 외부 서비스 의존)
    - 테스트 유지보수성 및 가독성
  - **NFR 테스트 검증**: RE `metric` 대비 NFR 테스트 시나리오의 충분성 확인 (부하 수준, 측정 방법 적정성)
  - **추적성 체인 검증**: 테스트 → Impl → Arch → RE 역추적이 모든 테스트에서 가능한지 확인
- **입력**: 생성된 테스트 코드 + 테스트 전략 + RE/Arch/Impl 산출물 (검증 기준)
- **출력**: 
  - 요구사항 추적 매트릭스 (RTM)
  - 테스트 리뷰 리포트 (커버리지 갭, 강도 이슈, 코드 품질 이슈, 추적성 이슈)
  - 커버리지 갭 자동 분류 (자동 보완 가능 / 해소 불가)
- **상호작용 모델**: 자동 리뷰 수행 → 커버리지 갭 자동 분류 → Should/Could/Won't 갭은 자동 수용하여 잔여 리스크로 기록 → Must 갭 중 자동 보완 가능한 것은 `generate` 재호출로 보완 → Must 갭 중 해소 불가능한 것만 사용자에게 에스컬레이션
- **에스컬레이션 조건**: Must 요구사항의 커버리지 갭이 자동 보완 불가능한 경우에만 사용자에게 에스컬레이션 (예: NFR 테스트에 필요한 인프라 부재, 외부 시스템 의존성으로 테스트 불가)

#### `report.md` — 품질 리포트 에이전트

- **역할**: 테스트 실행 결과를 수집하고, RE 메트릭 대비 품질 현황을 종합 리포트로 생성
- **핵심 역량**:
  - **코드 커버리지 집계**: 모듈별, 컴포넌트별, 전체 코드 커버리지 집계
  - **요구사항 커버리지 집계**: RTM 기반 covered/partial/uncovered 비율 집계
  - **NFR 측정 결과 대비 분석**: RE `quality_attribute_priorities.metric` 대비 실측치 비교
    - 예: `metric: "응답시간 < 200ms"` → 실측: 150ms → Pass
    - 예: `metric: "99.9% 가용성"` → 테스트 미실시 → N/A (잔여 리스크로 분류)
  - **품질 게이트 판정**: strategy에서 합의한 품질 게이트 기준 대비 pass/fail 판정
  - **잔여 리스크 식별**: uncovered 요구사항, 실패 테스트, 미달 NFR을 잔여 리스크로 분류
  - **개선 권고**: 리스크 수준에 따른 우선순위화된 개선 권고
  - **트렌드 분석**: 이전 측정 데이터가 있는 경우 품질 트렌드 시각화
- **입력**: 테스트 실행 결과 + RTM + 테스트 전략 (품질 게이트 기준) + RE 산출물 (metric 기준)
- **출력**:
  - 품질 리포트 (코드 커버리지, 요구사항 커버리지, NFR 결과, 품질 게이트 판정, 잔여 리스크, 권고)
- **상호작용 모델**: 자동으로 리포트 생성 → **최종 품질 리포트를 사용자에게 제시** (QA 파이프라인의 유일한 정규 사용자 접점). 잔여 리스크와 품질 게이트 판정 결과를 명확히 보고하되, 추가 의사결정이 필요한 사항은 후속 스킬(`deployment`)로 전달

### 3단계: 프롬프트 템플릿 작성 (`prompts/`)

각 에이전트에 대응하는 프롬프트 템플릿을 작성합니다:
- **RE/Arch/Impl 산출물 파싱 가이드**: 세 스킬의 산출물에서 테스트 관련 정보를 추출하는 방법
- **acceptance_criteria → 테스트 케이스 변환 가이드**: 수용 기준을 Given-When-Then 형식 테스트로 변환하는 규칙
- **NFR metric → 테스트 시나리오 변환 템플릿**: RE 품질 메트릭을 구체적 NFR 테스트로 변환하는 방법
- **아키텍처 패턴별 테스트 전략 가이드**: 마이크로서비스/이벤트 드리븐/레이어드 등 패턴별 테스트 접근법
- **RTM 생성 가이드**: 추적성 매트릭스 생성 및 갭 분석 방법
- **커버리지 갭 자동 분류 가이드**: Must/Should/Could/Won't별 갭 처리 규칙 및 자동 보완 vs 에스컬레이션 판별 기준
- **에스컬레이션 메시지 형식**: Must 커버리지 갭 에스컬레이션 시 사용자에게 전달할 정보 구조 (갭 사유, 영향 범위, 대안)
- 프레임워크별 테스트 코드 생성 템플릿 (Jest, pytest, JUnit, Go testing 등)
- 품질 게이트 기본값 설정 및 사용자 오버라이드 가이드
- Chain of Thought 가이드라인
- Few-shot 예시 포함

### 4단계: 입출력 예시 작성 (`examples/`)

각 에이전트별 대표적인 입출력 쌍을 작성합니다:
- **RE 경량 출력 → QA 경량**: 간단한 CRUD API의 acceptance_criteria 기반 단위 테스트 자동 생성 예시
- **RE 중량 출력 → QA 중량**: 분산 시스템의 테스트 피라미드 전략 자동 수립 + NFR 테스트 + RTM 예시
- **acceptance_criteria → 테스트 케이스 변환** 예시 (Given-When-Then)
- **NFR metric → 성능 테스트 시나리오** 변환 예시
- **아키텍처 패턴별 테스트 전략** 예시 (마이크로서비스 계약 테스트)
- **RTM 생성 및 커버리지 갭 자동 분류** 예시 (Must 갭 자동 보완 + Should/Could 갭 자동 수용)
- **에스컬레이션 예시**: Must 요구사항 NFR 테스트 인프라 부재 시 사용자 에스컬레이션 (질문 형식, 대안 제시 포함)
- **정상 완료 예시**: 에스컬레이션 없이 전체 자동 생성 후 최종 품질 리포트 제시
- **품질 게이트 판정** 예시 (pass/fail 시나리오)
- 엣지 케이스: 요구사항 변경 시 영향받는 테스트 식별 예시

## 핵심 설계 원칙

1. **요구사항 추적성 (Requirements Traceability)**: 모든 테스트 케이스는 `re_refs`/`arch_refs`/`impl_refs`로 원천 요구사항까지 역추적 가능. RTM으로 RE → Arch → Impl → QA 전체 체인의 커버리지를 가시화
2. **선행 산출물 기반 (Upstream-Driven)**: 테스트 전략과 범위는 RE/Arch/Impl 산출물에 근거하며, 임의의 판단이 아닌 구조화된 입력 기반으로 결정. RE `acceptance_criteria`가 테스트의 필요충분 조건
3. **적응적 깊이 (Adaptive Depth)**: Impl 모드에 연동하여 경량(핵심 단위 테스트 + 체크리스트)/중량(전체 피라미드 + NFR + RTM) 모드 자동 전환
4. **이중 커버리지 기준 (Dual Coverage)**: 코드 커버리지(라인/분기)와 요구사항 커버리지(RTM 기반)를 동시에 추적. 코드 커버리지 100%여도 요구사항 커버리지가 부족하면 품질 게이트 미통과
5. **테스트 피라미드 (Test Pyramid)**: 단위 > 통합 > E2E 비율 유지. 아키텍처 패턴에 따라 계약 테스트, NFR 테스트 등 추가 레이어 적용
6. **프레임워크 중립성**: 핵심 테스트 설계 원칙은 프레임워크에 독립적이되, Arch `technology_stack`에 따른 프레임워크별 관용구 존중
7. **자동 실행 + 결과 보고 (Auto-Execute with Result Reporting)**: 테스트 투자 범위는 MoSCoW 우선순위에서 자동 도출하고, 품질 게이트 기준은 합리적 기본값을 적용. 사용자에게는 **최종 품질 리포트만 제시**하며, Must 요구사항의 해소 불가능한 커버리지 갭이 발견된 경우에만 에스컬레이션
8. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **테스트 전략 / 테스트 스위트 / 요구사항 추적 매트릭스 / 품질 리포트** 4섹션으로 고정하여, 후속 스킬(`deployment`, `operation`, `management`, `security`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
