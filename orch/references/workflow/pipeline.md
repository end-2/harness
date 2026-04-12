# Pipeline Stage — DAG Execution and Skill Coordination

The pipeline stage executes the skill sequence determined by dispatch. It manages skill spawning, artifact handoff, approval gating, parallel execution, and relay delegation.

## Execution loop

For each step in the pipeline:

```
1. Check prerequisites
   - Previous sequential step must be completed
   - For parallel groups: all steps before the group must be completed
   - Required upstream artifacts must exist and be in approved phase

2. Prepare the step
   - Call: run.py update-state --run <id> --step <idx> --status running
   - Set environment variables:
     HARNESS_ARTIFACTS_DIR = <output-root>/runs/<run_id>/<skill>
     HARNESS_RUN_ID = <run_id>
   - Remember: HARNESS_ARTIFACTS_DIR is the current step's output directory, not a shared parent artifacts root

3. Assemble context for the skill
   - Upstream artifacts: Read completed skill outputs from runs/<id>/<prev-skill>/ and pass those paths explicitly
   - Behavioural rules: Read and inject rules from references/rules/
   - Skill entry point: <skill>/SKILL.md

4. Execute the skill
   - Preferred: use `spawn_agent` when the user's request authorizes orchestration or delegation
   - Fallback: execute locally in sequence when delegation is unavailable
   - Pass: skill path, upstream artifact paths, rules, environment variables

5. Monitor execution
   - If skill signals needs_user_input --> delegate to relay stage
   - If skill completes --> proceed to step 6
   - If skill fails --> record error, decide whether to retry or fail the run

6. Post-completion
   - Call: run.py observe --run <id> (scan artifact phases)
   - Call: run.py update-state --run <id> --step <idx> --status completed
   - Call: run.py render --run <id> (update human-readable files)
   - Log the invocation to calls.log
   - Check gating conditions for next step
```

## Skill spawning protocol

When spawning a content skill, construct the prompt with:

```
You are executing as part of an orchestrated pipeline run.

Run ID: <run_id>
Step: <idx> of <total>
Skill: <skill>:<agent>

## Environment
HARNESS_ARTIFACTS_DIR=<output-root>/runs/<run_id>/<skill>
HARNESS_RUN_ID=<run_id>

## Upstream context
<insert upstream artifact summaries and exact upstream artifact paths>

## Behavioural rules
<insert contents of references/rules/base.md>
<insert contents of references/rules/output-format.md>
<insert contents of references/rules/escalation-protocol.md (for dialogue skills)>

## Task
Read <skill>/SKILL.md and execute the <agent> stage.
Write all artifacts to the HARNESS_ARTIFACTS_DIR path.
```

## Parallel execution

Steps with the same `parallel_group` value are logically parallel. Execute them concurrently only when the runtime can isolate code changes safely:

1. **Before the group**: Ensure all preceding sequential steps are completed
2. **For each skill in the group**:
   - If safe isolated working directories are available, run the steps concurrently
   - Otherwise, run the steps one at a time after `impl`
   - In every case, the skill writes artifacts to its own `HARNESS_ARTIFACTS_DIR`
3. **Gate**: All parallel-group steps must reach terminal states before the next sequential step

If any parallel skill fails, the others continue to completion. Record the failure and decide:
- If the failed skill is optional for downstream steps → mark as failed, continue
- If the failed skill blocks downstream → pause the run, ask the user

## Approval gating

After each step completes, check whether the produced artifacts need user approval before proceeding:

- **Dialogue skills** (re:elicit, re:analyze, re:spec, arch:design): These involve user interaction during execution. Approval is typically handled within the skill itself.
- **Automatic skills** (ex, impl:generate, qa:generate, sec:audit): These produce artifacts that may need review. After completion, call `run.py observe` to check artifact phases.
- **Gate rule**: If a step's artifacts are in `in_review` and the next step requires `approved` upstream, pause and ask the user to review.

## Artifact handoff

When step N completes and step N+1 begins:

1. Identify the artifact paths from step N: `<output-root>/runs/<run_id>/<skill-N>/`
2. Read the relevant `.meta.yaml` files to get artifact IDs
3. Pass these as upstream context to step N+1
4. The downstream skill should `link --upstream` to these artifacts for traceability

## Error handling

| Error type | Action |
|------------|--------|
| Skill fails with recoverable error | Retry once, then fail the step |
| Skill fails with unrecoverable error | Fail the step, pause the run |
| Skill times out | Fail the step, record timeout in errors |
| Missing upstream artifact | Pause, ask user if they want to skip or fix |
| Approval rejected | Route back to the producing skill for revision |

On any failure:
```
run.py update-state --run <id> --step <idx> --status failed
```

## Calls log

Append to `<run-dir>/calls.log` for every skill invocation:

```
[2026-04-12T10:30:00Z] SPAWN  step=3 skill=arch agent=design
[2026-04-12T10:35:22Z] RELAY  step=3 skill=arch signal=needs_user_input
[2026-04-12T10:36:45Z] RELAY  step=3 skill=arch signal=user_response
[2026-04-12T10:42:10Z] DONE   step=3 skill=arch status=completed artifacts=ARCH-DEC-001,ARCH-COMP-001
```

## Completion

When all steps are completed (or the final step finishes):

1. Call `run.py observe --run <id>` for a final artifact summary
2. Generate completion reports:
   - `project-structure.md`: Directory layout, tech stack summary, build/run guide
   - `release-note.md`: Skills executed, key decisions, quality/security results, known limitations
3. Call `run.py complete --run <id>` only after every step is `completed` or `skipped`
4. Present the completion summary to the user
