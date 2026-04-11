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

RE 요구사항 → Arch 컴포넌트 → Impl 모듈 → QA 테스트 간의 추적성을 보장합니다. RTM은 본질적으로 구조화된 테이블 데이터이므로 **메타데이터 파일(YAML)에 1급 시민으로 저장**되며, 아래 필드는 그대로 메타데이터 스키마의 `rtm` 항목에 매핑됩니다.

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

### 산출물 파일 구성 (메타데이터 + 문서 분리)

QA 스킬의 네 섹션 산출물은 각 섹션마다 **메타데이터 파일(YAML)과 문서 파일(Markdown) 쌍**으로 저장되며, 에이전트는 두 파일의 역할을 엄격히 구분합니다.

| 구분 | 파일 형식 | 역할 | 편집 주체 |
|------|-----------|------|-----------|
| 메타데이터 | `*.meta.yaml` | 구조화된 필드(ID, refs, priority, coverage_status, phase, approval 등) 저장. 추적성·상태·승인·게이트 판정을 기계 친화적으로 관리 | **스크립트 전용** (에이전트 직접 편집 금지) |
| 문서 | `*.md` | 전략 서술, 근거 설명, 테스트 케이스 Given-When-Then, 리포트 해석 등 서술형 본문 | 에이전트가 템플릿 기반으로 편집 |

**YAML을 메타데이터 형식으로 채택한 이유**는 (1) 주석 지원으로 필드 의미·결정 근거를 인라인 기록 가능, (2) 사람이 리뷰하기 쉬운 가독성, (3) 스크립트에서 `PyYAML`/`ruamel.yaml`로 파싱·갱신이 단순하다는 점 때문입니다. JSON은 주석을 지원하지 않아 RTM처럼 갭 사유를 병기해야 하는 데이터에 부적합합니다.

#### 메타데이터 공통 스키마 (추적·상태·승인)

모든 `*.meta.yaml`은 아래 공통 헤더를 포함합니다.

| 필드 | 설명 |
|------|------|
| `id` | 산출물 식별자 (예: `TSTR-001`, `TS-001`, `RTM`, `QR-001`) |
| `kind` | `test_strategy` / `test_suite` / `rtm` / `quality_report` |
| `phase` | 현재 파이프라인 단계 (`strategy` / `generate` / `review` / `report` / `done`) |
| `progress` | 진행률 퍼센트 또는 상태 라벨 (`in_progress` / `blocked` / `complete`) |
| `approval.state` | 승인 상태 (`draft` / `pending_review` / `approved` / `rejected` / `escalated`) |
| `approval.approver` | 승인자 식별자 (자동 승인의 경우 `auto:review-agent` 등) |
| `approval.approved_at` | 승인 타임스탬프 |
| `approval.notes` | 승인/거절 사유, 에스컬레이션 메모 |
| `upstream_refs` | 상류 산출물 참조 (`re_refs`, `arch_refs`, `impl_refs`) |
| `downstream_refs` | 하류 소비 산출물 참조 (예: 후속 스킬에서 사용하는 ID) |
| `doc_path` | 짝이 되는 Markdown 문서 파일 경로 |

품질 리포트의 `quality_gate` 판정(`pass`/`fail`)은 해당 리포트 메타데이터의 `approval.state`에 직접 반영됩니다. 게이트 `pass` → `approval.state: approved`, `fail` → `approval.state: rejected`(또는 Must 갭 해소 불가 시 `escalated`)로 전이되며, 이 상태가 후속 스킬(`deployment`)의 게이트 입력으로 사용됩니다.

#### 스크립트 경유 필수 원칙

에이전트는 `*.meta.yaml`을 **직접 편집하지 않으며**, 반드시 `scripts/` 디렉토리의 커맨드를 경유해 상태를 갱신합니다. 직접 편집은 검증되지 않은 스키마 드리프트, 승인 상태 오염, 추적성 체인 단절을 유발하기 때문입니다. 대표 커맨드는 다음과 같습니다.

| 커맨드 | 용도 |
|--------|------|
| `python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --kind <kind> --id <id>` | 메타데이터 파일과 짝이 되는 Markdown 문서를 `templates/`에서 복사하여 생성 |
| `python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase --id <id> --phase <phase>` | 진행 단계 전이 |
| `python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-approval --id <id> --state <state> --approver <who> [--notes ...]` | 승인 상태 갱신 |
| `python ${CLAUDE_SKILL_DIR}/scripts/artifact.py add-ref --id <id> --kind upstream --ref <RE-ID>` | 상·하류 추적 참조 추가 |
| `python ${CLAUDE_SKILL_DIR}/scripts/rtm.py upsert --re-id <id> --test-refs <...> --status <covered\|partial\|uncovered>` | RTM 행 삽입/갱신 (구조화 데이터에 특화) |
| `python ${CLAUDE_SKILL_DIR}/scripts/rtm.py gap-report` | uncovered/partial 갭을 MoSCoW 우선순위별로 집계 |
| `python ${CLAUDE_SKILL_DIR}/scripts/gate.py evaluate --report <id>` | 품질 리포트 메타데이터의 게이트 기준을 평가하여 `approval.state` 자동 전이 |
| `python ${CLAUDE_SKILL_DIR}/scripts/artifact.py show --id <id>` | 메타데이터 조회 (JSON/YAML 출력) |

모든 스크립트 경로는 작업 디렉토리 비의존성을 위해 `${CLAUDE_SKILL_DIR}`로 절대화되며, `SKILL.md` 본문에서는 `` !`python ${CLAUDE_SKILL_DIR}/scripts/rtm.py gap-report` ``, `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py show --id RTM` `` 등 **동적 컨텍스트 주입(`` !`<cmd>` ``)** 을 활용해 Skill 호출 시점의 실제 RTM 상태·갭 리포트를 자동으로 주입합니다. 이 방식은 스크립트 경유 원칙과 완벽히 정합합니다.

#### 템플릿 기반 문서 골격

짝이 되는 Markdown 문서는 `templates/` 디렉토리에 섹션 헤더와 플레이스홀더가 포함된 템플릿으로 미리 정의됩니다. `scripts/artifact.py init`이 해당 템플릿을 복사해 기본 골격을 생성하면, 에이전트는 플레이스홀더 부분만 서술형으로 편집합니다.

| 템플릿 | 대상 산출물 |
|--------|-------------|
| `templates/test-strategy.md` | 테스트 전략 문서 (범위, 피라미드 근거, NFR 계획 서술) |
| `templates/test-suite.md` | 테스트 스위트 문서 (Given-When-Then 케이스, 설계 기법 설명) |
| `templates/rtm.md` | RTM 사람용 뷰 (메타데이터에서 렌더되는 요약 + 갭 해설) |
| `templates/quality-report.md` | 품질 리포트 문서 (실측 해석, 잔여 리스크 서술, 권고) |

이 구조를 통해 **구조화된 상태·추적 데이터는 YAML이 진실의 원천**으로 기능하고, **서술형 맥락은 Markdown이 담당**하는 관심사 분리를 달성합니다.

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
├── SKILL.md                 # 엔트리포인트: YAML frontmatter + 본문(500줄 이하)
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
├── references/              # 공식 Skill 표준의 supporting files (상세 문서 분리)
│   ├── consumption-contracts.md   # RE/Arch/Impl 소비 매핑 상세
│   ├── traceability-chain.md      # 추적성 체인 다이어그램/설명
│   ├── output-contract.md         # 4섹션 산출물 스키마 상세
│   ├── metadata-schema.md         # 공통 헤더 + 섹션별 메타데이터 필드 상세
│   └── framework-idioms.md        # Jest/pytest/JUnit/Go testing 등 프레임워크별 관용구
├── scripts/
│   ├── artifact.py          # 메타데이터 초기화·상태/승인/추적 갱신 CLI
│   ├── rtm.py               # RTM 행 upsert, 갭 리포트, 커버리지 집계
│   └── gate.py              # 품질 게이트 평가 및 approval 전이
├── templates/
│   ├── test-strategy.md     # 테스트 전략 문서 템플릿
│   ├── test-strategy.meta.yaml
│   ├── test-suite.md        # 테스트 스위트 문서 템플릿
│   ├── test-suite.meta.yaml
│   ├── rtm.md               # RTM 사람용 뷰 템플릿
│   ├── rtm.meta.yaml        # RTM 구조화 데이터 스키마
│   ├── quality-report.md    # 품질 리포트 문서 템플릿
│   └── quality-report.meta.yaml
└── examples/
    ├── strategy-input.md
    ├── strategy-output.md
    ├── strategy-output.meta.yaml
    ├── generate-input.md
    ├── generate-output.md
    ├── generate-output.meta.yaml
    ├── review-input.md
    ├── review-output.md
    ├── review-output.meta.yaml
    ├── rtm-output.md
    ├── rtm-output.meta.yaml
    ├── report-input.md
    ├── report-output.md
    └── report-output.meta.yaml
```

각 에이전트 산출물은 `*.md`(서술)와 `*.meta.yaml`(메타데이터)의 **쌍으로 제공**되며, 예시(`examples/`)에도 두 파일이 함께 포함되어 에이전트가 템플릿 → 스크립트 초기화 → 문서 편집 → 스크립트로 상태 전이 순서를 참조할 수 있도록 합니다.

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

### 1단계: 스킬 엔트리포인트 정의 (`SKILL.md` + YAML frontmatter)

Claude Code Skill 공식 표준에 따라 `qa/SKILL.md`를 엔트리포인트로 신설합니다. `skills.yaml`은 **사용하지 않으며**(표준 로더가 인식하지 못함), 메타데이터는 Markdown 상단의 YAML frontmatter(`---` 블록)에 **필수 필드(`name`, `description`)만** 선언합니다. 본문에는 파이프라인 흐름·호출 규칙·에스컬레이션 정책 요약·스크립트 커맨드 레퍼런스만 배치해 500줄 제한 내에서 유지합니다. 상세 설명(소비 매핑, 추적성 체인, 산출물 스키마, 메타데이터 상세, 프레임워크 관용구)은 `references/`로 이관하여 supporting files로 참조합니다.

#### 1-1. Frontmatter 명세

```yaml
---
name: qa
description: RE/Arch/Impl 산출물을 입력받아 테스트 전략·테스트 코드·RTM·품질 리포트를 자동 생성하고 요구사항 추적성을 검증합니다. 선행 산출물이 준비된 후 또는 테스트/품질 게이트 판정이 필요할 때 사용하세요.
---
```

**필드 해설**:

- `name`: 소문자/하이픈 규칙 준수(디렉토리명과 일치).
- `description`: **what + when**을 모두 포함해 250자 제한 내에서 작성. 자동(모델) 호출 시 이 설명으로 Skill이 선택되므로 "언제 사용할지" 트리거가 반드시 포함되어야 함.
- 그 외 선택 필드(`argument-hint`, `allowed-tools`, `context`, `agent`, `effort`, `model`, `hooks`, `paths`, `disable-model-invocation` 등)는 **기본값으로 두며**, 기본 동작으로 스킬 목적을 달성할 수 없는 구체적 사유가 있을 때에만 추가합니다.

#### 1-2. 메타데이터 편집 차단(스크립트 경유 원칙의 런타임 강제)

`allowed-tools`에 `Write`/`Edit`를 허용하되, **`*.meta.yaml` 경로에 대한 직접 편집은 프롬프트 강제 + 사전 훅으로 이중 차단**합니다.

- 프롬프트(`agents/*.md`, `prompts/*.md`)에 "`.meta.yaml`은 직접 편집 금지, 반드시 `scripts/artifact.py`를 경유" 규칙을 명시.
- (선택) `hooks.PreToolUse`에서 `Edit`/`Write` 툴 호출 시 대상 경로가 `**/*.meta.yaml`이면 차단하는 훅을 추가.

#### 1-3. 본문(Markdown) 구성

`SKILL.md` 본문은 150–250줄 수준으로 유지하며 다음 섹션으로 구성합니다.

1. **개요**(3–5줄): RE → Arch → Impl → QA 추적성 체인에서 QA의 역할 요약.
2. **입출력 계약 요약**: 선행 소비 계약과 4섹션 산출물 계약은 **요약 표만** 게재하고, 상세는 `references/consumption-contracts.md`, `references/output-contract.md`로 위임.
3. **동적 컨텍스트 주입**: 호출 시점의 실제 상태를 Skill에 주입.
   - `` !`python ${CLAUDE_SKILL_DIR}/scripts/rtm.py gap-report` `` → 현재 RTM 갭 리포트
   - `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py show --id RTM` `` → RTM 메타데이터
   - `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py show --kind quality_report` `` → 최신 품질 리포트 상태
4. **파이프라인 흐름**: `strategy → generate → review → report` 4단계 흐름도(이미 본 문서 293–330줄에 정의된 다이어그램을 축약 인용).
5. **서브에이전트 오케스트레이션**: 아래 1-4 옵션 중 **옵션 A를 채택**.
6. **호출 규칙 및 에스컬레이션 정책**: 자동 실행 + Must 갭 해소 불가 시에만 에스컬레이션.
7. **스크립트 커맨드 레퍼런스**: `${CLAUDE_SKILL_DIR}/scripts/` 경유 커맨드 인덱스(본 문서 198–208줄의 축약 표).
8. **선행 산출물 검증 규칙**: 선행 스킬(`re`/`arch`/`impl`)의 산출물이 미존재 또는 구버전인 경우 즉시 에러 종료.

#### 1-4. 서브에이전트 오케스트레이션 모델 (옵션 A 채택)

PLAN의 4개 서브에이전트(`strategy`/`generate`/`review`/`report`)와 Claude Code Skill 공식 표준(`context: fork` + `agent`) 사이의 관계를 다음과 같이 확정합니다.

- **옵션 A (채택)**: `SKILL.md`가 단일 통합 엔트리포인트로 동작하고, 본문에서 `Explore → Plan → Execute` 단계별 지침을 서술. 4개 서브에이전트는 **Skill 내부 논리 단계**로 통합되며, 상세 역량 기술·프롬프트는 `agents/strategy.md`, `prompts/strategy.md` 등 supporting files로 분리 보관하되, 런타임 분기와 호출 순서는 `SKILL.md` 본문이 단일 책임으로 담당. 런타임 상태 전이는 `scripts/artifact.py set-phase` 커맨드로 기록.
- **옵션 B (기각)**: 각 서브에이전트를 별도 Skill(`qa-strategy`, `qa-generate`, …)로 분리하고 상위 `qa` Skill이 `Task` 도구로 위임하는 방식. Skill 수 증가와 각 하위 Skill의 중복 frontmatter 유지 부담으로 현재 단계에서는 채택하지 않음.

#### 1-5. 입출력 스키마·의존성·기본값

Frontmatter가 담기 어려운 상세 정보는 아래 위치에 분산 기재합니다.

- **입력 스키마**(RE 3섹션, Arch 4섹션, Impl 4섹션 소비 계약): `references/consumption-contracts.md`에 상세 기재. `SKILL.md` 본문은 요약 표만 게재.
- **출력 스키마**(4섹션 `test_strategy` / `test_suite` / `requirements_traceability_matrix` / `quality_report`): `references/output-contract.md`에 필드 정의 및 필수/선택 여부까지 상세 기재. 후속 스킬(`deployment`, `operation`, `management`, `security`)이 직접 소비 가능한 계약 형식.
- **적응적 깊이 설정**: Impl 모드(경량/중량)에 따른 전환 규칙은 `SKILL.md` 본문에 간단히 기술.
- **지원 테스트 프레임워크 목록** (Jest, Vitest, pytest, JUnit, Go testing, Rust #[test] 등): `references/framework-idioms.md`.
- **품질 게이트 기본값** 및 사용자 오버라이드 규칙: `SKILL.md` 본문에 기본값 인라인 + 오버라이드 방법 서술.
- **에스컬레이션 조건**: Must 요구사항 커버리지 갭이 `generate` 재호출로도 해소 불가한 경우에 한정(본문 및 `hooks`로 이중 보장).
- **의존성 정보**: 선행 `re`/`arch`/`impl`, 후속 소비자 `deployment`/`operation`/`management`/`security` — `SKILL.md` 본문의 "선행/후속 스킬" 섹션에 명시.

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

### 4단계: 메타데이터 스키마 및 문서 템플릿 정의 (`templates/`)

- **메타데이터 공통 헤더 스키마** 정의 (`id`, `kind`, `phase`, `progress`, `approval.*`, `upstream_refs`, `downstream_refs`, `doc_path`)
- **섹션별 고유 필드** 스키마 확장:
  - `test-strategy.meta.yaml`: `scope`, `pyramid`, `priority_matrix`, `nfr_test_plan`, `environment_matrix`, `test_double_strategy`, `quality_gate_criteria`
  - `test-suite.meta.yaml`: `type`, `target_module`, `framework`, `test_cases[]`(각 케이스의 `case_id`, `technique`, `acceptance_criteria_ref`)
  - `rtm.meta.yaml`: 행(row)의 배열로 `re_id`, `re_priority`, `arch_refs`, `impl_refs`, `test_refs`, `coverage_status`, `gap_description` 포함
  - `quality-report.meta.yaml`: `code_coverage`, `requirements_coverage`, `nfr_results[]`, `quality_gate`(기준·실측·판정), `risk_items[]`
- **Markdown 템플릿 작성**: 섹션 헤더, 플레이스홀더(`<!-- FILL: ... -->`), 메타데이터에서 자동 주입될 필드 마커 정의
- **YAML 주석 가이드**: 각 필드에 의미·근거·갱신 시점을 주석으로 기록하는 규칙

### 5단계: 메타데이터/템플릿 조작 스크립트 구현 (`scripts/`)

- `scripts/artifact.py`:
  - `init --kind <kind> --id <id>`: `templates/`에서 `*.md`와 `*.meta.yaml`을 복사, 공통 헤더 초기화(`phase: strategy`, `approval.state: draft`)
  - `set-phase`, `set-approval`, `add-ref`, `show` 서브커맨드
  - 스키마 검증 (JSON Schema 또는 pydantic)으로 스크립트 경유 시 드리프트 방지
- `scripts/rtm.py`:
  - `upsert`, `gap-report`, `coverage-summary`
  - RE 요구사항을 스캔하여 누락된 행을 자동 생성하는 `bootstrap` 모드
- `scripts/gate.py`:
  - 품질 게이트 기준(strategy 단계에서 정한 값)과 리포트 실측치를 비교
  - 결과에 따라 리포트 메타데이터의 `approval.state`를 `approved`/`rejected`/`escalated`로 자동 전이
  - Must 갭 해소 불가 시 `escalated` 상태로 전이하고 에스컬레이션 페이로드 출력
- **에이전트 가이드 문서**: 각 에이전트 프롬프트(`agents/*.md`, `prompts/*.md`)에 "메타데이터는 반드시 `scripts/`를 경유하며, `*.meta.yaml`을 직접 편집하지 말 것" 규칙을 명시

### 6단계: 입출력 예시 작성 (`examples/`)

각 에이전트별 대표적인 입출력 쌍을 작성합니다:
- **RE 경량 출력 → QA 경량**: 간단한 CRUD API의 acceptance_criteria 기반 단위 테스트 자동 생성 예시
- **RE 중량 출력 → QA 중량**: 분산 시스템의 테스트 피라미드 전략 자동 수립 + NFR 테스트 + RTM 예시
- **acceptance_criteria → 테스트 케이스 변환** 예시 (Given-When-Then)
- **NFR metric → 성능 테스트 시나리오** 변환 예시
- **아키텍처 패턴별 테스트 전략** 예시 (마이크로서비스 계약 테스트)
- **RTM 생성 및 커버리지 갭 자동 분류** 예시 (Must 갭 자동 보완 + Should/Could 갭 자동 수용)
- **에스컬레이션 예시**: Must 요구사항 NFR 테스트 인프라 부재 시 사용자 에스컬레이션 (질문 형식, 대안 제시 포함)
- **정상 완료 예시**: 에스컬레이션 없이 전체 자동 생성 후 최종 품질 리포트 제시
- **품질 게이트 판정** 예시 (pass/fail 시나리오) — `gate.py evaluate` 호출과 메타데이터 `approval.state` 전이가 드러나도록 `quality-report.md`와 `quality-report.meta.yaml` 쌍으로 제공
- **메타데이터 + 문서 쌍 예시**: 각 에이전트 산출물에 대해 `*.md`와 `*.meta.yaml`을 함께 제공하여, 구조화 필드가 YAML에, 서술형 근거가 Markdown에 위치하는 분리 원칙을 구체화
- **스크립트 호출 트레이스 예시**: `python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init` → 에이전트 문서 편집 → `python ${CLAUDE_SKILL_DIR}/scripts/rtm.py upsert` → `python ${CLAUDE_SKILL_DIR}/scripts/gate.py evaluate` 순의 실제 커맨드 시퀀스
- 엣지 케이스: 요구사항 변경 시 영향받는 테스트 식별 예시

## 핵심 설계 원칙

1. **요구사항 추적성 (Requirements Traceability)**: 모든 테스트 케이스는 `re_refs`/`arch_refs`/`impl_refs`로 원천 요구사항까지 역추적 가능. RTM으로 RE → Arch → Impl → QA 전체 체인의 커버리지를 가시화
2. **선행 산출물 기반 (Upstream-Driven)**: 테스트 전략과 범위는 RE/Arch/Impl 산출물에 근거하며, 임의의 판단이 아닌 구조화된 입력 기반으로 결정. RE `acceptance_criteria`가 테스트의 필요충분 조건
3. **적응적 깊이 (Adaptive Depth)**: Impl 모드에 연동하여 경량(핵심 단위 테스트 + 체크리스트)/중량(전체 피라미드 + NFR + RTM) 모드 자동 전환
4. **이중 커버리지 기준 (Dual Coverage)**: 코드 커버리지(라인/분기)와 요구사항 커버리지(RTM 기반)를 동시에 추적. 코드 커버리지 100%여도 요구사항 커버리지가 부족하면 품질 게이트 미통과
5. **테스트 피라미드 (Test Pyramid)**: 단위 > 통합 > E2E 비율 유지. 아키텍처 패턴에 따라 계약 테스트, NFR 테스트 등 추가 레이어 적용
6. **프레임워크 중립성**: 핵심 테스트 설계 원칙은 프레임워크에 독립적이되, Arch `technology_stack`에 따른 프레임워크별 관용구 존중
7. **자동 실행 + 결과 보고 (Auto-Execute with Result Reporting)**: 테스트 투자 범위는 MoSCoW 우선순위에서 자동 도출하고, 품질 게이트 기준은 합리적 기본값을 적용. 사용자에게는 **최종 품질 리포트만 제시**하며, Must 요구사항의 해소 불가능한 커버리지 갭이 발견된 경우에만 에스컬레이션
8. **메타데이터-문서 분리와 스크립트 경유 갱신 (Metadata/Document Separation)**: 구조화된 상태·추적·승인 데이터는 `*.meta.yaml`에, 서술형 맥락은 `*.md`에 분리 저장. 메타데이터는 `scripts/` 커맨드를 통해서만 갱신되며, 에이전트는 YAML을 직접 편집하지 않음. 문서는 `templates/`의 사전 정의된 골격을 `scripts/artifact.py init`으로 생성한 뒤 플레이스홀더만 편집하여, 스키마 일관성·추적성·승인 상태의 무결성을 보장
9. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **테스트 전략 / 테스트 스위트 / 요구사항 추적 매트릭스 / 품질 리포트** 4섹션으로 고정하여, 후속 스킬(`deployment`, `operation`, `management`, `security`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
10. **Claude Code Skill 표준 준수 (Skill Standard Compliance)**: `SKILL.md` 엔트리포인트 + YAML frontmatter(`name`/`description`/`allowed-tools`/`paths`/`hooks` 등) + supporting files(`agents/`, `prompts/`, `references/`, `scripts/`, `templates/`, `examples/`) 구조를 따르며, `${CLAUDE_SKILL_DIR}` 치환과 `` !`<command>` `` 동적 컨텍스트 주입을 적극 활용해 Skill 런타임과 정합
