# Adaptive Depth

QA runs in one of two modes — **light** or **heavy** — and the mode drives how much of the four-stage workflow actually executes. The goal is correct sizing: a CRUD scaffold should not carry a 40-row RTM and a four-environment matrix, and a genuinely distributed system should not get a single-suite drop.

## How the mode is decided

QA's mode is **inherited from Impl's mode**, which in turn was inherited from Arch's. The pipeline stays coherent: a system small enough for light Arch and light Impl is also small enough for light QA.

**Detection**: read the Impl metadata. Specifically:

1. If `IMPL-MAP-*.implementation_map` has more than 3 entries → heavy.
2. Or if `IMPL-IDR-*.decisions` has more than 2 entries → heavy.
3. Or if `IMPL-CODE-*.module_dependencies` describes more than one module boundary → heavy.
4. Otherwise → light.

Tell the user which mode you chose and which signal you used. The user may override by saying "run QA in heavy mode" or "run QA in light mode" — record the override in the Test Strategy's `mode` field and note the reason in the markdown.

## What light mode means

Light mode is **not lazy**. It is "correct for a small system".

| Stage | Light mode action |
|-------|------------------|
| strategy | Single Test Strategy artifact. Pyramid limited to two layers (typically `unit` + `integration`). NFR plan covers only Must `RE-QA-*` rows. Environment matrix lists `local` + `ci`. Test-double strategy enumerates only the external dependencies that actually need a decision. |
| generate | One Test Suite artifact, usually one suite per `IMPL-MAP-*` entry collapsed into a single file. RTM includes Must rows in full and Should rows as a single line each. Skip Could/Won't rows entirely. |
| review | Run the requirements-coverage and traceability axes. Skip the deep test-strength axis unless a Must row looks weak. Subagent still emits a report file. |
| report | Single test run, single coverage measurement. NFR results limited to Must metrics. Quality gate criteria are the defaults from PLAN (`code_coverage_min: 0.80`, `requirements_coverage_must_min: 1.00`). |

Four sections are still produced, but with the following trimmed depth:

- **Test Strategy**: short pyramid, defaults for the gate, no test-double row for trivial in-process libraries.
- **Test Suite**: one or two suites total, each with the cases needed to cover Must rows plus the highest-value Should rows.
- **RTM**: one row per Must RE, plus a row per Should that has a corresponding test. Could/Won't rows are not entered.
- **Quality Report**: code coverage by total only (not per module), NFR table only for Must metrics, residual risks may be empty.

## What heavy mode means

| Stage | Heavy mode action |
|-------|------------------|
| strategy | One Test Strategy artifact in full form. Pyramid covers all relevant layers including `contract` and `nfr`. NFR plan has one row per `RE-QA-*` metric. Environment matrix lists `local` / `ci` / `staging` / `prod-like`. Test-double strategy has one row per `IMPL-CODE-*.external_dependencies` entry. |
| generate | One Test Suite artifact per Arch component group (typically one per `ARCH-COMP-*` or per `IMPL-MAP-*` cluster). RTM rows for every Must, Should, Could, and Won't with explicit reason. |
| review | All three axes in full: requirements coverage, test strength (assertion quality, technique fit, flakiness), traceability. Run as a subagent that emits one item per gap. |
| report | Full test runs for every suite, per-module coverage, full NFR matrix, residual-risk roll-up by priority, recommendations. Quality gate evaluated; verdict drives release. |

Four sections in full form:

- **Test Strategy**: full pyramid with rationale, full NFR plan, full environment matrix, complete test-double strategy.
- **Test Suite**: multiple suites, one per Arch component group; every test case carries `acceptance_criteria_ref` and `test_node`.
- **RTM**: every RE row present, with `coverage_status` and (when needed) `gap_description`. The RTM is the canonical roll-up.
- **Quality Report**: per-module coverage, full NFR results, residual risks by priority, gate criteria + actuals + verdict + reasons + evaluated_at.

## Mode is not about quality

Both modes produce a real quality gate. Mode controls **how much structure travels alongside the gate**, not how carefully the tests are written. A light-mode QA still verifies every Must requirement, still measures coverage, still runs the gate evaluation. It just does not generate a 40-row RTM when 12 rows cover the requirements actually present.
