# Pipeline: integration-verify

Full verification pipeline for testing that implementation and infrastructure work together in a local Docker Compose environment.

## Flow

```
verify:provision --> verify:instrument --> verify:scenario
    --> verify:execute --> verify:diagnose --> verify:report
```

## Steps

| # | Skill | Agent | Depends on |
|---|-------|-------|------------|
| 0 | verify | provision | — |
| 1 | verify | instrument | 0 |
| 2 | verify | scenario | 1 |
| 3 | verify | execute | 2 |
| 4 | verify | diagnose | 3 |
| 5 | verify | report | 4 |

## Prerequisites

Requires approved artifacts from:
- `impl` — code structure, build commands, environment config
- `devops` — IaC, observability config, runbooks

## When to use

- "Verify the implementation", "Does it work?", "Run integration tests"
- After impl and devops are complete
- Before declaring the system ready for deployment

## Dialogue expectations

Mostly automatic. Escalation only when:
- Docker environment fails to start
- Critical test failures that need user judgment on root cause
- Upstream artifact contradictions discovered during execution
