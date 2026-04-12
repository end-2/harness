# Pipeline: full-sdlc-existing

Full SDLC for an **existing** codebase. Prepends the `ex` skill (4-stage exploration) to provide codebase context for all downstream skills.

## Flow

```
ex:scan --> ex:detect --> ex:analyze --> ex:map
    --> re:elicit --> re:analyze --> re:spec
    --> arch:design --> impl:generate
    --> [qa:generate, sec:audit, devops:pipeline]  (parallel)
    --> verify:provision --> verify:execute
```

## Steps

| # | Skill | Agent | Depends on | Parallel group |
|---|-------|-------|------------|----------------|
| 0 | ex | scan | — | — |
| 1 | ex | detect | 0 | — |
| 2 | ex | analyze | 1 | — |
| 3 | ex | map | 2 | — |
| 4 | re | elicit | 3 | — |
| 5 | re | analyze | 4 | — |
| 6 | re | spec | 5 | — |
| 7 | arch | design | 6 | — |
| 8 | impl | generate | 7 | — |
| 9 | qa | generate | 8 | post-impl |
| 10 | sec | audit | 8 | post-impl |
| 11 | devops | pipeline | 8 | post-impl |
| 12 | verify | provision | 9,10,11 | — |
| 13 | verify | execute | 12 | — |

## Key difference from `full-sdlc`

The `ex` exploration phase (steps 0-3) runs automatically without user interaction. It produces a 4-section codebase analysis that downstream skills use as context:

- **EX structure map** → informs arch about existing architecture
- **EX tech stack** → informs impl about existing technologies
- **EX component relations** → informs arch about existing component boundaries
- **EX architecture inference** → provides arch with the current design patterns

This context prevents downstream skills from proposing changes that conflict with the existing codebase.

## Gating rules

- Steps 0-3 (ex): Automatic execution, no approval gating between ex stages
- Steps 4-6 (re): Each requires previous approved. re:elicit receives ex artifacts as context.
- Step 7 (arch): Receives both ex and re artifacts
- Remaining steps: Same gating as `full-sdlc`
