# Workflow — Stage 4: Deployment Strategy

## Role

Determine the deployment method, traffic routing, and rollback procedures by synthesizing SLO targets, error budget status, and architectural dependencies. This stage does not create a new artifact — it **updates** the existing Pipeline Config artifact (`DEVOPS-PL-*`) by filling the `deployment_method`, `deployment_rationale`, `rollback_trigger`, and `rollback_procedure` fields that Stage 3 (pipeline) left empty.

## Inputs

- **SLO definitions** (from Stage 1) — `DEVOPS-OBS-*.observability_config.slo_definitions`. The SLO availability target and error budget drive deployment conservatism.
- **ARCH-COMP-\*** — component `dependencies` field determines deploy order via topological sort.
- **ARCH-DEC-\*** — architectural decisions that mention deployment topology (monolith, microservices, serverless) constrain the available strategies.
- **Pipeline Config** (from Stage 3) — `DEVOPS-PL-*.pipeline_config`. This is the artifact being updated.

## Deployment method decision matrix

Use the SLO availability target and error budget remaining to select the deployment method. The matrix below provides the recommended strategy; override only with documented rationale.

| SLO availability target | Error budget remaining | Recommended strategy | Rationale |
|---|---|---|---|
| >= 99.9% | any | **Blue-green** or **Canary** | Zero-downtime is mandatory. Both strategies allow instant rollback without serving errors during deployment. |
| >= 99.5% | > 50% | **Canary** or **Rolling** | Budget headroom allows graduated rollout. Canary preferred for its observability advantage. |
| >= 99.5% | 25%–50% | **Canary** (conservative weights) | Moderate budget — use slower canary progression (1% → 5% → 25% → 100%). |
| >= 99.5% | < 25% | **Blue-green** | Low budget — cannot afford deployment-induced errors. Blue-green provides instant rollback. |
| < 99.5% | any | **Rolling** or **Recreate** | Relaxed SLO tolerates brief downtime. Rolling is preferred; Recreate only when stateful constraints prevent rolling updates. |

### Strategy characteristics

| Strategy | Downtime | Rollback speed | Resource overhead | Best for |
|---|---|---|---|---|
| **Blue-green** | Zero | Instant (DNS/LB switch) | 2x compute during deploy | High-SLO services, database migrations needing instant rollback |
| **Canary** | Zero | Fast (route traffic away from canary) | 1x + canary slice | Services with good observability, gradual confidence building |
| **Rolling** | Near-zero (brief mixed versions) | Moderate (roll forward or undo) | 1x (surge capacity configurable) | Stateless services with relaxed SLOs |
| **Recreate** | Yes (old down, new up) | Slow (redeploy old version) | 1x | Stateful services that cannot run mixed versions |

## Deploy ordering from dependency graph

Derive the deploy order from `ARCH-COMP-*.dependencies` using topological sort:

1. Build the directed dependency graph from all `ARCH-COMP-*` entries.
2. Topological sort — components with no inbound dependencies deploy first.
3. If the graph has **circular dependencies**, this is an Arch contract violation. Escalate to the user.
4. Components at the same topological level may deploy in parallel.
5. Record the deploy order in the pipeline config's stage ordering.

Example: if `gateway → api-service → database`, deploy order is: `database` → `api-service` → `gateway`.

## Rollback trigger design

Rollback triggers are derived from SLO burn-rate alerts (Stage 1). Each trigger maps an alerting condition to an automatic or manual rollback action.

```yaml
rollback_trigger:
  conditions:
    - type: error_rate
      threshold: "5%"           # derived from SLO error budget
      monitoring_ref: MON-001   # must reference a monitoring rule
      slo_ref: SLO-001
    - type: latency_p99
      threshold: "500ms"        # derived from SLO latency target
      monitoring_ref: MON-002
      slo_ref: SLO-001
```

**Design rules**:

- Every `rollback_trigger.condition` must reference a `monitoring_rules.id` from the Observability artifact. The review stage (Stage 8) verifies this linkage.
- The threshold must be derived from the SLO definition — not invented. Use the burn-rate threshold from the "Page (critical)" tier as the rollback trigger.
- For **canary** deployments: trigger fires → halt canary promotion → route 100% to stable.
- For **blue-green** deployments: trigger fires → switch LB/DNS back to the previous environment.
- For **rolling** deployments: trigger fires → `kubectl rollout undo` or equivalent.

## Rollback procedure steps

Define a concrete rollback procedure for each environment:

```yaml
rollback_procedure:
  steps:
    - "Halt deployment progression (canary: freeze weight, rolling: pause rollout)"
    - "Route 100% traffic to the last known stable version"
    - "Verify SLO metrics return to normal within 5 minutes"
    - "Notify on-call channel with deployment ID and rollback reason"
    - "Create incident ticket if SLO was breached during the rollback window"
  verification: "Confirm error rate and latency return below SLO threshold for 10 minutes"
  notification: "#deploy-alerts"
```

The rollback procedure must:

1. Reference the specific commands or API calls for the deployment platform (e.g. `kubectl rollout undo`, `aws ecs update-service`, Argo Rollouts abort).
2. Include a verification step that checks the SLO metrics after rollback.
3. Include a notification step that alerts the team.
4. Be usable by the incident runbooks (Stage 7) — the runbook's remediation steps reference `pipeline_config.rollback_procedure`.

## Health check integration

Each deployment strategy requires health checks to determine readiness:

| Check type | Source | Used by |
|---|---|---|
| **Startup probe** | `IMPL-GUIDE-*.run_commands` + known startup time | All strategies — wait for process to initialize |
| **Readiness probe** | `ARCH-COMP-*.interfaces` (HTTP health endpoint) | Rolling, Canary — determines when new instances receive traffic |
| **Liveness probe** | `ARCH-COMP-*.interfaces` (HTTP health endpoint) | All strategies — determines when to restart a failed instance |

## Traffic weight routing (canary)

When the selected strategy is canary, define the traffic progression:

| Phase | Canary weight | Duration | Gate condition |
|---|---|---|---|
| 1 | 1% | 5 minutes | No burn-rate alert fires |
| 2 | 5% | 10 minutes | No burn-rate alert fires |
| 3 | 25% | 15 minutes | No burn-rate alert fires |
| 4 | 50% | 15 minutes | No burn-rate alert fires |
| 5 | 100% | — | Promotion complete |

Adjust weights and durations based on the SLO error budget remaining. Lower budget → slower progression with longer observation windows.

## Output sequence

This stage **updates** the existing Pipeline Config artifact. All metadata operations use `${SKILL_DIR}/scripts/artifact.py`. Never edit `.meta.yaml` files directly.

1. Read the existing Pipeline Config artifact (`DEVOPS-PL-*`) to determine its id and current content.

2. Edit the paired `.md` file to add:
   - Deployment method and rationale (citing SLO target and error budget)
   - Deploy order derived from dependency graph
   - Rollback trigger conditions with monitoring refs
   - Rollback procedure steps
   - Health check configuration
   - Traffic weight routing (if canary)

3. Update progress:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py set-progress <id> --completed 1 --total 1
   ```

4. Link upstream to the SLO definitions and Arch decisions:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream DEVOPS-OBS-001
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream ARCH-DEC-001
   ```

5. Transition to review (if not already in review from Stage 3):
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
   ```

## Escalation conditions

Escalate to the user **only** when:

- The **required deployment method conflicts with infrastructure cost or resource constraints** — e.g. blue-green requires 2x compute resources but the RE budget constraint cannot accommodate it. Propose alternatives: canary (lower overhead) or negotiate a budget increase.
- The **Arch dependency graph is circular**, preventing a valid deploy order. This is an Arch contract violation — recommend reopening Arch.
- The **SLO target requires zero-downtime** but the application is stateful in a way that prevents running two versions simultaneously (e.g. database schema migration that is not backward-compatible). Propose solutions: backward-compatible migration strategy, expand/contract pattern, or temporary SLO relaxation during the migration window.
- The **deployment platform does not support the selected strategy** — e.g. the IaC targets a serverless platform (Lambda, Cloud Functions) that does not natively support canary deployments. Propose platform-specific alternatives (Lambda weighted aliases, Cloud Functions traffic splitting).

Do **not** escalate for:

- Choosing between canary and blue-green when both are viable (prefer canary for its observability advantage unless resource constraints favor blue-green).
- Selecting canary weight progression steps (use the standard progression above).
- Rollback procedure command syntax (derive from the deployment platform documentation).
