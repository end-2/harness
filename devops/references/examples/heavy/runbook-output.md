# DEVOPS-RB-001 — Incident Runbooks (E-Commerce Platform, heavy mode)

**Phase**: approved · **Mode**: heavy

Incident runbooks for the e-commerce platform. One runbook per critical alert scenario. Each runbook includes trigger condition, symptoms, diagnosis steps with commands, remediation with automation flags, escalation path, and communication templates.

---

## RB-001: High API Error Rate

**Trigger**: MON-001 fires (gateway availability burn rate > 14.4x over 5m AND 1h)
**Severity**: critical
**SLO ref**: SLO-001 (gateway availability 99.9%)

### Symptoms

- 5xx spike on gateway endpoints (`/api/*`)
- SLO burn-rate alert on DASH-002
- Elevated error rate visible on DASH-001 Service Overview
- Possible user-facing error pages or timeouts

### Diagnosis

| Step | Action | Command |
|------|--------|---------|
| 1 | Check recent deployments | `kubectl rollout history deployment/api-gateway -n production` |
| 2 | Check pod status and restarts | `kubectl get pods -l app=api-gateway -n production -o wide` |
| 3 | Check error logs (last 5 min) | `kubectl logs -l app=api-gateway -n production --tail=200 --since=5m \| jq 'select(.level=="error")'` |
| 4 | Check downstream service health | `kubectl get pods -l app=order-service -n production && kubectl get pods -l app=payment-service -n production` |
| 5 | Check resource utilization | `kubectl top pods -l app=api-gateway -n production` |
| 6 | Inspect traces for failing requests | Open Jaeger UI, filter by `service=api-gateway, status=error`, last 15 minutes |

### Remediation

| Step | Action | Command | Auto |
|------|--------|---------|------|
| 1 | If recent deploy: rollback gateway | `kubectl argo rollouts abort api-gateway -n production` | yes |
| 2 | If downstream failure: check specific service runbook | See RB-002 (payment) or order-service runbook | no |
| 3 | If resource exhaustion: scale up | `kubectl scale deployment/api-gateway -n production --replicas=6` | no |
| 4 | If configuration error: revert ConfigMap | `kubectl rollout undo deployment/api-gateway -n production` | no |
| 5 | Verify recovery | Monitor DASH-002 error budget burn rate for 10 minutes | no |

### Escalation

| Level | Contact | Channel | Timeout |
|-------|---------|---------|---------|
| 1 | On-call SRE | #incidents (Slack) + PagerDuty | 15 min |
| 2 | Platform engineering lead | #incidents-escalation (Slack) | 30 min |
| 3 | VP Engineering | phone call | 60 min |

---

## RB-002: Payment Service Timeout

**Trigger**: MON-005 fires (payment success rate burn rate > 14.4x over 5m AND 1h)
**Severity**: critical
**SLO ref**: SLO-005 (payment success rate 99.95%)

### Symptoms

- Payment transactions failing or timing out
- Elevated `payment_provider_duration_seconds` p99 on DASH-004
- Circuit breaker tripping to OPEN state on DASH-004
- Order placement failures downstream (users unable to complete checkout)
- Possible spike in retry volume (`payment_retries_total`)

### Diagnosis

| Step | Action | Command |
|------|--------|---------|
| 1 | Check circuit breaker state | `kubectl exec -n production deployment/payment-service -- curl localhost:8080/internal/circuit-breaker` |
| 2 | Check payment service pod health | `kubectl get pods -l app=payment-service -n production -o wide` |
| 3 | Check payment provider connectivity | `kubectl exec -n production deployment/payment-service -- curl -s -o /dev/null -w '%{http_code}' https://api.payment-provider.com/health` |
| 4 | Check error logs for provider errors | `kubectl logs -l app=payment-service -n production --tail=200 --since=5m \| jq 'select(.level=="error")'` |
| 5 | Check recent deployments | `kubectl rollout history deployment/payment-service -n production` |
| 6 | Inspect traces for slow transactions | Open Jaeger UI, filter by `service=payment-service`, sort by duration descending |
| 7 | Check database connection pool | `kubectl exec -n production deployment/payment-service -- curl localhost:8080/internal/metrics \| grep db_pool` |

### Remediation

| Step | Action | Command | Auto |
|------|--------|---------|------|
| 1 | If provider outage: activate circuit breaker (graceful degradation) | Circuit breaker auto-activates after 5 consecutive failures | yes |
| 2 | If recent deploy: rollback payment-service | `kubectl argo rollouts abort payment-service -n production` | yes |
| 3 | If circuit breaker open but provider recovered: reset breaker | `kubectl exec -n production deployment/payment-service -- curl -X POST localhost:8080/internal/circuit-breaker/reset` | no |
| 4 | If connection pool exhaustion: restart pods (rolling) | `kubectl rollout restart deployment/payment-service -n production` | no |
| 5 | If sustained provider degradation: enable payment queue (async processing) | Update ConfigMap `payment-config` to set `ASYNC_PAYMENTS=true`, restart pods | no |
| 6 | Verify recovery | Monitor DASH-004 transaction success rate and circuit breaker state for 10 minutes | no |

### Escalation

| Level | Contact | Channel | Timeout |
|-------|---------|---------|---------|
| 1 | On-call SRE | #incidents (Slack) + PagerDuty | 10 min (tighter SLA for payment) |
| 2 | Payment team lead | #payment-incidents (Slack) | 20 min |
| 3 | VP Engineering + payment provider support | phone call + provider support ticket | 45 min |

---

## RB-003: Database Connection Pool Exhaustion

**Trigger**: MON-013/MON-014 fires (resource utilization alerts) combined with log-based metric `db_connection_pool_exhausted_total > 0`
**Severity**: high
**SLO ref**: SLO-003 (order processing availability 99.9%), SLO-005 (payment success rate 99.95%)

### Symptoms

- `connection pool exhausted` errors in order-service and/or payment-service logs
- Elevated response latency across database-dependent services
- PostgreSQL `pg_stat_activity` showing many idle-in-transaction connections
- Possible cascading failures: order-service times out, gateway returns 503

### Diagnosis

| Step | Action | Command |
|------|--------|---------|
| 1 | Check active DB connections | `kubectl exec -n production deployment/order-service -- curl localhost:8080/internal/metrics \| grep 'db_pool_active\|db_pool_idle\|db_pool_max'` |
| 2 | Check PostgreSQL connection count | `kubectl exec -n production statefulset/postgresql-0 -- psql -U app -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"` |
| 3 | Identify long-running queries | `kubectl exec -n production statefulset/postgresql-0 -- psql -U app -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '30 seconds' ORDER BY duration DESC;"` |
| 4 | Check for connection leaks | `kubectl logs -l app=order-service -n production --tail=500 --since=15m \| jq 'select(.message \| contains("connection"))' \| head -50` |
| 5 | Check HPA status (pod count may have scaled up, exhausting pool) | `kubectl get hpa -n production` |
| 6 | Check if recent migration ran | `kubectl logs -l app=db-migration -n production --tail=50` |

### Remediation

| Step | Action | Command | Auto |
|------|--------|---------|------|
| 1 | Kill idle-in-transaction connections older than 60s | `kubectl exec -n production statefulset/postgresql-0 -- psql -U app -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND (now() - state_change) > interval '60 seconds';"` | no |
| 2 | If pod count scaled beyond pool capacity: adjust HPA max or pool size | Update ConfigMap: `DB_POOL_MAX_SIZE=30` (per pod), then `kubectl rollout restart deployment/order-service -n production` | no |
| 3 | If long-running queries: kill and investigate | `kubectl exec -n production statefulset/postgresql-0 -- psql -U app -c "SELECT pg_cancel_backend(<pid>);"` | no |
| 4 | If connection leak suspected: rolling restart affected service | `kubectl rollout restart deployment/order-service -n production` | no |
| 5 | If PostgreSQL at max_connections: increase limit | Update `postgresql.conf` via Helm values, `helm upgrade postgresql charts/postgresql -f values.production.yaml --set max_connections=200` | no |
| 6 | Verify recovery | Monitor `db_pool_active` metric and `pg_stat_activity` count for 10 minutes | no |

### Escalation

| Level | Contact | Channel | Timeout |
|-------|---------|---------|---------|
| 1 | On-call SRE | #incidents (Slack) + PagerDuty | 15 min |
| 2 | Database team lead | #database-ops (Slack) | 30 min |
| 3 | Platform engineering lead | #incidents-escalation (Slack) | 60 min |

---

## Communication Template

Used by all runbooks. Fill in the bracketed fields during the incident.

```
**Incident**: [RB-ID] [Short description]
**Status**: Investigating | Mitigated | Resolved
**Severity**: [critical | high | medium]
**Started**: [ISO 8601 timestamp]
**Impact**: [User-facing description of what is broken]
**Services affected**: [list of services]
**Current action**: [What the on-call is doing right now]
**Next update**: [Expected time of next status update]
```

Post to `#incidents` on state transitions (Investigating -> Mitigated -> Resolved). Tag `@incident-commander` on severity escalation.

## Postmortem Template

Created after every critical-severity incident and after high-severity incidents that breached an SLO.

```
## Incident [RB-ID]: [Title]

### Timeline
| Time (UTC) | Event |
|------------|-------|
| HH:MM | Alert fired (MON-XXX) |
| HH:MM | On-call acknowledged |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Incident resolved |

### Root Cause
[Technical description of what went wrong and why]

### Impact
- **Duration**: [X minutes]
- **Users affected**: [estimated count or percentage]
- **SLO impact**: [error budget consumed]
- **Revenue impact**: [if applicable, estimated lost transactions]

### What Went Well
- [List of things that worked during incident response]

### What Went Wrong
- [List of things that failed or were slow]

### Action Items
| Item | Owner | Due date | Priority |
|------|-------|----------|----------|
| [Preventive action] | [team/person] | [date] | [P0/P1/P2] |

### Lessons Learned
[Summary for future reference]
```

## Upstream Refs

ARCH-COMP-001, ARCH-COMP-002, ARCH-COMP-003, ARCH-COMP-004, DEVOPS-OBS-001, DEVOPS-PL-001
