# DevOps Skill 구현 계획

## 개요

Arch/Impl 스킬의 산출물과 RE 품질 속성을 입력으로 받아, **설계된 시스템을 배포하고 운영하기 위한 인프라, 파이프라인, 관찰 가능성, 운영 절차를 자동 생성**하는 스킬입니다.

Impl이 "코드로 어떻게 구현할 것인가"를 실행했다면, DevOps는 "그 코드를 어떻게 배포하고, 배포된 시스템을 어떻게 관찰·운영할 것인가"를 결정합니다. 배포(Deploy)와 관찰(Observe)을 **하나의 피드백 루프**로 통합하여, 배포 전략이 모니터링을 결정하고 모니터링 결과가 배포 결정(롤백, 프로모션)에 피드백되는 연속 사이클을 구현합니다. 이 Deploy → Observe 피드백 루프가 DevOps 스킬의 시그니처 가치입니다.

RE/Arch/Impl에서 의사결정이 완료된 상태이므로, DevOps는 Impl과 동일한 **자동 실행 + 예외 에스컬레이션** 모델을 채택합니다. 선행 산출물을 기계적으로 인프라/파이프라인/모니터링 설정으로 변환하는 것이 핵심이며, **선행 결정이 DevOps 레벨에서 실현 불가능한 경우에만 사용자에게 에스컬레이션**합니다. 단, 본 스킬의 기본 동작은 **산출물 파일 생성까지이며**, `terraform apply`/`kubectl apply` 같은 실제 인프라 변경은 별도 서브스킬에서 추가 사용자 승인을 거쳐야 합니다.

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

DevOps 스킬은 Arch, Impl, RE의 산출물을 소비합니다. Arch/Impl은 직접 소비하고, RE는 Arch 산출물의 참조(`re_refs`, `constraint_ref`)를 통해 간접 소비합니다. 상세한 파싱 가이드는 `references/contracts/`에 분리합니다.

### RE 품질 속성 → SLI/SLO 매핑

| RE 산출물 | 간접 참조 경로 | DevOps에서의 영향 |
|-----------|---------------|------------------|
| **요구사항 명세** | Arch `component_structure.re_refs` → `FR-xxx`, `NFR-xxx` | NFR의 가용성/성능 요구사항으로 배포 전략(무중단 여부, 멀티 리전) 결정 |
| **제약 조건** | Arch `technology_stack.constraint_ref` → `CON-xxx` | `hard` 제약(특정 클라우드, 리전, 컴플라이언스)을 IaC 프로바이더 선택과 로깅 보존 정책에 비협상 조건으로 반영 |
| **품질 속성 우선순위** | Arch `architecture_decisions.re_refs` → `QA:xxx` | `metric`("응답시간 < 200ms", "99.9% 가용성")을 SLI/SLO 정의의 **직접 근거**로 사용. `priority`로 모니터링/알림 우선순위 결정 |

### Arch 산출물 → IaC/배포 전략 매핑

| Arch 산출물 섹션 | 주요 필드 | DevOps에서의 소비 방법 |
|-----------------|-----------|---------------------|
| **아키텍처 결정** | `id`, `decision`, `trade_offs`, `re_refs` | `decision`에서 배포 단위(모놀리식 vs 서비스별), 스케일링 전략 도출. `trade_offs`로 배포 방식 선택 근거 확보 |
| **컴포넌트 구조** | `id`, `type`, `interfaces`, `dependencies` | `type`(`service`/`gateway`/`store`/`queue`)으로 인프라 리소스 유형 결정. `dependencies`로 배포 순서·서비스 의존성. `interfaces`로 헬스 체크 엔드포인트 도출 |
| **기술 스택** | `category`, `choice`, `constraint_ref` | `choice`로 런타임/DB/메시징 리소스 선택. `constraint_ref`로 RE 제약 준수 확인 |
| **다이어그램** | `type`, `code` | `c4-container`로 배포 토폴로지. `data-flow`로 서비스 간 통신 경로 및 모니터링 지점 식별 |

### Impl 산출물 → 파이프라인/모니터링 매핑

| Impl 산출물 섹션 | 주요 필드 | DevOps에서의 소비 방법 |
|-----------------|-----------|---------------------|
| **구현 맵** | `module_path`, `component_ref` | 모듈 경로로 빌드 대상 결정. `component_ref`로 Arch 컴포넌트와 배포 단위 매핑 |
| **코드 구조** | `build_config`, `external_dependencies`, `environment_config` | `build_config`로 CI 빌드 스테이지 구성. `external_dependencies`로 캐싱 전략. `environment_config`로 시크릿/환경 변수 관리 |
| **구현 결정** | `pattern_applied`, `arch_refs` | 적용 패턴으로 운영 특성 파악 (CQRS → 읽기/쓰기 분리 모니터링 등) |
| **구현 가이드** | `prerequisites`, `build_commands`, `run_commands` | `build_commands`로 CI 빌드 스테이지. `run_commands`로 컨테이너 엔트리포인트/헬스 체크. `prerequisites`로 CI 런타임 |

### 적응적 깊이

Arch/Impl 모드에 연동하여 DevOps의 산출물 수준을 자동 조절합니다.

| Arch/Impl 모드 | 판별 기준 | DevOps 모드 | 산출물 수준 |
|---------------|-----------|-------------|------------|
| 경량 | Arch 컴포넌트 ≤ 3개, 단일 배포 환경 | 경량 | 단일 파이프라인 + 기본 IaC + 핵심 SLO 3개 이내 + 기본 모니터링 + 핵심 런북 |
| 중량 | Arch 컴포넌트 > 3개 또는 멀티 환경/리전 | 중량 | 멀티 스테이지 파이프라인 + 환경별 IaC 모듈 + 종합 SLO + RED/USE 모니터링 + 분산 추적 + 상세 런북 + 로깅 표준 |

상세 판별 규칙은 `references/adaptive-depth.md`에 분리합니다.

## 최종 산출물 구조

DevOps 스킬의 최종 산출물은 다음 **네 가지 카테고리**로 구성됩니다. 인프라 프로비저닝, 코드 배포, 시스템 관찰까지를 범위로 하며, 비즈니스 로직 구현이나 테스트 작성은 선행 스킬(`impl`, `qa`)의 영역입니다. 워크플로우 단계(slo/iac/pipeline/strategy/monitor/log/incident/review)는 아래 4개 카테고리에 매핑됩니다.

### 1. 파이프라인 설정 (CI/CD)

CI/CD 워크플로 설정과 배포 전략을 정의합니다. 워크플로우 `pipeline` + `strategy` 단계의 산출물이 통합됩니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `PL-001`) |
| `platform` | CI/CD 플랫폼 (`github-actions` / `jenkins` / `gitlab-ci`) |
| `trigger` | 트리거 조건 (브랜치, 태그, PR 등) |
| `stages` | 스테이지 목록 (빌드, 테스트, 보안 스캔, 배포) |
| `caching` | 캐싱 전략 (의존성 캐시 키, 빌드 아티팩트 경로) |
| `secrets` | 필요한 시크릿 목록 (이름, 주입 방법, 소스) |
| `environments` | 대상 환경 목록 및 승격(promotion) 규칙 |
| `deployment_method` | 배포 방식 (`blue-green` / `canary` / `rolling` / `recreate`) 및 선택 근거 |
| `rollback_trigger` | 자동 롤백 트리거 조건 (SLO 위반, 헬스 체크 실패 등) |
| `rollback_procedure` | 롤백 절차 (단계, 검증, 알림) |
| `impl_refs` | 참조한 Impl 산출물 ID |
| `arch_refs` | 참조한 Arch 산출물 ID |
| `config_files` | 생성된 설정 파일 목록 및 경로 |

### 2. 인프라 코드 (IaC)

IaC 모듈과 환경별 설정을 정의합니다. 워크플로우 `iac` 단계의 산출물입니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `IAC-001`) |
| `tool` | IaC 도구 (`terraform` / `ansible` / `helm` / `pulumi`) |
| `provider` | 클라우드 프로바이더 (`aws` / `gcp` / `azure`) |
| `modules` | 모듈 목록 (이름, 경로, 책임, 입력/출력 변수) |
| `environments` | 환경별 설정 분리 구조 (dev/staging/prod 변수 오버라이드) |
| `state_management` | 상태 관리 전략 (backend, locking, 드리프트 탐지) |
| `networking` | 네트워크 구성 (VPC, 서브넷, 보안 그룹, 로드 밸런서) |
| `cost_estimate` | 환경별 예상 비용 범위 |
| `comp_refs` | 매핑 대상 Arch 컴포넌트 ID |
| `constraint_refs` | 참조한 RE 제약 조건 ID |
| `code_files` | 생성된 IaC 파일 목록 및 경로 |

### 3. 관찰 가능성 (SLO/모니터링/로깅)

SLO, 모니터링, 로깅, 분산 추적 설정을 통합 정의합니다. 워크플로우 `slo` + `monitor` + `log` 단계의 산출물이 통합됩니다.

| 필드 | 설명 |
|------|------|
| `slo_definitions` | SLI/SLO 정의 — `id`(`SLO-001`), `sli`, `target`, `window`, `error_budget`, `burn_rate_alert`, `re_refs` |
| `monitoring_rules` | 알림 규칙 — `id`(`MON-001`), `type`(`metric`/`log`/`trace`), `condition`, `threshold`, `severity`, `channel`, `slo_refs` |
| `dashboards` | 대시보드 — `id`(`DASH-001`), `title`, `panels`, `format`(`grafana-json`/`datadog-json`) |
| `logging_config` | 구조화 로그 포맷, 레벨, 상관 ID 전파, 마스킹 규칙, 보존/로테이션 |
| `tracing_config` | `sampling_rate`, `propagation`, `span_attributes` |
| `qa_refs` | 참조한 RE 품질 속성 (`QA:performance`, `QA:availability` 등) |
| `config_files` | 생성된 설정 파일 목록 및 경로 |

### 4. 운영 (배포 전략/인시던트 런북)

인시던트 대응 절차와 운영 가이드를 정의합니다. 워크플로우 `incident` + `review` 단계의 산출물입니다.

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
| `monitoring_refs` | 관련 모니터링 규칙 ID |
| `slo_refs` | 관련 SLO ID |
| `communication_template` | 커뮤니케이션 템플릿 (내부/외부 상태 페이지) |
| `postmortem_template` | 사후 분석 템플릿 |

### 산출물 파일 구성: 메타데이터 + 문서 분리

위 4카테고리의 산출물은 **메타데이터 파일과 문서 markdown 파일을 분리**하여 저장합니다. 두 파일은 1:1 대응하며 동일한 식별자(예: `PL-001`)를 공유합니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 파일 | **YAML** (`*.meta.yaml`) | 진행 상태, 승인 상태, 추적성, 카테고리별 구조화 필드 — 스크립트가 읽고 쓰는 단일 진실 공급원(SSoT) |
| 문서 파일 | Markdown (`*.md`) | 사람이 읽는 본문 — 배포 전략·롤백 절차·SLO 근거·런북 서술 |

**YAML 채택 이유**: 주석 지원으로 필드별 근거 인라인 기술 가능, 들여쓰기 기반 구조의 가독성, 표준 라이브러리 파싱 용이, 멀티라인/앵커로 환경별 오버라이드 표현에 유리.

> **주의 — 메타데이터 YAML ≠ IaC/파이프라인 YAML**: GitHub Actions workflow YAML, Kubernetes manifest, Helm values 등 **실행 가능한 운영 설정 파일**과 본 스킬의 **상태 관리용 메타데이터 YAML(`.meta.yaml`)**은 디렉토리와 확장자로 엄격히 구분합니다.

### 메타데이터 스키마 (공통 필드)

각 메타데이터 파일은 카테고리별 필드 외에 다음 공통 필드를 포함합니다.

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 고유 식별자 (예: `PL-001`) |
| `phase` | 생명주기 단계 (`draft` / `in_progress` / `ready_for_review` / `approved` / `published`) |
| `progress` | 진행률 (`section_completed`, `section_total`, `percent`) |
| `approval.state` | 승인 상태 (`pending` / `approved` / `changes_requested` / `rejected`) |
| `approval.approver` | 승인자 식별자 |
| `approval.approved_at` | 승인 시각 (ISO 8601) |
| `approval.notes` | 승인/반려 코멘트 |
| `upstream_refs` | 선행 참조 (Arch/Impl/RE의 `arch_refs`/`impl_refs`/`re_refs`를 포함) |
| `downstream_refs` | 후속 참조 (런북에서 참조되는 monitor 규칙 ID 등) |
| `document_path` | 짝을 이루는 markdown 문서의 상대 경로 |
| `updated_at` | 최종 수정 시각 |

### 스크립트 기반 메타데이터 조작 (필수)

에이전트는 **YAML 메타데이터 파일을 직접 편집하지 않습니다**. 모든 상태 갱신은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py`를 통해서만 수행하며, 이는 (1) 스키마 검증, (2) `updated_at` 자동 갱신, (3) 추적성 ref 양방향 무결성, (4) 승인 상태 전이 규칙(`draft → approved` 직행 금지 등)을 보장합니다.

핵심 스크립트 커맨드:

| 커맨드 | 용도 |
|--------|------|
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py init <kind> <id>` | 메타데이터 + markdown 템플릿 쌍 생성 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py set <id> --field k=v` | 도메인 필드 값 갱신 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py transition <id> --to <phase>` | 진행 단계 전이 (전이 그래프 검증) |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <id> --approver <name>` | 승인 상태 전이 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | 추적성 ref 추가 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py show <id>` | 메타데이터 조회 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py validate [<id>]` | 스키마/추적성 검증 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py list [--kind ...] [--phase ...]` | 메타데이터 인덱스 조회 (review 단계용) |

### 문서 템플릿 (`assets/templates/`)

markdown 문서 또한 자유 양식이 아니라 `assets/templates/`에 사전 정의된 템플릿을 사용합니다. `artifact.py init` 실행 시 템플릿이 복사되어 **섹션 헤더, 플레이스홀더, 선행 참조 슬롯이 채워진 골격**이 생성되며, 에이전트는 골격 안의 플레이스홀더를 채우는 방식으로 본문을 작성합니다.

| 템플릿 파일 | 대상 카테고리 |
|------------|--------------|
| `pipeline.md.tmpl` / `pipeline.meta.yaml.tmpl` | 파이프라인 설정 |
| `iac.md.tmpl` / `iac.meta.yaml.tmpl` | 인프라 코드 |
| `observability.md.tmpl` / `observability.meta.yaml.tmpl` | 관찰 가능성 |
| `runbook.md.tmpl` / `runbook.meta.yaml.tmpl` | 운영 런북 |

### 후속 스킬 연계

```
devops 산출물 구조:
┌─────────────────────────────────────────┐
│  파이프라인 설정 (Pipeline Config)       │──→ management:plan (릴리스 일정/주기)
│  - PL-001: GitHub Actions workflow      │──→ security:audit (파이프라인 보안 검증)
│  - 배포 방식, 롤백 절차                  │──→ qa:strategy (CI 품질 게이트 연동)
├─────────────────────────────────────────┤
│  인프라 코드 (Infrastructure Code)       │──→ security:audit (IaC 보안 스캔)
│  - IAC-001: Terraform AWS modules       │──→ management:risk (인프라 비용/장애 리스크)
├─────────────────────────────────────────┤
│  관찰 가능성 설정 (Observability)        │──→ management:report (SLO 달성률 현황)
│  - SLO-001 / MON-001 / 로깅·추적         │──→ qa:report (품질 게이트 판정 기준)
│                                         │──→ security:compliance (로깅 컴플라이언스)
├─────────────────────────────────────────┤
│  운영 런북 (Operational Runbooks)        │──→ operations (현장 운영 인계)
│  - RB-001: DB 연결 장애 런북             │──→ incident response (인시던트 대응 체계)
└─────────────────────────────────────────┘
```

## Deploy → Observe 피드백 루프

배포와 관찰을 하나의 스킬로 통합한 핵심 가치는 다음 연결에 있습니다. 이는 DevOps 스킬의 시그니처 개념이며, 8개 워크플로우 단계가 단순한 순차 실행이 아니라 **상호 피드백 그래프**를 형성하는 이유입니다.

| 연결 | 설명 |
|------|------|
| `strategy` → `monitor` | 배포 방식(카나리 등)에 따라 모니터링 지표(카나리 vs 베이스라인 비교 메트릭)가 결정됨 |
| `monitor` → `strategy` | SLO 번-레이트 알림이 자동 롤백 트리거로 연결됨 |
| `slo` → `strategy` | 에러 버짓 잔량에 따라 배포 빈도/방식의 보수성이 조절됨 |
| `strategy` → `incident` | 배포 롤백 절차가 런북의 조치 절차에 포함됨 |
| `monitor` → `incident` | 알림 조건이 런북의 트리거 조건으로 직접 연결됨 |
| `log` → `monitor` | 로그 기반 메트릭(에러율 등)이 모니터링 규칙의 데이터 소스가 됨 |

이 피드백 루프의 정합성 검증 체크리스트는 `references/feedback-loop.md`로 분리합니다.

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점은 `devops/SKILL.md`이며, `skills.yaml`/`agents/`/`prompts/` 디렉토리는 사용하지 않습니다. 8개 워크플로우 단계는 별도 시스템 프롬프트가 아니라 SKILL.md가 순차/병렬로 수행하는 단계로 재정의되며, 단계별 상세 행동 규칙은 `references/workflow/*.md`에 분리되어 on-demand 로드됩니다.

```
devops/
├── SKILL.md                              # 필수 진입점 (frontmatter + 8단계 워크플로우 요약, 500줄 이내)
├── scripts/
│   └── artifact.py                       # 메타데이터 init/set/transition/approve/link/show/validate/list
├── assets/
│   └── templates/
│       ├── pipeline.md.tmpl
│       ├── pipeline.meta.yaml.tmpl
│       ├── iac.md.tmpl
│       ├── iac.meta.yaml.tmpl
│       ├── observability.md.tmpl
│       ├── observability.meta.yaml.tmpl
│       ├── runbook.md.tmpl
│       └── runbook.meta.yaml.tmpl
└── references/
    ├── workflow/
    │   ├── slo.md                        # SLI/SLO 수립 단계 상세 규칙
    │   ├── iac.md                        # 인프라 코드 단계 상세 규칙
    │   ├── pipeline.md                   # CI/CD 파이프라인 단계 상세 규칙
    │   ├── strategy.md                   # 배포 전략 단계 상세 규칙
    │   ├── monitor.md                    # 모니터링 단계 상세 규칙
    │   ├── log.md                        # 로깅 단계 상세 규칙
    │   ├── incident.md                   # 인시던트 런북 단계 상세 규칙
    │   └── review.md                     # 통합 리뷰 단계 상세 규칙
    ├── contracts/
    │   ├── re-input-contract.md          # RE 품질 속성 → SLI/SLO 매핑 가이드
    │   ├── arch-input-contract.md        # Arch 4섹션 → IaC/배포 전략 매핑
    │   └── impl-input-contract.md        # Impl 4섹션 → 파이프라인/모니터링 매핑
    ├── schemas/
    │   ├── meta-schema.md                # 메타데이터 공통 필드 명세
    │   └── section-schemas.md            # 4카테고리 필드 명세
    ├── adaptive-depth.md                 # 경량/중량 분기 규칙
    ├── feedback-loop.md                  # Deploy → Observe 정합성 검증 체크리스트
    └── examples/
        ├── light/                        # 단일 서비스 + 기본 SLO + 핵심 런북 예시
        └── heavy/                        # 마이크로서비스 + 멀티 환경 + 종합 관찰 가능성 예시
```

요점:
- `SKILL.md`가 유일한 진입점이며, 8개 워크플로우 단계(slo/iac/pipeline/strategy/monitor/log/incident/review)는 SKILL.md 안에 짧게 요약하고, 상세 규칙은 `references/workflow/*.md`로 분리하여 on-demand 로드합니다.
- 표준 명칭 `assets/templates/`, `references/examples/`를 사용합니다.
- `skills.yaml`, `agents/`, `prompts/`는 사용하지 않습니다.

## 워크플로우 단계 (SKILL.md 내부 단일 진입점)

8개 단계는 단순한 선형 흐름이 아니라 의존성 그래프를 가집니다. SKILL.md는 단계 진입 시 해당 `references/workflow/<phase>.md`를 Read로 로드한 뒤 그 지시를 따릅니다.

```
Arch 4섹션 + Impl 4섹션 + RE 간접 참조
    │
    ▼
[Stage 1] slo ─────────────────────────────────────┐
    │  references/workflow/slo.md 로드              │
    │  (RE 품질 속성 → SLI/SLO, 에러 버짓 정책)      │
    │  ※ 전체 관찰 가능성의 기준점                    │
    │                                               │
    ├──→ [Stage 2] iac                              │
    │    references/workflow/iac.md 로드            │
    │    (Arch 컴포넌트 + 기술 스택 → IaC 모듈)      │
    │         │                                     │
    │         ▼                                     │
    ├──→ [Stage 3] pipeline                         │
    │    references/workflow/pipeline.md 로드       │
    │    (Impl 코드 구조 + IaC → CI/CD 파이프라인)   │
    │         │                                     │
    │         ▼                                     │
    ├──→ [Stage 4] strategy ◄──────────────────────┤
    │    references/workflow/strategy.md 로드       │
    │    (SLO + Arch → 배포 방식/롤백 절차)          │
    │    └── pipeline 설정에 역반영 ──→ PL 갱신     │
    │                                               │
    ├──→ [Stage 5] monitor ◄────────────────────────┘
    │    references/workflow/monitor.md 로드
    │    (SLO + strategy → 알림 규칙/대시보드)
    │         │
    ├──→ [Stage 6] log
    │    references/workflow/log.md 로드
    │    (Arch 컴포넌트 + 보안 제약 → 로깅 표준)
    │         │
    ├──→ [Stage 7] incident
    │    references/workflow/incident.md 로드
    │    (strategy 롤백 + monitor 알림 → 런북)
    │
    ▼
[Stage 8] review
    references/workflow/review.md 로드
    (전체 산출물 통합 리뷰 + 피드백 루프 검증)
```

각 워크플로우 파일에는 **역할 / 핵심 역량 / 입력 / 출력 / 상호작용 모델 / 에스컬레이션 조건**이 기술됩니다.

### `references/workflow/slo.md` — SLI/SLO 수립 단계
- **역할**: RE 품질 속성 메트릭을 SLI/SLO로 변환하여 전체 DevOps 파이프라인의 관찰 기준점 수립
- **핵심 역량**: RE `quality_attribute_priorities.metric` → 측정 가능한 SLI 변환(예: `"응답시간 < 200ms"` → `http_request_duration_seconds{quantile="0.99"} < 0.2`), SLO 목표·에러 버짓 자동 계산, 멀티 윈도우 번-레이트 알림 설계, Arch 컴포넌트별 SLO 분배
- **입력**: RE `quality_attribute_priorities`(Arch 경유), Arch `component_structure`, `architecture_decisions`
- **출력**: 관찰 가능성 카테고리의 `slo_definitions` 부분
- **상호작용 모델**: 자동 변환 → 결과 보고
- **에스컬레이션 조건**: RE `metric`이 측정 불가능한 정성적 표현인 경우(예: "사용자 만족도 높음") 정량적 지표 대안을 사용자에게 제시

### `references/workflow/iac.md` — 인프라 코드 단계
- **역할**: Arch 컴포넌트 구조와 기술 스택을 IaC로 자동 변환
- **핵심 역량**: `component_structure.type` → 리소스 매핑(`service`→컴퓨팅, `store`→DB, `queue`→메시징), `dependencies` → 네트워크 토폴로지 및 보안 그룹, `technology_stack.choice` → 클라우드 리소스(예: PostgreSQL → AWS RDS), Terraform/Ansible/Helm 코드 생성, 환경별 변수 오버라이드, 상태 관리·드리프트 탐지, 비용 최적화
- **입력**: Arch `component_structure`, `technology_stack`, `diagrams`(c4-container), RE `constraints`(간접)
- **출력**: 인프라 코드 카테고리
- **에스컬레이션 조건**: Arch 선택 기술이 대상 클라우드의 관리형 서비스로 제공되지 않을 때 자체 호스팅 vs 대체 서비스 대안 제시

### `references/workflow/pipeline.md` — CI/CD 파이프라인 단계
- **역할**: Impl 코드 구조와 IaC 인프라를 기반으로 CI/CD 파이프라인 자동 생성
- **핵심 역량**: `code_structure.build_config` → 빌드 스테이지, `external_dependencies` → 캐시 키, `implementation_guide.build_commands` → CI 빌드 스텝, 빌드→테스트→보안 스캔→배포 스테이지 구성, 캐싱·매트릭스·시크릿 관리, IaC apply 스텝 통합
- **입력**: Impl `code_structure`, `implementation_guide`, `implementation_map`, IaC 산출물
- **출력**: 파이프라인 설정 카테고리 중 CI/CD 워크플로 부분
- **에스컬레이션 조건**: 빌드 시간이 플랫폼 타임아웃 초과, 아티팩트 크기 제한 등 충돌 시 분할 빌드/플랫폼 변경 대안 제시

### `references/workflow/strategy.md` — 배포 전략 단계
- **역할**: SLO 목표와 Arch 결정을 기반으로 배포 방식과 롤백 절차를 자동 결정
- **핵심 역량**: SLO 가용성 목표 → 무중단 배포 필수 여부(99.9% 이상 → 블루/그린·카나리), 에러 버짓 잔량 → 보수성 결정, `dependencies` → 배포 순서, 블루/그린·카나리·롤링 전략 설계, 자동/수동 롤백 절차, 트래픽 가중치 라우팅, 헬스 체크 정의
- **입력**: SLO 산출물, Arch `component_structure`, `architecture_decisions`, Pipeline 산출물
- **출력**: 파이프라인 설정 카테고리 중 배포 전략 부분(pipeline에 역반영)
- **에스컬레이션 조건**: 필요한 배포 방식과 인프라 제약(비용·리소스) 충돌 시 트레이드오프 사용자 선택

### `references/workflow/monitor.md` — 모니터링 단계
- **역할**: SLO 정의를 기반으로 알림 규칙과 대시보드를 자동 생성
- **핵심 역량**: `slo_definitions.sli` → Prometheus/Datadog 쿼리, `burn_rate_alert` → 멀티 윈도우 알림, RED·USE 메트릭, Grafana 대시보드 JSON, 분산 추적 설정(Arch `diagrams.sequence` 기반), 알림 피로도 방지(번-레이트 우선), strategy 연동(카나리 vs 베이스라인 비교)
- **입력**: SLO 산출물, Arch `component_structure`, `diagrams`, Strategy 산출물
- **출력**: 관찰 가능성 카테고리 중 모니터링 부분
- **에스컬레이션 조건**: SLO 지표를 기술적으로 측정 불가한 경우 프록시 지표 대안 제시

### `references/workflow/log.md` — 로깅 단계
- **역할**: Arch 컴포넌트 구조와 보안 제약을 기반으로 로깅 표준과 설정 자동 생성
- **핵심 역량**: 서비스별 로그 네임스페이스, `interfaces` → API 접근 로그 포맷, 상관 ID 전파 경로, 구조화 로깅(JSON 포맷), 로그 레벨 가이드, 민감 정보 마스킹(RE regulatory 제약 반영), 보존·로테이션 정책, 로그 기반 메트릭을 monitor에 제공
- **입력**: Arch `component_structure`, RE `constraints`(간접), 보안 요구사항
- **출력**: 관찰 가능성 카테고리 중 로깅 부분
- **에스컬레이션 조건**: 컴플라이언스 요구사항과 로깅 성능 간 해소 불가능한 충돌 시 트레이드오프 제시

### `references/workflow/incident.md` — 인시던트 런북 단계
- **역할**: 배포 전략과 모니터링 설정을 기반으로 인시던트 대응 런북 자동 생성
- **핵심 역량**: 각 알림 → 알림별 대응 런북, `strategy.rollback_procedure` → 런북 조치 절차, 헬스 체크 → 진단 절차, Arch 컴포넌트별 장애 시나리오, 심각도별 에스컬레이션 경로, IaC 환경 기반 진단 명령어, 사후 분석 템플릿, 커뮤니케이션 템플릿
- **입력**: Strategy, Monitor, Arch `component_structure`, IaC 산출물
- **출력**: 운영 카테고리(런북 목록)
- **에스컬레이션 조건**: 없음 — 다른 단계 산출물 기반 자동 생성. 품질은 review에서 검증

### `references/workflow/review.md` — 통합 리뷰 단계
- **역할**: 전체 DevOps 산출물의 정합성, Deploy → Observe 피드백 루프의 완전성, 보안/비용을 통합 리뷰
- **핵심 역량**:
  - **피드백 루프 검증**: 모든 배포 전략에 모니터링 규칙이 있는지, 모든 알림에 대응 런북이 있는지, 롤백 트리거가 SLO 번-레이트와 연결되는지, 에러 버짓이 배포 전략에 반영되는지
  - **추적성 검증**: 모든 IaC 모듈이 Arch 컴포넌트에 매핑되는지, 파이프라인 빌드가 Impl 빌드 설정과 일치하는지, SLO가 RE 품질 속성을 모두 커버하는지
  - 보안 베스트 프랙티스, 비용 최적화, 환경 일관성 검증
- **입력**: 전체 DevOps 4카테고리 산출물 + Arch/Impl/RE(추적성 기준)
- **출력**: 리뷰 리포트
- **에스컬레이션 조건**: 선행 스킬 계약 위반 수준 이슈(Arch 컴포넌트에 IaC 모듈이 없음, RE 품질 속성에 SLO가 없음 등)

## 구현 단계

### 1단계: `SKILL.md` 작성

표준에서 메타데이터의 단일 출처는 `devops/SKILL.md`의 YAML frontmatter입니다. `name`과 `description`만 필수로 두고, 그 외 옵션 필드는 기본 동작으로 목적을 달성할 수 없음이 입증된 경우에만 추가합니다.

**권장 frontmatter 초안**:

```yaml
---
name: devops
description: Arch/Impl 산출물과 RE 품질 속성을 입력으로 받아 CI/CD 파이프라인·IaC 모듈·관찰 가능성 설정(SLO/모니터링/로깅/추적)·운영 런북을 자동 생성한다. arch/impl 스킬 완료 후 배포·관찰 설정이 필요할 때 사용. Deploy와 Observe를 단일 SLO 기반 피드백 루프로 통합.
---
```

**설계 원칙**:
- `name`: 디렉토리명과 일치시켜 `devops`로 고정
- `description`: 250자 컷오프 가정, 핵심 키워드(CI/CD, IaC, SLO, observability, runbook, feedback loop) 전방 배치, "무엇을/언제" 명시
- 그 외 옵션 필드(`argument-hint`, `allowed-tools`, `effort`, `disable-model-invocation` 등)는 기본 동작으로 목적 달성이 불가능함이 입증된 경우에만 도입

**SKILL.md 본문 구성 (500줄 이내)**:
1. 스킬 개요 (Arch/Impl 4섹션 + RE 간접 참조 → DevOps 4카테고리)
2. 입력/출력 계약 요약 (상세는 `references/contracts/*.md`)
3. 적응적 깊이 분기 로직
4. 8단계 워크플로우 요약 (각 단계 진입 시 `${CLAUDE_SKILL_DIR}/references/workflow/<stage>.md`를 Read로 로드)
5. 스크립트 호출 규약: 모든 메타데이터 조작은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py`만 사용
6. 시작 시 상태 주입: `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` ``로 현재 산출물 상태를 동적 컨텍스트로 주입
7. 선행 산출물 존재 확인: `` !`ls arch/artifacts` ``, `` !`ls impl/artifacts` `` 동적 주입

**치환자**: 모든 스크립트/참조 경로는 `${CLAUDE_SKILL_DIR}/...` 로 작성, 사용자 인자는 `$ARGUMENTS`로 받음.

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

8개 단계의 상세 행동 규칙을 `references/workflow/`에 markdown으로 분리하고, SKILL.md가 단계 진입 시 on-demand로 Read합니다. 각 파일은 위 워크플로우 단계 절에 기술된 역할/핵심 역량/입력/출력/상호작용 모델/에스컬레이션 조건을 상세화합니다.

스크립트 호출 규약("메타데이터 갱신은 반드시 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 호출")은 각 워크플로우 파일에 반복 명시하고, 각 단계에서 어떤 커맨드를 어떤 순서로 호출해야 하는지 시퀀스로 기술합니다.

### 3단계: 참조 문서 작성 (`references/`)

- `references/workflow/*.md` (8개): 단계별 상세 행동 규칙
- `references/contracts/re-input-contract.md`: RE 품질 속성 → SLI/SLO 매핑 가이드 (정량/정성 메트릭 패턴 카탈로그)
- `references/contracts/arch-input-contract.md`: Arch 4섹션 → IaC/배포 전략 변환 가이드 (컴포넌트 type → 리소스 매핑 패턴)
- `references/contracts/impl-input-contract.md`: Impl 4섹션 → 파이프라인/모니터링 변환 가이드
- `references/schemas/meta-schema.md`: 메타데이터 공통 필드 및 phase 전이 그래프 명세
- `references/schemas/section-schemas.md`: 4카테고리 도메인 필드 명세
- `references/adaptive-depth.md`: 경량/중량 모드 판별 규칙과 모드별 스킵 단계 정의
- `references/feedback-loop.md`: Deploy → Observe 정합성 검증 체크리스트 (review 단계가 사용)

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

표준 디렉토리 명칭은 `assets/`입니다. 4카테고리(`pipeline`, `iac`, `observability`, `runbook`)별 markdown 템플릿(`*.md.tmpl`)과 메타데이터 골격(`*.meta.yaml.tmpl`)을 작성합니다.

- `*.md.tmpl`: 섹션 헤더, 표 골격, 선행 참조 슬롯, 플레이스홀더 포함
- `*.meta.yaml.tmpl`: `phase: draft`, `approval.state: pending`, 빈 `upstream_refs`/`downstream_refs` 등 기본값 + 필드별 채움 가이드 주석
- 워크플로우의 8단계는 4카테고리 템플릿을 공유하며, 단계 결과가 통합되어 카테고리 산출물을 완성합니다.

### 5단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

`scripts/artifact.py`를 단일 진입점으로 구현합니다. 서브커맨드는 위 "스크립트 기반 메타데이터 조작" 절 표 참조. 모든 쓰기 커맨드는 `updated_at`을 자동 갱신하고, 잘못된 상태 전이/누락 필드를 차단합니다.

**스크립트 호출 강제 (다층 방어)**:

행동 규약만으로는 우회될 수 있으므로 4단 방어를 구성합니다.

1. **행동 규약 (가장 약함)**: `references/workflow/*.md`와 SKILL.md 본문에서 "메타데이터 갱신은 반드시 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 호출"을 반복 명시
2. **도구 권한 (중간)**: Edit/Write 대상은 markdown 본문으로 한정하도록 워크플로우 가이드에 명시
3. **PreToolUse hooks (가장 강함)**: 가능하다면 `*.meta.yaml`에 대한 Edit/Write 시도를 차단하는 PreToolUse hook을 등록하여 직접 편집을 원천 차단
4. **시작 시 상태 주입**: SKILL.md 상단에서 `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` ``로 현재 산출물 상태·추적성 무결성을 동적 주입하여 에이전트가 자연스럽게 스크립트 흐름을 따르도록 유도

### 6단계: 입출력 예시 작성 (`references/examples/`)

- **경량 예시 (`light/`)**: 단일 서비스 + GitHub Actions + 기본 SLO 3개 + 핵심 런북
- **중량 예시 (`heavy/`)**: 마이크로서비스 + 멀티 환경 Terraform + RED/USE 모니터링 + 분산 추적 + 상세 런북
- RE 품질 속성 → SLI/SLO 변환 예시(정량/정성 모두)
- Arch 컴포넌트 → Terraform AWS 변환 예시
- Impl 코드 구조 → GitHub Actions 변환 예시
- SLO + Arch → 카나리 배포 전략 도출 예시
- Deploy → Observe 피드백 루프 연계 예시(카나리 + SLO 번-레이트 롤백)
- 에스컬레이션 예시(클라우드 프로바이더 제약으로 IaC 변환 불가)
- **메타데이터 + 문서 쌍 예시**: 각 카테고리마다 `*-output.md`와 `*-output.meta.yaml`을 함께 제공. `phase`, `approval`, `upstream_refs`/`downstream_refs`가 채워진 실제 모습 시연
- **스크립트 사용 흐름 예시**: `artifact.py init pipeline PL-001` → 템플릿 전개 → `.md` 편집 → `artifact.py set ... --field platform=github-actions` → `artifact.py link ... --upstream IM-003` → `artifact.py transition ... --to ready_for_review` → `artifact.py approve ... --approver devops:review` 전체 커맨드 로그

## 핵심 설계 원칙

1. **RE 품질 속성 → SLO 기반 (Quality-Driven)**: RE의 `quality_attribute_priorities.metric`이 SLI/SLO의 직접 근거가 되며, SLO는 배포 전략(에러 버짓 기반 보수성), 모니터링(번-레이트 알림), 런북(롤백 트리거)을 관통하는 기준점. SLO 단계가 항상 첫 진입점
2. **Arch/Impl 산출물 기반 (Predecessor-Driven)**: 모든 인프라/파이프라인 결정은 Arch/Impl 산출물에 근거하며, `arch_refs`/`impl_refs`/`re_refs`로 추적성을 유지. 선행 스킬이 확정한 컴포넌트 구조·기술 스택·품질 속성은 재질문하지 않고 전제로 수용
3. **Deploy → Observe 피드백 루프 (Continuous Feedback)**: 배포와 관찰을 하나의 피드백 루프로 통합. 배포 전략이 모니터링을 결정하고(`strategy → monitor`), 모니터링 결과가 배포 결정에 피드백됨(`SLO burn rate → rollback trigger`). 이 연결이 DevOps 스킬 통합의 시그니처 가치이며 review 단계가 그 정합성을 검증
4. **적응적 깊이 (Adaptive Depth)**: Arch/Impl 모드에 연동하여 경량(단일 파이프라인 + 기본 모니터링)/중량(멀티 환경 IaC + 종합 관찰 가능성 + 상세 런북) 모드를 단일 진입점 안에서 자동 분기. 스킬을 별도 변형으로 분할하지 않음
5. **추적성 (Traceability)**: 모든 산출물은 `re_refs`/`arch_refs`/`impl_refs` 체인을 유지하여 "왜 이 SLO/IaC/파이프라인 결정을 했는가"를 RE까지 역추적 가능. review 단계가 체인의 완결성을 자동 검증
6. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **파이프라인 설정 / 인프라 코드 / 관찰 가능성 / 운영** 4카테고리로 고정하여, 후속 스킬(`management`, `security`, `qa`, operations)이 직접 소비할 수 있는 계약(contract) 역할을 수행
7. **메타데이터-문서 분리 및 스크립트 경유 원칙 (Metadata/Document Separation via Scripts)**: 산출물은 YAML 메타데이터 파일과 markdown 문서 파일을 분리하여 관리하고, 메타데이터(진행 상태·승인 상태·추적성 ref)는 에이전트가 직접 편집하지 않고 오직 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 커맨드를 통해서만 갱신. markdown 본문은 `assets/templates/`의 사전 정의 템플릿으로 골격을 생성한 뒤 에이전트가 플레이스홀더를 채움으로써 상태 일관성과 서식 표준을 동시에 보장. 실행 가능한 IaC/파이프라인 YAML과 상태 관리용 메타데이터 YAML(`.meta.yaml`)은 디렉토리·확장자로 엄격히 구분
