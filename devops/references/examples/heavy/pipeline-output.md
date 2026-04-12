# DEVOPS-PL-001 — Pipeline Config (E-Commerce Platform, heavy mode)

**Phase**: approved · **Mode**: heavy

Multi-service e-commerce platform with four microservices: api-gateway, order-service, payment-service, inventory-service. Multi-stage pipeline with build matrix, security scanning, environment promotion gates, and canary deployment with SLO-based promotion.

## Platform

GitHub Actions. The repository uses GitHub, and Actions provides sufficient matrix build and environment gate support for four services.

## Trigger Configuration

| Event | Condition | Stages triggered |
|-------|-----------|------------------|
| push | `main` branch | full pipeline through staging deploy |
| pull_request | any branch → `main` | build → unit-test → integration-test → security-scan |
| tag | `v*` pattern | full pipeline through production promote |
| workflow_dispatch | manual | full pipeline (for hotfix deploys) |

## Build Matrix

| Service | Dockerfile | Build context | ARCH ref |
|---------|-----------|---------------|----------|
| api-gateway | `services/gateway/Dockerfile` | `services/gateway/` | ARCH-COMP-001 |
| order-service | `services/order/Dockerfile` | `services/order/` | ARCH-COMP-002 |
| payment-service | `services/payment/Dockerfile` | `services/payment/` | ARCH-COMP-003 |
| inventory-service | `services/inventory/Dockerfile` | `services/inventory/` | ARCH-COMP-004 |

All four services build in parallel. Each matrix entry produces a container image tagged with the commit SHA.

## Pipeline Stages

### Stage 1: Build

Runs as a matrix across all four services.

| Step | Command | Notes |
|------|---------|-------|
| Checkout | `actions/checkout@v4` | |
| Setup Node | `actions/setup-node@v4` with 20.x | api-gateway is Node.js |
| Setup Go | `actions/setup-go@v5` with 1.22 | order, payment, inventory are Go |
| Restore cache | key per service lockfile | `package-lock.json` or `go.sum` |
| Install deps | `npm ci` / `go mod download` | Per service |
| Lint | `eslint` / `golangci-lint run` | Per service conventions |
| Build image | `docker build -t $SERVICE:$SHA .` | Multi-stage Dockerfile |

### Stage 2: Unit Test

Runs as a matrix across all four services. Requires build success.

| Step | Command | Notes |
|------|---------|-------|
| Unit tests | `npm test -- --coverage` / `go test ./... -coverprofile=cover.out` | Per service |
| Upload coverage | `actions/upload-artifact@v4` | Per service coverage report |

### Stage 3: Integration Test

Runs after all unit tests pass. Uses Docker Compose to stand up service dependencies.

| Step | Command | Notes |
|------|---------|-------|
| Start dependencies | `docker compose -f docker-compose.test.yml up -d` | PostgreSQL, Redis, Kafka |
| Run integration tests | `npm run test:integration` / `go test ./integration/... -tags=integration` | Per service |
| Collect results | `actions/upload-artifact@v4` | Combined test report |
| Tear down | `docker compose -f docker-compose.test.yml down` | Cleanup |

### Stage 4: Security Scan

Runs in parallel with integration tests.

| Step | Command | Notes |
|------|---------|-------|
| SAST | `semgrep scan --config=auto` | Static analysis across all services |
| Dependency audit | `npm audit --audit-level=high` / `govulncheck ./...` | Per service |
| Container scan | `trivy image $SERVICE:$SHA` | Per service image |
| Upload SARIF | `github/codeql-action/upload-sarif@v3` | Security findings as PR annotations |

### Stage 5: Staging Deploy

Runs on `main` push only. Deploys all services to staging via Helm.

| Step | Command | Notes |
|------|---------|-------|
| Push images | `docker push $ECR_REPO/$SERVICE:$SHA` | All four images |
| Helm upgrade | `helm upgrade --install $SERVICE charts/$SERVICE -f values.staging.yaml --set image.tag=$SHA` | Per service, staging namespace |
| Smoke tests | `kubectl exec -n staging -- curl http://$SERVICE/health` | Per service health check |
| Integration smoke | `newman run postman/staging-smoke.json` | Cross-service API tests |

### Stage 6: Canary Deploy

Runs on tag push or manual dispatch. Targets production namespace.

| Step | Command | Notes |
|------|---------|-------|
| Push images | `docker push $ECR_REPO/$SERVICE:$SHA` | Production registry |
| Canary rollout | Argo Rollouts `setWeight` progression | See traffic weight routing below |
| SLO gate check | Query Prometheus for burn-rate alerts | Per phase gate |
| Promotion or rollback | Argo Rollouts promote / abort | Based on SLO gate |

### Stage 7: Production Promote

Runs after canary completes successfully. Requires manual approval gate.

| Step | Command | Notes |
|------|---------|-------|
| Approval gate | GitHub Environment protection rule | Requires `prod-approvers` team |
| Promote canary | `kubectl argo rollouts promote $SERVICE -n production` | Full traffic to new version |
| Verify | Monitor SLO dashboards for 15 minutes post-promote | Automated health check |
| Tag release | `gh release create v$VERSION --generate-notes` | Release notes from commits |

## Caching

| Dependency | Cache key | Strategy |
|------------|-----------|----------|
| npm packages | `npm-${{ hashFiles('services/gateway/package-lock.json') }}` | Restore on lockfile match |
| Go modules | `go-${{ hashFiles('services/*/go.sum') }}` | Restore on lockfile match |
| Docker layers | BuildKit cache with registry backend | Layer-level caching |

## Secret Management

| Secret | Source | Injection | Used by |
|--------|--------|-----------|---------|
| `AWS_ACCESS_KEY_ID` | GitHub Secrets | env, deploy steps | all services |
| `AWS_SECRET_ACCESS_KEY` | GitHub Secrets | env, deploy steps | all services |
| `DATABASE_URL` | AWS Secrets Manager via `aws-actions/configure-aws-credentials` | env | order-service, inventory-service |
| `PAYMENT_PROVIDER_KEY` | HashiCorp Vault | env, payment-service deploy step only | payment-service |
| `KAFKA_SASL_PASSWORD` | AWS Secrets Manager | env | order-service, inventory-service |

## Environment Promotion

| Environment | Promotion rule | Approval | Deploy order |
|-------------|---------------|----------|--------------|
| dev | auto on PR merge to dev branch | no | parallel |
| staging | auto on green (main branch) | no | parallel (all services via Helm) |
| production | manual gate after canary success | yes (`prod-approvers` team) | dependency-ordered (see below) |

### Production Deploy Order (topological)

Derived from ARCH-COMP dependency graph:

```
inventory-service (no internal deps)
    ↓
payment-service (no internal deps)
    ↓
order-service (depends on: payment-service, inventory-service)
    ↓
api-gateway (depends on: order-service, payment-service, inventory-service)
```

`inventory-service` and `payment-service` deploy in parallel. `order-service` follows. `api-gateway` deploys last.

## Deployment Strategy

**Method**: canary

**Rationale**: SLO target is 99.9% availability across all services. Canary deployment provides graduated traffic shifting with SLO-based promotion gates, allowing early detection of regressions before full rollout. The system has comprehensive observability (RED metrics per service, distributed tracing) that supports canary-vs-baseline comparison.

### Traffic Weight Routing

| Phase | Canary weight | Duration | Gate condition |
|-------|--------------|----------|----------------|
| 1 | 10% | 5 minutes | No burn-rate alert (MON-001..MON-008) fires |
| 2 | 50% | 10 minutes | No burn-rate alert fires, error rate < SLO threshold |
| 3 | 100% | — | Promotion complete |

Conservative three-step progression. Error budget is tight at 99.9%, so observation windows are sufficient to detect regressions.

## Rollback

**Trigger conditions**:

| Condition | Threshold | Monitoring ref | SLO ref |
|-----------|-----------|---------------|---------|
| error_rate | > 0.1% (5xx responses) | MON-001 | SLO-001 |
| latency_p99 | > 300ms | MON-002 | SLO-002 |
| payment_failure_rate | > 0.5% | MON-005 | SLO-005 |
| order_error_rate | > 0.1% | MON-003 | SLO-003 |

**Automated rollback procedure**:

1. Argo Rollouts detects burn-rate breach from Prometheus analysis query
2. `kubectl argo rollouts abort $SERVICE -n production` — halt canary, route 100% to stable
3. Verify SLO metrics return to normal within 5 minutes
4. Notify `#deploy-alerts` and `#incidents` with deployment ID, service name, and rollback reason
5. Create incident ticket in PagerDuty if SLO was breached during rollback window
6. Block subsequent deploys until incident is resolved

**Manual rollback** (if automated rollback fails):

1. `kubectl argo rollouts undo $SERVICE -n production`
2. `kubectl rollout status deployment/$SERVICE-stable -n production --timeout=180s`
3. Escalate to on-call SRE via PagerDuty

## Upstream Refs

ARCH-COMP-001, ARCH-COMP-002, ARCH-COMP-003, ARCH-COMP-004, IMPL-CODE-001, IMPL-GUIDE-001, DEVOPS-OBS-001
