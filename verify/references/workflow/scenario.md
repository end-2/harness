# Scenario — Verification Scenario Derivation Stage

**Role**: Systematically derive verification scenarios from Arch sequence diagrams, RE acceptance criteria, DevOps observability config, and DevOps runbooks.

**Runs in**: subagent (clean context for systematic derivation).

## Entry conditions

- `instrument` stage completed.
- Arch diagrams are accessible (via Impl/DevOps `arch_refs`).
- DevOps observability and runbook artifacts are accessible.

## Scenario categories

### 1. Integration scenarios (SC-0xx)

Source: `ARCH-DIAG-*.sequence` diagrams and `RE-*.acceptance_criteria` (via Arch refs).

For each sequence diagram:
1. Read the participants and message flow.
2. Create a scenario that exercises the full flow end-to-end.
3. Define steps as concrete HTTP requests, message publications, or database queries.
4. Define expected results at each observation layer:
   - **Response**: HTTP status, response body shape.
   - **Metric**: counter increments, histogram observations.
   - **Log**: expected structured log entries.
   - **Trace** (heavy mode): trace spans matching the sequence flow.

Each sequence diagram should produce at least one happy-path scenario. Complex diagrams with branches (error paths, conditional flows) may produce multiple scenarios.

### 2. Failure scenarios (SC-1xx)

Source: `ARCH-COMP-*.dependencies` and `IMPL-IDR-*.pattern_applied`.

For each dependency between components:
1. **Service unavailability**: what happens when the dependency is stopped (`docker stop`)?
2. **High latency**: what happens when the dependency is slow (`tc netem delay`)?
3. **Error responses**: what happens when the dependency returns errors?

Patterns from `IMPL-IDR-*` guide expectations:
- Circuit Breaker → expect degraded but not crashed service.
- Retry with backoff → expect eventual success or graceful failure.
- Bulkhead → expect isolation (other endpoints still work).

### 3. Load scenarios (SC-2xx)

Source: `DEVOPS-OBS-*.slo_definitions` (performance SLOs).

Keep these light — Verify is not a load testing tool. The goal is to confirm:
1. The system handles a small burst of concurrent requests without errors.
2. Metrics (request count, latency histogram) are recorded correctly under load.

Typically one scenario: send N concurrent requests (N = 10–50) and check that all succeed and metrics are sane.

### 4. Observability scenarios (SC-3xx)

Source: `DEVOPS-OBS-*` (SLOs, monitoring rules, dashboards, logging config, tracing config) and `DEVOPS-RB-*` (runbook trigger conditions).

These verify the observability stack itself:
1. **SLO metric collection**: for each `slo_definitions[]`, query Prometheus and confirm the SLI metric exists and has a value.
2. **Alert rule syntax**: load alerting rules into Prometheus and confirm they parse without errors.
3. **Dashboard rendering**: load dashboards into Grafana and confirm they render (no "No data" panels when data exists).
4. **Log format validation**: check that logs match `DEVOPS-OBS-*.logging_config.format` (JSON structure, required fields).
5. **Masking verification**: if `DEVOPS-OBS-*.logging_config.masking` is set, send requests with sensitive data and verify it's masked in logs.
6. **Trace propagation** (heavy mode): send a request that crosses multiple services and verify a complete trace appears in Tempo.
7. **Runbook trigger reproduction**: for each `DEVOPS-RB-*.trigger_condition`, reproduce the condition and verify the alert fires.

## Scenario structure

Each scenario must include:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique ID following the category convention (SC-0xx, SC-1xx, SC-2xx, SC-3xx) |
| `category` | yes | `integration`, `failure`, `load`, or `observability` |
| `title` | yes | Short descriptive title |
| `description` | yes | What this scenario verifies and why |
| `preconditions` | yes | What must be true before running (services healthy, data seeded, etc.) |
| `steps` | yes | Ordered list of actions with type (http_request, fault_injection, metric_query, db_query, recovery) |
| `expected_results` | yes | What to check after execution, with type (response, metric, log, trace, dashboard) |
| `evidence_type` | yes | List of evidence types to collect |
| `arch_refs` | recommended | Source Arch artifact IDs |
| `re_refs` | optional | RE acceptance criteria IDs |
| `slo_refs` | optional | SLO IDs for observability scenarios |

## Adaptive depth impact

| Aspect | Light mode | Heavy mode |
|--------|-----------|-----------|
| Integration scenarios | 1–2 (main happy paths) | One per sequence diagram |
| Failure scenarios | 1 (main dependency) | One per dependency + pattern |
| Load scenarios | 0–1 (optional) | 1 (concurrent burst) |
| Observability scenarios | SLO metric check + basic log format | Full: SLO + alerts + dashboards + masking + tracing + runbooks |
| Total scenarios | 3 max | Comprehensive |

## Output

The subagent writes the scenario list to the allocated report file. The main agent creates the artifact:

```bash
python ${SKILL_DIR}/scripts/artifact.py init --section scenario
```

and merges the report body into `VERIFY-SC-*.md`.

## Report frontmatter

```yaml
kind: scenario
classification values:
  - content_draft      # scenario definitions ready for merge
  - coverage_gap       # identified area with no scenario coverage
  - source_ambiguity   # Arch diagram or RE criteria unclear
```
