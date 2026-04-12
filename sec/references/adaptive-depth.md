# Adaptive Depth

Sec runs in one of two modes — **light** or **heavy** — and the mode drives how deeply the four-stage security workflow executes. The goal is correct sizing: a three-endpoint CRUD app should not get a 40-page threat model with full PCI compliance mapping, and a distributed payment system should not get a one-page OWASP checklist.

## How the mode is decided

Sec determines its mode by inspecting the approved Arch artifacts. Three signals are checked in order:

| Signal | Detection | Result |
|--------|-----------|--------|
| Component count | Count `ARCH-COMP-*.components` entries | > 3 components → heavy |
| Inter-service communication | Check `ARCH-DIAG-*` for sequence diagrams between services, or `ARCH-COMP-*.dependencies` crossing service boundaries | Any inter-service communication → heavy |
| External interface count | Count interfaces in `ARCH-COMP-*` where `type` is `gateway`, `edge`, or otherwise external-facing | > 2 external interfaces → heavy |

If **any** signal triggers, the mode is heavy. If **none** trigger, the mode is light.

```
components ≤ 3  AND  no inter-service  AND  external interfaces ≤ 2  →  light
otherwise                                                              →  heavy
```

Tell the user which mode you chose and which signal(s) triggered it. The user may override by saying "run Sec in heavy mode" or "run Sec in light mode".

## Light mode

Light mode is **not superficial**. It is "correct for a small system". The security analysis is thorough within its scope but avoids over-engineering the artifact set.

### Stage-level behavior

| Stage | Light mode action |
|-------|------------------|
| threat-model | Abbreviated STRIDE — identify the top threats per category rather than exhaustive enumeration. Skip DREAD scoring; use simple `high / medium / low` risk levels instead. Produce a simplified DFD with one trust boundary. |
| audit | Focus on OWASP Top 10 only. Dependency CVE scan runs in full. Skip CWE-level deep analysis. Inline findings in a single vulnerability report rather than per-component reports. |
| review | Focus on top mitigations — verify that the highest-risk threats have planned or implemented mitigations. Skip exhaustive mitigation coverage analysis. |
| compliance | ASVS Level 1 only. Skip PCI/GDPR/HIPAA unless a `constraint_ref` explicitly requires them. Produce a single compliance report. |

### Artifact depth in light mode

- **Threat Model**: 3-8 threat entries covering OWASP Top 10 relevance. One trust boundary. Simplified data flow security table. No attack tree.
- **Vulnerability Report**: Inline report covering dependency CVEs and top code-level findings. No per-component breakdown.
- **Security Advisory**: 2-5 advisory entries focused on the highest-impact improvements.
- **Compliance Report**: ASVS L1 assessment only. Gap summary and roadmap kept brief.

## Heavy mode

### Stage-level behavior

| Stage | Heavy mode action |
|-------|------------------|
| threat-model | Full STRIDE analysis with DREAD scoring for every threat. Component-level threat analysis for each `ARCH-COMP-*`. Complete DFD with all trust boundaries. Attack tree in Mermaid. |
| audit | Full CWE/CVSS detailed analysis. Per-component vulnerability reports. Dependency CVE scan with transitive dependency analysis. Code-level pattern-specific checks from the [Impl input contract](contracts/impl-input-contract.md). |
| review | Exhaustive mitigation coverage — every `critical` and `high` threat must have a mitigation with status. Cross-reference verification between threats, vulnerabilities, and advisories. |
| compliance | ASVS Level 2 or Level 3 as appropriate. PCI DSS if payment processing. GDPR if PII of EU residents. HIPAA if health data. Additional standards as `constraint_ref` entries dictate. Remediation roadmap with phased timeline. |

### Artifact depth in heavy mode

- **Threat Model**: Full STRIDE with DREAD. One entry per significant threat (expect 10-30). Multiple trust boundaries. Complete data flow security table. Attack tree diagram.
- **Vulnerability Report**: Per-component analysis. Full CVSS vectors. Proof-of-concept for critical/high findings. Dependency vulnerability detail with fixed versions.
- **Security Advisory**: Comprehensive advisory set covering architecture, code, configuration, dependency, and process categories.
- **Compliance Report**: Multi-standard assessment. Detailed findings per requirement. Phased remediation roadmap with target dates.

## Mode is not about quality

Both modes produce actionable security artifacts. Mode controls **how much depth and breadth the analysis covers**, not how carefully the analysis is done. A light-mode Sec still catches critical vulnerabilities, still scans dependencies, still checks OWASP Top 10. It just does not produce a 30-entry threat model with full DREAD scores when the system has two components and one external endpoint.

## User override

The user can force either mode at any time:

- "Run Sec in heavy mode" — even if signals say light, produce full-depth artifacts.
- "Run Sec in light mode" — even if signals say heavy, produce trimmed artifacts.

Record the override in the threat model's metadata so downstream skills know the depth level.
