# Skill Registry — Discovery and Invocation Contract

This document defines how orch discovers and invokes the eight content skills in the harness monorepo.

## Skill discovery

Each content skill is identified by:

1. **Directory**: `<repo-root>/<skill>/` (e.g., `arch/`, `impl/`)
2. **Entry point**: `<skill>/SKILL.md` — must exist and contain valid YAML frontmatter with `name` and `description`
3. **Script**: `<skill>/scripts/artifact.py` — metadata management CLI

A skill is considered **available** if its `SKILL.md` exists and is readable.

## Registered skills

| Skill ID | Directory | Entry point | Artifact prefix | Section count |
|----------|-----------|-------------|-----------------|---------------|
| ex | `ex/` | `ex/SKILL.md` | EX- | 4 |
| re | `re/` | `re/SKILL.md` | RE- | 3 |
| arch | `arch/` | `arch/SKILL.md` | ARCH- | 4 |
| impl | `impl/` | `impl/SKILL.md` | IMPL- | 4 |
| qa | `qa/` | `qa/SKILL.md` | QA- | 4 |
| sec | `sec/` | `sec/SKILL.md` | SEC- | 4 |
| devops | `devops/` | `devops/SKILL.md` | DEVOPS- | 4 |
| verify | `verify/` | `verify/SKILL.md` | VERIFY- | 3 |

## Invocation protocol

When orch spawns a skill:

### 1. Environment variable injection

```bash
export HARNESS_ARTIFACTS_DIR="<output-root>/runs/<run_id>/<skill>"
export HARNESS_RUN_ID="<run_id>"
export SKILL_DIR="<repo-root>/<skill>"
```

`HARNESS_ARTIFACTS_DIR` always points to the current skill's output directory. Orch must pass upstream artifact directories separately.

### 2. Context assembly

Provide the skill with:
- Its own SKILL.md path (so it can read its instructions)
- Upstream artifact paths (outputs from previous pipeline steps)
- Behavioural rules from `orch/references/rules/`

### 3. Agent spawning

Use `spawn_agent` when the user's request authorizes orchestration or delegation. If delegation is unavailable, execute the step locally and keep the same environment/context contract.

### 4. Result collection

After the skill completes, collect:
- Artifact IDs produced (from the skill's return message and/or the generated `.meta.yaml` files)
- Artifact phases (from `run.py observe`)
- Any errors or escalation signals

## Skill dependency graph

The standard dependency order for content production:

```
ex (optional, for existing codebases)
 |
 v
re (requirements)
 |
 v
arch (architecture)
 |
 v
impl (implementation)
 |
 +--> qa (quality)      \
 +--> sec (security)     } parallel group
 +--> devops (operations)/
 |
 v
verify (verification)
```

Cross-skill artifact references follow this graph. A skill can reference artifacts from any upstream skill but should not reference downstream skills (verify should not reference re directly — it goes through impl/devops).

## Agent naming convention

Each skill supports one or more agents (workflow stages). The convention is `<skill>:<agent>`:

| Skill | Agents |
|-------|--------|
| ex | scan, detect, analyze, map |
| re | elicit, analyze, spec, review |
| arch | design, adr, diagram, review |
| impl | generate, pattern, review, refactor |
| qa | strategy, generate, trace, report |
| sec | threat-model, audit, compliance |
| devops | pipeline, iac, observe, runbook |
| verify | provision, instrument, scenario, execute, diagnose, report |

Not all agents need to run in every pipeline — the pipeline definition specifies which agents to invoke.

## Artifact path convention

Within a run directory, each skill's artifacts live in a dedicated subdirectory:

```
runs/<run_id>/
    ex/         # EX-* artifacts
    re/         # RE-* artifacts
    arch/       # ARCH-* artifacts
    impl/       # IMPL-* artifacts
    qa/         # QA-* artifacts
    sec/        # SEC-* artifacts
    devops/     # DEVOPS-* artifacts
    verify/     # VERIFY-* artifacts
```

Each skill writes its `<id>.meta.yaml` and `<id>.md` pairs into its subdirectory. The `HARNESS_ARTIFACTS_DIR` environment variable points to this path, and each skill's `artifact.py` reads it as the primary output location.
