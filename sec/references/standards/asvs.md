# OWASP ASVS — Application Security Verification Standard

Reference for verifying application security across three assurance levels.

---

## Verification Levels

| Level | Name | Use Case |
|-------|------|----------|
| **L1** | Opportunistic | All software. Minimum baseline. Defends against easily exploitable vulnerabilities. |
| **L2** | Standard | Applications handling sensitive data (PII, business data, health). Most applications should target L2. |
| **L3** | Advanced | High-value applications — financial, healthcare, critical infrastructure, military. Requires defense-in-depth and formal verification. |

---

## V1 — Architecture, Design, and Threat Modeling

**What to verify:**
- Security architecture documentation exists
- Threat model is current and covers all components
- All data flows are documented with trust boundaries
- Components follow principle of least privilege

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Threat model exists | - | Y | Y | Look for threat model docs, STRIDE analysis |
| Security architecture documented | - | Y | Y | Check for architecture decision records |
| All components have defined security controls | - | - | Y | Each service has auth, authz, logging defined |

**Code-level checks:** Look for architecture docs in repo. Verify security middleware is applied consistently. Check that trust boundaries are enforced (auth at API gateway, between microservices).

---

## V2 — Authentication

**What to verify:**
- Password strength policies enforced
- Credential storage uses approved algorithms
- MFA available/enforced for sensitive operations
- Brute-force protection implemented

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Passwords >= 8 chars min | Y | Y | Y | Check password validation logic |
| Passwords >= 64 chars max allowed | Y | Y | Y | Check max length is not too restrictive |
| Passwords hashed with bcrypt/scrypt/Argon2 | Y | Y | Y | Search for password hashing functions |
| MFA available | - | Y | Y | Check for TOTP/WebAuthn implementation |
| Account lockout after failures | Y | Y | Y | Search for failed login counting |
| Credential recovery is secure | Y | Y | Y | Check reset flow for token expiry, rate limits |

**Code-level checks:** Search for `bcrypt|argon2|scrypt|pbkdf2` in password storage. Check password validation regex/rules. Verify failed login attempt tracking. Check MFA enrollment flow.

---

## V3 — Session Management

**What to verify:**
- Session tokens are cryptographically random
- Sessions expire after inactivity
- Sessions are invalidated on logout
- Session IDs regenerated after authentication

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Session tokens >= 128 bits entropy | Y | Y | Y | Check session token generation |
| Session timeout configured | Y | Y | Y | Search for session timeout/expiry settings |
| Logout invalidates session server-side | Y | Y | Y | Check logout handler |
| Session regenerated on auth | Y | Y | Y | Search for session regeneration post-login |
| Tokens not in URL params | Y | Y | Y | Check for session ID in query strings |
| Cookie flags set (Secure, HttpOnly, SameSite) | Y | Y | Y | Check cookie configuration |

**Code-level checks:** Verify session config (timeout, cookie flags). Check logout invalidates server-side session. Search for `session.regenerate|new_session|rotate` after login.

---

## V4 — Access Control

**What to verify:**
- Principle of least privilege applied
- Access denied by default
- Consistent authorization mechanism
- Vertical and horizontal access controls

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Deny by default | Y | Y | Y | Check default route/handler behavior |
| Authorization on every request | Y | Y | Y | Verify middleware/decorator presence |
| RBAC or equivalent implemented | - | Y | Y | Check role/permission model |
| Ownership verified for data access | Y | Y | Y | Check IDOR protections |
| Admin functions separated | - | Y | Y | Check admin routes have elevated auth |
| Rate limiting on sensitive endpoints | - | Y | Y | Check rate limiter configuration |

**Code-level checks:** Audit all route handlers for authorization decorators/middleware. Check that resource access includes ownership verification. Verify admin endpoints require elevated roles.

---

## V5 — Validation, Sanitization, and Encoding

**What to verify:**
- All input validated server-side
- Output properly encoded for context
- Parameterized queries for all database access
- File uploads validated

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Server-side input validation | Y | Y | Y | Check request handlers validate input |
| Parameterized queries | Y | Y | Y | Search for string concat in SQL |
| Output encoding for HTML context | Y | Y | Y | Check template auto-escaping |
| HTTP response Content-Type set | Y | Y | Y | Check response headers |
| File upload validation | Y | Y | Y | Check type, size, name validation |
| No eval/exec on user input | Y | Y | Y | Search for eval/exec usage |

**Code-level checks:** Search for SQL string concatenation. Verify template engines have auto-escaping enabled. Check all `eval`/`exec` calls. Verify file upload handlers validate type and size.

---

## V7 — Error Handling and Logging

**What to verify:**
- Generic error messages for users
- Detailed errors only in logs
- Security events are logged
- No sensitive data in logs

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Generic error responses | Y | Y | Y | Check error handlers don't leak stack traces |
| Security events logged | - | Y | Y | Check auth failures, authz failures logged |
| No sensitive data in logs | Y | Y | Y | Search for password/token in log statements |
| Log injection prevented | - | Y | Y | Check log statements sanitize user input |
| Centralized logging | - | - | Y | Check logging infrastructure |

**Code-level checks:** Check error handlers for stack trace exposure. Search log statements for sensitive data. Verify auth events (login, failure, lockout) are logged.

---

## V8 — Data Protection

**What to verify:**
- Data classification exists
- PII is identified and protected
- Sensitive data encrypted at rest
- Data minimization applied

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Sensitive data identified | - | Y | Y | Check data model for PII/sensitive fields |
| Encryption at rest for sensitive data | - | Y | Y | Check database encryption, field-level encryption |
| No sensitive data in URL params | Y | Y | Y | Check query string usage |
| Cache-Control on sensitive responses | Y | Y | Y | Check response headers |
| Data minimization in API responses | - | Y | Y | Check for SELECT * or excess fields returned |
| Backup encryption | - | - | Y | Check backup configuration |

**Code-level checks:** Identify PII fields in data models. Check encryption configuration. Verify API responses don't return excess fields. Check cache headers on sensitive endpoints.

---

## V9 — Communication Security

**What to verify:**
- TLS 1.2+ on all connections
- Certificate validation enabled
- HSTS configured
- No mixed content

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| TLS on all connections | Y | Y | Y | Search for http:// URLs, check config |
| Strong TLS configuration | - | Y | Y | Check cipher suites, protocol versions |
| Certificate validation enabled | Y | Y | Y | Search for verify=False, VERIFY_SSL=false |
| HSTS header set | - | Y | Y | Check response headers |
| Certificate pinning | - | - | Y | Check mobile/API client TLS config |

**Code-level checks:** Search for `http://` in API URLs. Search for disabled certificate verification. Check HSTS header configuration. Verify TLS version in server config.

---

## V10 — Malicious Code

**What to verify:**
- Dependencies are from trusted sources
- Integrity checks on dependencies
- No backdoors or time bombs
- Subresource integrity for CDN resources

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Dependency integrity verified | Y | Y | Y | Check lockfiles exist with hashes |
| No known vulnerable dependencies | Y | Y | Y | Check for dependency scanning in CI |
| SRI for CDN resources | - | Y | Y | Check integrity attributes on script/link tags |
| No obfuscated code | - | - | Y | Check for intentionally obscured code |

**Code-level checks:** Verify lockfiles exist. Check CI for dependency scanning step. Search HTML for CDN resources without integrity attributes.

---

## V11 — Business Logic

**What to verify:**
- Business rules enforced server-side
- Anti-automation for sensitive flows
- Rate limiting on business operations
- Transaction limits enforced

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Business logic server-side | Y | Y | Y | Check that rules aren't only client-side |
| Anti-automation (CAPTCHA, rate limit) | - | Y | Y | Check registration, purchase, contact flows |
| Rate limiting | - | Y | Y | Check rate limiter on API endpoints |
| Abuse detection | - | - | Y | Check for anomaly detection logic |

**Code-level checks:** Verify pricing/discount logic is server-side. Check for rate limiting middleware. Verify multi-step flows can't be skipped.

---

## V12 — Files and Resources

**What to verify:**
- Upload validation (type, size, content)
- Files stored outside web root
- Antivirus scanning for uploads
- No path traversal

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| File type validation | Y | Y | Y | Check upload handlers |
| File size limits | Y | Y | Y | Check upload configuration |
| Files stored outside web root | Y | Y | Y | Check storage path |
| Path traversal prevented | Y | Y | Y | Check filename sanitization |
| Antivirus on uploads | - | - | Y | Check scanning integration |

**Code-level checks:** Check file upload handlers for type/size validation. Verify filename sanitization (strip `../`, special chars). Check storage location configuration.

---

## V13 — API Security

**What to verify:**
- Authentication on all API endpoints
- Input validation and schema enforcement
- Rate limiting
- Proper HTTP methods and status codes

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| API authentication required | Y | Y | Y | Check all API routes for auth |
| Schema validation on input | - | Y | Y | Check request validation (JSON schema, etc.) |
| Rate limiting per client | - | Y | Y | Check rate limiter config |
| GraphQL depth/complexity limits | - | Y | Y | Check GraphQL config if applicable |
| API versioning | - | Y | Y | Check URL or header versioning |
| Mass assignment prevention | Y | Y | Y | Check allowlists for writable fields |

**Code-level checks:** Audit API routes for auth. Check request body validation. For GraphQL: check query depth limits, complexity limits, introspection disabled in production.

---

## V14 — Configuration

**What to verify:**
- Security headers configured
- Debug mode disabled in production
- Default credentials removed
- Error pages don't leak information

| Req | L1 | L2 | L3 | Check |
|-----|----|----|-----|-------|
| Security headers set (CSP, HSTS, X-Frame-Options) | Y | Y | Y | Check response header config |
| Debug mode off in production | Y | Y | Y | Search for DEBUG=True |
| Default credentials removed | Y | Y | Y | Search for admin/admin, default passwords |
| Server version headers removed | - | Y | Y | Check Server, X-Powered-By headers |
| CORS properly configured | Y | Y | Y | Check Access-Control-Allow-Origin |
| CSP prevents inline scripts | - | Y | Y | Check CSP policy |

**Code-level checks:** Check security header middleware/configuration. Search for debug flags. Verify CORS configuration restricts origins. Check CSP for `unsafe-inline`.
