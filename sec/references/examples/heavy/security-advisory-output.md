# SEC-SR-001 — Security Advisory (E-Commerce Platform, heavy mode)

**Phase**: approved · **Mode**: heavy

## Summary

4 prioritised advisories synthesising findings from the threat model (SEC-TM-001) and vulnerability report (SEC-VA-001). Ordered by risk impact: architecture-level first, then code, dependency, and configuration.

## Advisories

### SR-001 — Missing Service Mesh mTLS Enforcement (Architecture)

| Field | Value |
|-------|-------|
| **Priority** | P1 — Critical |
| **Category** | Architecture |
| **Threat refs** | TM-003, TM-012 |
| **Vuln refs** | — |
| **Components** | All inter-service communication (ARCH-COMP-001-auth, order, payment, notif) |
| **Compliance** | PCI DSS 4.1 (encrypt cardholder data in transit), GDPR Art. 32 (appropriate technical measures) |

**Finding**: The Arch decision (ARCH-DEC-001) specifies Kubernetes with a service mesh, but the Impl artifacts show no mTLS configuration in the Helm charts or service definitions. Inter-service gRPC calls currently use plaintext. A compromised pod could intercept or spoof traffic across services, directly enabling TM-003 (service spoofing) and facilitating TM-012 (privilege escalation via lateral movement).

**Recommendation**:
1. Deploy Istio/Linkerd with `STRICT` mTLS mode for the namespace
2. Add `PeerAuthentication` policy requiring mTLS for all services
3. Configure `AuthorizationPolicy` to restrict which services can call which endpoints
4. Verify with `istioctl analyze` and network policy tests in CI

**Effort estimate**: 2-3 days for service mesh setup, 1 day for policy configuration, 1 day for CI integration.

---

### SR-002 — Input Validation Gaps Across Services (Code)

| Field | Value |
|-------|-------|
| **Priority** | P1 — Critical |
| **Category** | Code |
| **Threat refs** | TM-004, TM-013 |
| **Vuln refs** | VA-001, VA-002 |
| **Components** | ARCH-COMP-001-order, ARCH-COMP-001-gw |
| **Compliance** | OWASP ASVS V5 (Validation, Sanitization and Encoding) |

**Finding**: Two distinct input validation failures: (1) SQL injection in order search (VA-001, CVSS 9.8) via string interpolation instead of parameterised queries, and (2) reflected XSS in error handler (VA-002, CVSS 6.1) via unescaped path rendering. Both stem from missing input sanitisation at the boundary where user data enters the system.

**Recommendation**:
1. **Immediate**: Fix VA-001 by replacing string interpolation with bind parameters (see VA-001 remediation)
2. **Immediate**: Fix VA-002 by switching error responses to JSON format (see VA-002 remediation)
3. **Systematic**: Adopt Pydantic input models for all FastAPI endpoints with strict type validation
4. **Preventive**: Add `bandit` (Python) and `gosec` (Go) to CI pipeline to catch injection patterns
5. **Verification**: Add IDOR-specific integration tests for all CRUD endpoints (TM-013 mitigation)

**Effort estimate**: 1 day for immediate fixes, 2-3 days for systematic Pydantic adoption, 1 day for CI tooling.

---

### SR-003 — Outdated SQLAlchemy with Known CVE (Dependency)

| Field | Value |
|-------|-------|
| **Priority** | P2 — High |
| **Category** | Dependency |
| **Threat refs** | — |
| **Vuln refs** | VA-004 |
| **Components** | ARCH-COMP-001-order, ARCH-COMP-001-notif |
| **Compliance** | OWASP ASVS V14.2 (Dependency) |

**Finding**: `sqlalchemy==2.0.25` in two services has a known CVE (query cache poisoning, CVSS 7.5). While the vulnerable `baked_query` feature is not directly used in the current codebase, the dependency should be upgraded as a defence-in-depth measure. Additionally, no automated dependency scanning is configured in CI.

**Recommendation**:
1. Upgrade `sqlalchemy>=2.0.27` in `services/order/requirements.txt` and `services/notification/requirements.txt`
2. Run existing test suites to verify compatibility
3. Add `pip-audit` (Python) and `govulncheck` (Go) to CI pipeline for automated CVE scanning
4. Configure Dependabot or Renovate for automated dependency update PRs

**Effort estimate**: 0.5 day for upgrade + test, 1 day for CI dependency scanning setup.

---

### SR-004 — Missing Security Headers and Hardcoded Secret (Configuration)

| Field | Value |
|-------|-------|
| **Priority** | P1 — Critical (hardcoded secret), P2 — High (headers) |
| **Category** | Configuration |
| **Threat refs** | TM-001, TM-007 |
| **Vuln refs** | VA-003 |
| **Components** | ARCH-COMP-001-payment, ARCH-COMP-001-gw |
| **Compliance** | PCI DSS 6.5 (secure coding), OWASP ASVS V14.4 (HTTP Security Headers) |

**Finding**: Two configuration issues: (1) Stripe secret key hardcoded in source (VA-003, CVSS 7.5) — this is a live production credential with full Stripe API access; (2) Kong gateway does not set `Strict-Transport-Security`, `Content-Security-Policy`, or `X-Content-Type-Options` headers, leaving users exposed to downgrade attacks and content injection.

**Recommendation**:
1. **Emergency**: Rotate the Stripe key immediately via Stripe dashboard, audit Stripe logs for unauthorised charges
2. **Immediate**: Move secret to Kubernetes Secret / HashiCorp Vault, load via environment variable
3. **Immediate**: Add pre-commit hook with `detect-secrets` to prevent future credential commits
4. **Short-term**: Configure Kong security headers plugin:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `Content-Security-Policy: default-src 'self'`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
5. **Verification**: Add header assertion tests to integration suite

**Effort estimate**: 1 hour for key rotation (emergency), 1 day for secret management migration, 0.5 day for header configuration.

## Prioritised Action Summary

| Priority | Advisory | Action | Owner |
|----------|----------|--------|-------|
| P0 (emergency) | SR-004 | Rotate exposed Stripe key | Payment team |
| P1 | SR-001 | Deploy mTLS across service mesh | Platform team |
| P1 | SR-002 | Fix SQL injection and XSS | Order team / Gateway team |
| P1 | SR-004 | Migrate secrets to Vault, add security headers | Platform team |
| P2 | SR-003 | Upgrade SQLAlchemy, add dependency scanning | Order team / Notification team |

## Upstream Refs

- SEC-TM-001 (threat model), SEC-VA-001 (vulnerability report)
- ARCH-COMP-001, ARCH-DEC-001, ARCH-DEC-002
- IMPL-MAP-001, IMPL-MAP-003, IMPL-MAP-004, IMPL-CODE-001
- RE-CON-002, RE-CON-003
