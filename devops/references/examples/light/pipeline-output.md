# DEVOPS-PL-001 — Pipeline Config (Todo API, light mode)

**Phase**: approved · **Mode**: light

Single-service TODO API. One pipeline covers the full lifecycle: build, test, deploy. No matrix builds, no multi-environment promotion.

## Platform

GitHub Actions. Selected as the default — the repository already uses GitHub, and the project has no CI platform constraint.

## Trigger Configuration

| Event | Condition | Stages triggered |
|-------|-----------|------------------|
| push | `main` branch | build → test → deploy |
| pull_request | any branch → `main` | build → test |
| tag | `v*` pattern | build → test → deploy |

## Pipeline Stages

### Stage 1: Build

| Step | Command | Notes |
|------|---------|-------|
| Checkout | `actions/checkout@v4` | |
| Setup Python | `actions/setup-python@v5` with 3.12 | From IMPL-GUIDE-001 prerequisites |
| Restore cache | key: `pip-${{ hashFiles('requirements.lock') }}` | |
| Install deps | `pip install -r requirements.lock` | From IMPL-GUIDE-001 build_commands |
| Lint | `ruff check src/` | From IMPL-GUIDE-001 conventions |
| Build image | `docker build -t todo-api:${{ github.sha }} .` | Single image target |

### Stage 2: Test

| Step | Command | Notes |
|------|---------|-------|
| Unit tests | `pytest tests/ --cov=src --cov-report=xml` | From IMPL-GUIDE-001 build_commands |
| Upload coverage | `actions/upload-artifact@v4` | Stored as CI artifact |

### Stage 3: Deploy

Runs only on `main` push and tag push. Deploys to production via rolling update.

| Step | Command | Notes |
|------|---------|-------|
| Push image | `docker push $ECR_REPO/todo-api:${{ github.sha }}` | ECR registry |
| Deploy | `kubectl set image deployment/todo-api api=todo-api:${{ github.sha }}` | Rolling update |
| Verify | `kubectl rollout status deployment/todo-api --timeout=120s` | Wait for rollout |

## Caching

| Dependency | Cache key | Strategy |
|------------|-----------|----------|
| pip packages | `pip-${{ hashFiles('requirements.lock') }}` | Restore on lockfile match |

## Secret Management

| Secret | Source | Injection |
|--------|--------|-----------|
| `AWS_ACCESS_KEY_ID` | GitHub Secrets | env, deploy step only |
| `AWS_SECRET_ACCESS_KEY` | GitHub Secrets | env, deploy step only |
| `DATABASE_URL` | GitHub Secrets | env, deploy step only |

## Environment

| Environment | Promotion rule | Approval |
|-------------|---------------|----------|
| production | auto on green (main branch) | no |

## Deployment Strategy

**Method**: rolling

**Rationale**: SLO target is 99.5% availability. Rolling update provides near-zero downtime and is appropriate for a single-service system with a relaxed SLO. No canary or blue-green overhead needed.

**Rolling parameters**:
- `maxUnavailable`: 0
- `maxSurge`: 1

## Rollback

**Trigger conditions**:

| Condition | Threshold | SLO ref |
|-----------|-----------|---------|
| error_rate | > 1% (5xx responses) | SLO-001 |
| latency_p99 | > 500ms | SLO-002 |

**Procedure**:

1. `kubectl rollout undo deployment/todo-api` — revert to previous image
2. `kubectl rollout status deployment/todo-api --timeout=120s` — wait for rollback
3. Verify error rate returns below 1% within 5 minutes
4. Notify `#deploy-alerts` with deployment ID and rollback reason

## Upstream Refs

ARCH-COMP-001, IMPL-CODE-001, IMPL-GUIDE-001
