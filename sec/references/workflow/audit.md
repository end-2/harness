# Workflow — Stage 2: Security Audit Stage — Detailed Rules

## Role

Perform automated static analysis of Impl code for security vulnerabilities. Classify every finding by CWE, score with CVSS v3.1, map to OWASP Top 10, detect hardcoded secrets, and scan dependencies for known CVEs. This stage runs fully automatically with no user input — escalate only for critical findings.

## Inputs

### Impl artifact consumption

- **`IMPL-MAP-*.implementation_map.module_path`** — Audit target files. Every module path is a file or directory to analyse. Walk each path and include all source files.

- **`IMPL-MAP-*.implementation_map.interfaces_implemented`** — API endpoint audit targets. Every implemented interface is an entry point for injection, authentication, and authorization checks. Cross-reference with the threat model's attack surface catalog.

- **`IMPL-CODE-*.code_structure.external_dependencies`** — CVE scan targets. Every external dependency (name + version) is checked against known CVE databases. Record: dependency name, version, known CVEs, severity, patch availability.

- **`IMPL-CODE-*.code_structure.environment_config`** — Secret/credential exposure check. Scan every environment variable, config file path, and configuration value for hardcoded secrets, default credentials, and sensitive data in plaintext.

- **`IMPL-IDR-*.implementation_decisions.pattern_applied`** — Pattern-specific security checks:
  - `Repository` → SQL injection in query construction, ORM misuse
  - `Strategy` → untrusted strategy selection from user input
  - `Observer/Event` → event injection, unauthorized subscription
  - `Decorator` → privilege bypass via unwrapped access
  - `Factory` → object injection via untrusted type parameters
  - `Singleton` → thread-safety issues, shared state leakage

### Threat model integration

Read the threat model output from Stage 1. Prioritize audit scope by threat risk levels:

1. **Critical/High risk** components and data flows — deep analysis. Read every line of code in the module. Check all OWASP Top 10 categories.
2. **Medium risk** — standard analysis. Check the OWASP Top 10 categories relevant to the component's type (e.g. a data store gets A01, A02, A03, A05; an API gateway gets A01, A03, A07, A10).
3. **Low/Informational** — lightweight scan. Check for hardcoded secrets and known CVE dependencies only.

## OWASP Top 10 scanning

For each audit target, systematically scan for all ten categories. The patterns below are indicative, not exhaustive — adapt to the language and framework in `ARCH-TECH-*`.

### A01: Broken Access Control

Code patterns to detect:

- Missing authorization checks on endpoints (controller/handler has no authz middleware or decorator).
- Insecure Direct Object References (IDOR): user-supplied ID used directly in database query without ownership verification.
- Path traversal: user input concatenated into file paths without sanitization (`../` sequences).
- Missing function-level access control: admin endpoints accessible without role check.
- CORS misconfiguration allowing unauthorized origins (`Access-Control-Allow-Origin: *` with credentials).
- Metadata manipulation: JWT claims or session attributes modifiable by client.

### A02: Cryptographic Failures

Code patterns to detect:

- Weak algorithms: MD5, SHA1 for integrity, DES, 3DES, RC4 for encryption, RSA < 2048 bits.
- Hardcoded encryption keys, IV values, or salts in source code.
- Missing encryption for sensitive data at rest (PII/PHI/financial data stored in plaintext).
- Missing TLS for data in transit (HTTP endpoints handling sensitive data).
- Insufficient key length: AES-128 where AES-256 is required by regulation.
- Deterministic encryption where randomized is needed (ECB mode, static IV).
- Missing certificate validation in outbound HTTPS calls (`verify=False`, `rejectUnauthorized: false`).

### A03: Injection

Code patterns to detect:

- **SQL injection**: String concatenation or interpolation in SQL queries. Missing parameterized queries / prepared statements.
- **NoSQL injection**: Unsanitized user input in MongoDB queries (`$where`, `$regex` with user input).
- **OS command injection**: User input passed to `exec()`, `system()`, `subprocess.call(shell=True)`, backtick execution.
- **LDAP injection**: User input in LDAP filter construction without escaping.
- **XPath injection**: User input in XPath expressions.
- **Expression Language injection**: User input in template engines without sandboxing (SSTI).
- **Header injection**: User input in HTTP response headers (CRLF injection).

### A04: Insecure Design

Code patterns to detect:

- Missing rate limiting on authentication endpoints, password reset, and API calls.
- No account lockout after failed authentication attempts.
- Trust boundary violations: internal service endpoints exposed without authentication.
- Missing CSRF protection on state-changing operations.
- Business logic flaws: negative quantity in purchase, race conditions in balance checks.
- Missing input size limits (request body, file upload, array length).

### A05: Security Misconfiguration

Code patterns to detect:

- Default credentials in configuration files or code (`admin/admin`, `root/password`).
- Debug mode enabled in production configuration (`DEBUG=True`, `NODE_ENV=development`).
- Unnecessary features enabled: directory listing, HTTP TRACE method, GraphQL introspection.
- Verbose error messages exposing stack traces, SQL queries, or internal paths.
- Missing security headers in HTTP responses.
- Overly permissive file permissions in deployment scripts.
- Sample or test files included in production paths.

### A06: Vulnerable and Outdated Components

Analysis steps:

- Parse dependency manifest files (`package.json`, `requirements.txt`, `pom.xml`, `go.mod`, `Cargo.toml`, `Gemfile.lock`, etc.).
- Cross-reference each dependency name + version against known CVE databases.
- For each vulnerable dependency, record: CVE ID, CVSS score, description, patch version (if available), alternative library (if no patch).
- Flag dependencies with no recent maintenance (last release > 2 years, archived repository).
- Check for transitive dependency vulnerabilities where feasible.

### A07: Identification and Authentication Failures

Code patterns to detect:

- Credential stuffing enablement: no rate limiting on login, no CAPTCHA, no account lockout.
- Weak password policy: no minimum length, no complexity requirements, no breach-list check.
- Plaintext password storage or weak hashing (MD5, SHA1, unsalted SHA256).
- Session fixation: session ID not regenerated after authentication.
- Session tokens in URL parameters (leakage via referrer header, logs).
- Missing session timeout or excessively long session lifetimes.
- Predictable session token generation (sequential, timestamp-based).

### A08: Software and Data Integrity Failures

Code patterns to detect:

- Insecure deserialization: `pickle.loads()`, `ObjectInputStream`, `unserialize()`, `JSON.parse()` on untrusted input without validation.
- Missing integrity verification on updates, plugins, or downloaded resources (no checksum, no signature).
- CI/CD pipeline without integrity controls (unsigned artifacts, unverified base images).
- Missing Subresource Integrity (SRI) for CDN-loaded scripts and stylesheets.
- Auto-update mechanisms without signature verification.

### A09: Security Logging and Monitoring Failures

Code patterns to detect:

- Missing audit logging for authentication events (login, logout, failed attempts).
- Missing logging for authorization failures (access denied events).
- Missing logging for input validation failures (potential attack detection).
- Sensitive data in logs (passwords, tokens, credit card numbers, PII).
- Log injection vulnerability: user input written to logs without sanitization.
- No centralized logging configuration (logs scattered, no aggregation).
- Missing alerting thresholds for security events.

### A10: Server-Side Request Forgery (SSRF)

Code patterns to detect:

- User-supplied URLs passed to server-side HTTP clients without validation.
- URL validation bypass: IP address forms (`0x7f000001`, `2130706433`, `017700000001`), DNS rebinding, URL parsing inconsistencies.
- Access to cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
- Internal service discovery via user-controlled URLs.
- Missing allowlist for outbound request destinations.
- Redirect following that bypasses initial URL validation.

## CWE classification

Every finding must be classified with a specific CWE ID. Do not use broad categories — use the most specific CWE that matches the finding.

Common mappings:

| OWASP | Typical CWE IDs |
|---|---|
| A01 | CWE-284, CWE-285, CWE-639, CWE-22, CWE-352 |
| A02 | CWE-327, CWE-328, CWE-330, CWE-312, CWE-319 |
| A03 | CWE-89, CWE-79, CWE-78, CWE-77, CWE-90, CWE-917 |
| A04 | CWE-799, CWE-770, CWE-307, CWE-362 |
| A05 | CWE-16, CWE-209, CWE-215, CWE-611 |
| A06 | CWE-1104, CWE-937 |
| A07 | CWE-287, CWE-384, CWE-613, CWE-640 |
| A08 | CWE-502, CWE-829, CWE-494 |
| A09 | CWE-778, CWE-117, CWE-532 |
| A10 | CWE-918 |

Record the CWE ID, name, and a one-line description for each finding.

## CVSS v3.1 scoring

Score every finding using the CVSS v3.1 Base Score. Calculate from these metrics:

### Attack Vector (AV)

| Value | Description |
|---|---|
| Network (N) | Exploitable from the network (remote) |
| Adjacent (A) | Exploitable from adjacent network |
| Local (L) | Requires local access |
| Physical (P) | Requires physical access |

### Attack Complexity (AC)

| Value | Description |
|---|---|
| Low (L) | No special conditions needed |
| High (H) | Requires specific conditions or preparation |

### Privileges Required (PR)

| Value | Description |
|---|---|
| None (N) | No authentication needed |
| Low (L) | Basic user privileges |
| High (H) | Administrative privileges |

### User Interaction (UI)

| Value | Description |
|---|---|
| None (N) | No user interaction needed |
| Required (R) | Requires victim to perform an action |

### Scope (S)

| Value | Description |
|---|---|
| Unchanged (U) | Impact limited to vulnerable component |
| Changed (C) | Impact extends beyond vulnerable component |

### Impact (Confidentiality / Integrity / Availability)

| Value | Description |
|---|---|
| None (N) | No impact |
| Low (L) | Limited impact |
| High (H) | Total loss |

Present the CVSS vector string (e.g. `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`) and the calculated base score (0.0-10.0) for each finding.

### Severity mapping

| Score | Severity |
|---|---|
| 9.0-10.0 | Critical |
| 7.0-8.9 | High |
| 4.0-6.9 | Medium |
| 0.1-3.9 | Low |
| 0.0 | None |

## Secret detection

Scan all source files, configuration files, and environment files for hardcoded secrets. Patterns to detect:

- **API keys**: Strings matching provider-specific patterns (AWS `AKIA...`, Google `AIza...`, Stripe `sk_live_...`, etc.).
- **Passwords**: Variables named `password`, `passwd`, `secret`, `credential` with string literal assignments.
- **Tokens**: JWT tokens, OAuth tokens, bearer tokens in source code.
- **Certificates and private keys**: PEM-encoded certificates (`-----BEGIN`), PKCS files.
- **Connection strings**: Database URLs with embedded credentials (`postgres://user:pass@host`).
- **Cloud credentials**: AWS access keys, GCP service account JSON, Azure connection strings.

For each detected secret:

- Record the file path and line number.
- Classify the secret type.
- Assess exposure risk (committed to VCS, accessible in production, rotation difficulty).
- Recommend remediation: move to environment variable, use secrets manager, rotate immediately.

## Dependency analysis

For each external dependency with a known CVE:

1. Record: dependency name, current version, CVE ID, CVSS score, description.
2. Check patch availability: is there a fixed version? Record the version number.
3. If no patch is available: recommend alternatives (different library, workaround, WAF rule).
4. Assess transitive risk: is the vulnerable function actually called in the codebase?
5. Priority: dependencies with CVSS >= 7.0 and confirmed usage of the vulnerable function are high priority.

## Interaction model

This stage runs fully automatically. No user input is needed.

1. Read all Impl artifacts to determine audit scope.
2. Read the threat model from Stage 1 for prioritization.
3. Systematically scan each audit target through all OWASP Top 10 categories.
4. Classify, score, and document every finding.
5. Scan for hardcoded secrets.
6. Analyse dependencies for known CVEs.
7. Compile the Vulnerability Report.
8. Present the report summary to the user. Provide `sec-record` commands.

## Escalation

Escalate to the user immediately (pause analysis and present the finding) when:

- **CVSS >= 9.0** — A critical vulnerability that could lead to full system compromise. Present: the finding, CVSS vector, affected component, proof-of-concept scenario, and recommended immediate action.
- **Zero-day vulnerability** — A dependency has a known CVE with no available patch. Present: the CVE details, affected dependency, whether the vulnerable function is actually used, and alternative libraries or workarounds.
- **Active exploitation** — A finding matches a vulnerability known to be actively exploited in the wild (per CISA KEV or equivalent).

Do **not** escalate for:

- Medium or low severity findings — include in the report and proceed.
- Dependencies with CVEs that have available patches — record the patch version and recommend upgrade.
- Findings in test code or development-only dependencies (record but mark as low priority).

## Read-only reminder

Sec is read-only. This stage produces analysis text only. All artifact creation must go through `sec-record`. When the audit is complete, provide the user with the exact commands:

```
sec-record: artifact.py init --section vulnerability-report
# User populates SEC-VA-001.md with the vulnerability report content
sec-record: artifact.py link SEC-VA-001 --upstream SEC-TM-001
sec-record: artifact.py link SEC-VA-001 --upstream IMPL-MAP-001
sec-record: artifact.py link SEC-VA-001 --upstream IMPL-CODE-001
sec-record: artifact.py set-progress SEC-VA-001 --completed 6 --total 6
sec-record: artifact.py set-phase SEC-VA-001 in_review
```

Adjust the upstream links to include the threat model artifact and every Impl artifact referenced in the audit.
