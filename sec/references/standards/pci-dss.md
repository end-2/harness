# PCI DSS — Code-Level Requirements

Focused on requirements verifiable through code analysis. PCI DSS v4.0 aligned.

---

## Requirement 3 — Protect Stored Cardholder Data

### What to verify in code:

**Encryption of stored data:**
- PAN must be rendered unreadable wherever stored (encryption, hashing, masking, truncation)
- Acceptable algorithms: AES-256, RSA 2048+, TDES (legacy, migrating away)
- Unacceptable: DES, RC4, ECB mode, MD5/SHA1 for hashing PANs

**Key management:**
- Encryption keys not hardcoded in source
- Key rotation mechanism exists
- Key storage separated from encrypted data
- Key-encrypting keys separate from data-encrypting keys

**Data masking:**
- PAN display limited to first 6 / last 4 digits maximum
- Full PAN never in logs, error messages, or debug output

**Detection patterns:**
```
card.number|pan|credit.card|account.number  → check storage/display
encrypt|decrypt|AES|RSA  → verify algorithm and key handling
mask|truncate|first.6|last.4  → verify masking rules
log.*(card|pan|credit)|print.*(card|pan)  → sensitive data in logs
```

**Code-level checks:**
- Search data models for cardholder data fields — verify encryption at field or storage level
- Search logs for PAN/card data leakage
- Verify encryption key loading from secure config (env vars, vault), not hardcoded
- Check display functions for proper masking

---

## Requirement 4 — Encrypt Transmission of Cardholder Data

### What to verify in code:

**TLS enforcement:**
- All transmission of cardholder data over TLS 1.2 or higher
- No fallback to SSL or TLS 1.0/1.1
- Certificate validation enabled (no `verify=False`)

**Certificate management:**
- Certificates not expired or self-signed in production
- Certificate pinning for mobile/API clients (recommended)

**Detection patterns:**
```
http://  → non-HTTPS URLs where cardholder data transmitted
tls|ssl|TLS_VERSION  → check minimum version
verify\s*=\s*False|VERIFY_SSL.*false|rejectUnauthorized.*false
SSLv3|TLSv1\.0|TLSv1\.1  → deprecated protocols
cipher|CIPHER  → check for weak cipher suites
```

**Code-level checks:**
- Verify all API endpoints use HTTPS
- Check TLS configuration for minimum version 1.2
- Search for disabled certificate verification
- Verify no cardholder data sent via unencrypted channels (email, SMS, query strings)

---

## Requirement 6 — Develop and Maintain Secure Systems

### What to verify in code:

**Secure development:**
- OWASP Top 10 vulnerabilities addressed (see owasp-top-10-2021.md)
- Input validation on all user inputs
- Output encoding for all dynamic content
- Parameterized queries for database access
- No known vulnerable dependencies

**Code review:**
- Evidence of code review process (PR reviews, approval requirements)
- Security-focused review for payment-related code
- Static analysis in CI pipeline

**Change management:**
- Separate development/test/production environments
- No test data with real PANs
- Production changes require approval

**Detection patterns:**
```
# Check CI/CD for security scanning
sast|dast|sonar|snyk|trivy|bandit|semgrep  → in CI config
# Check for code review enforcement
required.reviewers|CODEOWNERS|branch.protection
# Check for environment separation
env|environment|staging|production  → verify separation
```

**Code-level checks:**
- Run through OWASP Top 10 checks on payment-related code
- Verify CI pipeline includes security scanning
- Check branch protection rules
- Verify no test credentials or test PANs in production code

---

## Requirement 7 — Restrict Access by Business Need to Know

### What to verify in code:

**Access control implementation:**
- Role-based access control (RBAC) implemented
- Cardholder data access restricted to necessary roles
- Default deny on all resources
- Admin functions require elevated privileges

**Detection patterns:**
```
role|permission|RBAC|authorize  → access control model
admin|manager|operator  → role definitions
deny.by.default|default.deny|403  → default behavior
cardholder|payment|card  → access restrictions on these resources
```

**Code-level checks:**
- Verify RBAC model exists and is enforced
- Check that cardholder data endpoints require specific roles
- Verify default deny behavior
- Audit admin endpoints for proper authorization

---

## Requirement 8 — Identify and Authenticate Access

### What to verify in code:

**Authentication strength:**
- MFA for administrative access
- MFA for all remote access to cardholder data environment
- Passwords: minimum 12 characters (PCI DSS v4.0), complexity enforced
- Account lockout after max 10 failed attempts within 30 minutes
- Session timeout after 15 minutes of inactivity

**Credential management:**
- No shared/generic accounts in application code
- No hardcoded credentials
- Secure password storage (bcrypt, Argon2, scrypt, PBKDF2)

**Detection patterns:**
```
min.length|MIN_PASSWORD|password.policy  → check >= 12
lockout|max.attempts|failed.login|MAX_FAILED  → check <= 10
session.*timeout|SESSION_TIMEOUT|idle.*timeout  → check <= 15 min
mfa|MFA|two.factor|2fa|totp|webauthn  → MFA implementation
bcrypt|argon2|scrypt|pbkdf2  → password hashing
shared.account|generic.user|service.account  → no shared credentials
```

**Code-level checks:**
- Verify password policy meets PCI requirements
- Check account lockout implementation
- Verify session timeout configuration (15 minutes)
- Confirm MFA on admin interfaces
- Search for hardcoded credentials

---

## Requirement 10 — Track and Monitor All Access

### What to verify in code:

**Audit logging:**
- Log all access to cardholder data
- Log all actions by admin/root accounts
- Log all authentication events (success and failure)
- Log all access control failures
- Log creation/deletion of system objects

**Log content (for each event):**
- User ID
- Event type
- Date/time
- Success/failure
- Origination (IP, source)
- Affected resource/data

**Log protection:**
- Logs cannot be modified by application
- Log data is not in plaintext PAN
- Centralized log collection
- Log retention: at least 12 months, 3 months immediately accessible

**Detection patterns:**
```
audit.log|access.log|security.log  → logging implementation
log.*(user|event|action|timestamp|ip|source)  → log content
log.*(card|pan|credit)  → sensitive data in logs (BAD)
immutable|append.only|write.once  → log protection
retention|rotate|archive  → log retention
```

**Code-level checks:**
- Verify audit logging on cardholder data access endpoints
- Check log format includes required fields (user, event, time, result, source)
- Search logs for PAN/sensitive data leakage
- Verify log storage configuration (retention, protection)
- Check that log deletion/modification is not possible through the application

---

## Requirement 11 — Test Security of Systems and Networks Regularly

### What to verify in code:

**Automated testing:**
- Vulnerability scanning in CI/CD pipeline
- Dependency scanning for known CVEs
- SAST (Static Application Security Testing) configured
- DAST (Dynamic Application Security Testing) for web applications

**Detection patterns:**
```
# In CI/CD configuration files
snyk|trivy|dependabot|renovate  → dependency scanning
sonarqube|semgrep|bandit|brakeman|eslint-security  → SAST
zap|burp|nikto|nuclei  → DAST
pentest|penetration.test  → documented testing
```

**Code-level checks:**
- Verify CI pipeline includes security scanning stages
- Check that scanning results block deployment on critical findings
- Verify dependency scanning is automated and current
- Check for security test cases in test suite

---

## Quick Reference: PCI DSS Code Audit Checklist

| Area | What to Search | Expected Finding |
|------|---------------|-----------------|
| PAN storage | `card_number`, `pan`, field-level encryption | Encrypted with AES-256 |
| PAN display | Rendering functions for card data | Masked: first 6 / last 4 only |
| PAN in logs | `log.*card`, `print.*pan` | No PAN in logs |
| TLS | `http://`, TLS config | TLS 1.2+ enforced |
| Passwords | Password policy config | >= 12 chars, complexity |
| Lockout | Failed login handling | Lockout after <= 10 failures |
| Session | Session timeout config | <= 15 min idle timeout |
| MFA | TOTP/WebAuthn implementation | Present on admin access |
| Audit logs | Logging middleware/interceptors | All access logged with required fields |
| SAST/DAST | CI/CD pipeline config | Security scanning present |
| Dependencies | Lockfiles, scanning config | Scanned, no known critical CVEs |
