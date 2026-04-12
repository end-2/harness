# Example: Full SDLC Pipeline — New Project

Demonstrates a complete `full-sdlc` pipeline execution from natural-language request to completion.

## User request

```
"I want to build a task management API with user authentication, project boards, 
and real-time notifications. It should handle 10K concurrent users."
```

## Stage 1: Dispatch

Dispatch analyses the request:
- Multiple skills needed (re, arch, impl, qa, sec, devops, verify)
- No existing codebase detected
- Matches `full-sdlc` pipeline

```bash
python ${SKILL_DIR}/scripts/run.py init-run --pipeline full-sdlc
```

Output:
```json
{
  "run_id": "20260412-103000-a1b2",
  "run_dir": "harness-output/runs/20260412-103000-a1b2",
  "pipeline": "full-sdlc"
}
```

## Stage 2: Pipeline execution

### Step 0: re:elicit

```bash
python ${SKILL_DIR}/scripts/run.py update-state --run 20260412-103000-a1b2 --step 0 --status running
```

The RE skill enters dialogue mode. Multiple relay rounds:

- Turn 1: "What types of tasks? Simple to-do items or complex with subtasks, dependencies?"
  - User: "Complex tasks with subtasks, assignees, due dates, and labels"
- Turn 2: "What does real-time mean — WebSocket push, SSE, or polling?"
  - User: "WebSocket for active users, email digest for inactive"
- Turn 3: "Authentication — social login, SSO, or email/password?"
  - User: "Email/password plus Google OAuth"

RE produces: RE-REQ-001 (requirements), RE-CON-001 (constraints), RE-QA-001 (quality attributes)

```bash
python ${SKILL_DIR}/scripts/run.py update-state --run 20260412-103000-a1b2 --step 0 --status completed
```

### Steps 1-2: re:analyze, re:spec (similar flow)

### Step 3: arch:design

Architecture skill reads RE artifacts and enters dialogue:

- Turn 1: "Your team size and technology preferences?"
  - User: "4 devs, all comfortable with Node.js/TypeScript. Some Go experience."
- Turn 2: "I recommend a modular monolith with TypeScript. The 10K concurrency target is achievable without microservices at this team size. Approve?"
  - User: "Yes, sounds right"

Produces: ARCH-DEC-001, ARCH-COMP-001, ARCH-TECH-001, ARCH-DIAG-001

### Step 4: impl:generate (automatic)

### Steps 5-7: qa + sec + devops (parallel)

All three run simultaneously in isolated worktrees:
```
EnterWorktree → qa:generate → ExitWorktree
EnterWorktree → sec:audit → ExitWorktree
EnterWorktree → devops:pipeline → ExitWorktree
```

### Steps 8-9: verify

Automatic environment setup and test execution.

## Completion

```bash
python ${SKILL_DIR}/scripts/run.py complete --run 20260412-103000-a1b2
```

### current-run.md (during execution)

```markdown
# Active Run: 20260412-103000-a1b2

- **Pipeline**: full-sdlc
- **Status**: running
- **Created**: 2026-04-12T10:30:00Z

## Steps

| # | Skill | Agent | Status |
|---|-------|-------|--------|
| 0 | re | elicit | done completed |
| 1 | re | analyze | done completed |
| 2 | re | spec | done completed |
| 3 | arch | design | >> running |
| 4 | impl | generate | ... pending |
| 5 | qa | generate | ... pending |
| 6 | sec | audit | ... pending |
| 7 | devops | pipeline | ... pending |
| 8 | verify | provision | ... pending |
| 9 | verify | execute | ... pending |
```

### current-run.md (after completion)

```
status: idle — no active run

Last completed run: 20260412-103000-a1b2
Completed at: 2026-04-12T11:15:00Z
```

### run.meta.yaml (final state)

```yaml
run_id: "20260412-103000-a1b2"
pipeline: full-sdlc
output_root: "./harness-output/"
status: completed
created_at: "2026-04-12T10:30:00Z"
updated_at: "2026-04-12T11:15:00Z"
ended_at: "2026-04-12T11:15:00Z"
steps:
  - {index: 0, skill: re, agent: elicit, status: completed, artifacts: [RE-REQ-001, RE-CON-001, RE-QA-001]}
  - {index: 1, skill: re, agent: analyze, status: completed, artifacts: [RE-REQ-001, RE-CON-001, RE-QA-001]}
  - {index: 2, skill: re, agent: spec, status: completed, artifacts: [RE-REQ-001, RE-CON-001, RE-QA-001]}
  - {index: 3, skill: arch, agent: design, status: completed, artifacts: [ARCH-DEC-001, ARCH-COMP-001, ARCH-TECH-001, ARCH-DIAG-001]}
  - {index: 4, skill: impl, agent: generate, status: completed, artifacts: [IMPL-MAP-001, IMPL-CODE-001, IMPL-IDR-001, IMPL-GUIDE-001]}
  - {index: 5, skill: qa, agent: generate, status: completed, parallel_group: post-impl, artifacts: [QA-STR-001, QA-TST-001, QA-TRC-001, QA-RPT-001]}
  - {index: 6, skill: sec, agent: audit, status: completed, parallel_group: post-impl, artifacts: [SEC-TM-001, SEC-VUL-001, SEC-REC-001, SEC-CPL-001]}
  - {index: 7, skill: devops, agent: pipeline, status: completed, parallel_group: post-impl, artifacts: [DEVOPS-PL-001, DEVOPS-IAC-001, DEVOPS-OBS-001, DEVOPS-RB-001]}
  - {index: 8, skill: verify, agent: provision, status: completed, artifacts: [VERIFY-ENV-001]}
  - {index: 9, skill: verify, agent: execute, status: completed, artifacts: [VERIFY-SC-001, VERIFY-RPT-001]}
dialogue_history:
  - {step_index: 0, skill: re, agent: elicit, turn: 1, summary: "Complex tasks with subtasks, assignees, due dates, labels"}
  - {step_index: 0, skill: re, agent: elicit, turn: 2, summary: "WebSocket for active, email digest for inactive"}
  - {step_index: 0, skill: re, agent: elicit, turn: 3, summary: "Email/password + Google OAuth"}
  - {step_index: 3, skill: arch, agent: design, turn: 1, summary: "4 devs, Node.js/TypeScript comfortable, some Go"}
  - {step_index: 3, skill: arch, agent: design, turn: 2, summary: "Approved modular monolith with TypeScript"}
errors: []
```
