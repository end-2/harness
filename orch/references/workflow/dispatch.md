# Dispatch Stage — Intent Analysis and Routing

Dispatch is the entry point for every orch invocation. It analyses the user's natural-language request (from `$ARGUMENTS`) and the current run state (from `current-run.md`, injected into SKILL.md) to decide what happens next.

## Decision tree

```
User request arrives
    |
    +-- Is current-run.md showing an active run?
    |   +-- YES: Is the request about that run?
    |   |   +-- "resume" / "continue" / "next step" --> Resume active run (jump to pipeline stage)
    |   |   +-- "status" / "where are we" --> Jump to status stage
    |   |   +-- "cancel" / "stop" --> Cancel active run via run.py cancel
    |   |   +-- Unrelated new request --> Warn user about active run, ask to cancel or continue
    |   +-- NO: Proceed to new request analysis
    |
    +-- Is this a status query?
    |   +-- "list runs" / "show run" / "what skills" --> Jump to status stage
    |
    +-- Is this a config change?
    |   +-- "set output path" / "enable/disable skill" --> Jump to config stage
    |
    +-- New execution request: Analyse intent
        +-- Single skill needed? --> Single dispatch (pipeline = single:<skill>:<agent>)
        +-- Multiple skills needed? --> Match to predefined pipeline or build dynamic DAG
```

## Intent analysis rules

### Detecting single-skill requests

A request maps to a single skill when:

- The user explicitly names a skill: "run ex", "do requirements analysis", "create architecture"
- The request scope clearly fits one skill's domain (code exploration, security audit, etc.)
- No cross-skill dependency is implied

Single dispatch uses `pipeline = single:<skill>:<agent>` and creates a lightweight run with one step.

### Detecting pipeline requests

A request needs a pipeline when:

- The user asks to "build from scratch", "create a full system", "do the full SDLC"
- Multiple skills are implied: "design and implement", "analyse, design, and test"
- The user names a pipeline: "run full-sdlc", "do the security gate"

### Pipeline selection

Match against predefined pipelines in this priority order:

1. **Exact name match**: User says "full-sdlc" or "security-gate" → use that pipeline
2. **Intent match**: User says "build a new app from scratch" → `full-sdlc` or `full-sdlc-existing`
3. **Existing project detection**: If any of these are true, prefer `-existing` variants:
   - There are source code files in the working directory (not just config files)
   - The user mentions "existing project", "current codebase", "add to"
   - `ex` artifacts already exist from a prior run
4. **Dynamic DAG**: If no predefined pipeline fits, construct a skill sequence from the request

### Pipeline-to-intent mapping

| User intent pattern | Pipeline |
|---------------------|----------|
| "build from scratch", "new system", "full SDLC" | `full-sdlc` |
| "add feature to existing", "extend this project" | `full-sdlc-existing` or `new-feature-existing` |
| "new feature", "add a feature" (no existing code) | `new-feature` |
| "security review", "security audit", "check security" | `security-gate` or `security-gate-existing` |
| "quick review", "review what we have" | `quick-review` |
| "explore this codebase", "analyse this code" | `explore` |
| "verify", "integration test", "does it work" | `integration-verify` or `integration-verify-existing` |

## Resume detection

A resume request is detected when:

- `current-run.md` shows a run with status `running`, `paused`, or `failed`
- The user says "continue", "resume", "pick up where we left off", "retry"
- The user references a specific run ID

On resume:
1. Read `run.meta.yaml` for the active run
2. Call `run.py next --run <id>` to find the next pending step
3. Jump to the pipeline stage starting from that step

## Output

Dispatch produces one of:

- A pipeline identifier and initial configuration → proceeds to **run** stage (init) then **pipeline** stage
- A status query → proceeds to **status** stage
- A config change → proceeds to **config** stage
- A resume instruction → proceeds to **pipeline** stage with the existing run

After deciding, tell the user what you're about to do:
- For pipelines: "I'll run the `<pipeline>` pipeline — this includes: <skill list>. Starting now."
- For single dispatch: "This looks like a `<skill>` task. I'll run `<skill>:<agent>` for you."
- For resume: "Resuming run `<id>` from step <N> (`<skill>:<agent>`)."
