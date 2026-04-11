# QA-SUITE-002 — Payments Orchestrator Test Suite

**Phase**: approved · **Target**: `src/orchestrator/`

Anchored to `IMPL-MAP-002` (orchestrator module). Covers FR-002, FR-003, FR-004, FR-005.

## Suite Summary

| Suite id | Type | Framework | Test files |
|----------|------|-----------|------------|
| TS-002 | unit | pytest 8.x | tests/orchestrator/test_payment.py, tests/orchestrator/test_idempotency.py |
| TS-003 | integration | pytest + httpx | tests/orchestrator/test_provider_contract.py |

## Cases

### TS-002-C01 — initiate payment with valid card returns pending state

- Technique: `example_based`
- Acceptance criterion: `FR-002.AC-1`
- **Given**: a customer with a valid tokenised card
- **When**: POST /payments with `{amount: 10_00, currency: "USD", card_token: "tok_ok"}`
- **Then**: 201 + body `{state: "pending", id: <uuid>}`, and a row exists in the orchestrator store
- test_node: `tests/orchestrator/test_payment.py::test_initiate_returns_pending`

### TS-002-C02 — duplicate idempotency key returns the original payment

- Technique: `state_transition`
- Acceptance criterion: `FR-005.AC-1`
- **Given**: a payment was already initiated with idempotency key `K1`
- **When**: POST /payments with the same key and the same body
- **Then**: 200 (not 201), body equals the original payment id, store row count unchanged
- test_node: `tests/orchestrator/test_idempotency.py::test_replay_returns_original`

### TS-002-C03 — refund cannot exceed original amount

- Technique: `boundary_value`
- Acceptance criterion: `FR-004.AC-2`
- **Given**: a confirmed payment of 100_00 cents
- **When**: POST /payments/{id}/refund with `{amount: 100_01}`
- **Then**: 422 with error `refund_exceeds_original`, no provider call
- test_node: `tests/orchestrator/test_payment.py::test_refund_overflow_rejected`

### TS-003-C01 — provider contract: charge request shape

- Technique: `decision_table`
- Acceptance criterion: `FR-002.AC-2`
- **Given**: the recorded provider fixtures in tests/fixtures/provider/
- **When**: orchestrator issues a charge for each (currency, amount) row in the table
- **Then**: outbound HTTP request matches the recorded shape byte-for-byte (modulo idempotency key)
- test_node: `tests/orchestrator/test_provider_contract.py::test_charge_shape`

## Upstream Refs

- RE-SPEC-001 (FR-002, FR-003, FR-004, FR-005)
- ARCH-COMP-002 (orchestrator)
- IMPL-MAP-002, IMPL-IDR-001 (Repository), IMPL-IDR-002 (Adapter)
- QA-STRATEGY-001
