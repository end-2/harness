# Workflow — Stage 1: SLI/SLO Establishment

## Role

Transform RE quality attribute metrics into concrete SLI (Service Level Indicator) and SLO (Service Level Objective) definitions. This stage is the baseline for all DevOps observability — every monitoring rule, alerting threshold, deployment strategy decision, and incident runbook ultimately traces back to an SLO established here. Without quantified SLOs, the rest of the DevOps pipeline operates on guesswork.

## Inputs

- **RE quality attributes** — accessed via Arch artifacts' `re_refs` and `constraint_ref` fields. These are the source of truth for "what good looks like" in quantitative terms.
- **ARCH-COMP-\*** — component list with `name`, `type`, `interfaces`, `dependencies`, and `re_refs`. Each component that exposes an interface to users or other services needs at least one SLO.
- **ARCH-DEC-\*** — architectural decisions. Patterns like "event-driven" or "synchronous REST" affect which SLIs are meaningful (e.g. event-driven systems need processing-lag SLIs, not just HTTP latency).
- **ARCH-DIAG-\*** — sequence and data-flow diagrams identify critical paths where end-to-end SLOs may span multiple components.

## RE metric to SLI transformation

Read [../contracts/arch-input-contract.md](../contracts/arch-input-contract.md) for the full Arch field mapping. The table below covers the most common RE metric patterns and their SLI translations.

| RE metric pattern | SLI transformation | Notes |
|---|---|---|
| `"response time < Xms"` | `http_request_duration_seconds{quantile="0.99"} < X/1000` | Use p99 unless RE specifies a different percentile. For gRPC, use `grpc_server_handling_seconds`. |
| `"availability >= X%"` | `1 - (sum(rate(http_requests_total{status=~"5.."}[window])) / sum(rate(http_requests_total[window])))` | Window must match the SLO window (typically 30d rolling). |
| `"throughput >= X rps"` | `rate(http_requests_total[5m]) >= X` | Throughput SLIs are capacity indicators; pair with a saturation metric. |
| `"error rate < X%"` | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) < X/100` | Distinguish between client errors (4xx) and server errors (5xx) — only 5xx count against availability SLOs. |
| `"data freshness < Xs"` | `time() - last_successful_sync_timestamp < X` | Common for async/event-driven data pipelines. |
| `"processing latency < Xs"` | `histogram_quantile(0.99, rate(message_processing_duration_seconds_bucket[5m])) < X` | For queue consumers and event processors. |
| Qualitative (e.g. "high performance", "reliable") | **Escalate** — propose a quantitative proxy to the user with reasoning. | See Escalation conditions below. |

### Handling qualitative RE metrics

When an RE quality attribute uses qualitative language without numbers, do **not** invent a threshold. Instead, propose a quantitative proxy with justification. Example:

- RE says: "The system must be highly available."
- Propose: "Availability SLO of 99.9% (43.8 min/month downtime budget) based on the service being user-facing and the Arch decision citing 'always-on' as a trade-off priority. Confirm or adjust."

## SLO target calculation

For each SLI, derive the SLO target:

1. **Direct mapping**: If the RE metric includes a numeric target (e.g. "99.9% availability"), use it directly.
2. **Constraint-derived**: If `constraint_ref` points to a hard constraint with a numeric bound, that bound becomes the SLO floor.
3. **Dependency-adjusted**: A composite service's SLO cannot exceed the product of its critical-path dependencies' SLOs. If service A (target 99.9%) depends on service B (target 99.9%), the composite ceiling is 99.8%. Adjust or flag.

## Error budget formula

For each SLO definition:

```
error_budget = 1 - target
```

Example: SLO target = 99.9% → error budget = 0.1% → over a 30-day window, that is 43.2 minutes of allowed downtime or the equivalent error volume.

Track error budget consumption as:

```
error_budget_remaining = 1 - (bad_events / total_events) / error_budget
```

When `error_budget_remaining < 0`, the SLO is breached.

## Multi-window burn-rate alert design

Burn rate measures how fast the error budget is being consumed relative to the SLO window. A burn rate of 1.0 means the budget will be exactly exhausted at the end of the window.

Design alerts using two windows to balance speed of detection with noise reduction:

| Alert tier | Fast window | Slow window | Burn rate threshold | Budget consumed if sustained | Use case |
|---|---|---|---|---|---|
| **Page (critical)** | 5m | 1h | 14.4x | 2% in 1h | Acute incident — immediate human response |
| **Page (high)** | 30m | 6h | 6x | 5% in 6h | Sustained degradation — needs attention within the hour |
| **Ticket (medium)** | 2h | 1d | 3x | 10% in 1d | Slow burn — create a ticket, investigate during business hours |
| **Log (low)** | 6h | 3d | 1x | 10% in 3d | Informational — budget tracking, no action required |

Both windows must fire simultaneously before the alert triggers. This prevents one-off spikes (fast fires, slow does not) and long-recovered issues (slow fires, fast does not) from paging.

For each SLO, generate at minimum the **critical** and **high** tiers. Medium and low are recommended but optional.

## Per-component SLO distribution

For multi-service architectures (identified from `ARCH-COMP-*` with multiple `type: service` or `type: gateway` entries):

1. **Identify user-facing entry points** — components of `type: gateway` or services with no inbound dependency from another internal service. These get the top-level SLO matching the RE target.
2. **Derive dependency SLOs** — for each critical-path dependency, its SLO target must be at least as tight as the parent's. Use: `dependency_target >= 1 - (1 - parent_target) / critical_path_length`.
3. **Non-critical-path services** — services reachable only through fallback paths or async channels may have relaxed SLOs. Document the rationale.
4. **Shared infrastructure** — databases, caches, and queues that serve multiple components inherit the tightest SLO among their consumers.

Record the distribution rationale in the markdown body so the review stage can verify it.

## SLO definition schema

Each SLO entry in the `observability_config.slo_definitions` block must conform to the schema in [../schemas/section-schemas.md](../schemas/section-schemas.md):

```yaml
slo_definitions:
  - id: SLO-001
    sli: "<PromQL or metric expression>"
    target: 99.9          # percentage
    window: 30d           # rolling window
    error_budget: 0.1     # = 1 - target/100, as percentage
    burn_rate_alert:
      fast_window: 5m
      slow_window: 1h
      threshold: 14.4
    re_refs: [QA:performance]
```

Every `re_refs` entry must trace to an RE quality attribute through the Arch artifact chain. Use `artifact.py link` to establish the upstream ref.

## Output sequence

All metadata operations use `${SKILL_DIR}/scripts/artifact.py`. Never edit `.meta.yaml` files directly.

1. Initialize the observability section:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py init --section observability
   ```
   This returns the new artifact id (e.g. `DEVOPS-OBS-001`).

2. Fill the `slo_definitions` portion of the paired `.md` file via Edit. Include:
   - SLI definition and PromQL/metric expression for each SLO
   - Target, window, and error budget
   - Burn-rate alert configuration (all tiers)
   - Per-component distribution rationale
   - RE metric source and transformation reasoning

3. Set progress and link upstream:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py set-progress <id> --completed 1 --total 4
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream ARCH-COMP-001
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream ARCH-DEC-001
   ```
   Link to every Arch component and decision that contributed to the SLO definitions.

4. When the SLO section is complete, transition to review:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
   ```

**Note**: This stage only fills the `slo_definitions` portion of the Observability artifact. The `monitoring_rules`, `dashboards`, `logging_config`, and `tracing_config` sections are filled by subsequent subagent stages (monitor, log). Progress should reflect this: after SLO stage, progress is typically 1/4 (SLOs defined, monitoring/dashboards/logging/tracing pending).

## Escalation conditions

Escalate to the user **only** when:

- An RE quality attribute uses **qualitative language with no quantifiable proxy** (e.g. "the system should feel fast" with no latency target and no comparable baseline). Propose a proxy with reasoning but require user confirmation.
- RE metrics are **internally contradictory** (e.g. "99.99% availability" combined with "maximum infrastructure cost of $50/month" for a multi-region service — the cost constraint makes the availability target unrealisable).
- A **hard constraint** (`constraint_ref` with enforcement level `hard`) specifies a target that exceeds the theoretical maximum given the dependency chain (e.g. a service depending on a third-party API with 99.5% SLA cannot itself guarantee 99.99%).
- The Arch component structure has **circular dependencies** that prevent topological SLO distribution.

Do **not** escalate for:

- Choosing between p95 and p99 for latency SLIs (default to p99 unless RE specifies otherwise).
- Selecting the SLO window duration (default to 30 days rolling).
- Burn-rate threshold fine-tuning (use the standard tiers above).
