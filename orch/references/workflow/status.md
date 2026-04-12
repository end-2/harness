# Status Stage — Run History and Skill State Queries

The status stage responds to informational queries about runs, skills, and artifacts. It reads metadata but never modifies it.

## Query types

### Run listing

```
User: "list runs" / "show all runs" / "what have we done"
```

```bash
python ${SKILL_DIR}/scripts/run.py list
```

Displays a table of all runs with: run_id, pipeline, status, created_at.

### Run details

```
User: "show run <id>" / "details of last run" / "what happened in <id>"
```

```bash
python ${SKILL_DIR}/scripts/run.py show --run <id>
```

Displays full run metadata: pipeline, status, each step with its status and artifacts, errors, timing.

For "last run" or "previous run", find the most recent run from the list.

### Skill state

```
User: "what skills are available" / "skill status"
```

List the eight content skills with their availability:
- Check if `<skill>/SKILL.md` exists in the workspace
- Check if the skill is disabled in config
- Show artifact count from the most recent run

### Artifact inventory

```
User: "what artifacts do we have" / "show artifacts from run <id>"
```

```bash
python ${SKILL_DIR}/scripts/run.py observe --run <id>
```

For each skill in the run, list artifacts with their phase and approval state.

### Active run status

```
User: "where are we" / "current status" / "what's happening"
```

Read `current-run.md` (already injected in SKILL.md context). If an active run exists, show:
- Current step and its status
- Progress (N of M steps complete)
- Any pending user actions (waiting for approval, needs_user_input)

### Run validation

```
User: "validate run <id>" / "check run integrity"
```

```bash
python ${SKILL_DIR}/scripts/run.py validate --run <id>
```

Reports schema errors, missing artifacts, broken traceability links.

## Response formatting

Format status responses as readable tables and summaries. Avoid dumping raw JSON — translate into human-friendly language:

Instead of:
```json
{"run_id": "20260412-103000-a1b2", "status": "completed", "steps": [...]}
```

Present:
```
Run 20260412-103000-a1b2 (full-sdlc) — completed

Steps:
  1. re:elicit      done
  2. re:analyze     done
  3. re:spec        done
  4. arch:design    done
  5. impl:generate  done
  6. qa:generate    done   (parallel)
  7. sec:audit      done   (parallel)
  8. devops:pipeline done  (parallel)
  9. verify:provision done
 10. verify:execute  done

All 10 steps completed. 23 artifacts produced.
```

## Comparison queries

```
User: "compare run A with run B" / "what changed between runs"
```

Load both runs and diff:
- Different pipelines?
- Steps that changed status?
- New or modified artifacts?
- Timing differences?
