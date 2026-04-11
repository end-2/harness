# DevOps Skill 구현 계획

## 개요

Arch/Impl 스킬의 산출물과 RE 품질 속성을 입력으로 받아, **설계된 시스템을 배포하고 운영하기 위한 인프라, 파이프라인, 관찰 가능성을 자동 생성**하는 스킬입니다.

Impl이 "코드로 어떻게 구현할 것인가"를 실행했다면, DevOps는 "그 코드를 어떻게 배포하고, 배포된 시스템을 어떻게 관찰·운영할 것인가"를 결정합니다. 배포(Deploy)와 관찰(Observe)을 **하나의 피드백 루프**로 통합하여, 배포 전략이 모니터링을 결정하고 모니터링 결과가 배포 결정(롤백, 프로모션)에 피드백되는 연속 사이클을 구현합니다.

RE/Arch/Impl에서 의사결정이 완료된 상태이므로, DevOps는 Impl과 동일한 **자동 실행 + 예외 에스컬레이션** 모델을 채택합니다. 선행 스킬 산출물을 기계적으로 인프라/파이프라인/모니터링 설정으로 변환하는 것이 핵심이며, **선행 결정이 DevOps 레벨에서 실현 불가능한 경우에만 사용자에게 에스컬레이션**합니다.

단, 이 "자동 실행"은 **사용자가 스킬을 명시적으로 호출한 이후 스킬 내부의 서브에이전트 간 파이프라인에 한정**됩니다. DevOps 스킬 자체는 인프라 프로비저닝·배포·롤백과 같이 되돌리기 어려운 작업을 포함하므로, **모델 자동 호출(model-invocation)로는 기동되지 않으며**, 반드시 사용자가 `/devops`로 명시 호출해야 합니다(`disable-model-invocation: true`). 또한 기본 동작은 **산출물(파이프라인/IaC/관찰 가능성/런북 파일) 생성까지이며**, `terraform apply` / `kubectl apply` 같은 **실제 인프라 변경은 별도의 `devops/apply` 서브스킬로 분리**하여 추가적인 사용자 승인 절차를 거칩니다.

### Claude Code Skill 표준 준수

본 스킬은 Claude Code Skill 공식 포맷(`SKILL.md` + YAML frontmatter, `scripts/`, `assets/`, `references/` 컨벤션)을 따릅니다. 진입점은 `devops/SKILL.md`이며, 상세 참조 자료는 `references/` 아래에 분리하여 Just-in-Time 로드 방식으로 활용합니다. 8개 서브 에이전트(`slo`, `iac`, `pipeline`, `strategy`, `monitor`, `log`, `incident`, `review`)는 **서브스킬(Sub-Skill)로 분리**하여 각자 독립된 `SKILL.md`와 frontmatter를 가지며, 상위 `devops/SKILL.md`가 오케스트레이터 역할을 수행합니다.

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

### 산출물 저장 형식: 메타데이터 + 문서 분리

각 산출물(파이프라인 설정, 인프라 코드, 관찰 가능성 설정, 운영 런북)은 **메타데이터 파일과 문서 markdown 파일의 쌍**으로 저장됩니다. 두 파일은 1:1로 대응하며 동일한 식별자(예: `PL-001`)를 공유합니다.

| 파일 | 형식 | 역할 |
|------|------|------|
| 메타데이터 파일 | **YAML** (`.meta.yaml`) | 상태 관리용 구조화 데이터 — 식별자, 필드 값, 진행/승인 상태, 추적성 참조 |
| 문서 파일 | **Markdown** (`.md`) | 사람이 읽는 본문 — 상세 설명, 다이어그램, 근거, 의사결정 서술 |

**YAML을 메타데이터 형식으로 채택하는 이유**:
- 주석 지원으로 필드별 근거와 제약을 인라인으로 기술 가능
- 사람이 읽기 쉬운 들여쓰기 기반 구조 (JSON 대비 시각적 가독성 우위)
- 다양한 언어의 스크립트에서 파싱이 용이하며 Impl/Arch 선행 스킬 산출물 포맷과도 일관성 확보
- 멀티라인 문자열 및 앵커/별칭 지원으로 반복 구조(환경별 오버라이드 등) 표현에 유리

> **주의 — 메타데이터 YAML ≠ IaC/파이프라인 YAML**: DevOps 스킬의 산출물에는 두 종류의 YAML이 혼재합니다.
> - **실제 산출 파일**: GitHub Actions workflow YAML, Kubernetes manifest, Helm values, Ansible playbook 등 **실행 가능한 운영 설정 파일**. 이 파일들은 `pipeline_configuration.config_files`, `infrastructure_code.code_files` 등의 경로로 참조되는 실제 배포 대상입니다.
> - **메타데이터 YAML (`.meta.yaml`)**: 위 실제 산출 파일들의 **상태·추적성·승인 정보를 관리하는 메타 파일**. 에이전트와 사용자 간 협업 상태를 표현하며, 런타임에 실행되지 않습니다.
>
> 두 종류는 디렉토리(`artifacts/` 내부의 하위 구조)와 확장자(`.meta.yaml` vs `.yaml`/`.tf`/`.yml`)로 명확히 구분합니다.

#### 메타데이터 필수 필드

각 메타데이터 파일은 개별 산출물 섹션의 기존 필드(위 4섹션 표 참조)에 더해 다음 **공통 관리 필드**를 포함합니다:

| 필드 그룹 | 필드 | 설명 |
|-----------|------|------|
| **진행 상태** | `phase` | 산출물 생명주기 단계 (`draft` / `in_progress` / `ready_for_review` / `approved` / `published`) |
| | `progress` | 0–100의 진행률. 하위 체크리스트 완료 비율로 계산 |
| | `updated_at` | 마지막 상태 갱신 시각 (스크립트가 자동 기록) |
| | `updated_by` | 상태를 갱신한 에이전트 식별자 (예: `devops:iac`) |
| **승인 상태** | `approval_state` | `pending` / `approved` / `changes_requested` / `rejected` |
| | `approver` | 승인자 식별자 (사용자 또는 상위 리뷰 에이전트) |
| | `approved_at` | 승인 시각 |
| | `review_comments` | 리뷰 코멘트 목록 (각 항목: `author`, `comment`, `resolved`) |
| **추적성** | `upstream_refs` | 선행 스킬 참조 (`arch_refs`, `impl_refs`, `re_refs`를 포함하는 상위 개념) |
| | `downstream_refs` | 후속 스킬/산출물 참조 (예: 런북에서 참조되는 monitor 규칙 ID) |
| | `doc_path` | 짝을 이루는 markdown 문서 파일의 상대 경로 |

**에이전트는 이 메타데이터 파일을 직접 편집하지 않습니다.** 모든 조작(생성·필드 갱신·phase 전이·승인 상태 변경·추적성 링크 추가)은 `scripts/` 디렉토리의 스크립트 커맨드를 통해서만 이루어집니다. 이렇게 하는 이유는 (1) 스키마 검증을 스크립트 진입점에 집중하여 메타데이터 무결성을 보장하고, (2) 상태 전이 규칙(예: `draft → approved` 직접 전이 금지)을 강제하며, (3) `updated_at`/`updated_by`와 같은 자동 필드를 일관되게 관리하기 위함입니다.

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

Claude Code Skill 표준 포맷(`SKILL.md` 진입점 + frontmatter, `scripts/`, `assets/`, `references/` 컨벤션)에 맞춰 아래와 같이 구성합니다. 상위 `devops/SKILL.md`는 오케스트레이터 역할을 하며, 8개 서브에이전트는 `sub-skills/<name>/SKILL.md`의 서브스킬로 분리됩니다.

```
devops/
├── SKILL.md                          # [필수] 진입점 — frontmatter + 오케스트레이션 지시문 (≤500줄)
├── assets/                           # 표준 컨벤션 이름 (과거 templates/)
│   ├── pipeline.meta.yaml.tmpl      # 파이프라인 메타데이터 골격 (빈 필드 + 주석 가이드)
│   ├── pipeline.md.tmpl             # 파이프라인 문서 골격 (섹션 헤더 + 플레이스홀더)
│   ├── iac.meta.yaml.tmpl
│   ├── iac.md.tmpl
│   ├── observability.meta.yaml.tmpl
│   ├── observability.md.tmpl
│   ├── runbook.meta.yaml.tmpl
│   └── runbook.md.tmpl
├── references/                       # Just-in-Time 로드되는 상세 참조 자료
│   ├── upstream-contract.md          # Arch/Impl/RE 소비 매핑 상세
│   ├── output-sections.md            # 4섹션 필드 정의 상세
│   ├── agent-flow.md                 # 서브스킬 호출 순서/병렬성 규칙
│   ├── escalation-rules.md           # 에이전트별 에스컬레이션 조건 카탈로그
│   ├── supported-tools.md            # 지원 CI/CD·IaC·클라우드·모니터링 카탈로그
│   ├── sli-slo-patterns.md           # RE 품질 속성 → SLI 변환 패턴 카탈로그
│   ├── deploy-strategy-tree.md       # 배포 전략 의사결정 트리
│   └── deploy-observe-checklist.md   # review 에이전트 검증 체크리스트
├── scripts/
│   ├── artifact.py          # 메타데이터/문서 쌍 조작 CLI (init/get/set/transition/approve/link/validate/list)
│   ├── validate_all.py      # hook용 전체 검증 진입점 (PostToolUse/Stop에서 호출)
│   ├── schema/
│   │   ├── pipeline.schema.yaml     # 파이프라인 설정 메타데이터 스키마
│   │   ├── iac.schema.yaml          # 인프라 코드 메타데이터 스키마
│   │   ├── observability.schema.yaml# 관찰 가능성 설정 메타데이터 스키마
│   │   └── runbook.schema.yaml      # 운영 런북 메타데이터 스키마
│   └── lib/                 # 공통 유틸리티 (YAML I/O, 상태 전이 규칙, 추적성 검증)
├── sub-skills/                       # 8개 서브에이전트 = 서브스킬
│   ├── slo/SKILL.md                  # SLO/SLI 도출 — disable-model-invocation: false (분석)
│   ├── iac/SKILL.md                  # IaC 생성 — disable-model-invocation: true (결정)
│   ├── pipeline/SKILL.md             # CI/CD 파이프라인 생성 — disable-model-invocation: true
│   ├── strategy/SKILL.md             # 배포 전략 결정 — disable-model-invocation: true
│   ├── monitor/SKILL.md              # 모니터링 규칙/대시보드 — disable-model-invocation: false
│   ├── log/SKILL.md                  # 로깅 표준 — disable-model-invocation: false
│   ├── incident/SKILL.md             # 런북 생성 — disable-model-invocation: false
│   ├── review/SKILL.md               # 통합 리뷰 — disable-model-invocation: false
│   └── apply/SKILL.md                # (별도) 실제 인프라 변경 수행 — disable-model-invocation: true, 사용자 명시 승인 필수
└── examples/
    ├── slo-input.md
    ├── slo-output.md               # 문서 markdown 예시
    ├── slo-output.meta.yaml        # 대응하는 메타데이터 예시
    ├── iac-input.md
    ├── iac-output.md
    ├── iac-output.meta.yaml
    ├── pipeline-input.md
    ├── pipeline-output.md
    ├── pipeline-output.meta.yaml
    ├── strategy-input.md
    ├── strategy-output.md
    ├── strategy-output.meta.yaml
    ├── monitor-input.md
    ├── monitor-output.md
    ├── monitor-output.meta.yaml
    ├── log-input.md
    ├── log-output.md
    ├── log-output.meta.yaml
    ├── incident-input.md
    ├── incident-output.md
    ├── incident-output.meta.yaml
    ├── review-input.md
    └── review-output.md
```

`examples/`의 각 산출 항목은 **문서 markdown 파일과 메타데이터 YAML 파일의 쌍**으로 제공되어, 에이전트가 템플릿 초기화 → 문서 편집 → 스크립트 기반 메타데이터 갱신의 전체 흐름을 참조할 수 있도록 합니다.

### `devops/SKILL.md` 최상단 frontmatter

상위 `devops/SKILL.md`의 진입부에는 아래와 같은 최소 YAML frontmatter를 배치합니다. Claude Code Skill 표준에 따라 `name`과 `description`만 필수이며, `description`은 250자 이내로 전방에 "무엇을 하는가 + 언제 사용하는가"를 배치하여 자동 호출 판별에 활용되도록 합니다.

```yaml
---
name: devops
description: Generate CI/CD pipelines, IaC modules, observability configuration (SLO/monitoring/logging/tracing), and operational runbooks from upstream arch/impl/re artifacts. Use after arch and impl skills finalized component structure and code structure. Integrates deploy and observe into a single SLO-driven feedback loop.
---
```

- `description`은 250자 컷오프를 고려하여 핵심 키워드(CI/CD, IaC, observability, runbooks, SLO feedback loop)를 전방 배치
- 경량/중량 모드는 `$ARGUMENTS`(또는 `$1`)로 받아 SKILL.md 본문에서 분기
- 모든 스크립트 호출은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py ...` 형태로 통일
- 선행 스킬 산출물 존재 확인은 SKILL.md 내 `` !`ls arch/artifacts` ``, `` !`ls impl/artifacts` `` 등 동적 컨텍스트 주입으로 호출 시점에 자동 수행
- 그 외 선택 필드(`argument-hint`, `allowed-tools`, `context`, `agent`, `effort`, `model`, `hooks`, `paths`, `disable-model-invocation` 등)는 기본값으로 두며, 기본 동작으로 스킬 목적을 달성할 수 없는 구체적 사유가 있을 때에만 추가합니다

각 서브스킬(`sub-skills/<name>/SKILL.md`)도 자체 frontmatter를 가지며, 파괴적 동작이 없는 분석 단계(`slo`, `monitor`, `log`, `incident`, `review`)는 `disable-model-invocation: false`, 배포 결정에 영향을 주는 단계(`iac`, `pipeline`, `strategy`)와 실제 인프라 변경(`apply`)은 `disable-model-invocation: true`로 차등 적용합니다.

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
- **사용자가 `/devops`로 스킬을 명시 호출한 이후에는**, 내부 서브스킬 파이프라인이 사용자 개입 없이 순차/병렬 자동 실행되며, 사용자 접점은 (1) 선행 결정 실현 불가 시 에스컬레이션과 (2) 최종 결과 보고 두 곳뿐. **스킬 자체는 모델 자동 호출(model-invocation)로 기동되지 않으며**(`disable-model-invocation: true`), 실제 인프라 변경(`terraform apply`, `kubectl apply` 등)은 본 스킬의 범위 밖이며 별도의 `devops/apply` 서브스킬에서 추가 사용자 승인 절차를 거친 뒤에만 수행

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

### 1단계: `devops/SKILL.md` 진입점 및 `references/` 구축

Claude Code Skill 표준에 따라 **단일 진입점은 `devops/SKILL.md`** 이며, 별도의 `skills.yaml`은 만들지 않습니다. 스킬 메타데이터는 SKILL.md의 YAML frontmatter에, 상세 참조 자료는 `references/` 하위 markdown 파일에 분산 배치합니다. SKILL.md 본문은 **500줄 이내**로 유지하고, 표/스키마/카탈로그는 references에서 Just-in-Time으로 로드합니다.

**1-1. `devops/SKILL.md` frontmatter**: 앞서 정의한 `name`, `description`(250자 이내, 전방에 "무엇을/언제" 배치), `argument-hint`, `disable-model-invocation: true`, `effort`, `allowed-tools`, `paths`, `hooks` 필드를 최상단에 배치.

**1-2. `devops/SKILL.md` 본문**: 아래 지시문만 간결하게 수록하고, 상세는 references로 위임.
- 오케스트레이션 규칙(서브스킬 호출 순서, 병렬성, `$ARGUMENTS`로 경량/중량 분기)
- 에이전트 행동 규칙(메타데이터 직접 편집 금지, `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 경유 강제)
- 선행 산출물 존재 확인(`` !`ls arch/artifacts` ``, `` !`ls impl/artifacts` `` 동적 주입)
- 에스컬레이션 판별의 대략적 원칙 + 상세는 `references/escalation-rules.md`로 위임
- Deploy → Observe 피드백 루프 검증의 핵심 항목 + 상세는 `references/deploy-observe-checklist.md`로 위임

**1-3. `references/` 파일 세트** — 상세 정보는 전부 references에 분산:
- `references/upstream-contract.md` — Arch/Impl 4섹션 소비 매핑 표, RE 간접 참조 경로, 입력 스키마
- `references/output-sections.md` — 4섹션(`pipeline_configuration`, `infrastructure_code`, `observability_configuration`, `operational_runbooks`) 필드 정의 및 필수/선택 여부, 후속 스킬 연계 계약
- `references/agent-flow.md` — 서브스킬 간 순차/병렬 호출 그래프, Deploy↔Observe 피드백 연결
- `references/escalation-rules.md` — 각 에이전트별 에스컬레이션 조건과 사용자 메시지 형식
- `references/supported-tools.md` — 지원 CI/CD 플랫폼(GitHub Actions, Jenkins, GitLab CI), IaC(Terraform, Ansible, Helm, Pulumi), 클라우드(AWS, GCP, Azure), 모니터링(Prometheus, Grafana, Datadog, CloudWatch), 로깅(ELK, Loki, CloudWatch Logs) 카탈로그
- `references/sli-slo-patterns.md` — RE 품질 속성 → SLI 변환 패턴 카탈로그
- `references/deploy-strategy-tree.md` — SLO 수준 + 아키텍처 특성 기반 배포 방식 선택 의사결정 트리
- `references/deploy-observe-checklist.md` — review 서브스킬이 사용하는 정합성 검증 체크리스트

**1-4. 적응적 깊이**: `$ARGUMENTS`(또는 `$1`)로 전달받은 모드 값(`light`/`heavy`)을 SKILL.md 본문의 분기 지시문에 사용. 인자가 없으면 선행 Arch/Impl 산출물의 규모(컴포넌트 수, 환경 수)로 자동 판별.

**1-5. 의존성 선언**: SKILL.md 본문에 선행(`arch`, `impl`, RE 간접 참조) 및 후속 소비자(`management`, `security`, `qa`) 관계를 명시. `paths` frontmatter로 `arch/**`, `impl/**`, `re/**`가 존재할 때만 활성화되도록 범위 제한.

### 2단계: 메타데이터 스키마 · 템플릿 · 조작 스크립트 구축 (`scripts/`, `assets/`)

에이전트가 YAML/JSON 파일을 직접 편집하지 않고 상태를 갱신할 수 있도록, 메타데이터 스키마와 템플릿, 그리고 조작 스크립트를 먼저 구축합니다. 이 단계는 이후 모든 에이전트가 의존하는 기반 계층입니다.

#### 2-1. 메타데이터 스키마 정의 (`scripts/schema/`)

4섹션 각각에 대한 YAML 스키마 파일을 작성합니다:

- `pipeline.schema.yaml`, `iac.schema.yaml`, `observability.schema.yaml`, `runbook.schema.yaml`
- 각 스키마는 (1) 기존 4섹션에 정의된 도메인 필드와 (2) 공통 관리 필드(`phase`, `progress`, `updated_at`, `updated_by`, `approval_state`, `approver`, `approved_at`, `review_comments`, `upstream_refs`, `downstream_refs`, `doc_path`)를 포함
- `phase`의 허용 전이 그래프 정의 (예: `draft → in_progress → ready_for_review → approved → published`, 역방향은 `changes_requested`를 통해서만 허용)
- `upstream_refs`/`downstream_refs`의 참조 대상 유형 제약 (예: 런북의 `upstream_refs`는 반드시 `MON-xxx` 또는 `PL-xxx`의 롤백 절차여야 함)

#### 2-2. 문서/메타데이터 템플릿 작성 (`assets/`)

> Claude Code Skill 표준 컨벤션에 따라 템플릿 디렉토리 이름은 `assets/`를 사용합니다(기존의 `templates/` 명칭에서 변경). SKILL.md 및 서브스킬에서는 `${CLAUDE_SKILL_DIR}/assets/pipeline.meta.yaml.tmpl` 형태로 참조합니다.

각 산출 항목 유형별로 **메타데이터 템플릿**과 **문서 템플릿**을 쌍으로 준비합니다:

- `*.meta.yaml.tmpl`: 스키마에 정의된 모든 필드를 빈 값 또는 기본값으로 포함하며, 각 필드에 주석으로 채움 가이드를 제공 (예: `# phase: 반드시 scripts/artifact.py transition으로만 변경`)
- `*.md.tmpl`: 문서의 기본 섹션 헤더와 플레이스홀더 (예: `## 개요`, `## 배포 전략 근거`, `## 롤백 절차`, `<!-- TODO: 여기에 SLO 번-레이트 임계값 근거를 기술 -->`) 를 미리 배치
- 템플릿은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py init` 명령이 소비하며, 에이전트는 생성된 골격을 기반으로 문서 markdown만 직접 편집
- `scripts/artifact.py validate`(및 `validate_all.py`)는 frontmatter의 `hooks.PostToolUse`/`hooks.Stop`에 연결되어, 에이전트가 `.meta.yaml`을 직접 편집한 경우 하드웨어 수준에서 차단되고 실패 메시지가 에이전트에 전달됨

#### 2-3. 메타데이터 조작 스크립트 작성 (`scripts/artifact.py`)

에이전트가 사용하는 유일한 상태 조작 인터페이스입니다. 최소 다음 서브커맨드를 제공합니다:

| 커맨드 | 역할 |
|--------|------|
| `artifact.py init <kind> <id>` | 템플릿으로부터 메타데이터 YAML + 문서 markdown 쌍 생성. `phase=draft`, `updated_at` 자동 기록 |
| `artifact.py get <id> [--field ...]` | 메타데이터 필드 조회. 에이전트가 상태를 확인할 때 사용 |
| `artifact.py set <id> --field <k>=<v>` | 도메인 필드 값 갱신. 스키마 검증 및 `updated_at`/`updated_by` 자동 기록. `phase`와 `approval_state`는 이 커맨드로 변경 불가 |
| `artifact.py transition <id> --to <phase>` | `phase` 상태 전이. 허용 전이 그래프에 따른 검증 수행 |
| `artifact.py approve <id> --approver <who> [--comment ...]` | `approval_state=approved` 전이 및 `approver`/`approved_at` 기록 |
| `artifact.py request-changes <id> --approver <who> --comment <msg>` | `changes_requested` 전이 및 `review_comments` 추가 |
| `artifact.py link <id> --upstream <ref> \| --downstream <ref>` | 추적성 참조 추가. 참조 대상 존재 여부 및 유형 제약 검증 |
| `artifact.py validate <id>` | 스키마 적합성 + 추적성 정합성 + `doc_path` 대응 파일 존재 검증 |
| `artifact.py list [--kind ...] [--phase ...] [--approval-state ...]` | 메타데이터 인덱스 조회 (리뷰 에이전트용) |

**에이전트 행동 규칙**: 에이전트 시스템 프롬프트(3단계)는 "`.meta.yaml` 파일을 직접 편집하지 말 것. 상태 갱신은 반드시 `scripts/artifact.py` 커맨드로 수행할 것"을 명시합니다. 문서 markdown 파일(`.md`)은 에이전트가 직접 편집할 수 있되, 편집 후 `artifact.py set --field progress=...` 또는 `artifact.py transition`으로 대응 메타데이터를 반드시 갱신해야 합니다.

### 3단계: 서브스킬 `SKILL.md` 작성 (`sub-skills/<name>/SKILL.md`)

8개 서브 에이전트는 각자 `sub-skills/<name>/SKILL.md`로 구성된 **서브스킬**이며, 자체 YAML frontmatter(`name`, `description`, `disable-model-invocation`, `effort`, `allowed-tools` 등)와 본문을 가집니다. 본문에서는 `` !`cat arch/artifacts/AD-*.meta.yaml` ``과 같은 동적 컨텍스트 주입을 활용하여 선행 산출물을 스킬 호출 시점에 자동 로드합니다. 아래는 각 서브스킬의 역할/입출력/에스컬레이션 요약입니다.

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

### 4단계: 서브스킬 본문 지시문 및 참조 자료 연동

서브스킬 SKILL.md의 본문과 대응 `references/` 자료를 함께 작성합니다. 과거 PLAN이 분리해 두었던 `prompts/` 디렉토리는 폐기하며, 각 서브스킬의 프롬프트는 해당 서브스킬의 SKILL.md 본문 + 참조 자료로 흡수됩니다. 작성 항목:
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
- **메타데이터 조작 스크립트 사용 가이드**: `scripts/artifact.py`의 각 서브커맨드를 언제 호출해야 하는지, 문서 편집과 메타데이터 갱신의 순서, `phase`/`approval_state` 전이 시점을 프롬프트에 명시
- Chain of Thought 가이드라인
- Few-shot 예시 포함

### 5단계: 입출력 예시 작성 (`examples/`)

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
- **메타데이터/문서 쌍 예시**: 각 산출 항목 유형(파이프라인, IaC, 관찰 가능성, 런북)마다 `*-output.md`와 `*-output.meta.yaml`을 **동시에** 제공. 메타데이터 파일은 진행 상태(`phase`, `progress`), 승인 상태(`approval_state`, `approver`), 추적성(`upstream_refs`, `downstream_refs`)이 모두 기입된 완성 상태를 보여주며, 대응 markdown은 동일 식별자를 가진 완성된 문서 본문을 보여줌
- **스크립트 사용 흐름 예시**: `artifact.py init pipeline PL-001` → 템플릿 전개 → 에이전트가 `.md` 편집 → `artifact.py set PL-001 --field platform=github-actions` → `artifact.py link PL-001 --upstream IM-003` → `artifact.py transition PL-001 --to ready_for_review` → `artifact.py approve PL-001 --approver devops:review` 순서의 전체 커맨드 로그

## 핵심 설계 원칙

1. **선행 스킬 기반 (Predecessor-Driven)**: 모든 인프라/파이프라인/모니터링 결정은 Arch/Impl/RE 산출물에 근거하며, `arch_refs`/`impl_refs`/`re_refs`로 추적성을 유지. 선행 스킬이 확정한 컴포넌트 구조, 기술 스택, 품질 속성은 재질문하지 않고 전제로 수용
2. **자동 실행 + 예외 에스컬레이션 (Auto-Execute with Exception Escalation)**: 사용자가 `/devops`로 스킬을 명시 호출한 뒤에는 선행 스킬 산출물을 기반으로 인프라/파이프라인/운영 설정을 자동 생성. 선행 결정이 DevOps 레벨에서 실현 불가능한 경우에만 사용자에게 에스컬레이션. **스킬 자체는 `disable-model-invocation: true`로 설정**되어 모델 자동 호출로는 기동되지 않으며, 실제 인프라 변경은 본 스킬의 범위 밖으로 분리되어 `devops/apply` 서브스킬에서 별도 사용자 승인 후 수행
3. **Deploy-Observe 연속성 (Deploy-Observe Continuity)**: 배포와 관찰을 하나의 피드백 루프로 통합. 배포 전략이 모니터링을 결정하고(`strategy` → `monitor`), 모니터링 결과가 배포 결정에 피드백(`SLO burn rate` → `rollback trigger`). 이 연결이 DevOps 스킬 통합의 핵심 가치
4. **SLO 중심 운영 (SLO-Centric Operations)**: `slo` 에이전트가 전체 파이프라인의 첫 번째 진입점. RE 품질 속성 메트릭에서 도출된 SLO가 배포 전략(에러 버짓 기반 보수성), 모니터링(번-레이트 알림), 런북(롤백 트리거)을 관통하는 기준점
5. **적응적 깊이 (Adaptive Depth)**: Arch/Impl 모드에 연동하여 경량(단일 파이프라인 + 기본 모니터링)/중량(멀티 환경 IaC + 종합 관찰 가능성 + 상세 런북) 모드 자동 전환
6. **불변 인프라 + GitOps**: 인프라는 수정하지 않고 교체. 모든 배포 설정은 Git에서 관리하는 선언적 배포. dev/staging/prod 환경 간 동일 구조에 변수만 분리
7. **관찰 가능성 3대 축 통합**: 메트릭(monitor), 로그(log), 트레이스(monitor 분산 추적)를 SLO 기준으로 통합. 상관 ID로 세 축 간 연결
8. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **파이프라인 설정 / 인프라 코드 / 관찰 가능성 설정 / 운영 런북** 4섹션으로 고정하여, 후속 스킬(`management`, `security`, `qa`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
9. **Claude Code Skill 표준 포맷 준수 (Skill-Format Conformance)**: 단일 진입점 `devops/SKILL.md` + YAML frontmatter, `scripts/`/`assets/`/`references/` 표준 디렉토리, 8개 서브에이전트의 서브스킬(`sub-skills/<name>/SKILL.md`) 분리, `$ARGUMENTS`/`${CLAUDE_SKILL_DIR}`/동적 컨텍스트 주입 활용, `paths`/`hooks` 기반 활성화 범위 및 메타데이터 무결성 강제, `disable-model-invocation: true`로 파괴적 작업의 자동 호출 차단. 실제 인프라 변경은 `devops/apply` 서브스킬로 분리하여 사용자 승인 절차를 이중화
10. **메타데이터-문서 분리 및 스크립트 기반 상태 관리 (Metadata-Document Separation, Script-Gated State)**: 모든 산출물은 **구조화 메타데이터(YAML) + 사람이 읽는 문서(markdown)**의 쌍으로 관리하며, 두 파일은 동일한 식별자로 1:1 대응. 에이전트는 문서 markdown은 직접 편집하되, 메타데이터 파일(`phase`, `progress`, `approval_state`, `upstream_refs`/`downstream_refs` 등)은 **반드시 `scripts/artifact.py` 커맨드를 통해서만** 조작. 이 원칙은 스키마 검증, 상태 전이 규칙, 자동 타임스탬프 기록을 단일 진입점에 집중시켜 메타데이터 무결성과 추적성을 보장. 실행 가능한 IaC/파이프라인 YAML 파일과 이 **상태 관리용 메타데이터 YAML(`.meta.yaml`)**은 디렉토리와 확장자로 엄격히 구분
