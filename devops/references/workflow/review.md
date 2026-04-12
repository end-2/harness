# Workflow — Stage 8: Integrated Review (subagent)

## Role

Verify all DevOps artifacts for feedback-loop integrity, traceability to upstream Arch/Impl/RE artifacts, and adherence to security, cost, and environment-consistency best practices. This is the quality gate before any DevOps artifact transitions to `approved`. The review subagent identifies gaps, classifies them, and routes each back to the responsible stage for correction. This stage is executed by a **subagent** — it does not call `${SKILL_DIR}/scripts/artifact.py` directly.

See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full subagent protocol.

> **Metadata reminder**: All metadata operations are handled by the main agent via `${SKILL_DIR}/scripts/artifact.py`. Subagents express metadata changes through `proposed_meta_ops` in their report frontmatter. `.meta.yaml` files must never be edited directly — not by the main agent, not by subagents.

## Inputs

- **All 4 DevOps category artifacts**:
  - `DEVOPS-PL-*` — Pipeline Config (pipeline + deployment strategy)
  - `DEVOPS-IAC-*` — Infrastructure Code
  - `DEVOPS-OBS-*` — Observability (SLOs, monitoring, logging, tracing)
  - `DEVOPS-RB-*` — Runbook entries
- **Upstream Arch artifacts**: `ARCH-COMP-*`, `ARCH-DEC-*`, `ARCH-TECH-*`, `ARCH-DIAG-*`
- **Upstream Impl artifacts**: `IMPL-MAP-*`, `IMPL-CODE-*`, `IMPL-IDR-*`, `IMPL-GUIDE-*`
- **RE artifacts** (indirect via Arch/Impl `re_refs` and `constraint_ref`)
- **Feedback loop checklist**: `${SKILL_DIR}/references/feedback-loop.md` — the authoritative checklist for feedback loop verification

## Verification axis 1: Feedback loop integrity

Load the checklist from `${SKILL_DIR}/references/feedback-loop.md` and verify each item against the DevOps artifacts. The checklist covers six loop connections:

### Completeness checks

| Check | How to verify | Classification on failure |
|---|---|---|
| Every `slo_definitions` entry has at least one `monitoring_rules` entry with `slo_refs` pointing to it | For each SLO id, search `monitoring_rules[].slo_refs` for a match | `feedback_loop_gap` → route to **monitor** |
| Every `monitoring_rules` entry with severity >= high has at least one `runbook_entries` with `monitoring_refs` pointing to it | For each high/critical MON id, search `runbook_entries[].monitoring_refs` for a match | `feedback_loop_gap` → route to **incident** |
| Every `pipeline_config.rollback_trigger` condition references a valid `monitoring_rules.id` | Check that each `rollback_trigger.conditions[].monitoring_ref` exists in `monitoring_rules` | `feedback_loop_gap` → route to **strategy** |
| Every `runbook_entries` that mentions rollback references `pipeline_config.rollback_procedure` | Check that rollback-related runbooks have a `rollback_ref` matching the pipeline config | `feedback_loop_gap` → route to **incident** |
| Every Arch component with type `service` or `gateway` has at least one SLO | For each qualifying ARCH-COMP, check `slo_definitions[].re_refs` or component coverage | `feedback_loop_gap` → route to **slo** |

### Consistency checks

| Check | How to verify | Classification on failure |
|---|---|---|
| SLO burn-rate alert thresholds match between `slo_definitions.burn_rate_alert` and corresponding `monitoring_rules.threshold` | Compare numerical values | `consistency_gap` → route to **monitor** |
| Rollback trigger thresholds are consistent with SLO error budgets | Verify trigger threshold derives from SLO error budget | `consistency_gap` → route to **strategy** |
| Deployment method is appropriate for SLO availability target | Check against the decision matrix in [strategy.md](strategy.md) (>= 99.9% requires zero-downtime) | `consistency_gap` → route to **strategy** |
| Log retention policy satisfies RE regulatory constraints | Compare `logging_config.retention` against constraint requirements | `consistency_gap` → route to **log** |

## Verification axis 2: Traceability

Every DevOps artifact must trace back to its upstream source. Verify the following chains:

### IaC to Arch traceability

| Check | How to verify | Classification on failure |
|---|---|---|
| Every IaC module has `comp_refs` pointing to an `ARCH-COMP-*` | For each `infrastructure_code.modules` entry, verify `comp_refs` is non-empty and references exist | `traceability_gap` → route to **iac** |
| Every IaC resource type matches the Arch component type mapping | Verify compute → service, database → store, etc. per the mapping in [iac.md](iac.md) | `traceability_gap` → route to **iac** |

### Pipeline to Impl traceability

| Check | How to verify | Classification on failure |
|---|---|---|
| Every pipeline build step traces to `IMPL-CODE-*.build_config` or `IMPL-GUIDE-*.build_commands` | Verify `impl_refs` on the pipeline config point to valid Impl artifacts | `traceability_gap` → route to **pipeline** |
| Pipeline stages include all build commands from IMPL-GUIDE | Cross-reference pipeline steps against `IMPL-GUIDE-*.build_commands` | `traceability_gap` → route to **pipeline** |

### SLO to RE traceability

| Check | How to verify | Classification on failure |
|---|---|---|
| Every SLO traces to a RE quality attribute via `re_refs` | Verify each `slo_definitions[].re_refs` is non-empty | `traceability_gap` → route to **slo** |
| Every SLO `re_refs` entry exists in the upstream Arch artifacts' `re_refs` | Cross-reference against `ARCH-COMP-*.re_refs` or `ARCH-DEC-*.re_refs` | `traceability_gap` → route to **slo** |

### Deployment to Arch traceability

| Check | How to verify | Classification on failure |
|---|---|---|
| Every deployment decision has `arch_refs` justifying it | Verify `pipeline_config.arch_refs` is non-empty | `traceability_gap` → route to **strategy** |
| Deploy order matches Arch dependency graph | Topological sort of `ARCH-COMP-*.dependencies` must match pipeline deploy stage order | `traceability_gap` → route to **pipeline** |

## Verification axis 3: Best practices

### Security

| Check | How to verify | Classification on failure |
|---|---|---|
| No secrets hardcoded in pipeline config | Scan `pipeline_config.stages[].steps` for literal secret values; all sensitive values must reference a secret store | `security_concern` |
| Least-privilege IAM | IaC security groups and IAM roles use minimal required permissions; no `*` in action or resource fields | `security_concern` |
| Security scan in pipeline | At least one pipeline stage performs SAST, dependency audit, or container image scanning | `security_concern` |
| Sensitive data masking in logs | `logging_config.masking_rules` covers PII/credential field patterns per RE constraints | `security_concern` |
| Encryption at rest | IaC state backend and databases have encryption enabled | `security_concern` |

### Cost

| Check | How to verify | Classification on failure |
|---|---|---|
| Right-sizing recommendations | Production compute instances are appropriate for expected load; dev/staging use smaller instances | `cost_concern` |
| Reserved instances for production | If deployment is long-lived (not serverless), note whether reserved/savings plan pricing is considered | `cost_concern` |
| Cost estimate present | `infrastructure_code.cost_estimate` is filled for production environment | `cost_concern` |
| No over-provisioned resources | Dev environment does not replicate production scale | `cost_concern` |

### Environment consistency

| Check | How to verify | Classification on failure |
|---|---|---|
| Same IaC structure across dev/staging/prod | All environments use the same Terraform modules, differing only in `.tfvars` overrides | `consistency_gap` → route to **iac** |
| Pipeline deploys to all environments | Pipeline config includes stages for all defined environments | `consistency_gap` → route to **pipeline** |
| Secret management is uniform | All environments use the same secret injection mechanism (not hardcoded in some, Vault in others) | `consistency_gap` → route to **pipeline** |
| Monitoring coverage is environment-aware | Production has full monitoring; staging has at minimum SLO alerts; dev may be reduced | `consistency_gap` → route to **monitor** |

## Classification and routing

Each finding is classified and routed to the responsible stage:

| Classification | Meaning | Route to |
|---|---|---|
| `feedback_loop_gap` | A connection in the deploy-observe feedback loop is broken | The stage responsible for the missing connection (slo, strategy, monitor, incident) |
| `traceability_gap` | An artifact is missing an upstream or downstream reference | The stage that produced the artifact missing the link (iac, pipeline, slo, strategy) |
| `consistency_gap` | An inconsistency exists between artifacts or between environments | The stage that owns the inconsistent artifact (iac, pipeline, monitor, log) |
| `security_concern` | A security best practice is not followed | Flagged as a **recommendation** — the main agent presents to the user but does not auto-route |
| `cost_concern` | A cost optimization opportunity exists | Flagged as a **recommendation** — informational, not blocking |
| `escalation` | An upstream contract violation that DevOps cannot fix (Arch or Impl artifact is wrong) | **Escalate to user** — recommend reopening the upstream skill |

### Severity assignment

| Classification | Default severity | Override condition |
|---|---|---|
| `feedback_loop_gap` | `high` | `critical` if the gap affects a >= 99.9% SLO |
| `traceability_gap` | `med` | `high` if it breaks the RE → ARCH → IMPL → DEVOPS chain |
| `consistency_gap` | `med` | `high` if production environment is affected |
| `security_concern` | `high` | `critical` if secrets are exposed or IAM is overly permissive |
| `cost_concern` | `low` | `med` if cost estimate exceeds budget constraint |
| `escalation` | `high` | Always `high` — user must decide |

## Report output

The subagent writes a structured verification report to the path allocated by the main agent.

### Report frontmatter

```yaml
---
report_id: <assigned by main agent>
kind: review
skill: devops
stage: review
created_at: <timestamp>
target_refs:
  - DEVOPS-PL-001
  - DEVOPS-IAC-001
  - DEVOPS-OBS-001
  - DEVOPS-RB-001
verdict: pass | at_risk | fail
summary: "<one-line summary of verification results>"
proposed_meta_ops: []
items:
  - id: 1
    severity: high
    classification: feedback_loop_gap
    message: "SLO-002 has no corresponding monitoring rule"
  - id: 2
    severity: med
    classification: traceability_gap
    message: "IaC module 'cache' has no comp_refs to ARCH-COMP"
  - id: 3
    severity: low
    classification: cost_concern
    message: "Dev environment uses production-sized instances"
---
```

Valid `classification` values for this stage: `feedback_loop_gap`, `traceability_gap`, `consistency_gap`, `security_concern`, `cost_concern`, `escalation`.

### Report body structure

The report body (below the frontmatter) contains a detailed verification report:

```markdown
## Feedback Loop Verification

### Completeness
- [x] Every SLO has at least one monitoring rule — PASS
- [ ] MON-003 (severity: high) has no runbook entry — FAIL (item #1)
...

### Consistency
- [x] Burn-rate thresholds match — PASS
- [x] Deployment method appropriate for SLO — PASS
...

## Traceability Verification

- [x] All IaC modules have comp_refs — PASS
- [ ] Pipeline missing impl_refs to IMPL-GUIDE-001 — FAIL (item #2)
...

## Best Practices

### Security
- [x] No hardcoded secrets — PASS
- [x] Security scan stage present — PASS
...

### Cost
- [ ] Dev environment over-provisioned — INFO (item #3)
...

### Environment Consistency
- [x] Same IaC modules across environments — PASS
...
```

### Verdict rules

| Condition | Verdict |
|---|---|
| Zero items with severity `high` or `critical` | `pass` |
| Any items with severity `high` but none `critical` | `at_risk` |
| Any items with severity `critical` or classification `escalation` | `fail` |

## Escalation conditions

Escalate (via `classification: escalation` in the report items) when:

- An **upstream Arch contract is violated** — e.g. an Arch component has no corresponding IaC module and no IaC stage can fix it because the component was not in the Arch artifact. The Arch skill must add the component.
- An **upstream Impl contract is violated** — e.g. build commands reference a tool not in the Arch tech stack, or environment config references a non-existent secret store.
- A **circular dependency** is detected in the deploy order that was not caught in earlier stages.
- **Multiple feedback loop gaps form a cascade** — e.g. SLO has no monitoring, monitoring has no runbook, meaning an entire incident response chain is missing.

Do **not** escalate for:

- Individual `security_concern` or `cost_concern` items — these are recommendations, not blockers.
- Minor traceability gaps that can be fixed by adding a `link` command (route back to the stage instead).
- Formatting or documentation quality issues.
