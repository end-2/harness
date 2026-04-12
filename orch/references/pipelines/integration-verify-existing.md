# Pipeline: integration-verify-existing

Verification pipeline for an **existing** codebase. Prepends `ex` exploration to understand the codebase before attempting verification.

## Flow

```
ex:scan --> ex:detect --> ex:analyze --> ex:map
    --> verify:provision --> verify:instrument --> verify:scenario
    --> verify:execute --> verify:diagnose --> verify:report
```

## Steps

| # | Skill | Agent | Depends on |
|---|-------|-------|------------|
| 0 | ex | scan | — |
| 1 | ex | detect | 0 |
| 2 | ex | analyze | 1 |
| 3 | ex | map | 2 |
| 4 | verify | provision | 3 |
| 5 | verify | instrument | 4 |
| 6 | verify | scenario | 5 |
| 7 | verify | execute | 6 |
| 8 | verify | diagnose | 7 |
| 9 | verify | report | 8 |

## Key difference from `integration-verify`

When impl/devops artifacts don't exist (because the code was written outside the harness pipeline), the `ex` exploration provides:
- Build system and entry points (from structure map) → provision uses these to build containers
- External dependencies (from tech stack) → provision uses these for infrastructure services
- Component interfaces (from component relations) → scenario derives test cases from these
- Existing test patterns (from architecture inference) → scenario incorporates existing tests

This allows verification of codebases that weren't built through the harness pipeline.
