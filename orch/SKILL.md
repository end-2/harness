---
name: orch
description: Orchestrate the full SDLC skill suite (ex, re, arch, impl, qa, sec, devops, verify) as a single natural-language entry point. Use this skill when the user wants to run a multi-skill pipeline, resume a prior run, check run status, or route a request to the right skill(s). Also trigger when the user mentions "pipeline", "full SDLC", "run all skills", "orchestrate", "resume run", "run status", wants to build a complete system from scratch, or needs coordinated multi-skill execution.
---

# Orch - Orchestration Skill

Orch is the control plane for the Harness skill suite. It does not author RE, Arch, Impl, QA, Sec, DevOps, or Verify content itself. Its job is to route work, manage the run lifecycle, hand off upstream artifacts, and keep the run state consistent.

Use Orch when the user wants:

- Multiple skills coordinated as one workflow
- A resumable run with status tracking
- A predefined pipeline (`full-sdlc`, `new-feature`, `security-gate`, and so on)
- Help choosing the right skill for a natural-language request

When only one skill is needed, prefer single dispatch over a full pipeline.

## First steps

Before doing anything substantial:

1. Read `harness-output/current-run.md` if it exists. If it does not exist, assume there is no active run.
2. Read [references/workflow/dispatch.md](references/workflow/dispatch.md). Every request starts there.
3. Treat the current conversation turn as the execution input. Do not rely on shell-style placeholder expansion.

## Workflow references

Load only the stage reference you need:

| Stage | Reference | When to load |
|-------|-----------|--------------|
| dispatch | [references/workflow/dispatch.md](references/workflow/dispatch.md) | Every request |
| pipeline | [references/workflow/pipeline.md](references/workflow/pipeline.md) | When dispatch selects a multi-step plan |
| relay | [references/workflow/relay.md](references/workflow/relay.md) | When a running skill asks for user input |
| run | [references/workflow/run.md](references/workflow/run.md) | When creating, updating, or completing a run |
| config | [references/workflow/config.md](references/workflow/config.md) | When the user changes Orch settings |
| status | [references/workflow/status.md](references/workflow/status.md) | When the user asks about runs, skills, or artifacts |

## Adaptive depth

Orch supports two execution modes:

| Mode | Trigger | Behavior |
|------|---------|----------|
| single dispatch | The request maps to one skill/agent | Create a one-step run such as `single:sec:audit` |
| pipeline | The request spans multiple skills | Select a predefined pipeline or build a dynamic sequence |

Detailed rules: [references/adaptive-depth.md](references/adaptive-depth.md)

## Predefined pipelines

| Pipeline | Flow |
|----------|------|
| `full-sdlc` | re -> arch -> impl -> [qa, sec, devops] -> verify |
| `full-sdlc-existing` | ex -> re -> arch -> impl -> [qa, sec, devops] -> verify |
| `new-feature` | re -> arch -> impl -> qa |
| `new-feature-existing` | ex -> re -> arch -> impl -> qa |
| `security-gate` | sec:threat-model -> sec:audit -> sec:compliance |
| `security-gate-existing` | ex -> sec:threat-model -> sec:audit -> sec:compliance |
| `quick-review` | re:review -> arch:review -> impl:review |
| `explore` | ex:scan -> ex:detect -> ex:analyze -> ex:map |
| `integration-verify` | verify (6 stages) |
| `integration-verify-existing` | ex -> verify (6 stages) |

`[qa, sec, devops]` is a logical parallel group. Run those steps concurrently only when the runtime can isolate code changes safely. If safe isolation is not available, execute the group sequentially after `impl`.

Pipeline definitions live under [references/pipelines/](references/pipelines/).

## Skill registry

Orch brokers these eight content skills:

| Skill | Role | Artifact prefix |
|-------|------|-----------------|
| ex | Codebase exploration | EX- |
| re | Requirements engineering | RE- |
| arch | Architecture design | ARCH- |
| impl | Implementation | IMPL- |
| qa | Quality assurance | QA- |
| sec | Security verification | SEC- |
| devops | Deployment and operations | DEVOPS- |
| verify | Integration verification | VERIFY- |

Full discovery and invocation rules: [references/contracts/skill-registry.md](references/contracts/skill-registry.md)

## Artifact path contract

When Orch starts a skill step, inject:

| Variable | Value | Meaning |
|----------|-------|---------|
| `HARNESS_ARTIFACTS_DIR` | `<output-root>/runs/<run_id>/<skill>` | Output directory for the current skill only |
| `HARNESS_RUN_ID` | `<run_id>` | Current run identifier |

Important:

- `HARNESS_ARTIFACTS_DIR` is not a shared parent artifact root.
- Upstream artifact directories must be passed explicitly as context, file paths, or summaries.
- Downstream skills should read upstream artifacts from the paths Orch hands them, not by inferring sibling directories from their own output directory.

## Run lifecycle

Every run lives under `<output-root>/runs/<run_id>/` and contains:

```text
<output-root>/
|-- current-run.md
|-- pipeline.meta.yaml
`-- runs/
    `-- <run_id>/
        |-- run.meta.yaml
        |-- run.meta.md
        |-- calls.log
        |-- project-structure.md
        |-- release-note.md
        |-- ex/
        |-- re/
        |-- arch/
        |-- impl/
        |-- qa/
        |-- sec/
        |-- devops/
        `-- verify/
```

Run state is script-managed. Do not edit `run.meta.yaml` or `pipeline.meta.yaml` directly.

## Script contract

Use `scripts/run.py` for all run metadata changes:

| Command | Purpose |
|---------|---------|
| `run.py init-run --pipeline <name> [--output-root <path>]` | Create a run and initialize metadata |
| `run.py update-state --run <id> --step <idx> --status <s>` | Update one step's status |
| `run.py complete --run <id>` | Complete a run after every step is terminal; also generate completion reports |
| `run.py cancel --run <id> --reason <r>` | Cancel a run |
| `run.py list` | List runs |
| `run.py show --run <id>` | Show one run's metadata |
| `run.py validate [--run <id>]` | Validate schema, pipeline references, and artifact integrity |
| `run.py observe --run <id>` | Summarize child-skill artifact phases and approvals |
| `run.py next --run <id>` | Return ready steps, wait states, or failed-step blockers |
| `run.py render --run <id>` | Re-render `run.meta.md` and `current-run.md` |

## Rules injected into spawned skills

When Orch dispatches a content skill, also load:

| Rule file | Purpose |
|-----------|---------|
| [references/rules/base.md](references/rules/base.md) | Common artifact and traceability rules |
| [references/rules/output-format.md](references/rules/output-format.md) | Markdown/YAML output contract |
| [references/rules/escalation-protocol.md](references/rules/escalation-protocol.md) | When to ask the user for input |
| [references/rules/dialogue-protocol.md](references/rules/dialogue-protocol.md) | `needs_user_input` and `user_response` structure |

## Stage summary

### 1. Dispatch

Read [references/workflow/dispatch.md](references/workflow/dispatch.md).

Classify the request as one of:

- New work requiring single dispatch or pipeline execution
- Resume of an existing run
- Status query
- Config change

Prefer predefined pipelines before inventing a dynamic one. Prefer `-existing` variants when the user is extending an existing codebase.

### 2. Pipeline

Read [references/workflow/pipeline.md](references/workflow/pipeline.md).

For each executable step:

1. Mark it `running` with `run.py update-state`
2. Inject `HARNESS_ARTIFACTS_DIR` and `HARNESS_RUN_ID`
3. Pass upstream artifact paths and summaries explicitly
4. Inject Orch rule references
5. Use the available delegation primitive (`spawn_agent`) only when the user's request authorizes orchestration; otherwise execute locally
6. After completion, run `run.py observe`, update the step state, and gate on approvals

When a skill emits `needs_user_input`, hand off to relay.

### 3. Relay

Read [references/workflow/relay.md](references/workflow/relay.md).

Translate a skill's structured question into a readable user message, collect the reply, package it as `user_response`, and return it to the skill.

### 4. Run

Read [references/workflow/run.md](references/workflow/run.md).

Initialize runs, keep `current-run.md` and `pipeline.meta.yaml` in sync, and generate end-of-run reports.

### 5. Config

Read [references/workflow/config.md](references/workflow/config.md).

Handle output-root and pipeline configuration requests conservatively. Do not promise persistent config changes unless the underlying file or command path exists.

### 6. Status

Read [references/workflow/status.md](references/workflow/status.md).

Report run history, active status, skill availability, and artifact inventory in human-readable form.

## Non-negotiables

- Orch does not produce content artifacts for the eight content skills.
- Never edit `run.meta.yaml` or `pipeline.meta.yaml` by hand.
- Always treat `HARNESS_ARTIFACTS_DIR` as the current step's output directory.
- Keep `current-run.md` synchronized with `run.meta.yaml`.
- Do not advance past a failed or still-running step.
- Only complete a run after every step is terminal (`completed` or `skipped`).
- Use concurrency only when it is safe for the current runtime. Correctness beats parallelism.
