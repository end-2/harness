# Pipeline: security-gate

Focused security review pipeline. Runs threat modelling, vulnerability audit, and compliance check.

## Flow

```
sec:threat-model --> sec:audit --> sec:compliance
```

## Steps

| # | Skill | Agent | Depends on |
|---|-------|-------|------------|
| 0 | sec | threat-model | — |
| 1 | sec | audit | 0 |
| 2 | sec | compliance | 1 |

## When to use

- Pre-release security gate
- Security review required by process/policy
- User asks "check security", "security audit", "threat model"

## Dialogue expectations

- **sec:threat-model** (step 0): Moderate dialogue — risk acceptance decisions, asset identification
- **sec:audit** (step 1): Minimal dialogue — automated vulnerability scanning
- **sec:compliance** (step 2): Light dialogue — compliance framework selection if not specified
