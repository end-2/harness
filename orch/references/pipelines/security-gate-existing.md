# Pipeline: security-gate-existing

Security review for an **existing** codebase. Prepends `ex` exploration to understand the codebase before auditing.

## Flow

```
ex:scan --> ex:detect --> ex:analyze --> ex:map
    --> sec:threat-model --> sec:audit --> sec:compliance
```

## Steps

| # | Skill | Agent | Depends on |
|---|-------|-------|------------|
| 0 | ex | scan | — |
| 1 | ex | detect | 0 |
| 2 | ex | analyze | 1 |
| 3 | ex | map | 2 |
| 4 | sec | threat-model | 3 |
| 5 | sec | audit | 4 |
| 6 | sec | compliance | 5 |

## Key difference from `security-gate`

The `ex` exploration provides the security skill with:
- Component boundaries and attack surface (from structure map)
- Technology stack and known vulnerability profiles (from tech stack detection)
- Data flow paths for threat modelling (from component relations)
- Existing security patterns or anti-patterns (from architecture inference)
