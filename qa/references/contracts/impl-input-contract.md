# Impl Input Contract

How the QA skill reads the four Impl artifacts and turns each field into a test-placement and test-double directive. Read this from `strategy` and `generate` whenever you need to know what a specific Impl field is supposed to drive.

## Location and readiness

- Impl artifacts live in the standalone location `./artifacts/impl/`. In orchestrated runs, Orch passes the exact upstream Impl artifact paths separately. `HARNESS_ARTIFACTS_DIR` still points to QA's own output directory.
- The four sections must all be present:
  - `IMPL-MAP-*` — implementation map
  - `IMPL-CODE-*` — code structure
  - `IMPL-IDR-*` — implementation decisions
  - `IMPL-GUIDE-*` — implementation guide
- Every one must be in phase `approved`. If any is in `draft` / `in_review` / `revising`, stop and tell the user — QA must not run on unstable input.

## IMPL-MAP-* → test placement and target

| Impl field | QA action |
|------------|-----------|
| `id` | Recorded in `impl_refs` on every test case targeting this entry |
| `component_ref` | Cross-reference for the suite's `arch_refs` |
| `module_path` | The directory under which the test files for this module live (mirrored or co-located, depending on `IMPL-GUIDE-*.conventions.tests`) |
| `entry_point` | The file the unit suite imports first |
| `internal_structure` | Hint for sub-suite organisation when one module has multiple cohesive units |
| `interfaces_implemented` | Each entry is a contract test target — verify the implementation actually honours the interface shape from Arch |
| `arch_refs` / `re_refs` | Propagated into the test case so the chain `RE → ARCH → IMPL → test` survives |

A useful default: one Test Suite per `IMPL-MAP-*` entry in light mode; one Test Suite per Arch component group in heavy mode.

## IMPL-CODE-* → seam map and dependency manifest

| Impl field | QA action |
|------------|-----------|
| `project_root` | Anchor for relative test file paths |
| `directory_layout` | Reference for where to place new test directories without disturbing existing layout |
| `module_dependencies` | The seam graph. An edge `from → to` is a candidate test boundary; the next layer is what gets faked in the from-side unit test |
| `external_dependencies` | Every row is a candidate test double. The QA test-double strategy lists one decision per row: real / in-memory fake / contract test + recorded fixtures / mock at the boundary |
| `build_config` | Drives how the test runner invokes the build (e.g. `pyproject.toml` → `pytest`; `Cargo.toml` → `cargo test`) |
| `environment_config` | Test environment variables; the test runner must set them or the suite must skip with a clear reason |

A test that imports an `external_dependencies` row directly without a doubling decision is a smell — flag it during `review`.

## IMPL-IDR-* → per-pattern testability

Patterns recorded in `pattern_applied` change how a test should be written. Apply these rules during `generate`:

| Pattern | Test rule |
|---------|-----------|
| Repository | Test the repository against an in-memory fake; test consumers with the in-memory repo, not a mock |
| Strategy | One test class per concrete strategy; one parameterised test that proves the dispatch picks the right strategy |
| Decorator | Verify both the wrapped behaviour (delegation) and the decoration (added effect); prefer property tests for invariants |
| Adapter | Contract test against the adapted protocol; unit test the translation logic with table-driven inputs |
| Observer / Pub-Sub | Test publishers in isolation with a recording subscriber; test subscribers in isolation with a synthetic event stream |
| Circuit Breaker | Test the closed → open → half-open → closed cycle as a state machine; do not test the timing accuracy directly |
| Outbox | Test that the writer enqueues and that the relay drains; test idempotency with replays |
| Saga / Orchestrator | Each step has its own test; the orchestrator has an end-to-end test with stub steps |

If an IDR exists but its pattern is not in this table, fall back to the rule "test the visible behaviour of the pattern, not its internals".

## IMPL-GUIDE-* → conventions and run commands

| Impl field | QA action |
|------------|-----------|
| `prerequisites` | The set of tools the test environment must have; record on the strategy's environment matrix |
| `setup_steps` | Lifted into the strategy's environment matrix `notes` so a future operator can reproduce the suite |
| `build_commands` | The test runner usually builds first; mirror these commands in CI |
| `run_commands` | The Quality Report stage uses these to actually invoke the suite |
| `conventions.tests` | Authoritative for test layout (co-located vs mirrored, file naming, fixture style). Follow it exactly |
| `extension_points` | Hints for where to add a new test when the next iteration brings new requirements |

## Traceability propagation

Every test case carries `impl_refs` listing every `IMPL-*` id it depends on (typically one `IMPL-MAP-*` plus zero or more `IMPL-IDR-*` rows for the patterns applied). Every `QA-SUITE-*` artifact links upstream to at least one `IMPL-MAP-*`.

## When Impl is wrong

If an Impl module is missing for a Must requirement, **do not** invent a target. Stop, escalate to the user, and recommend they re-open Impl. Impl is the source of truth for what the code actually contains.
