# Section Schemas

The four Sec sections each carry their own structured block inside the metadata file. The block mirrors the tables in the paired markdown document — the markdown is the human-readable source of truth for prose, and the YAML block is what downstream skills and scripts parse.

Common metadata fields (`artifact_id`, `phase`, `approval`, ...) are covered in [meta-schema.md](meta-schema.md).

## 1. `threat-model`

Block key: `threat_model`

```yaml
threat_model:
  threats:
    - id: TM-001
      title: Unauthenticated access to API gateway
      stride_category: spoofing
      description: |
        An attacker could impersonate a legitimate user by sending
        requests to the API gateway without valid credentials.
      attack_vector: |
        1. Attacker sends HTTP request to /api/v1/users without Authorization header
        2. Gateway forwards request to internal user-service
        3. User-service returns PII without auth check
      affected_components: [ARCH-COMP-001, ARCH-COMP-003]
      trust_boundary: external
      dread_score:
        damage: 8
        reproducibility: 9
        exploitability: 7
        affected_users: 9
        discoverability: 6
      risk_level: critical
      mitigation: |
        Enforce JWT validation at gateway level before forwarding.
        Implement service-to-service mTLS for internal communication.
      mitigation_status: planned
      arch_refs: [ARCH-COMP-001, ARCH-DEC-003]
      re_refs: [NFR-001]

  trust_boundaries:
    - id: TB-001
      name: External boundary
      components: [ARCH-COMP-001]
      entry_points: ["/api/v1/*"]
      controls: [JWT validation, rate limiting, WAF]

  data_flow_security:
    - id: DFS-001
      from: api-gateway
      to: user-service
      data_classification: PII
      encryption: TLS 1.3
      auth_method: mTLS

  attack_tree: |
    ```mermaid
    graph TD
      A[Access PII] --> B[Bypass Gateway Auth]
      A --> C[Exploit Internal Service]
      B --> D[Missing JWT Check]
      B --> E[Token Forgery]
      C --> F[SSRF via Gateway]
    ```
```

### Threat entry fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | `TM-NNN`, unique within this artifact |
| `title` | yes | Short human-readable title of the threat |
| `stride_category` | yes | One of `spoofing`, `tampering`, `repudiation`, `information_disclosure`, `denial_of_service`, `elevation_of_privilege` |
| `description` | yes | Detailed description of the threat scenario |
| `attack_vector` | yes | Step-by-step attack path an adversary would follow |
| `affected_components` | yes | List of `ARCH-COMP-*` ids that this threat targets |
| `trust_boundary` | yes | Which trust boundary is crossed or violated (`external`, `internal`, `data`, `processing`) |
| `dread_score` | yes | DREAD risk assessment (see below) |
| `risk_level` | yes | Derived from DREAD: `critical`, `high`, `medium`, `low`, `informational` |
| `mitigation` | yes | Recommended mitigation strategy |
| `mitigation_status` | yes | One of `implemented`, `planned`, `accepted_risk`, `not_applicable` |
| `arch_refs` | yes | Arch artifact ids that surfaced this threat |
| `re_refs` | optional | RE ids reached via Arch's `re_refs` |

### DREAD score fields

Each field is scored 1-10:

| Field | Description |
|-------|-------------|
| `damage` | How severe is the damage if the attack succeeds? |
| `reproducibility` | How easy is it to reproduce the attack? |
| `exploitability` | How easy is it to launch the attack? |
| `affected_users` | What percentage of users are affected? |
| `discoverability` | How easy is it to discover the vulnerability? |

**Risk level derivation**: average the five scores, then map: >= 9 critical, >= 7 high, >= 5 medium, >= 3 low, < 3 informational.

### Auxiliary fields

| Field | Required | Description |
|-------|----------|-------------|
| `trust_boundaries` | yes (at least one) | List of `{id, name, components, entry_points, controls}` defining each trust boundary in the system |
| `data_flow_security` | yes | List of `{id, from, to, data_classification, encryption, auth_method}` documenting security properties of each data flow |
| `attack_tree` | optional | Mermaid diagram showing attack paths; leaf nodes become test scenarios for qa |

## 2. `vulnerability-report`

Block key: `vulnerability_report`

```yaml
vulnerability_report:
  - id: VA-001
    title: SQL Injection in user search endpoint
    cwe_id: CWE-89
    owasp_category: A03:2021-Injection
    severity: high
    cvss_score: 8.6
    cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N"
    location:
      file: src/users/repository.ts
      line: 42
      function: searchUsers
    description: |
      The searchUsers function concatenates user input directly into
      a SQL query string without parameterization.
    proof_of_concept: |
      GET /api/v1/users?q=' OR 1=1--
      Returns all user records including PII.
    remediation: |
      Replace string concatenation with parameterized query.
      Use the ORM's built-in query builder.
    remediation_effort: low
    dependency_vuln: null
    impl_refs: [IMPL-MAP-001]
    arch_refs: [ARCH-COMP-003]
    re_refs: [FR-005]
    threat_refs: [SEC-TM-001]
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | `VA-NNN`, unique within this artifact |
| `title` | yes | Short human-readable title |
| `cwe_id` | yes | Common Weakness Enumeration identifier (e.g. `CWE-89`) |
| `owasp_category` | yes | OWASP Top 10 category (e.g. `A03:2021-Injection`) |
| `severity` | yes | One of `critical`, `high`, `medium`, `low`, `informational` |
| `cvss_score` | yes | CVSS v3.1 base score (0.0 - 10.0) |
| `cvss_vector` | yes | Full CVSS v3.1 vector string |
| `location` | yes | `{file, line, function}` — exact code location |
| `description` | yes | Detailed description of the vulnerability |
| `proof_of_concept` | optional | Demonstration of exploitability (sanitized for safety) |
| `remediation` | yes | Step-by-step fix guidance |
| `remediation_effort` | yes | One of `low` (hours), `medium` (days), `high` (weeks) |
| `dependency_vuln` | conditional | Present when the vulnerability is in a dependency; `{package, version, cve_id, fixed_version}` |
| `impl_refs` | yes | Impl artifact ids where the vulnerability was found |
| `arch_refs` | optional | Arch artifact ids related to the vulnerability |
| `re_refs` | optional | RE ids reached via Arch/Impl |
| `threat_refs` | optional | `SEC-TM-*` ids of threats this vulnerability substantiates |

### `dependency_vuln` fields (when applicable)

| Field | Required | Description |
|-------|----------|-------------|
| `package` | yes | Package name as it appears in the dependency manifest |
| `version` | yes | Currently-used version |
| `cve_id` | yes | CVE identifier (e.g. `CVE-2024-1234`) |
| `fixed_version` | yes | Minimum version that fixes the vulnerability; `null` if no fix exists |

## 3. `security-advisory`

Block key: `security_advisory`

```yaml
security_advisory:
  - id: SR-001
    title: Implement rate limiting on authentication endpoints
    category: configuration
    priority: high
    description: |
      Authentication endpoints currently have no rate limiting,
      enabling brute-force and credential-stuffing attacks.
    current_state: |
      All API endpoints share a single global rate limit of 1000 req/min.
      Auth endpoints have no specific throttling.
    recommended_action: |
      Add per-IP rate limiting of 10 req/min on /auth/login and /auth/token.
      Implement progressive delays after 3 failed attempts.
      Return 429 with Retry-After header.
    alternative_actions:
      - Add CAPTCHA after 5 failed attempts (less secure but better UX)
      - Implement account lockout after 10 failures (risk of DoS via lockout)
    affected_components: [ARCH-COMP-001]
    threat_refs: [SEC-TM-002]
    vuln_refs: []
    arch_refs: [ARCH-COMP-001]
    re_refs: [NFR-001]
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | `SR-NNN`, unique within this artifact |
| `title` | yes | Short human-readable title |
| `category` | yes | One of `architecture`, `code`, `configuration`, `dependency`, `process` |
| `priority` | yes | One of `critical`, `high`, `medium`, `low` |
| `description` | yes | Detailed description of the security concern |
| `current_state` | yes | Description of the current (insecure or suboptimal) state |
| `recommended_action` | yes | Primary recommended remediation |
| `alternative_actions` | optional | List of alternative approaches with trade-off notes |
| `affected_components` | yes | List of `ARCH-COMP-*` ids affected |
| `threat_refs` | optional | `SEC-TM-*` ids of threats this advisory addresses |
| `vuln_refs` | optional | `SEC-VA-*` ids of vulnerabilities this advisory addresses |
| `arch_refs` | optional | Arch artifact ids related to this advisory |
| `re_refs` | optional | RE ids reached via Arch |

**Category definitions**:

| Category | Scope | Example |
|----------|-------|---------|
| `architecture` | Structural security concern requiring Arch-level change | Missing trust boundary, insecure communication pattern |
| `code` | Code-level security improvement | Add input validation, replace insecure function |
| `configuration` | Runtime/infrastructure configuration change | Enable TLS, configure CORS, set security headers |
| `dependency` | Dependency management action | Upgrade vulnerable package, replace abandoned library |
| `process` | Development/operational process improvement | Add security review step, implement secret rotation |

## 4. `compliance-report`

Block key: `compliance_report`

```yaml
compliance_report:
  id: CR-001
  standard: OWASP ASVS
  version: "4.0.3"
  scope: Web application API layer
  overall_status: partially_compliant
  total_requirements: 50
  compliant_count: 38
  non_compliant_count: 8
  not_applicable_count: 4
  findings:
    - requirement_id: V2.1.1
      title: Password length minimum
      status: compliant
      evidence: |
        Password validation in src/auth/validation.ts enforces
        minimum 12 characters via Joi schema.
      gap_description: null
      remediation: null
    - requirement_id: V3.5.1
      title: OAuth token validation
      status: non_compliant
      evidence: |
        Token validation only checks expiry, not signature
        or audience claim.
      gap_description: |
        Missing signature verification and audience validation
        on OAuth2 access tokens.
      remediation: |
        Implement full JWT validation including signature, issuer,
        audience, and expiry checks using jose library.
  gap_summary: |
    8 non-compliant findings concentrated in session management (V3)
    and access control (V4). Most gaps relate to missing token
    validation and insufficient session timeout configuration.
  remediation_roadmap:
    - phase: immediate
      items: [V3.5.1, V4.1.2]
      target_date: 2026-05-01
    - phase: short_term
      items: [V3.2.1, V4.2.3, V5.1.1]
      target_date: 2026-06-01
    - phase: long_term
      items: [V8.1.1, V9.2.1, V14.1.1]
      target_date: 2026-09-01
  constraint_refs: [ARCH-TECH-002]
  threat_refs: [SEC-TM-001, SEC-TM-003]
  vuln_refs: [SEC-VA-001, SEC-VA-004]
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | `CR-NNN`, unique within this artifact |
| `standard` | yes | Compliance standard name (e.g. `OWASP ASVS`, `PCI DSS`, `HIPAA`, `GDPR`) |
| `version` | yes | Version of the standard being assessed against |
| `scope` | yes | What part of the system this assessment covers |
| `overall_status` | yes | One of `compliant`, `partially_compliant`, `non_compliant` |
| `total_requirements` | yes | Total number of requirements assessed |
| `compliant_count` | yes | Number of requirements met |
| `non_compliant_count` | yes | Number of requirements not met |
| `not_applicable_count` | yes | Number of requirements not applicable to this system |
| `findings` | yes | List of individual requirement assessments (see below) |
| `gap_summary` | yes | Narrative summary of non-compliant areas |
| `remediation_roadmap` | yes | Phased plan to address gaps (see below) |
| `constraint_refs` | optional | `ARCH-TECH-*` ids with regulatory constraints |
| `threat_refs` | optional | `SEC-TM-*` ids related to compliance findings |
| `vuln_refs` | optional | `SEC-VA-*` ids related to compliance findings |

### Finding entry fields

| Field | Required | Description |
|-------|----------|-------------|
| `requirement_id` | yes | Identifier from the compliance standard |
| `title` | yes | Human-readable requirement title |
| `status` | yes | One of `compliant`, `non_compliant`, `not_applicable` |
| `evidence` | yes | Evidence supporting the status determination |
| `gap_description` | conditional | Required when `status == non_compliant`; describes the gap |
| `remediation` | conditional | Required when `status == non_compliant`; step-by-step fix |

### Remediation roadmap entry fields

| Field | Required | Description |
|-------|----------|-------------|
| `phase` | yes | One of `immediate`, `short_term`, `long_term` |
| `items` | yes | List of `requirement_id` values to address in this phase |
| `target_date` | yes | ISO 8601 date for completion target |

**Counts integrity**: `compliant_count + non_compliant_count + not_applicable_count` must equal `total_requirements`. The script enforces this.
