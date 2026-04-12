# Example: Resuming a Paused Run

Demonstrates how orch resumes a run that was interrupted.

## Scenario

The user started a `full-sdlc` pipeline yesterday. Steps 0-4 completed (re + arch + impl). The session ended while qa/sec/devops parallel group was running. Today the user returns.

## current-run.md (at session start)

The dynamic context injected into SKILL.md shows:

```markdown
# Active Run: 20260411-153000-d5e6

- **Pipeline**: full-sdlc
- **Status**: running
- **Created**: 2026-04-11T15:30:00Z
- **Updated**: 2026-04-11T16:45:00Z

## Steps

| # | Skill | Agent | Status |
|---|-------|-------|--------|
| 0 | re | elicit | done completed |
| 1 | re | analyze | done completed |
| 2 | re | spec | done completed |
| 3 | arch | design | done completed |
| 4 | impl | generate | done completed |
| 5 | qa | generate | FAIL failed |
| 6 | sec | audit | done completed |
| 7 | devops | pipeline | done completed |
| 8 | verify | provision | ... pending |
| 9 | verify | execute | ... pending |

## Errors

- [step_failure] Step 5 (qa:generate): Timeout after 300s
```

## User request

```
"Continue where we left off"
```

## Stage 1: Dispatch

Dispatch sees:
- `current-run.md` shows an active run in `running` status
- User says "continue" → resume intent detected
- Run 20260411-153000-d5e6 has a failed step (qa:generate) and pending steps

```bash
python ${SKILL_DIR}/scripts/run.py next --run 20260411-153000-d5e6
```

Output:
```json
{
  "next_step": 5,
  "skill": "qa",
  "agent": "generate"
}
```

Message to user: "Resuming run 20260411-153000-d5e6. Steps 0-4 (re, arch, impl) are complete. Step 5 (qa:generate) failed with a timeout last session — I'll retry it. Steps 6-7 (sec, devops) completed successfully. After qa, I'll proceed to verify."

## Stage 2: Pipeline — retry failed step

```bash
python ${SKILL_DIR}/scripts/run.py update-state --run 20260411-153000-d5e6 --step 5 --status running
```

Spawn qa:generate with:
- HARNESS_ARTIFACTS_DIR pointing to the existing run directory
- Upstream IMPL artifacts (already present from step 4)

QA generation succeeds this time:
```bash
python ${SKILL_DIR}/scripts/run.py update-state --run 20260411-153000-d5e6 --step 5 --status completed
```

## Stage 2: Pipeline — continue with pending steps

Since steps 5, 6, 7 are now all completed, proceed to verify:

```bash
python ${SKILL_DIR}/scripts/run.py update-state --run 20260411-153000-d5e6 --step 8 --status running
# verify:provision runs...
python ${SKILL_DIR}/scripts/run.py update-state --run 20260411-153000-d5e6 --step 8 --status completed

python ${SKILL_DIR}/scripts/run.py update-state --run 20260411-153000-d5e6 --step 9 --status running
# verify:execute runs...
python ${SKILL_DIR}/scripts/run.py update-state --run 20260411-153000-d5e6 --step 9 --status completed
```

## Completion

```bash
python ${SKILL_DIR}/scripts/run.py complete --run 20260411-153000-d5e6
```

### Key points demonstrated

1. **Immediate context restoration**: `current-run.md` in the SKILL.md header provides instant understanding of the active run state — no directory scanning needed
2. **Selective retry**: Only the failed step (qa:generate) re-runs. Completed steps are preserved.
3. **Artifact persistence**: All artifacts from the previous session remain in `runs/<id>/` and are available as upstream context for resumed steps
4. **Transparent communication**: Orch tells the user exactly what it's doing and why before proceeding
