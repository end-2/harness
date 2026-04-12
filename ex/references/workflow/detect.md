# Stage 2 — Detect: Detailed Behavior Rules

## Purpose

Identify the complete technology stack used by the project — languages, frameworks, databases, build tools, test frameworks, CI/CD, and infrastructure — by analyzing manifest files and code patterns. Every detection must include evidence: which file and which pattern led to the conclusion.

## Prerequisites

Stage 1 (scan) must be complete. This stage consumes:
- Config files list (manifest locations, file roles)
- File classification map (source files by extension → language hints)
- Entry points (help distinguish primary vs auxiliary languages)

## Execution sequence

1. **Detect languages** — count source files by extension to determine primary and secondary languages. The language with the most source files is "primary"; others are "secondary". Record version if available from manifests (e.g., `"engines": {"node": ">=18"}` in `package.json`, `go 1.21` in `go.mod`, `python_requires` in `pyproject.toml`).

2. **Parse manifest files** — for each manifest identified by Stage 1, extract:
   - Direct dependencies with versions
   - Dev dependencies with versions
   - Dependency groups/extras (Python), optional dependencies
   - Scripts/tasks defined (npm scripts, Makefile targets, Cargo aliases)

3. **Detect frameworks** — match dependencies and code patterns against the signature catalog in `references/detect-patterns.md`. For each framework detected, record:
   - Which manifest listed it (dependency evidence)
   - Which code pattern confirmed it (import/config evidence)
   - Its role in the project (web framework, ORM, state management, etc.)

4. **Detect databases** — look for:
   - ORM configuration: `prisma/schema.prisma`, `ormconfig.*`, `alembic/`, `typeorm`, `sqlalchemy`, `gorm`
   - Migration directories: `migrations/`, `db/migrate/`, `prisma/migrations/`
   - Connection strings: `DATABASE_URL`, `MONGO_URI`, `REDIS_URL` in `.env*` files
   - Database driver dependencies in manifests

5. **Detect test infrastructure** — look for:
   - Test framework configs: `jest.config.*`, `vitest.config.*`, `pytest.ini`, `conftest.py`, `.rspec`
   - Test runner dependencies in manifests
   - Test directories and file patterns from Stage 1
   - Coverage configuration: `nyc`, `istanbul`, `coverage`, `.coveragerc`, `codecov.yml`

6. **Detect build / development tools** — look for:
   - Bundlers: webpack, vite, rollup, esbuild, parcel configs
   - Compilers: TypeScript (`tsconfig.json`), Babel, SWC
   - Linters/formatters: ESLint, Prettier, Biome, Ruff, golangci-lint, Clippy
   - Task runners: npm scripts, Makefile, Just, Taskfile

7. **Detect CI/CD and infrastructure** — look for:
   - CI configs: `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/config.yml`
   - Container: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
   - Orchestration: Kubernetes manifests (`k8s/`, `*.yaml` with `apiVersion`), Helm charts
   - IaC: Terraform (`.tf`), CloudFormation, Pulumi, CDK
   - Cloud SDK configs

8. **Assign IDs and compile** — assign sequential IDs (`TS-001`, `TS-002`, ...) to each detected technology. Group by category. Note relationships between technologies (e.g., "Next.js uses React" is implicit but worth noting for downstream context).

## Evidence requirements

Every detection must include:
- **File evidence**: the specific file where the technology was found (e.g., `package.json`, `Dockerfile`)
- **Pattern evidence**: what in that file confirmed the detection (e.g., `"dependencies.next": "14.0.0"`, `FROM node:18-alpine`)
- **Confidence note** (optional): if the detection is uncertain (e.g., a dependency is listed but never imported), mark it as "inferred from manifest, not confirmed in code"

## Lite mode behavior

In lite mode, the detection process is the same, but the output is condensed:
- Group minor dev tools together instead of listing each one
- Skip detailed version reporting for secondary tools
- Focus evidence on the most important technologies (primary language, main framework, database)

## Output

Pass the following to Stage 3:
- Technology list: each entry with `{id, category, name, version, evidence, role, config_location}`
- Technology relationships: notable connections between detected technologies
- Manifest summaries: parsed dependency lists for import analysis in Stage 3

## Script usage

No `artifact.py` calls in this stage. Detection results are held in working memory. Artifact creation happens in Stage 4 (map). All metadata updates go through `${SKILL_DIR}/scripts/artifact.py` — never edit `.meta.yaml` files directly.
