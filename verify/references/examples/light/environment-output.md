# Environment Setup

## 1. Mode

**Light** — single Arch component (Todo API), single deployment environment.

## 2. Services Summary

| Name | Type | Image / Build | Ports | Depends On | Health Check | Component Ref |
|------|------|--------------|-------|------------|-------------|---------------|
| todo-api | application | ./src/api | 8080:8080 | postgres | GET /health | ARCH-COMP-001 |
| postgres | infrastructure | postgres:16 | 5432:5432 | — | pg_isready | — |
| prometheus | observability | prom/prometheus | 9090:9090 | — | /-/healthy | — |
| grafana | observability | grafana/grafana | 3000:3000 | prometheus | /api/health | — |

## 3. Service Details

### todo-api

**Type**: application

**Build**: `./src/api` (Dockerfile present from Impl scaffold)

**Ports**: 8080:8080

**Dependencies**: postgres

**Health Check**

| Parameter | Value |
|-----------|-------|
| Endpoint | GET /health |
| Interval | 10s |
| Retries | 3 |

**Environment Variables**

| Variable | Value | Source |
|----------|-------|--------|
| DATABASE_URL | postgresql://app:dev@postgres:5432/tododb | IMPL-CODE-001 environment_config |
| PORT | 8080 | IMPL-CODE-001 environment_config |

### postgres

**Type**: infrastructure

**Image**: postgres:16

**Health Check**: `pg_isready -U app -d tododb` (interval 5s, retries 5)

## 4. Observability Stack

### Prometheus

- **Port**: 9090
- **Scrape targets**: todo-api:8080/metrics
- **Alerting rules**: monitoring/alerts.yml (from DEVOPS-OBS-001)

### Grafana

- **Port**: 3000
- **Dashboards**: monitoring/dashboards/ (auto-provisioned from DEVOPS-OBS-001)
- **Datasources**: prometheus

### Loki

Not provisioned (light mode).

### Tempo

Not provisioned (light mode).

## 5. Network Topology

| Network | Driver | Services |
|---------|--------|----------|
| verify-net | bridge | todo-api, postgres, prometheus, grafana |

## 6. Startup Order

1. postgres (infrastructure, no deps)
2. todo-api (depends on postgres)
3. prometheus, grafana (observability, independent)

## 7. Instrumentation Status

| Check | Status | Details |
|-------|--------|---------|
| Metrics endpoint | ✓ /metrics | prometheus_client middleware configured |
| Structured logging | ✓ JSON format | structlog with JSON renderer |
| Trace propagation | — (not required in light mode) | No distributed tracing needed for single service |

## 8. Generated Files

| File | Purpose |
|------|---------|
| docker-compose.verify.yml | Main compose file |
| monitoring/prometheus.yml | Prometheus scrape config |
| monitoring/alerts.yml | Alerting rules (from DEVOPS-OBS-001) |
| monitoring/dashboards/overview.json | Grafana dashboard (from DEVOPS-OBS-001) |
| monitoring/grafana/provisioning/datasources/datasources.yml | Grafana datasource config |
| monitoring/grafana/provisioning/dashboards/dashboards.yml | Grafana dashboard provisioning |

## 9. Upstream References

- Impl: IMPL-MAP-001, IMPL-CODE-001, IMPL-GUIDE-001
- DevOps: DEVOPS-OBS-001
- Arch: ARCH-COMP-001 (via IMPL-MAP-001 component_ref)
