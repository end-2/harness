# Stage 3 — Analyze: Detailed Behavior Rules

## Purpose

Build a module dependency graph from import statements, infer component boundaries, identify API surfaces, and determine the architectural style of the codebase. This is the deepest analytical stage — it turns raw file-level data into structural understanding.

## Prerequisites

Stages 1 (scan) and 2 (detect) must be complete. This stage consumes:
- File classification map and directory tree (from scan)
- Technology list and manifest summaries (from detect)
- Depth mode verdict (lite/heavy)

## Lite mode: abbreviated analysis

In lite mode, **skip import analysis and architecture inference entirely**. Instead:

1. Infer components from top-level directories (each top-level directory under `src/` or project root = one component)
2. Assign types based on directory naming conventions (`api/` -> handler, `models/` -> model, `utils/` -> util, `lib/` -> library, `services/` -> service, `test*/` -> test)
3. List external dependencies from manifests (already parsed in Stage 2)
4. Skip: import graph, circular dependency detection, architecture style inference, cross-cutting concern analysis
5. Output a simplified component list and skip directly to Stage 4

The rest of this document describes **heavy mode** behavior.

## Heavy mode execution sequence

### 1. Parse imports

For each source file, extract import/require/use statements using language-appropriate patterns:

| Language | Import patterns |
|----------|----------------|
| TypeScript/JavaScript | `import ... from '...'`, `import('...')`, `require('...')`, `export ... from '...'` |
| Python | `import ...`, `from ... import ...` |
| Go | `import (...)` block, `import "..."` |
| Java | `import ...;`, `import static ...;` |
| Rust | `use ...;`, `mod ...;`, `extern crate ...;` |
| Ruby | `require '...'`, `require_relative '...'` |
| PHP | `use ...;`, `require ...`, `include ...` |
| C/C++ | `#include "..."`, `#include <...>` |

Classify each import as:
- **Internal**: resolves to a file within the project (relative paths, aliases that map to project paths)
- **External**: resolves to a dependency in `node_modules`, site-packages, or similar

Build an adjacency list: `file A -> [file B, file C, ...]` for internal imports.

### 2. Infer component boundaries

Group files into components using these heuristics (see `references/analyze-heuristics.md` for full details):

1. **Directory-based grouping**: files in the same directory or immediate subdirectories form a candidate component
2. **Cohesion analysis**: files that import each other heavily belong to the same component
3. **Coupling analysis**: groups with few cross-boundary imports are good component boundaries
4. **Naming conventions**: directories named `features/`, `modules/`, `packages/`, `domains/` usually contain explicit component boundaries
5. **Package boundaries**: `package.json` workspaces, Go modules, Cargo workspace members

For each component, determine:
- **Name**: derived from directory name or package name
- **Path**: filesystem location
- **Type**: `service` / `library` / `handler` / `model` / `config` / `util` / `test`
- **Responsibility**: inferred from exported symbols, file names, and directory role
- **Internal dependencies**: which other components this one imports from
- **External dependencies**: which external packages this component uses
- **Dependents**: which components import from this one (reverse lookup)

### 3. Identify API surfaces

Scan for patterns that expose external interfaces:

| Pattern | Detection method |
|---------|-----------------|
| HTTP routes | Express `app.get/post/...`, Koa router, Flask `@app.route`, Django `urlpatterns`, Gin `router.GET/POST`, Spring `@RequestMapping` |
| gRPC services | `.proto` files with `service` definitions, generated stubs |
| GraphQL | Schema definitions (`.graphql` files), resolver patterns |
| WebSocket | `ws` / `socket.io` setup patterns |
| CLI commands | `commander`, `cobra`, `click`, `argparse` command definitions |
| Event handlers | Message queue consumers, event bus subscribers, cron job definitions |
| Exports (library) | Public module exports that constitute the library's API |

### 4. Detect design patterns

Look for structural patterns within components:

| Pattern | Signals |
|---------|---------|
| Repository | Classes/modules that abstract data access behind an interface |
| Factory | Functions/classes that create instances based on configuration |
| Observer/Event | Event emitter/listener patterns, pub/sub |
| Middleware | Chain-of-responsibility patterns in request handling |
| Singleton | Module-level instances, `getInstance()` patterns |
| Strategy | Interface implementations selected at runtime |
| Dependency Injection | Constructor injection, DI container configuration |
| MVC/MVP/MVVM | Clear separation of model/view/controller layers |

### 5. Infer architecture style

Match the overall structure against known architectural patterns (see `references/analyze-heuristics.md`):

| Style | Signals |
|-------|---------|
| **Monolithic** | Single deployment unit, shared database, no service boundaries |
| **Modular monolith** | Single deployment but clear module boundaries with defined interfaces |
| **Microservices** | Multiple `Dockerfile`s, separate `package.json`/`go.mod` per service, API gateway patterns |
| **Serverless** | Lambda/Cloud Functions config, `serverless.yml`, event-driven handlers |
| **Layered** | Clear presentation -> business -> data layers with one-way dependencies |
| **Hexagonal** | Ports/adapters pattern, domain core with no external dependencies |
| **Event-driven** | Message queues, event sourcing, CQRS patterns |

Report the style with confidence level (high/medium/low) and the specific evidence.

### 6. Detect cross-cutting concerns

Identify concerns that span multiple components:

- **Authentication/Authorization**: auth middleware, JWT handling, OAuth configs, RBAC
- **Logging**: logger configuration, structured logging, log levels
- **Error handling**: global error handlers, error middleware, custom error classes
- **Validation**: input validation libraries, schema validation, request validation
- **Caching**: cache configuration, Redis usage for caching, memoization
- **Monitoring**: APM integration, metrics collection, health checks

### 7. Detect circular dependencies

Walk the dependency graph and find cycles. Report each cycle with:
- The components involved (e.g., `CM-001 -> CM-003 -> CM-005 -> CM-001`)
- The specific files creating the cycle
- Severity assessment (tight coupling vs. loose/indirect cycle)

## Output

Pass the following to Stage 4:
- Component list: each with `{id, name, path, type, responsibility, deps_internal, deps_external, dependents, api_surface, patterns}`
- Architecture style inference: `{style, confidence, evidence}`
- Layer structure (if detected)
- Communication patterns
- Cross-cutting concerns
- Circular dependency warnings

## Script usage

No `artifact.py` calls in this stage. Analysis results are held in working memory. Artifact creation happens in Stage 4 (map). All metadata updates go through `${SKILL_DIR}/scripts/artifact.py` — never edit `.meta.yaml` files directly.
