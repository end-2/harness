# Arch Input Contract

How the QA skill reads the four Arch artifacts and turns each field into a test-design directive. Read this from `strategy` and `generate` whenever you need to know what a specific Arch field is supposed to produce in the test plan or test code.

## Location and readiness

- Arch artifacts live in `./artifacts/arch/` (override with `HARNESS_ARTIFACTS_DIR`).
- The four sections must all be present:
  - `ARCH-DEC-*` — decisions
  - `ARCH-COMP-*` — components
  - `ARCH-TECH-*` — technology stack
  - `ARCH-DIAG-*` — diagrams
- Every one must be in phase `approved`. If any is in `draft` / `in_review` / `revising`, stop and tell the user — QA must not run on unstable input.

## ARCH-DEC-* → test style

| Arch field | QA action |
|------------|-----------|
| `id` | Recorded in `arch_refs` on every test case that exists because of this decision |
| `decision` | Drives the per-pattern test style. See "Patterns → test style" below |
| `trade_offs` | Inform the residual-risk list when an unattractive trade-off shows up at runtime |
| `re_refs` | Propagated into the test case so the chain `RE → ARCH-DEC → test` survives |

### Patterns → test style

| ARCH-DEC pattern | Test style implication |
|------------------|------------------------|
| layered | One integration test per layer boundary; unit tests inside each layer with the next layer faked |
| hexagonal | One contract test per port; in-memory adapter implementations as the test doubles |
| event-driven | Async message tests at every consumer; idempotency tests for any handler that can be re-delivered |
| CQRS | Separate command-side and query-side suites; eventual-consistency window assertions on the query side |
| microservices | Contract tests at every service boundary; e2e tests reduced to the smallest meaningful path |
| pipeline / data-flow | Stage tests for every transformation; an end-to-end pipeline test that asserts the final shape |

## ARCH-COMP-* → integration boundaries

| Arch field | QA action |
|------------|-----------|
| `id` | `arch_refs` on every test case that targets this component |
| `name` | Becomes the suite title hint and the test directory name when `IMPL-MAP-*` does not pin one |
| `responsibility` | Lifted into the suite description; the SRP test line during review is "does this suite have one responsibility?" |
| `interfaces` | Each interface is a contract test target. Method signatures drive the input partition for unit tests |
| `dependencies` | Drives the integration test set: each declared dependency edge is a candidate integration scenario |
| `re_refs` | Propagated into the test case |

Interface protocols: when `interfaces` specifies a protocol (HTTP, gRPC, queue), the test plan adds both a typed contract test (language-level) and a wire contract test (transport-level).

## ARCH-TECH-* → test framework

| Arch field | QA action |
|------------|-----------|
| `category` | Slot in the testing toolchain (`testing` → unit/integration framework, `e2e` → browser/api driver, `load` → NFR tooling) |
| `choice` | The concrete framework. **This is the only allowed set** — do not invent a test framework. Common pickups: TypeScript → Vitest / Jest; Python → pytest; Go → `testing` + testify; Rust → built-in `#[test]` + insta; Java → JUnit 5; .NET → xUnit |
| `decision_ref` / `constraint_ref` | When present, drag along the same constraints (e.g. a `hard` constraint that pins a Java version pins the JUnit version too) |

When Arch did **not** pin a testing framework, fall back to the stack idiom:

- Python → pytest
- TypeScript / JavaScript → Vitest (or Jest if the project already uses it)
- Go → `testing` + `github.com/stretchr/testify`
- Rust → built-in `#[test]` + `insta` for snapshots, `proptest` for property tests
- Java → JUnit 5
- C# → xUnit

Record the chosen framework on the suite's `framework` field.

## ARCH-DIAG-* → e2e and integration scenarios

| Diagram type | QA action |
|-------------|-----------|
| `c4-context` | Informational only; helps decide which external systems need a contract test |
| `c4-container` | One or more integration suites per container boundary; an e2e test that walks the container topology end to end |
| `sequence` | The single most useful diagram for QA: each sequence diagram is a candidate e2e scenario. The method-call order in the diagram is the assertion order in the test |
| `data-flow` | Pipeline tests: one test per transformation stage, plus a full-pipeline test |

## Traceability propagation

Every test case carries `arch_refs` listing the Arch ids it depends on (typically one component plus zero or more decisions). Every `QA-SUITE-*` artifact links upstream to at least one `ARCH-COMP-*`.

## When Arch is wrong

If an Arch decision implies a test that the project genuinely cannot run (a contract framework that does not exist for the chosen stack, a sequence diagram whose endpoints have no Impl module), **do not** patch around it inside QA. Stop, escalate to the user, and recommend they re-open Arch. Arch is the source of truth for structure.
