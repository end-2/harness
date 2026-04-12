# Pipeline: full-sdlc

Full software development lifecycle for a **new** system (no existing codebase).

## Flow

```
re:elicit --> re:analyze --> re:spec --> arch:design --> impl:generate
    --> [qa:generate, sec:audit, devops:pipeline]  (parallel)
    --> verify:provision --> verify:execute
```

## Steps

| # | Skill | Agent | Depends on | Parallel group |
|---|-------|-------|------------|----------------|
| 0 | re | elicit | — | — |
| 1 | re | analyze | 0 | — |
| 2 | re | spec | 1 | — |
| 3 | arch | design | 2 | — |
| 4 | impl | generate | 3 | — |
| 5 | qa | generate | 4 | post-impl |
| 6 | sec | audit | 4 | post-impl |
| 7 | devops | pipeline | 4 | post-impl |
| 8 | verify | provision | 5,6,7 | — |
| 9 | verify | execute | 8 | — |

## Dialogue expectations

- **re:elicit** (step 0): Heavy dialogue — requirement gathering with user. Multiple relay rounds expected.
- **re:analyze** (step 1): Moderate dialogue — conflict resolution, priority clarification.
- **re:spec** (step 2): Light dialogue — specification review and approval.
- **arch:design** (step 3): Heavy dialogue — technical context, architecture decisions.
- **impl:generate** (step 4): Minimal dialogue — largely automatic from arch artifacts.
- **qa/sec/devops** (steps 5-7): Minimal — automatic generation from upstream artifacts.
- **verify** (steps 8-9): Minimal — automatic environment setup and execution.

## Gating rules

- Steps 0-2 (re): Each step's artifacts must be in `approved` phase before the next starts
- Step 3 (arch): Requires all 3 RE artifacts approved
- Step 4 (impl): Requires all 4 ARCH artifacts approved
- Steps 5-7 (parallel): Require IMPL artifacts approved. All 3 must complete before step 8.
- Steps 8-9 (verify): Require QA + SEC + DEVOPS artifacts approved

## Typical duration

This is the longest pipeline. Expect significant user interaction time during re and arch stages. The parallel group (qa/sec/devops) saves time by running concurrently.
