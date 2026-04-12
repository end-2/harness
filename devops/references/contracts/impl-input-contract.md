# Impl Input Contract

How the DevOps skill reads the four Impl artifacts and turns each field into a pipeline, build, or operational directive. Read this before `pipeline` or `monitor` when you need to know what a specific Impl field is supposed to produce in DevOps output.

## Location and readiness

- Impl artifacts live in `./artifacts/impl/` (override with `HARNESS_ARTIFACTS_DIR`, which points at the parent `artifacts/` directory).
- The four sections must all be present:
  - `IMPL-MAP-*` — implementation map
  - `IMPL-CODE-*` — code structure
  - `IMPL-IDR-*` — implementation decisions
  - `IMPL-GUIDE-*` — implementation guide
- Every one must be in phase `approved`. If any is in `draft` / `in_review` / `revising`, stop and tell the user — DevOps must not run on unstable input.

Use `python ${SKILL_DIR}/../impl/scripts/artifact.py list` (or read the metadata files directly) to confirm. If only the DevOps `artifact.py` is available locally, read the Impl YAML files with a small script that walks `./artifacts/impl/*.meta.yaml`.

## IMPL-MAP-* → build targets

| Impl field | DevOps action |
|------------|---------------|
| `id` | Recorded in `DEVOPS-PL-*.upstream_refs` when the map entry drives a build target |
| `module_path` | Determines the build scope: each distinct `module_path` becomes a build target in the CI pipeline. Monorepo layouts with multiple `module_path` values get parallel build jobs; single-module layouts get a single build job |
| `entry_point` | Used as the container `CMD` or process entrypoint in the IaC compute resource definition |
| `component_ref` | Maps back to an `ARCH-COMP-*`, which in turn maps to a deploy unit in `DEVOPS-IAC-*`. This is the bridge: `IMPL-MAP → ARCH-COMP → DEVOPS-IAC`. Every build target must trace to exactly one deploy unit through this chain |
| `interfaces_implemented` | Cross-referenced with `ARCH-COMP-*.interfaces` to verify the health check endpoints declared in IaC match what the code actually exposes |
| `re_refs` | Propagated to the pipeline and observability artifacts for end-to-end traceability |

**Build target rule**: one `IMPL-MAP-*` entry with a distinct `module_path` produces one build job in the CI pipeline. If multiple `IMPL-MAP-*` entries share the same `module_path`, they are built together as a single job. The `component_ref` determines which deploy unit receives the built artifact.

## IMPL-CODE-* → pipeline config

| Impl field | DevOps action |
|------------|---------------|
| `id` | Recorded in `DEVOPS-PL-*.upstream_refs` |
| `build_config` | Drives the CI build stages: identifies the build tool (Maven, Gradle, npm, cargo, etc.), the build output type (container image, JAR, wheel, binary), and any multi-stage build requirements. Each `build_config` entry becomes a concrete step in the pipeline YAML |
| `module_dependencies` | Used to determine build order within the pipeline. Internal dependencies that cross module boundaries require the dependent module to build first |
| `external_dependencies` | Drive CI cache configuration: dependency lockfiles (package-lock.json, go.sum, Cargo.lock) become cache keys. Each external dependency version is pinned in the pipeline's dependency-install step |
| `environment_config` | Drives secret and environment variable management: each entry becomes either a pipeline secret (credentials, API keys) injected at build/deploy time, or a runtime environment variable baked into the IaC compute definition. Sensitive values are never hardcoded — they reference a secret store (Vault, AWS Secrets Manager, K8s Secrets) |
| `tech_stack_ref` | Cross-referenced with `ARCH-TECH-*` to ensure the pipeline's runtime version matches the Arch-approved technology |

**Cache key rule**: for each `external_dependencies` entry, the pipeline must define a cache key derived from the lockfile hash. Cache invalidation follows: lockfile change → full reinstall; no change → restore from cache. This applies to both CI build caching and container layer caching.

**Secret management rule**: every `environment_config` entry marked as sensitive must map to a secret store reference in the pipeline YAML and in the IaC environment definition. The pipeline must never echo, log, or persist secret values.

## IMPL-IDR-* → operational characteristics

| Impl field | DevOps action |
|------------|---------------|
| `id` | Recorded in `DEVOPS-OBS-*.upstream_refs` or `DEVOPS-RB-*.upstream_refs` when the decision drives monitoring or runbook content |
| `pattern_applied` | Informs monitoring strategy and runbook content based on the pattern's operational profile |
| `rationale` | Recorded in the observability artifact or runbook to explain why a specific monitoring approach was chosen |
| `arch_refs` | Used to trace back to the Arch decision that mandated the pattern, completing the chain `ARCH-DEC → IMPL-IDR → DEVOPS-OBS/RB` |
| `re_refs` | Propagated to SLO definitions when the pattern was chosen to satisfy a specific quality attribute |

**Pattern-to-monitoring mapping**:

| Pattern | Monitoring directive | Runbook directive |
|---------|---------------------|-------------------|
| CQRS | Separate read/write metrics (latency, throughput, error rate per side). Alert on read/write ratio drift. Dashboard splits command vs query panels | Runbook for read-side rebuild from event store, write-side backpressure handling |
| Circuit Breaker | Dashboard panel showing circuit state (closed/open/half-open) per dependency. Alert on circuit-open events. Metric: `circuit_breaker_state`, `circuit_breaker_trip_total` | Runbook for manual circuit reset, dependency health investigation, fallback verification |
| Event Sourcing | Event store growth metric, projection lag metric, replay throughput metric. Alert on projection lag exceeding threshold | Runbook for event replay procedure, projection rebuild, snapshot management |
| Saga / Choreography | Saga completion rate, step duration per participant, compensation trigger count. Alert on saga timeout or repeated compensation | Runbook for stuck saga resolution, manual compensation, participant state reconciliation |
| Repository | Standard CRUD metrics on the backing store. No special monitoring beyond what the store type dictates | Standard store runbook (connection pool exhaustion, slow queries) |
| Retry / Backoff | Retry count per operation, retry exhaustion rate. Alert on retry exhaustion spike | Runbook for identifying the downstream cause of retries, adjusting retry policy |
| Outbox | Outbox table size, publish lag, delivery failure count. Alert on outbox growth or publish lag | Runbook for outbox drain failure, DLQ handling, manual replay |

If a pattern is not in this table, derive the monitoring and runbook directives from the pattern's failure modes and operational characteristics.

## IMPL-GUIDE-* → CI/CD commands

| Impl field | DevOps action |
|------------|---------------|
| `id` | Recorded in `DEVOPS-PL-*.upstream_refs` |
| `build_commands` | Become the literal CI build steps in the pipeline YAML. Each command is a pipeline step with its own error handling (fail-fast or continue-on-error based on criticality). Commands are executed in the declared order |
| `run_commands` | Become the container entrypoint (`CMD`/`ENTRYPOINT` in Dockerfile) and the health check command in the IaC compute definition. If multiple `run_commands` exist, the first is the primary entrypoint and the rest are sidecars or init containers |
| `prerequisites` | Drive CI runtime requirements: each prerequisite (language version, system package, tool version) becomes either a base image selection criterion or a setup step in the pipeline. The IaC compute definition must also satisfy these prerequisites |
| `conventions` | Inform pipeline linting and validation steps: coding conventions may require linters, formatters, or static analysis tools as pipeline stages |
| `extension_points` | Identify where plugin/extension build steps may be needed in the pipeline (e.g. a plugin system requires a separate build-and-package step for plugins) |

**Command fidelity rule**: `build_commands` and `run_commands` from the Implementation Guide are authoritative. The pipeline must use them exactly as declared, wrapping them in the appropriate pipeline syntax (GitHub Actions step, GitLab CI script, Jenkinsfile stage) but not altering the command itself. If a command is incompatible with the target CI platform, escalate to the user.

**Prerequisites rule**: every `prerequisites` entry must be satisfied in the CI runner environment. If the CI platform does not natively support a prerequisite version, the pipeline must include an explicit setup step (e.g. `actions/setup-node@v4` for a specific Node.js version, or a custom Docker image with the required toolchain).

## Traceability propagation

Every Pipeline Config must link upstream to the Impl artifacts it derives from:

```
python ${SKILL_DIR}/scripts/artifact.py link <devops-pl-id> --upstream IMPL-CODE-001
python ${SKILL_DIR}/scripts/artifact.py link <devops-pl-id> --upstream IMPL-GUIDE-001
```

Every build target in the pipeline must trace through the Implementation Map to an Arch component and then to a deploy unit:

```
python ${SKILL_DIR}/scripts/artifact.py link <devops-pl-id> --upstream IMPL-MAP-001
```

Every Observability entry driven by a pattern must link to the IDR:

```
python ${SKILL_DIR}/scripts/artifact.py link <devops-obs-id> --upstream IMPL-IDR-001
```

The full traceability chain is: `RE-* → ARCH-* → IMPL-* → DEVOPS-*`. Every DevOps artifact must have at least one upstream ref to an Impl artifact, and through Impl, to Arch and RE.

## When Impl is wrong

If an Impl artifact is genuinely unrealisable at the DevOps level (build commands produce an artifact type incompatible with the target platform, prerequisites conflict with each other, environment config references a secret store that does not exist on the target cloud), **do not** patch around it inside DevOps. Stop, escalate to the user, and recommend they re-open Impl. Impl is the source of truth for code structure and build configuration.
