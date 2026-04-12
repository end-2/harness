# GDPR — Code-Level Requirements

Focused on what is verifiable through code analysis. Covers the technical implementation requirements of the General Data Protection Regulation.

---

## Article 5 — Data Processing Principles

### Data Minimization (Art. 5(1)(c))

Only collect and process data that is strictly necessary for the stated purpose.

**Code-level checks:**
- Data models: are all fields necessary? Flag unused or overly broad fields
- API requests: are more fields collected than needed?
- Database queries: are they selecting only required columns?
- Third-party data sharing: is only necessary data transmitted?

**Detection patterns:**
```
SELECT \*  → overly broad data retrieval
user\.(profile|data|info)  → check what's included
collect|gather|capture  → data collection points
analytics|tracking|telemetry  → data collection scope
```

### Purpose Limitation (Art. 5(1)(b))

Data collected for one purpose must not be used for an incompatible purpose.

**Code-level checks:**
- Are data access patterns consistent with stated purposes?
- Is there purpose tagging/classification on data fields?
- Are there checks before using data for new features?

### Storage Limitation (Art. 5(1)(e))

Data should not be kept longer than necessary.

**Code-level checks:**
- Data retention policies implemented in code
- Automated deletion/anonymization jobs
- TTL on database records or cache entries

**Detection patterns:**
```
retention|ttl|expire|purge|cleanup|archive
cron|scheduled|job.*delete  → automated cleanup
```

---

## Articles 6-7 — Lawful Basis and Consent

### Consent Management Implementation

**Required functionality:**
- Consent collection: clear, specific, informed, unambiguous
- Consent storage: record what was consented to, when, by whom
- Consent withdrawal: as easy as giving consent
- Granular consent: separate consent for separate purposes
- No pre-ticked boxes or bundled consent

**Code-level checks:**
- Consent collection UI/API exists
- Consent records stored with timestamp, purpose, version
- Withdrawal endpoint/mechanism exists and works
- Consent is checked before processing

**Detection patterns:**
```
consent|opt.in|agree|accept  → consent collection points
consent.*store|save.*consent|record.*consent  → consent storage
withdraw|revoke|opt.out  → withdrawal mechanism
consent.*check|has.consent|is.consented  → consent verification
purpose|legal.basis  → purpose tracking
```

---

## Articles 15-20 — Data Subject Rights

### Art. 15: Right of Access

User can request all data held about them.

**Code-level checks:**
- Data export endpoint exists (e.g., `GET /api/user/data`)
- Export includes all data sources (DB, files, logs, third-party)
- Response is in a readable format

### Art. 16: Right to Rectification

User can correct inaccurate data.

**Code-level checks:**
- Profile update endpoints exist for all user data fields
- Updates propagate to all systems holding the data

### Art. 17: Right to Erasure ("Right to Be Forgotten")

User can request deletion of their data.

**Code-level checks:**
- Deletion endpoint exists (e.g., `DELETE /api/user/account`)
- Deletion covers all data stores (DB, backups, caches, logs, third-party)
- Soft delete vs. hard delete: soft delete must still anonymize PII
- Cascade deletion for related records

### Art. 20: Right to Data Portability

User can export data in a structured, machine-readable format.

**Code-level checks:**
- Export in standard format (JSON, CSV)
- Includes all user-provided data
- Available programmatically (API endpoint)

**Detection patterns:**
```
export|download.*data|data.portability  → export feature
delete.*account|erase|remove.*user|anonymize  → deletion feature
rectif|update.*profile|correct  → correction feature
/api/user/data|/api/me|/account/export  → data access endpoints
cascade|related.*delete|dependent  → cascade deletion
```

---

## Article 25 — Data Protection by Design and by Default

### By Design

Security and privacy built into the system from the start.

**Code-level checks:**
- Encryption used by default for sensitive data
- Access controls implemented at the architectural level
- Privacy-preserving defaults (no tracking without consent)
- Pseudonymization where possible

### By Default

Only data necessary for the specific purpose is processed.

**Code-level checks:**
- Default settings are privacy-preserving
- Optional data collection is opt-in, not opt-out
- API responses return minimum necessary fields
- Data sharing disabled by default

**Detection patterns:**
```
default.*public|default.*share|default.*visible  → check if privacy-first
opt.out  → should be opt-in instead
pseudonym|anonymize|hash.*identifier  → privacy techniques
```

---

## Article 32 — Security of Processing

### Technical Measures Required

**Encryption:**
- Personal data encrypted at rest (AES-256 or equivalent)
- Personal data encrypted in transit (TLS 1.2+)
- Encryption keys properly managed

**Pseudonymization:**
- Identifiers replaced with pseudonyms where possible
- Mapping table secured separately
- Processing possible without re-identification

**Resilience:**
- System can recover from incidents
- Backups exist and are encrypted
- Disaster recovery mechanisms

**Detection patterns:**
```
encrypt|AES|cipher  → encryption implementation
pseudonym|tokenize|hash.*pii  → pseudonymization
backup|recover|restore|replicate  → resilience
bcrypt|argon2|scrypt  → password protection
```

**Code-level checks:**
- Verify PII fields are encrypted at rest
- Verify TLS on all data transmission
- Check backup encryption configuration
- Verify access to personal data is logged

---

## Articles 33-34 — Breach Notification

### Detection and Notification Mechanisms

**Required capabilities:**
- Detect unauthorized access to personal data
- Notify supervisory authority within 72 hours
- Notify affected individuals without undue delay (if high risk)
- Document all breaches regardless of notification requirement

**Code-level checks:**
- Audit logging on all personal data access
- Anomaly detection or alerting on unusual access patterns
- Breach notification workflow/mechanism exists
- Incident log/registry exists

**Detection patterns:**
```
breach|incident|unauthorized.access  → breach handling
notify|notification|alert.*security  → notification mechanism
audit.log|access.log|security.event  → logging
anomaly|unusual|suspicious  → detection
72.hour|supervisory.authority  → compliance process
```

---

## Code-Level Audit Checklist

| Area | What to Search | Expected Finding |
|------|---------------|-----------------|
| Consent collection | Forms/APIs collecting consent | Granular, informed, recordable |
| Consent storage | Consent data model | Timestamp, purpose, version, user ID |
| Consent withdrawal | Withdrawal endpoint | Easy to withdraw, revokes processing |
| Data export | Export endpoint | Returns all user data in JSON/CSV |
| Data deletion | Deletion endpoint | Hard delete or full anonymization |
| Data portability | Export format | Standard machine-readable format |
| Encryption at rest | DB/storage config, field encryption | PII encrypted with AES-256 |
| Encryption in transit | TLS config, API URLs | TLS 1.2+ on all connections |
| Data minimization | API responses, DB queries | Only necessary fields collected/returned |
| Retention | Cleanup jobs, TTL settings | Automated deletion/anonymization |
| Access logging | Audit middleware | All PII access logged |
| Breach detection | Alerting config | Anomaly alerts on data access |
| Privacy defaults | Default settings | Opt-in for data sharing/tracking |
| Pseudonymization | Identifier handling | Pseudonyms used where possible |
