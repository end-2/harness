# Instrument — Instrumentation Verification Stage

**Role**: Verify that application code has the observability instrumentation needed for meaningful verification, and propose minimal additions if gaps exist.

**Runs in**: main agent (may suggest code changes requiring user approval).

## Entry conditions

- `provision` stage completed — Environment Setup artifact exists.
- Application source code is accessible.

## What to check

The observability stack is only useful if the application emits the right signals. This stage verifies three axes:

### 1. Metrics endpoint

Check that each application service exposes a Prometheus-compatible metrics endpoint.

- **Where to look**: search for metrics middleware/library in the source code.
  - Python: `prometheus_client`, `prometheus_fastapi_instrumentator`
  - Node.js: `prom-client`, `express-prometheus-middleware`
  - Go: `prometheus/client_golang`, `promhttp`
  - Java/Kotlin: `micrometer-registry-prometheus`, Spring Actuator `/actuator/prometheus`
- **What to confirm**: the endpoint (typically `/metrics`) is reachable and returns Prometheus text format.
- **Gap indicator**: no metrics library in dependencies, no `/metrics` route.

### 2. Structured logging

Check that logs are emitted in a structured format (JSON) with required fields.

- **Where to look**: logging configuration in the source.
  - Python: `structlog`, `python-json-logger`
  - Node.js: `pino`, `winston` with JSON format
  - Go: `zap`, `zerolog`
  - Java/Kotlin: Logback JSON encoder, `log4j2` JSON layout
- **What to confirm**: log output is JSON, includes `timestamp`, `level`, `message`, and `correlation_id` (if `DEVOPS-OBS-*.logging_config.correlation_id` is set).
- **Gap indicator**: plain text logging, no correlation ID propagation.

### 3. Trace propagation

Check that distributed tracing headers are propagated between services (heavy mode primarily, but basic check in light mode too).

- **Where to look**: OpenTelemetry SDK or framework-specific tracing.
  - `opentelemetry-api`, `opentelemetry-sdk`, `@opentelemetry/api`
  - Framework auto-instrumentation packages
- **What to confirm**: W3C Trace Context headers (`traceparent`, `tracestate`) are propagated in outgoing HTTP calls.
- **Gap indicator**: no tracing dependency, no trace context propagation in HTTP client configuration.

## Determining the right libraries

Use `ARCH-TECH-*.choice` to select the appropriate instrumentation approach:

| Technology | Metrics | Logging | Tracing |
|-----------|---------|---------|---------|
| Python (FastAPI/Flask) | prometheus_client | structlog | opentelemetry-instrumentation-fastapi |
| Node.js (Express/NestJS) | prom-client | pino | @opentelemetry/instrumentation-http |
| Go (net/http, Gin) | prometheus/client_golang | zap / zerolog | go.opentelemetry.io/otel |
| Java (Spring Boot) | micrometer-registry-prometheus | logback JSON | opentelemetry-javaagent |

## Handling gaps

When instrumentation is missing:

1. **Report the gap** in the Environment Setup artifact's instrumentation status.
2. **Propose a minimal fix** — the smallest change that enables the verification scenario:
   - Add the dependency to the manifest.
   - Add middleware/configuration.
   - Wire the exporter to the observability stack.
3. **Present to the user** for approval before making any code changes.
4. **Update the compose file** if needed (e.g., add environment variables for OTLP endpoint).

The goal is minimal invasion — enough to make verification scenarios work, not a full production instrumentation overhaul.

## Output

Update the Environment Setup artifact (`VERIFY-ENV-*`):

- Fill in the `instrumentation_status` section (metrics_endpoint, structured_logging, trace_propagation, gaps).
- If changes were made, update the docker-compose file to reflect new environment variables or dependencies.

```bash
python ${SKILL_DIR}/scripts/artifact.py set-progress <env-id> --completed 2 --total 6
```

## Escalation conditions

- **Technology stack does not support OpenTelemetry**: some niche frameworks or very old versions may not have instrumentation libraries. Suggest alternatives or skip tracing scenarios.
- **Instrumentation requires significant code restructuring**: if adding metrics/tracing means rewriting the HTTP layer or changing the framework, escalate rather than making the change.
