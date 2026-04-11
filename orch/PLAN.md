# Orch (Orchestration) Skill 구현 계획

## 개요

모든 스킬(ex, re, arch, impl, qa, sec, devops)의 실행을 조율하는 **컨트롤 플레인**입니다.
사용자는 항상 이 orchestration을 통해 통신하며, 개별 스킬을 직접 호출하지 않습니다.

**핵심 책임**:
- 사용자 요청을 분석하여 적절한 스킬/파이프라인으로 라우팅
- 에이전트를 통한 스킬 실행 및 흐름 제어 (순차/병렬)
- 실행(run)별 산출물 디렉토리 관리 및 저장 위치 지정
- 스킬 에이전트의 사용자 개입 요청을 중계 (relay)
- 에이전트 규칙(rule) 관리 및 산출물(output) 검증/저장
- 중단된 실행의 재개(resume) 지원
- 파이프라인 완료 후 프로젝트 구조 문서 및 릴리스 노트 자동 생성

## 표준 Claude Code Skill 포맷 준수

본 스킬은 [Claude Code Skill 공식 포맷](https://code.claude.com/docs/ko/skills)을 준수합니다.

- 엔트리 포인트는 `orch/SKILL.md` 단일 파일이며, YAML frontmatter를 포함합니다.
- SKILL.md 본문은 500줄 이하로 유지하고, 상세 설계·프롬프트·스키마·파이프라인 정의는 `references/` 하위 파일로 분리하여 온디맨드 로드됩니다.
- 템플릿(문서 골격, 메타데이터 초기값)은 `assets/templates/`에 위치합니다.
- 스크립트는 `scripts/`에 두고 SKILL.md에서 "실행하되 로드하지 않음" 규약으로 참조합니다.
- 문자열 치환(`$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`)과 동적 컨텍스트 주입(`` !`<command>` ``)을 적극 활용합니다.
- 내부 "에이전트"(dispatch/pipeline/relay/run/config/status)는 Skill 표준의 `agent` frontmatter 값(Explore/Plan/general-purpose/custom subagent)과 개념이 충돌하지 않도록 `references/agents/*.md`의 **서브에이전트 프롬프트 템플릿**으로 재배치되며, SKILL.md가 `Task` 도구로 스폰합니다.

### `orch/SKILL.md` Frontmatter

```yaml
---
name: orch
description: Orchestrates the full SDLC skill suite (ex, re, arch, impl, qa, sec, devops) as a single entry point. Use when the user wants to run a multi-skill pipeline, resume a prior run, or route a natural-language request to the right skill(s). Spawns subagents per step, relays dialogue, and persists per-run artifacts.
argument-hint: "<자연어 요청 | resume | status | config ...>"
context: fork
agent: general-purpose
model: claude-opus-4-6
effort: high
user-invocable: true
allowed-tools:
  - Task
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - EnterWorktree
  - ExitWorktree
paths:
  - harness-output/**
  - ${CLAUDE_SKILL_DIR}/references/**
  - ${CLAUDE_SKILL_DIR}/assets/**
  - ${CLAUDE_SKILL_DIR}/scripts/**
hooks:
  post-complete:
    - bash: ${CLAUDE_SKILL_DIR}/scripts/pipeline_state.py render --run "$RUN_ID"
---
```

**frontmatter 필드 근거**
- `context: fork` — heavy 파이프라인 실행 시 부모 세션 컨텍스트 오염을 방지 (배치/오케스트레이션 스킬 권고).
- `agent: general-purpose` — dispatch 라우팅에 자유도가 필요.
- `model` / `effort: high` — 라우팅 판단과 파이프라인 계획 수립에 고수준 추론 필요.
- `allowed-tools` — `Task`(서브에이전트 스폰), `Bash`(스크립트 실행), 파일 I/O 및 worktree 격리 도구 전부 선언.
- `paths` — 로더가 사전에 인지해야 할 파일 경로 범위 명시.
- `hooks.post-complete` — 파이프라인 종료 시 `project-structure.md` / `release-note.md` 생성 및 `current-run.md` 갱신을 harness가 자동 트리거.

### SKILL.md 본문 상단 패턴

SKILL.md는 다음과 같은 동적 컨텍스트 주입 헤더로 시작합니다. 이를 통해 "current-run.md를 읽어라"는 지시를 모델이 아닌 harness가 책임집니다.

```markdown
## Current State
!`test -f harness-output/current-run.md && cat harness-output/current-run.md || echo "status: idle"`

## Skill Root
!`echo ${CLAUDE_SKILL_DIR}`

## User Request
$ARGUMENTS
```

`${CLAUDE_SKILL_DIR}`는 `references/`, `assets/templates/`, `scripts/` 경로를 하드코딩하지 않도록 모든 참조 링크에 사용됩니다.

## 목표 구조

```
orch/
├── SKILL.md                          # 엔트리 포인트 (<500줄, frontmatter + dispatch 흐름 요약)
├── skills.yaml                       # (선택) 하위 스킬 레지스트리
├── references/                       # 온디맨드 로드 — SKILL.md가 링크로 참조
│   ├── rules/
│   │   ├── base.md
│   │   ├── output-format.md
│   │   ├── escalation-protocol.md
│   │   └── dialogue-protocol.md
│   ├── pipelines/
│   │   ├── full-sdlc.md
│   │   ├── full-sdlc-existing.md
│   │   ├── new-feature.md
│   │   ├── new-feature-existing.md
│   │   ├── security-gate.md
│   │   ├── security-gate-existing.md
│   │   ├── quick-review.md
│   │   └── explore.md
│   ├── agents/                       # 내부 subagent 프롬프트 템플릿 (Task 도구로 스폰)
│   │   ├── dispatch.md
│   │   ├── pipeline.md
│   │   ├── relay.md
│   │   ├── run.md
│   │   ├── config.md
│   │   └── status.md
│   └── schemas/
│       ├── artifact-meta.md          # <name>.meta.yaml 스키마 설명
│       └── pipeline-meta.md          # pipeline.meta.yaml / run.meta.yaml 스키마
├── assets/
│   └── templates/                    # 표준 `assets/` 규약
│       ├── artifact.meta.yaml        # 하위 스킬 산출물 메타데이터 템플릿
│       ├── pipeline.meta.yaml        # Orch 파이프라인 상태 메타데이터 템플릿
│       ├── run.meta.md               # 사람 읽기용 run 렌더링 템플릿
│       ├── current-run.md            # current-run.md 초기 템플릿
│       ├── ex/                       # ex 스킬 산출물 문서 템플릿 (4개)
│       ├── re/                       # re 스킬 산출물 문서 템플릿 (3개)
│       ├── arch/                     # arch 스킬 산출물 문서 템플릿 (4개)
│       ├── impl/                     # impl 스킬 산출물 문서 템플릿 (4개)
│       ├── qa/                       # qa 스킬 산출물 문서 템플릿 (4개)
│       ├── sec/                      # sec 스킬 산출물 문서 템플릿 (4개)
│       └── devops/                   # devops 스킬 산출물 문서 템플릿 (4개)
├── scripts/                          # "실행하되 로드하지 않음" 규약
│   ├── artifact.py                   # 하위 스킬 산출물 메타데이터 조작/조회 CLI
│   ├── pipeline_state.py             # Orch 자체 파이프라인 상태 메타데이터 CLI
│   └── lib/
│       ├── meta_io.py                # YAML 로드/저장, 스키마 검증
│       └── refs.py                   # upstream/downstream 참조 해석
└── examples/
    ├── full-run-example.md
    ├── dialogue-relay-example.md
    ├── escalation-example.md
    ├── resume-example.md
    ├── artifact-meta-example.yaml    # 산출물 메타데이터 파일 예시
    ├── artifact-doc-example.md       # 메타데이터와 쌍을 이루는 문서 파일 예시
    └── pipeline-meta-example.yaml    # Orch 파이프라인 상태 메타데이터 예시
```

**표준 준수 메모**
- `SKILL.md`가 엔트리 포인트이며 필수.
- `rules/`, `pipelines/`, `prompts/`, `agents/`는 모두 `references/` 하위로 통합. `prompts/`는 `agents/`와 중복이었으므로 제거.
- `templates/` → `assets/templates/`로 이동 (표준 `assets/` 규약).
- `scripts/`는 표준 규약 그대로 유지.
- `references/agents/*.md`의 "에이전트" 파일은 SKILL.md가 `Task` 도구로 스폰할 때 사용하는 **subagent 프롬프트 템플릿**이며, frontmatter `agent` 필드 값과는 다른 개념임을 명시.

---

## 산출물 디렉토리 구조

각 실행(run)은 독립된 디렉토리에 산출물을 저장합니다.
사용자는 출력 루트 경로를 지정할 수 있습니다 (기본값: `./harness-output/`).

각 산출물은 **메타데이터 파일(`*.meta.yaml`)과 문서 파일(`*.md`)의 쌍**으로 관리됩니다.
메타데이터 파일은 에이전트가 직접 편집하지 않고, `scripts/artifact.py`를 통해서만 갱신합니다.
문서 파일은 `scripts/artifact.py init`이 `assets/templates/`의 템플릿에서 기본 골격을 생성한 뒤 에이전트가 본문을 채웁니다.

```
<output-root>/
├── current-run.md                          # 현재 실행 상태 스냅샷 (사람이 읽는 뷰)
├── pipeline.meta.yaml                      # Orch 파이프라인 상태 메타데이터 (스크립트 전용)
└── runs/
    └── <run-id>/                           # 형식: YYYYMMDD-HHmmss-<4자리-해시>
        ├── run.meta.yaml                   # 실행 메타데이터, 파이프라인 상태 (스크립트 전용)
        ├── run.meta.md                     # run.meta.yaml의 사람 읽기용 렌더링
        ├── project-structure.md            # 프로젝트 구조 문서 (완료 시 생성)
        ├── release-note.md                 # 릴리스 노트 (완료 시 생성)
        ├── ex/
        │   ├── project_structure_map.meta.yaml
        │   ├── project_structure_map.md
        │   ├── technology_stack_detection.meta.yaml
        │   ├── technology_stack_detection.md
        │   ├── component_relationship_analysis.meta.yaml
        │   ├── component_relationship_analysis.md
        │   ├── architecture_inference.meta.yaml
        │   └── architecture_inference.md
        ├── re/
        │   ├── requirements_spec.md
        │   ├── constraints.md
        │   └── quality_attribute_priorities.md
        ├── arch/
        │   ├── architecture_decisions.md
        │   ├── component_structure.md
        │   ├── technology_stack.md
        │   └── diagrams.md
        ├── impl/
        │   ├── implementation_map.md
        │   ├── code_structure.md
        │   ├── implementation_decisions.md
        │   └── implementation_guide.md
        ├── qa/
        │   ├── test_strategy.md
        │   ├── test_suite.md
        │   ├── requirements_traceability_matrix.md
        │   └── quality_report.md
        ├── sec/
        │   ├── threat_model.md
        │   ├── vulnerability_report.md
        │   ├── security_recommendations.md
        │   └── compliance_status.md
        └── devops/
            ├── pipeline_config.md
            ├── infrastructure_code.md
            ├── observability_config.md
            └── operational_runbooks.md
```

> 위 트리는 `ex/`만 메타/문서 쌍을 명시적으로 보였습니다. 실제로는 모든 스킬 디렉토리(`re/`, `arch/`, `impl/`, `qa/`, `sec/`, `devops/`) 내 모든 산출물이 **`<name>.meta.yaml`과 `<name>.md`의 쌍**으로 생성됩니다.

---

## 메타데이터와 문서의 분리

산출물은 **구조화된 메타데이터 파일**과 **사람이 읽는 문서 파일**로 분리합니다. 이 분리가 Orch의 조율 기능의 근간이 됩니다.

### 왜 분리하는가

- **관심사 분리**: 상태/추적/승인 같은 기계가 소비하는 데이터와, 사람이 읽는 서술은 구조가 다릅니다. 한 파일에 섞으면 에이전트가 문서 본문을 수정할 때 상태 필드가 오염될 위험이 있습니다.
- **Orch의 관찰 대상**: Orch(특히 pipeline/dispatch 에이전트)는 각 하위 스킬의 산출물 **상태(phase)와 승인(approval)**을 기반으로 다음 스킬 트리거 여부를 결정합니다. 메타데이터가 고정된 위치에 있어야 이 관찰이 신뢰 가능해집니다.
- **파이프라인 상태 저장소로서의 메타데이터**: 각 하위 스킬의 `*.meta.yaml`이 모여 Orch가 읽어들이는 분산 상태 저장소 역할을 합니다. `run.meta.yaml`과 `pipeline.meta.yaml`이 이를 요약/인덱싱합니다.

### 왜 YAML인가 (JSON 아님)

| 기준 | YAML | JSON |
|------|------|------|
| 주석 지원 | 있음 (승인 근거, 상태 변경 이유 기재 가능) | 없음 |
| 사람 가독성 | 높음 (diff 리뷰 용이) | 보통 |
| 스크립트 파싱 | `PyYAML`로 1줄 (`yaml.safe_load`) | 표준 라이브러리 |
| 멀티라인 문자열 | 깔끔함 (`|`, `>`) | 이스케이프 지옥 |

→ **YAML 채택**. 산출물 메타데이터는 승인/상태 변경 이력에 주석을 남기는 것이 유용하고, 사람이 PR 리뷰에서 바로 읽을 수 있어야 하기 때문입니다.

### 산출물 메타데이터 스키마 (`<name>.meta.yaml`)

```yaml
# 예: runs/20260410-143022-a7f3/re/requirements_spec.meta.yaml
schema_version: 1
artifact:
  skill: re
  agent: spec
  name: requirements_spec
  run_id: 20260410-143022-a7f3
  doc_path: requirements_spec.md           # 쌍을 이루는 문서 파일 (상대 경로)
  created_at: 2026-04-10T14:35:13+09:00
  updated_at: 2026-04-10T14:36:45+09:00

progress:
  phase: drafting                          # pending | drafting | review | completed | failed
  progress_pct: 60                         # 0~100
  sections_total: 3
  sections_filled: 2
  last_transition: 2026-04-10T14:36:45+09:00

approval:
  state: pending                           # pending | approved | rejected | changes_requested
  approver: null                           # 사용자 식별자 또는 "user"
  approved_at: null
  comment: null
  history:
    - state: pending
      at: 2026-04-10T14:35:13+09:00
      by: system

traceability:
  upstream_refs:                           # 이 산출물이 소비한 업스트림 (추적성)
    - skill: re
      artifact: requirements_elicitation
      section_ids: [FR-001, FR-002, NFR-003]
  downstream_refs:                         # 하류에서 이 산출물을 참조한 경우 역으로 기록
    - skill: arch
      artifact: architecture_decisions
      section_ids: [AD-001]
```

### 문서 파일 (`<name>.md`)

- 서술형 본문만 포함 (섹션 헤더 + 플레이스홀더 + 에이전트가 채운 내용).
- 파일 상단에는 기존 `output-format.md` 규약대로 최소 메타 헤더만 유지(전체 상태는 `.meta.yaml`에 있음).
- `templates/<skill>/<name>.md`에서 골격을 복제하여 생성되며, 에이전트는 섹션 본문만 편집합니다.

### 스크립트를 통한 메타데이터 조작 (필수)

**에이전트는 `*.meta.yaml`을 직접 편집하지 않습니다.** 모든 상태 전이는 `scripts/artifact.py`를 거칩니다. 이는 스키마 검증, 타임스탬프 자동화, 승인 이력 append-only 보장을 위해 필요합니다.

`scripts/artifact.py` 주요 커맨드:

| 커맨드 | 역할 |
|--------|------|
| `artifact.py init --skill <s> --name <n> --run <id>` | `templates/`에서 문서 골격과 `.meta.yaml`을 함께 생성 |
| `artifact.py set-phase --path <meta> --phase <p>` | phase 전이 + 타임스탬프 자동 기록 |
| `artifact.py set-progress --path <meta> --pct <n> --filled <n>` | 진행률 갱신 |
| `artifact.py approve --path <meta> --approver <u> [--comment <c>]` | 승인 상태 기록 + history append |
| `artifact.py reject --path <meta> --approver <u> --comment <c>` | 거부 기록 |
| `artifact.py add-upstream --path <meta> --skill <s> --artifact <a> --sections <ids>` | 추적성 링크 추가 |
| `artifact.py get --path <meta> --field <dot.path>` | 필드 조회 (Orch가 상태 관찰에 사용) |
| `artifact.py query --run <id> --where phase=completed` | run 전체에서 조건 검색 (파이프라인 게이팅에 사용) |

`scripts/pipeline_state.py`는 Orch 자체의 파이프라인 상태(`pipeline.meta.yaml`, `run.meta.yaml`)를 관리합니다:

| 커맨드 | 역할 |
|--------|------|
| `pipeline_state.py init --run <id> --pipeline <name>` | `run.meta.yaml` 초기화 |
| `pipeline_state.py set-step --run <id> --step <idx> --status <s>` | 스킬 단계 상태 갱신 (running/completed/blocked) |
| `pipeline_state.py observe --run <id>` | 하위 스킬 `.meta.yaml`을 전부 스캔하여 phase/approval 요약 출력 (pipeline 에이전트의 게이팅 입력) |
| `pipeline_state.py next --run <id>` | 현재 상태 기준 다음 실행 가능 스킬 목록 반환 |
| `pipeline_state.py render --run <id>` | `run.meta.yaml` → `run.meta.md`와 `current-run.md`를 재생성 |

### Orch 관점: 메타데이터를 통한 관찰과 게이팅

Orch의 pipeline 에이전트는 각 스킬 완료 시 다음 순서로 동작합니다:

1. 스킬 에이전트가 `complete`를 반환.
2. run 에이전트가 산출물 문서 검증 후 `artifact.py set-phase --phase completed` 호출.
3. 필요 시 relay를 거쳐 사용자 승인 수집 → `artifact.py approve` 호출.
4. pipeline 에이전트가 `pipeline_state.py observe`로 전체 상태 요약 확인.
5. `pipeline_state.py next`로 다음 단계 결정(게이팅: 승인 필수 스킬이 pending이면 블록).
6. `pipeline_state.py render`로 사람이 읽는 `run.meta.md` / `current-run.md` 갱신.

이 흐름에서 **각 하위 스킬의 `.meta.yaml`은 Orch가 읽어들이는 분산 상태 저장소**로 기능하며, Orch 자체의 `pipeline.meta.yaml` / `run.meta.yaml`은 그 인덱스/요약본 역할을 합니다.

---

### `current-run.md` 스키마

실행 중인 run의 현재 상태 스냅샷입니다. `run.meta.md`가 상세 이력이라면, 이 파일은 현재 스냅샷에 집중합니다.
에이전트가 시작 시 이 파일 하나만 읽으면 현재 상황을 즉시 파악할 수 있습니다.

```markdown
# Current Run State

## Active Run
- run_id: 20260410-143022-a7f3
- pipeline: full-sdlc
- status: running
- current_step: arch:design
- current_step_status: dialogue
- last_updated: 2026-04-10T14:36:46+09:00

## Quick Context
- completed: [re:elicit, re:analyze, re:spec]
- pending: [impl:generate, qa:generate, sec:audit, devops:pipeline]
- user_action_needed: true
- last_question_summary: "기술 스택 선택 대기 중"
```

활성 run이 없으면 `status: idle`로 표시합니다:

```markdown
# Current Run State

## Active Run
- run_id: (none)
- status: idle
- last_completed_run: 20260410-143022-a7f3
- last_updated: 2026-04-10T15:20:00+09:00
```

### `run.meta.yaml` / `run.meta.md` 스키마

`run.meta.yaml`이 **정본(source of truth)**이며, 에이전트는 `pipeline_state.py`를 통해서만 갱신합니다.
`run.meta.md`는 이 YAML을 사람이 읽기 좋게 렌더링한 뷰로, `pipeline_state.py render`가 자동 생성합니다.

```yaml
# run.meta.yaml (정본)
schema_version: 1
run_id: 20260410-143022-a7f3
pipeline: full-sdlc
output_root: ./harness-output
created_at: 2026-04-10T14:30:22+09:00
status: running                            # pending | running | paused | completed | failed
steps:
  - index: 1
    skill: re
    agent: elicit
    status: completed                      # pending | running | dialogue | completed | failed
    approval: approved
    started_at: 2026-04-10T14:30:25+09:00
    completed_at: 2026-04-10T14:35:12+09:00
    artifacts: [re/requirements_elicitation]
  - index: 3
    skill: arch
    agent: design
    status: running
    approval: pending
    started_at: 2026-04-10T14:36:46+09:00
    completed_at: null
    artifacts: []
dialogue_history:
  - step: 1
    turns: 5
  - step: 3
    turns: 2
errors: []
```

렌더링된 `run.meta.md` 예시:

```markdown
# Run: <run-id>

## Configuration
- Pipeline: <파이프라인명>
- Output root: <산출물 루트 경로>
- Created: <ISO 8601 타임스탬프>
- Status: <pending | running | paused | completed | failed>

## Pipeline Status
| Step | Skill | Status | Started | Completed | Output |
|------|-------|--------|---------|-----------|--------|
| 1 | re:elicit | completed | 14:30:25 | 14:35:12 | re/ |
| 2 | re:spec | completed | 14:35:13 | 14:36:45 | re/ |
| 3 | arch:design | running | 14:36:46 | - | - |
| 4 | impl:generate | pending | - | - | - |
| 5 | [qa:generate, sec:audit, devops:pipeline] | pending | - | - | - |

## Dialogue History
- re:elicit: 5 turns
- arch:design: 2 turns (진행 중)

## Errors
- (없음)
```

스킬별 상태 값: `pending` | `running` | `dialogue` | `completed` | `failed`

---

## 에이전트 정의

### 1. `dispatch.md` — 디스패치 에이전트

- **역할**: 사용자의 유일한 진입점. 자연어 요청을 분석하여 스킬 또는 파이프라인으로 라우팅
- **핵심 역량**:
  - 자연어 의도 분석 및 스킬/에이전트 매핑
  - 복합 요청의 다중 스킬 분해 → 파이프라인 정의 생성
  - 선행 조건 검증 (예: arch:design 실행 전 RE 산출물 존재 여부 확인)
  - **기존 프로젝트 감지**: 사용자가 기존 코드베이스를 언급하거나 프로젝트 경로를 지정하면 ex 스킬을 파이프라인 선두에 배치
  - 기존 실행(run) 재개 요청 인식 및 라우팅
  - 컨텍스트 기반 라우팅 (현재 작업 단계 고려)
  - `current-run.md` 읽기를 통한 즉시 컨텍스트 파악 (run 디렉토리 스캔 불필요)
- **입력**:
  - SKILL.md `$ARGUMENTS` 치환값으로 받은 사용자 자연어 요청
  - SKILL.md 헤더의 `` !`cat harness-output/current-run.md` `` 동적 주입 결과 (harness가 매 호출마다 주입하므로 dispatch가 별도 파일 읽기를 할 필요 없음)
- **출력**: 파이프라인 정의 (스킬 목록 + 실행 순서 + 병렬 그룹) 또는 단일 스킬 호출 지시

### 2. `pipeline.md` — 파이프라인 에이전트

- **역할**: DAG 기반 워크플로 실행, 스킬 간 흐름 제어
- **핵심 역량**:
  - 순차 실행, 병렬 실행, 조건부 분기 지원
  - 각 스킬을 에이전트로 스폰하여 실행 (스폰 프로토콜 준수)
  - 대화형 스킬의 `needs_user_input` 신호 감지 → relay 에이전트에 위임
  - 자동 실행 스킬의 예외 에스컬레이션 처리
  - 스킬 완료 시 run 에이전트에 산출물 검증/저장 위임
  - 체크포인트 기록 및 재개 지원
  - 병렬 실행: 의존성 없는 스킬들을 동시에 에이전트 생성하여 병렬 처리
  - 파이프라인 완료 후 프로젝트 문서 생성 트리거
- **에이전트 스폰 프로토콜**:
  ```
  각 스킬 단계마다:
  1. 스킬 시스템 프롬프트 로드: ${CLAUDE_SKILL_DIR_<skill>}/SKILL.md 또는 references/agents/<agent>.md
  2. 기본 규칙 로드: ${CLAUDE_SKILL_DIR}/references/rules/base.md
  3. 산출물 형식 규칙 로드: ${CLAUDE_SKILL_DIR}/references/rules/output-format.md
  4. 산출물 골격 생성: scripts/artifact.py init으로 assets/templates/<skill>/ 기반
     문서 파일(.md)과 메타데이터 파일(.meta.yaml)을 함께 생성
  5. 업스트림 입력 조립: runs/<run-id>/<prev-skill>/*.md
     (각 스킬이 실제로 소비하는 섹션만 전달 — 전체 업스트림 아님)
  6. 전체 프롬프트 조립 = 기본 규칙 + 스킬 프롬프트 + 업스트림 데이터 + 출력 위치
     + "메타데이터는 scripts/artifact.py를 통해서만 갱신하라"는 지시
  7. Task 도구로 서브에이전트 스폰 (에이전트는 문서 .md만 편집)
     - 병렬 그룹의 경우 각 스킬을 독립 worktree에서 실행:
       EnterWorktree → 스폰 → ExitWorktree
  8. 에이전트 출력 수신
  9. needs_user_input 포함 시 → relay 에이전트에 위임
  10. complete 시 → run 에이전트가 검증 후 artifact.py set-phase로 상태 전이
  11. pipeline_state.py observe로 다음 단계 게이팅 판단
  ```
- **병렬 실행 worktree 격리**:
  - `[qa:generate, sec:audit, devops:pipeline]`와 같은 병렬 그룹의 스킬들은 동일 레포를 동시에 수정할 수 있어 충돌 위험이 있습니다.
  - 표준 `/batch` 스킬 패턴을 차용하여, 각 병렬 스킬은 `EnterWorktree`로 독립된 git worktree에 진입 후 작업을 수행하고 완료 시 `ExitWorktree`로 정리합니다.
  - 병렬 그룹 전원이 완료된 후 pipeline 에이전트가 산출물을 메인 worktree로 수집/머지합니다.
  - `allowed-tools`에 `EnterWorktree` / `ExitWorktree`가 이 목적으로 선언되어 있습니다.
- **사전 정의 파이프라인**:
  - `full-sdlc`: re:elicit → re:analyze → re:spec → arch:design → impl:generate → [qa:generate, sec:audit, devops:pipeline] (병렬)
  - `full-sdlc-existing`: ex:scan → ex:detect → ex:analyze → ex:map → re:elicit → re:analyze → re:spec → arch:design → impl:generate → [qa:generate, sec:audit, devops:pipeline] (병렬)
  - `new-feature`: re:elicit → re:spec → arch:design → impl:generate → qa:generate
  - `new-feature-existing`: ex:scan → ex:detect → ex:analyze → ex:map → re:elicit → re:spec → arch:design → impl:generate → qa:generate
  - `security-gate`: sec:threat-model → sec:audit → sec:compliance
  - `security-gate-existing`: ex:scan → ex:detect → ex:analyze → ex:map → sec:threat-model → sec:audit → sec:compliance
  - `quick-review`: re:review → arch:review → impl:review
  - `explore`: ex:scan → ex:detect → ex:analyze → ex:map
- **입력**: 파이프라인 정의 (dispatch 출력), run-id, 산출물 경로
- **출력**: 각 스킬 실행 결과 집계, 전체 워크플로 요약

### 3. `relay.md` — 릴레이 에이전트 (신규)

- **역할**: 실행 중인 스킬 에이전트와 사용자 간의 멀티턴 대화 중계
- **핵심 역량**:
  - 스킬 에이전트의 구조화된 질문(`needs_user_input`)을 사람이 읽기 좋은 형태로 변환
  - 사용자 응답 수집 및 대화 컨텍스트와 함께 패키징
  - 패키징된 응답을 스킬 에이전트에 재전달
  - 대화 이력 관리 (요약 유지 — 전체 원본이 아닌 요약본 전달)
  - 사용자의 "건너뛰기" 또는 "기본값 수용" 의사 인식
  - 자동 실행 스킬의 예외 에스컬레이션도 동일하게 처리
- **대화 프로토콜**:

  **스킬 에이전트 → orchestration**:
  ```markdown
  ## needs_user_input
  - skill: "re:elicit"
  - turn: 3
  - questions:
    - id: "q1"
      text: "예상 동시 접속자 수는 얼마인가요?"
      context: "확장성 관련 아키텍처 결정에 영향을 줍니다."
      type: open          # open | choice | confirmation
    - id: "q2"
      text: "인증 방식을 선택해주세요."
      type: choice
      options: ["OAuth 2.0", "JWT", "세션 기반"]
  - partial_output: { ... }
  ```

  **orchestration → 스킬 에이전트**:
  ```markdown
  ## user_response
  - skill: "re:elicit"
  - turn: 3
  - answers:
    - question_id: "q1"
      response: "피크 시 약 10,000명"
    - question_id: "q2"
      response: "OAuth 2.0"
  - conversation_summary: "... (이전 대화 요약) ..."
  ```

- **입력**: 스킬 에이전트의 `needs_user_input` 신호
- **출력**: 사용자 응답이 포함된 `user_response` 패키지

### 4. `run.md` — 실행 관리 에이전트 (신규)

- **역할**: 실행(run) 생명주기 관리, 산출물 디렉토리 생성/관리, 상태 추적, 재개 지원
- **핵심 역량**:
  - **초기화**: run-id 생성, `<output-root>/runs/<run-id>/` 디렉토리 구조 생성, `scripts/pipeline_state.py init`으로 `run.meta.yaml` 생성, render로 `run.meta.md`/`current-run.md` 갱신
  - **산출물 골격 생성**: 스킬 실행 전 `scripts/artifact.py init`을 호출하여 `templates/<skill>/`의 문서 골격과 `.meta.yaml`을 함께 생성
  - **산출물 저장 위치**: 사용자 설정에서 출력 루트 경로 읽기 (기본: `./harness-output/`)
  - **산출물 검증**: 스킬 완료 시 필수 섹션 존재 여부 검증 (EX=4개, RE=3개, ARCH=4개, IMPL=4개, QA=4개, SEC=4개, DEVOPS=4개)
  - **상태 전이 (스크립트 경유)**: `artifact.py set-phase`, `set-progress`, `approve` 등을 호출해서만 `.meta.yaml`을 갱신 — YAML을 직접 편집하지 않음
  - **상태 추적**: `pipeline_state.py set-step`으로 `run.meta.yaml`에 단계 상태 반영, `pipeline_state.py render`로 `run.meta.md` / `current-run.md` 동기화
  - **재개(resume)**: `current-run.md`로 활성 run 즉시 확인 → `pipeline_state.py observe`로 `run.meta.yaml` + 하위 `.meta.yaml` 전체 스캔 → 중단 지점부터 재실행
  - **완료 문서 생성**: 파이프라인 완료 후 `project-structure.md`와 `release-note.md` 생성
  - **완료 시 정리**: `current-run.md`를 `status: idle`로 갱신, `last_completed_run` 기록
- **실행 생명주기**:
  ```
  INIT → CONFIGURE → EXECUTE → COLLECT → REPORT → CLEANUP
    │        │           │         │         │         │
    │        │           │         │         │         └─ current-run.md → idle 상태로 갱신
    │        │           │         │         └─ 프로젝트 구조/릴리스 노트 생성 + 최종 요약
    │        │           │         └─ 산출물 검증 + 저장
    │        │           └─ 스킬 실행 (대화 릴레이 포함) + 매 단계 current-run.md 동기화
    │        └─ 파이프라인 결정, 출력 디렉토리 설정, 규칙 로드
    └─ run 디렉토리 생성, run-id 발급, 메타데이터 기록, current-run.md 갱신
  ```
- **입력**: 파이프라인 정의, 출력 설정
- **출력**: run 디렉토리 경로, 상태 업데이트, 완료 보고

### 5. `config.md` — 설정 관리 에이전트

- **역할**: 스킬 설정, 에이전트 규칙, 파이프라인 템플릿 관리
- **핵심 역량**:
  - 설치된 스킬의 활성화/비활성화 관리
  - 스킬별 설정값 조회 및 수정
  - 에이전트 우선순위 및 기본값 관리
  - 산출물 출력 루트 경로 설정
  - 파이프라인 템플릿 관리 (사전 정의 + 사용자 정의)
  - 설정 검증 및 충돌 탐지
  - 프로필 기반 설정 (프로젝트 유형별 사전 설정)
- **입력**: 설정 변경 요청
- **출력**: 설정 변경 결과, 현재 설정 상태

### 6. `status.md` — 현황 조회 에이전트

- **역할**: 실행 이력 조회, 스킬 상태 확인, 산출물 검색
- **핵심 역량**:
  - 설치된 스킬 및 에이전트 목록 조회
  - 각 스킬의 버전 및 상태 확인
  - 실행(run) 이력 및 결과 요약
  - 특정 run의 산출물 내용 조회
  - 스킬 간 의존성 그래프 시각화
  - 사용 통계 및 추천
- **입력**: 조회 조건 (스킬명, run-id, 기간, 상태)
- **출력**: 현황 리포트 (스킬 목록, 상태, 실행 이력, 통계)

---

## 규칙 체계 (`rules/`)

모든 스폰되는 에이전트에 주입되는 행동 규칙입니다.

### `base.md` — 기본 규칙

모든 에이전트에 공통 적용:
- orchestration 실행 내에서 동작하며, 지정된 산출물 형식을 정확히 따름
- 입력 데이터로 해결 불가능한 모호성 발견 시 `needs_user_input` 신호로 에스컬레이션
- 지정된 섹션 외의 산출물 생성 금지
- 업스트림 산출물의 ID를 참조하여 추적성 유지 (예: `FR-001`, `AD-001`)
- 각 산출물 파일에 메타데이터 헤더 포함 (skill, agent, run-id, timestamp)

### `output-format.md` — 산출물 형식 규약

- 모든 산출물은 Markdown(.md) 파일
- 각 섹션은 독립된 파일로 저장
- 스킬의 PLAN.md에 정의된 필드 테이블을 스키마로 사용
- 파일 상단에 메타데이터 블록 포함:
  ```markdown
  ---
  skill: re
  agent: elicit
  run_id: 20260410-143022-a7f3
  timestamp: 2026-04-10T14:35:12+09:00
  upstream_refs: []
  ---
  ```

### `escalation-protocol.md` — 에스컬레이션 규약

- **대화형 스킬** (re:elicit, re:analyze, re:spec, re:review, arch:design, sec:threat-model): 의미 있는 질문 묶음마다 `needs_user_input` 사용
- **자동 실행 스킬** (ex:*, impl:*, qa:*, sec:audit, sec:review, sec:compliance, devops:*): 예외 조건에서만 `needs_user_input` 사용 (예: 아키텍처 결정이 코드로 실현 불가능한 경우, 프로젝트 루트 접근 불가 등)
- 모든 에스컬레이션에 포함: 질문 텍스트, 맥락(왜 중요한지), 유형(open/choice/confirmation)

### `dialogue-protocol.md` — 대화 프로토콜

`needs_user_input` / `user_response` 신호의 정확한 구조를 정의합니다.
(상세 형식은 relay 에이전트 섹션 참조)

---

## 사전 정의 파이프라인 (`pipelines/`)

각 파이프라인은 독립 파일로 정의되어 pipeline 에이전트가 참조합니다.

### `full-sdlc.md` — 전체 SDLC 파이프라인

```
re:elicit → re:analyze → re:spec → arch:design → impl:generate → [qa:generate, sec:audit, devops:pipeline]
```
- 마지막 3개 스킬은 impl 완료 후 병렬 실행
- 모든 스킬 완료 후 프로젝트 구조 문서 + 릴리스 노트 생성

### `full-sdlc-existing.md` — 기존 프로젝트 전체 SDLC 파이프라인

```
ex:scan → ex:detect → ex:analyze → ex:map → re:elicit → re:analyze → re:spec → arch:design → impl:generate → [qa:generate, sec:audit, devops:pipeline]
```
- ex 4단계가 자동 실행으로 기존 코드베이스 컨텍스트 추출
- ex 산출물이 re:elicit에 업스트림 입력으로 주입되어 기존 시스템 맥락 반영
- 이후 흐름은 full-sdlc와 동일

### `new-feature.md` — 신규 기능 개발 파이프라인

```
re:elicit → re:spec → arch:design → impl:generate → qa:generate
```

### `new-feature-existing.md` — 기존 프로젝트 신규 기능 개발 파이프라인

```
ex:scan → ex:detect → ex:analyze → ex:map → re:elicit → re:spec → arch:design → impl:generate → qa:generate
```
- ex가 기존 코드 구조/기술 스택/컴포넌트 관계를 추출하여 후속 스킬에 컨텍스트 제공
- arch:design이 기존 아키텍처 제약을 전제로 설계

### `security-gate.md` — 보안 게이트 파이프라인

```
sec:threat-model → sec:audit → sec:compliance
```

### `security-gate-existing.md` — 기존 프로젝트 보안 게이트 파이프라인

```
ex:scan → ex:detect → ex:analyze → ex:map → sec:threat-model → sec:audit → sec:compliance
```
- ex가 컴포넌트/API 표면을 추출하여 sec:threat-model의 공격 표면 식별에 활용

### `quick-review.md` — 빠른 리뷰 파이프라인

```
re:review → arch:review → impl:review
```

### `explore.md` — 코드베이스 탐색 파이프라인

```
ex:scan → ex:detect → ex:analyze → ex:map
```
- ex 스킬만 단독 실행하여 기존 프로젝트의 구조화된 컨텍스트 맵 생성
- 후속 스킬 연계 없이 코드베이스 이해 목적으로 사용

---

## 완료 시 문서 생성

파이프라인의 모든 스킬이 완료되면, pipeline 에이전트가 마지막 단계로 다음 문서를 생성합니다:

### `project-structure.md` — 프로젝트 구조 문서

타겟 프로젝트의 전체적인 구조를 사람이 파악할 수 있도록 정리:
- 전체 디렉토리 구조 및 각 모듈/컴포넌트의 역할 설명
- 기술 스택 요약 (ex 또는 arch 산출물 기반)
- 의존성 관계도 (컴포넌트 간, 외부 라이브러리)
- 기존 코드베이스 컨텍스트 (ex 산출물이 있는 경우 — 기존 구조와 신규 변경 사항 대비)
- 설정/빌드/실행 가이드 (impl 산출물 기반)

### `release-note.md` — 릴리스 노트

해당 실행의 작업 내역을 사람이 읽을 수 있는 형태로 정리:
- 실행된 스킬 및 각 스킬의 주요 결정 사항 요약
- 요구사항 → 아키텍처 → 구현 간 핵심 추적성 요약
- 품질/보안 검증 결과 요약 (qa, sec 산출물 기반)
- 인프라/배포 구성 요약 (devops 산출물 기반)
- 알려진 제한사항 및 후속 작업 제안

두 문서 모두 `runs/<run-id>/` 루트에 생성됩니다.

---

## 실행 흐름 예시

### 전체 SDLC 파이프라인 (대화 포함)

```
사용자: "실시간 채팅 애플리케이션을 만들고 싶어"

1. DISPATCH: 의도 분석
   → 새 시스템 개발 → full-sdlc 파이프라인 선택
   → 출력: pipeline = [re:elicit, re:analyze, re:spec, arch:design, impl:generate, [qa:generate, sec:audit, devops:pipeline]]

2. RUN: 초기화
   → ./harness-output/runs/20260410-143022-a7f3/ 생성
   → run.meta.md 작성
   → current-run.md 갱신 (status: running, current_step: re:elicit)

3. PIPELINE: 실행 시작

   [Step 1] re:elicit (대화형)
   → 에이전트 스폰: base.md + re/agents/elicit.md + 사용자 요청
   → 에이전트 반환: needs_user_input (플랫폼? 사용자 수? ...)
   → RELAY: 사용자에게 질문 전달
   → 사용자: "웹과 모바일, 약 1만 명"
   → RELAY: 응답 패키징 → 에이전트에 재전달
   → ... (반복) ...
   → 에이전트 반환: complete (3개 섹션)
   → RUN: 검증 + runs/<id>/re/ 에 저장

   [Step 2] re:analyze (대화형, 유사 패턴)

   [Step 3] re:spec (대화형, 초안 확인)

   [Step 4] arch:design (대화형)
   → 에이전트 스폰: base.md + arch/agents/design.md + RE 산출물(runs/<id>/re/*.md)
   → 기술 컨텍스트 질문 → relay → 사용자 → relay → 에이전트
   → 완료: 4개 섹션 → RUN 검증/저장

   [Step 5] impl:generate (자동 실행)
   → 에이전트 스폰: base.md + impl/agents/generate.md + Arch 산출물(runs/<id>/arch/*.md)
   → 사용자 개입 없이 완료 (예외 시에만 relay)
   → 4개 섹션 → RUN 검증/저장

   [Step 6] 병렬 실행: qa:generate + sec:audit + devops:pipeline
   → 3개 에이전트 동시 스폰
   → 각각 독립적으로 완료 → RUN 검증/저장

   [Step 7] 완료 문서 생성
   → project-structure.md + release-note.md 생성

   [Step 8] 정리
   → current-run.md 갱신 (status: idle, last_completed_run: 20260410-143022-a7f3)

4. PIPELINE: 최종 요약을 사용자에게 보고
```

### 기존 프로젝트에 기능 추가 (ex 선행)

```
사용자: "~/projects/my-app 에 실시간 알림 기능을 추가하고 싶어"

1. DISPATCH: 의도 분석
   → 기존 프로젝트 경로 감지 (~/projects/my-app)
   → 기존 프로젝트 + 기능 추가 → new-feature-existing 파이프라인 선택
   → 출력: pipeline = [ex:scan, ex:detect, ex:analyze, ex:map, re:elicit, re:spec, arch:design, impl:generate, qa:generate]

2. RUN: 초기화
   → ./harness-output/runs/20260410-160000-b2c4/ 생성
   → run.meta.md 작성
   → current-run.md 갱신 (status: running, current_step: ex:scan)

3. PIPELINE: 실행 시작

   [Step 1~4] ex:scan → ex:detect → ex:analyze → ex:map (자동 실행)
   → 4단계 순차 실행, 사용자 개입 없음
   → ex:scan: 디렉토리 스캔 + 복잡도 판별 (중량 모드)
   → ex:detect: 기술 스택 탐지 (Next.js + Prisma + PostgreSQL)
   → ex:analyze: 컴포넌트 관계 + 아키텍처 추론 (layered)
   → ex:map: 4섹션 통합 산출물 생성 (토큰 예산 내)
   → RUN: 검증 + runs/<id>/ex/ 에 4개 파일 저장

   [Step 5] re:elicit (대화형)
   → 에이전트 스폰: base.md + re/agents/elicit.md + ex 산출물(runs/<id>/ex/*.md)
   → ex 산출물로 기존 시스템 맥락이 주입된 상태에서 요구사항 도출
   → "기존 Next.js + Prisma 구조에서 실시간 알림을 어떤 방식으로 구현할까요? WebSocket? SSE?"
   → ... (대화 진행) ...

   [Step 6~9] re:spec → arch:design → impl:generate → qa:generate
   → 이후 흐름은 new-feature와 동일 (단, 모든 스킬이 ex 산출물을 참조 가능)
```

### 코드베이스 탐색 (ex 단독)

```
사용자: "~/projects/legacy-api 코드 좀 분석해줘"

1. DISPATCH: 의도 분석
   → 기존 프로젝트 분석 요청 → explore 파이프라인 선택
   → 출력: pipeline = [ex:scan, ex:detect, ex:analyze, ex:map]

2. RUN: 초기화 + PIPELINE: 자동 실행
   → ex 4단계 자동 실행 → 4섹션 산출물 생성
   → 사용자에게 프로젝트 구조 맵, 기술 스택, 컴포넌트 관계, 아키텍처 추론 결과 보고
```

### 실행 재개

```
사용자: "아까 중단된 실행 이어서 해줘"

1. DISPATCH: 재개 요청 인식
   → current-run.md 읽기 → 활성 run-id 즉시 확인 (디렉토리 스캔 불필요)
   → pipeline 에이전트에 재개 모드로 전달

2. PIPELINE: run.meta.md 로드 (current-run.md에서 확인한 run-id 사용)
   → completed 스킬(re:elicit, re:spec) 건너뜀
   → arch:design (dialogue 상태)부터 재실행
   → 이전 산출물은 runs/<id>/ 에서 로드하여 활용
   → current-run.md 갱신 (status: running, current_step: arch:design)
```

---

## 핵심 설계 원칙

1. **단일 진입점**: 사용자는 항상 orchestration을 통해 통신. 개별 스킬 직접 호출 없음
2. **에이전트 기반 실행**: 모든 스킬은 Agent 도구를 통해 에이전트로 스폰되어 실행
3. **실행 격리**: 각 run은 독립된 디렉토리에 산출물 저장. 반복 사용 시 충돌 없음
4. **느슨한 결합**: 각 스킬은 독립적으로 동작 가능하며, orchestration은 조율 역할
5. **자기 기술적 (Self-describing)**: 각 스킬이 자신의 입출력을 명세하여 자동 연결 가능
6. **점진적 복잡성**: 단일 스킬 호출부터 복잡한 파이프라인까지 단계적 사용 가능
7. **관찰 가능성**: 모든 스킬 실행 과정이 `run.meta.md`에 기록되어 추적/디버깅 가능
8. **사용자 개입 중계**: 대화형 스킬의 질문과 자동 실행 스킬의 예외를 통일된 relay 메커니즘으로 전달
9. **재개 가능성**: `current-run.md`를 통해 활성 run을 즉시 식별하고, 중단된 실행을 상태 기반으로 재개 가능
10. **빠른 컨텍스트 복원**: `current-run.md` 단일 파일로 현재 실행 상태를 즉시 파악 — 디렉토리 스캔 불필요
11. **메타데이터-문서 분리 및 스크립트 경유 갱신**: 모든 산출물은 `<name>.meta.yaml`(상태/승인/추적성)과 `<name>.md`(서술)로 분리. 에이전트는 문서만 편집하고 메타데이터는 `scripts/artifact.py` / `scripts/pipeline_state.py`를 통해서만 갱신. 이 계층이 Orch가 하위 스킬 상태를 관찰하고 파이프라인을 게이팅·라우팅하는 기반이 됨

---

## 구현 단계

### 1단계: 규칙 체계 (`references/rules/`)

- `base.md`: 모든 에이전트 공통 행동 규칙 (메타데이터 직접 편집 금지 조항 포함)
- `output-format.md`: 산출물 Markdown 형식 계약 + `.meta.yaml` / `.md` 분리 규약
- `escalation-protocol.md`: 에스컬레이션 조건 및 방법
- `dialogue-protocol.md`: `needs_user_input` / `user_response` 신호 형식

### 2단계: 메타데이터 스키마, 템플릿, 스크립트

이 단계가 이후 모든 단계의 전제이므로 에이전트 구현보다 앞섭니다.

- `assets/templates/artifact.meta.yaml`: 산출물 메타데이터 템플릿 (phase, approval, traceability)
- `assets/templates/pipeline.meta.yaml`: Orch 파이프라인 상태 메타데이터 템플릿
- `assets/templates/run.meta.md`, `assets/templates/current-run.md`: 사람 읽기용 렌더링 초기 템플릿
- `assets/templates/<skill>/*.md`: 각 스킬 산출물 문서 골격 템플릿 (섹션 헤더 + 플레이스홀더)
- `references/schemas/artifact-meta.md`, `references/schemas/pipeline-meta.md`: 스키마 설명 문서
- `scripts/lib/meta_io.py`: YAML 로드/저장 + 스키마 검증
- `scripts/lib/refs.py`: upstream/downstream 추적성 링크 해석
- `scripts/artifact.py`: `init` / `set-phase` / `set-progress` / `approve` / `reject` / `add-upstream` / `get` / `query`
- `scripts/pipeline_state.py`: `init` / `set-step` / `observe` / `next` / `render`

### 3단계: `SKILL.md` 엔트리 포인트 작성

- `orch/SKILL.md`를 신설하고 앞 절의 frontmatter YAML 적용
- 본문 상단에 `$ARGUMENTS` + `` !`cat harness-output/current-run.md` `` 주입 헤더 배치
- 본문은 500줄 이내로 유지하고, 상세 설계는 `references/` 하위 파일에 대한 링크로 대체
- `${CLAUDE_SKILL_DIR}` 기반으로 모든 내부 경로 참조

### 4단계: 핵심 서브에이전트 프롬프트 (`references/agents/`)

SKILL.md가 `Task` 도구로 스폰할 때 사용하는 프롬프트 템플릿입니다.

- `run.md`: 실행 생명주기, 디렉토리 생성, `artifact.py init` 호출, 검증, `set-phase` 전이
- `relay.md`: 사용자 대화 중계, 승인 응답을 `artifact.py approve`로 전달
- `pipeline.md`: DAG 실행, 에이전트 스폰, `pipeline_state.py observe/next` 기반 게이팅, 병렬 실행, worktree 격리(`EnterWorktree`/`ExitWorktree`)
- `dispatch.md`: 의도 분석, 라우팅, harness가 주입한 `current-run.md` 스냅샷 활용

### 5단계: 설정 및 현황 서브에이전트

- `references/agents/config.md`: 설정 관리 (출력 경로, 스킬 활성화, 파이프라인 템플릿)
- `references/agents/status.md`: 실행 이력 및 현황 조회 (`artifact.py query`, `pipeline_state.py observe` 활용)

### 6단계: 파이프라인 템플릿 (`references/pipelines/`)

- `full-sdlc.md`, `full-sdlc-existing.md`, `new-feature.md`, `new-feature-existing.md`, `security-gate.md`, `security-gate-existing.md`, `quick-review.md`, `explore.md`

### 7단계: 예시 및 스킬 레지스트리

- `examples/`: 전체 실행, 대화 릴레이, 에스컬레이션, 재개 예시, **메타데이터/문서 파일 쌍 예시** (`artifact-meta-example.yaml` + `artifact-doc-example.md`), `pipeline-meta-example.yaml`
- `skills.yaml`: 스킬 이름, 버전, 설명, 서브에이전트 목록, 의존 하위 스킬 목록, 파이프라인 실행 엔진 설정, 라우팅 규칙 설정 스키마

### 8단계: Hooks 연동

- `hooks.post-complete`에 `scripts/pipeline_state.py render --run "$RUN_ID"`를 등록하여 파이프라인 완료 시 `run.meta.md` / `current-run.md` 자동 갱신
- 추후 `project-structure.md` / `release-note.md` 생성도 post-hook으로 이관 검토
