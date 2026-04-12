# Pipeline: quick-review

Lightweight review pipeline that runs review stages across re, arch, and impl. Does not create new artifacts — reviews existing ones.

## Flow

```
re:review --> arch:review --> impl:review
```

## Steps

| # | Skill | Agent | Depends on |
|---|-------|-------|------------|
| 0 | re | review | — |
| 1 | arch | review | 0 |
| 2 | impl | review | 1 |

## When to use

- Quick sanity check across the pipeline
- "Review what we have so far"
- Before a formal release or handoff

## Prerequisites

Existing artifacts must be present for each skill being reviewed. If a skill has no artifacts, its review step is automatically skipped.

## Dialogue expectations

Each review stage may surface findings that need user judgment. Expect moderate relay activity.
