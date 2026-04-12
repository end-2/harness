# Metadata Schema (common fields)

Every DevOps section metadata file (`DEVOPS-*.meta.yaml`) carries the same top-level fields, regardless of which section it represents. This document is the authoritative reference for those common fields. Section-specific fields live in [section-schemas.md](section-schemas.md).

All metadata is managed by `scripts/artifact.py`. **Never edit `*.meta.yaml` by hand.**

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `artifact_id` | string | yes | Stable identifier. Pattern: `DEVOPS-<SECTION>-<NNN>` where SECTION is one of `PL`, `IAC`, `OBS`, `RB`. Assigned by `artifact.py init`. |
| `section` | enum | yes | One of `pipeline`, `iac`, `observability`, `runbook`. |
| `phase` | enum | yes | Lifecycle phase. One of `draft`, `in_review`, `revising`, `approved`, `superseded`. |
| `progress` | object | yes | `{section_completed: int, section_total: int, percent: int}`. Managed by `set-progress`. |
| `approval` | object | yes | Approval record (see below). |
| `upstream_refs` | list[string] | yes | IDs that this artifact depends on. May be `ARCH-*`, `IMPL-*`, `RE-*`, or another `DEVOPS-*`. Managed by `link`. |
| `downstream_refs` | list[string] | yes | IDs that depend on this artifact. May be `SEC-*`, `MGMT-*`, `OP-*`. Managed by `link`. |
| `document_path` | string | yes | Relative path to the paired markdown file (e.g. `DEVOPS-PL-001.md`). |
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
  state: pending          # pending | approved | rejected | changes_requested
  approver: null          # username or role when state != pending
  approved_at: null       # ISO 8601 UTC, set when state transitions to approved
  notes: null             # free-text comment from the approver
  history:                # audit trail; append-only
    - state: changes_requested
      approver: alice
      at: 2026-04-11T10:00:00Z
      notes: "needs a runbook for the alerting gap"
    - state: pending
      approver: alice
      at: 2026-04-11T11:00:00Z
      notes: null
```

**Legal approval transitions** (also enforced by the script):

```
pending            → approved | rejected | changes_requested
changes_requested  → pending | approved | rejected
rejected           → pending
approved           → (terminal, reset requires phase → superseded)
```

**Phase gate**: `state` cannot transition to `approved` unless `phase == in_review`. The script refuses jumps like `draft → approved`.

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
- Cross-skill refs (e.g. linking `DEVOPS-PL-001` to `IMPL-CODE-001` or to `ARCH-COMP-001`) are **allowed** and expected. The reciprocal on the other side is best-effort — it only updates if the other artifact file is locally present.
- `validate` checks that all locally-resolvable refs are reciprocal, and flags any orphan ref as a warning.

## Validation

Run `python ${SKILL_DIR}/scripts/artifact.py validate` to check:

1. Every required field is present.
2. Enums (`phase`, `section`, `approval.state`) hold legal values.
3. `document_path` resolves to an existing file.
4. Traceability is reciprocal for locally-resolvable refs.
5. `progress` fields are coherent.

A non-zero exit means at least one check failed; the output lists each violation with its artifact id.
