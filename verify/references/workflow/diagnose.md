# Diagnose — Issue Diagnosis and Repair Stage

**Role**: Analyse failed scenarios, identify root causes, classify them by originating skill, and fix what can be fixed locally.

**Runs in**: main agent (issue fixes may require code/config changes needing user approval).

## Entry conditions

- `execute` stage completed — scenario results available.
- At least one scenario has `status: fail` (if all pass, skip to `report`).

## Diagnosis workflow

For each failed scenario:

### 1. Gather evidence

Collect all evidence from the failed scenario:
- HTTP response (status, body, headers).
- Error logs (from `docker compose logs` or Loki).
- Metrics (from Prometheus).
- Traces (from Tempo, heavy mode).
- Container status (`docker compose ps`, restart counts).

### 2. Identify the root cause

Work through these diagnostic paths:

**Container-level issues**:
- Service not running → check `docker compose ps`, look for crash loops.
- Service unhealthy → check health check endpoint, look for startup failures.
- OOM killed → check `docker inspect` for memory limits, `dmesg` for OOM events.

**Application-level issues**:
- Error response → read the error body and correlate with application logs.
- Timeout → check if the service is responding at all, look for blocked threads/event loops.
- Wrong response → compare expected vs actual, trace the code path.

**Configuration issues**:
- Connection refused → service name mismatch in environment variables (e.g., `localhost` instead of Docker service name).
- Authentication failed → wrong credentials in environment variables.
- Wrong port → port mapping mismatch between compose and application config.

**Observability issues**:
- Metric not found → wrong metric name in PromQL, metric not exposed by the app.
- Log format wrong → logging library not configured for JSON.
- Trace missing → OTLP endpoint not configured, trace propagation headers not forwarded.

### 3. Classify the issue origin

Every issue must be classified by the upstream skill that owns the root cause:

| Origin | Examples | Action |
|--------|----------|--------|
| `impl` | Code bug, missing error handler, wrong API contract, build error | Fix in source code (with user approval) or record for Impl feedback |
| `devops` | Wrong PromQL, incorrect dashboard query, missing alert rule, log format mismatch | Fix in observability config or record for DevOps feedback |
| `arch` | Interface mismatch between components, missing dependency, circular dependency | Cannot fix locally — escalate to user |
| `verify` | Wrong port mapping in compose, incorrect environment variable, test script error | Fix directly in verify artifacts |

### 4. Auto-fix or escalate

**Auto-fixable issues** (fix and re-verify):

- `verify` origin: compose config fixes (port mappings, env vars, network names, health check commands). Fix directly and re-run the affected scenario.
- `impl` origin (minor): typos in environment variable names, missing default values. Propose the fix to the user; if approved, apply and re-run.
- `devops` origin (minor): wrong metric names in PromQL, incorrect log field names. Fix in the local monitoring config and re-run.

**Non-fixable issues** (record for feedback):

- `impl` origin (significant): code bugs, missing error handling, wrong API contracts. Record with `IMPL-*` refs.
- `devops` origin (significant): fundamental observability design issues. Record with `DEVOPS-*` refs.
- `arch` origin: structural issues that require Arch-level changes. Escalate to the user immediately.

### 5. Re-run affected scenarios

After fixing an issue:

1. Restart affected services if needed: `docker compose -f docker-compose.verify.yml restart <service>`.
2. Re-run only the scenarios that failed due to the fixed issue.
3. Update the scenario result from `fail` to `pass` if the re-run succeeds.
4. Record the fix in the issue's `resolution` and `status` fields.

## Issue structure

Each discovered issue must include:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | ISS-001, ISS-002, ... |
| `severity` | yes | `high` (blocks verification), `med` (degrades but doesn't block), `low` (cosmetic) |
| `category` | yes | `impl`, `devops`, `arch`, `verify` |
| `description` | yes | What went wrong |
| `root_cause` | yes | Why it went wrong |
| `resolution` | if fixed | What was changed |
| `status` | yes | `fixed`, `escalated`, `deferred` |
| `scenario_refs` | yes | Which scenarios exposed this issue |
| `impl_refs` / `devops_refs` / `arch_refs` | by category | Upstream artifact that needs fixing |

## Output

The diagnosis results merge into the report stage:
- Updated scenario results (some `fail` → `pass` after fixes).
- Issue list with classifications.
- Fix history (what was changed and when).

## Escalation conditions

- **Root cause is Arch-level**: interface mismatch, dependency cycle, component boundary violation. Tell the user which Arch artifact needs review.
- **Fix requires significant code changes**: more than a config tweak. Present the diagnosis to the user and let them decide whether to fix in Impl or accept the issue.
