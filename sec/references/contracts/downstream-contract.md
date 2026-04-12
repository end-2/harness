# Downstream Consumption Contract

What downstream skills (`devops`, `qa`, `impl`) expect to find in the four Sec sections. Read this before transitioning any Sec artifact to `approved`, so you can verify the hand-off is consumable.

## devops — deployment constraints and security gates

**Reads**: `SEC-TM-*`, `SEC-SR-*`, `SEC-CR-*`, `SEC-VA-*`.

### From Threat Model (`SEC-TM-*`)

- `trust_boundary` → network segmentation requirements. Every trust boundary must map to a network boundary in the deployment topology.
- `mitigation` where mitigation involves infrastructure → deployment constraints (TLS termination, WAF rules, network policies, firewall rules).
- `affected_components` → which deployment units need security-hardened configurations.
- `dread_score` → prioritization of which deployment hardening to apply first.
- `data_flow_security` → encryption-in-transit requirements between deployment units.

### From Security Advisory (`SEC-SR-*`)

- `category == "configuration"` → infrastructure security configuration items (TLS versions, cipher suites, header policies, CORS settings).
- `category == "architecture"` → infrastructure-level changes (load balancer rules, service mesh policies, secret injection methods).
- `recommended_action` → specific infrastructure changes devops must implement.
- `priority` → ordering of security configuration tasks.

### From Compliance Report (`SEC-CR-*`)

- `findings` where `status == "non_compliant"` and remediation involves infrastructure → logging, monitoring, and audit trail requirements.
- `standard` → compliance-specific deployment requirements (PCI → network segmentation, HIPAA → encryption, GDPR → data residency).
- `remediation_roadmap` → timeline for infrastructure security improvements.

### From Vulnerability Report (`SEC-VA-*`)

- `severity == "critical" | "high"` → security scan gates in CI/CD pipeline; builds must not deploy if these are unresolved.
- `dependency_vuln` → dependency scanning step configuration in the build pipeline.
- `remediation` → automated fix targets for dependency update automation.

**devops will fail its run if**: a threat model entry names an infrastructure mitigation but no corresponding security advisory provides the specific configuration, or a compliance finding requires logging but no monitoring requirement is specified.

## qa — security test scenarios

**Reads**: `SEC-TM-*`, `SEC-VA-*`, `SEC-SR-*`.

### From Threat Model (`SEC-TM-*`)

- `stride_category` + `attack_vector` → negative test scenarios. Each threat becomes at least one test that verifies the attack is blocked.
- `mitigation` + `mitigation_status` → security acceptance criteria. If `mitigation_status == "implemented"`, qa must verify it works; if `"planned"`, qa must create a placeholder test.
- `affected_components` → scope of security testing per component.
- `trust_boundary` → boundary-crossing tests (e.g., test that an internal service rejects unauthenticated requests from outside its boundary).
- `attack_tree` → test case derivation from attack paths; each leaf node in the attack tree is a test scenario.

### From Vulnerability Report (`SEC-VA-*`)

- `cwe_id` / `owasp_category` → regression test targets. Each reported vulnerability must have a corresponding test that prevents reintroduction.
- `proof_of_concept` → test input for the regression test (sanitized if needed).
- `location` → specific file and function to target in the test.
- `remediation` → the fix that the test should verify is in place.

### From Security Advisory (`SEC-SR-*`)

- `recommended_action` → security acceptance criteria that qa includes in the test plan.
- `category == "code"` → code-level security tests (input validation, output encoding, auth checks).
- `affected_components` → components that need security-focused test coverage.

**qa will fail its run if**: a threat model entry with `risk_level == "critical" | "high"` has no corresponding test scenario, or a vulnerability report entry has no regression test target.

## impl — remediation guidance

**Reads**: `SEC-VA-*`, `SEC-SR-*`.

### From Vulnerability Report (`SEC-VA-*`)

- `location` → exact file, line, and function to fix.
- `remediation` → step-by-step fix guidance.
- `remediation_effort` → estimated effort for planning.
- `cwe_id` → reference to the weakness pattern for understanding the fix category.
- `dependency_vuln.fixed_version` → target version for dependency updates.
- `impl_refs` → the Impl artifact that owns the vulnerable code.

### From Security Advisory (`SEC-SR-*`)

- `category == "code"` → code-level security improvements (add input validation, replace insecure function, implement proper error handling).
- `recommended_action` → specific code change to make.
- `alternative_actions` → fallback approaches if the primary recommendation is not feasible.
- `affected_components` → which Impl modules need changes.

**impl will fail its run if**: a vulnerability report entry references an `impl_ref` that does not exist, or a security advisory with `priority == "critical"` has no `recommended_action`.

## Downstream linking

Before approving, for each downstream skill the Sec artifacts will feed, add a downstream ref:

```
python ${SKILL_DIR}/scripts/artifact.py link <sec-tm-id> --downstream QA-STRATEGY-001
```

If the downstream artifact does not exist yet, leave the `downstream_ref` list empty — the downstream skill will back-fill when it runs. What matters at Sec approval time is that the upstream refs (back to Arch, Impl, and RE) are complete.
