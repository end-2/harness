# OWASP Top 10 (2021) — Detection Patterns

Quick-reference for AI-driven code analysis. For each category: what it is, what to search for, and how to fix it.

---

## A01 — Broken Access Control

**Description:** Users act outside intended permissions — accessing other users' data, modifying access controls, or escalating privileges.

**Common CWEs:** CWE-200, CWE-201, CWE-352, CWE-639, CWE-862, CWE-863, CWE-913

**Detection Patterns:**
- Missing authorization checks on endpoints/handlers
- Direct object references using user-supplied IDs without ownership validation (`/api/users/{id}`, `?account_id=`)
- CORS misconfiguration (`Access-Control-Allow-Origin: *`)
- Missing CSRF token validation
- Role checks only on frontend, not backend
- JWT manipulation without server-side validation
- Path traversal in file access (`../`)

**Search patterns:**
```
@app.route|@RequestMapping|router\.(get|post|put|delete)  → then check for missing @auth/@login_required/middleware
user_id|account_id|order_id  → from request params used directly in DB queries
Access-Control-Allow-Origin.*\*
csrf|CSRF  → check if disabled or missing
```

**Vulnerable:**
```python
@app.route('/api/orders/<order_id>')
def get_order(order_id):
    return db.query(f"SELECT * FROM orders WHERE id = {order_id}")
```

**Secure:**
```python
@app.route('/api/orders/<order_id>')
@login_required
def get_order(order_id):
    order = db.query("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, current_user.id))
    if not order:
        abort(404)
    return order
```

**Remediation:** Deny by default. Enforce ownership checks server-side. Use indirect references. Implement RBAC. Disable CORS wildcard. Add CSRF tokens. Rate-limit API access. Log access control failures.

---

## A02 — Cryptographic Failures

**Description:** Failures related to cryptography — missing encryption, weak algorithms, poor key management, exposing sensitive data.

**Common CWEs:** CWE-259, CWE-327, CWE-328, CWE-330, CWE-331, CWE-311, CWE-312, CWE-319, CWE-798

**Detection Patterns:**
- Weak algorithms: MD5, SHA1, DES, 3DES, RC4, ECB mode
- Hardcoded keys, passwords, secrets in source
- Missing TLS enforcement (HTTP URLs, disabled certificate verification)
- Insufficient randomness (`Math.random()`, `rand()`, `random.random()`)
- Plaintext storage of passwords or sensitive data
- Missing salt in password hashing

**Search patterns:**
```
md5|MD5|sha1|SHA1|DES|3DES|RC4|ECB
password\s*=\s*["']|secret\s*=\s*["']|api_key\s*=\s*["']
http://  → (non-HTTPS URLs for sensitive endpoints)
verify\s*=\s*False|VERIFY_SSL.*false|InsecureRequestWarning
Math\.random|rand\(\)|random\.random
\.encode\(|base64  → used as "encryption"
```

**Vulnerable:**
```python
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()
```

**Secure:**
```python
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

**Remediation:** Use AES-256-GCM or ChaCha20-Poly1305 for encryption. Use bcrypt/scrypt/Argon2 for passwords. Use CSPRNG for random values. Enforce TLS 1.2+. Never hardcode secrets. Classify data and encrypt accordingly.

---

## A03 — Injection

**Description:** User-supplied data sent to an interpreter as part of a command or query without proper validation/sanitization.

**Common CWEs:** CWE-79, CWE-89, CWE-78, CWE-94, CWE-917, CWE-77

**Detection Patterns:**
- String concatenation/interpolation in SQL queries
- User input passed to `eval()`, `exec()`, `system()`, `os.popen()`
- Template strings with user input (SSTI)
- LDAP/XPath queries built from user input
- User input rendered without encoding (XSS)
- ORM raw query methods with interpolation

**Search patterns:**
```
execute\(.*[f"'%+]|query\(.*[f"'%+]  → SQL injection
eval\(|exec\(|system\(|popen\(|subprocess\.call\(.*shell=True
\.innerHTML\s*=|document\.write\(|v-html|dangerouslySetInnerHTML
render_template_string\(|Template\(.*user|Jinja2.*from_string
```

**Vulnerable:**
```python
cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
```

**Secure:**
```python
cursor.execute("SELECT * FROM users WHERE name = %s", (username,))
```

**Remediation:** Use parameterized queries/prepared statements. Use ORM methods. Validate and sanitize all input. Apply output encoding. Avoid `eval()`/`exec()`. Use allowlists for command arguments.

---

## A04 — Insecure Design

**Description:** Missing or ineffective security controls by design — not implementation bugs, but architectural flaws.

**Common CWEs:** CWE-209, CWE-256, CWE-501, CWE-522, CWE-840

**Detection Patterns:**
- No rate limiting on authentication endpoints
- Missing account lockout mechanism
- Business logic that trusts client-side validation only
- No transaction limits or velocity checks
- Missing abuse-case handling in workflows
- Password reset flows without proper verification
- Multi-step workflows that can be skipped

**Search patterns:**
```
rate.limit|throttle|RateLimit  → check if present on auth endpoints
lockout|max.attempts|failed.login  → check if implemented
price|amount|quantity  → from client input without server validation
reset.password|forgot.password  → check verification flow
```

**Vulnerable:**
```python
@app.route('/api/transfer', methods=['POST'])
def transfer():
    amount = request.json['amount']  # No limit check
    from_account = request.json['from']  # No ownership check
    to_account = request.json['to']
    execute_transfer(from_account, to_account, amount)
```

**Secure:**
```python
@app.route('/api/transfer', methods=['POST'])
@login_required
@rate_limit(max=10, per='hour')
def transfer():
    amount = request.json['amount']
    if amount <= 0 or amount > current_user.daily_limit:
        abort(400)
    if request.json['from'] != current_user.account_id:
        abort(403)
    execute_transfer(current_user.account_id, request.json['to'], amount)
```

**Remediation:** Threat model during design. Define security requirements per feature. Use abuse-case stories. Implement rate limiting, transaction limits, and multi-factor verification for sensitive operations. Validate business logic server-side.

---

## A05 — Security Misconfiguration

**Description:** Insecure default configurations, incomplete setups, open cloud storage, unnecessary features enabled, verbose error messages.

**Common CWEs:** CWE-16, CWE-611, CWE-1188

**Detection Patterns:**
- Debug mode enabled in production (`DEBUG = True`)
- Default credentials in configs
- Verbose error pages/stack traces returned to client
- Unnecessary HTTP methods enabled
- Missing security headers (CSP, HSTS, X-Frame-Options)
- XML external entity processing enabled
- Directory listing enabled
- Default admin accounts/paths

**Search patterns:**
```
DEBUG\s*=\s*True|debug:\s*true|NODE_ENV.*development
admin|root  → default credentials in config files
stack.trace|traceback|printStackTrace  → exposed to users
X-Frame-Options|Content-Security-Policy|Strict-Transport  → check if set
xml.*external|DTD|ENTITY|etree.*parse  → XXE
```

**Vulnerable:**
```python
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'dev-secret-key'
```

**Secure:**
```python
app.config['DEBUG'] = os.environ.get('DEBUG', 'false').lower() == 'true'
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']  # Fail if missing
```

**Remediation:** Harden all environments. Remove defaults. Disable debug mode. Set security headers. Disable XML external entities. Review cloud permissions. Automate configuration verification. Strip unnecessary features/frameworks.

---

## A06 — Vulnerable and Outdated Components

**Description:** Using components (libraries, frameworks) with known vulnerabilities, or not tracking/updating dependencies.

**Common CWEs:** CWE-1104

**Detection Patterns:**
- Outdated dependency versions in manifest files
- Known vulnerable library versions
- Dependencies without pinned versions
- No lockfile present
- Vendored/copied library code (stale copies)
- Missing dependency scanning in CI/CD

**Search patterns:**
```
package.json|requirements.txt|Gemfile|pom.xml|go.mod|Cargo.toml  → check versions
package-lock.json|yarn.lock|Pipfile.lock|Gemfile.lock  → should exist
vendor/|third.party/|lib/  → vendored code
```

**Checks:**
- Are dependency versions pinned?
- Is there a lockfile?
- Are there known CVEs for listed versions? (cross-reference with NVD/advisory databases)
- Is there a dependency scanning step in CI?

**Remediation:** Maintain dependency inventory. Use automated scanning (Dependabot, Snyk, Trivy). Pin versions. Update regularly. Remove unused dependencies. Subscribe to security advisories.

---

## A07 — Identification and Authentication Failures

**Description:** Weaknesses in authentication mechanisms — weak passwords, credential stuffing, session mismanagement.

**Common CWEs:** CWE-287, CWE-297, CWE-384, CWE-521, CWE-613, CWE-798

**Detection Patterns:**
- Missing MFA implementation
- Weak password policies (short min length, no complexity)
- Session IDs in URLs
- No session expiration/rotation
- Plaintext credential storage or transmission
- Hardcoded credentials
- Missing brute-force protection

**Search patterns:**
```
min.length|password.policy|MIN_PASSWORD  → check strength requirements
session.*expire|session.*timeout|SESSION_LIFETIME  → check if set
session.*rotate|regenerate.session  → after login
hardcoded|password\s*=\s*["'][^"']+["']  → in source
bcrypt|argon2|scrypt|pbkdf2  → should be present for password hashing
```

**Vulnerable:**
```python
if user.password == request.form['password']:  # Plaintext comparison
    session['user'] = user.id  # No session rotation
```

**Secure:**
```python
if bcrypt.checkpw(request.form['password'].encode(), user.password_hash):
    session.regenerate()
    session['user'] = user.id
```

**Remediation:** Implement MFA. Enforce strong passwords (NIST 800-63b). Use bcrypt/Argon2. Rotate sessions on login. Set session timeouts. Implement account lockout. Never hardcode credentials.

---

## A08 — Software and Data Integrity Failures

**Description:** Code/infrastructure without integrity verification — insecure CI/CD, unsigned updates, deserialization of untrusted data.

**Common CWEs:** CWE-502, CWE-829, CWE-494, CWE-915

**Detection Patterns:**
- Deserialization of untrusted input (`pickle.loads`, `ObjectInputStream`, `unserialize`, `yaml.load`)
- Missing integrity checks on dependencies (no lockfile hashes, no subresource integrity)
- CI/CD pipelines without signature verification
- Auto-update mechanisms without signature checks
- Mass assignment vulnerabilities

**Search patterns:**
```
pickle\.load|yaml\.load\(|ObjectInputStream|unserialize\(|Marshal\.load
eval\(.*request|JSON\.parse\(.*body  → with subsequent object property spread
integrity=|sha256-|sha384-  → SRI on CDN resources (check if present)
mass.assign|attr_accessible|permit\(|fillable  → mass assignment controls
```

**Vulnerable:**
```python
data = pickle.loads(request.data)  # Arbitrary code execution
```

**Secure:**
```python
data = json.loads(request.data)  # Safe deserialization
schema.validate(data)
```

**Remediation:** Verify digital signatures. Use lockfiles with hashes. Use SRI for CDN resources. Avoid unsafe deserialization. Use allowlists for mass assignment. Secure CI/CD pipelines. Code-review all pipeline changes.

---

## A09 — Security Logging and Monitoring Failures

**Description:** Insufficient logging, detection, and response capability — breaches go undetected.

**Common CWEs:** CWE-117, CWE-223, CWE-532, CWE-778

**Detection Patterns:**
- Missing logging on authentication events (login, failure, lockout)
- Missing logging on access control failures
- Missing logging on input validation failures
- Sensitive data in logs (passwords, tokens, PII)
- No centralized logging
- No alerting on suspicious activity
- Log injection vulnerabilities

**Search patterns:**
```
log\.(info|warn|error|debug)|logger\.|logging\.  → check what's logged
password|token|secret|credit.card  → in log statements (data leak)
login|authenticate|authorize  → check if failures are logged
alert|notify|alarm  → check if security events trigger alerts
```

**Vulnerable:**
```python
logger.info(f"Login attempt: user={username}, password={password}")  # Leaking password
# No logging on failed login attempts
```

**Secure:**
```python
logger.info(f"Login attempt: user={username}")
if not authenticate(username, password):
    logger.warning(f"Failed login: user={username}, ip={request.remote_addr}")
    alert_if_threshold_exceeded(username)
```

**Remediation:** Log all authentication, authorization, and input validation events. Never log sensitive data. Use structured logging. Centralize logs. Set up alerting for suspicious patterns. Ensure logs are tamper-resistant. Test logging and alerting regularly.

---

## A10 — Server-Side Request Forgery (SSRF)

**Description:** Application fetches a remote resource using user-supplied URL without validation, allowing attackers to reach internal services.

**Common CWEs:** CWE-918

**Detection Patterns:**
- User-supplied URLs passed to HTTP clients
- URL parameters used for file fetching, webhooks, or API calls
- Missing URL validation/allowlisting
- Access to cloud metadata endpoints (`169.254.169.254`)
- DNS rebinding vulnerabilities

**Search patterns:**
```
requests\.get\(.*request|urllib\.open\(.*param|fetch\(.*user|HttpClient.*url
url\s*=\s*request\.|webhook.*url|callback.*url|redirect.*url
169\.254\.169\.254|metadata\.google|metadata\.aws
```

**Vulnerable:**
```python
@app.route('/fetch')
def fetch_url():
    url = request.args.get('url')
    response = requests.get(url)  # Attacker can target internal services
    return response.text
```

**Secure:**
```python
@app.route('/fetch')
def fetch_url():
    url = request.args.get('url')
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        abort(400)
    if is_internal_ip(parsed.hostname):
        abort(403)
    response = requests.get(url, allow_redirects=False, timeout=5)
    return response.text
```

**Remediation:** Validate and sanitize all user-supplied URLs. Use allowlists for permitted domains/IPs. Block internal/private IP ranges. Disable HTTP redirects or re-validate after redirect. Use network segmentation. Block metadata endpoints.
