# HIPAA — Code-Level Requirements

Focused on Technical Safeguards (45 CFR 164.312) verifiable through code analysis. Covers electronic Protected Health Information (ePHI) handling.

---

## Technical Safeguards (§164.312)

### §164.312(a) — Access Control

Implement technical policies and procedures to allow only authorized persons to access ePHI.

#### Unique User Identification (Required)

Each user must have a unique identifier. No shared accounts for ePHI access.

**Code-level checks:**
- User model has unique identifiers
- No shared/generic accounts in code or config
- Service accounts are individually tracked
- User ID included in all audit logs

**Detection patterns:**
```
shared.account|generic.user|common.login|group.account  → shared accounts
user.id|user_id|userId|subject  → unique identification in auth
service.account|system.user  → verify individually tracked
```

#### Emergency Access Procedure (Required)

Mechanism to access ePHI during emergencies.

**Code-level checks:**
- Break-glass or emergency access mechanism exists
- Emergency access is logged and audited
- Emergency access requires justification

**Detection patterns:**
```
emergency|break.glass|override|escalat  → emergency access
```

#### Automatic Logoff (Addressable)

Terminate sessions after inactivity.

**Code-level checks:**
- Session timeout configured (recommended: 15 minutes or less for ePHI systems)
- Idle timeout on all interfaces accessing ePHI
- Timeout applies to API sessions and web sessions

**Detection patterns:**
```
session.*timeout|idle.*timeout|auto.*logoff|SESSION_LIFETIME
inactiv|expire.*session  → session expiry
```

#### Encryption and Decryption (Addressable)

Encrypt ePHI at rest.

**Code-level checks:**
- ePHI fields encrypted at rest (AES-256 recommended)
- Encryption keys managed securely (not hardcoded)
- Full-disk encryption or field-level encryption for ePHI
- Key rotation mechanism

**Detection patterns:**
```
encrypt|decrypt|AES|cipher|crypto  → encryption implementation
key.*management|key.*rotation|KMS|vault  → key handling
phi|ePHI|patient|medical|health.*record|diagnosis|treatment  → ePHI fields
```

---

### §164.312(b) — Audit Controls

Implement mechanisms to record and examine access to ePHI.

#### Activity Logging (Required)

**What must be logged:**
- All access to ePHI (read, write, delete)
- Authentication events (login, logout, failure)
- Administrative actions (user management, config changes)
- Data exports and bulk access

**Log content per event:**
- Who (user ID)
- What (action, resource)
- When (timestamp)
- Where (source IP, system)
- Outcome (success/failure)

**Code-level checks:**
- Audit middleware/interceptor on ePHI endpoints
- Log entries include all required fields
- Logging cannot be bypassed or disabled by users
- No ePHI in log messages themselves

**Detection patterns:**
```
audit|access.log|security.log  → logging implementation
log.*(patient|phi|medical|health)  → ePHI in logs (BAD unless metadata only)
log.*(user|action|timestamp|ip|result)  → log content fields
middleware.*log|interceptor.*audit|before.*action.*log  → logging middleware
```

#### Log Review and Protection

**Code-level checks:**
- Logs stored in centralized, tamper-resistant system
- Log retention meets minimum requirements (6 years for HIPAA)
- Log access restricted to authorized personnel
- Alerts on suspicious access patterns

**Detection patterns:**
```
retention|archive|rotate  → log retention
immutable|append.only|write.once|tamper  → log protection
alert|notify.*suspicious|anomaly  → alerting
```

---

### §164.312(c) — Integrity

Protect ePHI from improper alteration or destruction.

#### Integrity Mechanisms (Addressable)

**Code-level checks:**
- Data integrity checks on ePHI (checksums, digital signatures)
- Database constraints preventing invalid ePHI states
- Version control or audit trail on ePHI modifications
- Input validation on ePHI fields

**Detection patterns:**
```
checksum|hash|digest|signature  → integrity verification
version|revision|audit.trail|history  → change tracking
constraint|validate|check  → data validation
```

#### Authentication of ePHI (Addressable)

Verify that ePHI has not been altered or destroyed without authorization.

**Code-level checks:**
- Digital signatures or HMAC on ePHI records
- Integrity verification on data retrieval
- Tamper detection mechanisms

---

### §164.312(d) — Person or Entity Authentication

Verify the identity of persons seeking access to ePHI.

**Code-level checks:**
- Strong authentication required for ePHI access
- MFA implemented (recommended for all ePHI access)
- Token-based authentication with proper validation
- Password requirements meet minimum standards

**Detection patterns:**
```
mfa|MFA|two.factor|2fa|totp|webauthn  → MFA implementation
authenticate|verify.*identity|login  → authentication flow
bcrypt|argon2|scrypt|pbkdf2  → password storage
jwt|token.*verify|session.*validate  → token authentication
```

---

### §164.312(e) — Transmission Security

Protect ePHI during electronic transmission.

#### Integrity Controls (Addressable)

**Code-level checks:**
- TLS 1.2+ on all ePHI transmission
- Message integrity verification (HMAC, digital signatures)
- No ePHI in URL query parameters
- No ePHI in unencrypted email

#### Encryption (Addressable but strongly recommended)

**Code-level checks:**
- All API endpoints transmitting ePHI use HTTPS
- Certificate validation enabled
- No fallback to unencrypted protocols
- VPN or encrypted channels for inter-system ePHI transfer

**Detection patterns:**
```
http://  → non-HTTPS (check if ePHI transmitted)
verify\s*=\s*False|rejectUnauthorized.*false  → disabled cert validation
tls|ssl|TLS_VERSION  → check minimum version >= 1.2
email.*phi|send.*patient|smtp.*medical  → ePHI via email
query.*param.*(patient|phi|medical)  → ePHI in URLs
```

---

## PHI Field Identification Guide

When analyzing code, identify fields that constitute PHI:

| Category | Example Fields |
|----------|---------------|
| Demographics | name, address, date_of_birth, ssn, phone, email |
| Medical | diagnosis, treatment, medication, lab_result, vital_signs |
| Financial | insurance_id, billing_code, payment_info |
| Identifiers | patient_id, mrn (medical record number), account_number |
| Dates | admission_date, discharge_date, appointment_date, dob |
| Geographic | zip_code (if population < 20k), address, city |
| Other | biometric, photo, device_id (if linkable to patient) |

**Detection patterns for PHI fields:**
```
patient|medical|health|clinical|diagnosis|treatment
medication|prescription|pharmacy|drug|dosage
lab.result|vital|blood.pressure|heart.rate|bmi
insurance|claim|billing|cpt|icd
ssn|social.security|mrn|medical.record
dob|date.of.birth|birth.date|age
```

---

## Minimum Necessary Rule

Only access/disclose the minimum ePHI necessary for the task.

**Code-level checks:**
- API responses return only required ePHI fields
- Database queries select specific columns, not `SELECT *`
- Role-based data filtering (e.g., billing staff see billing fields only)
- Bulk data access restricted and logged

**Detection patterns:**
```
SELECT \*.*patient|SELECT \*.*medical  → overly broad ePHI queries
return.*patient.*all|response.*full.*record  → excess data in responses
role.*filter|field.*access|column.*permission  → field-level access control
```

---

## Business Associate Agreement (BAA) Data Handling

When code interfaces with third-party services handling ePHI:

**Code-level checks:**
- Third-party integrations identified
- ePHI transmission to third parties encrypted
- Data shared with third parties is minimized
- Third-party API calls are logged
- Third-party data storage/handling documented

**Detection patterns:**
```
third.party|vendor|partner|external.*api  → third-party integrations
send.*patient|transmit.*phi|share.*medical  → ePHI sharing
api.*(twilio|sendgrid|stripe|aws|azure|gcp)  → cloud/SaaS integrations
```

---

## Code-Level Audit Checklist

| Area | What to Search | Expected Finding |
|------|---------------|-----------------|
| PHI fields | Data models, schemas | PHI fields identified and tagged |
| Encryption at rest | DB config, field encryption | ePHI encrypted with AES-256 |
| Encryption in transit | TLS config, API URLs | TLS 1.2+ on all ePHI endpoints |
| Access control | Auth middleware on PHI endpoints | Auth required for all ePHI access |
| Unique user IDs | User model, auth system | No shared/generic accounts |
| MFA | Auth flow | MFA on ePHI access (recommended) |
| Session timeout | Session config | <= 15 min idle timeout |
| Audit logging | Logging middleware | All ePHI access logged with who/what/when/where |
| Log protection | Log config | Tamper-resistant, 6-year retention |
| No PHI in logs | Log statements | No ePHI values in log messages |
| Integrity | Data validation, checksums | ePHI integrity verified |
| Minimum necessary | API responses, queries | Only required fields returned |
| Emergency access | Break-glass mechanism | Exists and is audited |
| BAA handling | Third-party integrations | ePHI to third parties encrypted and logged |
