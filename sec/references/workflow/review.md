# Workflow — Stage 3: Security Code Review Stage — Detailed Rules

## Role

Perform deep review of security logic correctness, verifying that threat model mitigations are actually implemented in code and that authentication, authorization, input validation, cryptographic, and error handling logic is correct. This stage goes beyond the pattern-matching of Stage 2 (audit) to assess whether the security controls are logically sound and complete.

## Inputs

- **`SEC-TM-*`** (from Stage 1) — The threat model with mitigations. Every `TM-xxx` mitigation must be verified against code.
- **`SEC-VA-*`** (from Stage 2) — The vulnerability report. Review findings inform where to focus deep review.
- **`IMPL-MAP-*`** — Module paths for locating implementation code.
- **`IMPL-CODE-*`** — Code structure, dependencies, and environment config.
- **`IMPL-IDR-*`** — Implementation decisions and applied patterns.
- **`IMPL-GUIDE-*`** — Conventions, framework choices, and run commands.
- **`ARCH-COMP-*`** — Component interfaces and dependencies for understanding the intended security boundaries.
- **`ARCH-DEC-*`** — Architecture decisions for understanding intended security properties.

## Threat model mitigation verification

For each threat mitigation in `SEC-TM-*`, verify that the code implements it correctly. This is the primary purpose of this stage.

### Verification procedure

1. Read the mitigation description from the threat model (e.g. `TM-001: Spoofing → JWT verification`).
2. Locate the implementation code using `IMPL-MAP-*` module paths and `IMPL-CODE-*` structure.
3. Verify the implementation against the specific criteria below.
4. Record the verification result: `implemented` (correct), `partial` (present but incomplete), `incorrect` (present but flawed), `missing` (not found in code).

### Common mitigation verification criteria

**JWT verification**:
- Algorithm pinning: the code explicitly specifies allowed algorithms (no `alg: none` or algorithm confusion).
- Expiry check: `exp` claim is validated and expired tokens are rejected.
- Signature verification: the signature is verified against the expected key (not skipped or ignored).
- Issuer/audience validation: `iss` and `aud` claims are checked against expected values.
- Key management: signing keys are not hardcoded, are loaded from secure storage.

**Data encryption at rest**:
- Algorithm choice: AES-256-GCM or AES-256-CBC with HMAC (not AES-128, not ECB mode).
- Key management: encryption keys are not in source code, are loaded from a key management service or secure config.
- Scope coverage: all data fields classified as sensitive in the threat model are encrypted.
- Key rotation: mechanism exists for rotating encryption keys without data loss.

**Data encryption in transit**:
- TLS configuration: minimum TLS 1.2, strong cipher suites, no fallback to plaintext.
- Certificate validation: outbound connections verify server certificates (no `verify=False`).
- Mutual TLS: if specified in the mitigation, both client and server certificates are verified.

**Rate limiting**:
- Implementation presence: rate limiting middleware or decorator is applied to the specified endpoints.
- Configuration adequacy: limits are reasonable for the endpoint type (e.g. login: 5 attempts/minute, API: 100 requests/minute).
- Bypass resistance: rate limiting is applied before authentication (not after), uses IP + user identifier, handles distributed requests.

**Input validation**:
- Validation presence: all user inputs specified in the mitigation are validated.
- Validation approach: allowlist (whitelist) preferred over denylist (blacklist).
- Validation location: server-side validation exists (client-side only is insufficient).

**Audit logging**:
- Event coverage: all events specified in the mitigation are logged (auth attempts, access denials, data modifications).
- Log content: logs include timestamp, user identity, action, resource, result — but not sensitive data (passwords, tokens, PII).
- Tamper resistance: logs are written to append-only storage or forwarded to a centralized logging system.

## Authentication review

Review the complete authentication flow for correctness:

### Flow completeness

- Registration: is the full registration flow secure (email verification, CAPTCHA, rate limiting)?
- Login: is the login flow complete (credential verification, session creation, MFA prompt)?
- Logout: does logout invalidate the session server-side (not just client-side cookie deletion)?
- Password reset: is the reset flow secure (time-limited tokens, rate limiting, no user enumeration)?
- Token refresh: is the refresh token flow secure (rotation, revocation, binding)?

### Credential storage

- Passwords must be hashed with a modern adaptive algorithm: `bcrypt` (cost >= 12), `argon2id` (preferred), or `scrypt`.
- Reject: MD5, SHA1, SHA256 without salt, SHA256 with static salt, plaintext storage.
- Salt: must be unique per user, generated from CSPRNG, stored alongside the hash.
- Pepper: recommended (application-level secret added before hashing), stored in secure config.

### MFA implementation

If MFA is implemented or required by the threat model:
- TOTP: correct time window handling, replay prevention, backup codes.
- WebAuthn/FIDO2: correct challenge-response, origin validation.
- SMS/Email OTP: rate limiting, expiry, single-use enforcement.

### Session management

- **Timeout**: session expires after inactivity (recommended: 15-30 minutes for sensitive apps).
- **Rotation**: session ID is regenerated after authentication (prevents session fixation).
- **Invalidation**: explicit logout invalidates the session server-side.
- **Storage**: session data stored server-side (not in client-accessible cookies). If JWTs are used, verify short expiry and refresh token rotation.
- **Cookie flags**: `Secure`, `HttpOnly`, `SameSite=Strict` (or `Lax` with CSRF tokens).

## Authorization review

### RBAC/ABAC implementation

- Role definitions are centralized (not scattered across endpoints).
- Role assignment is managed through a secure admin interface (not user-modifiable).
- Permission checks are consistent: same middleware/decorator pattern used across all protected endpoints.
- Default deny: endpoints without explicit permission grants are inaccessible.

### Privilege escalation paths

- Vertical: can a regular user access admin functionality? Check every admin endpoint for role verification.
- Horizontal (IDOR): can user A access user B's resources? Check that every resource access includes ownership verification.
- Diagonal: can a user combine multiple low-privilege operations to achieve a high-privilege result?

### Default-deny principle

- New endpoints added without authorization decorators/middleware are denied by default (framework configuration).
- API routes have a catch-all that denies unmatched paths.
- Missing authorization returns 403 (not 200 with empty data, which leaks existence).

## Input validation review

### Validation approach

- **Allowlist (whitelist)**: define what is permitted (preferred). Example: `user_id` must be a UUID matching `/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i`.
- **Denylist (blacklist)**: define what is forbidden (fragile, bypass-prone). Flag any denylist-only validation as a finding.

### Output encoding (XSS prevention)

- HTML context: HTML entity encoding for user data rendered in HTML.
- JavaScript context: JavaScript encoding for user data embedded in scripts.
- URL context: URL encoding for user data in URLs.
- CSS context: CSS encoding for user data in style attributes.
- Framework auto-escaping: verify it is enabled and not bypassed (`| safe`, `dangerouslySetInnerHTML`, `v-html`).

### Parameterized queries (SQL injection prevention)

- All database queries use parameterized queries or ORM query builders.
- No string concatenation or interpolation in SQL statements.
- Stored procedures: parameters are passed, not interpolated.
- Dynamic query construction (search filters, sorting): uses safe builder patterns, not string assembly.

### File upload restrictions

- File type validation: check MIME type and file extension (not just extension).
- File size limits enforced server-side.
- Uploaded files stored outside the web root.
- Filename sanitization: strip path components, generate random filenames.
- Content scanning: for executable content, embedded scripts.

### Content-type validation

- Request `Content-Type` header is validated before parsing.
- Responses set explicit `Content-Type` with charset.
- JSON APIs reject non-JSON content types.

## Error handling review

### Information leakage

Verify that error responses do not expose:

- Stack traces in production responses.
- Internal file paths or directory structure.
- Database error messages (table names, column names, query fragments).
- Framework version numbers or server software identifiers.
- Internal IP addresses or hostnames.
- Detailed validation error messages that reveal business logic.

### Custom error pages

- 4xx and 5xx errors return generic, non-informative messages in production.
- Error detail logging goes to server-side logs (not client responses).
- Different error types (auth failure, not found, server error) return appropriately distinct HTTP status codes without leaking the reason for the distinction.

### Fail-secure behavior

- On authentication failure: deny access (not grant access with reduced privileges).
- On authorization check failure: deny the operation (not proceed with default permissions).
- On input validation failure: reject the request (not sanitize and proceed).
- On encryption failure: fail the operation (not fall back to plaintext).
- On external service failure: fail closed (not bypass the security check).

## Security headers

Verify the following HTTP response headers are set correctly:

| Header | Expected value | Purpose |
|---|---|---|
| `Content-Security-Policy` | Restrictive policy (no `unsafe-inline`, no `unsafe-eval` unless justified) | Prevent XSS, data injection |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Force HTTPS |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` or `no-referrer` | Control referrer leakage |
| `Permissions-Policy` | Restrict unnecessary browser features (camera, microphone, geolocation) | Reduce attack surface |
| `Cache-Control` | `no-store` for sensitive responses | Prevent caching of sensitive data |

## CORS configuration

- **Allowed origins**: verify that `Access-Control-Allow-Origin` is set to specific origins (not `*` when credentials are used).
- **Allowed methods**: verify only necessary HTTP methods are permitted.
- **Allowed headers**: verify only necessary headers are permitted (not `*`).
- **Credentials**: if `Access-Control-Allow-Credentials: true`, the origin must not be `*`.
- **Preflight caching**: `Access-Control-Max-Age` is set to a reasonable value.
- **Exposed headers**: only necessary headers are exposed to the client.

## Cryptographic review

### Algorithm selection

Verify algorithms meet current standards:

| Purpose | Acceptable | Unacceptable |
|---|---|---|
| Symmetric encryption | AES-256-GCM, AES-256-CBC+HMAC, ChaCha20-Poly1305 | DES, 3DES, RC4, AES-128 (if regulation requires 256), ECB mode |
| Asymmetric encryption | RSA-2048+ (OAEP padding), ECDSA P-256+, Ed25519 | RSA-1024, RSA with PKCS#1 v1.5 padding for encryption |
| Hashing (integrity) | SHA-256, SHA-384, SHA-512, SHA-3 | MD5, SHA-1 |
| Password hashing | Argon2id, bcrypt (cost >= 12), scrypt | MD5, SHA-1, SHA-256 (even with salt), PBKDF2 (< 600k iterations) |
| Key derivation | HKDF, PBKDF2 (>= 600k iterations) | Custom KDFs, single-pass hash |
| Random generation | CSPRNG (`/dev/urandom`, `SecureRandom`, `crypto.randomBytes`) | `Math.random()`, `random.random()`, `rand()`, time-based seeds |

### Key management

- Keys are not hardcoded in source code.
- Keys are loaded from environment variables, secrets manager, or HSM.
- Key rotation mechanism exists.
- Old keys are retained for decryption of existing data during rotation.

### IV/nonce handling

- IVs and nonces are never reused with the same key.
- GCM nonces: 96 bits, unique per encryption operation (counter or random).
- CBC IVs: random, unpredictable, generated from CSPRNG.

## Interaction model

This stage runs automatically. The sequence:

1. Read the threat model (`SEC-TM-*`) to build the mitigation verification checklist.
2. Read the audit report (`SEC-VA-*`) to understand known vulnerability locations.
3. For each mitigation in the threat model, locate the code and verify implementation.
4. Perform deep review of auth, authz, input validation, error handling, headers, CORS, and crypto.
5. Compile findings into the Security Advisory recommendations.
6. Present the review report to the user with `sec-record` commands.

## Escalation

Escalate to the user immediately when:

- **Unimplemented critical mitigation**: a `critical` or `high` risk threat from the threat model has a mitigation that is `missing` or `incorrect` in code. Present: the threat ID, mitigation description, what was expected, what was found (or not found), and the affected component.
- **Architecture-level security flaw**: a security issue that cannot be fixed by code changes alone — requires Arch-level redesign. Example: no authentication boundary between public and internal services, shared database with no row-level security. Flag for `arch:review` feedback.
- **Cryptographic misuse**: fundamentally broken cryptographic implementation (e.g. ECB mode for sensitive data, nonce reuse in GCM, custom encryption algorithm). This class of bug is subtle and high-impact.

Do **not** escalate for:

- Missing security headers (record as a finding, recommend addition).
- Partial input validation (record as a finding with specific gaps).
- Non-critical mitigations that are partially implemented (record status and recommend completion).

## Read-only reminder

Sec is read-only. This stage produces analysis and recommendations. All artifact updates go through `sec-record`. When the review is complete, provide the user with the exact commands:

```
sec-record: artifact.py init --section security-advisory
# User populates SEC-SR-001.md with the security advisory content
sec-record: artifact.py link SEC-SR-001 --upstream SEC-TM-001
sec-record: artifact.py link SEC-SR-001 --upstream SEC-VA-001
sec-record: artifact.py link SEC-SR-001 --upstream IMPL-MAP-001
sec-record: artifact.py set-progress SEC-SR-001 --completed 4 --total 4
sec-record: artifact.py set-phase SEC-SR-001 in_review
```

Note: the Security Advisory artifact is initialized here but fully populated in Stage 4 (compliance), which synthesizes all findings into the final advisory. Stage 3 contributes review findings to the advisory content.
