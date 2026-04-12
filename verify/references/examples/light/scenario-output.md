# Verification Scenarios (Light Mode Example)

## 1. Scenario Summary

| ID | Category | Title | Source | Evidence Types |
|----|----------|-------|--------|---------------|
| SC-001 | integration | Create todo item | ARCH-DIAG-001 | response, metric, log |
| SC-101 | failure | PostgreSQL unavailability | ARCH-COMP-001 deps | response, metric, log |
| SC-301 | observability | SLO metric collection | DEVOPS-OBS-001 | metric |

## 2. Integration Scenarios

### SC-001 — Create todo item

**Category**: integration

**Description**: Verify the full create-todo flow from API request to database persistence, confirming the Arch sequence diagram is realised at runtime.

**Source**: ARCH-DIAG-001 (create todo sequence)

**Preconditions**

- All services healthy
- Database migrated (empty todos table)

**Steps**

| # | Action | Type | Details |
|---|--------|------|---------|
| 1 | POST /api/v1/todos | http_request | payload: {"title": "Buy groceries", "completed": false} |
| 2 | GET /api/v1/todos | http_request | Verify the item appears in the list |

**Expected Results**

| Type | Condition |
|------|-----------|
| response | POST returns HTTP 201 with todo id |
| response | GET returns list containing the created todo |
| metric | http_requests_total{status="201", method="POST"} incremented |
| log | Structured log: {"event": "todo_created", "todo_id": "..."} |

## 3. Failure Scenarios

### SC-101 — PostgreSQL unavailability

**Category**: failure

**Description**: Verify graceful degradation when PostgreSQL is stopped.

**Preconditions**

- All services healthy, at least one successful request completed

**Steps**

| # | Action | Type | Details |
|---|--------|------|---------|
| 1 | docker stop postgres | fault_injection | Simulate DB outage |
| 2 | POST /api/v1/todos | http_request | Expect error response |
| 3 | docker start postgres | recovery | Restore DB |
| 4 | Wait for health check | recovery | pg_isready passes |
| 5 | POST /api/v1/todos | http_request | Expect success after recovery |

**Expected Results**

| Type | Condition |
|------|-----------|
| response | HTTP 503 during outage |
| response | HTTP 201 after recovery |
| metric | Error rate spike visible in Prometheus |
| log | Error-level log with database connection failure |

## 4. Observability Scenarios

### SC-301 — SLO metric collection

**Category**: observability

**Description**: Verify that the SLO metric (http_requests_total) defined in DEVOPS-OBS-001 is collected by Prometheus.

**Steps**

| # | Action | Type | Details |
|---|--------|------|---------|
| 1 | Send 5 requests to POST /api/v1/todos | http_request | Generate metrics |
| 2 | Query Prometheus | metric_query | http_requests_total |

**Expected Results**

| SLO ID | SLI Metric | Collected? |
|--------|-----------|------------|
| SLO-001 | http_requests_total | ✓ (value > 0) |
