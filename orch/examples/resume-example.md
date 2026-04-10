# 실행 재개 예시

## 시나리오

사용자가 이전에 중단된 full-sdlc 실행을 재개합니다. arch:design 단계에서 대화 중에 중단되었습니다.

---

## 중단 시점의 상태

### current-run.md

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

### run.meta.md

```markdown
# Run: 20260410-143022-a7f3

## Configuration
- Pipeline: full-sdlc
- Output root: ./harness-output/
- Created: 2026-04-10T14:30:22+09:00
- Status: running

## Pipeline Status
| Step | Skill | Status | Started | Completed | Output |
|------|-------|--------|---------|-----------|--------|
| 1 | re:elicit | completed | 14:30:25 | 14:32:12 | re/ |
| 2 | re:analyze | completed | 14:32:13 | 14:34:05 | re/ |
| 3 | re:spec | completed | 14:34:06 | 14:36:45 | re/ |
| 4 | arch:design | dialogue | 14:36:46 | - | - |
| 5 | impl:generate | pending | - | - | - |
| 6 | [qa, sec, devops] | pending | - | - | - |

## Dialogue History
- re:elicit: 3 turns
- re:analyze: 2 turns
- re:spec: 1 turn
- arch:design: 1 turn (진행 중 — 기술 스택 선택 대기)

## Errors
- (없음)
```

---

## 재개 흐름

### 1. 사용자 요청

```
"아까 중단된 실행 이어서 해줘"
```

### 2. DISPATCH: 재개 요청 인식

```markdown
## dispatch_result
- action: resume
- run_id: "20260410-143022-a7f3"
- resume_from: "arch:design"
```

판단 근거:
- "아까 중단된", "이어서" → 재개 요청 인식
- `current-run.md` 읽기 → `run_id: 20260410-143022-a7f3`, `status: running`
- `current_step: arch:design`, `current_step_status: dialogue`

### 3. RUN: 재개 정보 로드

```markdown
## resume_info
- run_id: 20260410-143022-a7f3
- pipeline: full-sdlc
- resume_from: arch:design
- resume_status: dialogue
- completed_skills: [re:elicit, re:analyze, re:spec]
- available_outputs:
    - re/requirements_spec.md
    - re/constraints.md
    - re/quality_attribute_priorities.md
- dialogue_context: "arch:design turn 1 — 기술 스택 선택 대기 중"
```

### 4. PIPELINE: 재개 모드 실행

**건너뛰는 스킬**: re:elicit, re:analyze, re:spec (completed)

**재개 지점**: arch:design (dialogue 상태)

에이전트 스폰:
- 시스템 프롬프트: `arch/agents/design.md`
- 규칙: `orch/rules/base.md` + `orch/rules/output-format.md`
- 업스트림: `runs/<id>/re/*.md` (이전 산출물 로드)
- 대화 컨텍스트: 이전 대화 요약 포함

### 5. current-run.md 갱신

```markdown
# Current Run State

## Active Run
- run_id: 20260410-143022-a7f3
- pipeline: full-sdlc
- status: running
- current_step: arch:design
- current_step_status: dialogue
- last_updated: 2026-04-10T16:00:05+09:00

## Quick Context
- completed: [re:elicit, re:analyze, re:spec]
- pending: [impl:generate, qa:generate, sec:audit, devops:pipeline]
- user_action_needed: true
- last_question_summary: "기술 스택 선택 대기 중 (재개됨)"
```

### 6. 이후 흐름

arch:design의 대화가 이전 턴에서 이어서 진행됩니다. 에이전트는 이전 대화 요약과 업스트림 산출물을 기반으로 맥락을 복원하고, 사용자에게 기술 스택 선택 질문을 다시 제시합니다.

## 핵심 포인트

1. **current-run.md로 즉시 식별** — 디렉토리 스캔 없이 활성 run을 바로 파악
2. **완료된 스킬 건너뜀** — re 관련 3단계를 재실행하지 않음
3. **대화 컨텍스트 복원** — 이전 대화 요약을 에이전트에 전달하여 맥락 유지
4. **기존 산출물 재활용** — runs/<id>/re/ 의 산출물을 업스트림으로 활용
