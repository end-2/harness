# Run Stage — Lifecycle Management

The run stage manages the creation, tracking, and completion of execution runs. Every orch execution — whether single dispatch or full pipeline — creates a run.

## Run lifecycle

```
INIT ------> CONFIGURE ------> EXECUTE ------> COLLECT ------> REPORT ------> CLEANUP
  |              |                 |                |               |              |
  |  create dir  | set output     | pipeline runs  | observe all   | generate     | update
  |  init meta   | validate cfg   | steps execute  | skill states  | reports      | current-run
  |  gen run-id  |                |                |               |              | to idle
```

### INIT

Create the run directory and initialise metadata:

```bash
python ${SKILL_DIR}/scripts/run.py init-run --pipeline <name> [--output-root <path>]
```

This command:
1. Generates a run ID: `YYYYMMDD-HHmmss-<4hex>`
2. Creates the directory tree: `<output-root>/runs/<run_id>/` with subdirs for each skill
3. Initialises `run.meta.yaml` with pipeline steps, all in `pending` status
4. Creates or refreshes `pipeline.meta.yaml` and marks the run as active
5. Creates an empty `calls.log`
6. Renders `current-run.md` showing the new run
7. Returns JSON with `run_id` and `run_dir`

### CONFIGURE

Validate the configuration before execution starts:

- Output root exists and is writable
- Pipeline definition is valid (all referenced skills exist)
- No conflicting active run (check `current-run.md`)

If an active run exists, ask the user:
- Cancel the existing run and start a new one?
- Resume the existing run instead?
- Run both in parallel? (not recommended)

### EXECUTE

Hand off to the pipeline stage. The run stage just tracks state — the pipeline stage does the actual work.

During execution, the run stage responds to state updates:
- `run.py update-state` calls from the pipeline stage
- Auto-transitions: run status moves from `pending` to `running` when the first step starts

### COLLECT

After all pipeline steps complete, gather results:

```bash
python ${SKILL_DIR}/scripts/run.py observe --run <id>
```

This scans all `<run-dir>/<skill>/*.meta.yaml` files and produces a summary of:
- Which artifacts each skill produced
- Phase and approval state of each artifact
- Any missing or failed artifacts

### REPORT

Generate the two completion documents:

**`project-structure.md`**:
- Directory tree of the run output
- Technology stack summary (from arch artifacts)
- Component list (from arch artifacts)
- Build and run instructions (from impl artifacts)
- Infrastructure overview (from devops artifacts)

**`release-note.md`**:
- Pipeline that ran and duration
- Each skill's output summary (artifact count, key decisions)
- Quality results (from qa artifacts)
- Security findings (from sec artifacts)
- Verification verdict (from verify artifacts)
- Known limitations and next steps
- Full traceability chain: RE → ARCH → IMPL → QA/SEC/DEVOPS → VERIFY

### CLEANUP

Finalise the run:

```bash
python ${SKILL_DIR}/scripts/run.py complete --run <id>
```

This:
1. Sets run status to `completed` and records `ended_at`
2. Generates `project-structure.md` and `release-note.md`
3. Updates `current-run.md` to show idle state with last run reference
4. Renders final `run.meta.md`

`complete` only succeeds when every step is already terminal (`completed` or `skipped`).

## Resume support

When resuming a paused or failed run:

1. Read `run.meta.yaml` to find the current state
2. Call `run.py next --run <id>` to identify ready steps, running blockers, or failed-step blockers
3. If `ready_steps` is returned, jump to the pipeline stage from that step or step group
4. If `blocked_on_failed` is returned, resolve or retry the failed step before continuing

Resume preserves all completed step artifacts — only pending or failed steps re-execute.

## Cancellation

```bash
python ${SKILL_DIR}/scripts/run.py cancel --run <id> --reason "User requested cancellation"
```

This:
1. Sets run status to `cancelled` with a reason
2. Records the cancellation in `errors[]`
3. Updates `current-run.md` to idle
4. Completed step artifacts are preserved — only in-progress work is abandoned

## Concurrent runs

Orch supports one active run at a time. `current-run.md` acts as a lightweight lock:
- If it shows an active run, warn the user before starting a new one
- Completed/cancelled runs are archived in `runs/` and do not block new runs
- The user can explicitly force a new run while one is active, but this is discouraged
