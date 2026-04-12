# Impl Input Contract

How the Sec skill reads the four Impl artifacts and turns each field into a code-level security-analysis directive. Read this after the Arch input contract — Arch gives the structural threat model, Impl gives the code-level attack surface.

## Location and readiness

- Impl artifacts live in `./artifacts/impl/` (override with `HARNESS_ARTIFACTS_DIR`, which points at the parent `artifacts/` directory).
- The four sections must all be present:
  - `IMPL-MAP-*` — implementation map
  - `IMPL-CODE-*` — code structure
  - `IMPL-IDR-*` — implementation decisions
  - `IMPL-GUIDE-*` — implementation guide
- Every one must be in phase `approved`. If any is in `draft` / `in_review` / `revising`, stop and tell the user — Sec must not run on unstable input.

Use `python ${SKILL_DIR}/../impl/scripts/artifact.py list` (or read the metadata files directly) to confirm readiness.

## IMPL-MAP-* → audit file scope and API surface

| Impl field | Sec action |
|------------|------------|
| `id` | Recorded in vulnerability report's `impl_refs` when a code-level issue is found in this module |
| `component_ref` | Maps back to the Arch component's security requirements — every security requirement on `ARCH-COMP-*` must be verified in the corresponding implementation |
| `module_path` | Defines the file scope for the security audit; every file under this path is in scope for code-level review |
| `entry_point` | Priority audit target — the entry point is the first line of defense and must enforce authentication, authorization, and input validation |
| `interfaces_implemented` | Each interface is an API endpoint or service contract; check for: input validation, authentication enforcement, authorization checks, rate limiting, error handling that does not leak internals |
| `internal_structure` | Identify security-sensitive files (auth modules, crypto utilities, configuration loaders, serialization handlers) |
| `arch_refs` | Used to verify that every Arch-level security requirement has a code-level implementation |
| `re_refs` | Used to trace security requirements back to their origin in RE |

**API endpoint security checklist** (applied per `interfaces_implemented` entry):

| Check | Description |
|-------|-------------|
| Authentication | Is the endpoint protected by an auth mechanism? Is the mechanism appropriate (API key, JWT, OAuth2)? |
| Authorization | Does the endpoint check permissions? Is it role-based, attribute-based, or resource-based? |
| Input validation | Are all inputs validated? Schema validation, type checking, length limits, allowed characters? |
| Output encoding | Are outputs encoded to prevent XSS, header injection, or log injection? |
| Rate limiting | Is the endpoint rate-limited? Is the limit appropriate for its sensitivity? |
| Error handling | Do error responses avoid leaking stack traces, internal paths, or database schemas? |

## IMPL-CODE-* → dependency and configuration audit

| Impl field | Sec action |
|------------|------------|
| `project_root` | Root scope for static analysis and dependency scanning |
| `directory_layout` | Identify security-sensitive directories (config/, secrets/, certs/, keys/) that should not exist in the repo |
| `module_dependencies` | Check for privilege boundary violations — a lower-trust module must not import a higher-trust module's internals |
| `external_dependencies` | Primary CVE scan targets (see dependency audit below) |
| `build_config` | Check for secrets in build files, insecure build flags, unsigned artifacts |
| `environment_config` | Secret and credential management audit (see configuration audit below) |

**Dependency audit** (applied per `external_dependencies` entry):

| Check | Description |
|-------|-------------|
| CVE scan | Query NVD/OSV for known vulnerabilities in `{name}@{version}` |
| Version currency | Is the version within one major of latest? End-of-life versions are a finding |
| License risk | Are there copyleft or problematic licenses that conflict with project constraints? |
| Transitive depth | Flag deeply-nested transitive dependencies (supply chain risk) |
| Pinning | Version must be pinned (exact or range with upper bound); unpinned is a finding |

Every dependency finding is recorded as a `dependency_vuln` entry in the vulnerability report with `package`, `version`, `cve_id`, and `fixed_version`.

**Configuration audit** (applied per `environment_config` entry):

| Secret management method | Risk level | Sec action |
|--------------------------|-----------|------------|
| Hardcoded in source | Critical | Immediate finding — must remediate |
| `.env` file (not in `.gitignore`) | High | Finding — file must be gitignored and rotated |
| `.env` file (gitignored) | Medium | Advisory — recommend secret manager for production |
| Environment variable (runtime) | Low | Acceptable for non-production; advisory for production |
| Secret manager (Vault, AWS SM, GCP SM) | Acceptable | Verify access control and rotation policy |

## IMPL-IDR-* → pattern-specific security checks

| Impl field | Sec action |
|------------|------------|
| `id` | Recorded in security advisory's `impl_refs` when a pattern choice has security implications |
| `title` / `decision` | Review the decision text for security-relevant choices (token storage, serialization, input validation strategy) |
| `rationale` | Check whether security was considered in the rationale; absence is an advisory |
| `alternatives_considered` | Check whether more secure alternatives were rejected; if so, record the risk |
| `pattern_applied` | Apply pattern-specific security checks (see table below) |
| `arch_refs` | Trace back to the Arch decision to verify security intent is preserved in implementation |

**Pattern to security check mapping**:

| Pattern | Security checks |
|---------|----------------|
| Repository | SQL injection via dynamic queries, ORM misconfiguration, mass assignment, unparameterized queries |
| Strategy | Privilege check on strategy swap — can an attacker select a weaker strategy? Input-driven strategy selection must validate the input |
| Factory | Object creation injection, untrusted input in factory selection, resource exhaustion via unbounded creation |
| Observer / Event | Event spoofing, unauthorized subscription, information leakage via event payloads, replay attacks |
| Decorator | Decorator bypass (can the unwrapped object be accessed directly?), ordering-dependent security checks |
| Middleware / Pipeline | Middleware ordering (auth before business logic), short-circuit bypass, error-handling gaps between stages |
| Singleton | Thread-safety of shared state, credential caching lifetime, stale security context |

## IMPL-GUIDE-* → operational security review

| Impl field | Sec action |
|------------|------------|
| `prerequisites` | Check runtime versions for known vulnerabilities; flag end-of-life runtimes |
| `setup_steps` | Review for insecure setup actions (disabling TLS verification, running as root, chmod 777) |
| `build_commands` | Identify build pipeline security points: dependency installation (lockfile integrity), compilation flags (stack protection, ASLR), artifact signing |
| `run_commands` | Check for insecure runtime flags (debug mode, verbose logging with secrets, disabled security features) |
| `conventions` | Review error-handling convention for information leakage, logging convention for PII/secret exposure |
| `extension_points` | Each extension point is a potential injection vector; verify that extensions are sandboxed or validated |

## Traceability propagation

Every vulnerability report entry must link upstream to the Impl artifact where the vulnerability was found:

```
python ${SKILL_DIR}/scripts/artifact.py link <sec-va-id> --upstream IMPL-CODE-001
```

Every security advisory that recommends a code change must link to the relevant IDR:

```
python ${SKILL_DIR}/scripts/artifact.py link <sec-sr-id> --upstream IMPL-IDR-003
```

## When Impl is insecure

If an implementation decision is fundamentally insecure (e.g., credentials hardcoded in source, authentication disabled for convenience, known-vulnerable dependency with no upgrade path), escalate to the user following the [escalation protocol](../escalation-protocol.md). Code-level fixes belong in Impl; Sec identifies the risks and provides remediation guidance.
