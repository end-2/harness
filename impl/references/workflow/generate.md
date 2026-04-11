# Workflow — Stage 1: generate

## Role

Read the four approved Arch artifacts and produce (a) actual source code under the project tree and (b) drafts of the four Impl section artifacts (Implementation Map, Code Structure, Implementation Decisions, Implementation Guide). This is the only stage in Impl that *creates* new files.

## Inputs

- `ARCH-DEC-*` — structural decisions (patterns, layering, boundaries). Mandatory for code shape.
- `ARCH-COMP-*` — components with `name`, `responsibility`, `type`, `interfaces`, `dependencies`, `re_refs`. Authoritative boundary.
- `ARCH-TECH-*` — technology stack with `category`, `choice`, `constraint_ref`. The set of technologies you may use.
- `ARCH-DIAG-*` — diagrams (C4, sequence, data-flow). Method-call order and data movement.
- The existing codebase (if any) as a snapshot to auto-detect conventions.

## Arch → code mapping

Read [../contracts/arch-input-contract.md](../contracts/arch-input-contract.md) for the full table. Quick reference:

| Arch field | Code-generation directive |
|------------|---------------------------|
| `component.name` + `component.type` | Module / package name and kind (library, service, CLI, worker) |
| `component.responsibility` | Single-responsibility boundary of the module |
| `component.interfaces` | Interface / type / trait definitions, API contract stubs |
| `component.dependencies` | Import graph, directional; forbid cycles not present in Arch |
| `decision.decision` | Code-level pattern (layered, hexagonal, event-driven handlers) |
| `decision.trade_offs` | Preserved as inline comments at the point of enforcement |
| `tech-stack.choice` | Concrete language / framework / library selection |
| `diagram.sequence` | Method-call ordering inside the relevant handlers |
| `diagram.data-flow` | Data transformation pipeline wiring |

## Codebase context auto-detection

**Do not ask the user about conventions — detect them.** Sources of evidence, in priority order:

1. **Existing source files** (if any): naming style (camelCase vs snake_case), file organisation, import style, docstring conventions, error-handling pattern, logging style.
2. **Dependency manifests**: `package.json`, `pnpm-lock.yaml`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`. The set of already-adopted libraries tells you what the rest of the system assumes.
3. **Formatter / linter config**: `.prettierrc`, `.eslintrc`, `ruff.toml`, `black` config, `rustfmt.toml`, `.editorconfig`. Follow it.
4. **Build / CI**: `Dockerfile`, `Makefile`, `.github/workflows/*.yml`, `justfile`. They constrain what your build must produce.
5. **Stack idioms** (fallback when no existing code): Go → returned errors + context.Context, Rust → `Result<T, E>` + thiserror, Java → checked/unchecked exceptions + SLF4J, Python → exceptions + structlog, Node/TS → async/await + pino.

Record the detected convention set in the Implementation Guide `conventions` section so downstream skills can see what you enforced.

## Output — four sections

Create the four Impl sections in order. Each section is a metadata + markdown pair produced by `artifact.py init`.

### 1. Implementation Map

For each `ARCH-COMP-*`, create one `IM-xxx` entry with `component_ref`, `module_path`, `entry_point`, `internal_structure` (2–3 level tree), and `interfaces_implemented`. Link upstream to the Arch component:

```
python ${SKILL_DIR}/scripts/artifact.py link <impl-map-id> --upstream ARCH-COMP-001
```

### 2. Code Structure

Capture `project_root`, `directory_layout`, `module_dependencies` (edge list + a Mermaid graph that matches `ARCH-COMP-*.dependencies`), `external_dependencies` (name, version, purpose, `tech_stack_ref`), `build_config`, `environment_config`.

### 3. Implementation Decisions

Start empty. `generate` only writes IDRs for **code-level** choices that are *not* settled in Arch (e.g. "use a repository per aggregate" when Arch says "hexagonal" but does not name the pattern). Arch-mandated patterns are recorded in Stage 2.

### 4. Implementation Guide

Draft `prerequisites`, `setup_steps`, `build_commands`, `run_commands`, `conventions` (from detection), `extension_points` (tied to Implementation Map module paths).

## Writing source code

The actual source code under the project tree is written with Write / Edit. It is **not** tracked by `artifact.py`. However:

- The import graph of the source **must** match the Code Structure section. If you find yourself wanting a new edge, update Code Structure first, then write the code.
- Every file you create that corresponds to an Arch component must be reachable from some Implementation Map entry. Unmapped files are a smell — either add them to the map or remove them.

## Script sequence

For each of the four sections:

1. `artifact.py init --section <name>` → returns the new `<id>`.
2. Fill the `.md` file via Edit. Never Edit `.meta.yaml`.
3. Incrementally: `artifact.py set-progress <id> --completed N --total M`.
4. Add traceability as you go: `artifact.py link <id> --upstream <ARCH-*>` and (when both artifacts exist locally) `--downstream <downstream-id>`.
5. When the section draft is complete: `artifact.py set-phase <id> in_review`.

## Escalation

Escalate to the user **only** when:

- An Arch interface cannot be realised in the chosen technology (e.g. Arch specifies a streaming response on a library that does not support it).
- The existing codebase and an Arch decision are in unresolvable conflict (e.g. Arch mandates a framework that is incompatible with the current build toolchain).
- A `hard` RE constraint (via `constraint_ref`) would be violated by any realisation of the Arch decision.

Do **not** escalate for:

- Convention choices (detect or fall back to stack idioms).
- Dependency version selection (pick the latest stable compatible release).
- Small code-level trade-offs (record as an IDR in Stage 2).
