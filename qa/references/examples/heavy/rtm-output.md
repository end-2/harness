# QA-RTM-001 — Requirements Traceability Matrix (Payments)

**Phase**: approved · Generated and maintained via `artifact.py rtm-upsert`. Do not edit by hand.

## Coverage Summary

```
must:    6 covered / 0 partial / 0 uncovered
should:  1 covered / 1 partial / 0 uncovered
could:   0 covered / 1 partial / 0 uncovered
wont:    0 covered / 0 partial / 1 uncovered
```

## Matrix

| RE | Title | Priority | Arch | Impl | Tests | Status |
|----|-------|----------|------|------|-------|--------|
| FR-001 | Authenticate caller | must | ARCH-COMP-001 | IMPL-MAP-001 | QA-SUITE-001:TS-001-C01..C04 | covered |
| FR-002 | Initiate payment | must | ARCH-COMP-002 | IMPL-MAP-002 | QA-SUITE-002:TS-002-C01, TS-003-C01 | covered |
| FR-003 | Confirm payment | must | ARCH-COMP-002 | IMPL-MAP-002 | QA-SUITE-002:TS-002-C04, TS-002-C05 | covered |
| FR-004 | Refund payment | must | ARCH-COMP-002 | IMPL-MAP-002 | QA-SUITE-002:TS-002-C03, TS-002-C06 | covered |
| FR-005 | Idempotent retries | must | ARCH-COMP-002, ARCH-COMP-003 | IMPL-MAP-002, IMPL-MAP-003 | QA-SUITE-002:TS-002-C02 | covered |
| FR-006 | Webhook delivery | must | ARCH-COMP-004 | IMPL-MAP-004 | QA-SUITE-004:TS-004-C01..C03 | covered |
| FR-007 | Audit log export | should | ARCH-COMP-002 | IMPL-MAP-002 | QA-SUITE-002:TS-002-C07 | covered |
| FR-008 | 3DS step-up | could | ARCH-COMP-002 | IMPL-MAP-002 | QA-SUITE-002:TS-002-C08 | partial |
| FR-009 | BNPL | wont | — | — | — | uncovered |
| RE-QA-001 | latency p95 | must | ARCH-COMP-002 | IMPL-MAP-002 | QA-SUITE-005:TS-005-N01 | covered |
| RE-QA-002 | success rate | must | ARCH-COMP-002 | IMPL-MAP-002 | QA-SUITE-005:TS-005-N02 | covered |
| RE-QA-003 | webhook delivery time | should | ARCH-COMP-004 | IMPL-MAP-004 | QA-SUITE-005:TS-005-N03 | partial |

## Gap Commentary

- **FR-008 (could, partial)**: only the happy path is covered; challenge-required path requires the IdP step-up sandbox which is not in CI. Accepted as residual risk.
- **FR-009 (wont, uncovered)**: explicitly deferred per RE.
- **RE-QA-003 (should, partial)**: synthetic relay covers the throughput target but real subscriber latency is not measured. Accepted as residual risk.
