# CWE Catalog — Common Weakness Enumeration Reference

Quick-lookup catalog of frequently encountered CWEs. For each: ID, name, what it means, and what to search for in code.

---

## Injection

### CWE-89: SQL Injection

**Description:** User input incorporated into SQL queries without proper sanitization or parameterization.

**Detection patterns:**
```
execute\(.*[f"'%+]|query\(.*[f"'%+]|raw\(.*[f"'%+]
cursor\.(execute|fetchone|fetchall).*format\(
\.where\(.*\+|\.filter\(.*\+  → string concatenation in ORM
```

---

### CWE-78: OS Command Injection

**Description:** User input passed to system shell commands without sanitization.

**Detection patterns:**
```
os\.system\(|os\.popen\(|subprocess\.call\(.*shell=True
exec\(|Runtime\.getRuntime\(\)\.exec\(
child_process\.exec\(|spawn\(.*shell.*true
```

---

### CWE-79: Cross-Site Scripting (XSS)

**Description:** User input included in web page output without proper encoding.

**Detection patterns:**
```
\.innerHTML\s*=|document\.write\(|\.html\(
dangerouslySetInnerHTML|v-html|ng-bind-html
\|safe|\|raw|autoescape\s+false|mark_safe\(
render_template_string\(
```

---

### CWE-94: Code Injection

**Description:** User input interpreted as code by the application.

**Detection patterns:**
```
eval\(|exec\(|compile\(.*request
new Function\(|setTimeout\(.*user|setInterval\(.*user
ScriptEngine.*eval|GroovyShell.*evaluate
```

---

### CWE-917: Expression Language Injection

**Description:** User input evaluated as an expression in a template or expression engine.

**Detection patterns:**
```
SpEL.*parseExpression|#\{.*request|EL.*getValue
\$\{.*user|\$\{.*param|\$\{.*request
template.*from_string\(|render_template_string\(
```

---

## Authentication

### CWE-287: Improper Authentication

**Description:** The application does not sufficiently verify user identity.

**Detection patterns:**
```
authenticate|login|verify.*user  → check if properly implemented
@public|@no.auth|skip.*auth  → intentionally unprotected
token.*verify|jwt.*decode  → check if signature is validated
```

---

### CWE-306: Missing Authentication for Critical Function

**Description:** Critical endpoints accessible without authentication.

**Detection patterns:**
```
@app\.route|@RequestMapping|router\.(get|post|put|delete)  → check auth decorators
admin|config|setting|delete|modify  → endpoints without auth middleware
```

---

### CWE-798: Hardcoded Credentials

**Description:** Credentials embedded in source code.

**Detection patterns:**
```
password\s*=\s*["'][^"']+["']|passwd\s*=\s*["']
api[_-]?key\s*=\s*["'][^"']+["']|secret\s*=\s*["']
token\s*=\s*["'][A-Za-z0-9+/=]+["']
AWS_ACCESS_KEY|AKIA[0-9A-Z]{16}
```

---

### CWE-521: Weak Password Requirements

**Description:** Application does not enforce sufficient password complexity/length.

**Detection patterns:**
```
min.length|password.*length|MIN_PASSWORD  → check if >= 8 (NIST: >= 8)
complexity|uppercase|lowercase|digit|special  → check policy
```

---

## Authorization

### CWE-862: Missing Authorization

**Description:** Application does not perform authorization checks for requested operations.

**Detection patterns:**
```
# Endpoint handlers without authorization middleware/decorators
@app\.route  → missing @login_required, @permission_required
router\.(get|post)  → missing auth middleware in chain
```

---

### CWE-863: Incorrect Authorization

**Description:** Authorization check exists but is flawed.

**Detection patterns:**
```
role.*==|isAdmin|hasRole  → check logic for bypasses
or.*admin|if.*user\.role  → check for logic errors
```

---

### CWE-639: Insecure Direct Object Reference (IDOR)

**Description:** Application uses user-supplied identifiers to access objects without ownership verification.

**Detection patterns:**
```
params\[:id\]|request\.args\.get\('id|req\.params\.id
/api/users/{id}|/api/orders/{id}  → check if ownership verified
findById\(.*req|get.*req\.params  → without user filter
```

---

## Cryptography

### CWE-327: Use of Broken Cryptographic Algorithm

**Description:** Application uses cryptographic algorithms known to be weak.

**Detection patterns:**
```
DES|3DES|RC4|RC2|Blowfish|MD4
ECB  → block cipher mode (insecure)
RSA.*512|RSA.*1024  → insufficient key size
```

---

### CWE-328: Use of Weak Hash (Reversible One-Way Hash)

**Description:** Using hash functions that are too fast or reversible for password storage.

**Detection patterns:**
```
md5\(|MD5\.|sha1\(|SHA1\.|sha256\(  → for password hashing (sha256 alone is insufficient)
hashlib\.(md5|sha1|sha256)\(.*password
DigestUtils\.(md5|sha1)
```

---

### CWE-330: Insufficient Randomness

**Description:** Using predictable random values for security-sensitive purposes.

**Detection patterns:**
```
Math\.random\(\)|rand\(\)|random\.random\(\)|Random\(\)
srand\(time|seed.*time  → predictable seeding
new Random\(\)  → Java (use SecureRandom)
```

---

### CWE-311: Missing Encryption of Sensitive Data

**Description:** Sensitive data stored or transmitted without encryption.

**Detection patterns:**
```
http://  → non-HTTPS for sensitive data
plaintext|plain.text  → in context of storage
password.*=.*store|save.*password  → check if encrypted
```

---

## Data Exposure

### CWE-200: Information Exposure

**Description:** Application exposes sensitive information to unauthorized actors.

**Detection patterns:**
```
\.env|config\.(json|yml|yaml|ini)  → check if exposed/accessible
/api/  → responses returning excess fields
SELECT \*  → returning all columns
```

---

### CWE-209: Information Exposure Through Error Messages

**Description:** Error messages reveal implementation details.

**Detection patterns:**
```
traceback|stack.trace|printStackTrace
debug.*true|DEBUG.*True  → in production config
except.*pass|catch.*empty  → swallowed errors (different problem)
return.*str\(e\)|response.*exception\.getMessage
```

---

### CWE-532: Information Exposure Through Log Files

**Description:** Sensitive data written to log files.

**Detection patterns:**
```
log\.(info|debug|warn|error).*password|logger.*token
log\.(info|debug|warn|error).*credit.card|logger.*ssn
print\(.*password|console\.log\(.*token
```

---

## Configuration

### CWE-16: Configuration

**Description:** Weaknesses caused by insecure configuration settings.

**Detection patterns:**
```
DEBUG\s*=\s*True|debug:\s*true
allow_all|permit_all|\*  → overly permissive settings
CORS.*\*|Access-Control.*\*
```

---

### CWE-1188: Insecure Default Initialization of Resource

**Description:** Resources initialized with insecure default values.

**Detection patterns:**
```
default.*password|default.*secret|default.*key
TODO.*change|FIXME.*security|HACK
placeholder|example\.com|changeme|admin123
```

---

## Session Management

### CWE-384: Session Fixation

**Description:** Application does not regenerate session ID after authentication.

**Detection patterns:**
```
session.*login|authenticate.*session  → check if session regenerated
regenerate|rotate.*session|new.*session  → should be present post-login
```

---

### CWE-613: Insufficient Session Expiration

**Description:** Sessions that do not expire or have overly long lifetimes.

**Detection patterns:**
```
session.*expire|session.*timeout|SESSION_LIFETIME|maxAge
permanent.*session|remember.*forever
cookie.*expire|max.age  → check values
```

---

## File Handling

### CWE-22: Path Traversal

**Description:** User input used to construct file paths without sanitization.

**Detection patterns:**
```
\.\./|\.\.\\  → literal traversal patterns
open\(.*request|File\(.*param|fs\.(read|write).*req
path\.join\(.*user|os\.path\.join\(.*request  → without validation
```

---

### CWE-434: Unrestricted Upload of File with Dangerous Type

**Description:** File upload without validation of file type, size, or content.

**Detection patterns:**
```
upload|multipart|file.*save|write.*file
content.type|mime.type|extension  → check if validated
\.exe|\.php|\.jsp|\.sh  → check if blocked
file.*size|max.*size|limit.*size  → check if enforced
```

---

## Other Critical Weaknesses

### CWE-918: Server-Side Request Forgery (SSRF)

**Description:** Application fetches resources from user-supplied URLs without validation.

**Detection patterns:**
```
requests\.get\(.*request|urllib.*request|fetch\(.*user
url\s*=\s*request|webhook.*url|callback.*url
HttpClient.*param|RestTemplate.*param
```

---

### CWE-502: Deserialization of Untrusted Data

**Description:** Application deserializes data from untrusted sources without validation.

**Detection patterns:**
```
pickle\.load|yaml\.load\(|yaml\.unsafe_load
ObjectInputStream|readObject\(
unserialize\(|Marshal\.load|JSON\.parse  → when followed by property access
```

---

### CWE-611: Improper Restriction of XML External Entity Reference (XXE)

**Description:** XML parser processes external entity references from untrusted input.

**Detection patterns:**
```
xml\.etree|lxml\.etree|DocumentBuilder|SAXParser
XMLReader|XmlPullParser
FEATURE.*external|FEATURE.*dtd  → check if disabled
etree\.parse\(|etree\.fromstring\(  → check parser configuration
```
