# Escalation Protocol

When and how the Sec skill pauses automated analysis to require a human decision. Security analysis can surface findings that must not be silently accepted or deferred — this protocol defines those boundaries.

## Escalation conditions

Three conditions trigger mandatory escalation. If any condition is met, Sec **must** pause and present the finding to the user before continuing.

### 1. Critical vulnerability (CVSS >= 9.0)

A vulnerability with a CVSS base score of 9.0 or higher indicates a critical risk that could lead to full system compromise, mass data breach, or complete service disruption.

**Trigger**: any `vulnerability_report` entry where `cvss_score >= 9.0`.

**Examples**:
- Unauthenticated remote code execution
- SQL injection returning all database contents
- Authentication bypass on external-facing endpoints
- Hardcoded credentials with administrative access

### 2. Hard regulatory constraint non-compliance

A compliance finding where the system fails a requirement tied to a `hard` constraint from Arch's technology stack or RE's constraints. These are non-negotiable regulatory obligations.

**Trigger**: any `compliance_report` finding where `status == "non_compliant"` and the requirement traces to a `constraint_ref` with `type == "hard"`.

**Examples**:
- PCI DSS requirement violated for a payment-processing system
- HIPAA safeguard missing for a health-data system
- GDPR data-protection requirement unmet for EU-resident PII

### 3. Unmitigated critical threat

A threat model entry with `risk_level == "critical"` that has no planned or implemented mitigation.

**Trigger**: any `threat_model` entry where `risk_level == "critical"` and `mitigation_status == "not_applicable"` or mitigation is empty/missing.

**Examples**:
- External-facing service with no authentication and no plan to add it
- Sensitive data transmitted in plaintext with no encryption plan
- Admin interface exposed to the internet with no access control

## Escalation procedure

When a trigger condition is met, follow this sequence:

### Step 1 — Pause analysis

Stop processing the current stage. Do not continue to the next finding or the next stage.

### Step 2 — Present the finding

Present the finding to the user with the following structure:

```
SECURITY ESCALATION — [condition type]

Severity:    [critical / regulatory / unmitigated]
Finding:     [one-line summary]
Components:  [affected ARCH-COMP-* ids]
Detail:      [2-3 sentence description of the risk]

Recommendation:
  [primary recommended action]

Alternatives:
  1. [alternative action with trade-off]
  2. [alternative action with trade-off]

Options:
  (a) Accept recommendation — [what happens]
  (b) Choose alternative — [specify which]
  (c) Accept risk — requires rationale (will be recorded in audit trail)
  (d) Defer — pause Sec analysis and escalate to Arch / Impl for structural fix
```

### Step 3 — Wait for user response

Do not proceed until the user responds. Do not auto-accept, auto-defer, or apply a default. The user must make an explicit choice.

### Step 4 — Record the decision

Record the user's decision using the artifact management script:

**If the user accepts the recommendation or an alternative**:

```bash
python ${SKILL_DIR}/scripts/artifact.py approve <artifact-id> \
  --approver "<user>" \
  --rationale "Accepted recommendation: <summary>"
```

**If the user accepts the risk**:

```bash
python ${SKILL_DIR}/scripts/artifact.py accept-risk \
  --artifact <artifact-id> \
  --approver "<user>" \
  --rationale "<user-provided rationale>"
```

The user **must** provide a rationale for risk acceptance. "No reason" or empty rationale is rejected by the script. The rationale should explain the business justification for accepting the risk.

**If the user defers to Arch / Impl**:

```bash
python ${SKILL_DIR}/scripts/artifact.py defer <artifact-id> \
  --approver "<user>" \
  --rationale "Deferred to <Arch|Impl> for structural fix: <summary>"
```

### Step 5 — Resume analysis

After the user responds and the decision is recorded, continue analysis from where it was paused. The recorded decision becomes part of the artifact's approval history.

## Compliance escalation — special rules

Compliance escalations (condition 2) have stricter rules than vulnerability or threat escalations:

- **Cannot be auto-accepted**: even if the user says "accept risk", the script requires explicit `--compliance-override` flag acknowledgment.
- **Cannot be deferred indefinitely**: a compliance gap must have a remediation target date. The user must provide a timeline.
- **Requires named approver**: the `approver` field must be a real person, not a role or "system". Compliance auditors need a named individual.
- **May require external approval**: for some standards (PCI DSS Level 1, SOC 2 Type II), the script warns that external auditor notification may be needed.

```bash
python ${SKILL_DIR}/scripts/artifact.py accept-risk \
  --artifact SEC-CR-001 \
  --approver "alice.kim" \
  --rationale "Gap accepted for MVP. Remediation scheduled for Q3." \
  --compliance-override \
  --remediation-target "2026-09-01"
```

## Audit trail

Every escalation and its resolution is recorded in the artifact's `approval.history` array:

```yaml
approval:
  history:
    - state: rejected
      approver: system
      rationale: "ESCALATION: CVSS 9.2 — unauthenticated RCE in user-service"
      at: 2026-04-12T14:30:00Z
      session_id: sec-session-042
    - state: conditionally_approved
      approver: alice.kim
      rationale: "Risk accepted for staging environment only. Production blocked until fix deployed."
      at: 2026-04-12T14:45:00Z
      session_id: sec-session-042
```

Key properties of the audit trail:

- **Append-only**: previous entries are never modified or deleted.
- **Session-linked**: `session_id` ties each entry to the analysis session, so auditors can reconstruct the sequence of events.
- **Timestamped**: ISO 8601 UTC timestamps provide ordering and time-to-resolution metrics.
- **Rationale-required**: every entry must have a non-empty `rationale` explaining the decision.

For compliance-sensitive projects, this audit trail is the primary evidence that security findings were reviewed and dispositioned by an authorized individual. Treat it accordingly.
