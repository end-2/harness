# CVSS v3.1 — Base Score Calculation Guide

Reference for scoring vulnerabilities using the Common Vulnerability Scoring System v3.1.

---

## Base Metric Groups

### Attack Vector (AV)

How the vulnerability is exploited.

| Value | Code | Description | Score Impact |
|-------|------|-------------|-------------|
| Network | N | Exploitable remotely over the network (e.g., internet) | Highest |
| Adjacent | A | Requires access to the local network segment (e.g., same WiFi, VLAN) | High |
| Local | L | Requires local system access (e.g., logged-in user, local app) | Medium |
| Physical | P | Requires physical access to the device | Lowest |

---

### Attack Complexity (AC)

Conditions beyond the attacker's control that must exist to exploit.

| Value | Code | Description |
|-------|------|-------------|
| Low | L | No special conditions. Works reliably against the target. |
| High | H | Requires specific conditions: race condition, non-default config, MITM position, etc. |

---

### Privileges Required (PR)

Level of privilege needed before exploitation.

| Value | Code | Description |
|-------|------|-------------|
| None | N | No authentication needed. Anonymous attack. |
| Low | L | Requires basic user-level access. |
| High | H | Requires admin/root-level access. |

Note: When Scope is Changed, PR has greater impact on the score.

---

### User Interaction (UI)

Whether a user other than the attacker must participate.

| Value | Code | Description |
|-------|------|-------------|
| None | N | No user interaction needed. Fully automated. |
| Required | R | Requires a user to perform some action (click link, open file). |

---

### Scope (S)

Whether exploiting the vulnerability impacts resources beyond its security scope.

| Value | Code | Description |
|-------|------|-------------|
| Unchanged | U | Impact limited to the vulnerable component. |
| Changed | C | Impact extends to other components (e.g., sandbox escape, hypervisor breakout). |

---

### Confidentiality Impact (C)

Impact on information confidentiality.

| Value | Code | Description |
|-------|------|-------------|
| None | N | No confidentiality impact. |
| Low | L | Some information disclosed, but attacker has no control over what. |
| High | H | Total information disclosure, or attacker can access any/all data. |

---

### Integrity Impact (I)

Impact on data integrity.

| Value | Code | Description |
|-------|------|-------------|
| None | N | No integrity impact. |
| Low | L | Limited data modification possible, but attacker has no control over consequence. |
| High | H | Complete loss of integrity; attacker can modify any data. |

---

### Availability Impact (A)

Impact on system availability.

| Value | Code | Description |
|-------|------|-------------|
| None | N | No availability impact. |
| Low | L | Degraded performance or partial availability loss. |
| High | H | Complete denial of service; resource is fully unavailable. |

---

## Score Ranges

| Score | Severity |
|-------|----------|
| 0.0 | None |
| 0.1 - 3.9 | Low |
| 4.0 - 6.9 | Medium |
| 7.0 - 8.9 | High |
| 9.0 - 10.0 | Critical |

---

## Vector String Format

```
CVSS:3.1/AV:<N|A|L|P>/AC:<L|H>/PR:<N|L|H>/UI:<N|R>/S:<U|C>/C:<N|L|H>/I:<N|L|H>/A:<N|L|H>
```

Example: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` = 9.8 Critical

---

## Common Scenarios with Example Scores

### Unauthenticated Remote Code Execution
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8 Critical
```
Network-accessible, no auth, no user interaction, full compromise.

### SQL Injection in Login Page
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N = 9.1 Critical
```
Data read/write but service stays up.

### Reflected XSS
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N = 6.1 Medium
```
Requires victim to click a link. Scope changed (browser context).

### Stored XSS in Admin Panel
```
CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N = 5.4 Medium
```
Requires low privileges to inject, victim interaction to trigger.

### SSRF to Internal Metadata
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N = 8.6 High
```
Can read internal resources across scope boundary.

### Local Privilege Escalation
```
CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H = 7.8 High
```
Requires local access and low privileges; full local compromise.

### Denial of Service via Resource Exhaustion
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H = 7.5 High
```
Remote, no auth, complete availability loss.

### Hardcoded API Key Exposure
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N = 7.5 High
```
Anyone can read the key and access the associated service.

### CSRF on Password Change
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:H/A:N = 6.5 Medium
```
Requires victim interaction; integrity impact only.

### Information Disclosure via Error Messages
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N = 5.3 Medium
```
Low confidentiality impact; aids further attacks.

### Path Traversal (Read Only)
```
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N = 6.5 Medium
```
Requires auth; can read arbitrary files.

### Weak Password Policy
```
CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N = 7.4 High
```
High complexity (requires brute force); leads to full account compromise.

---

## Scoring Decision Guide

When assigning a CVSS score, ask these questions in order:

1. **How is it reached?** Network (most web vulns) vs. Local vs. Physical → AV
2. **Are special conditions needed?** Race condition, non-default config → AC:H, otherwise AC:L
3. **Does the attacker need an account?** None/Low/High → PR
4. **Does a victim need to do something?** Click a link, open a file → UI:R
5. **Does the impact cross a security boundary?** Sandbox escape, affects other tenants → S:C
6. **What can the attacker read?** Nothing/Some/Everything → C
7. **What can the attacker modify?** Nothing/Some/Everything → I
8. **Can the attacker disrupt service?** No/Partially/Completely → A
