# SEC-CR-001 — Compliance Report (E-Commerce Platform, heavy mode)

**Phase**: approved · **Mode**: heavy

## Summary

Partial OWASP ASVS L2 compliance assessment. 10 representative requirements checked across 4 ASVS chapters. Overall: 5 compliant, 4 non-compliant, 1 not applicable. Applicable standards driven by RE constraints: GDPR (RE-CON-002), PCI DSS SAQ-A (RE-CON-003).

## OWASP ASVS L2 — Selected Requirements

| # | ASVS Req ID | Chapter | Requirement | Status | Evidence | Gap |
|---|-------------|---------|-------------|--------|----------|-----|
| 1 | V2.1.1 | V2: Authentication | User passwords are at least 12 characters | compliant | Auth service enforces 12-char minimum via Pydantic validator (`services/auth/internal/models/user.go:34`) | — |
| 2 | V2.5.4 | V2: Authentication | Password storage uses bcrypt/scrypt/argon2 with appropriate cost | compliant | Auth service uses `golang.org/x/crypto/bcrypt` with cost=12 (`services/auth/internal/auth/password.go:18`) | — |
| 3 | V2.8.1 | V2: Authentication | Time-based OTP or equivalent MFA is available | non_compliant | No MFA implementation found in auth service. Only password-based authentication. | MFA not implemented. Required for admin users at minimum under ASVS L2. |
| 4 | V3.5.2 | V3: Session | JWT tokens validated for signature, expiry, and issuer | compliant | Auth middleware validates signature (HS256), expiry, and issuer claim (`services/auth/internal/middleware/jwt.go:22-45`) | — |
| 5 | V4.1.2 | V4: Access Control | Access controls enforced at server side on every request | non_compliant | Order service endpoints `/orders/{id}` do not verify resource ownership — user A can access user B's orders (TM-013, VA-001 related) | Missing ownership check in `order_repo.py:47`. IDOR vulnerability confirmed. |
| 6 | V5.3.4 | V5: Validation | Output encoding applied to prevent XSS | non_compliant | Kong error handler reflects request path without HTML encoding (VA-002) | XSS in error page. Error responses should use JSON format for API. |
| 7 | V5.3.5 | V5: Validation | Parameterised queries used for all database access | non_compliant | Order search uses string interpolation in SQL query (VA-001) | SQL injection via `text(f"...")` pattern. Must use bind parameters. |
| 8 | V9.1.1 | V9: Communications | TLS used for all client-server connections | compliant | Kong terminates TLS 1.3 at the edge. HSTS header not yet configured (SR-004) but TLS enforcement is present. | — |
| 9 | V9.2.1 | V9: Communications | TLS or equivalent used for all internal connections | compliant | Arch specifies mTLS via service mesh. Implementation pending (SR-001) but Helm charts include Istio sidecar annotations. Classified as compliant with conditions. | mTLS deployment must be verified post-rollout. |
| 10 | V14.3.1 | V14: Configuration | No credentials in source code | not_applicable | Hardcoded Stripe key found (VA-003) but classified under PCI DSS scope, not ASVS. Flagged in SR-004 for immediate rotation. | Addressed under PCI DSS below. |

## PCI DSS SAQ-A — Key Checks

The platform uses Stripe as the payment processor (SAQ-A scope: payment data handled by Stripe, only tokens stored locally).

| PCI DSS Req | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| 3.4 | Render PAN unreadable wherever stored | compliant | No raw PAN stored; only Stripe payment tokens in `paydb` with AES-256-at-rest encryption |
| 4.1 | Use strong cryptography for transmission of cardholder data | compliant | All Stripe API calls over TLS 1.2+ (enforced by Stripe SDK) |
| 6.5 | Address common coding vulnerabilities | non_compliant | SQL injection (VA-001) and hardcoded credential (VA-003) demonstrate gaps in secure coding practices |
| 8.1 | Unique ID for each user with computer access | compliant | All admin and service accounts use individual credentials; shared accounts prohibited by IMPL-GUIDE-001 |

## GDPR Article 32 — Technical Measures

| Measure | Status | Evidence |
|---------|--------|----------|
| Encryption of personal data in transit | compliant | TLS 1.3 at edge, mTLS for inter-service (pending deployment) |
| Encryption of personal data at rest | compliant | AES-256-at-rest for all databases containing PII (auth, order, payment) |
| Pseudonymisation | non_compliant | PII stored in plaintext in auth and order databases; no field-level tokenisation |
| Access logging and audit trail | compliant | Structured logging with user ID correlation; payment audit log (TM-006 mitigation) |

## Remediation Roadmap

| Priority | Gap | ASVS / Standard | Remediation | Target |
|----------|-----|-----------------|-------------|--------|
| P0 | Hardcoded Stripe key | PCI DSS 6.5 | Rotate key, migrate to Vault (SR-004) | Immediate |
| P1 | SQL injection | ASVS V5.3.5, PCI DSS 6.5 | Parameterised queries (VA-001 fix) | Week 1 |
| P1 | IDOR / broken access control | ASVS V4.1.2 | Ownership validation in repository (TM-013 mitigation) | Week 1 |
| P1 | XSS in error handler | ASVS V5.3.4 | JSON error responses (VA-002 fix) | Week 1 |
| P2 | No MFA | ASVS V2.8.1 | Implement TOTP for admin users, optional for regular users | Week 3 |
| P2 | PII pseudonymisation | GDPR Art. 32 | Field-level tokenisation for name/email/address in auth and order DBs | Week 4 |
| P3 | HSTS header | ASVS V9.1.1 (enhancement) | Configure Kong HSTS plugin (SR-004) | Week 2 |

## Upstream Refs

- SEC-TM-001 (threat model), SEC-VA-001 (vulnerability report), SEC-SR-001 (security advisory)
- ARCH-COMP-001, ARCH-DEC-001, ARCH-DEC-002
- IMPL-MAP-001, IMPL-MAP-003, IMPL-MAP-004, IMPL-CODE-001, IMPL-GUIDE-001
- RE-CON-001, RE-CON-002, RE-CON-003
