---
name: sec
description: Turn approved Arch and Impl artifacts into four security section artifacts — Threat Model, Vulnerability Report, Security Advisory, and Compliance Report — through STRIDE threat modeling, CWE/CVSS vulnerability auditing, security code review, and OWASP ASVS / PCI DSS / GDPR / HIPAA compliance verification. Use this skill whenever the user wants a security analysis of an approved architecture or implementation, asks for threat modeling or STRIDE analysis, needs a vulnerability audit or code security review, wants compliance verification against security standards, mentions attack surfaces or trust boundaries, or is about to hand off to deployment — even if they don't explicitly say "security".
---

# Sec — Security Skill

Sec is a verification stage of the Harness pipeline. It consumes approved Arch artifacts (Architecture Decisions, Component Structure, Technology Stack, Diagrams) and Impl artifacts (Implementation Map, Code Structure, Implementation Decisions, Implementation Guide) to produce four security section artifacts that downstream skills (`devops`, `qa`, `impl`) can read directly.

If RE answered **"what are we building?"**, Arch answered **"how is it structured?"**, Impl answered **"what does the code look like?"**, and QA answered **"does the code satisfy the requirements?"**, Sec answers **"is that design and code secure?"**. The architectural and implementation decisions were already settled upstream — do **not** re-debate them. Sec's job is to verify security, identify threats and vulnerabilities, recommend mitigations, and assess compliance.

Threat modeling requires domain context that Arch artifacts alone cannot provide (data sensitivity classifications, threat actor profiles, regulatory scope), so it uses a **dialogue model** with the user. The remaining stages — audit, review, compliance — derive mechanically from upstream artifacts and run as **automatic execution + exception escalation**.

**Sec is read-only.** It analyses artifacts and code but never modifies them. All metadata creation and state changes (phase transitions, approvals, audit trail entries) require the user to explicitly invoke the companion `sec-record` skill in the sibling [sec-record](/Users/sejong/workspace/harness/sec-record/SKILL.md) directory. This separation ensures that risk-acceptance decisions and compliance judgements always have a human in the loop.

## Current state (injected at load)

!`python3 ${SKILL_DIR}/scripts/report.py summary`

The command above lists existing sec artifacts, their phase, approval state, and traceability integrity. Read it before deciding whether this run is a fresh start, a continuation of in-progress analysis, or a re-assessment after upstream changes.

## Input / output contract

**Input**: approved Arch and Impl artifacts in `./artifacts/arch/` and `./artifacts/impl/` (or wherever `HARNESS_ARTIFACTS_DIR` points). Specifically:

From Arch:
- `ARCH-DEC-*` — Architecture Decisions with `re_refs` and trade-offs
- `ARCH-COMP-*` — Component Structure with types, interfaces, and dependencies
- `ARCH-TECH-*` — Technology Stack with `constraint_ref` to RE constraints
- `ARCH-DIAG-*` — Diagrams (C4, sequence, data-flow)

From Impl:
- `IMPL-MAP-*` — Implementation Map with module paths and interface implementations
- `IMPL-CODE-*` — Code Structure with directory layout, dependencies, and environment config
- `IMPL-IDR-*` — Implementation Decisions with applied patterns
- `IMPL-GUIDE-*` — Implementation Guide with setup, build, and conventions

If any upstream artifact is missing or still in `draft` / `in_review`, stop and tell the user — Sec must not run on unstable input. RE artifacts are consumed indirectly through Arch's `re_refs` and `constraint_ref` chains. Read [references/contracts/arch-input-contract.md](references/contracts/arch-input-contract.md) and [references/contracts/impl-input-contract.md](references/contracts/impl-input-contract.md) for the exact parsing rules.

**Output**: four section artifacts under `./artifacts/sec/`, each stored as a YAML metadata file plus a Markdown document:

1. **Threat Model** (`SEC-TM-*`) — trust boundaries derived from component types, data flow security classifications, STRIDE threats per component/flow/boundary, DREAD risk scores, mitigation strategies, and attack trees in Mermaid. Traces back to `ARCH-COMP-*` and `ARCH-DEC-*` via `arch_refs`.
2. **Vulnerability Report** (`SEC-VA-*`) — code-level vulnerabilities classified by CWE, mapped to OWASP Top 10, scored with CVSS v3.1, with file:line locations, proof-of-concept scenarios, and remediation guidance. Traces to `IMPL-MAP-*` and `IMPL-IDR-*` via `impl_refs`.
3. **Security Advisory** (`SEC-SR-*`) — prioritised action items synthesising threats, vulnerabilities, and review findings into architecture / code / configuration / dependency / process recommendations. Cross-references `threat_refs` and `vuln_refs`.
4. **Compliance Report** (`SEC-CR-*`) — per-standard verification (OWASP ASVS L1–L3, PCI DSS, GDPR, HIPAA) with requirement-level pass/fail/N-A status, evidence, gap analysis, and remediation roadmap. Applicable standards are determined from RE `constraints` (via Arch `constraint_ref`).

Each section is a pair `<id>.meta.yaml` + `<id>.md`. Metadata is the single source of truth for state and traceability and is **only** modified through `scripts/artifact.py` (invoked via the `sec-record` skill). Markdown holds the human-readable analysis and is produced from `assets/templates/` scaffolding.

Full schemas: read [references/schemas/section-schemas.md](references/schemas/section-schemas.md) and [references/schemas/meta-schema.md](references/schemas/meta-schema.md) when you need the exact field list.

Downstream consumption contract: read [references/contracts/downstream-contract.md](references/contracts/downstream-contract.md) before declaring the artifact ready, so you know what `devops`, `qa`, and `impl` will look for.

## Adaptive depth

Sec's output depth follows the complexity signalled by Arch and Impl artifacts. Do **not** apply full STRIDE + DREAD + ASVS-L3 to a single-feature CRUD app, and do not reduce a distributed system with PII handling to a quick OWASP checklist.

| Mode | Trigger (from Arch/Impl artifacts) | Output style |
|------|-------------------------------------|--------------|
| **light** | Arch components ≤ 3 **and** single service **and** external interfaces ≤ 2 | OWASP Top 10 checklist audit, lightweight STRIDE (top threats only), dependency CVE scan, inline security guide. Compliance limited to ASVS L1. |
| **heavy** | Arch components > 3 **or** inter-service communication exists **or** external interfaces > 2 | Full STRIDE threat model with DREAD prioritisation, component-level static analysis, CWE-classified vulnerability report with CVSS scoring, OWASP ASVS L2/L3 compliance, and standards-specific reports (PCI DSS / GDPR / HIPAA) as driven by RE constraints. |

Pick the mode at the **start** of `threat-model`, after reading the Arch and Impl artifacts. Tell the user which mode you chose and why. The user may override. Full rules: [references/adaptive-depth.md](references/adaptive-depth.md).

## Workflow (four stages)

```
Arch artifacts (all approved) + Impl artifacts (all approved)
    |
    v
[1] threat-model  --> derive trust boundaries + attack surfaces from Arch,
    |                  dialogue with user on domain context, STRIDE analysis,
    |                  DREAD scoring, mitigation strategies
    v
[2] audit         --> static analysis of Impl code against OWASP Top 10,
    |                  CWE classification, CVSS scoring, dependency CVE scan,
    |                  hardcoded secret detection
    v
[3] review        --> verify threat mitigations are implemented in code,
    |                  deep review of auth/authz/input-validation/crypto logic,
    |                  security header and CORS checks
    v
[4] compliance    --> map stages 1-3 results to ASVS / PCI DSS / GDPR / HIPAA,
                      generate compliance report + integrated security advisory
```

Each stage has detailed behavior rules in `references/workflow/<stage>.md`. When you enter a stage, **Read that file first** and follow the rules there. SKILL.md only gives the summary.

The pipeline is **sequential**: each stage consumes the output of all preceding stages. In light mode, `review` focuses on OWASP Top 10 mitigations only and compliance is limited to ASVS L1 — see [references/adaptive-depth.md](references/adaptive-depth.md).

### Stage 1 — threat-model

Load [references/workflow/threat-model.md](references/workflow/threat-model.md).

- Read Arch artifacts. Derive trust boundaries from `component_structure.type` (`gateway` = external boundary, `store` = data boundary, `queue` = async boundary). Map `interfaces` to attack surfaces. Trace `dependencies` to data flow paths.
- **Dialogue with the user** to surface domain context not captured in Arch: data sensitivity classifications (PII / PHI / financial / public), user roles and privilege model, external system trust levels, regulatory scope specifics, threat actor profiles (script kiddie, insider, nation-state).
- Apply STRIDE to each component, data flow, and trust boundary crossing. Score each threat with DREAD (Damage, Reproducibility, Exploitability, Affected Users, Discoverability — each 1–10).
- Propose mitigation strategies (mitigate, transfer, accept, avoid) and present to user for confirmation. Risk acceptance decisions require explicit user acknowledgement and must be recorded via `sec-record`.
- Generate attack trees in Mermaid for high-risk threats.

**Escalation**: `risk_level: critical` threats require immediate user attention before proceeding.

### Stage 2 — audit

Load [references/workflow/audit.md](references/workflow/audit.md).

- Determine audit scope from Impl artifacts: `implementation_map.module_path` for file targets, `interfaces_implemented` for API endpoint checks, `code_structure.external_dependencies` for CVE scanning, `environment_config` for secret/credential exposure.
- Prioritise audit based on threat model: components and flows marked high/critical risk get deeper analysis.
- Scan for OWASP Top 10 vulnerability patterns (A01 Broken Access Control through A10 SSRF).
- Classify every finding by CWE ID. Score with CVSS v3.1 base score.
- Detect hardcoded secrets (API keys, passwords, tokens, certificates).
- Analyse `external_dependencies` against known CVE databases. Flag patches available vs. no-fix-available.

**Escalation**: CVSS ≥ 9.0 findings and zero-day vulnerabilities (no patch available) are escalated to the user immediately with recommended alternatives.

**Interaction model**: automatic execution, no user input needed (except escalations).

### Stage 3 — review

Load [references/workflow/review.md](references/workflow/review.md).

- Verify that each threat model mitigation (`TM-*.mitigation`) is correctly implemented in code. For example: `TM-001: Spoofing -> JWT verification` means check that JWT validation covers algorithm pinning, expiry, and signature verification.
- Deep-review authentication and authorisation logic: flow completeness, privilege escalation paths, session management, password storage.
- Verify input validation and sanitisation: whitelist vs. blacklist, output encoding (XSS), parameterised queries (SQLi), file upload restrictions.
- Check error handling for information leakage (stack traces, internal paths, DB errors in responses).
- Verify security headers (CSP, HSTS, X-Frame-Options) and CORS configuration.
- Assess cryptographic usage: algorithm choice, key length, IV/nonce reuse.

**Escalation**: critical-threat mitigations that are unimplemented or incorrectly implemented in code are escalated. Architecture-level security flaws that require Arch changes are flagged for `arch:review` feedback.

**Interaction model**: automatic execution, results reported at completion.

### Stage 4 — compliance

Load [references/workflow/compliance.md](references/workflow/compliance.md).

- Determine applicable standards from RE `constraints` (via Arch `constraint_ref`): `type: regulatory` constraints map to specific standards (GDPR, HIPAA, PCI DSS). OWASP ASVS level is determined by the system's risk profile and regulatory requirements.
- Map results from stages 1–3 to standard requirements: threat model mitigations → ASVS design requirements; audit findings → ASVS implementation requirements; review results → ASVS verification requirements.
- For each applicable standard, produce a requirement-level checklist: `requirement_id`, `status` (compliant / non_compliant / not_applicable), `evidence`, `gap_description`, `remediation`.
- Generate the integrated **Security Advisory** by synthesising threat mitigations, vulnerability remediation, review feedback, and compliance gaps into a priority-ordered action list.
- Present the final security report to the user — this is the primary user-facing deliverable of the Sec pipeline.

**Escalation**: `hard` regulatory constraints (from RE) with `non_compliant` status are escalated immediately — regulatory non-compliance carries legal risk and cannot be auto-accepted.

## Recording artifacts (sec-record)

Sec is **read-only** — it analyses and recommends but never writes metadata or changes approval states. All write operations require the user to invoke the companion `sec-record` skill:

| Action | sec-record command |
|--------|--------------------|
| Create artifact pair from template | `artifact.py init --section <name>` |
| Transition phase | `artifact.py set-phase <id> <phase>` |
| Update progress | `artifact.py set-progress <id> --completed N --total M` |
| Add traceability link | `artifact.py link <id> --upstream <ref>` |
| Request approval | `approval.py request <id>` |
| Approve artifact | `approval.py approve <id> --approver <name> --rationale "..."` |
| Reject artifact | `approval.py reject <id> --approver <name> --rationale "..."` |
| Record risk acceptance | `approval.py accept-risk <id> --approver <name> --rationale "..." [--compliance-override]` |
| Validate schemas | `validate.py [<id>]` |

When analysis produces results that need recording, tell the user exactly which `sec-record` commands to run. For example: "The threat model draft is ready. To create the artifact and transition it to review, run: `/sec-record init --section threat-model` followed by `/sec-record set-phase SEC-TM-001 in_review`."

The artifact directory defaults to `./artifacts/sec/` under the user's current working directory. Override with `HARNESS_ARTIFACTS_DIR`.

## Traceability chain

Sec sits at the verification end of the RE → Arch → Impl → Sec chain:

```
RE constraints/NFRs  -->  Arch decisions/components  -->  Impl code/patterns  -->  Sec findings
   (re_refs)                  (arch_refs)                   (impl_refs)           (threat/vuln/compliance)
```

Every threat traces to Arch components (`arch_refs`) and RE NFRs (`re_refs`). Every vulnerability traces to Impl modules (`impl_refs`) and Arch components. Every compliance finding traces to RE constraints (via `constraint_ref`). Cross-references within Sec (`threat_refs`, `vuln_refs`) link the four sections together.

## Escalation protocol

Three conditions trigger immediate escalation to the user (analysis pauses until the user responds):

1. **Critical vulnerability** — CVSS ≥ 9.0 or zero-day with no available patch
2. **Regulatory non-compliance** — `hard` RE constraint with `non_compliant` status
3. **Unmitigated critical threat** — `risk_level: critical` with `mitigation_status: unmitigated`

For each escalation, present: the finding, its severity, the affected components, the recommended action, and alternatives. The user's decision must be recorded via `sec-record` (`approval.py accept-risk` or `approval.py approve` with rationale) to maintain the audit trail. For compliance-report artifacts, `accept-risk` additionally requires `--compliance-override`. Full protocol: [references/escalation-protocol.md](references/escalation-protocol.md).

## A few non-negotiables

- **Arch and Impl are the source of truth.** Do not invent components or assume code patterns not present in the artifacts. If the artifacts are incomplete, send the user back to the relevant upstream skill.
- **Dialogue for threat modeling, automation for the rest.** Stage 1 requires user input on domain context. Stages 2–4 run automatically and only escalate on the conditions listed above.
- **Adaptive depth.** Light mode is not careless — it is correct sizing. Do not produce a 50-page STRIDE analysis for a single REST endpoint.
- **Four sections, nothing more.** Sec stops at design-and-code security verification. Penetration testing (DAST), runtime security monitoring, and infrastructure hardening belong to `devops`.
- **Traceability.** Every threat cites Arch refs. Every vulnerability cites Impl refs. Every compliance finding cites the standard requirement and the RE constraint that mandated it. If a finding has no anchor, it does not belong in the artifact yet.
- **Read-only analysis.** Sec never writes metadata directly. All state changes go through `sec-record` on explicit user invocation. This is not bureaucracy — it ensures risk-acceptance decisions have a human accountable for them.
- **Standards-based.** Use STRIDE/DREAD for threats, CWE for vulnerability classification, CVSS v3.1 for scoring, OWASP Top 10 for code patterns, and ASVS/PCI-DSS/GDPR/HIPAA for compliance. Consistent use of industry standards makes artifacts auditable and comparable.
