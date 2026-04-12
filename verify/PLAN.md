# Verify Skill 구현 계획

## 개요

Impl 스킬의 산출물(구현 코드)과 DevOps 스킬의 산출물(파이프라인 설정, IaC, 관찰 가능성 설정, 런북)을 입력으로 받아, **로컬 환경에서 전체 시스템을 통합 실행하고, observability 스택을 통해 실제 동작을 관찰하며, 시스템이 설계 의도대로 작동하는지 검증**하는 스킬입니다.

DevOps가 "어떻게 배포하고 관찰할 것인가"를 **선언적 산출물**로 답했다면, Verify는 "그 선언이 **실제로 동작하는가**"를 로컬 환경에서 실증합니다. Observability 스택(메트릭, 로그, 트레이싱)은 검증의 목적이 아니라 **검증 과정의 관찰 용이성을 높이기 위한 수단**입니다. 구현된 코드가 아키텍처 의도대로 통합되는지, 컴포넌트 간 통신이 정상인지, 장애 시나리오에서 기대한 대로 동작하는지를 실행 환경에서 확인하고, 발견된 이슈를 진단·해결하는 것이 핵심 가치입니다.

### 전통적 통합 검증 vs AI 컨텍스트 Verify

| 구분 | 전통적 통합 검증 | AI 컨텍스트 Verify |
|------|-----------------|-------------------|
| 수행자 | DevOps/SRE 엔지니어가 수동으로 로컬 또는 스테이징에서 확인 | 개발자가 AI에게 로컬 통합 환경 구성과 검증을 위임 |
| 입력 | README의 "로컬 실행 방법", 구전 지식 | **Impl/DevOps 스킬의 구조화된 산출물** — 컴포넌트 구조, 기술 스택, observability 설정이 명시적 |
| 환경 구성 | docker-compose를 수동 작성, 시행착오 반복 | **Arch 컴포넌트 구조 + DevOps IaC/observability 설정 기반 자동 생성** |
| 관찰 수단 | `curl` + `docker logs` + 눈으로 확인 | **Prometheus + Grafana + Loki + Tempo 스택 자동 프로비저닝**, 대시보드/알림 규칙까지 DevOps 산출물에서 로드 |
| 검증 범위 | "일단 떠요" 수준, 주요 경로만 확인 | **Arch 시퀀스 다이어그램 기반 시나리오 자동 도출**, 정상 경로 + 장애 시나리오 + 부하 시나리오 체계적 검증 |
| 이슈 대응 | 로그 뒤져서 원인 추적, 수동 수정 | **구조화된 진단 → 원인 분류 → 자동 수정 또는 에스컬레이션** 파이프라인 |
| 산출물 | "확인했습니다" 슬랙 메시지 | **구조화된 검증 리포트** — 시나리오별 pass/fail, 메트릭 증거, 이슈 목록, 수정 이력 |
| 추적성 | 없음 | **RE 요구사항 → Arch 결정 → Impl 코드 → DevOps 설정 → Verify 결과**까지 전체 SDLC 추적성 완결 |

## 선행 스킬 산출물 소비 계약

Verify 스킬은 SDLC 파이프라인의 최종 검증 단계로서, 선행 스킬 전체의 산출물을 소비합니다. 직접 소비하는 것은 Impl과 DevOps이며, RE/Arch는 이들의 참조 체인을 통해 간접 소비합니다.

### Impl 산출물 소비 매핑

| Impl 산출물 섹션 | 주요 필드 | Verify에서의 소비 방법 |
|-----------------|-----------|---------------------|
| **구현 맵** | `module_path`, `component_ref`, `entry_point` | `module_path`로 빌드 대상 결정. `component_ref`로 Arch 컴포넌트와 컨테이너 매핑. `entry_point`로 서비스 실행 명령 도출 |
| **코드 구조** | `build_config`, `external_dependencies`, `environment_config` | `build_config`로 컨테이너 빌드 절차 결정. `external_dependencies`로 외부 서비스(DB, 캐시, 큐) 컨테이너 구성. `environment_config`로 서비스 간 연결 환경 변수 설정 |
| **구현 결정** | `pattern_applied`, `arch_refs` | 적용 패턴으로 검증 시나리오 도출 (예: CQRS → 읽기/쓰기 경로 독립 검증, Circuit Breaker → 장애 격리 검증) |
| **구현 가이드** | `prerequisites`, `build_commands`, `run_commands` | `prerequisites`로 빌드 환경 의존성 확인. `build_commands`로 이미지 빌드. `run_commands`로 서비스 실행 |

### DevOps 산출물 소비 매핑

| DevOps 산출물 섹션 | 주요 필드 | Verify에서의 소비 방법 |
|-------------------|-----------|---------------------|
| **파이프라인 설정** (`DEVOPS-PL-*`) | `deployment_method`, `rollback_trigger`, `rollback_procedure` | 배포 방식에 따른 검증 시나리오 구성 (카나리 → 버전 병행 테스트, 블루/그린 → 전환 테스트). 롤백 트리거 조건 실제 재현 검증 |
| **인프라 코드** (`DEVOPS-IAC-*`) | `modules`, `environments`, `networking` | IaC 모듈 구조를 로컬 docker-compose로 변환. 네트워킹 설정을 Docker 네트워크로 매핑 |
| **관찰 가능성** (`DEVOPS-OBS-*`) | `slo_definitions`, `monitoring_rules`, `dashboards`, `logging_config`, `tracing_config` | SLO 정의를 Prometheus에 로드하여 메트릭 수집 검증. 알림 규칙 문법/동작 검증. 대시보드를 Grafana에 로드하여 렌더링 확인. 로깅 설정을 Loki로 인제스트 검증. 트레이싱 설정을 Tempo로 전파 검증 |
| **런북** (`DEVOPS-RB-*`) | `trigger_condition`, `diagnosis_steps`, `remediation_steps` | 런북 트리거 조건을 실제 재현하여 진단 절차의 실행 가능성 검증. 조치 절차의 적용 가능성 확인 |

### Arch 산출물 간접 참조

| Arch 산출물 | 간접 참조 경로 | Verify에서의 영향 |
|------------|---------------|------------------|
| **컴포넌트 구조** | Impl `component_ref` → `ARCH-COMP-*` | 컴포넌트 간 의존성 순서로 서비스 기동 순서 결정, 인터페이스로 헬스 체크 엔드포인트 도출 |
| **다이어그램** | Arch `ARCH-DIAG-*` sequence/data-flow | 시퀀스 다이어그램에서 통합 검증 시나리오 자동 도출, 데이터 흐름에서 트레이싱 전파 경로 검증 기준 도출 |
| **기술 스택** | Arch `ARCH-TECH-*` | 기술 스택별 적절한 observability 계측 라이브러리 선택 (OpenTelemetry SDK, Micrometer 등) |

### RE 산출물 간접 참조

| RE 산출물 | 간접 참조 경로 | Verify에서의 영향 |
|-----------|---------------|------------------|
| **품질 속성 우선순위** | Arch `re_refs` → DevOps SLO | SLO 메트릭의 실제 측정 가능성 검증 (정의된 SLI가 실제로 메트릭으로 수집되는지 확인) |
| **제약 조건** | Arch `constraint_ref` → DevOps logging | 규제 제약에 따른 로그 마스킹 동작 검증 (PII가 실제로 마스킹되는지 확인) |

### 추적성 체인 (RE → Arch → Impl → DevOps → Verify)

Verify는 전체 SDLC 추적성 체인의 최종 실증 지점입니다. 선행 스킬 체인이 "문서 상의 정합성"을 보장했다면, Verify는 "실행 상의 정합성"을 보장합니다.

```
RE:spec 산출물        Arch 산출물         Impl 산출물         DevOps 산출물        Verify 산출물
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ QA:perf      │──│ AD-001       │──│ IM-001       │──│ DEVOPS-OBS   │──│ VR-001       │
│  metric:     │  │  decision    │  │  module_path │  │  slo_defs    │  │  scenario    │
│  "<200ms"    │  │  re_refs     │  │  component   │  │  mon_rules   │  │  evidence    │
│              │  │              │  │  _ref        │  │  dashboards  │  │  (메트릭     │
│              │  │ COMP-001     │──│ IDR-001      │──│ DEVOPS-PL    │──│   스크린샷,  │
│ FR-001       │──│  type:       │  │  pattern     │  │  deploy      │  │   로그,      │
│  acceptance  │  │  service     │  │  _applied    │  │  _method     │  │   트레이스)  │
│  _criteria   │  │  interfaces  │  │              │  │  rollback    │  │  verdict     │
│              │  │  deps        │  │              │  │  _trigger    │  │  issues      │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
         문서 상의 정합성 (Traceability)                    ↔         실행 상의 정합성 (Verification)
```

### 적응적 깊이

Arch/Impl 모드에 연동하여 Verify 산출물 수준을 자동 조절합니다.

| Arch/Impl 모드 | 판별 기준 | Verify 모드 | 검증 수준 |
|---------------|-----------|-------------|----------|
| 경량 | Arch 컴포넌트 ≤ 3개, 단일 배포 환경 | 경량 | 단일 docker-compose + 기본 observability (Prometheus + Grafana) + 주요 경로 시나리오 3개 이내 + 헬스 체크 검증 |
| 중량 | Arch 컴포넌트 > 3개 또는 멀티 환경/리전 | 중량 | 전체 observability 스택 (Prometheus + Grafana + Loki + Tempo) + 정상/장애/부하 시나리오 + 분산 트레이싱 전파 검증 + SLO 메트릭 수집 검증 + 로그 마스킹 검증 |

상세 판별 규칙은 `references/adaptive-depth.md`에 분리합니다.

## 최종 산출물 구조

Verify 스킬의 최종 산출물은 다음 **세 가지 카테고리**로 구성됩니다. 로컬 환경 구성, 시나리오 실행, 검증 결과를 범위로 합니다.

### 1. 환경 설정 (Environment Setup)

로컬 통합 실행 환경의 구성 파일을 생성합니다. 워크플로우 `provision` 단계의 산출물입니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `VERIFY-ENV-001`) |
| `compose_config` | docker-compose 설정 — 애플리케이션 서비스 + 인프라 서비스(DB, 캐시, 큐) + observability 스택 |
| `services` | 서비스 목록 — 이름, 이미지/빌드 경로, 포트, 의존성, 헬스 체크, 환경 변수 |
| `observability_stack` | observability 컴포넌트 — Prometheus, Grafana, Loki, Tempo 설정 및 프로비저닝 |
| `network_topology` | Docker 네트워크 구성 — 서비스 간 통신 경로, 외부 노출 포트 |
| `startup_order` | 서비스 기동 순서 — Arch 의존성 그래프 기반, 헬스 체크 대기 조건 |
| `arch_refs` | 매핑 대상 Arch 컴포넌트 ID |
| `devops_refs` | 참조한 DevOps 산출물 ID (IaC, observability) |

### 2. 검증 시나리오 (Verification Scenarios)

Arch 시퀀스 다이어그램과 요구사항에서 도출된 검증 시나리오입니다. 워크플로우 `scenario` 단계의 산출물입니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `VERIFY-SC-001`) |
| `category` | 시나리오 분류 (`integration` / `failure` / `load` / `observability`) |
| `title` | 시나리오 제목 |
| `description` | 검증 목적 설명 |
| `preconditions` | 사전 조건 (서비스 상태, 데이터 초기화 등) |
| `steps` | 실행 단계 — HTTP 요청, 메시지 발행, 장애 주입 등 |
| `expected_results` | 기대 결과 — 응답 상태, 메트릭 변화, 로그 출력, 트레이스 생성 |
| `evidence_type` | 증거 유형 (`metric` / `log` / `trace` / `response` / `dashboard`) |
| `arch_refs` | 근거 Arch 다이어그램/컴포넌트 ID |
| `re_refs` | 근거 RE 요구사항 ID (acceptance_criteria) |
| `slo_refs` | 관련 SLO ID (observability 시나리오의 경우) |

### 3. 검증 리포트 (Verification Report)

검증 실행 결과를 구조화한 리포트입니다. 워크플로우 `execute` + `report` 단계의 산출물입니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `VERIFY-RPT-001`) |
| `verdict` | 전체 판정 (`pass` / `pass_with_issues` / `fail`) |
| `scenario_results` | 시나리오별 결과 — `scenario_id`, `status` (pass/fail/skip), `evidence`, `duration` |
| `evidence_artifacts` | 수집된 증거 — 메트릭 쿼리 결과, 로그 샘플, 트레이스 ID, 대시보드 스크린샷 경로 |
| `issues` | 발견된 이슈 목록 — `severity`, `category`, `description`, `root_cause`, `resolution`, `status` |
| `environment_health` | 환경 상태 요약 — 서비스별 헬스 상태, 리소스 사용량 |
| `slo_validation` | SLO 메트릭 수집 검증 결과 — `slo_id`, `metric_collected` (bool), `sample_value`, `threshold` |
| `feedback` | 선행 스킬 피드백 — 발견된 이슈가 어느 스킬의 산출물에서 기인하는지 분류 |
| `arch_refs` / `impl_refs` / `devops_refs` / `re_refs` | 추적성 참조 |

### 산출물 파일 구성: 메타데이터 + 문서 분리

다른 스킬과 동일하게 **메타데이터 파일(YAML)과 문서 파일(Markdown)을 분리**하여 저장합니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 파일 | **YAML** (`*.meta.yaml`) | 진행 상태, 승인 상태, 추적성, 카테고리별 구조화 필드 — 스크립트가 읽고 쓰는 단일 진실 공급원(SSoT) |
| 문서 파일 | Markdown (`*.md`) | 사람이 읽는 본문 — 시나리오 서술, 증거 첨부, 이슈 분석 |

### 스크립트 기반 메타데이터 조작 (필수)

다른 스킬과 동일하게 에이전트는 **YAML 메타데이터 파일을 직접 편집하지 않습니다**. 모든 상태 갱신은 `${SKILL_DIR}/scripts/artifact.py`를 통해서만 수행합니다.

### 후속 스킬 연계

```
verify 산출물 구조:
┌─────────────────────────────────────────┐
│  환경 설정 (Environment Setup)           │──→ devops:review (환경 구성 정합성 피드백)
│  - VERIFY-ENV-001: docker-compose       │──→ impl:refactor (환경 호환 이슈 피드백)
│  - observability stack provisioning     │
├─────────────────────────────────────────┤
│  검증 시나리오 (Verification Scenarios)   │──→ qa:report (통합 테스트 커버리지 보완)
│  - VERIFY-SC-001~N: 통합/장애/부하       │──→ arch:review (아키텍처 결정 실증 근거)
├─────────────────────────────────────────┤
│  검증 리포트 (Verification Report)       │──→ devops:review (observability 설정 피드백)
│  - VERIFY-RPT-001: 시나리오별 결과       │──→ sec:audit (런타임 보안 검증 근거)
│  - 이슈 목록 + 수정 이력                 │──→ orch:status (SDLC 파이프라인 완결 근거)
└─────────────────────────────────────────┘
```

## 핵심 개념: Observability as Verification Lens

Observability 스택은 Verify의 **목적이 아니라 수단**입니다. 전통적 통합 테스트가 "요청 → 응답" 차원에서만 검증하는 한계를 observability 스택이 보완합니다.

| 관찰 계층 | 도구 | 검증에 기여하는 바 |
|----------|------|------------------|
| **메트릭** | Prometheus + Grafana | 요청이 처리되었는가? 지연시간은 SLO 범위 내인가? 에러율은? — DevOps가 정의한 SLI/SLO를 실제로 측정할 수 있는지 확인 |
| **로그** | Loki | 각 서비스가 구조화된 로그를 올바르게 출력하는가? 상관 ID가 전파되는가? 민감 정보가 마스킹되는가? — DevOps logging_config의 실제 동작 검증 |
| **트레이싱** | Tempo (또는 Jaeger) | 요청이 컴포넌트 간 올바르게 전파되는가? 병목 지점은 어디인가? — Arch 시퀀스 다이어그램의 실제 동작 검증 |

이 세 축의 관찰을 결합하면 단순한 "떠요/안 떠요"를 넘어 **"설계 의도대로 동작하는가"**를 실증할 수 있습니다.

## 워크플로우 단계

6개 단계로 구성되며, 의존성 그래프를 가집니다.

```
Impl 산출물 (IMPL-MAP / IMPL-CODE / IMPL-IDR / IMPL-GUIDE, all approved)
DevOps 산출물 (DEVOPS-PL / DEVOPS-IAC / DEVOPS-OBS / DEVOPS-RB, all approved)
Arch 산출물 (간접 참조)
    │
    ▼
[1] provision   → Impl 코드 + DevOps IaC/OBS → docker-compose 환경 생성
    │              app 서비스 + infra 서비스 + observability 스택
    │
    ▼
[2] instrument  → 계측 확인 — 앱에 OpenTelemetry/메트릭/로깅 계측이 있는지 확인
    │              누락 시 최소 계측 코드 주입 제안
    │
    ▼
[3] scenario    → Arch 시퀀스 다이어그램 + RE acceptance_criteria → 검증 시나리오 도출
    │              정상 경로 / 장애 시나리오 / 부하 시나리오 / observability 검증
    │
    ▼
[4] execute     → 환경 기동 + 시나리오 순차 실행 + 증거 수집
    │              메트릭 쿼리, 로그 검색, 트레이스 조회로 증거 확보
    │
    ▼
[5] diagnose    → 실패 시나리오 분석 + 이슈 분류 + 수정
    │              이슈 원인을 선행 스킬(impl/devops/arch) 산출물로 역추적
    │              자동 수정 가능한 이슈는 수정 후 재검증
    │
    ▼
[6] report      → 검증 리포트 생성 + 선행 스킬 피드백 + 전체 판정
```

각 워크플로우 파일에는 **역할 / 핵심 역량 / 입력 / 출력 / 상호작용 모델 / 에스컬레이션 조건**이 기술됩니다.

### `references/workflow/provision.md` — 환경 프로비저닝 단계
- **역할**: Impl 코드와 DevOps 산출물을 기반으로 로컬 통합 실행 환경 자동 구성
- **핵심 역량**:
  - `ARCH-COMP-*.type` → Docker 서비스 매핑 (`service` → 앱 컨테이너, `store` → DB 컨테이너, `queue` → 메시징 컨테이너)
  - `IMPL-GUIDE-*.build_commands` → Dockerfile 빌드 단계
  - `DEVOPS-OBS-*` → Prometheus/Grafana/Loki/Tempo 설정 파일 프로비저닝
  - `DEVOPS-OBS-*.dashboards` → Grafana 대시보드 자동 로드
  - `DEVOPS-OBS-*.monitoring_rules` → Prometheus alerting rules 자동 로드
  - 서비스 간 의존성 기반 헬스 체크 + 기동 순서 결정
  - Docker 네트워크 구성으로 서비스 간 DNS 기반 통신 보장
- **입력**: Impl `implementation_map`, `code_structure`, `implementation_guide`, DevOps `iac`, `observability`
- **출력**: 환경 설정 카테고리 (`VERIFY-ENV-*`)
- **상호작용 모델**: 자동 생성 → Docker 데몬 가용성/포트 충돌 시 사용자에게 확인
- **에스컬레이션 조건**: Docker 데몬 미실행, 필수 포트 점유, 리소스(메모리/디스크) 부족, Impl 코드가 빌드 불가

### `references/workflow/instrument.md` — 계측 확인 단계
- **역할**: 애플리케이션 코드에 observability 계측이 적절히 설정되어 있는지 확인하고, 누락 시 보완 제안
- **핵심 역량**:
  - `ARCH-TECH-*.choice` 기반 적절한 계측 라이브러리 판별 (OpenTelemetry, Micrometer, structlog 등)
  - 메트릭 엔드포인트 노출 확인 (`/metrics`, `/actuator/prometheus` 등)
  - 구조화 로깅 설정 확인 (JSON 포맷, 필수 필드)
  - 트레이싱 전파 설정 확인 (W3C Trace Context 헤더)
  - 누락 계측에 대한 최소 침습적 보완 코드 제안
- **입력**: Impl 코드, DevOps `observability` (logging_config, tracing_config)
- **출력**: 계측 상태 리포트 (환경 설정 카테고리에 추가)
- **상호작용 모델**: 자동 검사 → 누락 발견 시 보완 방법을 사용자에게 제안
- **에스컬레이션 조건**: 기술 스택이 OpenTelemetry를 지원하지 않는 경우, 계측 추가가 코드 구조를 크게 변경해야 하는 경우

### `references/workflow/scenario.md` — 검증 시나리오 도출 단계
- **역할**: Arch 시퀀스 다이어그램과 RE acceptance_criteria에서 검증 시나리오를 체계적으로 도출
- **핵심 역량**:
  - `ARCH-DIAG-*.sequence` → 정상 경로 통합 시나리오 (각 시퀀스가 하나의 시나리오)
  - `ARCH-COMP-*.dependencies` → 장애 시나리오 (의존 서비스 중단, 지연, 에러 반환)
  - `DEVOPS-OBS-*.slo_definitions` → SLO 검증 시나리오 (메트릭이 실제로 수집되는지)
  - `DEVOPS-OBS-*.monitoring_rules` → 알림 규칙 검증 (조건 발동 시 실제 알림 생성)
  - `DEVOPS-OBS-*.logging_config` → 로깅 검증 (포맷, 상관 ID, 마스킹)
  - `DEVOPS-RB-*.trigger_condition` → 런북 트리거 재현 시나리오
  - RE `acceptance_criteria` → 비즈니스 로직 수준 통합 검증
- **입력**: Arch `diagrams`, `component_structure`, DevOps `observability`, `runbooks`, RE (간접)
- **출력**: 검증 시나리오 카테고리 (`VERIFY-SC-*`)
- **상호작용 모델**: 시나리오 자동 도출 → 사용자에게 우선순위/범위 확인
- **에스컬레이션 조건**: 없음 — 시나리오는 선행 산출물에서 기계적 도출

### `references/workflow/execute.md` — 검증 실행 단계
- **역할**: 프로비저닝된 환경에서 시나리오를 순차 실행하고 증거를 수집
- **핵심 역량**:
  - docker-compose 환경 기동 + 모든 서비스 헬스 체크 통과 대기
  - 시나리오별 실행: HTTP 요청 발송, 메시지 발행, 장애 주입 (컨테이너 중단/네트워크 지연)
  - 증거 수집: Prometheus 쿼리(PromQL), Loki 쿼리(LogQL), Tempo 쿼리(트레이스 ID), HTTP 응답
  - 시나리오 결과 판정: expected_results 대비 실제 결과 비교
  - 환경 상태 모니터링: 서비스 헬스, 리소스 사용량
- **입력**: 환경 설정 (`VERIFY-ENV-*`), 검증 시나리오 (`VERIFY-SC-*`)
- **출력**: 시나리오 실행 결과 (검증 리포트 카테고리에 입력)
- **상호작용 모델**: 자동 실행 → 실패 시 중단 또는 계속 여부 사용자 확인
- **에스컬레이션 조건**: 환경 기동 실패 (컨테이너 크래시, OOM), 네트워크 연결 불가

### `references/workflow/diagnose.md` — 진단 및 수정 단계
- **역할**: 실패한 시나리오의 원인을 분석하고, 이슈를 선행 스킬 산출물로 역추적하여 분류·수정
- **핵심 역량**:
  - 실패 시나리오의 증거(로그, 메트릭, 트레이스)를 분석하여 근본 원인 식별
  - 이슈 원인을 선행 스킬로 분류:
    - `impl` 원인: 코드 버그, 환경 변수 오설정, 빌드 오류
    - `devops` 원인: observability 설정 오류 (잘못된 PromQL, 대시보드 쿼리 오류, 로깅 포맷 불일치)
    - `arch` 원인: 컴포넌트 간 인터페이스 불일치, 의존성 순환
  - 자동 수정 가능한 이슈 (오타, 설정 오류 등)는 수정 후 해당 시나리오 재실행
  - 자동 수정 불가한 이슈는 원인 스킬에 대한 피드백으로 기록
- **입력**: 실패 시나리오 결과, 증거 아티팩트
- **출력**: 이슈 목록 + 수정 이력 (검증 리포트에 병합)
- **상호작용 모델**: 자동 진단 → 수정 제안 시 사용자 확인 → 수정 적용 → 재검증
- **에스컬레이션 조건**: 근본 원인이 Arch 레벨 구조 변경을 요구하는 경우

### `references/workflow/report.md` — 검증 리포트 생성 단계
- **역할**: 전체 검증 결과를 구조화된 리포트로 생성하고, 선행 스킬에 대한 피드백을 분류
- **핵심 역량**:
  - 시나리오별 pass/fail 집계 + 전체 verdict 판정
  - 증거 아티팩트 정리 (메트릭 쿼리 결과, 로그 샘플, 트레이스 ID)
  - SLO 메트릭 수집 검증 결과 (DevOps가 정의한 SLI가 실제로 측정 가능한지)
  - 이슈 목록과 수정 이력 정리
  - 선행 스킬 피드백 분류: 어떤 이슈가 어느 스킬의 개선으로 해결 가능한지
  - SDLC 추적성 체인 완결 근거 제시
- **입력**: 전체 실행 결과, 이슈 목록, 증거
- **출력**: 검증 리포트 카테고리 (`VERIFY-RPT-*`)
- **에스컬레이션 조건**: 없음 — 순수 집계/분석

### 서브에이전트 위임

| 단계 | 실행 위치 | 이유 |
|------|---------|------|
| 1. provision | main | docker-compose 생성 시 Impl/DevOps 산출물을 종합적으로 참조해야 하며, 환경 이슈 발생 시 사용자와 즉시 소통 필요 |
| 2. instrument | main | 코드 수정 제안이 필요할 수 있어 사용자 승인 필요 |
| 3. scenario | **subagent** | Arch 다이어그램에서 시나리오를 기계적으로 도출 — 깨끗한 컨텍스트가 더 체계적인 시나리오 생성 |
| 4. execute | main | 환경과 실시간 상호작용 (docker exec, HTTP 요청, 장애 주입), 실패 시 사용자 판단 필요 |
| 5. diagnose | main | 이슈 수정 시 코드/설정 변경이 필요하여 사용자 승인 필요 |
| 6. report | **subagent** | 수집된 결과에서 리포트를 기계적으로 생성 — 깨끗한 컨텍스트가 더 객관적인 판정 |

## 목표 구조 (Claude Code Skill 표준 준수)

```
verify/
├── SKILL.md                              # 필수 진입점 (frontmatter + 6단계 워크플로우 요약, 500줄 이내)
├── scripts/
│   └── artifact.py                       # 메타데이터 init/set-phase/approve/link/validate/list + report 관리
├── assets/
│   └── templates/
│       ├── environment.md.tmpl           # 환경 설정 문서 템플릿
│       ├── environment.meta.yaml.tmpl    # 환경 설정 메타데이터 템플릿
│       ├── scenario.md.tmpl              # 검증 시나리오 문서 템플릿
│       ├── scenario.meta.yaml.tmpl       # 검증 시나리오 메타데이터 템플릿
│       ├── report.md.tmpl                # 검증 리포트 문서 템플릿
│       ├── report.meta.yaml.tmpl         # 검증 리포트 메타데이터 템플릿
│       └── docker-compose.tmpl           # docker-compose 기본 골격 (observability 스택 포함)
└── references/
    ├── workflow/
    │   ├── provision.md                  # 환경 프로비저닝 단계 상세 규칙
    │   ├── instrument.md                 # 계측 확인 단계 상세 규칙
    │   ├── scenario.md                   # 검증 시나리오 도출 단계 상세 규칙
    │   ├── execute.md                    # 검증 실행 단계 상세 규칙
    │   ├── diagnose.md                   # 진단 및 수정 단계 상세 규칙
    │   └── report.md                     # 검증 리포트 생성 단계 상세 규칙
    ├── contracts/
    │   ├── impl-input-contract.md        # Impl 산출물 → 환경 구성 매핑
    │   ├── devops-input-contract.md      # DevOps 산출물 → observability 스택 구성 매핑
    │   ├── arch-input-contract.md        # Arch 산출물 → 시나리오 도출 매핑
    │   ├── subagent-report-contract.md   # 서브에이전트 핸드오프 리포트 계약
    │   └── downstream-contract.md        # 후속 스킬 소비 계약
    ├── schemas/
    │   ├── meta-schema.md                # 메타데이터 공통 필드 명세
    │   └── section-schemas.md            # 3카테고리 필드 명세
    ├── stacks/
    │   ├── observability.md              # Prometheus + Grafana + Loki + Tempo 스택 구성 가이드
    │   └── fault-injection.md            # 장애 주입 기법 카탈로그 (컨테이너 중단, 네트워크 지연, 리소스 제한)
    ├── adaptive-depth.md                 # 경량/중량 분기 규칙
    └── examples/
        ├── light/                        # 단일 서비스 + 기본 observability + 핵심 시나리오 예시
        └── heavy/                        # 마이크로서비스 + 전체 스택 + 종합 시나리오 예시
```

## 핵심 설계 원칙

1. **Observability는 수단, 검증이 목적 (Observability as a Lens)**: observability 스택은 "시스템이 관찰 가능한가"를 검증하는 것이 아니라, "시스템이 설계 의도대로 동작하는가"를 관찰하기 위한 렌즈. 메트릭·로그·트레이싱은 검증 시나리오의 증거 수집 수단
2. **SDLC 추적성 완결 (Traceability Closure)**: RE → Arch → Impl → QA → DevOps → Verify로 이어지는 추적성 체인의 최종 실증 지점. "문서 상의 정합성"(선행 스킬들)을 "실행 상의 정합성"으로 전환
3. **선행 산출물 기반 (Predecessor-Driven)**: 환경 구성은 Arch/Impl에서 자동 도출, 시나리오는 Arch 다이어그램에서 자동 도출, observability 설정은 DevOps 산출물에서 로드. 수동 구성 최소화
4. **이슈 역추적 및 피드백 (Issue Backtracking)**: 발견된 이슈를 원인 스킬(impl/devops/arch)로 역추적하여 피드백. Verify는 문제를 발견할 뿐 아니라 어디서 고쳐야 하는지를 가리킴
5. **로컬 환경 한정 (Local Scope)**: Docker Compose 기반 로컬 실행만 범위. 클라우드 환경 배포, 성능 벤치마킹, 프로덕션 검증은 범위 밖. 로컬에서 확인 가능한 수준의 통합 검증에 집중
6. **적응적 깊이 (Adaptive Depth)**: Arch/Impl 모드에 연동. 단일 서비스는 기본 observability + 핵심 시나리오, 분산 시스템은 전체 스택 + 종합 시나리오
7. **비파괴적 실행 (Non-Destructive Execution)**: docker-compose up/down으로 환경을 깨끗하게 생성/정리. 호스트 시스템에 영구적 변경 없음. 장애 주입도 컨테이너 레벨로 격리
8. **메타데이터-문서 분리 및 스크립트 경유 원칙**: 다른 스킬과 동일하게 메타데이터는 `scripts/artifact.py`를 통해서만 조작

## 구현 단계

### 1단계: `SKILL.md` 작성

**권장 frontmatter 초안**:

```yaml
---
name: verify
description: Impl 구현 코드와 DevOps 산출물을 입력으로 받아, Docker Compose 기반 로컬 환경에서 전체 시스템을 통합 실행하고 observability 스택(Prometheus/Grafana/Loki/Tempo)으로 관찰하며, Arch 시퀀스 다이어그램에서 도출한 시나리오로 설계 의도대로 동작하는지 검증한다. 이슈 발견 시 원인 스킬로 역추적하여 진단·수정한다.
---
```

**SKILL.md 본문 구성 (500줄 이내)**:
1. 스킬 개요 (Impl + DevOps 산출물 → 로컬 통합 검증)
2. 입력/출력 계약 요약 (상세는 `references/contracts/*.md`)
3. 핵심 개념: Observability as Verification Lens
4. 적응적 깊이 분기 로직
5. 6단계 워크플로우 요약 (각 단계 진입 시 `references/workflow/<stage>.md`를 Read로 로드)
6. 스크립트 호출 규약
7. 시작 시 상태 주입

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

6개 단계의 상세 행동 규칙을 `references/workflow/`에 분리. 특히 `provision.md`에는 docker-compose 생성 규칙(서비스 매핑, 네트워크, 헬스 체크), `execute.md`에는 시나리오 실행 프로토콜(증거 수집 방법, 판정 기준)을 상세화.

### 3단계: 참조 문서 작성 (`references/`)

- `references/contracts/*.md` (5개): 입력 계약, 서브에이전트 리포트 계약, 하류 소비 계약
- `references/schemas/*.md` (2개): 메타데이터 공통 필드, 3카테고리 도메인 필드
- `references/stacks/observability.md`: Prometheus + Grafana + Loki + Tempo 구성 가이드 — 서비스 디스커버리, 데이터소스 프로비저닝, 대시보드 자동 로드
- `references/stacks/fault-injection.md`: 장애 주입 기법 — `docker stop`, `tc netem` 지연, 메모리 제한, DNS 차단
- `references/adaptive-depth.md`: 경량/중량 분기 규칙

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

3카테고리(`environment`, `scenario`, `report`)별 markdown/메타데이터 템플릿 + docker-compose 기본 골격 템플릿.

### 5단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

다른 스킬의 `artifact.py`와 동일한 인터페이스. `init --section <environment|scenario|report>` + 표준 서브커맨드.

### 6단계: 입출력 예시 작성 (`references/examples/`)

- **경량 예시 (`light/`)**: 단일 웹 서비스 + PostgreSQL, Prometheus + Grafana만 사용, 헬스 체크 + API 응답 검증 + 메트릭 수집 확인
- **중량 예시 (`heavy/`)**: 마이크로서비스 3개 + DB + 캐시 + 큐, 전체 observability 스택, 정상/장애/부하 시나리오, 분산 트레이싱 전파 검증, SLO 메트릭 검증, 로그 마스킹 검증
