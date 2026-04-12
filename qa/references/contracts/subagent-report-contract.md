# Subagent Report Contract

The QA `review` and `report` stages run as subagents. They cannot edit metadata directly, cannot edit source files, and cannot send long messages back to the main agent. Instead, every subagent allocates a report file under `./artifacts/qa/.reports/`, writes its findings into that file, and returns only `report_id + verdict + summary` in its message.

This document specifies the exact frontmatter schema that the script (`artifact.py report validate`) checks, and the per-stage `items[]` and `proposed_meta_ops[]` shapes that the main agent expects.

## Allocation

Before spawning the subagent, the main agent allocates a report path:

```bash
python ${SKILL_DIR}/scripts/artifact.py report path \
    --kind <review|report> --stage <review|report> --scope all
```

The script writes a stub file with the required frontmatter. The subagent receives the path as one of its inputs and **edits the existing file** — it does not create a new one.

## Frontmatter schema

```yaml
---
report_id: review-all-20260411T140000Z   # filename stem; do not change
kind: review                              # review | report
skill: qa                                 # always 'qa'
stage: review                             # the stage that produced the report
created_at: 2026-04-11T14:00:00Z          # ISO 8601 UTC; do not change
target_refs: []                           # optional; QA artifact ids the report is about
verdict: pass                             # pass | at_risk | fail | escalated | n/a
summary: "0 must gaps, 2 should gaps accepted as residual risk"
proposed_meta_ops: []                     # see "Meta ops" below
items: []                                 # see per-stage shape below
---
```

Required fields: `report_id`, `kind`, `skill`, `stage`, `created_at`, `target_refs`, `verdict`, `summary`. The script's `report validate` command checks each one.

`verdict` semantics:

| Verdict | Meaning |
|---------|---------|
| `pass` | Stage's job is done; nothing requires the main agent's attention beyond applying meta ops |
| `at_risk` | Some Should/Could/Won't gaps exist but no Must gap; main agent records the residual risks |
| `fail` | At least one Must gap with `auto_fixable: true`; main agent loops back to `generate` |
| `escalated` | At least one Must gap with `auto_fixable: false`; main agent escalates to the user |
| `n/a` | Initial stub state; never legal in a finalised report |

`summary` must be a single sentence under ~120 chars. It is the only piece of the report that goes into the agent message.

## Body

The body (everything after the closing `---`) is plain markdown for the human reader. The main agent does not parse it. Subagents should write a short structured body — a coverage table for `report`, an RTM-gap summary for `review` — but every machine-readable claim must also appear in `items[]` or `proposed_meta_ops[]`.

## Per-stage shapes

### review stage — `items[]`

```yaml
items:
  - re_id: FR-014
    priority: should
    gap_type: partial_criteria      # missing_test | partial_criteria | weak_assertion | missing_nfr_scenario | traceability_break | flaky_pattern
    description: "decision-table covers 3 of 4 flag combinations"
    suggested_fix: "add a case for combination (admin=true, beta=true)"
    auto_fixable: true
    related_test_refs: [QA-SUITE-002:TS-002-C03]
```

### review stage — `proposed_meta_ops[]`

```yaml
proposed_meta_ops:
  - op: rtm-upsert
    re_id: FR-014
    re_priority: should
    re_title: "User can toggle beta features"
    arch_refs: [ARCH-COMP-002]
    impl_refs: [IMPL-MAP-002]
    test_refs: [QA-SUITE-002:TS-002-C01, QA-SUITE-002:TS-002-C02, QA-SUITE-002:TS-002-C03]
    status: partial
    gap: "decision-table covers 3 of 4 flag combinations"
```

The main agent walks `proposed_meta_ops` and translates each row into the matching `artifact.py` invocation.

### report stage — `items[]`

For the report stage `items[]` is optional and informational — typically one row per failed test:

```yaml
items:
  - kind: failed_test
    test_node: tests/auth/test_service.py::test_logout_clears_session
    failure: "AssertionError: session token still present"
```

### report stage — `proposed_meta_ops[]`

```yaml
proposed_meta_ops:
  - op: write-quality-report-actuals
    artifact_id: QA-REPORT-001
    quality_gate:
      actuals:
        code_coverage: 0.84
        requirements_coverage_must: 1.00
        failed_tests: 0
        nfr_results:
          - metric_id: RE-QA-001
            target: "p95 < 200 ms"
            actual: "148 ms"
            pass: true
    quality_report:
      code_coverage:
        by_module:
          - module: src/auth/
            lines: 0.92
            branches: 0.87
        total: { lines: 0.84, branches: 0.78 }
      residual_risks:
        - re_id: FR-014
          priority: should
          status: partial
          reason: "IdP stub not in CI; deferred"
  - op: gate-evaluate
    artifact_id: QA-REPORT-001
```

The main agent applies `write-quality-report-actuals` by translating it into `artifact.py set-block` calls for `quality_report` and `quality_gate.actuals`. Keep the payload minimal: only the keys named in the op.

## Validation

After the subagent returns, the main agent runs:

```
python ${SKILL_DIR}/scripts/artifact.py report validate <report_id>
```

If validation fails, the main agent does **not** apply any meta ops and instead spawns the subagent again with the validation errors as input. Do not try to "fix" the report by hand — invalid reports are a sign that the subagent did not have enough context.
