# Workflow — Stage 5: Monitoring (subagent)

## Role

Generate alerting rules, dashboards, and distributed tracing configuration from the SLO definitions and deployment strategy. This stage is executed by a **subagent** — it does not call `${SKILL_DIR}/scripts/artifact.py` directly. Instead, it writes a report file at the path allocated by the main agent, and the main agent merges the report body into the Observability artifact (`DEVOPS-OBS-*`).

See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full subagent protocol.

> **Metadata reminder**: All metadata operations are handled by the main agent via `${SKILL_DIR}/scripts/artifact.py`. Subagents express metadata changes through `proposed_meta_ops` in their report frontmatter. `.meta.yaml` files must never be edited directly — not by the main agent, not by subagents.

## Inputs

- **Observability artifact** (`DEVOPS-OBS-*`) — specifically `observability_config.slo_definitions` from Stage 1. Each SLO drives one or more monitoring rules.
- **Strategy output** (from Stage 4) — `DEVOPS-PL-*.pipeline_config.deployment_method` and `rollback_trigger`. Deployment strategy determines strategy-aware monitoring (canary comparison, blue-green health).
- **ARCH-COMP-\*** — component list with `name`, `type`, `interfaces`, `dependencies`. Determines per-service monitoring scope and service topology for dependency-aware alerting.
- **ARCH-DIAG-\*** — sequence diagrams and data-flow diagrams. Sequence diagrams drive distributed tracing span definitions; data-flow diagrams identify transformation stages that need throughput/latency metrics.
- **IMPL-IDR-\*** (optional) — implementation decisions. Pattern-specific monitoring directives from the pattern-to-monitoring mapping in [../contracts/impl-input-contract.md](../contracts/impl-input-contract.md).

## SLO burn-rate to alerting rules

For each `slo_definitions` entry, generate monitoring rules at each alert tier:

| SLO field | Monitoring rule derivation |
|---|---|
| `sli` | Base metric expression for the rule condition |
| `target` + `error_budget` | Threshold calculation: `threshold = burn_rate * error_budget` |
| `burn_rate_alert.fast_window` | Short evaluation window for the rule |
| `burn_rate_alert.slow_window` | Long evaluation window — both must fire to trigger |
| `burn_rate_alert.threshold` | Burn-rate multiplier for the critical tier |
| `re_refs` | Propagated to monitoring rule metadata for traceability |

### Prometheus alerting rule template

```yaml
groups:
  - name: slo-burn-rate
    rules:
      - alert: <SLO-id>_BurnRateCritical
        expr: |
          (
            sum(rate(http_requests_total{status=~"5..",service="<service>"}[5m]))
            / sum(rate(http_requests_total{service="<service>"}[5m]))
          ) > (14.4 * <error_budget>)
          and
          (
            sum(rate(http_requests_total{status=~"5..",service="<service>"}[1h]))
            / sum(rate(http_requests_total{service="<service>"}[1h]))
          ) > (14.4 * <error_budget>)
        for: 2m
        labels:
          severity: critical
          slo: <SLO-id>
        annotations:
          summary: "SLO {{ $labels.slo }} burn rate critical (14.4x)"
          runbook_url: "<link to runbook>"
```

Generate equivalent rules for Datadog, CloudWatch, or other platforms based on `ARCH-TECH-*.choice` in the observability category.

## Multi-window burn-rate alerting

To avoid alert fatigue, every alerting rule must use the multi-window approach:

1. **Both windows must fire simultaneously** before the alert triggers. This prevents:
   - False positives from one-off spikes (fast window fires, slow does not)
   - Stale alerts from recovered incidents (slow window fires, fast does not)

2. Generate rules for at minimum two tiers:
   - **Critical** (5m/1h, 14.4x burn rate) — pages the on-call engineer
   - **High** (30m/6h, 6x burn rate) — creates an urgent ticket

3. Optional tiers for completeness:
   - **Medium** (2h/1d, 3x burn rate) — ticket, investigate during business hours
   - **Low** (6h/3d, 1x burn rate) — informational, budget tracking

## RED metrics per service

For every `ARCH-COMP-*` with `type: service` or `type: gateway`, generate RED (Rate, Errors, Duration) metrics:

| Metric | PromQL expression | Purpose |
|---|---|---|
| **Rate** | `rate(http_requests_total{service="<name>"}[5m])` | Request throughput — capacity indicator |
| **Errors** | `rate(http_requests_total{status=~"5..",service="<name>"}[5m])` | Error rate — reliability indicator |
| **Duration** | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="<name>"}[5m]))` | Latency p99 — performance indicator |

## USE metrics per resource

For every infrastructure resource provisioned by IaC (compute, database, cache, queue), generate USE (Utilization, Saturation, Errors) metrics:

| Resource type | Utilization | Saturation | Errors |
|---|---|---|---|
| **Compute** (CPU) | `container_cpu_usage_seconds_total / container_spec_cpu_quota` | CPU throttling count | OOM kills |
| **Memory** | `container_memory_usage_bytes / container_spec_memory_limit_bytes` | Memory swap usage | OOM events |
| **Database** | Connection pool utilization | Query queue depth | Connection errors, slow query count |
| **Cache** | Memory used / max memory | Eviction rate | Connection errors, miss rate |
| **Queue** | Messages in flight / max capacity | Queue depth growth rate | Dead letter queue count |

## Dashboard generation

Generate dashboard definitions in JSON format compatible with the target monitoring platform:

### Grafana JSON structure

```json
{
  "dashboard": {
    "title": "<Service> Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "targets": [{"expr": "rate(http_requests_total{service='<name>'}[5m])"}]
      },
      {
        "title": "Error Rate",
        "type": "timeseries",
        "targets": [{"expr": "rate(http_requests_total{status=~'5..',service='<name>'}[5m])"}]
      },
      {
        "title": "Latency (p99)",
        "type": "timeseries",
        "targets": [{"expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service='<name>'}[5m]))"}]
      },
      {
        "title": "SLO Error Budget",
        "type": "gauge",
        "targets": [{"expr": "<error_budget_remaining_expression>"}]
      }
    ]
  }
}
```

Generate dashboards for:

1. **Service overview** — one per `ARCH-COMP-*` service, with RED metrics and SLO burn rate
2. **Infrastructure overview** — USE metrics for all provisioned resources
3. **SLO summary** — error budget burn-down across all SLOs
4. **Deployment** — deployment frequency, lead time, change failure rate, recovery time (DORA metrics where measurable)

## Strategy-aware monitoring

The deployment method from Stage 4 drives additional monitoring requirements:

| Deployment method | Additional monitoring |
|---|---|
| **Canary** | Canary-vs-baseline comparison dashboard panel. Metrics split by `version` label. Alert if canary error rate exceeds baseline by more than the burn-rate threshold. |
| **Blue-green** | Health monitoring for both blue and green environments simultaneously. Alert if the standby environment becomes unhealthy. |
| **Rolling** | Track the percentage of instances running the new version. Alert if rollout stalls (no progress for > 10 minutes). |
| **Recreate** | Downtime window monitoring. Alert if actual downtime exceeds expected window. |

## Distributed tracing configuration

Derive tracing spans from `ARCH-DIAG-*` sequence diagrams:

1. Each inter-component call in a sequence diagram becomes a **trace span** with:
   - `span.name`: `<source_component>.<operation>` (e.g. `api-service.getUser`)
   - `span.kind`: `CLIENT` on the caller, `SERVER` on the callee
   - `span.attributes`: service name, deployment environment, version

2. Configure sampling rate based on traffic volume:
   - High traffic (> 1000 rps): 1–10% sampling
   - Medium traffic (100–1000 rps): 10–50% sampling
   - Low traffic (< 100 rps): 100% sampling

3. Propagation format: W3C Trace Context (default) unless Arch specifies otherwise.

```yaml
tracing_config:
  sampling_rate: 0.1
  propagation: w3c
  span_attributes:
    - key: service.name
      source: env
    - key: deployment.environment
      source: env
    - key: service.version
      source: env
```

## Report output

The subagent writes its output to the report file allocated by the main agent. The report body contains:

1. **Monitoring rules** — full alerting rule definitions (Prometheus YAML, Datadog JSON, or equivalent) for all SLO burn-rate tiers and strategy-aware alerts.
2. **Dashboard definitions** — Grafana JSON or Datadog JSON for all dashboards.
3. **Tracing configuration** — sampling, propagation, and span attribute config.
4. **RED/USE metric definitions** — per-service and per-resource metric expressions.

The main agent reads the report and merges the content into the `DEVOPS-OBS-*` artifact's `.md` file, filling the `monitoring_rules`, `dashboards`, and `tracing_config` sections.

### Report frontmatter

```yaml
---
report_id: <assigned by main agent>
kind: monitor
skill: devops
stage: monitor
created_at: <timestamp>
target_refs:
  - DEVOPS-OBS-001
verdict: pass | at_risk | fail
summary: "<one-line summary of what was generated>"
proposed_meta_ops:
  - cmd: set-progress
    artifact_id: DEVOPS-OBS-001
    completed: 3
    total: 4
items:
  - id: 1
    severity: info
    classification: content_draft
    message: "<description of generated content>"
---
```

Valid `classification` values for this stage: `content_draft`, `slo_gap`, `strategy_mismatch`.

- `content_draft` — normal content generation output
- `slo_gap` — an SLO has no corresponding monitoring rule (should not happen if Stage 1 was complete)
- `strategy_mismatch` — the deployment strategy requires monitoring that the current config cannot support

## Escalation conditions

Escalate (via report `verdict: fail` and `classification: strategy_mismatch`) when:

- The monitoring platform specified in `ARCH-TECH-*` does not support multi-window alerting (e.g. basic CloudWatch alarms cannot express "both windows must fire"). Propose alternatives or workarounds.
- The SLO definitions reference metrics that are not emittable by the application's framework (e.g. no histogram support in the chosen metrics library). Propose instrumentation changes.

Do **not** escalate for:

- Dashboard layout and panel arrangement decisions.
- Choosing between recording rules and raw queries for alerting (prefer recording rules for performance).
- Sampling rate selection (use the guidelines above).
