# Fault Injection Techniques Catalogue

This document catalogues fault injection methods available in the Docker Compose local environment. All techniques operate at the container level — no host system changes.

## Service Unavailability

### Stop a service

```bash
docker compose -f docker-compose.verify.yml stop <service>
```

Simulates: complete service outage (process crash, node failure).
Recovery: `docker compose -f docker-compose.verify.yml start <service>`
Wait for: health check to pass.

### Pause a service

```bash
docker compose -f docker-compose.verify.yml pause <service>
```

Simulates: frozen process (deadlock, GC pause, resource exhaustion). The service is alive but unresponsive.
Recovery: `docker compose -f docker-compose.verify.yml unpause <service>`

### Kill a service (ungraceful)

```bash
docker compose -f docker-compose.verify.yml kill -s SIGKILL <service>
```

Simulates: hard crash (no graceful shutdown). Useful for testing data durability.
Recovery: `docker compose -f docker-compose.verify.yml start <service>`

## Network Faults

### Add latency

```bash
docker exec <container> tc qdisc add dev eth0 root netem delay 500ms 100ms
```

Simulates: network latency (500ms ± 100ms jitter). Tests timeout handling.
Recovery: `docker exec <container> tc qdisc del dev eth0 root`

### Packet loss

```bash
docker exec <container> tc qdisc add dev eth0 root netem loss 50%
```

Simulates: unreliable network (50% packet loss). Tests retry logic.
Recovery: `docker exec <container> tc qdisc del dev eth0 root`

### DNS failure

```bash
docker exec <container> sh -c "echo '127.0.0.1 <target-service>' >> /etc/hosts"
```

Simulates: DNS resolution failure for a specific service.
Recovery: `docker exec <container> sh -c "sed -i '/<target-service>/d' /etc/hosts"`

**Note**: `tc` (traffic control) requires the `iproute2` package in the container. If not available, use the alternative approaches below.

## Resource Constraints

### Memory limit

```yaml
# In docker-compose.verify.yml
services:
  api-service:
    deploy:
      resources:
        limits:
          memory: 128M
```

Simulates: memory-constrained environment. Tests OOM behaviour.

### CPU throttle

```yaml
services:
  api-service:
    deploy:
      resources:
        limits:
          cpus: "0.5"
```

Simulates: CPU-constrained environment. Tests degradation under load.

## Database-Specific Faults

### Connection limit exhaustion

```bash
# Set max connections to 1 (PostgreSQL)
docker exec <postgres-container> psql -U app -d appdb -c "ALTER SYSTEM SET max_connections = 1;"
docker compose -f docker-compose.verify.yml restart postgres
```

Tests: connection pool behaviour, connection timeout handling.

### Slow queries

```bash
# Add artificial delay (PostgreSQL)
docker exec <postgres-container> psql -U app -d appdb -c "SELECT pg_sleep(5);"
```

Tests: query timeout handling, connection pool exhaustion under slow queries.

## Choosing the right technique

| Scenario goal | Technique | Expected app behaviour |
|--------------|-----------|----------------------|
| Dependency outage | `docker stop` | Return error gracefully (503), circuit breaker opens |
| Network partition | `tc netem delay` or `docker pause` | Timeout handling, retry with backoff |
| Cascading failure | Stop multiple dependencies | Bulkhead isolation (other endpoints still work) |
| Recovery | `docker start` after fault | Health check passes, normal operation resumes |
| Data durability | `docker kill -s SIGKILL` | No data loss after ungraceful shutdown |

## Safety notes

- All fault injection is **container-scoped** — no host system impact.
- Always run recovery steps after fault scenarios.
- Verify health checks pass after recovery before continuing.
- For `tc` commands, ensure the container has `NET_ADMIN` capability or `iproute2` installed.
- Don't inject faults into observability services (Prometheus, Grafana, Loki, Tempo) during verification — they are the observation tools.
