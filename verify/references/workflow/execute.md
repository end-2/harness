# Execute — Scenario Execution Stage

**Role**: Start the Docker Compose environment, run each verification scenario in order, collect evidence, and judge pass/fail.

**Runs in**: main agent (real-time environment interaction, failure requires user judgment).

## Entry conditions

- `provision` stage completed — docker-compose.verify.yml exists and services are buildable.
- `scenario` stage completed — `VERIFY-SC-*` artifact exists with scenario definitions.
- Docker daemon is running.

## Environment startup

1. Build application images:
   ```bash
   docker compose -f docker-compose.verify.yml build
   ```
   If build fails, report the error referencing the specific `IMPL-MAP-*` entry and escalate.

2. Start all services:
   ```bash
   docker compose -f docker-compose.verify.yml up -d
   ```

3. Wait for all services to be healthy:
   ```bash
   docker compose -f docker-compose.verify.yml ps
   ```
   Check that every service shows `healthy` status. Wait up to 60 seconds with polling. If a service doesn't become healthy, check its logs (`docker compose logs <service>`) and report the failure.

4. Verify observability stack connectivity:
   - Prometheus: `curl http://localhost:9090/-/healthy`
   - Grafana: `curl http://localhost:3000/api/health`
   - Loki (heavy): `curl http://localhost:3100/ready`
   - Tempo (heavy): `curl http://localhost:3200/ready`

## Scenario execution order

Execute scenarios in this order to build evidence progressively:

1. **Integration scenarios** first — establish baseline behaviour.
2. **Observability scenarios** — verify metrics/logs/traces while the system is healthy.
3. **Load scenarios** — apply concurrent requests while monitoring.
4. **Failure scenarios** last — these may disrupt services; run recovery steps between each.

Within each category, execute in ID order (SC-001 before SC-002).

## Executing a scenario

For each scenario in `VERIFY-SC-*`:

### 1. Check preconditions

Verify all preconditions are met (services healthy, data state correct). If a precondition fails, skip the scenario and record `status: skip` with the reason.

### 2. Run steps

Execute each step in order:

| Step type | How to execute |
|-----------|---------------|
| `http_request` | Use `curl` or equivalent. Record full response (status, headers, body). |
| `fault_injection` | `docker stop <service>`, `docker pause <service>`, or `docker exec <service> tc qdisc add dev eth0 root netem delay 500ms`. |
| `recovery` | `docker start <service>`, `docker unpause <service>`, or remove the netem rule. Wait for health check to pass. |
| `metric_query` | Query Prometheus: `curl 'http://localhost:9090/api/v1/query?query=<PromQL>'`. |
| `log_query` | Query Loki: `curl 'http://localhost:3100/loki/api/v1/query_range?query=<LogQL>'`. Or use `docker compose logs <service>` for light mode. |
| `trace_query` | Query Tempo: `curl 'http://localhost:3200/api/traces/<traceID>'`. |
| `db_query` | `docker exec <db-service> psql/mysql/mongosh -c '<query>'`. |
| `load_injection` | Run N concurrent requests using `xargs -P`, `parallel`, or a simple script. |

### 3. Collect evidence

After executing steps, collect evidence for each `expected_results` entry:

- **Response evidence**: HTTP status code, response body (truncated if large), response time.
- **Metric evidence**: PromQL query, result value, timestamp.
- **Log evidence**: LogQL query (or grep on docker logs), matching log entries.
- **Trace evidence**: trace ID, span names, duration.
- **Dashboard evidence**: Grafana panel screenshot URL or API query confirmation.

Assign each piece of evidence an ID (EVD-001, EVD-002, ...).

### 4. Judge the result

Compare actual results against `expected_results`:

- **pass**: all expected results match.
- **fail**: at least one expected result does not match.
- Record the duration of the scenario execution.

### 5. Clean up (for failure scenarios)

After failure scenarios, always run the recovery steps to restore the environment to a healthy state before the next scenario. Verify health checks pass after recovery.

## Evidence collection tips

### Prometheus queries

```bash
# Instant query
curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total{status="201"}' | jq '.data.result'

# Range query (last 5 minutes)
curl -s 'http://localhost:9090/api/v1/query_range?query=rate(http_requests_total[1m])&start='$(date -v-5M +%s)'&end='$(date +%s)'&step=15' | jq '.data.result'
```

### Loki queries

```bash
# Search for specific log entry
curl -s 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={service="api"} |= "user_created"' \
  --data-urlencode 'start='$(date -v-5M +%s.%N) \
  --data-urlencode 'end='$(date +%s.%N) | jq '.data.result'
```

### Light mode (no Loki/Tempo)

```bash
# Logs via docker
docker compose -f docker-compose.verify.yml logs api-service --since 1m | grep "user_created"

# No distributed trace verification in light mode
```

## Output

The execution results feed into the `diagnose` stage. Record:
- Per-scenario: status (pass/fail/skip), duration, evidence IDs.
- Environment health: service statuses, restart counts, memory usage.
- All evidence artifacts with IDs, types, queries, and results.

## Escalation conditions

- **Environment fails to start**: container crash loops, OOM kills. Show `docker compose logs` output and escalate.
- **Network unreachable**: services cannot communicate. Check Docker network and escalate.
- **Build failure**: application image doesn't build. Reference the specific Impl artifact and escalate.
