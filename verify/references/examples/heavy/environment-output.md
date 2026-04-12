# Environment Setup (Heavy Mode Example)

## 1. Mode

**Heavy** — 4 Arch components (API Gateway, Auth Service, Order Service, Notification Worker), multi-service with async messaging.

## 2. Services Summary

| Name | Type | Image / Build | Ports | Depends On | Health Check | Component Ref |
|------|------|--------------|-------|------------|-------------|---------------|
| api-gateway | application | ./src/gateway | 8080:8080 | auth-svc, order-svc | GET /health | ARCH-COMP-001 |
| auth-svc | application | ./src/auth | 8081:8081 | postgres, redis | GET /health | ARCH-COMP-002 |
| order-svc | application | ./src/orders | 8082:8082 | postgres, rabbitmq | GET /health | ARCH-COMP-003 |
| notification-worker | application | ./src/notifications | — | rabbitmq, redis | process check | ARCH-COMP-004 |
| postgres | infrastructure | postgres:16 | 5432:5432 | — | pg_isready | — |
| redis | infrastructure | redis:7-alpine | 6379:6379 | — | redis-cli ping | — |
| rabbitmq | infrastructure | rabbitmq:3-management | 5672:5672, 15672:15672 | — | rabbitmq-diagnostics check_port_connectivity | — |
| prometheus | observability | prom/prometheus | 9090:9090 | — | /-/healthy | — |
| grafana | observability | grafana/grafana | 3000:3000 | prometheus, loki, tempo | /api/health | — |
| loki | observability | grafana/loki | 3100:3100 | — | /ready | — |
| tempo | observability | grafana/tempo | 3200:3200, 4317:4317 | — | /ready | — |

## 3. Observability Stack

### Prometheus
- **Port**: 9090
- **Scrape targets**: api-gateway:8080, auth-svc:8081, order-svc:8082
- **Alerting rules**: monitoring/alerts.yml (8 rules from DEVOPS-OBS-001)

### Grafana
- **Port**: 3000
- **Dashboards**: Service Overview, SLO Burn-Down, Per-Service Latency (from DEVOPS-OBS-001)
- **Datasources**: prometheus, loki, tempo

### Loki
- **Port**: 3100
- **Log drivers**: api-gateway, auth-svc, order-svc, notification-worker

### Tempo
- **Port**: 3200 (UI), 4317 (OTLP gRPC)
- **Receivers**: OTLP
- **All services configured with OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317**

## 4. Startup Order

1. postgres, redis, rabbitmq (infrastructure)
2. auth-svc (depends on postgres, redis)
3. order-svc (depends on postgres, rabbitmq)
4. notification-worker (depends on rabbitmq, redis)
5. api-gateway (depends on auth-svc, order-svc)

## 5. Instrumentation Status

| Check | Status | Details |
|-------|--------|---------|
| Metrics endpoint | ✓ /metrics on all 4 services | prometheus_client middleware |
| Structured logging | ✓ JSON format on all services | structlog/pino with correlation_id |
| Trace propagation | ✓ W3C Trace Context | opentelemetry-sdk on all services, headers propagated in HTTP clients |

## 6. Upstream References

- Impl: IMPL-MAP-001 through IMPL-MAP-004, IMPL-CODE-001, IMPL-GUIDE-001
- DevOps: DEVOPS-IAC-001, DEVOPS-OBS-001
- Arch: ARCH-COMP-001 through ARCH-COMP-004
