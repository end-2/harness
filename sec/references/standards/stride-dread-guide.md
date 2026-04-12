# STRIDE & DREAD — Threat Analysis Guide

Practical reference for systematic threat modeling and risk scoring.

---

## STRIDE Threat Categories

### Spoofing

**Definition:** Pretending to be something or someone else to gain illegitimate access.

**Typical Targets:** Authentication systems, user sessions, API tokens, email senders, IP addresses.

**Example Threats:**
- Stolen or forged credentials
- Session hijacking via token theft
- IP spoofing to bypass network ACLs
- Forged email headers in notification systems
- Replayed authentication tokens

**Typical Mitigations:**
- Strong authentication (MFA)
- Mutual TLS for service-to-service
- Signed tokens with expiration (JWT with short TTL)
- Session binding (IP, device fingerprint)
- Anti-replay mechanisms (nonces, timestamps)

---

### Tampering

**Definition:** Unauthorized modification of data — at rest, in transit, or in memory.

**Typical Targets:** Database records, configuration files, API payloads, cookies, URL parameters, logs.

**Example Threats:**
- Modifying request parameters to change prices/quantities
- SQL injection to alter database records
- Man-in-the-middle modifying API responses
- Cookie tampering to escalate privileges
- Log tampering to cover tracks

**Typical Mitigations:**
- Input validation and integrity checks
- Digital signatures on critical data
- TLS for data in transit
- Database integrity constraints
- Immutable audit logs
- HMAC on cookies and tokens

---

### Repudiation

**Definition:** Denying having performed an action when there is no way to prove otherwise.

**Typical Targets:** Financial transactions, data modifications, administrative actions, consent records.

**Example Threats:**
- User denies placing an order
- Admin denies changing permissions
- Developer denies deploying malicious code
- User denies giving consent

**Typical Mitigations:**
- Comprehensive audit logging with tamper protection
- Digital signatures on transactions
- Timestamps from trusted sources
- Non-repudiation through cryptographic proof
- Centralized, append-only log storage

---

### Information Disclosure

**Definition:** Exposing information to unauthorized parties.

**Typical Targets:** PII, credentials, business data, system internals, source code, configuration.

**Example Threats:**
- Verbose error messages revealing stack traces
- API responses returning excess fields
- Directory listing exposing source files
- Credentials in logs or version control
- Timing attacks revealing valid usernames

**Typical Mitigations:**
- Minimize data in API responses
- Generic error messages for end users
- Remove debug endpoints in production
- Encrypt sensitive data at rest and in transit
- Constant-time comparison for secrets
- Data classification and access controls

---

### Denial of Service

**Definition:** Making a system unavailable or degraded for legitimate users.

**Typical Targets:** Web servers, APIs, databases, authentication services, file storage, message queues.

**Example Threats:**
- Resource exhaustion via large payloads
- Algorithmic complexity attacks (ReDoS, hash collision)
- Unbounded queries consuming database resources
- File upload filling disk
- Account lockout abuse

**Typical Mitigations:**
- Rate limiting and throttling
- Input size limits (payload, file, query)
- Timeout configuration
- Resource quotas per user/tenant
- Pagination for list endpoints
- CDN and DDoS protection
- Circuit breakers

---

### Elevation of Privilege

**Definition:** Gaining capabilities beyond what is authorized — vertical (user to admin) or horizontal (user A accessing user B's data).

**Typical Targets:** Role/permission systems, admin interfaces, API endpoints, file system access.

**Example Threats:**
- Modifying role claims in JWT
- IDOR to access other users' resources
- Path traversal to access system files
- SQL injection to bypass authentication
- Exploiting default admin accounts

**Typical Mitigations:**
- Principle of least privilege
- Server-side authorization on every request
- Input validation preventing injection
- Secure token verification (signature + claims)
- Remove default accounts
- Sandboxing and process isolation

---

## Applying STRIDE Systematically

### Per-Component Analysis

For each component in the system (web server, API, database, message queue, file storage, cache):

1. List assets the component handles
2. Walk through each STRIDE category
3. Ask: "How could an attacker achieve [S/T/R/I/D/E] against this component?"
4. Document threats and proposed mitigations

### Per-Data-Flow Analysis

For each data flow between components:

1. Identify what data travels the flow
2. Identify the transport mechanism
3. For each STRIDE category, ask:
   - **S:** Can the sender be spoofed?
   - **T:** Can the data be modified in transit?
   - **R:** Can the sender deny sending?
   - **I:** Can an eavesdropper read the data?
   - **D:** Can the flow be disrupted?
   - **E:** Can the flow be hijacked for privilege escalation?

### Per-Trust-Boundary Analysis

For each trust boundary (user-to-server, server-to-database, internal-to-external, container-to-host):

1. Identify what crosses the boundary
2. Identify authentication/authorization at the boundary
3. For each STRIDE category, ask what threats exist at this crossing point
4. Verify that controls exist for each applicable threat

### Prioritization

After enumeration, prioritize using DREAD scoring (below) or a simpler High/Medium/Low classification based on:
- Likelihood of exploitation
- Impact if exploited
- Difficulty of mitigation

---

## DREAD Risk Scoring

### Factors (1-10 Scale)

#### Damage (D) — What is the impact if exploited?

| Score | Meaning |
|-------|---------|
| 1-2   | Minimal impact, no data loss, minor inconvenience |
| 3-4   | Limited data exposure, minor financial impact |
| 5-6   | Significant data breach, moderate financial loss |
| 7-8   | Major data breach, significant financial/reputational damage |
| 9-10  | Complete system compromise, massive data loss, regulatory penalties |

#### Reproducibility (R) — How easy to reproduce?

| Score | Meaning |
|-------|---------|
| 1-2   | Very difficult, requires rare conditions or race conditions |
| 3-4   | Difficult, requires specific environment or timing |
| 5-6   | Moderate, requires some setup but is reliable |
| 7-8   | Easy, works most of the time with minimal setup |
| 9-10  | Trivial, works every time with a simple request |

#### Exploitability (E) — How easy to exploit?

| Score | Meaning |
|-------|---------|
| 1-2   | Requires deep expertise, custom tooling, insider knowledge |
| 3-4   | Requires security expertise and specialized tools |
| 5-6   | Requires moderate skill, public tools available |
| 7-8   | Easy with basic tools, script-kiddie level |
| 9-10  | No special tools needed, browser or curl sufficient |

#### Affected Users (A) — What percentage of users affected?

| Score | Meaning |
|-------|---------|
| 1-2   | Very small subset, specific conditions required |
| 3-4   | Small percentage of users |
| 5-6   | Moderate percentage, specific user group |
| 7-8   | Most users or a critical user group (admins) |
| 9-10  | All users |

#### Discoverability (D) — How easy to find?

| Score | Meaning |
|-------|---------|
| 1-2   | Extremely difficult to discover, requires source code access |
| 3-4   | Difficult, requires detailed probing or fuzzing |
| 5-6   | Moderate, discoverable through systematic testing |
| 7-8   | Easy, visible in public interfaces or documentation |
| 9-10  | Obvious, publicly known, or in published source code |

### Scoring Calculation

**Total Score = D + R + E + A + D** (sum of all five factors, range 5-50)

### Risk Level Mapping

| Total Score | Risk Level | Recommended Action |
|-------------|------------|-------------------|
| 40-50       | **Critical** | Immediate remediation. Block deployment until fixed. |
| 25-39       | **High** | Remediate within current sprint. Escalate to security lead. |
| 15-24       | **Medium** | Schedule remediation. Track in backlog with priority. |
| 5-14        | **Low** | Accept risk or schedule for future improvement. Document decision. |

### Example Scoring

**SQL Injection in login endpoint:**
- Damage: 9 (full database access)
- Reproducibility: 9 (reliable with known payload)
- Exploitability: 8 (sqlmap automates it)
- Affected Users: 10 (all users)
- Discoverability: 7 (common test target)
- **Total: 43 — Critical**

**Missing rate limiting on search API:**
- Damage: 3 (service degradation)
- Reproducibility: 9 (send many requests)
- Exploitability: 9 (trivial)
- Affected Users: 6 (all users during attack)
- Discoverability: 5 (requires testing)
- **Total: 32 — High**

**Verbose error messages in API:**
- Damage: 3 (information disclosure)
- Reproducibility: 9 (trigger any error)
- Exploitability: 9 (trivial)
- Affected Users: 2 (attacker only benefits)
- Discoverability: 8 (visible in normal usage)
- **Total: 31 — High**
