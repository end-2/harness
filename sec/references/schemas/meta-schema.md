# Metadata Schema (common fields)

Every Sec section metadata file (`SEC-*.meta.yaml`) carries the same top-level fields, regardless of which section it represents. This document is the authoritative reference for those common fields. Section-specific fields live in [section-schemas.md](section-schemas.md).

All metadata is managed by `scripts/artifact.py`. **Never edit `*.meta.yaml` by hand.**

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `artifact_id` | string | yes | Stable identifier. Pattern: `SEC-<SECTION>-<NNN>` where SECTION is one of `TM`, `VA`, `SR`, `CR`. Assigned by `artifact.py init`. |
| `section` | enum | yes | One of `threat-model`, `vulnerability-report`, `security-advisory`, `compliance-report`. |
| `phase` | enum | yes | Lifecycle phase. One of `draft`, `in_review`, `revising`, `approved`, `superseded`. |
| `progress` | object | yes | `{section_completed: int, section_total: int, percent: int}`. Managed by `set-progress`. |
| `approval` | object | yes | Approval record (see below). |
| `upstream_refs` | list[string] | yes | IDs that this artifact depends on. May be `ARCH-*`, `IMPL-*`, or `RE-*`. Managed by `link`. |
| `downstream_refs` | list[string] | yes | IDs that depend on this artifact. May be `DEVOPS-*`, `QA-*`, or `IMPL-*`. Managed by `link`. |
| `cross_refs` | object | yes | Cross-references between Sec sections (see below). |
| `document_path` | string | yes | Relative path to the paired markdown file (e.g. `SEC-TM-001.md`). |
| `created_at` | string | yes | ISO 8601 UTC timestamp of creation. Set by `init`. |
| `updated_at` | string | yes | ISO 8601 UTC timestamp of last change. Auto-refreshed on every write. |

## Artifact ID patterns

| Section | ID pattern | Example |
|---------|-----------|---------|
| Threat Model | `SEC-TM-NNN` | `SEC-TM-001` |
| Vulnerability Report | `SEC-VA-NNN` | `SEC-VA-001` |
| Security Advisory | `SEC-SR-NNN` | `SEC-SR-001` |
| Compliance Report | `SEC-CR-NNN` | `SEC-CR-001` |

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
  state: pending
  approver: null
  approved_at: null
  conditions: null
  rationale: null
  history:
    - state: rejected
      approver: alice
      rationale: "CVSS 9.2 threat not mitigated — requires user decision"
      at: 2026-04-11T10:00:00Z
      session_id: sec-session-001
    - state: conditionally_approved
      approver: alice
      rationale: "risk accepted for MVP, must remediate before GA"
      at: 2026-04-11T11:30:00Z
      session_id: sec-session-001
```

| Field | Type | Description |
|-------|------|-------------|
| `state` | enum | One of `pending`, `approved`, `rejected`, `changes_requested`, `conditionally_approved`. |
| `approver` | string | Username or role when state is not `pending`. |
| `approved_at` | string | ISO 8601 UTC, set when state transitions to `approved` or `conditionally_approved`. |
| `conditions` | string | When `state == conditionally_approved`, the conditions that must be met. |
| `rationale` | string | Free-text rationale from the approver, especially important for risk acceptance. |
| `history` | list | Append-only audit trail of all state transitions. |

**History entry fields**:

| Field | Type | Description |
|-------|------|-------------|
| `state` | enum | The state transitioned to. |
| `approver` | string | Who made the decision. |
| `rationale` | string | Why the decision was made. |
| `at` | string | ISO 8601 UTC timestamp. |
| `session_id` | string | Links the decision to a specific analysis session for traceability. |

**Audit trail significance**: The `approval.history` array is the primary audit artifact for security governance. Every escalation, risk acceptance, and compliance decision is recorded here with the decision-maker's identity and rationale. This trail is:

- **Immutable**: entries are append-only; the script refuses deletions.
- **Traceable**: `session_id` links each decision to the analysis session that produced the finding.
- **Accountable**: `approver` records who accepted the risk, not just that it was accepted.
- **Justified**: `rationale` captures the business reason, which is required for compliance audits.

For compliance-sensitive projects (PCI, HIPAA, GDPR), the approval history may be subject to external audit. Ensure rationale fields are substantive, not pro-forma.

**Legal approval transitions** (enforced by the script):

```
pending                  → approved | rejected | conditionally_approved
pending                  → changes_requested
rejected                 → pending
changes_requested        → pending | approved | rejected
conditionally_approved   → approved | pending
approved                 → (terminal)
```

**Phase gate**: `state` cannot transition to `approved` unless `phase == in_review`. The script refuses jumps like `draft → approved`.

## `cross_refs` object

```yaml
cross_refs:
  threat_refs: [SEC-TM-001, SEC-TM-003]
  vuln_refs: [SEC-VA-002]
```

Cross-references link related Sec sections to each other:

| Field | Description |
|-------|-------------|
| `threat_refs` | Threat model entries related to this artifact. A vulnerability report should reference the threats it substantiates. |
| `vuln_refs` | Vulnerability report entries related to this artifact. A security advisory should reference the vulnerabilities it addresses. |

These are intra-skill references (within Sec), distinct from `upstream_refs` (to Arch/Impl/RE) and `downstream_refs` (to devops/qa/impl).

## Phase transitions

```
draft      → in_review | superseded
in_review  → revising  | approved | superseded
revising   → in_review | superseded
approved   → superseded
superseded → (terminal)
```

## Traceability rules

- `upstream_refs` and `downstream_refs` are always populated through `artifact.py link`. The script maintains **bidirectional integrity**: linking A to B automatically adds the reciprocal B to A when both live under the same artifacts directory.
- Cross-skill refs (e.g. linking `SEC-TM-001` to `ARCH-COMP-001` or to `RE-NFR-002`) are **allowed** and expected. The reciprocal on the other side is best-effort — it only updates if the other artifact file is locally present.
- `cross_refs` within Sec (threat-to-vulnerability, vulnerability-to-advisory) are managed separately and do not require bidirectional enforcement — they are informational links for navigability.
- `validate` checks that all locally-resolvable refs are reciprocal, and flags any orphan ref as a warning.

## Validation

Run `python ${SKILL_DIR}/scripts/artifact.py validate` or `python ${SKILL_DIR}/scripts/validate.py [<id>]` to check:

1. Every required field is present.
2. Enums (`phase`, `section`, `approval.state`) hold legal values.
3. `document_path` resolves to an existing file.
4. Traceability is reciprocal for locally-resolvable refs.
5. `progress` fields are coherent.
6. `cross_refs` entries resolve to existing Sec artifacts.
7. `approval.history` entries have all required fields (`state`, `approver`, `rationale`, `at`, `session_id`).

A non-zero exit means at least one check failed; the output lists each violation with its artifact id.
