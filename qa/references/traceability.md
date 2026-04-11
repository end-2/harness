# Traceability

QA's job is not just to write tests — it is to maintain the chain `RE → Arch → Impl → QA → test_node` so that any requirement can be traced to the exact assertion that proves it (and any failed assertion can be traced back to the requirement it threatens). The Requirements Traceability Matrix (RTM) is the single artifact that holds this chain.

## The chain

```
RE-SPEC-001 (FR-002 "user can log in")
   │
   ├─ ARCH-COMP-001 "auth service"
   │     │
   │     └─ IMPL-MAP-001 src/auth/
   │           │
   │           └─ QA-SUITE-001:TS-001 "auth service unit tests"
   │                 │
   │                 └─ TS-001-C01 "login with valid credentials returns a session"
   │                       │
   │                       └─ tests/auth/test_service.py::test_login_with_valid_credentials
```

Each link in the chain is recorded somewhere:

| Link | Where it lives |
|------|----------------|
| RE → Arch | `ARCH-COMP-*.re_refs` |
| Arch → Impl | `IMPL-MAP-*.arch_refs` |
| Impl → QA | `QA-SUITE-*.impl_refs` (and `arch_refs`, `re_refs`) |
| QA → test runner | `test_case.test_node` |
| RE → QA (the rollup) | `QA-RTM-*.rtm_rows[]` |

The RTM is the **only** place where the full chain is written down in one row. Everywhere else you see only one or two links at a time.

## RTM row construction

A correct RTM row answers four questions:

1. **What requirement?** `re_id`, `re_title`, `re_priority`.
2. **Where is it built?** `arch_refs`, `impl_refs`.
3. **What proves it works?** `test_refs` of the form `<suite-id>:<case-id>`.
4. **Is it actually covered?** `coverage_status` ∈ `covered` / `partial` / `uncovered`. If not fully covered, `gap_description` explains why.

Rows are managed exclusively through `artifact.py rtm-upsert`:

```bash
python ${SKILL_DIR}/scripts/artifact.py rtm-upsert QA-RTM-001 \
    --re-id FR-002 \
    --re-title "User can log in with email and password" \
    --re-priority must \
    --arch-refs ARCH-COMP-001 \
    --impl-refs IMPL-MAP-001 \
    --test-refs QA-SUITE-001:TS-001-C01,QA-SUITE-001:TS-001-C02 \
    --status covered
```

Calling `rtm-upsert` against an existing `re_id` merges the new refs into the existing row instead of overwriting.

## How to populate the RTM

Populate the RTM from RE rows, **not** from test cases. Walking RE → tests guarantees that you notice missing tests; walking tests → RE only catches tests that exist for nothing.

For each RE row:

1. Look up which `ARCH-COMP-*` claims it via `re_refs`. If none does, the gap is upstream — escalate, do not invent a row.
2. Look up which `IMPL-MAP-*` claims that component via `arch_refs`.
3. Find the `QA-SUITE-*` whose `impl_refs` include that map entry. List every test case whose `acceptance_criteria_ref` points at one of this RE's criteria.
4. Choose `coverage_status`:
   - **covered** — every acceptance criterion has at least one case.
   - **partial** — some but not all acceptance criteria have cases. Set `gap_description` to enumerate the missing criteria.
   - **uncovered** — no test case references this RE. Set `gap_description` to a one-line reason (typically "deferred — Should/Could/Won't" or "no test target — escalate to Impl").
5. Run `rtm-upsert`.

Light mode skips Could/Won't rows entirely. Heavy mode writes one row per RE regardless of priority — Won't rows simply have `coverage_status: uncovered` and a `gap_description: "explicitly deferred per RE"`.

## Gap roll-up

`artifact.py rtm-gap-report` is the only blessed source of the gap summary. It groups rows by MoSCoW priority and prints the count by status:

```
must:    12 covered / 0 partial / 0 uncovered
should:   8 covered / 2 partial / 0 uncovered
could:    3 covered / 0 partial / 4 uncovered
wont:     0 covered / 0 partial / 6 uncovered
```

A non-zero exit indicates at least one Must row is `partial` or `uncovered`. The Quality Report's residual-risks section quotes this output verbatim — never re-derive it by walking the rows yourself.

## Gap analysis routing

Gaps surfaced by `rtm-gap-report` are routed by priority:

| Priority | Gap | Routing |
|----------|-----|---------|
| Must | partial / uncovered, fix is local | `review` returns `verdict: fail` with `auto_fixable: true`; main agent loops back to `generate` |
| Must | partial / uncovered, fix needs upstream change | `review` returns `verdict: escalated` with `auto_fixable: false`; main agent escalates to user |
| Should | partial / uncovered | Accept as residual risk; record in Quality Report |
| Could / Won't | uncovered | Expected; record once in Quality Report and move on |

## When the chain breaks

A broken chain is itself a gap, and the `review` stage flags it as `gap_type: traceability_break`. Common breaks:

- A test case has `acceptance_criteria_ref: FR-002.AC-1` but no `RE-SPEC-*` defines that criterion. Fix at RE.
- A `QA-SUITE-*` has `impl_refs: [IMPL-MAP-099]` that does not exist. Fix at Impl or fix the suite.
- An RTM row claims `coverage_status: covered` but `test_refs` is empty. The script will reject this on `validate`.
- A test_node in a case does not exist in the actual test runner output. Fix the test file or the case.

The `validate` subcommand catches the structural breaks (missing refs, unknown ids in the local artifact directory). The `review` subagent catches the semantic ones (test exists but doesn't actually assert the criterion).
