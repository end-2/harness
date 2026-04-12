# SEC-TM-001 — Threat Model (Bookmark API, light mode)

**Phase**: approved · **Mode**: light

## Mode and Scope

Light mode, inherited from Arch. Two components, one external interface, single service, no PII beyond email, no regulatory constraints. Full STRIDE with DREAD scoring would be disproportionate.

## Trust Boundaries

| Boundary ID | Name | From | To | Classification |
|-------------|------|------|----|----------------|
| TB-001 | External boundary | User (internet) | ARCH-COMP-001-api | untrusted → trusted |
| TB-002 | Data boundary | ARCH-COMP-001-api | ARCH-COMP-001-db | trusted → data store |

## STRIDE — Top Threats

| Threat ID | Category | Component / Flow | Description | Risk | Mitigation |
|-----------|----------|------------------|-------------|------|------------|
| TM-001 | Spoofing | TB-001 (external) | Attacker forges or steals JWT to impersonate a user | high | Validate JWT signature, pin algorithm to RS256/HS256, enforce expiry, rotate secrets |
| TM-002 | Injection | TB-002 (data) | SQL injection via unsanitised input in bookmark CRUD | high | Use parameterised queries exclusively (pg library supports this natively) |
| TM-003 | Info Disclosure | ARCH-COMP-001-api | Verbose error responses leak stack traces or DB schema | medium | Use helmet for headers, return generic error bodies in production, log details server-side only |
| TM-004 | Elevation of Privilege | ARCH-COMP-001-api | Missing authz check allows user A to read/modify user B's bookmarks | high | Enforce ownership check in repository layer; every query filters by authenticated user ID |

## OWASP Top 10 Checklist

| OWASP ID | Category | Status | Notes |
|----------|----------|--------|-------|
| A01 | Broken Access Control | needs verification | TM-004: confirm per-user scoping in all CRUD endpoints |
| A02 | Cryptographic Failures | ok | JWT with HS256, HTTPS enforced (RE-CON-001) |
| A03 | Injection | needs verification | TM-002: confirm parameterised queries in `src/db/` |
| A05 | Security Misconfiguration | ok | helmet middleware active, `.env` for secrets |
| A07 | Identity & Auth Failures | needs verification | TM-001: confirm JWT validation completeness |
| A09 | Security Logging & Monitoring | needs verification | confirm error logging does not include tokens or credentials |

Items not listed (A04, A06, A08, A10) are not applicable given the current architecture scope.

## Inline Security Notes

- **JWT secret management**: `dotenv` loads the signing secret from `.env`. Confirm `.env` is in `.gitignore` and the secret is not hardcoded in source.
- **Dependency posture**: `jsonwebtoken@9.0.2` has no known CVEs as of assessment date. `pg@8.11.3` is current. Monitor via `npm audit`.
- **Rate limiting**: not present in current Impl artifacts. Recommend adding `express-rate-limit` middleware to mitigate brute-force on `/auth`.

## Upstream Refs

- ARCH-COMP-001, ARCH-DEC-001, ARCH-TECH-001
- IMPL-MAP-001, IMPL-CODE-001, IMPL-IDR-001
- RE-CON-001, RE-QA-001
