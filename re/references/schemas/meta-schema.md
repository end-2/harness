# Metadata Schema — Common Fields

Every RE artifact (`requirements`, `constraints`, `quality-attributes`) has a `*.meta.yaml` file. The **common fields** documented here are shared across all three sections. Section-specific fields (the tables of FRs, constraints, quality attributes) are documented in [section-schemas.md](section-schemas.md).

Never edit `*.meta.yaml` files by hand. All common-field mutations happen through `scripts/artifact.py`.

## Common fields

| Field | Type | Description |
|-------|------|-------------|
| `artifact_id` | string | Unique identifier. Format `RE-REQ-NNN` / `RE-CON-NNN` / `RE-QA-NNN`. Assigned by `artifact.py init`. |
| `section` | string | One of `requirements`, `constraints`, `quality-attributes`. |
| `phase` | string | Current workflow phase (see below). |
| `progress.section_completed` | int | Number of section rows confirmed by the user. |
| `progress.section_total` | int | Total number of rows expected. |
| `progress.percent` | int | Derived: `round(100 * completed / total)`. |
| `approval.state` | string | One of `pending`, `approved`, `rejected`, `changes_requested`. |
| `approval.approver` | string \| null | Who approved / rejected. |
| `approval.approved_at` | ISO 8601 \| null | Timestamp of the approval transition. |
| `approval.notes` | string \| null | Free-form notes recorded at approval time. |
| `approval.history` | list | Append-only audit trail of state transitions with timestamps. |
| `upstream_refs` | list[string] | References to upstream sources (user prompts, prior artifacts). |
| `downstream_refs` | list[string] | References to downstream consumers (other artifact IDs). |
| `document_path` | string | Relative path to the paired markdown document. |
| `created_at` | ISO 8601 | Creation timestamp (written by `init`). |
| `updated_at` | ISO 8601 | Last modification timestamp (auto-refreshed by every write). |

## Phase values

| Phase | Meaning | Legal next phases |
|-------|---------|-------------------|
| `draft` | Freshly created by `init`. Not yet ready for review. | `in_review`, `superseded` |
| `in_review` | Complete enough to be reviewed by the user. | `revising`, `approved`, `superseded` |
| `revising` | Review found issues; the author is fixing them. | `in_review`, `superseded` |
| `approved` | Reviewed and accepted. Consumable by downstream skills. | `superseded` |
| `superseded` | Replaced by a newer artifact. Kept for history only. | — |

Transitions are enforced by `artifact.py set-phase`. Jumping from `draft` directly to `approved` is rejected.

## Approval state values

| State | Meaning | Legal next states |
|-------|---------|-------------------|
| `pending` | No decision yet. Default on `init`. | `approved`, `rejected`, `changes_requested` |
| `changes_requested` | User asked for changes. Artifact usually moves to phase `revising`. | `pending`, `approved`, `rejected` |
| `rejected` | Explicitly rejected. Rare — typically means the artifact is being discarded. | `pending` |
| `approved` | Accepted. Phase automatically moves to `approved`. | — |

Approval transitions are enforced by `artifact.py approve`. Approval to `approved` additionally requires the artifact to be in phase `in_review` first.

## Traceability semantics

`upstream_refs` and `downstream_refs` are symmetric: if A lists B as a downstream ref and B is a known artifact, B must list A as an upstream ref. `artifact.py link` automatically updates both sides when both referenced artifacts exist. `artifact.py validate` enforces the reciprocal integrity.

`upstream_refs` for RE artifacts typically include:

- `user-prompt:<hash-or-snippet>` — the user's original utterance
- `RE-REQ-001` / etc. — links between RE artifacts (e.g. a constraint that traces to a requirement)

`downstream_refs` for RE artifacts are typically populated by downstream skills when they consume the artifact (e.g. an `arch` artifact referencing `RE-REQ-001`). RE does not need to populate them itself unless cross-linking between its own three sections.

## Example

```yaml
artifact_id: RE-REQ-001
section: requirements
phase: in_review
progress:
  section_completed: 5
  section_total: 7
  percent: 71
approval:
  state: pending
  approver: null
  approved_at: null
  notes: null
  history:
    - state: pending
      approver: null
      at: 2026-04-11T12:00:00Z
      notes: null
upstream_refs:
  - user-prompt:initial-rfp
downstream_refs: []
document_path: RE-REQ-001.md
created_at: 2026-04-11T12:00:00Z
updated_at: 2026-04-11T12:34:56Z

functional_requirements:
  - id: FR-001
    title: User login with email+password
    # ...
non_functional_requirements: []
```
