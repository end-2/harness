# RE Input Contract

How the QA skill reads the three RE artifacts and turns each field into a test-derivation directive. Read this from `strategy` and `generate` whenever you need to know what a specific RE field is supposed to produce in the test plan or test code.

## Location and readiness

- RE artifacts live in the standalone location `./artifacts/re/`. In orchestrated runs, Orch passes the exact upstream RE artifact paths separately. `HARNESS_ARTIFACTS_DIR` still points to QA's own output directory.
- The three sections must all be present:
  - `RE-SPEC-*` — requirements specification
  - `RE-CON-*` — constraints
  - `RE-QA-*` — quality attribute priorities
- Every one must be in phase `approved`. If any is in `draft` / `in_review` / `revising`, stop and tell the user — QA must not run on unstable input.

## RE-SPEC-* → test cases

| RE field | QA action |
|----------|-----------|
| `id` | Recorded as `re_refs` on every test case derived from this row |
| `category` | `functional` → unit / integration / e2e cases; `non_functional` → NFR cases |
| `title` | Lifted into the suite's `description` for the case set |
| `acceptance_criteria` | Each criterion becomes one or more test cases. The criterion id is recorded on the case as `acceptance_criteria_ref` so a case can be walked back to the exact criterion that justifies it |
| `priority` | MoSCoW gate. `must` → mandatory coverage (escalate if uncovered); `should` → best-effort coverage (residual risk if missing); `could` → covered only if an Impl module exists; `wont` → recorded as out-of-scope, never tested |
| `dependencies` | Drives the integration test set: every dependency edge is a candidate integration scenario between the depending and depended-on Impl modules |

The criterion → case conversion is the single most important rule of `generate`. A criterion that says "users with more than 5 failed logins are locked out for 15 minutes" produces at least three cases: 4 failures (no lockout), 5 failures (lockout begins), 5 failures + 15 minutes (lockout expires). The technique is `boundary_value` (the off-by-one count) plus `state_transition` (locked → unlocked).

## RE-CON-* → environment matrix and compliance tests

| RE field | QA action |
|----------|-----------|
| `id` | Recorded as a constraint ref on the relevant environment matrix row or the compliance test case |
| `type` | `regulatory` → compliance test target (record in the suite as a `contract` or `e2e` test, depending on what the constraint says); `technical` → environment matrix row (e.g. "must run on Postgres 15" pins the CI environment); `business` → usually informational, only becomes a test if it constrains observable behaviour |
| `flexibility` | `hard` → non-negotiable, must be visibly verified; `soft` → best effort; `informational` → no test |
| `rationale` | Copied into the environment matrix `notes` so a future reader knows why an environment row exists |

## RE-QA-* → NFR test plan

This is the source of every `nfr` test case. The mapping is mechanical:

| RE field | QA action |
|----------|-----------|
| `id` | Recorded as the `metric_id` on the NFR scenario and the matching `nfr_results` row in the Quality Report |
| `attribute` | Selects the tooling category: latency → load tester (k6, locust, gatling); availability → chaos / fault injection; durability → restore drills; security-class attributes are still QA's job to verify, but the `security` skill owns the threat model |
| `priority` | Same MoSCoW gate as RE-SPEC-* |
| `metric` | Lifted **verbatim** into the strategy's NFR plan and into the report's `nfr_results.target`. Do not paraphrase, do not "round up" — the gate evaluator parses the same string |
| `trade_off_notes` | Recorded in the strategy as the tolerance window when judging "close to" the metric |

## Traceability propagation

Every test case must carry `re_refs` listing every RE id it covers (typically one, sometimes more if the criterion is shared). Every RTM row must carry `re_id` plus the chain `arch_refs / impl_refs / test_refs`. The chain is built incrementally by `generate` calling `rtm-upsert` after each new case.

## When RE is wrong

If an RE row is genuinely untestable (no observable assertion can be derived, or the criterion contradicts another), **do not** invent a test or paper over the problem. Stop, escalate to the user, and recommend they re-open RE. RE is the source of truth for what counts as "done".
