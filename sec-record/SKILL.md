---
name: sec-record
description: Execute the write-side workflow for the Sec pipeline by creating Sec artifact pairs, linking traceability, requesting approval, approving or rejecting artifacts, accepting risk with an audit trail, and validating Sec metadata through the audited scripts in `../sec/scripts/`. Use when the user explicitly wants to record Sec analysis results, change `SEC-*` artifact state, capture a human approval or risk-acceptance decision, or validate existing Sec artifacts. Do not use this skill for security analysis itself; use `sec` for read-only analysis.
---

# Sec Record

Use this skill only for explicit write operations on Sec artifacts. `sec` performs the analysis; `sec-record` creates or updates the `SEC-*.meta.yaml` audit trail that makes the results durable.

## Current State

!`python3 ${SKILL_DIR}/../sec/scripts/report.py summary`

Read the summary before changing anything so you know whether you are creating a new artifact, resuming review, or updating an already-approved record.

## Safety Rules

- Use only the audited scripts in `${SKILL_DIR}/../sec/scripts/`.
- Never edit `*.meta.yaml` by hand.
- Require a human rationale for approvals, rejections, and risk acceptance.
- Treat compliance-report risk acceptance as special: require `--compliance-override`.
- Validate after meaningful state changes.

## Quick Start

### Create a new artifact pair

```bash
python3 ${SKILL_DIR}/../sec/scripts/artifact.py init --section threat-model
```

Supported sections:

- `threat-model`
- `vulnerability-report`
- `security-advisory`
- `compliance-report`

### Link traceability

```bash
python3 ${SKILL_DIR}/../sec/scripts/artifact.py link SEC-TM-001 --upstream ARCH-COMP-001
python3 ${SKILL_DIR}/../sec/scripts/artifact.py link SEC-TM-001 --downstream SEC-VA-001
```

### Move through review

```bash
python3 ${SKILL_DIR}/../sec/scripts/approval.py request SEC-TM-001
python3 ${SKILL_DIR}/../sec/scripts/approval.py approve SEC-TM-001 \
  --approver "alice.kim" \
  --rationale "Threat model reviewed and accepted for downstream use."
```

### Reject or accept risk

```bash
python3 ${SKILL_DIR}/../sec/scripts/approval.py reject SEC-VA-001 \
  --approver "alice.kim" \
  --rationale "Need stronger remediation guidance before approval."

python3 ${SKILL_DIR}/../sec/scripts/approval.py accept-risk SEC-SR-001 \
  --approver "alice.kim" \
  --rationale "Deferred to the next release with compensating controls in place."
```

For a compliance report:

```bash
python3 ${SKILL_DIR}/../sec/scripts/approval.py accept-risk SEC-CR-001 \
  --approver "alice.kim" \
  --rationale "Accepted temporarily for MVP with a dated remediation plan." \
  --compliance-override
```

### Validate and inspect

```bash
python3 ${SKILL_DIR}/../sec/scripts/validate.py
python3 ${SKILL_DIR}/../sec/scripts/validate.py SEC-TM-001
python3 ${SKILL_DIR}/../sec/scripts/artifact.py show SEC-TM-001
```

## Workflow

### 1. Create or locate the artifact

- Use `artifact.py init --section <name>` for a new artifact.
- Use `artifact.py show <id>` or the injected summary when continuing existing work.

### 2. Record traceability before approval

- Add every required `ARCH-*`, `IMPL-*`, `RE-*`, and `SEC-*` relationship with `artifact.py link`.
- Keep `upstream_refs` complete before moving into review.

### 3. Move into review

- Use `approval.py request <id>` to set `approval.state=pending` and `phase=in_review`.
- Use `artifact.py set-progress <id> --completed N --total M` when the stage defines explicit checklist counts.

### 4. Capture the human decision

- Use `approval.py approve` for acceptance.
- Use `approval.py reject` when more work is needed.
- Use `approval.py accept-risk` only when the user explicitly accepts the remaining risk and provides the rationale.

### 5. Validate

- Run `validate.py` after creating artifacts, after adding links, and after any approval-state change.
- Treat validation failures as blockers; fix the metadata instead of overriding the script.

## Command Reference

| Need | Command |
|------|---------|
| Create artifact pair | `artifact.py init --section <name>` |
| Set phase directly | `artifact.py set-phase <id> <phase>` |
| Update checklist progress | `artifact.py set-progress <id> --completed N --total M` |
| Link upstream/downstream refs | `artifact.py link <id> --upstream <ref>` / `--downstream <ref>` |
| Request review | `approval.py request <id>` |
| Approve | `approval.py approve <id> --approver <name> --rationale "..."` |
| Reject | `approval.py reject <id> --approver <name> --rationale "..."` |
| Accept risk | `approval.py accept-risk <id> --approver <name> --rationale "..." [--compliance-override]` |
| Validate | `validate.py [<id>]` |
| Inspect metadata | `artifact.py show <id>` |

## A Few Non-Negotiables

- Keep `sec-record` write-only. If the task is analysis, hand it back to `sec`.
- Preserve the human audit trail. Do not synthesize approval rationale.
- Use `--compliance-override` only when the user explicitly accepts a compliance gap.
- Prefer the narrowest command that expresses the decision cleanly. Use `approval.py` for approvals and risk decisions instead of generic metadata edits.
