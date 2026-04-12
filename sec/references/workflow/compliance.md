# Workflow — Stage 4: Compliance Verification Stage — Detailed Rules

## Role

Map analysis results from Stages 1-3 to applicable security standards, produce per-requirement compliance checklists, generate the integrated Security Advisory, and present the final security report to the user. This is the final stage of the Sec pipeline and produces the primary user-facing deliverable.

## Inputs

- **`SEC-TM-*`** (from Stage 1) — Threat model with mitigations and risk levels.
- **`SEC-VA-*`** (from Stage 2) — Vulnerability report with CWE classifications and CVSS scores.
- **`SEC-SR-*`** (from Stage 3, partial) — Security review findings on mitigation implementation status.
- **`ARCH-COMP-*`** — Component structure for mapping compliance requirements to system elements.
- **`ARCH-TECH-*`** — Technology stack with `constraint_ref` to RE constraints.
- **`IMPL-MAP-*`** — Implementation map for locating code evidence.
- **`IMPL-CODE-*`** — Code structure for dependency and configuration evidence.
- **RE constraints** (via Arch `constraint_ref`) — `type: regulatory` constraints determine which standards apply.

## Standard determination

Determine which compliance standards apply by reading the RE constraint chain:

1. Read `ARCH-TECH-*.constraint_ref` entries.
2. For each `constraint_ref`, trace back to the RE constraint.
3. Filter for `type: regulatory` or `type: security` constraints.
4. Map each constraint to specific standards:

| RE constraint keyword | Standard |
|---|---|
| GDPR, personal data, EU data protection | GDPR code-level requirements |
| HIPAA, PHI, health data, medical records | HIPAA code-level requirements |
| PCI DSS, payment card, cardholder data | PCI DSS code-level requirements |
| SOC 2, service organization | SOC 2 trust service criteria |
| General security, no specific regulation | OWASP ASVS only |

If no regulatory constraints exist, apply OWASP ASVS L1 as the baseline. OWASP ASVS always applies regardless of other standards.

## OWASP ASVS verification

### Level determination

The ASVS verification level is determined by the system's risk profile:

| Level | Trigger | Description |
|---|---|---|
| **L1 — Automated basics** | Light mode, no regulatory constraints, low-risk system | Basic security verification. Automated checks only. Covers the most common vulnerabilities. |
| **L2 — Standard (recommended)** | Heavy mode, moderate-risk system, handles PII or financial data | Standard security verification. Covers most security requirements for typical business applications. |
| **L3 — Advanced** | Financial systems, medical systems, government systems, or explicit RE constraint requiring L3 | Comprehensive security verification. Maximum assurance level. Required for systems handling highly sensitive data. |

Default to L2 for heavy mode. Default to L1 for light mode. Override if a regulatory constraint explicitly specifies a level.

### ASVS requirement mapping

Map the outputs of Stages 1-3 to ASVS verification categories:

| ASVS chapter | Primary source | Verification method |
|---|---|---|
| V1: Architecture | Threat model (Stage 1) | Trust boundaries, component security properties |
| V2: Authentication | Review (Stage 3) | Auth flow completeness, credential storage |
| V3: Session management | Review (Stage 3) | Session handling, timeout, invalidation |
| V4: Access control | Review (Stage 3) + Audit (Stage 2) | RBAC/ABAC, IDOR checks |
| V5: Validation | Review (Stage 3) + Audit (Stage 2) | Input validation, output encoding |
| V6: Cryptography | Review (Stage 3) | Algorithm selection, key management |
| V7: Error handling | Review (Stage 3) | Information leakage, fail-secure |
| V8: Data protection | Audit (Stage 2) + Threat model (Stage 1) | Sensitive data handling, encryption |
| V9: Communication | Review (Stage 3) | TLS configuration, certificate validation |
| V10: Malicious code | Audit (Stage 2) | Backdoors, time bombs, logic bombs |
| V11: Business logic | Threat model (Stage 1) + Audit (Stage 2) | Business logic flaws, race conditions |
| V12: Files and resources | Audit (Stage 2) | File upload, path traversal |
| V13: API | Audit (Stage 2) + Review (Stage 3) | API security, GraphQL, WebSocket |
| V14: Configuration | Audit (Stage 2) | Security headers, error config |

For each ASVS requirement at the determined level, produce a checklist row.

## PCI DSS code-level requirements

Apply when payment card data is in scope. Focus on code-level requirements (not infrastructure or process):

### Requirement 3: Protect stored account data

- Card data (PAN) is encrypted at rest with strong cryptography (AES-256).
- Encryption keys are managed securely: generated, stored, rotated, and destroyed per documented procedures.
- PAN is masked when displayed (show only first 6 / last 4 digits).
- Sensitive authentication data (CVV, PIN) is never stored after authorization.
- Evidence: locate encryption calls in code, verify key loading from secure config.

### Requirement 6: Develop and maintain secure systems

- Code is developed following secure coding guidelines (OWASP Top 10 coverage from Stage 2).
- Custom code is reviewed for vulnerabilities before release (Stage 3 review).
- Public-facing web applications are protected against common attacks (WAF or equivalent).
- Evidence: audit findings (Stage 2) and review results (Stage 3).

### Requirement 7: Restrict access by business need to know

- Access control is implemented in code (RBAC/ABAC from Stage 3 review).
- Default deny: systems deny access unless explicitly permitted.
- Evidence: authorization review results from Stage 3.

### Requirement 8: Identify users and authenticate access

- Unique user identification for all access.
- Strong authentication: MFA for administrative access, strong passwords.
- Session management: timeout, invalidation.
- Evidence: authentication review results from Stage 3.

### Requirement 10: Log and monitor all access

- Audit trail for all access to cardholder data.
- Logging includes: user ID, event type, date/time, success/failure, origination, affected data/resource.
- Logs are protected against tampering.
- Evidence: logging review from Stage 2 (A09) and Stage 3.

## GDPR code-level requirements

Apply when EU personal data is in scope:

### Article 6: Lawful basis / Consent management

- Consent collection: code implements explicit consent capture before data processing.
- Consent storage: consent records include timestamp, scope, and version.
- Consent withdrawal: mechanism exists to withdraw consent and cease processing.
- Evidence: locate consent management code, verify completeness.

### Article 5(1)(c): Data minimization

- Only necessary data fields are collected (no excessive data collection).
- Data retention: mechanism exists to delete data after the retention period.
- Anonymization/pseudonymization: implemented where specified in the threat model.
- Evidence: review data models, collection forms, retention logic.

### Article 17: Right to erasure

- Deletion endpoint or mechanism exists to erase all personal data for a given subject.
- Deletion is cascading: all related records, backups (within feasibility), and cached copies are addressed.
- Deletion verification: confirmation that data has been removed.
- Evidence: locate deletion code, verify cascade logic.

### Article 20: Data portability

- Export endpoint or mechanism exists to provide personal data in a structured, machine-readable format (JSON, CSV).
- Export includes all data categories held for the data subject.
- Evidence: locate export code, verify data coverage.

### Article 33: Breach notification

- Incident detection mechanism exists in code (anomaly detection, integrity monitoring).
- Notification workflow is implemented or integrated (72-hour notification requirement).
- Evidence: locate breach detection and notification code.

## HIPAA code-level requirements

Apply when protected health information (PHI) is in scope:

### Section 164.312(a)(1): Access control

- Unique user identification: each user has a unique identifier.
- Emergency access procedure: mechanism exists for emergency PHI access with audit trail.
- Automatic logoff: session timeout for inactive sessions.
- Encryption and decryption: PHI is encrypted at rest and in transit.
- Evidence: auth/authz review from Stage 3, encryption review.

### Section 164.312(b): Audit controls

- All access to PHI is logged: who accessed, what was accessed, when, from where.
- Logs are tamper-evident: append-only storage or integrity hashing.
- Log retention: minimum 6 years (per HIPAA requirement).
- Evidence: logging review from Stages 2 and 3.

### Section 164.312(c)(1): Integrity

- Electronic PHI integrity: mechanism to detect unauthorized alteration or destruction.
- Checksums, digital signatures, or integrity monitoring on PHI records.
- Evidence: locate integrity verification code.

### Section 164.312(d): Person or entity authentication

- Verify identity of persons or entities seeking access to PHI.
- Multi-factor authentication for remote access to PHI.
- Evidence: authentication review from Stage 3.

### Section 164.312(e)(1): Transmission security

- PHI in transit is encrypted (TLS 1.2+).
- Integrity controls for PHI in transit (message authentication).
- Evidence: TLS configuration review from Stage 3.

## Requirement-level checklist

For each applicable standard requirement, produce a checklist row with the following fields:

```yaml
- requirement_id: "ASVS-2.1.1"          # Standard-specific requirement ID
  standard: "OWASP ASVS L2"             # Standard name and level
  description: "Verify that user set passwords are at least 12 characters in length"
  status: compliant                       # compliant | non_compliant | not_applicable
  evidence: "Password validation in auth/validators.py:42 enforces minimum 12 characters"
  gap_description: null                   # null if compliant, description if non_compliant
  remediation: null                       # null if compliant, specific fix if non_compliant
  source_stage: "review"                  # Which stage provided the evidence (threat-model, audit, review)
  severity: null                          # null if compliant, critical/high/medium/low if non_compliant
```

### Status determination rules

- **`compliant`**: Evidence from Stages 1-3 confirms the requirement is met. Cite the specific finding, file:line, or review result.
- **`non_compliant`**: Evidence from Stages 1-3 shows the requirement is not met. Describe the gap and provide a specific remediation.
- **`not_applicable`**: The requirement does not apply to this system. Provide justification (e.g. "No file upload functionality exists" for file upload requirements).

Do not mark a requirement as `compliant` without evidence. If no evidence exists (the requirement was not checked in Stages 1-3), mark as `non_compliant` with `gap_description: "Not verified — insufficient evidence from prior stages"` and `remediation: "Manual verification required"`.

## Integrated Security Advisory generation

Synthesize all findings from Stages 1-3 and compliance gaps into a single, priority-ordered action list. This is the primary deliverable of the Sec pipeline.

### Synthesis process

1. Collect all threat mitigations from `SEC-TM-*` with status `unmitigated` or `partial`.
2. Collect all vulnerabilities from `SEC-VA-*` with CVSS >= 4.0.
3. Collect all review findings from Stage 3 with status `missing`, `incorrect`, or `partial`.
4. Collect all compliance gaps with status `non_compliant`.
5. Deduplicate: if the same issue appears in multiple sources, merge into a single advisory item with cross-references.
6. Prioritize using the following order:
   - **P0 — Immediate**: CVSS >= 9.0, critical threat unmitigated, hard regulatory non-compliance.
   - **P1 — Urgent**: CVSS 7.0-8.9, high threat unmitigated, regulatory non-compliance with remediation path.
   - **P2 — Important**: CVSS 4.0-6.9, medium threat, ASVS non-compliance.
   - **P3 — Recommended**: CVSS < 4.0, low threat, best-practice improvements.

### Advisory item format

Each advisory item contains:

```yaml
- id: "ADV-001"
  priority: "P0"
  title: "SQL injection in user search endpoint"
  category: "vulnerability"              # threat | vulnerability | review | compliance
  description: "User input is concatenated into SQL query in search/handler.py:87"
  affected_components: ["api-service"]
  threat_refs: ["TM-003"]               # Cross-reference to threat model
  vuln_refs: ["VA-007"]                  # Cross-reference to vulnerability report
  compliance_refs: ["ASVS-5.3.4", "PCI-DSS-6.5.1"]  # Cross-reference to compliance requirements
  remediation: "Replace string concatenation with parameterized query using SQLAlchemy's bindparam()"
  estimated_effort: "low"                # low (< 1 day), medium (1-3 days), high (> 3 days)
```

## Gap analysis

Group all `non_compliant` items by:

1. **Severity**: critical gaps first, then high, medium, low.
2. **Standard**: group by compliance standard to show per-standard posture.
3. **Pattern**: identify systemic issues. Example: if 5 different endpoints lack input validation, the pattern is "missing input validation framework" — the remediation is a framework-level fix, not 5 individual fixes.

Present pattern-level findings prominently — they indicate systemic security issues that are more impactful than individual gaps.

## Remediation roadmap

Produce a priority-ordered improvement plan:

### Phase 1 — Immediate (0-1 weeks)

- All P0 items.
- Critical vulnerabilities with known exploits.
- Hard regulatory non-compliance items.

### Phase 2 — Short-term (1-4 weeks)

- All P1 items.
- High-severity vulnerabilities.
- Systemic pattern fixes (e.g. add input validation framework, configure security headers globally).

### Phase 3 — Medium-term (1-3 months)

- All P2 items.
- Medium-severity vulnerabilities.
- ASVS level advancement (e.g. from L1 to L2 compliance).

### Phase 4 — Long-term (3-6 months)

- All P3 items.
- Best-practice improvements.
- Full ASVS L3 compliance (if targeted).
- Security architecture improvements flagged for `arch:review`.

Each phase item includes: the advisory ID, description, estimated effort, and the specific compliance requirements it addresses.

## Interaction model

This stage follows a structured automatic sequence:

1. **Auto-mapping** — Read all Stage 1-3 outputs. Determine applicable standards from RE constraints. Map findings to standard requirements.
2. **Auto-judgment** — For each requirement, determine status based on evidence from prior stages. Produce the requirement-level checklist.
3. **Advisory generation** — Synthesize all findings into the priority-ordered Security Advisory. Perform gap analysis. Build the remediation roadmap.
4. **Present final report** — Present the complete compliance report and Security Advisory to the user. This is the primary interaction point — pause for the user to review.

No user input is needed for steps 1-3. Step 4 requires the user to review and confirm the report before artifacts are created via `sec-record`.

## Escalation

Escalate to the user immediately when:

- **Hard regulatory non-compliance**: A `hard` RE constraint (from `constraint_ref` with `flexibility: hard` and `type: regulatory`) maps to a standard requirement with `non_compliant` status. This carries legal risk and cannot be auto-accepted. Present: the constraint, the standard requirement, the gap, and the remediation options.
- **Multiple critical gaps in a single standard**: Three or more `critical` severity gaps in the same compliance standard indicate a systemic compliance failure. Recommend a focused compliance remediation sprint.
- **Conflicting compliance requirements**: Two applicable standards impose contradictory requirements (rare but possible — e.g. data retention for audit vs. data deletion for GDPR). Present both requirements and ask the user for prioritization.

Do **not** escalate for:

- `not_applicable` classifications — record the justification and proceed.
- Non-critical compliance gaps with clear remediation paths — include in the advisory and proceed.
- Standards that are not triggered by RE constraints — do not apply them unless the user requests.

## Read-only reminder

Sec is read-only. This stage produces the final compliance report and Security Advisory text. All artifact creation goes through `sec-record`. When the compliance verification is complete, provide the user with the exact commands:

```
sec-record: artifact.py init --section compliance-report
# User populates SEC-CR-001.md with the compliance report content
sec-record: artifact.py link SEC-CR-001 --upstream SEC-TM-001
sec-record: artifact.py link SEC-CR-001 --upstream SEC-VA-001
sec-record: artifact.py link SEC-CR-001 --upstream SEC-SR-001
sec-record: artifact.py set-progress SEC-CR-001 --completed 4 --total 4
sec-record: artifact.py set-phase SEC-CR-001 in_review
```

For the Security Advisory (if not already initialized in Stage 3):

```
sec-record: artifact.py init --section security-advisory
# User populates SEC-SR-001.md with the full security advisory content
sec-record: artifact.py link SEC-SR-001 --upstream SEC-TM-001
sec-record: artifact.py link SEC-SR-001 --upstream SEC-VA-001
sec-record: artifact.py link SEC-SR-001 --upstream SEC-CR-001
sec-record: artifact.py set-progress SEC-SR-001 --completed 4 --total 4
sec-record: artifact.py set-phase SEC-SR-001 in_review
```

After both artifacts are in `in_review`, the user reviews the complete Sec output. Approval of all four artifacts (`SEC-TM-*`, `SEC-VA-*`, `SEC-SR-*`, `SEC-CR-*`) marks the Sec pipeline as complete.
