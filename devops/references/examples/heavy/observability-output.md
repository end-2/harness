# DEVOPS-OBS-001 — Observability (E-Commerce Platform, heavy mode)

**Phase**: approved · **Mode**: heavy

Multi-service e-commerce platform: api-gateway, order-service, payment-service, inventory-service. Comprehensive SLOs per service, multi-window burn-rate alerts, RED/USE metrics, distributed tracing, and structured logging with correlation IDs and PII masking.

## SLO Definitions

### Gateway SLOs

#### SLO-001: Gateway Availability

| Field | Value |
|-------|-------|
| SLI | `1 - (sum(rate(http_requests_total{service="api-gateway",status=~"5.."}[5m])) / sum(rate(http_requests_total{service="api-gateway"}[5m])))` |
| Target | 99.9% |
| Window | 30d rolling |
| Error budget | 0.1% (43.2 min/month) |

Burn-rate alerts:

| Tier | Fast window | Slow window | Threshold | Action |
|------|-------------|-------------|-----------|--------|
| critical | 5m | 1h | 14.4x | page on-call SRE |
| high | 30m | 6h | 6x | page within 1 hour |
| medium | 2h | 1d | 3x | create ticket |

#### SLO-002: Gateway Latency

| Field | Value |
|-------|-------|
| SLI | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="api-gateway"}[5m]))` |
| Target | p99 < 300ms |
| Window | 30d rolling |
| Error budget | 0.1% of requests may exceed 300ms |

Burn-rate alerts: same tier structure as SLO-001.

### Order Service SLOs

#### SLO-003: Order Processing Availability

| Field | Value |
|-------|-------|
| SLI | `1 - (sum(rate(grpc_server_handled_total{grpc_service="order.OrderService",grpc_code!="OK"}[5m])) / sum(rate(grpc_server_handled_total{grpc_service="order.OrderService"}[5m])))` |
| Target | 99.9% |
| Window | 30d rolling |
| Error budget | 0.1% |

#### SLO-004: Order Processing Latency

| Field | Value |
|-------|-------|
| SLI | `histogram_quantile(0.99, rate(grpc_server_handling_seconds_bucket{grpc_service="order.OrderService"}[5m]))` |
| Target | p99 < 500ms |
| Window | 30d rolling |
| Error budget | 0.1% of requests may exceed 500ms |

### Payment Service SLOs

#### SLO-005: Payment Success Rate

| Field | Value |
|-------|-------|
| SLI | `1 - (sum(rate(payment_transactions_total{status="failed"}[5m])) / sum(rate(payment_transactions_total[5m])))` |
| Target | 99.95% |
| Window | 30d rolling |
| Error budget | 0.05% (tightest SLO — payment failures have direct revenue impact) |

#### SLO-006: Payment Latency

| Field | Value |
|-------|-------|
| SLI | `histogram_quantile(0.99, rate(payment_processing_duration_seconds_bucket[5m]))` |
| Target | p99 < 2000ms |
| Window | 30d rolling |
| Error budget | 0.1% (2s ceiling accounts for external provider round-trip) |

### Inventory Service SLOs

#### SLO-007: Inventory Query Availability

| Field | Value |
|-------|-------|
| SLI | `1 - (sum(rate(grpc_server_handled_total{grpc_service="inventory.InventoryService",grpc_code!="OK"}[5m])) / sum(rate(grpc_server_handled_total{grpc_service="inventory.InventoryService"}[5m])))` |
| Target | 99.9% |
| Window | 30d rolling |
| Error budget | 0.1% |

#### SLO-008: Inventory Data Freshness

| Field | Value |
|-------|-------|
| SLI | `time() - inventory_last_sync_timestamp` |
| Target | < 30s staleness |
| Window | 30d rolling |
| Error budget | 0.1% of time may exceed 30s lag |

## Monitoring Rules

### Critical Tier (Page)

| Rule ID | Type | Condition | Severity | Channel | SLO ref |
|---------|------|-----------|----------|---------|---------|
| MON-001 | metric | gateway availability burn rate > 14.4x (5m/1h) | critical | pagerduty | SLO-001 |
| MON-002 | metric | gateway latency burn rate > 14.4x (5m/1h) | critical | pagerduty | SLO-002 |
| MON-003 | metric | order availability burn rate > 14.4x (5m/1h) | critical | pagerduty | SLO-003 |
| MON-004 | metric | order latency burn rate > 14.4x (5m/1h) | critical | pagerduty | SLO-004 |
| MON-005 | metric | payment success rate burn rate > 14.4x (5m/1h) | critical | pagerduty | SLO-005 |
| MON-006 | metric | payment latency burn rate > 14.4x (5m/1h) | critical | pagerduty | SLO-006 |
| MON-007 | metric | inventory availability burn rate > 14.4x (5m/1h) | critical | pagerduty | SLO-007 |
| MON-008 | metric | inventory freshness burn rate > 14.4x (5m/1h) | critical | pagerduty | SLO-008 |

### High Tier (Page within 1h)

| Rule ID | Type | Condition | Severity | Channel | SLO ref |
|---------|------|-----------|----------|---------|---------|
| MON-009 | metric | gateway availability burn rate > 6x (30m/6h) | high | pagerduty | SLO-001 |
| MON-010 | metric | payment success rate burn rate > 6x (30m/6h) | high | pagerduty | SLO-005 |

### Medium Tier (Ticket)

| Rule ID | Type | Condition | Severity | Channel | SLO ref |
|---------|------|-----------|----------|---------|---------|
| MON-011 | metric | any service availability burn rate > 3x (2h/1d) | medium | jira | SLO-001..SLO-007 |
| MON-012 | metric | any service latency burn rate > 3x (2h/1d) | medium | jira | SLO-002, SLO-004, SLO-006 |

### Infrastructure Alerts

| Rule ID | Type | Condition | Severity | Channel |
|---------|------|-----------|----------|---------|
| MON-013 | metric | CPU utilization > 80% sustained 10m | high | slack:#infra-alerts |
| MON-014 | metric | Memory utilization > 85% sustained 10m | high | slack:#infra-alerts |
| MON-015 | metric | Disk usage > 80% | medium | jira |
| MON-016 | metric | Pod restart count > 3 in 15m | high | pagerduty |

## Dashboards

### DASH-001: Service Overview

Top-level dashboard showing all four services at a glance.

| Panel | Query | Visualization |
|-------|-------|---------------|
| Request Rate (all services) | `sum by (service)(rate(http_requests_total[5m]))` | timeseries |
| Error Rate (all services) | `sum by (service)(rate(http_requests_total{status=~"5.."}[5m])) / sum by (service)(rate(http_requests_total[5m]))` | timeseries |
| Latency p99 (all services) | `histogram_quantile(0.99, sum by (service, le)(rate(http_request_duration_seconds_bucket[5m])))` | timeseries |
| Active Requests | `sum by (service)(http_requests_in_flight)` | stat |
| Pod Status | `kube_pod_status_phase{namespace="production"}` | table |

Format: grafana-json

### DASH-002: SLO Dashboard

Dedicated SLO tracking dashboard.

| Panel | Query | Visualization |
|-------|-------|---------------|
| Error Budget Remaining (per SLO) | `1 - slo:error_budget_consumed:ratio` by SLO label | gauge (green/yellow/red) |
| Burn Rate (per SLO) | `slo:burn_rate:5m` by SLO label | timeseries |
| Budget Consumption Trend | `slo:error_budget_consumed:ratio` over 30d | timeseries |
| SLO Compliance Table | current target vs actual per SLO | table |

Format: grafana-json

### DASH-003: Infrastructure

Kubernetes and AWS resource metrics.

| Panel | Query | Visualization |
|-------|-------|---------------|
| CPU Utilization | `rate(container_cpu_usage_seconds_total[5m])` by pod | timeseries |
| Memory Usage | `container_memory_working_set_bytes` by pod | timeseries |
| Network I/O | `rate(container_network_receive_bytes_total[5m])` by pod | timeseries |
| Disk I/O | `rate(container_fs_reads_bytes_total[5m])` by pod | timeseries |
| HPA Status | `kube_horizontalpodautoscaler_status_current_replicas` | stat |
| Node Allocatable vs Requested | CPU and memory capacity vs requests | bar gauge |

Format: grafana-json

### DASH-004: Payment Service Deep Dive

Payment-specific operational dashboard.

| Panel | Query | Visualization |
|-------|-------|---------------|
| Transaction Rate | `rate(payment_transactions_total[5m])` by status | timeseries |
| Provider Response Time | `histogram_quantile(0.99, rate(payment_provider_duration_seconds_bucket[5m]))` | timeseries |
| Circuit Breaker State | `payment_circuit_breaker_state` | stat (open/closed/half-open) |
| Retry Rate | `rate(payment_retries_total[5m])` | timeseries |
| Revenue Impact (failed payments) | `sum(rate(payment_transactions_total{status="failed"}[5m])) * avg(payment_amount)` | stat |

Format: grafana-json

## RED Metrics per Service

Each service exposes the RED (Rate, Errors, Duration) metrics:

| Service | Rate metric | Error metric | Duration metric |
|---------|------------|--------------|-----------------|
| api-gateway | `http_requests_total` | `http_requests_total{status=~"5.."}` | `http_request_duration_seconds` |
| order-service | `grpc_server_handled_total` | `grpc_server_handled_total{grpc_code!="OK"}` | `grpc_server_handling_seconds` |
| payment-service | `payment_transactions_total` | `payment_transactions_total{status="failed"}` | `payment_processing_duration_seconds` |
| inventory-service | `grpc_server_handled_total` | `grpc_server_handled_total{grpc_code!="OK"}` | `grpc_server_handling_seconds` |

## USE Metrics per Resource

| Resource | Utilization | Saturation | Errors |
|----------|------------|------------|--------|
| CPU | `rate(container_cpu_usage_seconds_total[5m])` | `container_cpu_cfs_throttled_seconds_total` | n/a |
| Memory | `container_memory_working_set_bytes` | `container_memory_oom_total` | OOM kills |
| Network | `rate(container_network_receive_bytes_total[5m])` | `container_network_receive_packets_dropped_total` | `container_network_receive_errors_total` |
| Disk | `rate(container_fs_reads_bytes_total[5m])` | `container_fs_io_time_weighted_seconds_total` | `container_fs_io_error_total` |
| DB connections | `pg_stat_activity_count / pg_settings_max_connections` | `pg_stat_activity_waiting` | `pg_stat_activity_state{state="idle in transaction"}` |

## Distributed Tracing

| Field | Value |
|-------|-------|
| Backend | Jaeger (OTLP collector) |
| Propagation | W3C Trace Context (`traceparent` header) |
| Sampling rate | 10% (production), 100% (staging) |
| Exporter | OpenTelemetry SDK → OTLP gRPC → Jaeger collector |

### Span Attributes

| Attribute | Source | Description |
|-----------|--------|-------------|
| `service.name` | env `OTEL_SERVICE_NAME` | Identifies the service |
| `service.version` | env `APP_VERSION` (commit SHA) | Deployed version |
| `deployment.environment` | env `DEPLOY_ENV` | production / staging / dev |
| `http.method` | instrumentation | GET, POST, etc. |
| `http.status_code` | instrumentation | Response status |
| `http.route` | instrumentation | URL path pattern |
| `db.system` | instrumentation | postgresql, redis |
| `db.statement` | instrumentation (sanitized) | Query pattern without values |

### Critical Trace Paths

| Path | Services involved | Purpose |
|------|-------------------|---------|
| Place order | api-gateway → order-service → payment-service → inventory-service | End-to-end order flow |
| Payment retry | order-service → payment-service (retry loop) | Idempotency verification |
| Inventory check | api-gateway → inventory-service | Stock availability query |

## Logging Configuration

| Field | Value |
|-------|-------|
| Format | JSON structured |
| Default level | info (production), debug (staging) |
| Framework | OpenTelemetry log bridge |

### Correlation ID Propagation

All log entries include:
- `trace_id`: from W3C Trace Context
- `span_id`: current span
- `request_id`: from `X-Request-ID` header (generated at api-gateway if absent)

This allows joining logs across services for a single request.

### PII Masking Rules

| Field pattern | Strategy | Rationale |
|--------------|----------|-----------|
| `*.email` | hash (SHA-256) | GDPR — personal data |
| `*.phone` | redact | GDPR — personal data |
| `*.card_number` | redact | PCI-DSS — cardholder data must never appear in logs |
| `*.cvv` | redact | PCI-DSS |
| `*.password` | redact | Security best practice |
| `*.ssn` | redact | Regulatory compliance |
| `*.address` | hash (SHA-256) | GDPR — personal data |

### Retention Policy

| Tier | Duration | Storage | Purpose |
|------|----------|---------|---------|
| Hot | 7 days | Elasticsearch | Active investigation and search |
| Warm | 30 days | S3 (compressed) | Recent incident review |
| Archive | 365 days | S3 Glacier | Compliance and audit |

Retention aligns with PCI-DSS requirement for 1-year audit trail on payment-related logs.

### Log-Based Metrics

Logs feed recording rules that generate Prometheus metrics for conditions not easily captured by application instrumentation:

| Metric | Log condition | Purpose |
|--------|--------------|---------|
| `payment_provider_timeout_total` | log level=error, message contains "provider timeout" | Tracks provider reliability without code instrumentation |
| `auth_failure_total` | log level=warn, message contains "authentication failed" | Feeds into security monitoring |
| `db_connection_pool_exhausted_total` | log level=error, message contains "connection pool exhausted" | Feeds MON-015 infrastructure alert |

## Upstream Refs

ARCH-COMP-001, ARCH-COMP-002, ARCH-COMP-003, ARCH-COMP-004, ARCH-DEC-001, IMPL-CODE-001
