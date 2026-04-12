# Workflow — Stage 6: Logging (subagent)

## Role

Generate logging standards, structured log format configuration, correlation ID propagation rules, sensitive data masking policies, and retention policies from the Arch component topology and RE regulatory constraints. This stage is executed by a **subagent** — it does not call `${SKILL_DIR}/scripts/artifact.py` directly. Instead, it writes a report file at the path allocated by the main agent, and the main agent merges the report body into the Observability artifact (`DEVOPS-OBS-*`).

See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full subagent protocol.

> **Metadata reminder**: All metadata operations are handled by the main agent via `${SKILL_DIR}/scripts/artifact.py`. Subagents express metadata changes through `proposed_meta_ops` in their report frontmatter. `.meta.yaml` files must never be edited directly — not by the main agent, not by subagents.

## Inputs

- **ARCH-COMP-\*** — component list with `name`, `type`, `interfaces`, `dependencies`. Component names become log namespaces; dependencies inform correlation ID propagation paths.
- **RE constraints** (indirect via Arch `constraint_ref`) — regulatory constraints drive data masking requirements (PII, PCI, HIPAA) and retention policies (minimum/maximum retention periods).
- **Security requirements** — derived from RE constraints and downstream security skill expectations (see [../contracts/downstream-contract.md](../contracts/downstream-contract.md)). Determine what fields must be masked and which log levels are appropriate per environment.
- **ARCH-DIAG-\*** — sequence diagrams identify inter-service call chains where correlation IDs must propagate.
- **IMPL-IDR-\*** (optional) — implementation decisions that specify logging frameworks or patterns (e.g. structured logging with pino, structlog, serilog).

## Structured log format

All services must emit logs in JSON format with the following mandatory fields:

```json
{
  "timestamp": "2026-04-12T10:00:00.000Z",
  "level": "info",
  "service": "api-service",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "message": "Request processed successfully",
  "context": {
    "request_id": "req-abc-123",
    "user_id": "usr-456",
    "method": "GET",
    "path": "/api/users/456",
    "status_code": 200,
    "duration_ms": 42
  }
}
```

### Field definitions

| Field | Type | Required | Description |
|---|---|---|---|
| `timestamp` | ISO 8601 UTC | yes | Time the log event occurred. Millisecond precision minimum. |
| `level` | enum | yes | One of `trace`, `debug`, `info`, `warn`, `error`, `fatal`. |
| `service` | string | yes | Service name from `ARCH-COMP-*.name`. |
| `trace_id` | string | conditional | W3C Trace Context trace ID. Required when tracing is configured. |
| `span_id` | string | conditional | W3C Trace Context span ID. Required when tracing is configured. |
| `message` | string | yes | Human-readable description of the event. |
| `context` | object | optional | Structured key-value pairs with request-specific context. |

### Additional recommended fields

| Field | When to include |
|---|---|
| `error.type` | On `error` or `fatal` level — exception class name |
| `error.message` | On `error` or `fatal` level — exception message |
| `error.stack` | On `error` or `fatal` level — stack trace (truncated to 5000 chars) |
| `deployment.environment` | Always — `dev`, `staging`, `production` |
| `deployment.version` | Always — git SHA or semantic version |

## Per-service log namespaces

Derive one log namespace per `ARCH-COMP-*` entry:

| ARCH-COMP name | Log namespace | Purpose |
|---|---|---|
| `api-gateway` | `app.api-gateway` | Gateway access logs, rate limiting events |
| `user-service` | `app.user-service` | Business logic logs for user operations |
| `order-service` | `app.order-service` | Business logic logs for order operations |
| `<component-name>` | `app.<component-name>` | Scoped logging for the component |

Namespace prefixes enable log routing and filtering. Infrastructure logs (from the platform itself) use the `infra.*` prefix to distinguish from application logs.

## Correlation ID propagation

Correlation IDs enable tracing a single user request across all services it touches. Configure propagation based on the Arch sequence diagrams:

### W3C Trace Context (default)

| Header | Format | Example |
|---|---|---|
| `traceparent` | `{version}-{trace-id}-{parent-id}-{trace-flags}` | `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01` |
| `tracestate` | Vendor-specific key-value pairs | `congo=t61rcWkgMzE` |

### Custom header fallback

If the application framework does not support W3C Trace Context natively, use a custom header:

| Header | Format | Propagation rule |
|---|---|---|
| `X-Request-ID` | UUID v4 | Generate at the gateway if not present; forward through all downstream calls |
| `X-Correlation-ID` | UUID v4 | Alias for `X-Request-ID` for legacy system compatibility |

### Propagation rules

1. The **entry-point component** (gateway or first service to receive the external request) generates the correlation ID if none is present in the incoming request.
2. Every **downstream call** includes the correlation ID in the request header.
3. Every **log line** includes the correlation ID in the `trace_id` field (or `context.request_id` if using the custom header approach).
4. Every **async message** (queue, event bus) includes the correlation ID in the message metadata/attributes.
5. The trace ID is propagated across all components in the `ARCH-DIAG-*.sequence` call chains.

## Sensitive data masking rules

Derive masking rules from RE regulatory constraints and security requirements:

| Constraint type | Fields to mask | Masking strategy |
|---|---|---|
| PII (GDPR, CCPA) | `*.email`, `*.phone`, `*.address`, `*.name` (when in log context) | `redact` — replace with `[REDACTED]` |
| PCI-DSS | `*.card_number`, `*.cvv`, `*.expiry` | `redact` — replace with `[REDACTED]` |
| Authentication | `*.password`, `*.token`, `*.api_key`, `*.secret` | `redact` — replace with `[REDACTED]` |
| HIPAA | `*.ssn`, `*.medical_record`, `*.diagnosis` | `hash` — one-way hash for correlation without exposure |
| General security | `*.authorization` header values | `redact` — replace with `[REDACTED]` |

### Masking configuration

```yaml
masking_rules:
  - field_pattern: "*.password"
    strategy: redact
  - field_pattern: "*.token"
    strategy: redact
  - field_pattern: "*.api_key"
    strategy: redact
  - field_pattern: "*.ssn"
    strategy: hash
  - field_pattern: "*.card_number"
    strategy: redact
  - field_pattern: "context.email"
    strategy: redact
```

Masking must be applied **at the point of log emission**, not after the fact. Log libraries must be configured to intercept and mask before writing to any transport (stdout, file, network).

## Log level guidelines per environment

| Level | `dev` | `staging` | `production` | When to use |
|---|---|---|---|---|
| `trace` | on | off | off | Detailed debugging (method entry/exit, variable values) |
| `debug` | on | on | off | Diagnostic information useful for troubleshooting |
| `info` | on | on | on | Normal operational events (request processed, job completed) |
| `warn` | on | on | on | Unexpected but recoverable conditions (retry triggered, cache miss fallback) |
| `error` | on | on | on | Failures that need investigation (unhandled exceptions, external service errors) |
| `fatal` | on | on | on | Process-terminating failures |

Default log level per environment:

```yaml
level_default: info
level_overrides:
  dev: debug
  staging: info
  production: info
```

## Retention and rotation policy

Derive retention periods from RE regulatory constraints. If no constraint specifies a retention period, use these defaults:

| Tier | Retention period | Storage type | Purpose |
|---|---|---|---|
| **Hot** | 7 days | Primary log store (Elasticsearch, CloudWatch Logs, Loki) | Active investigation and dashboards |
| **Warm** | 30 days | Reduced-cost storage (S3 Infrequent Access, GCS Nearline) | Recent incident investigation |
| **Archive** | 365 days (or per compliance requirement) | Cold storage (S3 Glacier, GCS Coldline) | Audit trail, compliance |

```yaml
retention:
  hot_days: 7
  warm_days: 30
  archive_days: 365
```

**Compliance override**: if RE constraints specify a minimum retention period (e.g. "retain financial transaction logs for 7 years"), the archive tier must satisfy that requirement. Record the constraint reference.

**Rotation**: log files (if written to disk) rotate at 100MB or daily, whichever comes first. Rotated files move to the warm tier after the hot retention period expires.

## Log-based metrics

Logs feed back into monitoring (Stage 5) through log-based metrics. Define these to bridge logging and alerting. When `monitor` and `log` run in parallel, treat these metrics as supplemental inputs that the main agent reconciles into the final Observability artifact after both reports return:

| Log pattern | Derived metric | Feeds into |
|---|---|---|
| `level == "error"` count per service per 5m window | `log_errors_total{service="<name>"}` | Error rate monitoring, SLO burn-rate (when no native metrics exist) |
| `level == "error" && error.type == "TimeoutException"` | `log_timeout_errors_total{service="<name>"}` | Dependency health monitoring |
| `duration_ms > <SLO latency threshold>` | `log_slow_requests_total{service="<name>"}` | Latency SLO monitoring (fallback) |
| `level == "fatal"` count per service | `log_fatal_total{service="<name>"}` | Critical alerting, incident detection |

These metrics are used by monitoring rules of `type: log` in the Observability artifact schema.

## Report output

The subagent writes its output to the report file allocated by the main agent. The report body contains:

1. **Structured log format specification** — JSON schema with mandatory and optional fields
2. **Per-service log namespace table** — derived from ARCH-COMP names
3. **Correlation ID propagation configuration** — headers, generation rules, and propagation paths
4. **Masking rules** — field patterns and strategies, with constraint references
5. **Log level configuration** — per-environment defaults and overrides
6. **Retention policy** — hot/warm/archive tiers with durations and compliance justification
7. **Log-based metric definitions** — patterns and derived metric names

The main agent reads the report and merges the content into the `DEVOPS-OBS-*` artifact's `.md` file, filling the `logging_config` section.

### Report frontmatter

```yaml
---
report_id: <assigned by main agent>
kind: log
skill: devops
stage: log
created_at: <timestamp>
target_refs:
  - DEVOPS-OBS-001
verdict: pass | at_risk | fail
summary: "<one-line summary of what was generated>"
proposed_meta_ops:
  - cmd: set-progress
    artifact_id: DEVOPS-OBS-001
    completed: 4
    total: 4
items:
  - id: 1
    severity: info
    classification: content_draft
    message: "<description of generated content>"
---
```

Valid `classification` values for this stage: `content_draft`, `compliance_gap`, `masking_gap`.

- `content_draft` — normal content generation output
- `compliance_gap` — RE constraint requires a retention period or audit capability that the proposed config does not satisfy
- `masking_gap` — a field that should be masked based on RE/security constraints is not covered by masking rules

## Escalation conditions

Escalate (via report `verdict: fail` and appropriate classification) when:

- An RE **compliance constraint requires log retention** that exceeds the storage capacity or cost budget (e.g. "retain all logs for 10 years" with no archive tier budget). Flag as `compliance_gap`.
- The **logging framework specified in IMPL-IDR does not support structured JSON output** natively, requiring a custom formatter that may not preserve all required fields. Flag as `compliance_gap` with a recommendation.
- **Masking requirements conflict with debugging needs** — e.g. a field needed for incident diagnosis is also subject to PII masking. Propose solutions: masked in production, unmasked in dev/staging; or use hashed values that allow correlation without exposure. Flag as `masking_gap`.

Do **not** escalate for:

- Choosing between logging libraries (follow IMPL-IDR or Arch tech stack choice).
- Log format details beyond the mandatory fields (the structured format above is the standard).
- Rotation thresholds (use the defaults above).
