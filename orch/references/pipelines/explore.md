# Pipeline: explore

Codebase exploration pipeline. Runs all four `ex` stages to produce a comprehensive analysis of the existing codebase.

## Flow

```
ex:scan --> ex:detect --> ex:analyze --> ex:map
```

## Steps

| # | Skill | Agent | Depends on |
|---|-------|-------|------------|
| 0 | ex | scan | — |
| 1 | ex | detect | 0 |
| 2 | ex | analyze | 1 |
| 3 | ex | map | 2 |

## When to use

- "Explore this codebase", "Analyse this project"
- Understanding an unfamiliar project before making changes
- Generating documentation for an undocumented codebase

## Output

Four EX artifacts:
1. **Structure map** — directory tree, entry points, build system
2. **Tech stack** — languages, frameworks, dependencies, versions
3. **Component relations** — module boundaries, imports, API contracts, data flow
4. **Architecture inference** — design patterns, architectural style, quality attribute observations

## Dialogue expectations

Fully automatic — no user interaction expected. The `ex` skill analyses the codebase by reading files and running tools.
