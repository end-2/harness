---
name: devops
description: Turn approved Arch and Impl artifacts plus RE quality attributes into four DevOps deliverables — CI/CD pipeline config, Infrastructure-as-Code modules, observability setup (SLO/monitoring/logging/tracing), and operational runbooks — through an 8-stage workflow that unifies Deploy and Observe into a single SLO-driven feedback loop. Use this skill whenever the user is ready to move from implementation to deployment, asks to generate infrastructure or pipeline configuration from approved Arch/Impl artifacts, wants SLO definitions derived from RE quality attributes, needs monitoring/alerting/logging/runbook generation, mentions CI/CD pipelines or deployment strategies, or is about to hand off to operations — even if they don't explicitly say "DevOps".
---

# DevOps — Deploy & Observe Skill

DevOps is the fifth stage of the Harness pipeline. It consumes the approved Arch and Impl artifacts (and RE quality attributes indirectly through Arch's `re_refs`) and produces four categories of deliverables that unify deployment and observability into a single SLO-driven feedback loop.

If RE answered **"what are we building?"**, Arch answered **"how is it structured?"**, Impl answered **"what does the code look like?"**, and QA answered **"how do we know it works?"**, DevOps answers **"how do we deploy it, observe it, and keep it running?"**. The trade-offs between components, technologies, quality attributes, and test strategies were already settled upstream — do **not** re-debate them. DevOps is an **automatic execution + exception escalation** model: mechanically transform upstream artifacts into infrastructure, pipelines, monitoring, and runbooks, and only escalate when an upstream decision is genuinely unrealisable at the infrastructure level.

The signature value of this skill is the **Deploy → Observe feedback loop**: deployment strategy determines monitoring (canary metrics, rollback triggers), and monitoring results feed back into deployment decisions (SLO burn-rate → automatic rollback, error budget → deployment conservatism). This loop is not bolted on after the fact — it is woven through every stage.

> **Scope boundary**: DevOps generates artifact *files* (Terraform modules, pipeline YAML, Grafana dashboards, runbook markdown). It does **not** execute `terraform apply`, `kubectl apply`, or any destructive infrastructure command. Actual provisioning requires a separate step with explicit user approval.

## Current state (injected at load)

!`python ${SKILL_DIR}/scripts/artifact.py validate`

The command above lists existing DevOps artifacts, their phase, approval state, and traceability integrity. Read it before deciding whether this run is a fresh start, a continuation of in-progress generation, or a review pass.

## Input / output contract

**Input**: the approved Arch and Impl artifacts. RE is consumed indirectly through Arch's `re_refs` and `constraint_ref` chains.

- `ARCH-DEC-*` — Architecture Decisions (deployment unit shape, scaling strategy)
- `ARCH-COMP-*` — Component Structure (types, dependencies, interfaces → infra resources, deploy order, health checks)
- `ARCH-TECH-*` — Technology Stack (runtime, DB, messaging → cloud resource selection)
- `ARCH-DIAG-*` — Diagrams (c4-container → deploy topology, data-flow → monitoring points)
- `IMPL-CODE-*` — Code Structure (build_config, external_dependencies, environment_config)
- `IMPL-GUIDE-*` — Implementation Guide (build_commands, run_commands, prerequisites)
- `IMPL-MAP-*` — Implementation Map (module_path, component_ref → build targets)
- `IMPL-IDR-*` — Implementation Decisions (pattern_applied → operational characteristics)

If any required artifact is missing or not in `approved` phase, stop and tell the user — DevOps must not run on unstable input. Read the contract references for exact field mappings:

- [references/contracts/arch-input-contract.md](references/contracts/arch-input-contract.md) — Arch → IaC / deploy strategy
- [references/contracts/impl-input-contract.md](references/contracts/impl-input-contract.md) — Impl → pipeline / monitoring
- [references/contracts/re-input-contract.md](references/contracts/re-input-contract.md) — RE quality attributes → SLI/SLO (via Arch)

**Output**: four category artifacts under `./artifacts/devops/`, each stored as a YAML metadata file plus a Markdown document:

1. **Pipeline Config** (`DEVOPS-PL-*`) — CI/CD workflow definition plus deployment method, rollback triggers, and rollback procedure. Integrates the `pipeline` and `strategy` workflow stages.
2. **Infrastructure Code** (`DEVOPS-IAC-*`) — IaC modules, environment configs, state management, networking, cost estimates. Output of the `iac` stage.
3. **Observability** (`DEVOPS-OBS-*`) — SLI/SLO definitions, monitoring/alerting rules, dashboards, logging config, tracing config. Integrates the `slo`, `monitor`, and `log` stages.
4. **Runbook** (`DEVOPS-RB-*`) — Incident response procedures, diagnosis/remediation steps, escalation paths, postmortem templates. Output of the `incident` stage.

Each section is a pair `<id>.meta.yaml` + `<id>.md`. Metadata is the single source of truth for state and traceability and is **only** modified through `scripts/artifact.py`. Markdown holds the human-readable body and is edited directly, but only inside the scaffolding produced by `assets/templates/`.

Full schemas: read [references/schemas/section-schemas.md](references/schemas/section-schemas.md) and [references/schemas/meta-schema.md](references/schemas/meta-schema.md) when you need the exact field list.

Downstream consumption contract: read [references/contracts/downstream-contract.md](references/contracts/downstream-contract.md) before declaring artifacts ready, so you know what `security`, `management`, and operations consumers will look for.

## Adaptive depth

DevOps output depth follows Arch/Impl mode. A single-service CRUD app should not get multi-region Terraform with full RED/USE dashboards, and a genuinely distributed system should not get a bare-bones single pipeline.

| Mode | Trigger (from upstream artifacts) | Output style |
|------|----------------------------------|--------------|
| **light** | Arch components ≤ 3, single deployment environment | Single CI/CD pipeline, basic IaC (one environment), ≤ 3 core SLOs, essential monitoring rules, one or two critical runbooks. |
| **heavy** | Arch components > 3 or multi-environment/multi-region | Multi-stage pipeline with environment promotion, modular IaC per environment, comprehensive SLO set, RED/USE monitoring + distributed tracing, detailed runbooks per failure scenario. |

Pick the mode at the **start** of `slo`, after reading the upstream artifacts. Tell the user which mode you chose and why. The user may override. Full rules: [references/adaptive-depth.md](references/adaptive-depth.md).

## Workflow (eight stages)

```
Arch artifacts (ARCH-DEC / ARCH-COMP / ARCH-TECH / ARCH-DIAG, all approved)
Impl artifacts (IMPL-MAP / IMPL-CODE / IMPL-IDR / IMPL-GUIDE, all approved)
RE quality attributes (via Arch re_refs / constraint_ref)
    │
    ▼
[1] slo        → RE quality attributes → SLI/SLO definitions + error budgets
    │             (baseline for all subsequent observability)
    ├──→ [2] iac       → Arch components + tech stack → IaC modules
    │         │
    ├──→ [3] pipeline  → Impl code structure + IaC → CI/CD workflow
    │         │
    ├──→ [4] strategy  → SLO + Arch → deploy method + rollback ──→ update PL
    │         │
    ├──→ [5] monitor   → SLO + strategy → alerting rules + dashboards
    │
    ├──→ [6] log       → Arch components + security constraints → logging config
    │
    ├──→ [7] incident  → strategy rollback + monitor alerts → runbooks
    │
    ▼
[8] review     → full artifact review + feedback loop integrity check
```

Each stage has detailed behaviour rules in `references/workflow/<stage>.md`. When you enter a stage, **Read that file first** and follow the rules there. SKILL.md only gives the summary.

The pipeline is **checkpoint-based**. If review finds gaps in the feedback loop (e.g. an alert with no runbook, a deployment strategy with no rollback monitoring), step back to the relevant stage and fix. Only **upstream contract violations** (Arch component with no IaC mapping, RE quality attribute with no SLO) escalate to the user.

### Subagent delegation (hybrid)

Stages split between the **main agent** (which talks to the user and writes the core artifacts) and isolated **subagents** (which work in a clean context window):

| Stage | Runs in | Why |
|-------|---------|-----|
| 1. slo | main | establishes the SLO baseline that all subsequent stages reference; needs Arch context to resolve `re_refs` |
| 2. iac | main | writes IaC files that reference Arch components; may generate actual `.tf` / Helm files alongside metadata |
| 3. pipeline | main | writes pipeline YAML that references IaC and Impl build config; may need to surface conflicts to the user |
| 4. strategy | main | modifies the Pipeline Config artifact (adds deployment method, rollback); needs the SLO context from stage 1 |
| 5. monitor | **subagent** | pure derivation from settled SLO definitions + strategy — a clean context produces tighter alerting rules |
| 6. log | **subagent** | pure derivation from Arch component structure + security constraints — independent of deployment context |
| 7. incident | **subagent** | assembles runbooks from settled monitor alerts + strategy rollback procedures — benefits from a focused context |
| 8. review | **subagent** | pure verification over all settled artifacts — a clean context catches more feedback-loop gaps |

**Sequencing rule (mandatory):** stages have a dependency order. `slo` must complete before `strategy` and `monitor`. `iac` must complete before `pipeline`. `strategy` must complete before `incident`. `monitor` and `log` must complete before `incident`. `pipeline` must complete before `strategy` (strategy updates the pipeline). Never start a stage before its dependencies have finished writing to disk. Stages 5 and 6 (`monitor` and `log`) may run **in parallel**, but the main agent must reconcile both reports into the final Observability artifact before starting `incident`. Treat log-derived metrics as supplemental monitoring inputs that are merged after both subagents return.

**File-based handoff (light and heavy both):** subagent stages (`monitor`, `log`, `incident`, `review`) each write their output to a **report file** under `./artifacts/devops/.reports/` and return only `report_id + verdict + summary` in their message. For `monitor`, `log`, and `incident` the report body contains the draft content the main agent merges into the corresponding artifact `.md` file. For `review` the body is a structured verification report. Subagents **never** edit artifact `.md` files directly, **never** call `artifact.py init / set-phase / link / approve` — they may only propose `link` and `set-progress` operations in `proposed_meta_ops`, and the main agent decides whether to apply them. Read [references/contracts/subagent-report-contract.md](references/contracts/subagent-report-contract.md) for the frontmatter schema and per-stage `classification` values.

Before spawning any subagent, the main agent allocates the report path:

```bash
python ${SKILL_DIR}/scripts/artifact.py report path \
    --kind <monitor|log|incident|review> --stage <stage> --scope all
```

and passes the printed `path` to the subagent as one of its inputs.

### Stage 1 — slo

Load [references/workflow/slo.md](references/workflow/slo.md).

- Read Arch artifacts to resolve `re_refs` and `constraint_ref` chains back to RE quality attributes. Transform each measurable `metric` into a concrete SLI (e.g. `"response time < 200ms"` → `http_request_duration_seconds{quantile="0.99"} < 0.2`).
- Define SLO targets, error budgets, time windows, and multi-window burn-rate alert thresholds.
- Distribute SLOs across Arch components where applicable.

This is the first stage that writes to disk. Create the Observability artifact:

```
python ${SKILL_DIR}/scripts/artifact.py init --section observability
```

Fill in the `slo_definitions` portion of the markdown. Link upstream to the RE quality attributes via Arch refs.

**Escalation condition**: RE metric is a qualitative statement (e.g. "high user satisfaction") with no quantifiable proxy — present alternatives to the user.

### Stage 2 — iac

Load [references/workflow/iac.md](references/workflow/iac.md).

- Map `ARCH-COMP-*.type` to cloud resources (`service` → compute, `store` → DB, `queue` → messaging). Use `ARCH-TECH-*.choice` for concrete service selection. Respect `constraint_ref` for provider/region locks.
- Generate IaC modules (Terraform/Helm/Ansible), environment variable overrides, state management config, and networking.

Create the Infrastructure Code artifact and optionally the actual IaC source files:

```
python ${SKILL_DIR}/scripts/artifact.py init --section iac
```

**Escalation condition**: Arch-chosen technology has no managed service on the target cloud — present self-hosting vs alternative options.

### Stage 3 — pipeline

Load [references/workflow/pipeline.md](references/workflow/pipeline.md).

- Derive CI/CD stages from `IMPL-CODE-*.build_config` and `IMPL-GUIDE-*.build_commands`. Configure caching from `external_dependencies`, secrets from `environment_config`.
- Integrate IaC apply steps from stage 2.

Create the Pipeline Config artifact:

```
python ${SKILL_DIR}/scripts/artifact.py init --section pipeline
```

**Escalation condition**: build time exceeds platform timeout limits, or artifact size conflicts with registry limits.

### Stage 4 — strategy

Load [references/workflow/strategy.md](references/workflow/strategy.md).

- Derive deployment method from SLO availability targets (≥ 99.9% → blue-green or canary), error budget remaining, and `ARCH-COMP-*.dependencies` for deploy ordering.
- Define rollback triggers (SLO burn-rate breach, health-check failure) and rollback procedure.
- **Update the Pipeline Config artifact** with deployment method, rollback triggers, and rollback procedure fields.

**Escalation condition**: required deployment method conflicts with infrastructure cost or resource constraints.

### Stage 5 — monitor (subagent)

**Run as a subagent.** Allocate a report path, then spawn with the Observability artifact (SLO definitions), Strategy output, and Arch artifacts.

Load [references/workflow/monitor.md](references/workflow/monitor.md).

- Derive alerting rules from `slo_definitions.burn_rate_alert`. Generate dashboard definitions (Grafana/Datadog JSON). Configure distributed tracing based on Arch sequence diagrams.
- Connect strategy: canary deployments get canary-vs-baseline comparison metrics; rollback triggers wire to SLO burn-rate alerts.

### Stage 6 — log (subagent)

**Run as a subagent.** May run **in parallel** with monitor. Allocate a report path, then spawn with Arch component structure and RE constraints (via Arch).

Load [references/workflow/log.md](references/workflow/log.md).

- Define structured log format (JSON), per-service log namespaces, correlation ID propagation, sensitive-data masking rules, retention/rotation policy.
- Derive log-based metrics (error rate, latency percentiles) that complement stage 5 monitoring. When `monitor` and `log` ran in parallel, the main agent reconciles these metrics into the final Observability artifact before starting `incident`.

### Stage 7 — incident (subagent)

**Run as a subagent.** Allocate a report path, then spawn with Strategy (rollback procedures), Monitor (alerting rules), and Arch component structure.

Load [references/workflow/incident.md](references/workflow/incident.md).

- Generate one runbook per alerting rule or failure scenario. Include trigger condition, symptoms, diagnosis steps (with actual commands), remediation steps, escalation path, and communication template.
- Link each runbook to the monitoring rule and SLO that trigger it.

Create the Runbook artifact:

```
python ${SKILL_DIR}/scripts/artifact.py init --section runbook
```

### Stage 8 — review (subagent)

**Run as a subagent.** Allocate a report path, then spawn with all four DevOps artifacts plus the upstream Arch/Impl/RE artifacts.

Load [references/workflow/review.md](references/workflow/review.md).

The review validates along three axes:

1. **Feedback loop integrity** — every deployment strategy has monitoring rules, every alert has a runbook, rollback triggers connect to SLO burn-rate, error budgets feed deployment conservatism.
2. **Traceability** — every IaC module maps to an Arch component, every pipeline build matches Impl build config, every SLO traces to an RE quality attribute.
3. **Best practices** — security (secrets not hardcoded, least-privilege IAM), cost (right-sizing, reserved instance recommendations), environment consistency.

Classification drives routing:
- Feedback-loop gaps and best-practice issues → route back to the relevant stage.
- Upstream contract violations (Arch component without IaC, RE quality attribute without SLO) → **escalate to the user**.

When the review report is clean and the user approves, transition each artifact to `approved`:

```
python ${SKILL_DIR}/scripts/artifact.py approve <id> --approver <user> --notes "..."
```

Once all four category artifacts are `approved`, DevOps is done. Point the user at the next skill (`security`, `management`, operations handoff) and stop.

## Script contract (mandatory)

**Never edit `*.meta.yaml` files directly.** All state changes — phase, progress, approval, traceability — must go through `scripts/artifact.py`. The script enforces:

- Schema validation (rejects unknown phases, missing fields).
- `updated_at` auto-refresh.
- Legal phase transitions only (`draft → in_review → revising → in_review → approved → superseded`). You cannot jump straight from `draft` to `approved`.
- Bidirectional `upstream_refs` / `downstream_refs` integrity.
- An `approval.history` audit trail with timestamps.

Available subcommands:

| Command | Purpose |
|---------|---------|
| `artifact.py init --section <name>` | Create a metadata + markdown pair from templates. `<name>` is one of `pipeline`, `iac`, `observability`, `runbook`. Returns the new `artifact_id`. |
| `artifact.py set-phase <id> <phase>` | Transition phase. |
| `artifact.py set-progress <id> --completed N --total M` | Update progress. |
| `artifact.py approve <id> --approver <name> [--state <s>] [--notes ...]` | Transition approval state. |
| `artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | Add a traceability reference. Cross-skill refs (`RE-*`, `ARCH-*`, `IMPL-*`, `QA-*`) are allowed. |
| `artifact.py show <id>` | Pretty-print the metadata. |
| `artifact.py list` | List all DevOps artifacts in the project. |
| `artifact.py validate [<id>]` | Validate schema and traceability for one or all artifacts. |
| `artifact.py report path --kind <k> --stage <s> [--scope all]` | Allocate a fresh subagent handoff report file. Returns `{report_id, path}`. |
| `artifact.py report list [--kind <k>] [--stage <s>] [--target <id>]` | List reports, newest first. |
| `artifact.py report show <report_id>` | Print a report (frontmatter + body). |
| `artifact.py report validate <report_id-or-path>` | Validate a report's frontmatter against the handoff contract. |

The artifact directory defaults to `./artifacts/devops/` under the user's current working directory. Override with `HARNESS_ARTIFACTS_DIR`. Actual IaC/pipeline config files (`.tf`, `.yml`, Helm charts) live under the project tree and are edited directly — they are not tracked by this script. Subagent reports live under `<artifacts-dir>/.reports/`.

## A few non-negotiables

- **Arch/Impl are the source of truth for structure.** Do not invent components, change technology choices, or add infrastructure not justified by upstream artifacts. If Arch is wrong, send the user back to Arch.
- **Automatic execution, exception escalation.** Do not ask the user for cloud provider, deployment strategy, or monitoring tool unless the upstream artifacts are genuinely ambiguous. Detect from Arch tech stack and constraints. Escalate only when an upstream decision cannot be realised at the infrastructure level.
- **Adaptive depth.** Light mode is not lazy — it is correct sizing. Do not generate multi-region Terraform with full RED/USE dashboards for a single-service CRUD app.
- **Four categories, nothing more.** DevOps stops at pipeline + IaC + observability + runbooks. Security scanning belongs to `security`; project scheduling belongs to `management`; business logic and tests belong to `impl` and `qa`.
- **Deploy → Observe feedback loop.** Every deployment strategy must have corresponding monitoring. Every alert must have a runbook. Rollback triggers must connect to SLO burn-rate. This is the signature value — review enforces it.
- **Traceability.** Every IaC module cites an Arch component. Every SLO cites an RE quality attribute. Every pipeline build step cites an Impl build config. If an artifact has no upstream anchor, it does not belong yet.
- **Scripts only for metadata.** If you ever feel tempted to `Edit` a `.meta.yaml`, stop — the right answer is almost always a subcommand of `artifact.py`.
- **Subagent reports go to files, not messages.** `monitor`, `log`, `incident`, and `review` each allocate a report path before spawning, write findings to that file, and return only `report_id + verdict + summary`. Subagents never call `artifact.py set-phase / approve`; in DevOps they may only emit `link` and `set-progress` via `proposed_meta_ops`, and the main agent applies them if appropriate.
- **No destructive infrastructure commands.** This skill generates files. It does not run `terraform apply`, `kubectl apply`, `docker push`, or any command that modifies live infrastructure. Those require separate user approval.
