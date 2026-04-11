# Orch (Orchestration) Skill 구현 계획

## 개요

harness 모노레포의 8개 스킬(ex, re, arch, impl, qa, sec, devops, orch) 전체를 조율하는 **컨트롤 플레인**입니다. 사용자는 항상 orch 스킬을 통해 통신하며, 개별 스킬을 직접 호출하지 않습니다. 자연어 요청을 받아 적절한 스킬 또는 사전 정의 파이프라인으로 라우팅하고, 실행(run) 단위로 산출물·상태·로그를 관리합니다.

다른 스킬이 "콘텐츠 산출물"(요구사항, 아키텍처, 코드 등)을 생성하는 것과 달리 orch의 산출물은 **실행 자체**(run state, 호출 로그, 완료 보고서)입니다.

### 전통적 워크플로우 엔진 vs AI 컨텍스트 오케스트레이션

| 구분 | 전통적 워크플로우 엔진 | AI 컨텍스트 오케스트레이션 (orch) |
|------|------------------------|-----------------------------------|
| 입력 | DAG 정의 파일, JSON 페이로드 | **사용자 자연어 요청** + 현재 run 스냅샷 |
| 의도 분석 | 사람이 사전에 DAG 작성 | LLM 기반 의도 분석으로 자동 라우팅 |
| 사용자 개입 | 별도 UI / 외부 시스템 | **relay 스테이지를 통한 멀티턴 대화 중계** |
| 상태 저장 | 중앙 DB | run 디렉토리 내 YAML 파일 (`run.meta.yaml`) |
| 재개 | 작업 ID 기반 재시작 | `current-run.md` 스냅샷 단일 파일로 즉시 복원 |
| 사용자 진입점 | API/CLI 다수 | **단일 진입점 — orch가 유일한 사용자 인터페이스** |

## 스킬 레지스트리 및 소비 관계

orch는 콘텐츠를 직접 소비/생산하지 않습니다. 대신 **스킬 브로커**로서 다음 역할을 수행합니다.

### 스킬 디스커버리

orch는 모노레포의 7개 콘텐츠 스킬을 레지스트리로 인식합니다. 각 스킬은 `<skill>/SKILL.md`라는 표준 진입점과 산출물 디렉토리(`runs/<id>/<skill>/`)를 가집니다.

| 스킬 | 역할 | 주요 산출물 섹션 |
|------|------|-----------------|
| ex | 기존 코드베이스 탐색 | 4섹션 (구조 맵, 기술 스택, 컴포넌트 관계, 아키텍처 추론) |
| re | 요구사항 명세 | 3섹션 (요구사항, 제약, 품질 속성) |
| arch | 아키텍처 설계 | 4섹션 (결정, 컴포넌트, 기술 스택, 다이어그램) |
| impl | 구현 매핑 | 4섹션 (구현 맵, 코드 구조, 결정, 가이드) |
| qa | 품질 검증 | 4섹션 (전략, 테스트, 추적성, 보고서) |
| sec | 보안 검증 | 4섹션 (위협 모델, 취약점, 권고, 컴플라이언스) |
| devops | 운영/배포 | 4섹션 (파이프라인, IaC, 관측, 런북) |

### 입출력 브로커링

orch가 콘텐츠를 만들지는 않지만, 스킬 간 입출력을 조립·전달합니다.

- 업스트림 스킬 산출물(`runs/<id>/<prev-skill>/*.md`)을 후속 스킬의 컨텍스트로 주입
- 각 스킬의 `*.meta.yaml` 상태(phase/approval)를 관찰하여 다음 스킬 트리거 여부 결정
- 모든 메타데이터 조작은 orch의 `${CLAUDE_SKILL_DIR}/scripts/artifact.py`를 통해서만 이루어지며, 콘텐츠 스킬은 본문(`*.md`)만 편집합니다.

상세한 레지스트리 구조와 디스커버리 규약은 `references/contracts/skill-registry.md`에 분리합니다.

## 적응적 깊이 (단일 스킬 vs 파이프라인 실행)

orch는 사용자 요청의 복잡도에 따라 **단일 스킬 디스패치**와 **다중 스킬 파이프라인 실행** 사이에서 모드를 자동 선택합니다.

| 모드 | 판별 기준 | 동작 |
|------|-----------|------|
| 경량 (단일 디스패치) | 단일 스킬·에이전트로 충족 가능한 요청 ("ex로 이 코드 분석해줘") | dispatch만 거쳐 한 스킬을 직접 스폰. run.meta.yaml은 단일 스텝으로 기록 |
| 중량 (파이프라인) | 다중 스킬·다중 단계가 필요한 요청 ("이 앱을 새로 만들어줘") | dispatch → pipeline → relay/run 전 단계 활성화. 사전 정의 파이프라인 또는 동적 DAG 생성 |

판별 규칙은 `references/adaptive-depth.md`로 분리합니다.

## 런타임 산출물 구조

orch의 산출물은 콘텐츠 스킬의 4섹션 문서가 아니라, **실행 자체의 런타임 데이터**입니다. 다음 4가지로 구성됩니다.

### 1. 런 디렉토리 (`runs/<run_id>/`)

각 실행은 독립된 디렉토리에 격리됩니다. 사용자는 출력 루트 경로(기본: `./harness-output/`)를 지정할 수 있습니다.

```
<output-root>/
├── current-run.md                      # 활성 run 스냅샷 (사람 읽기용)
├── pipeline.meta.yaml                  # orch 자체 파이프라인 상태 (스크립트 전용)
└── runs/
    └── <run_id>/                       # 형식: YYYYMMDD-HHmmss-<4자리-해시>
        ├── run.meta.yaml               # 정본 run 상태 (스크립트 전용)
        ├── run.meta.md                 # YAML의 사람 읽기용 렌더링
        ├── calls.log                   # 스킬 호출 로그
        ├── project-structure.md        # 완료 시 생성
        ├── release-note.md             # 완료 시 생성
        ├── ex/  re/  arch/  impl/  qa/  sec/  devops/
        │   └── <name>.meta.yaml + <name>.md  # 각 스킬 산출물 쌍
```

각 콘텐츠 스킬 디렉토리 하위 산출물은 해당 스킬의 책임이며, orch는 이들의 `.meta.yaml`을 관찰만 합니다.

### 2. 런 상태 (`run.meta.yaml`)

| 필드 | 설명 |
|------|------|
| `run_id` | 실행 식별자 (`YYYYMMDD-HHmmss-<hash>`) |
| `pipeline` | 파이프라인 식별자 (예: `full-sdlc`) 또는 `single:<skill>:<agent>` |
| `output_root` | 산출물 루트 경로 |
| `status` | `pending` / `running` / `paused` / `completed` / `failed` |
| `created_at` / `updated_at` | ISO 8601 타임스탬프 |
| `steps[]` | 단계별 상태 (index, skill, agent, status, approval, artifacts) |
| `dialogue_history[]` | 단계별 대화 턴 수 요약 |
| `errors[]` | 발생한 오류 |

### 3. 스킬 호출 로그 (`calls.log`)

각 스킬 스폰/완료 이벤트와 relay 왕복을 시간순으로 기록합니다. 디버깅과 재현에 사용됩니다.

### 4. 완료 보고서 (`project-structure.md` / `release-note.md`)

파이프라인 완료 직후 pipeline 스테이지가 생성하는 사람이 읽는 마무리 문서입니다.

- `project-structure.md`: 전체 디렉토리 구조, 기술 스택 요약, 의존 관계, 빌드/실행 가이드
- `release-note.md`: 실행된 스킬과 주요 결정, 추적성 요약, 품질/보안 결과, 알려진 제한사항

### 산출물 파일 구성: 메타데이터 + 문서 분리

orch도 다른 스킬과 동일한 **YAML 메타데이터 + Markdown 문서** 분리 패턴을 따릅니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 | YAML (`run.meta.yaml`, `pipeline.meta.yaml`) | run/pipeline의 상태·승인·추적 정보. 스크립트가 단일 진실 공급원으로 읽고 씀 |
| 문서 | Markdown (`run.meta.md`, `current-run.md`, `release-note.md`, `project-structure.md`) | 사람이 읽는 렌더링 또는 완료 보고서 |

**YAML 채택 근거**: 주석 지원으로 상태 전이 사유를 인라인으로 남길 수 있고, PR 리뷰에서 사람이 직접 읽을 수 있으며, PyYAML로 손쉽게 파싱됩니다.

### 메타데이터 스키마 (공통 필드 + 런 전용 필드)

다른 스킬과 동일한 공통 필드를 따르되, run 전용 필드를 추가합니다.

| 필드 분류 | 필드 |
|----------|------|
| 공통 | `artifact_id`, `phase`, `approval.state`, `approval.approver`, `approval.approved_at`, `upstream_refs`, `downstream_refs`, `updated_at` |
| 런 전용 | `run_id`, `pipeline`, `output_root`, `started_at`, `ended_at`, `status`, `involved_skills[]`, `steps[]`, `dialogue_history[]` |

상세 스키마는 `references/schemas/run-state-schema.md`와 `references/schemas/pipeline-schema.md`로 분리합니다.

### 스크립트 기반 메타데이터 조작 (필수)

orch 에이전트(스테이지)는 **YAML을 직접 편집하지 않습니다**. 모든 상태 전이는 `${CLAUDE_SKILL_DIR}/scripts/run.py`(또는 `artifact.py`)를 거치며, 이는 스키마 검증·타임스탬프 자동화·승인 이력 append-only를 보장합니다.

| 스크립트 커맨드 | 역할 |
|----------------|------|
| `run.py init-run --pipeline <name>` | run-id 발급, 디렉토리 생성, `run.meta.yaml` 초기화 |
| `run.py update-state --run <id> --step <idx> --status <s>` | 단계 상태 갱신 + `updated_at` 자동 |
| `run.py complete --run <id>` | 완료 처리 + `current-run.md`를 idle로 전환 |
| `run.py cancel --run <id> --reason <r>` | 실행 취소 기록 |
| `run.py list` | 전체 run 목록 조회 |
| `run.py show --run <id>` | 단일 run 상세 조회 |
| `run.py validate [--run <id>]` | 스키마/추적성 무결성 검증 |
| `run.py observe --run <id>` | 하위 스킬 `.meta.yaml`을 전부 스캔하여 phase/approval 요약 (게이팅 입력) |
| `run.py next --run <id>` | 현재 상태 기준 다음 실행 가능 단계 반환 |
| `run.py render --run <id>` | `run.meta.yaml` → `run.meta.md` / `current-run.md` 재생성 |

### 문서 템플릿 (`assets/templates/`)

표준 `assets/templates/` 규약을 따르며, 다음 템플릿을 사전 정의합니다.

| 템플릿 파일 | 대상 |
|------------|------|
| `run.meta.yaml.tmpl` | `run.meta.yaml` 초기 골격 (status: pending, 빈 steps 등) |
| `pipeline.meta.yaml.tmpl` | orch 자체 파이프라인 상태 골격 |
| `run.meta.md.tmpl` | `run.meta.yaml`의 사람 읽기용 렌더링 슬롯 |
| `current-run.md.tmpl` | `current-run.md` 초기 템플릿 |
| `completion-report.md.tmpl` | `release-note.md` 골격 |
| `project-structure.md.tmpl` | `project-structure.md` 골격 |

### 후속 스킬 연계 (orch is the broker)

orch는 콘텐츠 스킬에 산출물을 전달하지 않습니다. 대신 **콘텐츠 스킬 사이의 산출물 전달을 중개**합니다.

```
사용자 자연어
    │
    ▼
orch (dispatch → pipeline)
    │  - 스킬 레지스트리에서 적절 스킬 선택
    │  - 업스트림 산출물(runs/<id>/<prev>/*.md) 조립
    │  - 후속 스킬 스폰 시 컨텍스트로 주입
    │  - 완료된 산출물의 .meta.yaml을 observe하여 게이팅
    ▼
콘텐츠 스킬(ex/re/arch/impl/qa/sec/devops)
```

각 콘텐츠 스킬의 `.meta.yaml`은 orch가 읽어들이는 **분산 상태 저장소**로 기능하며, `run.meta.yaml`은 그 인덱스/요약본 역할을 합니다.

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 [Claude Code Skill 공식 표준](https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점은 `orch/SKILL.md`이며, `skills.yaml`, `agents/`, `prompts/` 디렉토리는 사용하지 않습니다.

```
orch/
├── SKILL.md                              # 필수 진입점 (frontmatter + 동적 컨텍스트 주입 + 워크플로우 요약, 500줄 이내)
├── scripts/
│   ├── run.py                            # run/pipeline 메타데이터 조작 CLI (init-run/update-state/complete/observe/next/render/validate)
│   └── lib/
│       ├── meta_io.py                    # YAML 로드/저장, 스키마 검증
│       └── refs.py                       # upstream/downstream 추적성 해석
├── assets/
│   └── templates/
│       ├── run.meta.yaml.tmpl
│       ├── pipeline.meta.yaml.tmpl
│       ├── run.meta.md.tmpl
│       ├── current-run.md.tmpl
│       ├── completion-report.md.tmpl
│       └── project-structure.md.tmpl
└── references/
    ├── workflow/                         # SKILL.md가 단계 진입 시 on-demand로 Read하는 6 스테이지 상세 규칙
    │   ├── dispatch.md
    │   ├── pipeline.md
    │   ├── relay.md
    │   ├── run.md
    │   ├── config.md
    │   └── status.md
    ├── rules/                            # 스폰되는 스킬에 주입되는 행동 규칙 (4개, orch 고유)
    │   ├── base.md
    │   ├── output-format.md
    │   ├── escalation-protocol.md
    │   └── dialogue-protocol.md
    ├── pipelines/                        # 사전 정의 파이프라인 (8개, orch 고유)
    │   ├── full-sdlc.md
    │   ├── full-sdlc-existing.md
    │   ├── new-feature.md
    │   ├── new-feature-existing.md
    │   ├── security-gate.md
    │   ├── security-gate-existing.md
    │   ├── quick-review.md
    │   └── explore.md
    ├── contracts/
    │   └── skill-registry.md             # 스킬 디스커버리 및 호출 규약
    ├── schemas/
    │   ├── run-state-schema.md           # run.meta.yaml 스키마 명세
    │   └── pipeline-schema.md            # pipeline.meta.yaml 스키마 명세
    ├── adaptive-depth.md                 # 단일 디스패치 vs 파이프라인 분기 규칙
    └── examples/                         # 실행 흐름 예시 (3개)
        ├── full-sdlc-example.md
        ├── existing-project-example.md
        └── resume-example.md
```

요점:
- `SKILL.md`가 유일한 필수 진입점이며, 6개의 워크플로우 스테이지(dispatch/pipeline/relay/run/config/status)는 동일 SKILL.md 안에 짧게 요약하고 상세 규칙은 `references/workflow/*.md`에 분리합니다.
- 표준 명칭 `assets/templates/`, `references/`, `scripts/`만 사용하며 `skills.yaml`은 폐기합니다.
- `references/workflow/*.md`는 별도 시스템 프롬프트가 아니라 SKILL.md가 on-demand로 Read하는 단계별 행동 규칙 문서입니다.

## 워크플로우 단계 (SKILL.md 내부 단일 진입점)

기존 PLAN의 "6개 내부 에이전트" 개념은 표준 스킬 모델과 직접 매핑되지 않습니다. 대신 SKILL.md가 순차적으로 수행하는 **6개의 워크플로우 스테이지**로 재정의하고, 각 스테이지의 상세 행동 규칙은 `references/workflow/<stage>.md`에 분리합니다. 필요 시점에 SKILL.md가 Read로 로드합니다.

```
사용자 자연어 요청
    │
    ▼
[Stage 1] dispatch ───────── references/workflow/dispatch.md 로드
    │  (의도 분석 → 단일 스킬 vs 파이프라인 라우팅)
    │
    ▼
[Stage 2] pipeline ───────── references/workflow/pipeline.md 로드
    │  (DAG 실행, 스킬 스폰, 게이팅, 병렬 실행 worktree 격리)
    │
    ├──→ [Stage 3] relay ──── references/workflow/relay.md 로드
    │    (needs_user_input 신호 → 사용자 대화 → 응답 패키징)
    │
    ├──→ [Stage 4] run ────── references/workflow/run.md 로드
    │    (run-id 발급, 디렉토리 생성, 산출물 검증, 완료 처리)
    │
    ├──→ [Stage 5] config ─── references/workflow/config.md 로드
    │    (출력 경로, 스킬 활성화, 파이프라인 템플릿 관리)
    │
    ▼
[Stage 6] status ─────────── references/workflow/status.md 로드
    (실행 이력, 산출물 조회, 통계)
```

각 스테이지의 상세는 다음과 같이 분리됩니다.

### `references/workflow/dispatch.md`
- **역할**: 사용자의 유일한 진입점. 자연어 요청을 분석하여 스킬 또는 파이프라인으로 라우팅
- **핵심 역량**: 자연어 의도 분석, 복합 요청의 다중 스킬 분해, 선행 조건 검증, 기존 프로젝트 감지(ex 선행 배치), 재개 요청 인식, `current-run.md` 단일 파일로 즉시 컨텍스트 파악
- **입력**: `$ARGUMENTS` 사용자 요청 + 동적 주입된 `current-run.md` 스냅샷
- **출력**: 파이프라인 정의(스킬 목록 + 순서 + 병렬 그룹) 또는 단일 스킬 호출 지시

### `references/workflow/pipeline.md`
- **역할**: DAG 기반 워크플로 실행, 스킬 간 흐름 제어
- **핵심 역량**: 순차/병렬/조건부 실행, 각 스킬을 Task로 스폰, `needs_user_input` 감지 → relay 위임, 체크포인트 기록, 병렬 실행 시 `EnterWorktree`/`ExitWorktree`로 worktree 격리, 완료 후 보고서 생성
- **입력**: dispatch 출력(파이프라인 정의), run-id, 산출물 경로
- **출력**: 각 스킬 실행 결과 집계, 전체 워크플로 요약
- **상호작용 모델**: 스킬 스폰 → 결과 수신 → `run.py observe`로 게이팅 → 다음 단계 결정

### `references/workflow/relay.md`
- **역할**: 실행 중 스킬과 사용자 간 멀티턴 대화 중계
- **핵심 역량**: 구조화된 `needs_user_input`을 사람이 읽기 좋은 형태로 변환, 사용자 응답 수집·패키징, 대화 이력 요약 유지, "건너뛰기" / "기본값 수용" 의사 인식
- **입력**: 스킬의 `needs_user_input` 신호
- **출력**: `user_response` 패키지 (이전 대화 요약 포함)

### `references/workflow/run.md`
- **역할**: run 생명주기 관리, 디렉토리 생성, 상태 추적, 재개 지원
- **핵심 역량**: `run.py init-run`으로 디렉토리·메타데이터 초기화, 산출물 골격 생성, 필수 섹션 검증(EX=4, RE=3, ARCH=4, IMPL=4, QA=4, SEC=4, DEVOPS=4), `run.py update-state`로 단계 상태 반영, `run.py render`로 `run.meta.md` / `current-run.md` 동기화, 완료 시 `current-run.md`를 idle로 갱신
- **입력**: 파이프라인 정의, 출력 설정
- **출력**: run 디렉토리 경로, 상태 업데이트, 완료 보고
- **생명주기**: INIT → CONFIGURE → EXECUTE → COLLECT → REPORT → CLEANUP

### `references/workflow/config.md`
- **역할**: 스킬 설정, 행동 규칙, 파이프라인 템플릿 관리
- **핵심 역량**: 스킬 활성화/비활성화, 출력 루트 경로 설정, 파이프라인 템플릿 관리(사전 정의 + 사용자 정의), 설정 검증, 프로필 기반 설정
- **입력**: 설정 변경 요청
- **출력**: 변경 결과, 현재 설정 상태

### `references/workflow/status.md`
- **역할**: 실행 이력 조회, 스킬 상태 확인, 산출물 검색
- **핵심 역량**: 설치된 스킬 목록, 스킬 버전/상태, run 이력, 특정 run 산출물 조회, 의존성 그래프, 사용 통계
- **입력**: 조회 조건 (스킬명, run-id, 기간, 상태)
- **출력**: 현황 리포트

## 동적 컨텍스트 주입 (orch 고유)

orch SKILL.md는 표준 frontmatter를 가지지만, 본문 상단에 **harness가 매 호출마다 주입하는 동적 컨텍스트 헤더**를 포함합니다. 이 패턴은 "current-run.md를 읽어라"는 지시를 모델이 아니라 harness가 책임지게 합니다.

```markdown
## Current State
!`test -f harness-output/current-run.md && cat harness-output/current-run.md || echo "status: idle"`

## Skill Root
!`echo ${CLAUDE_SKILL_DIR}`

## User Request
$ARGUMENTS
```

- **Current State**: 활성 run 스냅샷이 자동 주입되어 dispatch 스테이지가 별도 파일 읽기 없이 즉시 라우팅 가능
- **Skill Root**: `${CLAUDE_SKILL_DIR}`을 모든 내부 참조 경로의 기준점으로 사용 (하드코딩 방지)
- **User Request**: 사용자 자연어 요청을 표준 `$ARGUMENTS` 치환자로 수신

이 패턴은 다른 스킬에는 없는 orch 고유의 설계로, **사용자의 유일한 진입점**이라는 책임에서 비롯됩니다.

## 규칙 체계 (`references/rules/`)

orch가 스킬을 스폰할 때 모든 스킬에 공통 주입되는 행동 규칙입니다. 4개 파일로 구성되며 orch 고유 자산입니다.

### `base.md` — 기본 규칙
모든 스폰 스킬에 공통 적용. orch 컨텍스트 내 동작, 산출물 형식 준수, `needs_user_input` 에스컬레이션 규약, 업스트림 ID 추적성, 메타데이터 헤더 포함.

### `output-format.md` — 산출물 형식 규약
모든 산출물은 Markdown(.md) + 메타데이터(.meta.yaml) 쌍으로 저장. 파일 상단 메타 헤더, 섹션 분리 규칙, PLAN.md 필드 테이블 스키마.

### `escalation-protocol.md` — 에스컬레이션 규약
대화형 스킬(re:elicit, re:analyze, re:spec, re:review, arch:design, sec:threat-model)은 의미 단위마다 `needs_user_input` 사용. 자동 실행 스킬(ex/impl/qa/sec:audit/devops)은 예외 조건에서만 사용.

### `dialogue-protocol.md` — 대화 프로토콜
`needs_user_input` / `user_response` 신호의 정확한 구조 정의(질문 유형 open/choice/confirmation, 응답 패키지, 대화 요약).

## 사전 정의 파이프라인 (`references/pipelines/`)

orch가 즉시 라우팅 가능한 8개의 사전 정의 파이프라인. 각각 독립 파일로 정의되어 pipeline 스테이지가 참조합니다.

| 파이프라인 | 흐름 |
|-----------|------|
| `full-sdlc` | re:elicit → re:analyze → re:spec → arch:design → impl:generate → [qa:generate, sec:audit, devops:pipeline] |
| `full-sdlc-existing` | ex(4단계) → re(3단계) → arch:design → impl:generate → [qa, sec, devops] |
| `new-feature` | re:elicit → re:spec → arch:design → impl:generate → qa:generate |
| `new-feature-existing` | ex(4단계) → re:elicit → re:spec → arch:design → impl:generate → qa:generate |
| `security-gate` | sec:threat-model → sec:audit → sec:compliance |
| `security-gate-existing` | ex(4단계) → sec:threat-model → sec:audit → sec:compliance |
| `quick-review` | re:review → arch:review → impl:review |
| `explore` | ex:scan → ex:detect → ex:analyze → ex:map |

병렬 그룹(`[qa:generate, sec:audit, devops:pipeline]`)은 동일 레포 동시 수정 충돌을 막기 위해 각 스킬이 `EnterWorktree`로 독립 worktree에 진입 후 작업하고, 완료 시 pipeline 스테이지가 메인으로 머지합니다.

`-existing` 변종은 ex 4단계가 자동 실행으로 기존 코드베이스 컨텍스트를 추출하여 후속 스킬에 컨텍스트를 제공합니다.

## 구현 단계

### 1단계: `SKILL.md` 작성 (필수 진입점 + frontmatter + 동적 컨텍스트)

표준 frontmatter 필수 필드만 두고, 본문 상단에 동적 컨텍스트 주입 헤더를 배치합니다.

```yaml
---
name: orch
description: Orchestrates the full SDLC skill suite (ex, re, arch, impl, qa, sec, devops) as a single entry point. Use when the user wants to run a multi-skill pipeline, resume a prior run, or route a natural-language request to the right skill(s). Spawns subagents per step, relays dialogue, and persists per-run artifacts.
---
```

**frontmatter 설계 원칙**:
- `name: orch` 필수, 디렉토리명과 일치
- `description`은 250자 경계에서 잘릴 수 있음을 가정하여 라우팅 키워드(파이프라인/resume/status/config)를 앞에 배치
- 그 외 옵션 필드(`argument-hint`, `allowed-tools`, `context`, `agent`, `model`, `effort`, `hooks`, `paths`, `disable-model-invocation` 등)는 기본값으로 두고, 기본 동작으로 목적을 달성할 수 없음이 입증된 경우에만 추가합니다.

**SKILL.md 본문 구성 (500줄 이내)**:
1. 동적 컨텍스트 주입 헤더 (Current State / Skill Root / User Request)
2. 6개 워크플로우 스테이지 요약 (각 스테이지는 `references/workflow/<stage>.md`를 Read로 로드)
3. 스크립트 호출 규약 (`${CLAUDE_SKILL_DIR}/scripts/run.py`)

상세 규칙·스키마·파이프라인 정의는 모두 `references/`로 분리합니다.

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

기존 "6개 내부 에이전트" 개념을 6개 워크플로우 단계로 재정의하여 `references/workflow/`에 markdown 파일로 분리합니다. SKILL.md가 단계 진입 시 on-demand로 Read합니다. dispatch.md, pipeline.md, relay.md, run.md, config.md, status.md.

### 3단계: 참조 문서 작성 (`references/`)

- `references/rules/` 4개 (base, output-format, escalation-protocol, dialogue-protocol)
- `references/pipelines/` 8개 (full-sdlc, full-sdlc-existing, new-feature, new-feature-existing, security-gate, security-gate-existing, quick-review, explore)
- `references/contracts/skill-registry.md`: 스킬 디스커버리 및 호출 규약
- `references/schemas/run-state-schema.md`, `references/schemas/pipeline-schema.md`
- `references/adaptive-depth.md`: 단일 디스패치 vs 파이프라인 분기 규칙

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

표준 디렉토리 명칭은 `assets/templates/`입니다.

- `run.meta.yaml.tmpl`, `pipeline.meta.yaml.tmpl`: YAML 초기 골격(status: pending, 빈 steps 등)
- `run.meta.md.tmpl`, `current-run.md.tmpl`: 사람 읽기용 렌더링 슬롯
- `completion-report.md.tmpl`, `project-structure.md.tmpl`: 완료 보고서 골격

### 5단계: 런 관리 스크립트 구현 (`scripts/`)

`scripts/run.py`를 단일 진입점으로 구현하며 `init-run` / `update-state` / `complete` / `cancel` / `list` / `show` / `validate` / `observe` / `next` / `render` 서브커맨드를 제공합니다. 모든 쓰기 커맨드는 `updated_at`을 자동 갱신하고, 잘못된 상태 전이/누락 필드를 차단합니다.

**스크립트 호출 강제 (다층 방어)**:

행동 규약만으로는 우회될 수 있으므로 다층 방어를 구성합니다.

1. **행동 규약 (가장 약함)**: `references/workflow/*.md`와 SKILL.md 본문에서 "메타데이터 갱신은 반드시 `${CLAUDE_SKILL_DIR}/scripts/run.py`를 호출한다"를 반복 명시
2. **도구 권한 (중간)**: 워크플로우 가이드에서 Edit/Write 대상은 사람 읽기용 markdown으로 한정하도록 명시
3. **PreToolUse hooks (가장 강함)**: `*.meta.yaml`에 대한 직접 Edit/Write 시도를 차단하는 PreToolUse hook을 등록
4. **시작 시 상태 주입**: SKILL.md 동적 컨텍스트 헤더의 `current-run.md` 자동 주입을 통해 에이전트가 자연스럽게 스크립트 기반 흐름을 따르도록 유도

### 6단계: 입출력 예시 작성 (`references/examples/`)

3개의 실행 흐름 예시를 작성합니다.

- `full-sdlc-example.md`: 신규 시스템 개발 (대화 포함 전체 SDLC). dispatch → run init → 6 스텝 진행 → 완료 보고서 → idle 전환
- `existing-project-example.md`: 기존 프로젝트에 기능 추가 (ex 선행 → re/arch/impl/qa). 기존 프로젝트 감지 → `new-feature-existing` 라우팅
- `resume-example.md`: 중단된 실행 재개. `current-run.md`로 활성 run 즉시 식별 → 중단 지점부터 재실행

각 예시는 `run.meta.yaml` / `current-run.md`의 실제 모습과 함께 단계별 상태 전이를 보여줍니다.

## 핵심 설계 원칙

1. **사용자 유일 진입점 (Sole User Entry)**: 사용자는 항상 orch를 통해 통신. 개별 스킬 직접 호출 없음. orch는 모노레포에서 사용자에 노출되는 단 하나의 인터페이스.
2. **스킬 브로커 (Skill Broker)**: 자연어 요청을 분석하여 스킬/파이프라인으로 라우팅. orch는 콘텐츠를 생산하지 않고 콘텐츠 스킬 사이의 입출력을 중개.
3. **동적 컨텍스트 주입 (Dynamic Context Injection)**: SKILL.md 상단에서 `current-run.md` 스냅샷, `${CLAUDE_SKILL_DIR}`, `$ARGUMENTS`를 harness가 매 호출마다 주입. 모델이 아닌 harness가 컨텍스트 로딩을 책임.
4. **적응적 깊이 (Adaptive Depth)**: 단일 스킬 디스패치(경량)와 다중 스킬 파이프라인(중량) 사이에서 사용자 요청 복잡도에 따라 자동 분기.
5. **재개 가능성 (Resumability)**: `current-run.md` 단일 파일로 활성 run을 즉시 식별하고, `run.meta.yaml` 상태 기반으로 중단된 실행을 재개. 디렉토리 스캔 불필요.
6. **추적성 (Traceability)**: 모든 스킬 호출이 `run_id`로 추적되며, `calls.log`와 `run.meta.yaml`의 `steps[]`로 전체 실행 과정을 재현 가능.
7. **메타데이터-문서 분리 및 스크립트 경유 원칙**: run 상태는 `run.meta.yaml`(상태/승인/추적성)과 `run.meta.md`/`current-run.md`(사람 읽기용 렌더링)로 분리. 메타데이터는 에이전트가 직접 편집하지 않고 오직 `${CLAUDE_SKILL_DIR}/scripts/run.py` 커맨드를 통해서만 갱신. 사람 읽기용 문서는 `assets/templates/`의 사전 정의 템플릿으로 골격을 생성한 뒤 스크립트 렌더링으로 채워, 상태 일관성과 서식 표준을 동시에 보장.
8. **Claude Code Skill 표준 준수 (Standard Compliance)**: 단일 진입점 `SKILL.md` + YAML frontmatter, `scripts/`·`assets/`·`references/`의 표준 디렉토리 명칭, `${CLAUDE_SKILL_DIR}`/`$ARGUMENTS` 치환자 활용, 동적 컨텍스트 주입(`` !`<command>` ``)을 통해 공식 표준(https://code.claude.com/docs/ko/skills)과 완전히 호환.
