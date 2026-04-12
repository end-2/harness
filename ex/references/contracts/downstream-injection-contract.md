# Downstream Injection Contract

Ex produces 4-section artifacts and **pushes** them as context into downstream skills. This document specifies which sections feed which skills, what each skill expects to find, and how the injection works.

## Injection model

Unlike other Harness skills that **pull** from upstream artifacts, Ex **pushes** its output into downstream skills. This means:

1. Ex registers downstream refs via `artifact.py link-defaults <id>` (or explicit `link` calls for exceptional extra refs)
2. When a downstream skill runs, it checks for Ex artifacts in the project's artifacts directory
3. If found, the downstream skill loads the relevant sections as context before its own analysis

## Section-to-skill mapping

```
Structure Map (EX-STR-*)
  -> re   : domain context, existing feature inventory
  -> impl : directory conventions to follow
  -> qa   : test entry points, existing test structure

Tech Stack (EX-TS-*)
  -> arch : existing technology constraints for design decisions
  -> impl : language idioms, framework conventions to follow
  -> qa   : test framework selection context

Components (EX-CMP-*)
  -> arch : existing component boundaries for architecture review
  -> impl : existing module structure to extend (not duplicate)
  -> sec  : attack surface identification (API surfaces, external interfaces)

Architecture (EX-ARC-*)
  -> arch : existing architecture as a starting constraint (not blank-slate)
  -> re   : system-level constraints for requirements
  -> qa   : existing test patterns to build upon
```

## What each downstream skill expects

### re (Requirements Engineering)

**From Structure Map**: existing directory layout hints at existing features and domain concepts. RE uses this to avoid requiring features that already exist and to understand the vocabulary of the existing system.

**From Architecture**: system-level constraints (e.g., "this is a monolith, so microservice-style requirements would require a migration") inform what is feasible within the current system.

**Key fields consumed**:
- `structure-map.entry_points` — what the system already does
- `structure-map.directory_conventions` — domain vocabulary
- `architecture.architecture_style` — feasibility constraints
- `architecture.communication_patterns` — integration constraints

### arch (Architecture)

**From Tech Stack**: existing technology choices are constraints, not suggestions. If the project uses PostgreSQL and Prisma, arch should not propose switching to MongoDB unless explicitly asked.

**From Components**: existing component boundaries are the starting point. Arch reviews or extends them — it does not redesign from scratch.

**From Architecture**: the existing architecture style is a given. Arch works within it or explicitly proposes changes with migration paths.

**Key fields consumed**:
- `tech-stack.technologies` — technology constraints
- `components.components` — existing boundaries
- `components.api_surface` — existing interfaces
- `architecture.architecture_style` — starting architecture
- `architecture.layer_structure` — existing layers

### impl (Implementation)

**From Structure Map**: directory conventions tell impl where to place new files and how to name them.

**From Tech Stack**: language version and framework tell impl which idioms and APIs to use.

**From Components**: existing module structure tells impl where new code belongs and what existing modules to import (not duplicate).

**Key fields consumed**:
- `structure-map.directory_conventions` — placement rules
- `structure-map.config_files` — build/lint config to respect
- `tech-stack.technologies` (filtered: language, framework) — coding conventions
- `components.components` — existing modules to integrate with

### qa (Quality Assurance)

**From Structure Map**: existing test directories and test entry points tell qa where tests live and what test structure to follow.

**From Tech Stack**: test framework selection is already made — qa uses it rather than proposing a new one.

**From Architecture**: existing test patterns (unit/integration/e2e split, coverage config) are the baseline.

**Key fields consumed**:
- `structure-map.entry_points` — what to test
- `structure-map.file_count.test` — existing test coverage level
- `tech-stack.technologies` (filtered: test) — test framework
- `architecture.test_patterns` — existing test strategy

### sec (Security)

**From Components**: API surfaces and external interfaces define the attack surface. Components with `api_surface` entries are the primary audit targets.

**From Architecture**: communication patterns reveal data flow paths. Cross-cutting concerns (especially auth, validation) show what security measures exist.

**Key fields consumed**:
- `components.api_surface` — attack surface
- `components.dependencies_external` — supply chain scope
- `architecture.communication_patterns` — data flow
- `architecture.cross_cutting_concerns` (filtered: auth, validation) — existing security controls
- `architecture.data_stores` — data at rest

## Injection lifecycle

1. **Ex runs** → creates 4 artifacts → registers section-specific downstream refs
2. **Downstream skill starts** → Orch passes Ex's artifact directory explicitly in orchestrated runs, or the downstream skill reads Ex's standalone output directory when run directly
3. **Downstream skill loads** the relevant `.md` files as context
4. **Downstream skill proceeds** with its own analysis, informed by Ex context

If Ex artifacts are absent, downstream skills proceed without codebase context (their default behavior). Ex context is always additive — it never blocks downstream skills from running.
