# Metadata Schema — Common Fields

Every Ex artifact metadata file (`*.meta.yaml`) contains these common fields. Section-specific fields are documented in [section-schemas.md](section-schemas.md).

## Common fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `artifact_id` | string | Yes | Unique identifier. Format: `EX-{PREFIX}-{NNN}` where PREFIX is `STR` (structure-map), `TS` (tech-stack), `CMP` (components), or `ARC` (architecture). Auto-assigned by `artifact.py init`. |
| `section` | string | Yes | Section name. One of: `structure-map`, `tech-stack`, `components`, `architecture`. |
| `phase` | string | Yes | Current lifecycle phase. See phase transitions below. |
| `progress` | object | Yes | Progress tracking. Fields: `section_completed` (int), `section_total` (int), `percent` (int 0-100). |
| `approval` | object | Yes | Approval tracking. Fields: `state`, `approver`, `approved_at`, `notes`, `history[]`. |
| `upstream_refs` | list[string] | Yes | Artifact IDs this artifact depends on. For Ex, typically empty (codebase is the input). |
| `downstream_refs` | list[string] | Yes | Skill identifiers or artifact IDs that consume this artifact. Ex injects into: `re`, `arch`, `impl`, `qa`, `sec`. |
| `document_path` | string | Yes | Relative path to the paired `.md` file. |
| `created_at` | string (ISO 8601) | Yes | Creation timestamp. Auto-set by `artifact.py init`. |
| `updated_at` | string (ISO 8601) | Yes | Last modification timestamp. Auto-refreshed by every `artifact.py` write operation. |

## Phase transitions

```
draft -> in_review -> revising -> in_review -> approved -> superseded
```

Legal transitions:

| From | To |
|------|----|
| `draft` | `in_review`, `superseded` |
| `in_review` | `revising`, `approved`, `superseded` |
| `revising` | `in_review`, `superseded` |
| `approved` | `superseded` |
| `superseded` | (terminal) |

## Approval states

| State | Meaning |
|-------|---------|
| `pending` | Not yet reviewed |
| `approved` | Accepted — artifact phase also transitions to `approved` |
| `rejected` | Not accepted — requires rework |
| `changes_requested` | Partially acceptable — specific changes needed |

Legal transitions:

| From | To |
|------|----|
| `pending` | `approved`, `rejected`, `changes_requested` |
| `changes_requested` | `pending`, `approved`, `rejected` |
| `rejected` | `pending` |
| `approved` | (terminal) |

## Approval history

The `approval.history` array records every state transition:

```yaml
history:
  - state: changes_requested
    approver: user
    at: "2026-04-12T10:00:00Z"
    notes: "Component boundaries need refinement"
  - state: approved
    approver: user
    at: "2026-04-12T11:30:00Z"
    notes: "Looks good after revision"
```

## Traceability integrity

`artifact.py validate` checks:
- If artifact A lists B in `downstream_refs`, then B must list A in `upstream_refs` (when B exists in the same artifacts directory).
- For cross-skill references (e.g., `downstream_refs: [re, arch]`), the reference is a skill name, not an artifact ID — no reciprocal check is performed.
- Section payload shape and required fields for the active section.
- Cross-section component references (for example architecture layer/component refs that point to missing component IDs).
