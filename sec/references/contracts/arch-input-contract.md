# Arch Input Contract

How the Sec skill reads the four Arch artifacts and turns each field into a security-analysis directive. Read this before the `threat-model` stage when you need to know what a specific Arch field means for security.

## Location and readiness

- Arch artifacts live in `./artifacts/arch/` (override with `HARNESS_ARTIFACTS_DIR`, which points at the parent `artifacts/` directory).
- The four sections must all be present:
  - `ARCH-DEC-*` — architecture decisions
  - `ARCH-COMP-*` — component structure
  - `ARCH-TECH-*` — technology stack
  - `ARCH-DIAG-*` — diagrams
- Every one must be in phase `approved`. If any is in `draft` / `in_review` / `revising`, stop and tell the user — Sec must not run on unstable input.

Use `python ${SKILL_DIR}/../arch/scripts/artifact.py list` (or read the metadata files directly) to confirm readiness.

## ARCH-DEC-* → security implications

| Arch field | Sec action |
|------------|------------|
| `id` | Recorded in threat model's `arch_refs` whenever a decision introduces a security-relevant surface |
| `decision` | Map the architectural style to its threat profile (see table below) |
| `rationale` | Review for security reasoning — absence of security rationale is itself a finding |
| `trade_offs` | Identify where security was explicitly sacrificed for another quality; each such trade-off becomes a threat candidate |
| `alternatives_considered` | Check whether a more secure alternative was rejected; if so, record the risk acceptance |
| `re_refs` | Propagated into `SEC-TM-*.re_refs` so downstream skills can trace threats back to requirements |

**Decision-to-threat mapping**:

| Architecture style | Key threats to model |
|-------------------|---------------------|
| Microservices | Inter-service authentication, service impersonation, network-level eavesdropping, distributed secret management |
| Event-driven | Message integrity and authenticity, replay attacks, event ordering manipulation, dead-letter queue poisoning |
| Monolith | Privilege escalation within process, single point of compromise, shared-memory data leakage |
| Serverless | Cold-start injection, function-level over-permissioning, ephemeral storage data remnants |
| CQRS | Write-side authorization bypass, read-model data leakage, eventual consistency race conditions |

## ARCH-COMP-* → trust boundaries and attack surface

| Arch field | Sec action |
|------------|------------|
| `id` | Recorded as `affected_components` on threat model entries |
| `name` | Human-readable label in threat descriptions and DFD |
| `type` | Determines trust boundary classification (see table below) |
| `responsibility` | Review for security-sensitive operations (auth, payment, PII handling) |
| `interfaces` | Each interface is an attack surface entry point; enumerate input vectors |
| `dependencies` | Map data flow paths to identify privilege propagation and lateral movement opportunities |
| `re_refs` | Propagated so threats trace back to the requirements they endanger |

**Component type to trust boundary**:

| Component type | Trust boundary | Security treatment |
|---------------|----------------|-------------------|
| `gateway` / `edge` | External boundary | Full input validation, rate limiting, WAF rules, authentication enforcement |
| `service` | Internal boundary | Service-to-service auth (mTLS / JWT), least-privilege access, input sanitization |
| `store` / `database` | Data boundary | Encryption at rest, access control, query parameterization, audit logging |
| `worker` / `queue` | Processing boundary | Message validation, idempotency checks, poison-message handling |
| `library` | Code boundary | Dependency scanning, API misuse detection, transitive dependency audit |

## ARCH-TECH-* → known vulnerability patterns

| Arch field | Sec action |
|------------|------------|
| `category` | Determines which vulnerability databases to query (language CVEs, framework advisories, runtime patches) |
| `choice` | Map to known vulnerability patterns for the specific technology (see table below) |
| `rationale` | Check for security-driven selection criteria |
| `decision_ref` | Inherit security constraints from the referenced ADR |
| `constraint_ref` | `hard` constraints with regulatory implications (PCI, HIPAA, GDPR) trigger compliance-report entries |

**Technology to vulnerability pattern mapping** (representative, not exhaustive):

| Technology | Known vulnerability patterns |
|-----------|------------------------------|
| Express.js | Prototype pollution, ReDoS in middleware, header injection, missing CSRF by default |
| Django | CSRF token misconfiguration, ORM injection via `extra()`, template injection, DEBUG mode exposure |
| Spring Boot | SpEL injection, actuator endpoint exposure, deserialization via Jackson, mass assignment |
| React | XSS via `dangerouslySetInnerHTML`, SSR hydration mismatch, dependency chain vulnerabilities |
| PostgreSQL | SQL injection via string concatenation, privilege escalation via functions, pg_dump credential exposure |
| Redis | Unauthenticated access by default, Lua script injection, command injection via EVAL |
| Kafka | Plaintext transport by default, ACL misconfiguration, consumer group hijacking |

Every `ARCH-TECH-*.choice` entry must have a corresponding vulnerability scan target in the vulnerability report.

## ARCH-DIAG-* → system boundaries and data flows

| Diagram type | Sec action |
|-------------|------------|
| `c4-context` | Identify all external actors and system boundaries; each external actor is a potential threat source in the DFD |
| `c4-container` | Map containers to trust boundaries; every boundary crossing requires an authentication/authorization check |
| `sequence` | Verify auth/authz at every step; identify where tokens are passed, validated, or absent |
| `data-flow` | Trace sensitive data paths end-to-end; every hop must have encryption-in-transit and access control |

**DFD construction from diagrams**:

1. Extract external actors from `c4-context` — these become external entities in the DFD.
2. Extract containers from `c4-container` — these become processes in the DFD.
3. Extract data stores from component structure — these become data stores in the DFD.
4. Extract data flows from `data-flow` diagrams — these become data flows in the DFD.
5. Overlay trust boundaries from the component-type mapping above.
6. Apply STRIDE to every element in the DFD.

## Traceability propagation

Every threat model entry must link upstream to the Arch artifact that surfaced the threat:

```
python ${SKILL_DIR}/scripts/artifact.py link <sec-tm-id> --upstream ARCH-COMP-001
```

Every vulnerability report entry that stems from a technology choice must link to the tech-stack entry:

```
python ${SKILL_DIR}/scripts/artifact.py link <sec-va-id> --upstream ARCH-TECH-003
```

## When Arch is insecure

If an architecture decision is fundamentally insecure (e.g., no authentication on an external-facing gateway, PII stored in plaintext with no encryption plan, hard regulatory constraint violated), **do not** patch around it inside Sec. Escalate to the user following the [escalation protocol](../escalation-protocol.md) and recommend they re-open Arch. Arch is the source of truth for structure; Sec identifies the risks, but structural fixes belong in Arch.
