# Workflow — Stage 3: review

## Role

Verify that the generated tests actually cover the requirements they claim to cover, that every test traces back through `impl_refs → arch_refs → re_refs` to a single root requirement, and that the assertions are non-vacuous. Refresh the RTM, classify every gap, and route. **Run as a subagent.** Subagents emit a structured report file and never edit metadata directly.

## Inputs

- The generated test source files under the project tree.
- The four QA section artifacts (`QA-STRATEGY-*`, `QA-SUITE-*`, `QA-RTM-*`, optional `QA-REPORT-*`) — read-only.
- The RE / Arch / Impl artifacts cited by the strategy — read-only.
- A pre-allocated report path from `artifact.py report path --kind review --stage review --scope all`.

## Three review axes

### 1. Requirements coverage

For every `RE-SPEC-*` row in scope:

- At least one test case in some `QA-SUITE-*` carries an `acceptance_criteria_ref` to one of its acceptance criteria.
- Each `acceptance_criteria` row of a Must requirement is covered by at least one case.
- Every `RE-QA-*` quality attribute with a `metric` has a corresponding NFR test scenario in some suite.

Classify the row as `covered` (all criteria touched), `partial` (some criteria covered, some not), or `uncovered` (no test cites this RE id at all).

### 2. Test strength

Read each test file. Flag a case as weak when:

- The assertion is `assert True`, `assert result is not None`, or any other tautology.
- The test passes against an obvious stub (the seam returns the same value the assertion checks).
- A boundary technique was claimed but no boundary value is exercised.
- A property test has fewer than 3 generated examples or no shrinking.
- The test depends on time, ordering, or an external service without a fake — flaky pattern.

### 3. Traceability

- Every `QA-SUITE-*.test_cases[].acceptance_criteria_ref` resolves to a real `RE-SPEC-*` criterion.
- Every `IMPL-MAP-*` entry has at least one test case targeting its `module_path`.
- Every `RE-QA-*.metric` has a `nfr` test scenario.
- Every test file under the project tree maps back to some `IMPL-MAP-*.module_path` via the convention recorded in `IMPL-GUIDE-*`.

## Gap classification

Each finding goes into the report `items[]` array with one of these `gap_type` values:

| `gap_type` | Meaning |
|-----------|---------|
| `missing_test` | RE id has no test case at all |
| `partial_criteria` | Some `acceptance_criteria` rows have no case |
| `weak_assertion` | A test exists but its assertion does not actually constrain behaviour |
| `missing_nfr_scenario` | A `RE-QA-*.metric` has no NFR test |
| `traceability_break` | A case cites a ref that does not resolve, or vice versa |
| `flaky_pattern` | Time / ordering / external dependency without a fake |

Each item also carries:

- `re_id` — the requirement under review.
- `priority` — MoSCoW (lifted from RE).
- `suggested_fix` — concrete generation directive (e.g. "add a boundary case for FR-002.AC-3 covering empty username").
- `auto_fixable` — boolean. True if Stage 2 could close the gap with the inputs already present.

## Routing

- `covered` rows and any gap on a Should / Could / Won't requirement → **accept**. Record as residual risk; do not block.
- `must` gap with `auto_fixable: true` → **route back to generate** with a targeted directive. Loop until either the gap closes or it flips to `auto_fixable: false`.
- `must` gap with `auto_fixable: false` → **escalate to the user**, citing the RE id and what is missing. Examples: an NFR metric whose tooling is not in the project, an `acceptance_criteria` so vague that no observable assertion exists.

After the main agent applies the routing decisions, refresh every affected RTM row via `rtm-upsert` with the new status and (if still partial / uncovered) a `--gap` description.

## Subagent contract

The subagent **must**:

1. Read the QA section artifacts and the RE / Arch / Impl artifacts directly (paths supplied as inputs).
2. Read every test file under the project tree.
3. Walk every `acceptance_criteria` and check coverage.
4. Walk every test file and classify it on the three axes above.
5. Write the findings into the pre-allocated report file. The frontmatter must include `verdict` (`pass` if no Must gaps, `at_risk` if Should/Could gaps only, `fail` if any Must gap, `escalated` if any Must gap is `auto_fixable: false`), `summary`, and `items[]`.
6. Emit `proposed_meta_ops` for any RTM row that should be refreshed:
   ```yaml
   proposed_meta_ops:
     - op: rtm-upsert
       re_id: FR-014
       status: partial
       gap: "decision-table covers 3 of 4 flag combinations"
       arch_refs: [ARCH-COMP-002]
       impl_refs: [IMPL-MAP-002]
       test_refs: [QA-SUITE-002:TS-002-C01, QA-SUITE-002:TS-002-C02, QA-SUITE-002:TS-002-C03]
   ```
7. Return only `report_id + verdict + summary` in the agent message — no body, no diffs, no inline findings.

Subagents **never** call `artifact.py rtm-upsert / set-phase / approve / link / gate-evaluate` directly. The main agent applies every meta op after validating the report.

## Loop termination

The review → generate → review loop terminates when one of:

1. The report's `verdict` is `pass` (no Must gaps remain).
2. The report's `verdict` is `at_risk` and the user accepts the residual risks.
3. The report's `verdict` is `escalated` and the user has either resolved the blocking item or instructed QA to proceed with `escalated` rows recorded as residual risks.

In every case, transition each Test Suite and the RTM artifact to `approved` (via `artifact.py approve`) before handing off to Stage 4. Test Strategy is approved as soon as its in_review draft has been confirmed.
