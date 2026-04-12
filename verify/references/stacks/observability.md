# Observability Stack Configuration Guide

This document describes how to provision the local observability stack from DevOps artifacts.

## Architecture

```
┌──────────────┐     metrics     ┌──────────────┐     query      ┌──────────────┐
│ App Service  │────────────────→│  Prometheus   │←───────────────│   Grafana    │
│ /metrics     │                 │  :9090        │                │   :3000      │
└──────────────┘                 └──────────────┘                └──────────────┘
       │                                                               ↑
       │ logs (Docker driver)    ┌──────────────┐     query           │
       └────────────────────────→│    Loki       │←───────────────────┘
       │                         │   :3100       │
       │                         └──────────────┘
       │ traces (OTLP)           ┌──────────────┐     query
       └────────────────────────→│    Tempo      │←───────────────────┘
                                 │   :3200       │
                                 └──────────────┘
```

## Prometheus Configuration

### prometheus.yml

```yaml
global:
  scrape_interval: 5s      # Fast for local verification
  evaluation_interval: 5s

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  - job_name: 'app-services'
    static_configs:
      - targets:
        # One target per application service from IMPL-MAP
        - 'api-service:8080'
        - 'worker-service:8081'
    metrics_path: /metrics   # or /actuator/prometheus for Spring

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### alerts.yml

Load directly from `DEVOPS-OBS-*.monitoring_rules[]`. Convert each rule to Prometheus format:

```yaml
groups:
  - name: slo_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Error rate exceeds 1%"
```

## Grafana Configuration

### Datasource provisioning

Create `monitoring/grafana/provisioning/datasources/datasources.yml`:

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  # Heavy mode only
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
```

### Dashboard provisioning

Create `monitoring/grafana/provisioning/dashboards/dashboards.yml`:

```yaml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: 'Verify'
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

Copy dashboard JSON files from `DEVOPS-OBS-*.dashboards[]` into `monitoring/dashboards/`.

## Loki Configuration (Heavy Mode)

### loki-config.yml

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  ring:
    kvstore:
      store: inmemory
    replication_factor: 1
  path_prefix: /loki

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

storage_config:
  filesystem:
    directory: /loki/chunks

limits_config:
  reject_old_samples: false
```

### Docker log driver

Configure application services to send logs to Loki:

```yaml
services:
  api-service:
    logging:
      driver: loki
      options:
        loki-url: "http://localhost:3100/loki/api/v1/push"
        loki-external-labels: "service={{.Name}}"
```

Alternatively, use the Promtail sidecar pattern if the Docker Loki plugin isn't available.

## Tempo Configuration (Heavy Mode)

### tempo-config.yml

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
        http:
          endpoint: "0.0.0.0:4318"

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal

metrics_generator:
  storage:
    path: /var/tempo/generator/wal
```

### Application OTLP configuration

Set these environment variables on application services:

```yaml
environment:
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317
  - OTEL_SERVICE_NAME=api-service
  - OTEL_TRACES_SAMPLER=always_on  # 100% sampling for local verification
```

## Port allocation

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics query UI and API |
| Grafana | 3000 | Dashboard UI |
| Loki | 3100 | Log query API |
| Tempo | 3200 | Trace query UI |
| Tempo OTLP gRPC | 4317 | Trace ingestion (gRPC) |
| Tempo OTLP HTTP | 4318 | Trace ingestion (HTTP) |

## Verification queries

### Prometheus

```bash
# Check if a metric exists
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result'

# Check specific SLI metric
curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total' | jq '.data.result'

# Check alerting rules loaded
curl -s 'http://localhost:9090/api/v1/rules' | jq '.data.groups'
```

### Loki

```bash
# Search logs
curl -s 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={service="api-service"}' \
  --data-urlencode "start=$(date -v-5M +%s)" \
  --data-urlencode "end=$(date +%s)" | jq '.data.result'
```

### Tempo

```bash
# Search for traces by service
curl -s 'http://localhost:3200/api/search?q=resource.service.name=api-service&limit=5' | jq '.traces'

# Get specific trace
curl -s 'http://localhost:3200/api/traces/<traceID>' | jq '.batches'
```
