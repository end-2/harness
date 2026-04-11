# Metadata Schema — Common Fields

Every Arch artifact metadata file (`*.meta.yaml`) shares these fields. `scripts/artifact.py` validates them on every write and on `validate`.

| Field | Type | Managed by | Description |
|-------|------|-----------|-------------|
| `artifact_id` | string | `init` (immutable) | Stable identifier. Format: `ARCH-<SECTION>-<NNN>`. Section prefix is one of `DEC` / `COMP` / `TECH` / `DIAG`. |
| `section` | enum | `init` (immutable) | One of `decisions`, `components`, `tech-stack`, `diagrams`. |
| `phase` | enum | `set-phase` | One of `draft`, `in_review`, `revising`, `approved`, `superseded`. See transitions below. |
| `progress.section_completed` | int | `set-progress` | Count of "done" items (ADRs / components / tech rows / diagrams). |
| `progress.section_total` | int | `set-progress` | Total items to complete in this section. |
| `progress.percent` | int | `set-progress` | Derived `round(100 * completed / total)`. |
| `approval.state` | enum | `approve` | One of `pending`, `approved`, `rejected`, `changes_requested`. |
| `approval.approver` | string | `approve` | User or role that acted on the last transition. |
| `approval.approved_at` | ISO 8601 | `approve` | Timestamp of the transition to `approved`. |
| `approval.notes` | string \| null | `approve` | Free-form note attached to the last transition. |
| `approval.history` | list | `approve` | Append-only audit trail of every transition. |
| `upstream_refs` | list[string] | `link` | IDs of artifacts this one depends on. Cross-skill ids allowed (`RE-QA-001`, `RE-CON-002`, …). |
| `downstream_refs` | list[string] | `link` | IDs of artifacts that depend on this one. Kept bidirectionally consistent with `upstream_refs` across the project. |
| `document_path` | string | `init` | Filename of the paired markdown document, relative to the artifact directory. |
| `created_at` | ISO 8601 | `init` | Creation timestamp. |
| `updated_at` | ISO 8601 | auto | Stamped on every write by `save_meta`. |

## Phase transitions

```
draft ──┬─→ in_review ──┬─→ revising ──→ in_review ──→ approved
        │               │
        └─→ superseded  └─→ superseded
```

Direct `draft → approved` is **forbidden**. Every approval must pass through `in_review`.

## Approval transitions

```
pending ──┬─→ approved
          ├─→ rejected
          └─→ changes_requested

changes_requested ──┬─→ pending
                    ├─→ approved
                    └─→ rejected

rejected ──→ pending

approved (terminal)
```

`approved` also sets `phase` to `approved` and stamps `approved_at`.

## Never edit these fields directly

All of the above are managed exclusively through `scripts/artifact.py`. Direct edits to `*.meta.yaml` risk breaking traceability and audit history. The only part of the metadata file that may be edited by hand (and only with care) is the section-specific structured block (`architecture_decisions`, `components`, `technology_stack`, `diagrams`) — but the recommended flow is to treat markdown as the source of truth during iteration and populate the structured block at `review` time.
