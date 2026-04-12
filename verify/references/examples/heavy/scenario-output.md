# Verification Scenarios (Heavy Mode Example)

## 1. Scenario Summary

| ID | Category | Title | Source | Evidence Types |
|----|----------|-------|--------|---------------|
| SC-001 | integration | User registration flow | ARCH-DIAG-001 | response, metric, log, trace |
| SC-002 | integration | Create order flow | ARCH-DIAG-002 | response, metric, log, trace |
| SC-003 | integration | Notification delivery flow | ARCH-DIAG-003 | log, metric, trace |
| SC-101 | failure | Auth service unavailability | ARCH-COMP-002 deps | response, metric, log |
| SC-102 | failure | Database unavailability | ARCH-COMP-003 deps | response, metric, log |
| SC-103 | failure | RabbitMQ unavailability | ARCH-COMP-003 deps | response, metric, log |
| SC-104 | failure | Auth service high latency | ARCH-COMP-002 | response, metric |
| SC-201 | load | Concurrent order creation | DEVOPS-OBS-001 SLO | response, metric |
| SC-301 | observability | SLO metric collection | DEVOPS-OBS-001 | metric |
| SC-302 | observability | Alert rule verification | DEVOPS-OBS-001 | metric |
| SC-303 | observability | Dashboard rendering | DEVOPS-OBS-001 | dashboard |
| SC-304 | observability | Log format and masking | DEVOPS-OBS-001 | log |
| SC-305 | observability | Distributed trace propagation | DEVOPS-OBS-001 | trace |
| SC-306 | observability | Runbook trigger reproduction | DEVOPS-RB-001 | metric, log |

## 2. Integration Scenarios

### SC-001 — User registration flow

**Description**: Verify the full registration flow: API Gateway → Auth Service → PostgreSQL, confirming the ARCH-DIAG-001 sequence.

**Steps**

| # | Action | Type | Details |
|---|--------|------|---------|
| 1 | POST /api/v1/auth/register | http_request | {"email": "test@example.com", "password": "secure123"} |
| 2 | Query Prometheus | metric_query | http_requests_total{service="auth-svc", status="201"} |
| 3 | Query Loki | log_query | {service="auth-svc"} |= "user_registered" |
| 4 | Query Tempo | trace_query | Find trace with spans: api-gateway → auth-svc → postgres |

**Expected Results**

| Type | Condition |
|------|-----------|
| response | HTTP 201, body contains user token |
| metric | auth-svc request counter incremented |
| log | "user_registered" event in auth-svc, correlation_id matches request |
| trace | Complete trace: api-gateway → auth-svc → postgres (3 spans) |

### SC-002 — Create order flow

**Description**: Verify the order creation flow: API Gateway → Order Service → PostgreSQL + RabbitMQ (publish notification), confirming ARCH-DIAG-002 sequence.

### SC-003 — Notification delivery flow

**Description**: Verify async notification: RabbitMQ → Notification Worker → external call, confirming ARCH-DIAG-003 sequence.

## 3. Failure Scenarios

### SC-101 — Auth service unavailability

**Steps**: Stop auth-svc → request to /api/v1/auth/login → expect 503 from gateway → start auth-svc → expect recovery.

### SC-102 — Database unavailability

**Steps**: Stop postgres → request to /api/v1/orders → expect 503 → start postgres → expect recovery.

### SC-103 — RabbitMQ unavailability

**Steps**: Stop rabbitmq → create order → expect order saved but notification deferred → start rabbitmq → expect notification delivered.

### SC-104 — Auth service high latency

**Steps**: Add 2s delay to auth-svc network → request through gateway → expect timeout or slow response → remove delay → verify circuit breaker recovery.

## 4. Load Scenarios

### SC-201 — Concurrent order creation

**Steps**: 20 concurrent POST /api/v1/orders → all should succeed → p99 latency < 500ms (SLO target) → error rate 0%.

## 5. Observability Scenarios

### SC-301 — SLO metric collection

Verify all 5 SLOs have collectible metrics in Prometheus.

### SC-302 — Alert rule verification

Trigger high error rate (by stopping postgres) → verify Prometheus alert fires.

### SC-303 — Dashboard rendering

Open Grafana dashboards → verify all panels show data (no "No data" panels).

### SC-304 — Log format and masking

Send request with email in body → check logs → verify email is masked (j***@example.com).

### SC-305 — Distributed trace propagation

Send request through gateway → auth → order → verify complete trace in Tempo with correct span hierarchy.

### SC-306 — Runbook trigger reproduction

Reproduce DEVOPS-RB-001 trigger (high error rate for 5 minutes) → verify diagnosis commands from runbook work in the local environment.
