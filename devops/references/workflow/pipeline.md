# Workflow — Stage 3: CI/CD Pipeline

## Role

Generate CI/CD pipeline configuration from the Impl code structure and the IaC infrastructure output. The pipeline is the bridge between code changes and deployed infrastructure — it builds, tests, scans, and deploys every commit according to the rules established by Impl (what to build) and IaC (where to deploy). This stage produces the Pipeline Config artifact and optionally writes actual pipeline YAML files.

## Inputs

- **IMPL-CODE-\*** — code structure with `build_config`, `module_dependencies`, `external_dependencies`, `environment_config`, and `tech_stack_ref`. These drive build steps, caching, and secret management.
- **IMPL-GUIDE-\*** — implementation guide with `build_commands`, `run_commands`, `prerequisites`, `conventions`, and `extension_points`. These provide the literal commands the pipeline executes.
- **IMPL-MAP-\*** — implementation map with `module_path`, `entry_point`, and `component_ref`. Determines build targets and container entrypoints.
- **IaC output** (from Stage 2) — `DEVOPS-IAC-*` with `infrastructure_code.modules`, `environments`, and `provider`. Determines deploy targets and environment promotion chain.

Read [../contracts/impl-input-contract.md](../contracts/impl-input-contract.md) for the full Impl field mapping before beginning this stage.

## Impl field to pipeline action mapping

| Impl field | Pipeline action | Details |
|---|---|---|
| `IMPL-CODE-*.build_config.file` | Build stage steps | Identifies the build tool (Dockerfile, Makefile, package.json scripts). Becomes the primary build step. |
| `IMPL-CODE-*.module_dependencies` | Build order | Internal module dependencies determine parallel vs sequential build jobs. Dependencies that cross module boundaries require the dependent module to build first. |
| `IMPL-CODE-*.external_dependencies` | Cache key generation | Each lockfile (package-lock.json, go.sum, Cargo.lock, pnpm-lock.yaml) becomes a cache key. Cache invalidation: lockfile hash change triggers full reinstall. |
| `IMPL-CODE-*.environment_config` | Secret/env var injection | Sensitive entries map to secret store references (GitHub Secrets, Vault, AWS Secrets Manager). Non-sensitive entries become pipeline environment variables. |
| `IMPL-GUIDE-*.build_commands` | CI build step commands | Used **verbatim** as pipeline step commands. Wrap in platform syntax but do not alter the command itself. |
| `IMPL-GUIDE-*.run_commands` | Container entrypoint / health check | First command becomes `CMD`/`ENTRYPOINT`. If health-check-capable (HTTP server), derive the health check probe from `ARCH-COMP-*.interfaces`. |
| `IMPL-GUIDE-*.prerequisites` | CI runner requirements | Each prerequisite (language version, system package) becomes a setup step (e.g. `actions/setup-node@v4`) or base image selection criterion. |
| `IMPL-GUIDE-*.conventions` | Lint/format validation steps | Coding conventions that have tooling (prettier, eslint, ruff, black) become pipeline lint steps. |
| `IMPL-MAP-*.module_path` | Build target scope | Each distinct `module_path` becomes a build job. Multiple map entries sharing a `module_path` are built together. |
| `IMPL-MAP-*.entry_point` | Container CMD | The process entrypoint for the deploy unit. |

## Pipeline stage ordering

The pipeline must follow this stage order. Each stage gates the next — failure stops the pipeline.

```
┌──────────┐    ┌──────────┐    ┌───────────────┐    ┌──────────┐    ┌──────────┐
│ Checkout  │───▶│  Build   │───▶│     Test      │───▶│ Security │───▶│  Deploy  │
│ + Setup   │    │ + Lint   │    │ (unit + int)  │    │   Scan   │    │          │
└──────────┘    └──────────┘    └───────────────┘    └──────────┘    └──────────┘
```

### Stage details

| Stage | Steps | Source |
|---|---|---|
| **Checkout + Setup** | Clone repo, restore caches, install prerequisites | `IMPL-GUIDE-*.prerequisites` |
| **Build + Lint** | Install dependencies, run linters/formatters, compile/build | `IMPL-GUIDE-*.build_commands`, `IMPL-GUIDE-*.conventions` |
| **Test** | Run unit tests, integration tests, generate coverage report | `IMPL-GUIDE-*.build_commands` (test commands) |
| **Security Scan** | SAST (static analysis), dependency audit (CVE check), container image scan | Best practice — tool selection from `ARCH-TECH-*.choice` ecosystem |
| **Deploy** | Push artifact (container image, package), apply IaC, deploy to target environment | IaC modules from `DEVOPS-IAC-*`, deployment method from Stage 4 |

## Caching strategies

| Dependency type | Cache key | Restore strategy |
|---|---|---|
| Package manager (npm, pip, cargo) | Hash of lockfile | Restore on lockfile match, full install on miss |
| Build output (compiled assets, .next/) | Hash of source files | Restore if source unchanged |
| Container layers | Layer digest | Docker layer caching via buildkit or registry cache |
| Terraform providers | Provider version lock | Restore on lock match |

## Secret management

Every secret referenced in `IMPL-CODE-*.environment_config` must be:

1. **Stored** in the CI platform's secret store (GitHub Secrets, GitLab CI Variables, Jenkins Credentials) or an external vault (HashiCorp Vault, AWS Secrets Manager).
2. **Injected** as environment variables at the step level, not the workflow level, to minimize exposure scope.
3. **Never** logged, echoed, or written to artifact output. Pipeline must mask secret values in logs.
4. **Rotated** according to the secret store's rotation policy. Document the rotation mechanism in the pipeline config.

## IaC apply step integration

The deploy stage integrates with the IaC from Stage 2:

1. **Terraform plan** runs on every PR (no apply) — output stored as a PR comment or artifact.
2. **Terraform apply** runs on merge to main (staging) or on manual approval (production).
3. Environment promotion follows the `environments` chain from `DEVOPS-IAC-*`:
   - PR merge → staging (auto)
   - Staging smoke tests pass → production (manual gate or auto based on `approval_required`)

## Artifact publishing

| Build output | Publishing target | Trigger |
|---|---|---|
| Container image | Container registry (ECR, GCR, ACR, Docker Hub) | Every successful build on main |
| Package (npm, PyPI, crate) | Package registry | Tag push matching `v*` |
| Terraform plan | PR artifact / comment | Every PR |
| Test/coverage report | CI artifact storage | Every build |

## Output sequence

All metadata operations use `${SKILL_DIR}/scripts/artifact.py`. Never edit `.meta.yaml` files directly.

1. Initialize the pipeline section:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py init --section pipeline
   ```
   This returns the new artifact id (e.g. `DEVOPS-PL-001`).

2. Fill the paired `.md` file via Edit with:
   - Pipeline platform selection and rationale
   - Trigger configuration (branches, tags, PRs)
   - Full stage breakdown with steps and commands
   - Caching configuration
   - Secret management setup
   - Environment promotion chain
   - Optionally write actual pipeline YAML files (e.g. `.github/workflows/ci.yml`)

3. Link upstream and set progress:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py set-progress <id> --completed 1 --total 1
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream IMPL-CODE-001
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream IMPL-GUIDE-001
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream IMPL-MAP-001
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream DEVOPS-IAC-001
   ```
   Link to every Impl artifact that drives the pipeline, plus the IaC artifact for deploy targets. Also link Arch decisions that shaped the pipeline structure:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream ARCH-DEC-001
   ```

4. Transition to review:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
   ```

**Note**: The `deployment_method`, `rollback_trigger`, and `rollback_procedure` fields in the Pipeline Config schema are **not** filled in this stage. They are added by Stage 4 (strategy), which updates the same Pipeline Config artifact.

## Escalation conditions

Escalate to the user **only** when:

- **Build time exceeds platform timeout** — the estimated build duration (based on project size and build commands) exceeds the CI platform's job timeout limit (e.g. GitHub Actions 6h, GitLab CI 1h default). Propose solutions: build parallelization, incremental builds, or platform tier upgrade.
- **Artifact size exceeds platform limits** — container image or package exceeds the registry's maximum size. Propose solutions: multi-stage builds, dependency pruning, or alternative artifact formats.
- A **build command from IMPL-GUIDE is incompatible** with the target CI platform (e.g. a command that requires a GUI environment on a headless CI runner). Per the Impl input contract, escalate rather than silently altering the command.
- A **prerequisite cannot be satisfied** on any available CI runner type (e.g. requires a GPU for build but the CI platform has no GPU runners).

Do **not** escalate for:

- Choosing between CI platforms (default to GitHub Actions unless the project already uses another).
- Selecting cache strategies (use the standard strategies above).
- Pipeline YAML syntax decisions (follow the platform's documentation).
