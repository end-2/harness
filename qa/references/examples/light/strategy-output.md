# QA-STRATEGY-001 — Test Strategy (Todo API, light mode)

**Phase**: approved · **Mode**: light

## Mode and Scope

Light mode, inherited from Impl. Two components, one IDR, single SQLite backend — full RTM and per-environment matrix would be overkill.

| RE id | Title | Priority | Decision | Reason |
|-------|-------|----------|----------|--------|
| FR-001 | Create a todo | must | in scope | core CRUD |
| FR-002 | List todos | must | in scope | core CRUD |
| FR-003 | Mark todo done | must | in scope | core CRUD |
| FR-004 | Delete a todo | should | in scope | exercised by integration test |
| FR-005 | Bulk export CSV | wont | out | explicitly deferred per RE |
| RE-QA-001 | latency p95 | must | in scope | NFR |

## Test Pyramid

| Layer | Ratio | Rationale |
|-------|-------|-----------|
| unit | 0.70 | Storage repository + handler logic; small surface |
| integration | 0.30 | One FastAPI test client per CRUD path |

## NFR Test Plan

| Metric | Attribute | Target | Scenario | Tooling |
|--------|-----------|--------|----------|---------|
| RE-QA-001 | latency | p95 < 100 ms | 50 RPS for 60 s on /todos | k6 |

## Environment Matrix

| Environment | Purpose | Notes | Constraints |
|-------------|---------|-------|-------------|
| local | Developer suite | python 3.12, sqlite file | RE-CON-001 |
| ci | Full suite + NFR | GitHub Actions, sqlite in tmpfs | RE-CON-001 |

## Test Double Strategy

| Seam | Strategy | Notes |
|------|----------|-------|
| src/storage → sqlite | Real sqlite, fresh file per test | Repository pattern (IMPL-IDR-001) makes substitution trivial |

## Quality Gate Criteria

- `code_coverage_min`: 0.80
- `requirements_coverage_must_min`: 1.00
- `max_failed_tests`: 0
- `nfr_metric_refs`: [RE-QA-001]

## Upstream Refs

- RE-SPEC-001, RE-CON-001, RE-QA-001
- ARCH-COMP-001, ARCH-DEC-001
- IMPL-MAP-001, IMPL-CODE-001, IMPL-IDR-001, IMPL-GUIDE-001
