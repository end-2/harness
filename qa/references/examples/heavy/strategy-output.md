# QA-STRATEGY-001 — Test Strategy (Payments service, heavy mode)

**Phase**: approved · **Mode**: heavy

A multi-service payments platform: an API gateway, a payments orchestrator, an idempotency store, and an outbound webhook relay. Heavy Arch (Container diagram + 5 ADRs), heavy Impl (4 modules, 3 IDRs).

## Mode and Scope

Heavy mode, inherited from Impl. Distributed boundaries, IdP integration, payment provider with strict idempotency rules, and SLO-bound NFRs require the full pyramid and a real environment matrix.

| RE id | Priority | Decision | Reason |
|-------|----------|----------|--------|
| FR-001 (auth) | must | in scope | core auth flow |
| FR-002 (initiate payment) | must | in scope | core domain |
| FR-003 (confirm payment) | must | in scope | core domain |
| FR-004 (refund) | must | in scope | core domain |
| FR-005 (idempotent retries) | must | in scope | provider mandates idempotency |
| FR-006 (webhook delivery) | must | in scope | downstream integrations rely on it |
| FR-007 (audit log export) | should | in scope | compliance |
| FR-008 (3DS step-up) | could | partial | ship if time allows |
| FR-009 (BNPL) | wont | out | explicitly deferred per RE |
| RE-QA-001 (latency p95) | must | in scope | SLO |
| RE-QA-002 (success rate) | must | in scope | SLO |
| RE-QA-003 (webhook delivery time) | should | in scope | best-effort SLO |

## Test Pyramid

| Layer | Ratio | Rationale |
|-------|-------|-----------|
| unit | 0.55 | 4 modules × ~6 unit suites each (per IMPL-MAP fan-out) |
| integration | 0.20 | 4 inter-module contracts (gateway↔orchestrator, orchestrator↔store, orchestrator↔relay, relay↔provider stub) |
| contract | 0.10 | OpenAPI conformance + provider HTTP contract recorded fixtures |
| e2e | 0.10 | 3 critical journeys: initiate→confirm, initiate→refund, retry idempotency |
| nfr | 0.05 | k6 load profile per RE-QA metric |

## NFR Test Plan

| Metric | Attribute | Target | Scenario | Tooling |
|--------|-----------|--------|----------|---------|
| RE-QA-001 | latency | p95 < 200 ms | 100 RPS for 5 min on /payments | k6 |
| RE-QA-002 | reliability | success rate > 99.9% | 1h soak at 50 RPS, kill provider stub once | k6 + chaos toolkit |
| RE-QA-003 | webhook delivery | 95% within 30 s | 200 events/min for 10 min | k6 + relay stub |

## Environment Matrix

| Environment | Purpose | Notes | Constraints |
|-------------|---------|-------|-------------|
| local | Unit + integration | docker compose: postgres 16, redis 7 | RE-CON-002 |
| ci | Full suite (unit/integration/contract) | GitHub Actions, services as docker compose | RE-CON-002 |
| staging | e2e + nfr | k8s namespace `payments-staging`, real provider sandbox | RE-CON-003 |
| prod-like | smoke + soak | mirrors prod topology | RE-CON-003, RE-CON-004 |

## Test Double Strategy

| Seam | Strategy | Notes |
|------|----------|-------|
| orchestrator → payment provider HTTP | contract test + recorded fixtures, real call only in staging | provider charges per call; Adapter pattern (IMPL-IDR-002) |
| orchestrator → idempotency store | in-memory fake for unit, real redis for integration | Repository (IMPL-IDR-001) |
| relay → webhook subscribers | recording subscriber in tests | Pub-Sub (IMPL-IDR-003) |
| gateway → identity provider | fake at HTTP layer | tokens issued by test signer |

## Quality Gate Criteria

- `code_coverage_min`: 0.85
- `requirements_coverage_must_min`: 1.00
- `max_failed_tests`: 0
- `nfr_metric_refs`: [RE-QA-001, RE-QA-002, RE-QA-003]

## Upstream Refs

RE-SPEC-001, RE-CON-002, RE-CON-003, RE-CON-004, RE-QA-001..003, ARCH-COMP-001..004, ARCH-DEC-001..005, ARCH-DIAG-001, IMPL-MAP-001..004, IMPL-CODE-001, IMPL-IDR-001..003, IMPL-GUIDE-001.
