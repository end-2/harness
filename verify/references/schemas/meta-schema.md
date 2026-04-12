# Metadata Schema (common fields)

Every Verify section metadata file (`VERIFY-*.meta.yaml`) carries the same top-level fields, regardless of which section it represents. This document is the authoritative reference for those common fields. Section-specific fields live in [section-schemas.md](section-schemas.md).

All metadata is managed by `scripts/artifact.py`. **Never edit `*.meta.yaml` by hand.**

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `artifact_id` | string | yes | Stable identifier. Pattern: `VERIFY-<SECTION>-<NNN>` where SECTION is one of `ENV`, `SC`, `RPT`. Assigned by `artifact.py init`. |
| `section` | enum | yes | One of `environment`, `scenario`, `report`. |
| `phase` | enum | yes | Lifecycle phase. One of `draft`, `in_review`, `revising`, `approved`, `superseded`. |
| `progress` | object | yes | `{section_completed: int, section_total: int, percent: int}`. Managed by `set-progress`. |
| `approval` | object | yes | Approval record (see below). |
| `upstream_refs` | list[string] | yes | IDs that this artifact depends on. May be `IMPL-*`, `DEVOPS-*`, `ARCH-*`, `RE-*`, or another `VERIFY-*`. Managed by `link`. |
| `downstream_refs` | list[string] | yes | IDs that depend on this artifact. May be `SEC-*`, `ORCH-*`. Managed by `link`. |
| `document_path` | string | yes | Relative path to the paired markdown file (e.g. `VERIFY-ENV-001.md`). |
| `created_at` | string | yes | ISO 8601 UTC timestamp of creation. Set by `init`. |
| `updated_at` | string | yes | ISO 8601 UTC timestamp of last change. Auto-refreshed on every write. |

## `progress` object

```yaml
progress:
  section_completed: 4
  section_total: 6
  percent: 67
```

- `section_total` may be `0` for a freshly initialized artifact; once work starts it should be `> 0`.
- `0 <= section_completed <= section_total`.
- `percent` is derived from the two counts; `0/0` must remain `0%`, otherwise the script computes and enforces the exact value.

## `approval` object

```yaml
approval:
  state: pending
  approver: null
  approved_at: null
  notes: null
  history:
    - state: changes_requested
      approver: alice
      at: 2026-04-12T10:00:00Z
      notes: "SC-101 needs a recovery step"
    - state: pending
      approver: alice
      at: 2026-04-12T11:00:00Z
      notes: null
```

**Legal approval transitions** (enforced by the script):

```
pending            → approved | rejected | changes_requested
changes_requested  → pending | approved | rejected
rejected           → pending
approved           → (terminal, reset requires phase → superseded)
```

**Phase gate**: `state` cannot transition to `approved` unless `phase == in_review`.

## Phase transitions

```
draft      → in_review | superseded
in_review  → revising  | approved   | superseded
revising   → in_review | superseded
approved   → superseded
superseded → (terminal)
```

## Traceability rules

- `upstream_refs` and `downstream_refs` are always populated through `artifact.py link`. The script maintains **bidirectional integrity**.
- Cross-skill refs (e.g. linking `VERIFY-ENV-001` to `IMPL-MAP-001` or `DEVOPS-OBS-001`) are **allowed** and expected.
- `validate` checks that all locally-resolvable refs are reciprocal.
