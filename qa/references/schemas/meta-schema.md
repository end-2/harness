# Metadata Schema (common fields)

Every QA section metadata file (`QA-*.meta.yaml`) carries the same top-level fields, regardless of which section it represents. This document is the authoritative reference for those common fields. Section-specific fields live in [section-schemas.md](section-schemas.md).

All metadata is managed by `scripts/artifact.py`. **Never edit `*.meta.yaml` by hand.** The single exception is the Stage 4 `write-quality-report-actuals` meta op, where the main agent edits the Quality Report's `quality_gate.actuals` and `quality_report` blocks directly because there is no script subcommand for setting individual keys.

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `artifact_id` | string | yes | Stable identifier. Pattern: `QA-<SECTION>-<NNN>` where SECTION is one of `STRATEGY`, `SUITE`, `RTM`, `REPORT`. Assigned by `artifact.py init`. |
| `section` | enum | yes | One of `test-strategy`, `test-suite`, `rtm`, `quality-report`. |
| `phase` | enum | yes | Lifecycle phase. One of `draft`, `in_review`, `revising`, `approved`, `superseded`. |
| `progress` | object | yes | `{section_completed: int, section_total: int, percent: int}`. Managed by `set-progress`. |
| `approval` | object | yes | Approval record (see below). |
| `upstream_refs` | list[string] | yes | IDs that this artifact depends on. May be `RE-*`, `ARCH-*`, `IMPL-*`, or another `QA-*`. Managed by `link`. |
| `downstream_refs` | list[string] | yes | IDs that depend on this artifact. May be `DEPLOY-*`, `OP-*`, `MGMT-*`, `SEC-*`. Managed by `link`. |
| `document_path` | string | yes | Relative path to the paired markdown file (e.g. `QA-STRATEGY-001.md`). |
| `created_at` | string | yes | ISO 8601 UTC timestamp of creation. Set by `init`. |
| `updated_at` | string | yes | ISO 8601 UTC timestamp of last change. Auto-refreshed on every write. |

## `progress` object

```yaml
progress:
  section_completed: 3
  section_total: 5
  percent: 60
```

- `section_total > 0` required when set.
- `0 <= section_completed <= section_total`.
- `percent` is derived from the two counts; the script computes it and rejects incoherent values.

## `approval` object

```yaml
approval:
  state: pending          # pending | approved | rejected | changes_requested | escalated
  approver: null          # username, role, or 'auto:gate-evaluator'
  approved_at: null       # ISO 8601 UTC, set when state transitions to approved
  notes: null             # free-text comment from the approver
  history:                # audit trail; append-only
    - state: changes_requested
      approver: alice
      at: 2026-04-11T10:00:00Z
      notes: "needs an NFR scenario for RE-QA-002"
    - state: pending
      approver: alice
      at: 2026-04-11T11:00:00Z
      notes: null
```

**Legal approval transitions** (also enforced by the script):

```
pending            → approved | rejected | changes_requested | escalated
changes_requested  → pending | approved | rejected | escalated
rejected           → pending
escalated          → pending | approved | rejected | changes_requested
approved           → (terminal, reset requires phase → superseded)
```

QA adds the `escalated` state, which is reserved for Quality Reports whose `gate-evaluate` flagged at least one Must requirement still uncovered.

**Phase gate**: `state` cannot transition to `approved` unless `phase == in_review`. The script refuses jumps like `draft → approved`. The one exception is `gate-evaluate`, which auto-promotes a Quality Report from `draft` / `revising` to `in_review` when the verdict is `pass`, since the gate evaluation is itself the review.

**Quality Report exclusivity**: a Quality Report's `approval` may **only** be transitioned by `gate-evaluate`. Calling `artifact.py approve` directly on a `QA-REPORT-*` is refused, so the verdict always reflects measured results.

## Phase transitions

```
draft      → in_review | superseded
in_review  → revising  | approved   | superseded
revising   → in_review | superseded
approved   → superseded
superseded → (terminal)
```

## Traceability rules

- `upstream_refs` and `downstream_refs` are always populated through `artifact.py link`. The script maintains **bidirectional integrity**: linking A → B automatically adds the reciprocal B → A when both live under the same artifacts directory.
- Cross-skill refs (e.g. linking `QA-SUITE-001` to `IMPL-MAP-001`, `ARCH-COMP-001`, or `RE-SPEC-001`) are **allowed** and expected. The reciprocal on the other side is best-effort — it only updates if the other artifact file is locally present.
- `validate` checks that all locally-resolvable refs are reciprocal, and flags any orphan ref as an error.

## RTM-specific rules

The `rtm` section adds one structured field, `rtm_rows[]`. It is also under script control:

- Rows may **only** be added or modified through `artifact.py rtm-upsert`. Direct edits via `Edit`/`Write` are forbidden.
- Each row's `coverage_status` must be one of `covered` / `partial` / `uncovered`. `validate` rejects unknown values.
- The `gap_description` field is optional but expected when `coverage_status` is `partial` or `uncovered`.
- `rtm-gap-report` is the only blessed source of the gap roll-up; the Quality Report quotes its output verbatim.

## Quality Report-specific rules

The `quality-report` section adds two structured fields, `quality_report` (presentation data) and `quality_gate` (criteria + actuals + verdict).

- `quality_gate.criteria` is set during the `strategy` stage as part of the Test Strategy hand-off (the values come from `QA-STRATEGY-*.test_strategy.quality_gate_criteria`).
- `quality_gate.actuals` is set during the `report` stage by the main agent applying the `write-quality-report-actuals` meta op.
- `quality_gate.verdict`, `quality_gate.reasons`, and `quality_gate.evaluated_at` are set **only** by `artifact.py gate-evaluate`. They must not be edited by hand.

## Validation

Run `python ${SKILL_DIR}/scripts/artifact.py validate` to check:

1. Every required field is present.
2. Enums (`phase`, `section`, `approval.state`, `coverage_status`) hold legal values.
3. `document_path` resolves to an existing file.
4. Traceability is reciprocal for locally-resolvable refs.
5. `progress` fields are coherent.
6. `rtm_rows[]` is well-formed when present.

A non-zero exit means at least one check failed; the output lists each violation with its artifact id.
