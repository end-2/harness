# DEVOPS-OBS-001 — Observability (Todo API, light mode)

**Phase**: approved · **Mode**: light

Single-service TODO API. Three core SLOs, basic alerting, one dashboard, structured logging. No distributed tracing (single service, no cross-service calls).

## SLO Definitions

### SLO-001: Availability

| Field | Value |
|-------|-------|
| SLI | `1 - (sum(rate(http_requests_total{service="todo-api",status=~"5.."}[5m])) / sum(rate(http_requests_total{service="todo-api"}[5m])))` |
| Target | 99.5% |
| Window | 30d rolling |
| Error budget | 0.5% (3.6 hours/month) |

**Burn-rate alert**: fast window 5m, slow window 1h, threshold 14.4x (critical tier only).

### SLO-002: Latency

| Field | Value |
|-------|-------|
| SLI | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="todo-api"}[5m]))` |
| Target | p99 < 500ms |
| Window | 30d rolling |
| Error budget | 0.5% of requests may exceed 500ms |

**Burn-rate alert**: fast window 5m, slow window 1h, threshold 14.4x (critical tier only).

### SLO-003: Error Rate

| Field | Value |
|-------|-------|
| SLI | `sum(rate(http_requests_total{service="todo-api",status=~"5.."}[5m])) / sum(rate(http_requests_total{service="todo-api"}[5m]))` |
| Target | < 1% |
| Window | 30d rolling |
| Error budget | 1% of total requests |

**Burn-rate alert**: fast window 5m, slow window 1h, threshold 14.4x (critical tier only).

## Monitoring Rules

| Rule ID | Type | Condition | Severity | Channel | SLO ref |
|---------|------|-----------|----------|---------|---------|
| MON-001 | metric | availability burn rate > 14.4x over 5m AND 1h | critical | pagerduty | SLO-001 |
| MON-002 | metric | p99 latency > 500ms sustained over 5m AND 1h | critical | pagerduty | SLO-002 |
| MON-003 | metric | error rate burn rate > 14.4x over 5m AND 1h | critical | pagerduty | SLO-003 |

Light mode uses only the critical tier. No ticket or log-level alerts.

## Dashboard

### DASH-001: Todo API Overview

Single Grafana dashboard with the following panels:

| Panel | Query | Visualization |
|-------|-------|---------------|
| Request Rate | `rate(http_requests_total{service="todo-api"}[5m])` | timeseries |
| Error Rate | `rate(http_requests_total{service="todo-api",status=~"5.."}[5m]) / rate(http_requests_total{service="todo-api"}[5m])` | timeseries |
| Latency p99 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="todo-api"}[5m]))` | timeseries |
| Error Budget Remaining | `1 - (slo:error_budget_consumed:ratio{slo="SLO-001"})` | gauge |

Format: grafana-json

## Logging Configuration

| Field | Value |
|-------|-------|
| Format | JSON structured |
| Default level | info |
| Correlation ID | `X-Request-ID` header (passed through, no cross-service propagation) |
| Retention: hot | 7 days |
| Retention: warm | 30 days |
| Retention: archive | 90 days |

No PII masking rules needed — the TODO API stores only task titles and completion status. No sensitive user data flows through log output.

## Tracing

Not applicable. Single-service architecture has no cross-service call chains. Request correlation is handled by the `X-Request-ID` header in structured logs.

## Upstream Refs

ARCH-COMP-001, IMPL-CODE-001
