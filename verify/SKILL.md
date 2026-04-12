---
name: verify
description: Consume approved Impl code and DevOps artifacts to provision a Docker Compose local environment with an observability stack (Prometheus/Grafana/Loki/Tempo), derive verification scenarios from Arch sequence diagrams, execute them, and validate that the system behaves as designed — diagnosing and backtracking issues to the originating skill. Use this skill whenever the user wants to validate that implementation and DevOps outputs actually work together, asks to spin up a local integration environment, needs end-to-end verification of the SDLC pipeline, wants to run integration or failure scenarios against a local stack, mentions "verify", "integration test environment", "local stack", "docker-compose validation", or is ready to close the SDLC loop from requirements through runtime evidence — even if they don't explicitly say "verify".
---

# Verify — Local Integration Verification Skill

Verify is the final validation stage of the Harness pipeline. It consumes the approved Impl artifacts (source code, implementation map, code structure, implementation decisions, implementation guide) and DevOps artifacts (pipeline config, IaC, observability setup, runbooks) and proves — through actual execution in a local Docker Compose environment — that the system behaves as its architecture intended.

If RE answered **"what are we building?"**, Arch answered **"how is it structured?"**, Impl answered **"what does the code look like?"**, QA answered **"how do we know it works?"**, and DevOps answered **"how do we deploy and observe it?"**, Verify answers **"does it actually work end-to-end when we put it all together?"**. The trade-offs were settled upstream — do **not** re-debate them. Verify is an **automatic execution + exception escalation** model: mechanically compose the local environment from upstream artifacts, run scenarios derived from Arch diagrams, and only escalate when a discovered issue requires changes at a level above Verify's scope.

The signature value of this skill is **Observability as a Verification Lens**: rather than limiting verification to "request → response", Verify uses the full observability stack (metrics, logs, traces) that DevOps defined to observe *how* the system processes each scenario — confirming that the design intent is realised at runtime, not just that an endpoint returns 200.

> **Scope boundary**: Verify operates exclusively in the local Docker Compose environment. It does **not** deploy to cloud, staging, or production. It does **not** run performance benchmarks or load tests beyond simple smoke-level verification. The environment is created with `docker compose up` and torn down with `docker compose down` — no permanent changes to the host system.

## Current state (injected at load)

!`python ${SKILL_DIR}/scripts/artifact.py validate`

The command above lists existing Verify artifacts, their phase, approval state, and traceability integrity. Read it before deciding whether this run is a fresh start, a continuation of in-progress verification, or a re-run after upstream fixes.

## Input / output contract

**Input**: the approved Impl and DevOps artifacts. Arch and RE are consumed indirectly through Impl's `arch_refs` and DevOps's `re_refs` / `slo_definitions` chains.

- `IMPL-MAP-*` — Implementation Map (module_path, component_ref, entry_point → build targets, container mapping)
- `IMPL-CODE-*` — Code Structure (build_config, external_dependencies, environment_config → Dockerfile, service dependencies)
- `IMPL-IDR-*` — Implementation Decisions (pattern_applied → scenario derivation: CQRS → separate read/write paths, Circuit Breaker → failure isolation)
- `IMPL-GUIDE-*` — Implementation Guide (prerequisites, build_commands, run_commands → container build and execution)
- `DEVOPS-PL-*` — Pipeline Config (deployment_method, rollback_trigger → deployment scenario verification)
- `DEVOPS-IAC-*` — Infrastructure Code (modules, networking → Docker network mapping)
- `DEVOPS-OBS-*` — Observability (slo_definitions, monitoring_rules, dashboards, logging_config, tracing_config → observability stack provisioning)
- `DEVOPS-RB-*` — Runbook (trigger_condition, diagnosis_steps → runbook trigger reproduction scenarios)

If any required artifact is missing or not in `approved` phase, stop and tell the user — Verify must not run on unstable input. Read the contract references for exact field mappings:

- [references/contracts/impl-input-contract.md](references/contracts/impl-input-contract.md) — Impl → environment provisioning
- [references/contracts/devops-input-contract.md](references/contracts/devops-input-contract.md) — DevOps → observability stack + scenario derivation
- [references/contracts/arch-input-contract.md](references/contracts/arch-input-contract.md) — Arch → scenario derivation (indirect)

**Output**: three category artifacts under `./artifacts/verify/`, each stored as a YAML metadata file plus a Markdown document:

1. **Environment Setup** (`VERIFY-ENV-*`) — docker-compose configuration, service definitions (app + infra + observability), network topology, startup order, health checks. Output of the `provision` + `instrument` stages.
2. **Verification Scenario** (`VERIFY-SC-*`) — test scenarios derived from Arch sequence diagrams and RE acceptance criteria, categorised as integration / failure / load / observability. Output of the `scenario` stage.
3. **Verification Report** (`VERIFY-RPT-*`) — scenario-by-scenario pass/fail results with evidence (metrics, logs, traces), issue list with root-cause classification, SLO metric validation, upstream skill feedback. Output of the `execute` + `diagnose` + `report` stages.

Each section is a pair `<id>.meta.yaml` + `<id>.md`. Metadata is the single source of truth for state and traceability and is **only** modified through `scripts/artifact.py`. Markdown holds the human-readable body and is edited directly, but only inside the scaffolding produced by `assets/templates/`.

Full schemas: read [references/schemas/section-schemas.md](references/schemas/section-schemas.md) and [references/schemas/meta-schema.md](references/schemas/meta-schema.md) when you need the exact field list.

Downstream consumption contract: read [references/contracts/downstream-contract.md](references/contracts/downstream-contract.md) before declaring artifacts ready, so you know what downstream consumers (DevOps review, Impl refactor, Arch review, Sec audit, Orch status) will look for.

## Core concept: Observability as Verification Lens

Observability is a **means**, not an end. The goal is to verify that the system behaves as designed — observability tools make that verification possible beyond simple request/response:

| Observation Layer | Tool | What it proves |
|-------------------|------|----------------|
| **Metrics** | Prometheus + Grafana | Requests are processed within SLO bounds. Error rates match expectations. DevOps-defined SLIs are actually measurable. |
| **Logs** | Loki | Services emit structured logs correctly. Correlation IDs propagate across services. Sensitive data is masked as DevOps logging_config specifies. |
| **Traces** | Tempo | Requests flow through components in the order Arch sequence diagrams specify. Bottlenecks and unexpected hops are visible. |

Combining these three axes moves verification from "it starts" to "it works as designed".

## Adaptive depth

Verify output depth follows Arch/Impl mode. A single-service CRUD app does not need the full Prometheus+Grafana+Loki+Tempo stack with distributed tracing validation, and a genuinely distributed system should not get only a health-check ping.

| Mode | Trigger (from upstream artifacts) | Output style |
|------|----------------------------------|--------------|
| **light** | Arch components ≤ 3, single deployment environment | Single docker-compose with app services + basic infra. Prometheus + Grafana only. ≤ 3 core scenarios (health check, main happy path, one failure). Basic metric collection validation. |
| **heavy** | Arch components > 3 or multi-environment/multi-region | Full observability stack (Prometheus + Grafana + Loki + Tempo). Comprehensive scenarios: integration + failure + load + observability. Distributed tracing propagation validation. SLO metric collection verification. Log masking verification. |

Pick the mode at the **start** of `provision`, after reading the upstream artifacts. Tell the user which mode you chose and why. The user may override. Full rules: [references/adaptive-depth.md](references/adaptive-depth.md).

## Workflow (six stages)

```
Impl artifacts (IMPL-MAP / IMPL-CODE / IMPL-IDR / IMPL-GUIDE, all approved)
DevOps artifacts (DEVOPS-PL / DEVOPS-IAC / DEVOPS-OBS / DEVOPS-RB, all approved)
Arch artifacts (indirect, via Impl/DevOps refs)
    │
    ▼
[1] provision   → Impl code + DevOps IaC/OBS → docker-compose environment
    │             app services + infra services + observability stack
    ▼
[2] instrument  → verify observability instrumentation in app code
    │             check metrics endpoints, structured logging, trace propagation
    ▼
[3] scenario    → Arch sequence diagrams + RE acceptance criteria → verification scenarios
    │             integration / failure / load / observability categories
    ▼
[4] execute     → start environment + run scenarios + collect evidence
    │             metrics queries, log searches, trace lookups, HTTP responses
    ▼
[5] diagnose    → analyse failures + classify root cause + fix or escalate
    │             backtrack issues to impl / devops / arch origin
    ▼
[6] report      → structured verification report + upstream skill feedback + verdict
```

Each stage has detailed behaviour rules in `references/workflow/<stage>.md`. When you enter a stage, **Read that file first** and follow the rules there. SKILL.md only gives the summary.

The pipeline is **checkpoint-based**. If diagnose finds auto-fixable issues (config typos, wrong port mappings), fix them and re-run the affected scenarios. Only **upstream contract violations** (Arch-level structural problems, DevOps observability gaps that require config regeneration) escalate to the user.

### Subagent delegation (hybrid)

Stages split between the **main agent** (which talks to the user and manages the environment) and isolated **subagents** (which work in a clean context window):

| Stage | Runs in | Why |
|-------|---------|-----|
| 1. provision | main | docker-compose generation requires synthesising Impl + DevOps artifacts; environment issues need real-time user communication |
| 2. instrument | main | may suggest code changes requiring user approval |
| 3. scenario | **subagent** | mechanical derivation from Arch diagrams — clean context produces more systematic scenarios |
| 4. execute | main | real-time environment interaction (docker exec, HTTP requests, fault injection); failure requires user judgment |
| 5. diagnose | main | issue fixes may require code/config changes needing user approval |
| 6. report | **subagent** | objective aggregation of results — clean context prevents bias from the execution dialogue |

**Sequencing rule (mandatory):** stages have a hard dependency order — `provision → instrument → scenario → execute → diagnose → report`. `scenario` may start as soon as `instrument` finishes (it does not depend on a running environment). `execute` requires both a provisioned environment (from `provision`) and scenarios (from `scenario`). Never start a stage before its dependencies have finished writing to disk.

**File-based handoff:** subagent stages (`scenario`, `report`) write their output to a **report file** under `./artifacts/verify/.reports/` and return only `report_id + verdict + summary`. For `scenario` the report body contains the scenario definitions to merge into `VERIFY-SC-*.md`. For `report` the body contains the structured verification report to merge into `VERIFY-RPT-*.md`. Subagents **never** edit artifact `.md` files directly, **never** call `artifact.py init / set-phase / link / approve` — they emit `proposed_meta_ops` in the report frontmatter and the main agent applies them. Read [references/contracts/subagent-report-contract.md](references/contracts/subagent-report-contract.md) for the frontmatter schema and per-stage `classification` values.

Before spawning any subagent, the main agent allocates the report path:

```bash
python ${SKILL_DIR}/scripts/artifact.py report path \
    --kind <scenario|report> --stage <stage> --scope all
```

and passes the printed `path` to the subagent as one of its inputs.

### Stage 1 — provision

Load [references/workflow/provision.md](references/workflow/provision.md).

- Read Impl and DevOps artifacts. Map `ARCH-COMP-*.type` (via `IMPL-MAP-*.component_ref`) to Docker services: `service` → app container, `store` → database container, `queue` → messaging container.
- Generate docker-compose.yml: application services (built from `IMPL-GUIDE-*.build_commands`), infrastructure services (from `IMPL-CODE-*.external_dependencies`), observability stack (from `DEVOPS-OBS-*`).
- Configure Docker networks, health checks (from component interfaces), startup ordering (from dependency graph), and environment variables (from `IMPL-CODE-*.environment_config`).
- Provision observability: load Prometheus scrape config and alerting rules from `DEVOPS-OBS-*.monitoring_rules`, load Grafana dashboards from `DEVOPS-OBS-*.dashboards`, configure Loki and Tempo (heavy mode).

Create the Environment Setup artifact:

```
python ${SKILL_DIR}/scripts/artifact.py init --section environment
```

**Escalation condition**: Docker daemon not running, required ports occupied, insufficient resources (memory/disk), Impl code fails to build.

### Stage 2 — instrument

Load [references/workflow/instrument.md](references/workflow/instrument.md).

- Check application code for observability instrumentation: metrics endpoint (`/metrics`, `/actuator/prometheus`), structured logging (JSON format, required fields), trace propagation (W3C Trace Context headers).
- Use `ARCH-TECH-*.choice` to select the appropriate instrumentation library (OpenTelemetry SDK, Micrometer, structlog, etc.).
- Report instrumentation status. If gaps are found, propose minimal-invasive additions to the user.

Update the Environment Setup artifact with instrumentation status.

**Escalation condition**: technology stack does not support OpenTelemetry, instrumentation changes require significant code restructuring.

### Stage 3 — scenario (subagent)

**Run as a subagent.** Allocate a report path, then spawn with the Arch diagrams (via Impl/DevOps refs), DevOps observability config, DevOps runbooks, and RE acceptance criteria (indirect).

Load [references/workflow/scenario.md](references/workflow/scenario.md).

- Derive **integration scenarios** from `ARCH-DIAG-*.sequence` — each sequence diagram becomes one or more scenarios.
- Derive **failure scenarios** from `ARCH-COMP-*.dependencies` — for each dependency, test service unavailability, high latency, and error responses.
- Derive **observability scenarios** from `DEVOPS-OBS-*` ��� SLO metric collection, alert rule firing, dashboard rendering, log format and masking.
- Derive **runbook reproduction scenarios** from `DEVOPS-RB-*.trigger_condition` — reproduce the trigger and verify diagnosis steps work.

Create the Verification Scenario artifact:

```
python ${SKILL_DIR}/scripts/artifact.py init --section scenario
```

### Stage 4 — execute

Load [references/workflow/execute.md](references/workflow/execute.md).

- Start the docker-compose environment. Wait for all services to pass health checks.
- Execute scenarios in dependency order: integration first, then failure, then observability.
- For each scenario: run the steps (HTTP requests, message publishing, fault injection via `docker stop`/`docker pause`/network delay), then collect evidence — Prometheus queries (PromQL), Loki queries (LogQL), Tempo trace lookups, HTTP response bodies.
- Judge each scenario: compare actual results against `expected_results` from the scenario definition.
- Monitor environment health throughout: service status, resource usage, container restarts.

**Escalation condition**: environment fails to start (container crash, OOM), network unreachable.

### Stage 5 — diagnose

Load [references/workflow/diagnose.md](references/workflow/diagnose.md).

- For each failed scenario, analyse the evidence (logs, metrics, traces) to identify the root cause.
- Classify the issue origin:
  - `impl`: code bug, wrong environment variable, build error
  - `devops`: observability config error (wrong PromQL, dashboard query mismatch, log format discrepancy)
  - `arch`: component interface mismatch, dependency cycle
- Auto-fixable issues (typos, config values, port mappings): fix, then re-run only the affected scenarios.
- Non-fixable issues: record with origin classification for feedback in the report stage.

**Escalation condition**: root cause requires Arch-level structural change.

### Stage 6 — report (subagent)

**Run as a subagent.** Allocate a report path, then spawn with all execution results, evidence artifacts, issue list, and the upstream artifact references.

Load [references/workflow/report.md](references/workflow/report.md).

- Aggregate scenario results: per-scenario pass/fail/skip with evidence references.
- Compute overall verdict: `pass` (all scenarios pass), `pass_with_issues` (all pass but issues were found and fixed), `fail` (at least one scenario fails after diagnosis).
- Validate SLO metrics: for each `DEVOPS-OBS-*.slo_definitions`, confirm the metric is actually collected and report a sample value.
- Classify upstream feedback: which issues trace to which upstream skill's artifacts.
- Complete the SDLC traceability chain: RE requirement → Arch decision → Impl code → DevOps config → **Verify evidence**.

Create the Verification Report artifact:

```
python ${SKILL_DIR}/scripts/artifact.py init --section report
```

When the report is complete and the user approves, transition each artifact to `approved`:

```
python ${SKILL_DIR}/scripts/artifact.py approve <id> --approver <user> --notes "..."
```

Once all three category artifacts are `approved`, Verify is done. Point the user at the downstream consumers and stop.

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
| `artifact.py init --section <name>` | Create a metadata + markdown pair from templates. `<name>` is one of `environment`, `scenario`, `report`. Returns the new `artifact_id`. |
| `artifact.py set-phase <id> <phase>` | Transition phase. |
| `artifact.py set-progress <id> --completed N --total M` | Update progress. |
| `artifact.py approve <id> --approver <name> [--state <s>] [--notes ...]` | Transition approval state. |
| `artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | Add a traceability reference. Cross-skill refs (`RE-*`, `ARCH-*`, `IMPL-*`, `DEVOPS-*`) are allowed. |
| `artifact.py show <id>` | Pretty-print the metadata. |
| `artifact.py list` | List all Verify artifacts in the project. |
| `artifact.py validate [<id>]` | Validate schema and traceability for one or all artifacts. |
| `artifact.py report path --kind <k> --stage <s> [--scope all]` | Allocate a fresh subagent handoff report file. Returns `{report_id, path}`. |
| `artifact.py report list [--kind <k>] [--stage <s>] [--target <id>]` | List reports, newest first. |
| `artifact.py report show <report_id>` | Print a report (frontmatter + body). |
| `artifact.py report validate <report_id-or-path>` | Validate a report's frontmatter against the handoff contract. |

The artifact directory defaults to `./artifacts/verify/` under the user's current working directory. Override with `HARNESS_ARTIFACTS_DIR`. Docker Compose files, observability configs, and test scripts generated during verification live under the project tree and are edited directly — they are not tracked by this script. Subagent reports live under `<artifacts-dir>/.reports/`.

## A few non-negotiables

- **Impl and DevOps are the source of truth.** Do not invent services, change observability configs, or add infrastructure not justified by upstream artifacts. If they are wrong, send the user back to the originating skill.
- **Automatic execution, exception escalation.** Do not ask the user for Docker settings, observability tool choices, or scenario priorities unless the upstream artifacts are genuinely ambiguous. Detect from the artifacts. Escalate only when an upstream decision cannot be verified at the local level.
- **Adaptive depth.** Light mode is not lazy — it is correct sizing. Do not deploy a full Prometheus+Grafana+Loki+Tempo stack for a single-service CRUD app.
- **Three categories, nothing more.** Verify stops at environment setup + scenarios + report. Security scanning belongs to `sec`; QA test generation belongs to `qa`; deployment belongs to `devops`.
- **Observability is a lens, not a goal.** Metrics, logs, and traces exist to observe verification — not to verify the observability stack itself (though confirming that DevOps-defined SLOs are measurable is in scope).
- **Traceability.** Every environment service cites an Arch component. Every scenario cites an Arch diagram or RE acceptance criterion. Every report issue cites the upstream artifact it traces to. If an artifact has no upstream anchor, it does not belong yet.
- **Scripts only for metadata.** If you ever feel tempted to `Edit` a `.meta.yaml`, stop — the right answer is almost always a subcommand of `artifact.py`.
- **Subagent reports go to files, not messages.** `scenario` and `report` each allocate a report path before spawning, write findings to that file, and return only `report_id + verdict + summary`. Subagents never call `artifact.py set-phase / approve`; they emit `proposed_meta_ops` and the main agent applies them.
- **Non-destructive execution.** `docker compose up` creates the environment, `docker compose down -v` tears it down. Fault injection uses container-level operations (`docker stop`, `docker pause`, `tc netem`). No permanent changes to the host system.
- **Issue backtracking.** When Verify finds a problem, it does not just report "test failed". It classifies the root cause as `impl`, `devops`, or `arch` and points to the specific upstream artifact that needs fixing. This is how Verify closes the SDLC feedback loop.
