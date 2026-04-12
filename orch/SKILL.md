---
name: orch
description: Orchestrate the full SDLC skill suite (ex, re, arch, impl, qa, sec, devops, verify) as a single natural-language entry point. Use this skill when the user wants to run a multi-skill pipeline, resume a prior run, check run status, or route a request to the right skill(s). Also triggers when the user mentions "pipeline", "full SDLC", "run all skills", "orchestrate", "resume run", "run status", wants to build a complete system from scratch, or needs coordinated multi-skill execution — even if they don't explicitly say "orch".
---

# Orch — Orchestration Skill

Orch is the **control plane** of the Harness pipeline. It does not produce content artifacts — that is the job of the eight content skills (ex, re, arch, impl, qa, sec, devops, verify). Instead, Orch receives a natural-language request, routes it to the right skill(s) or a predefined pipeline, manages the run lifecycle (creation, execution, pause, resume, completion), and brokers artifact handoff between skills.

Orch is an **optional orchestration layer**. When only one skill is needed, users can call it directly. Orch adds value when:

- Multiple skills must run in sequence or parallel
- Artifact handoff between skills needs coordination
- The user wants resumable, trackable long-running execution
- A predefined pipeline (full-sdlc, new-feature, security-gate, etc.) fits the task

## Current state (injected at load)

!`test -f harness-output/current-run.md && cat harness-output/current-run.md || echo "status: idle — no active run"`

## Skill root

!`echo ${SKILL_DIR}`

## User request

$ARGUMENTS

---

## Workflow overview (six stages)

Orch processes every request through up to six stages. Not all stages activate for every request — a simple status query touches only `status`, while a full-SDLC pipeline activates all six.

```
User natural-language request
    |
    v
[1] dispatch ---- analyse intent, route to skill or pipeline
    |
    v
[2] pipeline ---- execute DAG: spawn skills, gate on approval, handle parallelism
    |
    +---> [3] relay ---- mediate user <-> skill dialogue when skill needs input
    |
    +---> [4] run ------ manage run lifecycle (init, state, complete, resume)
    |
    +---> [5] config --- manage settings (output path, skill toggles, templates)
    |
    v
[6] status ------ query run history, skill state, artifacts
```

When entering a stage, **Read** the corresponding reference file before proceeding:

| Stage | Reference | When to load |
|-------|-----------|-------------|
| dispatch | `${SKILL_DIR}/references/workflow/dispatch.md` | Every request (this is always the first stage) |
| pipeline | `${SKILL_DIR}/references/workflow/pipeline.md` | When dispatch produces a multi-step plan |
| relay | `${SKILL_DIR}/references/workflow/relay.md` | When a spawned skill signals `needs_user_input` |
| run | `${SKILL_DIR}/references/workflow/run.md` | When creating, updating, or completing a run |
| config | `${SKILL_DIR}/references/workflow/config.md` | When the user changes settings or output paths |
| status | `${SKILL_DIR}/references/workflow/status.md` | When the user asks about run history or skill state |

## Skill registry

Orch brokers eight content skills. Each has a standard entry point (`<skill>/SKILL.md`) and artifact directory.

| Skill | Role | Artifact sections | Artifact prefix |
|-------|------|-------------------|-----------------|
| ex | Codebase exploration | 4 (structure map, tech stack, component relations, architecture inference) | EX- |
| re | Requirements engineering | 3 (requirements, constraints, quality attributes) | RE- |
| arch | Architecture design | 4 (decisions, components, tech stack, diagrams) | ARCH- |
| impl | Implementation mapping | 4 (implementation map, code structure, decisions, guide) | IMPL- |
| qa | Quality assurance | 4 (strategy, tests, traceability, report) | QA- |
| sec | Security verification | 4 (threat model, vulnerabilities, recommendations, compliance) | SEC- |
| devops | Operations/deployment | 4 (pipeline, IaC, observability, runbooks) | DEVOPS- |
| verify | Local integration verification | 3 (environment setup, scenarios, report) | VERIFY- |

Full registry and discovery rules: Read [references/contracts/skill-registry.md](references/contracts/skill-registry.md).

## Adaptive depth

Orch auto-selects between two execution modes based on request complexity:

| Mode | Trigger | Behaviour |
|------|---------|-----------|
| **single dispatch** | Request maps to one skill/agent ("analyse this codebase", "review my architecture") | Dispatch directly to that skill. Minimal run metadata — single step in `run.meta.yaml`. |
| **pipeline** | Request spans multiple skills ("build this from scratch", "add a feature with full testing") | Select a predefined pipeline or build a dynamic DAG. Full run lifecycle with multi-step tracking. |

Detailed rules: Read [references/adaptive-depth.md](references/adaptive-depth.md).

## Predefined pipelines

Ten pipelines are available for immediate routing. The `-existing` variants prepend `ex` (4-stage codebase exploration) to provide context for subsequent skills.

| Pipeline | Flow |
|----------|------|
| `full-sdlc` | re → arch → impl → [qa, sec, devops] → verify |
| `full-sdlc-existing` | ex → re → arch → impl → [qa, sec, devops] → verify |
| `new-feature` | re → arch → impl → qa |
| `new-feature-existing` | ex → re → arch → impl → qa |
| `security-gate` | sec:threat-model → sec:audit → sec:compliance |
| `security-gate-existing` | ex → sec:threat-model → sec:audit → sec:compliance |
| `quick-review` | re:review → arch:review → impl:review |
| `explore` | ex:scan → ex:detect → ex:analyze → ex:map |
| `integration-verify` | verify (6 stages) |
| `integration-verify-existing` | ex → verify (6 stages) |

`[qa, sec, devops]` denotes a **parallel group** — each skill runs in an isolated worktree (`EnterWorktree`) to avoid merge conflicts, and results are merged back when all complete.

Pipeline definitions: Read files in `${SKILL_DIR}/references/pipelines/`.

## Artifact path injection

When spawning a skill, Orch injects two environment variables to isolate artifacts per run:

| Variable | Value | Purpose |
|----------|-------|---------|
| `HARNESS_ARTIFACTS_DIR` | `<output-root>/runs/<run_id>/<skill>` | All skill artifacts write here |
| `HARNESS_RUN_ID` | `<run_id>` | Skills can reference the run ID in logs/reports |

Each content skill's `scripts/artifact.py` already reads `HARNESS_ARTIFACTS_DIR` as its first priority, falling back to `./artifacts/<skill>/`. This means run isolation works without modifying any content skill.

## Run lifecycle

Every execution creates a **run** — a directory under `<output-root>/runs/<run_id>/` containing:

```
<output-root>/
+-- current-run.md              # Active run snapshot (human-readable)
+-- pipeline.meta.yaml          # Orch pipeline state (script-managed)
+-- runs/
    +-- <run_id>/               # Format: YYYYMMDD-HHmmss-<4-char-hash>
        +-- run.meta.yaml       # Canonical run state (script-managed)
        +-- run.meta.md         # Human-readable rendering of run state
        +-- calls.log           # Skill invocation log
        +-- project-structure.md  # Generated on completion
        +-- release-note.md       # Generated on completion
        +-- ex/ re/ arch/ impl/ qa/ sec/ devops/ verify/
            +-- *.meta.yaml + *.md   # Content skill artifacts
```

## Script contract (mandatory)

**Never edit `*.meta.yaml` files directly.** All run state changes go through `${SKILL_DIR}/scripts/run.py`. The script enforces schema validation, timestamps, and legal state transitions.

| Command | Purpose |
|---------|---------|
| `run.py init-run --pipeline <name> [--output-root <path>]` | Issue run-id, create directory, initialise `run.meta.yaml` |
| `run.py update-state --run <id> --step <idx> --status <s>` | Update step status + auto `updated_at` |
| `run.py complete --run <id>` | Mark run completed, generate completion reports, update `current-run.md` to idle |
| `run.py cancel --run <id> --reason <r>` | Record cancellation |
| `run.py list` | List all runs |
| `run.py show --run <id>` | Show single run details |
| `run.py validate [--run <id>]` | Schema and traceability validation |
| `run.py observe --run <id>` | Scan all child skill `.meta.yaml` files, summarise phase/approval |
| `run.py next --run <id>` | Return next executable step based on current state |
| `run.py render --run <id>` | Regenerate `run.meta.md` and `current-run.md` from `run.meta.yaml` |

## Rules injected into spawned skills

When Orch spawns a content skill, it injects these behavioural rules into the skill's context:

| Rule file | Purpose |
|-----------|---------|
| `${SKILL_DIR}/references/rules/base.md` | Common rules: artifact format, `needs_user_input` protocol, upstream ID traceability |
| `${SKILL_DIR}/references/rules/output-format.md` | Markdown + YAML pair convention, section structure, meta header |
| `${SKILL_DIR}/references/rules/escalation-protocol.md` | When and how to signal `needs_user_input` (dialogue vs automatic skills) |
| `${SKILL_DIR}/references/rules/dialogue-protocol.md` | `needs_user_input` / `user_response` signal structure (question types, response packaging) |

## Stage summaries

### Stage 1 — dispatch

Read [references/workflow/dispatch.md](references/workflow/dispatch.md) before proceeding.

Analyse the user's natural-language request against the current run state (injected above). Determine whether this is:

- A **new request** requiring single dispatch or pipeline execution
- A **resume** of a paused/failed run (detected from `current-run.md`)
- A **status query** (route to `status` stage)
- A **config change** (route to `config` stage)

For new requests, match against predefined pipelines first. If no pipeline fits, build a dynamic skill sequence. For existing projects (detected by code presence or user mention), prefer `-existing` pipeline variants that prepend `ex`.

### Stage 2 — pipeline

Read [references/workflow/pipeline.md](references/workflow/pipeline.md) before proceeding.

Execute the skill sequence from dispatch. For each step:

1. Call `run.py update-state` to mark the step as `running`
2. Inject `HARNESS_ARTIFACTS_DIR` and `HARNESS_RUN_ID` environment variables
3. Inject upstream artifacts as context (previous skill outputs from `runs/<id>/<prev-skill>/`)
4. Inject behavioural rules from `references/rules/`
5. Spawn the skill as a subagent (Task)
6. On completion, call `run.py observe` to check artifact phase/approval
7. Gate on approval before proceeding to the next step

For **parallel groups**, use `EnterWorktree` to give each skill an isolated worktree. Merge results back when all parallel skills complete.

When a skill signals `needs_user_input`, delegate to the **relay** stage.

### Stage 3 — relay

Read [references/workflow/relay.md](references/workflow/relay.md) before proceeding.

Mediate dialogue between a running skill and the user:

1. Receive the skill's `needs_user_input` signal (structured question with type: open/choice/confirmation)
2. Present the question to the user in a readable form
3. Collect the user's response
4. Package it as a `user_response` with conversation summary
5. Return to the skill

Recognise shortcuts: "skip" means use defaults, "yes/ok" means confirm, numbered responses map to choices.

### Stage 4 — run

Read [references/workflow/run.md](references/workflow/run.md) before proceeding.

Manage the run lifecycle: initialise directories and metadata, track step state, handle completion and cancellation, support resume from checkpoint.

Run lifecycle: `INIT -> CONFIGURE -> EXECUTE -> COLLECT -> REPORT -> CLEANUP`

### Stage 5 — config

Read [references/workflow/config.md](references/workflow/config.md) before proceeding.

Handle configuration requests: output root path, skill enable/disable, pipeline template management, validation profiles.

### Stage 6 — status

Read [references/workflow/status.md](references/workflow/status.md) before proceeding.

Query and report: installed skills and versions, run history with filters, specific run details, artifact inventory, dependency graphs.

## Non-negotiables

- **Orch does not produce content.** It routes, coordinates, and tracks. Content creation is the exclusive responsibility of the eight content skills.
- **Scripts only for metadata.** Run state lives in `run.meta.yaml` and `pipeline.meta.yaml`. These are only modified through `${SKILL_DIR}/scripts/run.py`. If you feel tempted to `Edit` a `.meta.yaml`, stop.
- **Artifact path injection.** Every skill spawn must include `HARNESS_ARTIFACTS_DIR` and `HARNESS_RUN_ID`. Without these, artifacts land in the wrong place and run isolation breaks.
- **Adaptive depth.** Do not spin up a 10-step pipeline for "just run ex on this codebase". Match the execution weight to the request.
- **Resumability.** `current-run.md` is the fast path to understanding active state. It must be kept in sync with `run.meta.yaml` via `run.py render` after every state change.
- **Traceability.** Every run step records which skill ran, what artifacts it produced, and which upstream artifacts it consumed. The `calls.log` captures the full invocation timeline.
- **Parallel isolation.** Skills in a parallel group must each run in their own worktree. Never spawn parallel skills in the shared working directory.
