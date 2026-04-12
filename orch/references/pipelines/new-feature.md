# Pipeline: new-feature

Lightweight pipeline for adding a **new feature** to a new system. Skips security, devops, and verification for faster iteration.

## Flow

```
re:elicit --> re:spec --> arch:design --> impl:generate --> qa:generate
```

## Steps

| # | Skill | Agent | Depends on |
|---|-------|-------|------------|
| 0 | re | elicit | — |
| 1 | re | spec | 0 |
| 2 | arch | design | 1 |
| 3 | impl | generate | 2 |
| 4 | qa | generate | 3 |

## When to use

- Adding a well-scoped feature that doesn't need security review or infrastructure changes
- Rapid prototyping where verification can happen manually
- Features where the deployment model is already established

## What's skipped vs full-sdlc

- `re:analyze` — skipped, go directly from elicit to spec for speed
- `sec`, `devops`, `verify` — skipped entirely
- No parallel group — linear execution only
