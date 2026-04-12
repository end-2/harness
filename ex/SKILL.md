---
name: ex
description: Automatically analyze an existing codebase to generate an LLM-optimized 4-section project map (Structure Map, Tech Stack, Components, Architecture Inference) and inject it as context into downstream skills (re/arch/impl/qa/sec). Use this skill whenever the user points at an existing project they want to understand, onboard onto, add features to, review architecturally, audit for security, or plan tests for — even if they do not explicitly say "explore" or "analyze".
---

# Ex — Codebase Exploration Skill

Ex is the reverse-engineering entry point of the Harness pipeline. While other skills (`re`, `arch`, `impl`, …) work **forward** from requirements, Ex works **backward** from code — extracting what already exists so that forward skills can build on it coherently.

Given a project root path, Ex automatically scans, detects, analyzes, and maps the codebase into a structured 4-section artifact that downstream skills consume directly. The user does not need to answer questions; the code itself is the single source of truth.

## Current state (injected at load)

!`python ${SKILL_DIR}/scripts/artifact.py validate`

The command above lists existing artifacts, their phase, approval state, and traceability integrity. Read it before deciding whether this run is a fresh start or a continuation.

## Pre-scan context

!`pwd`
!`test -d "$1" && echo "TARGET OK: $1" || echo "TARGET MISSING: $1"`
!`ls -la "$1" 2>/dev/null | head -30`
!`find "$1" -maxdepth 2 -type f \( -name "package.json" -o -name "go.mod" -o -name "Cargo.toml" -o -name "pyproject.toml" -o -name "requirements.txt" -o -name "pom.xml" -o -name "build.gradle" -o -name "Gemfile" \) 2>/dev/null`
!`git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null`

This pre-scan context warms the analysis — Stage 1 (scan) already knows manifest locations, directory depth, and git state before it begins.

## Input / output contract

**Input**: `$ARGUMENTS` — parsed as follows:

| Argument | Required | Description |
|----------|----------|-------------|
| `$1` (`project_root`) | Yes | Absolute or relative path to the target project root. Escalate immediately if absent or inaccessible. |
| `--depth lite\|heavy` | No | Force lightweight or heavyweight mode. Auto-detected if omitted. |
| `--budget N` | No | Target token count for the final output (default: 4000). |
| `--focus <path>` | No | Concentrate analysis on a specific subdirectory or component. |
| `--out <dir>` | No | Output directory for all 8 artifact files. Map this to `HARNESS_ARTIFACTS_DIR` (or pass `--artifacts-dir` to `artifact.py`) before any script call. Default: `${SKILL_DIR}/out/${HARNESS_RUN_ID\|SESSION_ID\|standalone}/` |
| `--exclude <glob,...>` | No | Additional exclusion patterns beyond `.gitignore` defaults. |

**Output**: four section artifacts, each stored as a YAML metadata file plus a Markdown document:

1. **Project Structure Map** — directory tree, file classification, entry points, config files.
2. **Technology Stack Detection** — languages, frameworks, databases, build tools, CI/CD, with evidence.
3. **Component Relationships** — modules, dependencies, API surfaces, design patterns.
4. **Architecture Inference** — architectural style, layer structure, communication patterns, cross-cutting concerns.

Each section is a pair `<section>.meta.yaml` + `<section>.md`. Metadata is the single source of truth for structured/tracking fields and is **only** modified through `scripts/artifact.py`. Markdown holds the human-readable body, edited directly within the scaffolding from `assets/templates/`.

Full schemas: read [references/schemas/section-schemas.md](references/schemas/section-schemas.md) and [references/schemas/meta-schema.md](references/schemas/meta-schema.md) when you need the exact field list.

Downstream injection contract: read [references/contracts/downstream-injection-contract.md](references/contracts/downstream-injection-contract.md) to understand how each section feeds into `re`/`arch`/`impl`/`qa`/`sec`.

## Non-destructive analysis principle

Ex **never writes anything into the target project** (`project_root`). All outputs go to the `--out` directory. If `--out` is omitted, `artifact.py` falls back to `${SKILL_DIR}/out/${HARNESS_RUN_ID\|SESSION_ID\|standalone}/`, which keeps standalone runs outside the target repo. The target codebase is treated as strictly read-only.

## Adaptive depth

Project complexity is auto-detected to select the right analysis depth. A single SKILL.md handles both modes — no separate `ex-light`/`ex-heavy` split.

| Mode | Trigger | Output level |
|------|---------|--------------|
| **lite** | Files <= 50, 1 language, <= 1 framework, dir depth <= 3 | Directory tree + tech stack summary + entry point list + brief dependencies |
| **heavy** | Files > 50, or > 1 language, or > 1 framework, or dir depth > 3 | Full structure map + component relationship graph + API boundary analysis + dependency tree + pattern detection + architecture inference |

The user can override with `--depth lite` or `--depth heavy`. Full rules: [references/adaptive-depth.md](references/adaptive-depth.md).

## Workflow (four stages)

```
$1 = project_root
    |
    v
[1] scan   -> directory tree, file classification, entry points, complexity verdict
    |
    v
[2] detect -> tech stack identification from manifests + code patterns
    |
    v
[3] analyze -> import graph, component boundaries, architecture style inference
    |
    v
[4] map    -> integrate into 4-section output within token budget, register downstream refs
    |
    v
re / arch / impl / qa / sec receive context injection
```

Each stage has detailed behavior rules in `references/workflow/<stage>.md`. When you enter a stage, **Read that file first** and follow the rules there. This document only gives the summary.

The pipeline is **sequential** — each stage depends on the prior stage's output. However, unlike interactive skills (like `re`), Ex does not pause for user input between stages. It runs fully automatically and reports results at the end.

### Stage 1 — scan

Load [references/workflow/scan.md](references/workflow/scan.md).

- Build the directory tree respecting `.gitignore` and default exclusions (`node_modules`, `.git`, `__pycache__`, `dist`, `build`, `vendor`, `venv`).
- Classify files: source code, config, test, docs, build artifacts, static assets.
- Identify entry points: `main`, `index`, `app`, `server`, `bootstrap`, `cmd/` conventions.
- Map config files: `package.json`, `Makefile`, `Dockerfile`, `.env.example`, CI configs — tag each with its role.
- **Determine adaptive depth**: count files, languages, frameworks, directory depth. Decide lite vs heavy mode and record the reasoning.
- Produce a token-efficient tree representation: group repetitive patterns (e.g. `components/{Header,Footer,Nav,...12 more}/index.tsx`).

Output: directory tree (compressed), file classification, entry points, config files, depth mode verdict with evidence.

### Stage 2 — detect

Load [references/workflow/detect.md](references/workflow/detect.md) and [references/detect-patterns.md](references/detect-patterns.md).

- Parse manifest files identified in Stage 1 to extract dependencies and versions.
- Detect frameworks from dependency names + code patterns (imports, decorators, config files). See the detection signature catalog in `references/detect-patterns.md`.
- Detect databases (ORM configs, migration dirs, `DATABASE_URL`), test frameworks, build tools, CI/CD, containers.
- Record **evidence** for every detection: which file, which line/pattern led to the conclusion.

Output: categorized tech stack list with id, name, version, evidence, role, and config location.

### Stage 3 — analyze

Load [references/workflow/analyze.md](references/workflow/analyze.md) and [references/analyze-heuristics.md](references/analyze-heuristics.md).

- Parse import/require/use statements to build a module dependency graph.
- Infer component boundaries: high internal cohesion + low external coupling = boundary.
- Identify API surfaces: HTTP routes, gRPC services, event handlers, CLI commands.
- Infer architecture style: layered, hexagonal, monolithic, microservices, event-driven, serverless — using structural signatures.
- Detect cross-cutting concerns: auth middleware, logging, error handling patterns.
- Flag circular dependencies.
- **In lite mode**: skip import analysis and architecture inference; use directory-based classification only.

Output: component list (name, path, type, responsibility, internal/external deps, dependents, API surface, patterns), architecture style with evidence, cross-cutting concerns, circular dependency warnings.

### Stage 4 — map

Load [references/workflow/map.md](references/workflow/map.md) and [references/token-budget.md](references/token-budget.md).

- Integrate Stage 1-3 results into the final 4-section output: scan -> Structure Map, detect -> Tech Stack, analyze -> Components + Architecture.
- Apply token budget management (default 4000 tokens): prioritize entry points/APIs > component structure > tech stack > detailed dependencies.
- Compress repetitive patterns, group similar files, apply hierarchical detail levels.
- Verify cross-section consistency (IDs, paths referenced across sections must match).
- Create artifact pairs from templates:
  ```
  python ${SKILL_DIR}/scripts/artifact.py init --section structure-map
  python ${SKILL_DIR}/scripts/artifact.py init --section tech-stack
  python ${SKILL_DIR}/scripts/artifact.py init --section components
  python ${SKILL_DIR}/scripts/artifact.py init --section architecture
  ```
- Write the structured section payloads through the script before final validation:
  ```
  python ${SKILL_DIR}/scripts/artifact.py set-section <structure-id> --from /tmp/structure-map.yaml
  python ${SKILL_DIR}/scripts/artifact.py set-section <tech-id>      --from /tmp/tech-stack.yaml
  python ${SKILL_DIR}/scripts/artifact.py set-section <comp-id>      --from /tmp/components.yaml
  python ${SKILL_DIR}/scripts/artifact.py set-section <arch-id>      --from /tmp/architecture.yaml
  ```
  Each payload may be YAML or JSON. It can be the exact section fields or a wrapper object that contains them.
- Fill in the Markdown bodies — never touch `.meta.yaml` with Edit/Write.
- Update state through the script:
  ```
  python ${SKILL_DIR}/scripts/artifact.py set-progress <id>  --completed 1 --total 1
  python ${SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
  python ${SKILL_DIR}/scripts/artifact.py link-defaults <id>
  ```
- Report the absolute paths of all output files so the user can find them.

Output: finalized 4-section artifacts with downstream injection refs registered.

## Script contract (mandatory)

**Never edit `*.meta.yaml` files directly.** All state changes — phase, progress, structured section payloads, approval, traceability — must go through `scripts/artifact.py`. The script enforces:

- Schema validation (rejects unknown phases, missing fields).
- Section payload validation (rejects malformed `technologies`, `components`, `architecture`, etc.).
- `updated_at` auto-refresh.
- Legal phase transitions only (`draft -> in_review -> revising -> in_review -> approved -> superseded`).
- Bidirectional `upstream_refs` / `downstream_refs` integrity.
- An `approval.history` audit trail with timestamps.

Available subcommands:

| Command | Purpose |
|---------|---------|
| `artifact.py init --section <name>` | Create a metadata + markdown pair from templates. Returns the new `artifact_id`. |
| `artifact.py set-section <id> --from <path> \| --value <yaml-or-json>` | Replace the structured payload for that section (`structure-map`, `tech-stack`, `components`, or `architecture`) through the script. |
| `artifact.py set-phase <id> <phase>` | Transition phase. |
| `artifact.py set-progress <id> --completed N --total M` | Update progress. |
| `artifact.py approve <id> --approver <name> [--notes ...]` | Transition approval state. |
| `artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | Add a traceability reference. |
| `artifact.py link-defaults <id>` | Apply the documented downstream skill links for that section (`Structure Map -> re/impl/qa`, etc.). |
| `artifact.py show <id>` | Pretty-print the metadata. |
| `artifact.py list` | List all artifacts. |
| `artifact.py validate [<id>]` | Validate schema and traceability for one or all artifacts. |

The artifact directory resolves in this order: `--artifacts-dir`, then `HARNESS_ARTIFACTS_DIR`, then `${SKILL_DIR}/out/${HARNESS_RUN_ID\|SESSION_ID\|standalone}/`.

## Escalation rules

Ex runs fully automatically. Escalate to the user **only** when analysis is physically impossible:

- `project_root` does not exist or is inaccessible
- Filesystem contains only binary files (no parseable source)
- Symbolic link cycles prevent traversal
- No manifest files and no recognizable source code found

Full catalog: [references/escalation.md](references/escalation.md).

For everything else — ambiguous architecture, unclear patterns, mixed conventions — make your best inference and note the uncertainty in the evidence fields. Do not ask the user for clarification on code structure; the code is the authority.

## Reporting format

When all four sections are complete, present a summary to the user:

1. Which depth mode was selected and why
2. Key findings (dominant language, architecture style, notable patterns)
3. Absolute paths to all output files
4. Which downstream skills can now consume this context (with suggested next steps)

Keep the summary concise — the detailed analysis lives in the artifacts themselves.
