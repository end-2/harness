# QA-REPORT-001 — Quality Report (Payments, sprint 23)

**Phase**: approved (auto by gate-evaluate) · **Verdict**: pass

## Executive Summary

All 6 Must functional requirements and all 2 Must NFR metrics are covered and passing. 1 Should and 1 Could carry residual risk; both are accepted. Gate verdict: **pass**.

## Code Coverage

| Module | Lines | Branches | Notes |
|--------|-------|----------|-------|
| src/gateway/ | 0.91 | 0.86 | IMPL-MAP-001 |
| src/orchestrator/ | 0.93 | 0.88 | IMPL-MAP-002 |
| src/idempotency_store/ | 0.95 | 0.92 | IMPL-MAP-003 |
| src/relay/ | 0.87 | 0.81 | IMPL-MAP-004 |
| **total** | **0.91** | **0.86** | |

## Requirements Coverage (from `rtm-gap-report`)

```
must:    6 covered / 0 partial / 0 uncovered
should:  1 covered / 1 partial / 0 uncovered
could:   0 covered / 1 partial / 0 uncovered
wont:    0 covered / 0 partial / 1 uncovered
```

## NFR Results

| Metric | Target | Actual | Pass | Notes |
|--------|--------|--------|------|-------|
| RE-QA-001 | p95 < 200 ms | 167 ms | ✓ | k6 run id 412 |
| RE-QA-002 | success rate > 99.9% | 99.96% | ✓ | k6 + chaos toolkit run id 413 |
| RE-QA-003 | webhook 95% within 30 s | 92% within 30 s | partial | synthetic relay only; accepted as residual risk |

## Quality Gate

| Criterion | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| code_coverage | ≥ 0.85 | 0.91 | ✓ |
| requirements_coverage_must | ≥ 1.00 | 1.00 | ✓ |
| max_failed_tests | ≤ 0 | 0 | ✓ |
| nfr_results | all pass | RE-QA-003 partial (Should) | accepted |

**Verdict**: pass · evaluated_at 2026-04-11T14:00:00Z

## Residual Risks

- **FR-008 (could, partial)** — challenge-required 3DS path requires the IdP step-up sandbox which is not in CI. Tracked for next iteration.
- **RE-QA-003 (should, partial)** — real subscriber latency not measured; will be picked up by operation as a synthetic monitor.

## Recommendations

- Wire the IdP step-up sandbox into CI before opening the v2 milestone.
- Move the synthetic relay metric from staging to a continuous probe in operation.
- Increase relay branch coverage above 0.85 by exercising backoff edge cases.
