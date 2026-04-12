# Pipeline: new-feature-existing

Add a new feature to an **existing** codebase. Prepends `ex` exploration for codebase context.

## Flow

```
ex:scan --> ex:detect --> ex:analyze --> ex:map
    --> re:elicit --> re:spec --> arch:design --> impl:generate --> qa:generate
```

## Steps

| # | Skill | Agent | Depends on |
|---|-------|-------|------------|
| 0 | ex | scan | — |
| 1 | ex | detect | 0 |
| 2 | ex | analyze | 1 |
| 3 | ex | map | 2 |
| 4 | re | elicit | 3 |
| 5 | re | spec | 4 |
| 6 | arch | design | 5 |
| 7 | impl | generate | 6 |
| 8 | qa | generate | 7 |

## When to use

- Adding a feature to a codebase where you need to understand the existing structure first
- The user says "add X to this project" or "I want a new feature for..."
- There are source files in the working directory

## Key difference from `new-feature`

Steps 0-3 run automatically to explore the existing codebase. The exploration results inform:
- `re:elicit` — what already exists, so requirements focus on the delta
- `arch:design` — existing architecture to extend rather than redesign
- `impl:generate` — existing code patterns to follow
