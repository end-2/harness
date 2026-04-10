# DevOps Skill 구현 계획

## 개요

Arch/Impl 스킬의 산출물과 RE 품질 속성을 입력으로 받아, **설계된 시스템을 배포하고 운영하기 위한 인프라, 파이프라인, 관찰 가능성을 자동 생성**하는 스킬입니다.

Impl이 "코드로 어떻게 구현할 것인가"를 실행했다면, DevOps는 "그 코드를 어떻게 배포하고, 배포된 시스템을 어떻게 관찰·운영할 것인가"를 결정합니다. 배포(Deploy)와 관찰(Observe)을 **하나의 피드백 루프**로 통합하여, 배포 전략이 모니터링을 결정하고 모니터링 결과가 배포 결정(롤백, 프로모션)에 피드백되는 연속 사이클을 구현합니다.

RE/Arch/Impl에서 의사결정이 완료된 상태이므로, DevOps는 Impl과 동일한 **자동 실행 + 예외 에스컬레이션** 모델을 채택합니다. 선행 스킬 산출물을 기계적으로 인프라/파이프라인/모니터링 설정으로 변환하는 것이 핵심이며, **선행 결정이 DevOps 레벨에서 실현 불가능한 경우에만 사용자에게 에스컬레이션**합니다.

### 전통적 DevOps vs AI 컨텍스트 DevOps

| 구분 | 전통적 DevOps | AI 컨텍스트 DevOps |
|------|-------------|-------------------|
| 수행자 | 전담 DevOps/SRE 엔지니어 | 개발자가 AI에게 인프라/파이프라인/모니터링 생성을 위임 |
| 입력 | 구두 요청, 티켓, 위키 문서 | **Arch/Impl 스킬의 구조화된 산출물** + RE 품질 속성 메트릭 |
| 파이프라인 구성 | 수동 YAML 작성, 시행착오 반복 | **Impl 코드 구조/빌드 설정 기반 자동 파이프라인 생성** |
| 인프라 설계 | 아키텍트/DevOps 간 구두 조율 | **Arch 컴포넌트 구조 → IaC 자동 변환** |
| 모니터링 설계 | 경험 기반 임계값, 알림 피로 빈번 | **RE 품질 속성 메트릭 → SLO → 알림 규칙 체계적 도출** |
| 배포 전략 | 팀 관행, 과거 경험 기반 | **SLO + 아키텍처 특성 기반 전략 자동 추천** |
| 런북 | 장애 경험 후 사후 작성, 관리 부재 | **배포 전략 + 모니터링 설정 기반 자동 생성** |
| 배포-운영 연계 | 별도 팀/프로세스, 지연된 피드백 | **Deploy → Observe 피드백 루프를 단일 스킬 내에서 자동 연결** |

## 선행 스킬 산출물 소비 계약

DevOps 스킬은 Arch, Impl, RE의 산출물을 소비합니다. Arch/Impl은 직접 소비하고, RE는 Arch 산출물의 참조(`re_refs`, `constraint_ref`)를 통해 간접 소비합니다.

### Arch 출력 → DevOps 소비 매핑

| Arch 산출물 섹션 | 주요 필드 | DevOps에서의 소비 방법 |
|-----------------|-----------|---------------------|
| **아키텍처 결정** | `id`, `decision`, `trade_offs`, `re_refs` | `decision`에서 배포 단위(모놀리식 vs 서비스별) 결정, 스케일링 전략 도출. `trade_offs`로 배포 방식 선택의 근거 확보. `re_refs`로 RE까지 추적성 유지 |
| **컴포넌트 구조** | `id`, `name`, `type`, `interfaces`, `dependencies` | `type`(`service`/`gateway`/`store`/`queue` 등)으로 인프라 리소스 유형(컴퓨팅, DB, 메시징 등) 결정. `dependencies`로 배포 순서 및 서비스 의존성 설정. `interfaces`로 헬스 체크 엔드포인트 및 모니터링 지점 도출 |
| **기술 스택** | `category`, `choice`, `constraint_ref` | `choice`로 런타임/DB/메시징 인프라 리소스 선택. `constraint_ref`로 RE 제약(클라우드 프로바이더, 리전, 컴플라이언스 등) 준수 확인 |
| **다이어그램** | `type`, `code` | `c4-container`로 배포 토폴로지 도출. `data-flow`로 서비스 간 통신 경로 및 모니터링 지점 식별 |

### Impl 출력 → DevOps 소비 매핑

| Impl 산출물 섹션 | 주요 필드 | DevOps에서의 소비 방법 |
|-----------------|-----------|---------------------|
| **구현 맵** | `module_path`, `component_ref` | 모듈 경로로 빌드 대상 결정. `component_ref`로 Arch 컴포넌트와 배포 단위 매핑 확정 |
| **코드 구조** | `build_config`, `external_dependencies`, `environment_config` | `build_config`로 CI 파이프라인 빌드 스테이지 구성. `external_dependencies`로 의존성 캐싱 전략 결정. `environment_config`로 시크릿/환경 변수 관리 설계 |
| **구현 결정** | `pattern_applied`, `arch_refs` | 적용된 패턴으로 운영 특성 파악 (예: CQRS → 읽기/쓰기 분리 모니터링, Event Sourcing → 이벤트 스토어 모니터링) |
| **구현 가이드** | `prerequisites`, `build_commands`, `run_commands` | `build_commands`로 CI 빌드 스테이지 생성. `run_commands`로 컨테이너 엔트리포인트/헬스 체크 설정. `prerequisites`로 CI 환경 런타임 설정 |

### RE 산출물 간접 참조

DevOps는 RE 산출물을 직접 소비하지 않으나, Arch 산출물의 `re_refs`와 `constraint_ref`를 통해 간접 참조합니다.

| RE 산출물 | 간접 참조 경로 | DevOps에서의 영향 |
|-----------|---------------|------------------|
| **요구사항 명세** | Arch `component_structure.re_refs` → `FR-xxx`, `NFR-xxx` | NFR의 가용성/성능 요구사항으로 배포 전략(무중단 여부, 멀티 리전) 결정 |
| **제약 조건** | Arch `technology_stack.constraint_ref` → `CON-xxx` | `hard` 제약(특정 클라우드, 리전, 컴플라이언스)을 IaC 프로바이더 선택과 로깅 보존 정책에 비협상 조건으로 반영 |
| **품질 속성 우선순위** | Arch `architecture_decisions.re_refs` → `QA:xxx` | `metric`("응답시간 < 200ms", "99.9% 가용성")을 SLI/SLO 정의의 **직접 근거**로 사용. `priority`로 모니터링/알림 우선순위 결정 |

### 적응적 깊이 연동

Arch/Impl의 모드에 연동하여 DevOps의 산출물 수준을 자동 조절합니다.

| Arch/Impl 모드 | 판별 기준 | DevOps 모드 | 산출물 수준 |
|---------------|-----------|-------------|------------|
| 경량 | Arch 컴포넌트 ≤ 3개, 단일 배포 환경 | 경량 | 단일 파이프라인 + 기본 IaC + 핵심 SLO 3개 이내 + 기본 모니터링 + 핵심 런북 |
| 중량 | Arch 컴포넌트 > 3개 또는 멀티 환경/리전 | 중량 | 멀티 스테이지 파이프라인 + 환경별 IaC 모듈 + 종합 SLO + RED/USE 모니터링 + 분산 추적 + 상세 런북 + 로깅 표준 |

## 최종 산출물 구조

DevOps 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. 인프라 프로비저닝, 코드 배포, 시스템 관찰까지를 범위로 하며, 비즈니스 로직 구현이나 테스트 작성은 선행 스킬(`impl`, `qa`)의 영역입니다.

### 1. 파이프라인 설정 (Pipeline Configuration)

CI/CD 워크플로 설정과 배포 전략을 정의합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `PL-001`) |
| `platform` | CI/CD 플랫폼 (`github-actions` / `jenkins` / `gitlab-ci`) |
| `trigger` | 트리거 조건 (브랜치, 태그, PR 등) |
| `stages` | 스테이지 목록 (빌드, 테스트, 보안 스캔, 배포) — 각 스테이지의 명령어, 의존성, 조건 포함 |
| `caching` | 캐싱 전략 (의존성 캐시 키, 빌드 아티팩트 경로) |
| `secrets` | 필요한 시크릿 목록 (이름, 주입 방법, 소스) |
| `environments` | 대상 환경 목록 및 승격(promotion) 규칙 |
| `deployment_method` | 배포 방식 (`blue-green` / `canary` / `rolling` / `recreate`) 및 선택 근거 |
| `rollback_trigger` | 자동 롤백 트리거 조건 (SLO 위반, 헬스 체크 실패 등) |
| `rollback_procedure` | 롤백 절차 (단계, 검증, 알림) |
| `impl_refs` | 참조한 Impl 산출물 ID (`IM-xxx` 등) |
| `arch_refs` | 참조한 Arch 산출물 ID (`AD-xxx`, `COMP-xxx` 등) |
| `config_files` | 생성된 설정 파일 목록 및 경로 |

### 2. 인프라 코드 (Infrastructure Code)

IaC 모듈과 환경별 설정을 정의합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `IAC-001`) |
| `tool` | IaC 도구 (`terraform` / `ansible` / `helm` / `pulumi`) |
| `provider` | 클라우드 프로바이더 (`aws` / `gcp` / `azure`) |
| `modules` | 모듈 목록 (이름, 경로, 책임, 입력/출력 변수) |
| `environments` | 환경별 설정 분리 구조 (dev/staging/prod 변수 오버라이드) |
| `state_management` | 상태 관리 전략 (backend 유형, locking 방식, 드리프트 탐지) |
| `networking` | 네트워크 구성 (VPC, 서브넷, 보안 그룹, 로드 밸런서) |
| `cost_estimate` | 환경별 예상 비용 범위 |
| `comp_refs` | 매핑 대상 Arch 컴포넌트 ID (`COMP-xxx` 등) |
| `constraint_refs` | 참조한 RE 제약 조건 ID (`CON-xxx` 등) |
| `code_files` | 생성된 IaC 파일 목록 및 경로 |

### 3. 관찰 가능성 설정 (Observability Configuration)

SLO, 모니터링, 로깅, 분산 추적 설정을 통합 정의합니다.

| 필드 | 설명 |
|------|------|
| `slo_definitions` | SLI/SLO 정의 목록 — 각 항목: `id`(`SLO-001`), `sli`(지표), `target`(목표치), `window`(측정 기간), `error_budget`(에러 버짓), `burn_rate_alert`(번-레이트 알림 임계값), `re_refs`(근거 RE 품질 속성) |
| `monitoring_rules` | 알림 규칙 목록 — 각 항목: `id`(`MON-001`), `type`(`metric`/`log`/`trace`), `condition`(조건식), `threshold`(임계값), `severity`(심각도), `channel`(알림 채널), `slo_refs`(연결 SLO) |
| `dashboards` | 대시보드 정의 — 각 항목: `id`(`DASH-001`), `title`, `panels`(패널 목록), `format`(`grafana-json`/`datadog-json`) |
| `logging_config` | 로깅 설정 — `format`(구조화 로그 포맷), `levels`(레벨별 가이드라인), `correlation_id`(상관 ID 전파 방식), `masking_rules`(민감 정보 마스킹), `retention`(보존 정책), `rotation`(로테이션 정책) |
| `tracing_config` | 분산 추적 설정 — `sampling_rate`, `propagation`(전파 방식), `span_attributes`(스팬 속성) |
| `qa_refs` | 참조한 RE 품질 속성 (`QA:performance`, `QA:availability` 등) |
| `config_files` | 생성된 설정 파일 목록 및 경로 |

### 4. 운영 런북 (Operational Runbooks)

인시던트 대응 절차와 운영 가이드를 정의합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `RB-001`) |
| `title` | 런북 제목 |
| `trigger_condition` | 런북 실행 트리거 (어떤 알림/증상이 발생했을 때) |
| `severity` | 인시던트 심각도 (`critical` / `high` / `medium` / `low`) |
| `symptoms` | 관찰 가능한 증상 목록 |
| `diagnosis_steps` | 진단 절차 (명령어, 쿼리, 확인 사항) |
| `remediation_steps` | 조치 절차 (수동/자동 구분, 스크립트 포함) |
| `escalation_path` | 에스컬레이션 경로 (담당자, 채널, 시간 기준) |
| `rollback_ref` | 연결된 롤백 절차 ID (파이프라인 설정의 `rollback_procedure` 참조) |
| `monitoring_refs` | 관련 모니터링 규칙 ID (`MON-xxx` 등) |
| `slo_refs` | 관련 SLO ID (`SLO-xxx` 등) |
| `communication_template` | 커뮤니케이션 템플릿 (내부/외부 상태 페이지) |
| `postmortem_template` | 사후 분석 템플릿 |

### 후속 스킬 연계

```
devops 산출물 구조:
┌─────────────────────────────────────────┐
│  파이프라인 설정 (Pipeline Config)       │──→ management:plan (릴리스 일정/주기)
│  - PL-001: GitHub Actions workflow     │──→ security:audit (파이프라인 보안 검증)
│  - 배포 방식, 롤백 절차                  │──→ qa:strategy (CI 품질 게이트 연동)
├─────────────────────────────────────────┤
│  인프라 코드 (Infrastructure Code)       │──→ security:audit (IaC 보안 스캔)
│  - IAC-001: Terraform AWS modules      │──→ management:risk (인프라 비용/장애 리스크)
│  - 환경별 설정, 상태 관리                 │
├─────────────────────────────────────────┤
│  관찰 가능성 설정 (Observability)        │──→ management:report (SLO 달성률 현황)
│  - SLO-001: 가용성 99.9%               │──→ qa:report (품질 게이트 판정 기준)
│  - MON-001: 응답시간 p99 알림            │──→ security:compliance (로깅 컴플라이언스)
│  - 로깅/추적 설정                        │
├─────────────────────────────────────────┤
│  운영 런북 (Operational Runbooks)        │──→ management:risk (운영 리스크 대응)
│  - RB-001: DB 연결 장애 런북             │──→ management:retrospective (인시던트 회고)
│  - 진단/조치/에스컬레이션 절차             │
└─────────────────────────────────────────┘
```

## 목표 구조

```
devops/
├── skills.yaml
├── agents/
│   ├── slo.md
│   ├── iac.md
│   ├── pipeline.md
│   ├── strategy.md
│   ├── monitor.md
│   ├── log.md
│   ├── incident.md
│   └── review.md
├── prompts/
│   ├── slo.md
│   ├── iac.md
│   ├── pipeline.md
│   ├── strategy.md
│   ├── monitor.md
│   ├── log.md
│   ├── incident.md
│   └── review.md
└── examples/
    ├── slo-input.md
    ├── slo-output.md
    ├── iac-input.md
    ├── iac-output.md
    ├── pipeline-input.md
    ├── pipeline-output.md
    ├── strategy-input.md
    ├── strategy-output.md
    ├── monitor-input.md
    ├── monitor-output.md
    ├── log-input.md
    ├── log-output.md
    ├── incident-input.md
    ├── incident-output.md
    ├── review-input.md
    └── review-output.md
```

## 에이전트 내부 흐름

```
Arch 산출물 (4섹션) + Impl 산출물 (4섹션) + RE 간접 참조
    │
    ▼
devops:slo ──────────────────────────────────────────┐
    │  (RE 품질 속성 메트릭 → SLI/SLO 정의)            │
    │  ※ 전체 관찰 가능성의 기준점                       │
    │                                                 │
    ├──→ devops:iac                                   │
    │    (Arch 컴포넌트 구조 + 기술 스택                 │
    │     → IaC 모듈 자동 생성)                         │
    │         │                                       │
    │         ▼                                       │
    ├──→ devops:pipeline                              │
    │    (Impl 코드 구조 + IaC 인프라                    │
    │     → CI/CD 파이프라인 자동 생성)                   │
    │         │                                       │
    │         ▼                                       │
    ├──→ devops:strategy ◄────────────────────────────┤
    │    (SLO 목표 + Arch 결정                          │
    │     → 배포 방식/롤백 절차 결정)                     │
    │         │                                       │
    │         ├── strategy → pipeline에 반영 ──→ PL 갱신 │
    │         │                                       │
    ├──→ devops:monitor ◄─────────────────────────────┘
    │    (SLO → 알림 규칙/대시보드 생성)
    │         │
    ├──→ devops:log
    │    (Arch 컴포넌트 + 보안 제약 → 로깅 표준)
    │         │
    ├──→ devops:incident
    │    (strategy 롤백 + monitor 알림
    │     → 런북 자동 생성)
    │
    ▼
devops:review
    (전체 산출물 통합 리뷰:
     배포-관찰 연계 검증 + 보안 + 비용)
```

### 에이전트 호출 규칙

- `slo`는 항상 최초 진입점. RE 품질 속성 메트릭을 SLI/SLO로 변환하여 전체 DevOps 파이프라인의 기준점을 수립
- `iac`는 `slo` 이후 호출. Arch 컴포넌트 구조를 인프라 리소스로 변환
- `pipeline`은 `iac` 이후 호출. Impl 코드 구조와 IaC 인프라를 기반으로 CI/CD 워크플로 생성
- `strategy`는 `slo` + `pipeline` 이후 호출. SLO 목표와 인프라 특성을 기반으로 배포 방식 결정. 결정된 전략은 `pipeline` 설정에 역반영
- `monitor`는 `slo` 이후 호출 (pipeline/strategy와 병렬 가능). SLO 정의를 알림 규칙과 대시보드로 변환
- `log`는 `iac` 이후 호출 (monitor와 병렬 가능). Arch 컴포넌트별 로깅 표준 정의
- `incident`는 `strategy` + `monitor` 이후 호출. 배포 전략의 롤백 절차와 모니터링 알림을 런북으로 통합
- `review`는 모든 에이전트 완료 후 최종 호출. 산출물 간 정합성 및 배포-관찰 피드백 루프의 완전성을 검증
- **전체 파이프라인은 사용자 개입 없이 자동 실행**되며, 사용자 접점은 (1) 선행 결정 실현 불가 시 에스컬레이션과 (2) 최종 결과 보고 두 곳뿐

### Deploy → Observe 피드백 루프

배포와 관찰을 하나의 스킬로 통합한 핵심 가치는 다음 연결에 있습니다:

| 연결 | 설명 |
|------|------|
| `strategy` → `monitor` | 배포 방식(카나리 등)에 따라 모니터링 지표(카나리 vs 베이스라인 비교 메트릭)가 결정됨 |
| `monitor` → `strategy` | SLO 번-레이트 알림이 자동 롤백 트리거로 연결됨 |
| `slo` → `strategy` | 에러 버짓 잔량에 따라 배포 빈도/방식의 보수성이 조절됨 |
| `strategy` → `incident` | 배포 롤백 절차가 런북의 조치 절차에 포함됨 |
| `monitor` → `incident` | 알림 조건이 런북의 트리거 조건으로 직접 연결됨 |
| `log` → `monitor` | 로그 기반 메트릭(에러율 등)이 모니터링 규칙의 데이터 소스가 됨 |

## 구현 단계

### 1단계: 스킬 메타데이터 정의 (`skills.yaml`)

- 스킬 이름, 버전, 설명
- 에이전트 목록 및 각 에이전트의 역할 정의
- **입력 스키마**: Arch 산출물 4섹션 + Impl 산출물 4섹션 소비 계약, RE 간접 참조 경로
- **출력 스키마**: 4섹션 (`pipeline_configuration`, `infrastructure_code`, `observability_configuration`, `operational_runbooks`) 산출물 계약
  - 각 섹션의 필드 정의 및 필수/선택 여부 명시
  - 후속 스킬 연계를 위한 출력 계약(contract) 명세
- **적응적 깊이 설정**: Arch/Impl 모드에 따른 경량/중량 모드 기준 및 전환 규칙
- 지원 CI/CD 플랫폼 (GitHub Actions, Jenkins, GitLab CI)
- 지원 IaC 도구 (Terraform, Ansible, Helm, Pulumi)
- 지원 클라우드 프로바이더 (AWS, GCP, Azure)
- 지원 모니터링 도구 (Prometheus, Grafana, Datadog, CloudWatch)
- 지원 로깅 스택 (ELK, Loki, CloudWatch Logs)
- **에스컬레이션 조건 정의**: 선행 결정 실현 불가 시 사용자 에스컬레이션 조건 및 판별 기준
- 의존성 정보 (선행: `arch`, `impl`, RE 간접 참조, 후속 소비자: `management`, `security`, `qa`)

### 2단계: 에이전트 시스템 프롬프트 작성 (`agents/`)

#### `slo.md` — SLO 관리 에이전트

- **역할**: RE 품질 속성 메트릭을 SLI/SLO로 변환하여 전체 DevOps 파이프라인의 **관찰 기준점**을 수립
- **핵심 역량**:
  - **RE 품질 속성 → SLI 변환**: RE의 `quality_attribute_priorities.metric`을 측정 가능한 SLI(Service Level Indicator)로 변환
    - `metric: "응답시간 < 200ms"` → SLI: `http_request_duration_seconds{quantile="0.99"}`, 목표: `< 0.2`
    - `metric: "99.9% 가용성"` → SLI: `1 - (error_requests / total_requests)`, 목표: `≥ 0.999`
  - SLO (Service Level Objective) 목표 수립 — 측정 기간(window), 목표치, 에러 버짓 자동 계산
  - 에러 버짓 (Error Budget) 정책 설계 — 소진율에 따른 배포 동결/보수화 규칙
  - SLO 기반 알림 (번-레이트 알림) 설정 — 멀티 윈도우, 멀티 번-레이트
  - SLA와 SLO 간 매핑 및 갭 분석 — RE `constraints`에 SLA 관련 제약이 있는 경우
  - Arch 컴포넌트별 SLO 분배 — 시스템 SLO를 컴포넌트별 SLO로 분해
- **입력**: RE `quality_attribute_priorities` (Arch 경유), Arch `component_structure`, Arch `architecture_decisions`
- **출력**: `observability_configuration.slo_definitions` 섹션 (SLI 정의, 목표치, 에러 버짓 정책, 번-레이트 알림 규칙)
- **상호작용 모델**: RE 품질 속성 수신 → SLI/SLO 자동 변환 → 에러 버짓 정책 자동 설계 → 결과 보고
- **에스컬레이션 조건**: RE 품질 속성 `metric`이 측정 가능한 SLI로 변환 불가능한 경우 (예: "사용자 만족도 높음" 같은 정성적 메트릭). 사용자에게 정량적 지표 대안을 제시하고 선택 요청

#### `iac.md` — Infrastructure as Code 에이전트

- **역할**: Arch 컴포넌트 구조와 기술 스택을 기반으로 인프라 코드를 **자동 생성**
- **핵심 역량**:
  - **Arch 산출물 → IaC 변환**:
    - `component_structure.type`(`service` → 컴퓨팅, `store` → 데이터베이스, `queue` → 메시징) 리소스 매핑
    - `component_structure.dependencies` → 네트워크 토폴로지 및 보안 그룹 규칙
    - `technology_stack.choice` → 구체적 클라우드 리소스 선택 (예: PostgreSQL → AWS RDS)
    - `technology_stack.constraint_ref` → RE 제약 조건 준수 (프로바이더, 리전 등)
  - Terraform/Ansible/Helm 코드 생성 — IaC 도구는 기술 스택과 팀 맥락에 따라 자동 선택
  - 모듈화 및 재사용 가능한 구조 설계 — 컴포넌트 유형별 모듈 분리
  - 환경별 (dev/staging/prod) 설정 분리 — 변수 오버라이드 구조
  - 상태 관리 및 드리프트 탐지 전략
  - 비용 최적화 제안 — 리소스 사이징, 예약 인스턴스, 스팟 인스턴스 활용
- **입력**: Arch `component_structure`, `technology_stack`, `diagrams`(c4-container), RE `constraints` (간접)
- **출력**: `infrastructure_code` 섹션 (IaC 모듈, 환경별 설정, 변수, 상태 관리 설정)
- **상호작용 모델**: Arch 산출물 수신 → 컴포넌트-리소스 매핑 자동 생성 → 환경별 IaC 코드 자동 생성 → 결과 보고
- **에스컬레이션 조건**: Arch가 선택한 기술이 대상 클라우드 프로바이더에서 관리형 서비스로 제공되지 않는 경우 (예: 특정 DB가 선택한 클라우드에 없음). 사용자에게 대안(자체 호스팅 vs 대체 서비스)을 제시하고 선택 요청

#### `pipeline.md` — CI/CD 파이프라인 에이전트

- **역할**: Impl 코드 구조와 IaC 인프라를 기반으로 CI/CD 파이프라인을 **자동 생성**
- **핵심 역량**:
  - **Impl 산출물 → 파이프라인 변환**:
    - `code_structure.build_config` → 빌드 스테이지 명령어
    - `code_structure.external_dependencies` → 의존성 캐시 키 및 경로
    - `implementation_guide.build_commands` → CI 빌드 스텝
    - `implementation_guide.prerequisites` → CI 환경 런타임 설정
    - `implementation_map.module_path` → 빌드 대상 경로 (모노레포 시 변경 감지 경로)
  - 플랫폼별 파이프라인 설정 파일 생성 (GitHub Actions YAML, Jenkinsfile 등)
  - 빌드 → 테스트 → 보안 스캔 → 배포 스테이지 구성 — `qa` 품질 게이트, `security` 스캔 스텝 연동 지점 포함
  - 캐싱 전략 — 의존성 캐시, 빌드 아티팩트 캐시, Docker 레이어 캐시
  - 병렬 실행 및 매트릭스 빌드 최적화
  - 시크릿 관리 및 환경 변수 설정 — Impl `environment_config` 기반
  - IaC 배포 스텝 통합 — `iac` 에이전트 산출물의 apply 명령 포함
- **입력**: Impl `code_structure`, `implementation_guide`, `implementation_map`, IaC 산출물
- **출력**: `pipeline_configuration` 섹션 중 CI/CD 워크플로 부분 (스테이지, 캐싱, 시크릿, 환경 설정)
- **상호작용 모델**: Impl 산출물 + IaC 산출물 수신 → 빌드/테스트/배포 스테이지 자동 구성 → 결과 보고
- **에스컬레이션 조건**: Impl 빌드 구조가 CI 플랫폼의 제약과 충돌하는 경우 (예: 빌드 시간이 플랫폼 타임아웃 초과, 아티팩트 크기 제한). 사용자에게 분할 빌드 또는 플랫폼 변경 대안을 제시

#### `strategy.md` — 배포 전략 에이전트

- **역할**: SLO 목표와 Arch 결정을 기반으로 **배포 방식과 롤백 절차를 자동 결정**
- **핵심 역량**:
  - **SLO + Arch → 배포 전략 도출**:
    - SLO 가용성 목표 → 무중단 배포 필수 여부 결정 (99.9% 이상 → 블루/그린 또는 카나리)
    - SLO 에러 버짓 잔량 → 배포 보수성 결정 (버짓 < 20% → 카나리 + 느린 롤아웃)
    - Arch `component_structure.dependencies` → 배포 순서 (데이터베이스 마이그레이션 → 서비스 배포)
    - Arch `architecture_decisions` → 배포 단위 (모놀리식 전체 배포 vs 서비스별 독립 배포)
  - 블루/그린, 카나리 (단계적 롤아웃), 롤링 업데이트 전략 설계
  - 롤백 절차 수립 — 자동 롤백 트리거(SLO 위반), 수동 롤백 절차
  - 트래픽 관리 — 가중치 기반 라우팅, 헤더 기반 라우팅
  - 피처 플래그 기반 배포 전략 (해당 시)
  - 헬스 체크 정의 — Arch `interfaces`에서 헬스 엔드포인트 도출
- **입력**: SLO 산출물, Arch `component_structure`, `architecture_decisions`, Pipeline 산출물
- **출력**: `pipeline_configuration` 섹션 중 배포 전략 부분 (방식, 롤아웃 절차, 롤백 트리거/절차, 헬스 체크)
- **상호작용 모델**: SLO + Arch 산출물 수신 → 배포 방식 자동 결정 → 롤백 절차 자동 설계 → pipeline 설정에 역반영 → 결과 보고
- **에스컬레이션 조건**: SLO 수준이 요구하는 배포 방식이 인프라 제약(비용, 리소스)과 충돌하는 경우 (예: 블루/그린이 필요하지만 예산이 2배 인프라를 허용하지 않음). 사용자에게 트레이드오프(SLO 수준 완화 vs 비용 증가)를 제시하고 선택 요청

#### `monitor.md` — 모니터링 에이전트

- **역할**: SLO 정의를 기반으로 **알림 규칙과 대시보드를 자동 생성**
- **핵심 역량**:
  - **SLO → 모니터링 변환**:
    - `slo_definitions.sli` → Prometheus/Datadog 쿼리 자동 생성
    - `slo_definitions.burn_rate_alert` → 멀티 윈도우 알림 규칙 생성
    - `slo_definitions.error_budget` → 에러 버짓 소진율 대시보드
  - RED 메트릭 (Rate, Errors, Duration) 기반 서비스 모니터링 설계
  - USE 메트릭 (Utilization, Saturation, Errors) 기반 리소스 모니터링 설계
  - Prometheus 알림 규칙 / Grafana 대시보드 JSON 생성
  - 분산 추적 (Distributed Tracing) 설정 — Arch `diagrams.sequence`에서 주요 흐름 도출
  - 알림 피로도 방지 — 심각도별 알림 채널 분리, 번-레이트 기반 알림 (원시 임계값 지양)
  - **strategy 연동**: 배포 방식에 따른 배포 시 모니터링 (카나리 → 카나리 vs 베이스라인 비교 메트릭)
- **입력**: SLO 산출물, Arch `component_structure`, `diagrams`, Strategy 산출물
- **출력**: `observability_configuration` 섹션 중 모니터링 부분 (알림 규칙, 대시보드, 추적 설정)
- **상호작용 모델**: SLO + strategy 산출물 수신 → 알림 규칙 자동 생성 → 대시보드 자동 생성 → 결과 보고
- **에스컬레이션 조건**: SLO 지표를 기술적으로 측정할 수 없는 경우 (예: 선택한 인프라에서 해당 메트릭 수집이 불가능). 사용자에게 프록시 지표 대안을 제시

#### `log.md` — 로깅 에이전트

- **역할**: Arch 컴포넌트 구조와 보안 제약을 기반으로 **로깅 표준과 설정을 자동 생성**
- **핵심 역량**:
  - **Arch 컴포넌트 → 로깅 전략 변환**:
    - `component_structure`의 서비스 목록 → 서비스별 로그 네임스페이스
    - `component_structure.interfaces` → API 접근 로그 포맷
    - `component_structure.dependencies` → 상관 ID 전파 경로
  - 구조화된 로깅 (Structured Logging) 표준 정의 — JSON 포맷, 필수 필드 규격
  - 로그 레벨 가이드라인 — 컴포넌트 유형별 적정 로그 레벨 정의
  - 상관 ID (Correlation ID) 기반 분산 로그 추적 — 서비스 간 전파 방식
  - 민감 정보 마스킹 정책 — RE `constraints`의 regulatory 제약 반영
  - 로그 보존 및 로테이션 정책 — 컴플라이언스 요구사항 연동
  - **monitor 연동**: 로그 기반 메트릭(에러율, 특정 패턴 발생률)을 monitor 규칙에 제공
- **입력**: Arch `component_structure`, RE `constraints` (간접), Security 요구사항
- **출력**: `observability_configuration` 섹션 중 로깅 부분 (포맷, 레벨, 보존 정책, 마스킹 규칙)
- **상호작용 모델**: Arch 산출물 + 보안 제약 수신 → 로깅 표준 자동 생성 → 설정 파일 자동 생성 → 결과 보고
- **에스컬레이션 조건**: 보안 컴플라이언스 요구사항과 로깅 성능 간 해소 불가능한 충돌 (예: 규제상 전수 로깅이 필요하지만 트래픽 규모상 비용/성능에 심각한 영향). 사용자에게 트레이드오프 제시

#### `incident.md` — 인시던트 대응 에이전트

- **역할**: 배포 전략과 모니터링 설정을 기반으로 **인시던트 대응 런북을 자동 생성**
- **핵심 역량**:
  - **strategy + monitor → 런북 자동 생성**:
    - `monitoring_rules`의 각 알림 → 알림별 대응 런북 자동 생성
    - `strategy.rollback_procedure` → 런북의 조치 절차에 롤백 스텝 포함
    - `strategy.health_checks` → 런북의 진단 절차에 헬스 체크 확인 포함
  - 장애 유형별 대응 절차 작성 — Arch 컴포넌트별 장애 시나리오 도출
  - 에스컬레이션 경로 정의 — 심각도별 담당자/채널/시간 기준
  - 진단 명령어 및 조치 스크립트 포함 — IaC 환경 기반 구체적 명령어
  - 사후 분석 (Post-mortem) 템플릿 생성
  - 커뮤니케이션 템플릿 — 내부 공지, 외부 상태 페이지 업데이트
- **입력**: Strategy 산출물 (롤백 절차), Monitor 산출물 (알림 규칙), Arch `component_structure`, IaC 산출물
- **출력**: `operational_runbooks` 섹션 (런북 목록, 진단/조치/에스컬레이션 절차, 커뮤니케이션 템플릿)
- **상호작용 모델**: strategy + monitor 산출물 수신 → 알림별 런북 자동 생성 → 장애 시나리오별 런북 자동 생성 → 결과 보고
- **에스컬레이션 조건**: 없음 — 다른 에이전트 산출물 기반 자동 생성. 런북의 품질은 `review`에서 검증

#### `review.md` — DevOps 리뷰 에이전트

- **역할**: 전체 DevOps 산출물의 정합성, 배포-관찰 피드백 루프의 완전성, 보안/비용을 **통합 리뷰**
- **핵심 역량**:
  - **배포-관찰 피드백 루프 검증**:
    - 모든 배포 전략에 대응하는 모니터링 규칙이 있는지 확인
    - 모든 알림 규칙에 대응하는 런북이 있는지 확인
    - 롤백 트리거가 SLO 번-레이트 알림과 연결되어 있는지 확인
    - 에러 버짓 정책이 배포 전략에 반영되어 있는지 확인
  - **선행 스킬 추적성 검증**:
    - 모든 IaC 모듈이 Arch 컴포넌트에 매핑되는지 확인
    - 파이프라인 빌드 스텝이 Impl 빌드 설정과 일치하는지 확인
    - SLO가 RE 품질 속성 메트릭을 모두 커버하는지 확인
  - **보안 베스트 프랙티스 검증**: 시크릿 노출, 권한 최소화, IaC 보안 (상세 보안 분석은 `security` 스킬 영역)
  - **비용 최적화 리뷰**: IaC 리소스 사이징, 과잉 프로비저닝 식별
  - **환경 일관성 검증**: dev/staging/prod 간 설정 드리프트 식별
  - **컨테이너 이미지 최적화 리뷰**: Dockerfile 베스트 프랙티스 (해당 시)
- **입력**: 전체 DevOps 산출물 (4섹션) + Arch/Impl/RE 산출물 (추적성 검증 기준)
- **출력**: 리뷰 리포트 (배포-관찰 연계 검증 결과, 추적성 검증 결과, 보안 이슈, 비용 최적화 포인트, 환경 일관성 이슈)
- **상호작용 모델**: 전체 산출물 수신 → 자동 리뷰 수행 → 자동 수정 가능한 이슈는 해당 에이전트에 피드백 → **선행 스킬 계약 위반 수준의 이슈만 사용자에게 에스컬레이션**
- **에스컬레이션 조건**: Arch 컴포넌트에 대응하는 IaC 모듈이 없는 경우, RE 품질 속성에 대응하는 SLO가 없는 경우, 배포 전략과 모니터링 간 근본적 불일치 등 **선행 스킬 계약 위반** 수준의 이슈

### 3단계: 프롬프트 템플릿 작성 (`prompts/`)

각 에이전트에 대응하는 프롬프트 템플릿을 작성합니다:
- **Arch/Impl 산출물 파싱 가이드**: Arch 4섹션 + Impl 4섹션에서 인프라/파이프라인/모니터링 생성 지시를 추출하는 방법
- **RE 품질 속성 → SLI/SLO 변환 가이드**: 정성적/정량적 품질 메트릭을 측정 가능한 SLI로 변환하는 패턴 카탈로그
- **컴포넌트 유형 → 인프라 리소스 매핑 가이드**: Arch `type`별 클라우드 리소스 매핑 패턴
- **배포 전략 의사결정 트리**: SLO 수준 + 아키텍처 특성 → 최적 배포 방식 선택 가이드
- **에스컬레이션 판별 가이드**: 선행 결정 실현 불가 여부를 판별하는 기준 및 에스컬레이션 메시지 형식
- **배포-관찰 피드백 루프 검증 체크리스트**: review 에이전트용 정합성 검증 항목
- 플랫폼별 파이프라인 생성 템플릿 (GitHub Actions, Jenkins, GitLab CI)
- IaC 도구별 모듈 구조 템플릿 (Terraform, Helm)
- 알림 규칙 / 대시보드 생성 템플릿 (Prometheus, Grafana)
- 구조화 로깅 포맷 템플릿
- 런북 작성 템플릿
- 출력 형식 지정 (4섹션 각 필드 형식)
- Chain of Thought 가이드라인
- Few-shot 예시 포함

### 4단계: 입출력 예시 작성 (`examples/`)

각 에이전트별 대표적인 입출력 쌍을 작성합니다:
- **경량 모드 전체 파이프라인 예시**: 단일 서비스 + GitHub Actions + 기본 SLO + 핵심 런북
- **중량 모드 전체 파이프라인 예시**: 마이크로서비스 + 멀티 환경 IaC + 종합 관찰 가능성 + 상세 런북
- RE 품질 속성 → SLI/SLO 변환 예시 (정량적/정성적 메트릭 모두 포함)
- Arch 컴포넌트 → Terraform AWS 인프라 변환 예시
- Impl 코드 구조 → GitHub Actions 파이프라인 변환 예시
- SLO + Arch 결정 → 카나리 배포 전략 도출 예시
- SLO → Prometheus 알림 규칙 + Grafana 대시보드 변환 예시
- 배포-관찰 피드백 루프 연계 예시 (카나리 배포 + SLO 번-레이트 롤백)
- **에스컬레이션 예시**: 클라우드 프로바이더 제약으로 IaC 변환 불가 시 사용자 에스컬레이션
- **정상 완료 예시**: 에스컬레이션 없이 전체 자동 생성 후 결과 보고
- 런북 자동 생성 예시 (알림 → 진단 → 롤백 → 에스컬레이션)

## 핵심 설계 원칙

1. **선행 스킬 기반 (Predecessor-Driven)**: 모든 인프라/파이프라인/모니터링 결정은 Arch/Impl/RE 산출물에 근거하며, `arch_refs`/`impl_refs`/`re_refs`로 추적성을 유지. 선행 스킬이 확정한 컴포넌트 구조, 기술 스택, 품질 속성은 재질문하지 않고 전제로 수용
2. **자동 실행 + 예외 에스컬레이션 (Auto-Execute with Exception Escalation)**: 선행 스킬에서 의사결정이 완료된 상태이므로, 인프라/파이프라인/운영 설정을 자동 생성. 선행 결정이 DevOps 레벨에서 실현 불가능한 경우에만 사용자에게 에스컬레이션
3. **Deploy-Observe 연속성 (Deploy-Observe Continuity)**: 배포와 관찰을 하나의 피드백 루프로 통합. 배포 전략이 모니터링을 결정하고(`strategy` → `monitor`), 모니터링 결과가 배포 결정에 피드백(`SLO burn rate` → `rollback trigger`). 이 연결이 DevOps 스킬 통합의 핵심 가치
4. **SLO 중심 운영 (SLO-Centric Operations)**: `slo` 에이전트가 전체 파이프라인의 첫 번째 진입점. RE 품질 속성 메트릭에서 도출된 SLO가 배포 전략(에러 버짓 기반 보수성), 모니터링(번-레이트 알림), 런북(롤백 트리거)을 관통하는 기준점
5. **적응적 깊이 (Adaptive Depth)**: Arch/Impl 모드에 연동하여 경량(단일 파이프라인 + 기본 모니터링)/중량(멀티 환경 IaC + 종합 관찰 가능성 + 상세 런북) 모드 자동 전환
6. **불변 인프라 + GitOps**: 인프라는 수정하지 않고 교체. 모든 배포 설정은 Git에서 관리하는 선언적 배포. dev/staging/prod 환경 간 동일 구조에 변수만 분리
7. **관찰 가능성 3대 축 통합**: 메트릭(monitor), 로그(log), 트레이스(monitor 분산 추적)를 SLO 기준으로 통합. 상관 ID로 세 축 간 연결
8. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **파이프라인 설정 / 인프라 코드 / 관찰 가능성 설정 / 운영 런북** 4섹션으로 고정하여, 후속 스킬(`management`, `security`, `qa`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
