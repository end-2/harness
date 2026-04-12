# Workflow — Stage 7: Incident Runbook (subagent)

## Role

Generate incident runbooks from the deployment strategy's rollback procedures and the monitoring stage's alerting rules. Each high- or critical-severity monitoring rule gets a dedicated runbook entry with trigger conditions, diagnosis steps (including actual CLI commands derived from IaC environment info), remediation steps, escalation paths, and communication templates. This stage is executed by a **subagent** — it does not call `${SKILL_DIR}/scripts/artifact.py` directly.

See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full subagent protocol.

> **Metadata reminder**: All metadata operations are handled by the main agent via `${SKILL_DIR}/scripts/artifact.py`. Subagents express metadata changes through `proposed_meta_ops` in their report frontmatter. `.meta.yaml` files must never be edited directly — not by the main agent, not by subagents.

**Important**: The main agent must initialize the runbook artifact **before** spawning this subagent:

```bash
python ${SKILL_DIR}/scripts/artifact.py init --section runbook
```

Subagents never call `artifact.py` to create or modify artifacts. The main agent initializes the runbook section, spawns this subagent, and then merges the subagent's report body into the runbook artifact.

## Inputs

- **Strategy output** (from Stage 4) — `DEVOPS-PL-*.pipeline_config.rollback_trigger` and `rollback_procedure`. Every runbook that involves rollback must reference these procedures.
- **Monitoring rules** (from Stage 5) — `DEVOPS-OBS-*.observability_config.monitoring_rules`. Every rule with `severity: critical` or `severity: high` must have at least one corresponding runbook entry.
- **ARCH-COMP-\*** — component list with `name`, `type`, `interfaces`, `dependencies`. Component names appear in diagnosis commands; dependencies inform which upstream/downstream services to check.
- **IaC output** (from Stage 2) — `DEVOPS-IAC-*.infrastructure_code`. Module names, provider, environments, and resource types inform the actual CLI commands used in diagnosis and remediation steps.
- **SLO definitions** (from Stage 1) — `DEVOPS-OBS-*.observability_config.slo_definitions`. Runbooks reference the SLO that the incident threatens.

## Runbook generation rules

### One runbook per high/critical alerting rule

For every `monitoring_rules` entry with `severity: critical` or `severity: high`:

1. Create a runbook entry with `monitoring_refs` pointing to the rule's `id`.
2. Set the runbook `severity` to match the monitoring rule's severity.
3. Set `slo_refs` to the monitoring rule's `slo_refs`.
4. Derive the `trigger_condition` from the monitoring rule's `condition` and `threshold`.

### Runbook entry structure

Each runbook entry must conform to the schema in [../schemas/section-schemas.md](../schemas/section-schemas.md):

```yaml
runbook_entries:
  - id: RB-001
    title: "<Short incident scenario title>"
    trigger_condition: "<MON-id> fires (<human-readable condition>)"
    severity: critical
    symptoms:
      - "<Observable indicator 1>"
      - "<Observable indicator 2>"
    diagnosis_steps:
      - step: 1
        action: "<What to check>"
        command: "<Actual CLI command>"
      - step: 2
        action: "<What to check next>"
        command: "<Actual CLI command>"
    remediation_steps:
      - step: 1
        action: "<First remediation action>"
        command: "<Actual CLI command>"
        auto: true
      - step: 2
        action: "<Manual follow-up>"
        command: "<Actual CLI command>"
        auto: false
    escalation_path:
      - level: 1
        contact: "on-call SRE"
        channel: "#incidents"
        timeout_minutes: 15
      - level: 2
        contact: "engineering lead"
        channel: "#incidents-escalation"
        timeout_minutes: 30
    rollback_ref: "PL-001.rollback_procedure"
    monitoring_refs: [MON-001]
    slo_refs: [SLO-001]
    communication_template: |
      ...
    postmortem_template: |
      ...
```

## Trigger condition mapping

Map each monitoring rule to a runbook trigger:

| Monitoring rule type | Trigger condition pattern |
|---|---|
| SLO burn-rate (metric) | `"MON-<id> fires (burn rate > <threshold>x on <SLO-id>)"` |
| Error rate threshold | `"MON-<id> fires (error rate > <threshold>% for <service>)"` |
| Latency threshold | `"MON-<id> fires (p99 latency > <threshold>ms for <service>)"` |
| Resource saturation | `"MON-<id> fires (<resource> utilization > <threshold>% for <component>)"` |
| Log-based alert | `"MON-<id> fires (<N> <level> log events in <window> for <service>)"` |

## Symptom description

For each trigger, list 2-4 observable symptoms that an on-call engineer would notice:

- User-facing impact (e.g. "5xx spike on /api/* endpoints", "page load times > 10s")
- Dashboard indicators (e.g. "SLO burn rate alert firing on dashboard X", "error rate panel shows red")
- Log patterns (e.g. "repeated TimeoutException in <service> logs", "connection refused errors to <dependency>")
- Infrastructure signals (e.g. "CPU utilization at 95% on <component> pods", "database connection pool exhausted")

## Diagnosis steps with actual commands

Diagnosis commands must be **concrete and executable** — use the IaC environment information (provider, tool, resource names) to construct real commands.

### Kubernetes-based deployments (EKS/GKE/AKS)

| Diagnosis action | Command |
|---|---|
| Check deployment status | `kubectl rollout status deployment/<component-name> -n <namespace>` |
| Check pod health | `kubectl get pods -l app=<component-name> -n <namespace>` |
| View recent logs | `kubectl logs -l app=<component-name> -n <namespace> --tail=100 --since=10m` |
| Check resource usage | `kubectl top pods -l app=<component-name> -n <namespace>` |
| Describe failing pod | `kubectl describe pod <pod-name> -n <namespace>` |
| Check service endpoints | `kubectl get endpoints <component-name> -n <namespace>` |
| Check recent events | `kubectl get events -n <namespace> --sort-by='.lastTimestamp' \| tail -20` |

### AWS-based deployments (ECS/RDS/ElastiCache)

| Diagnosis action | Command |
|---|---|
| Check ECS service status | `aws ecs describe-services --cluster <cluster> --services <service>` |
| Check ECS task health | `aws ecs list-tasks --cluster <cluster> --service-name <service> --desired-status RUNNING` |
| View CloudWatch logs | `aws logs tail /ecs/<service> --since 10m --follow` |
| Check RDS status | `aws rds describe-db-instances --db-instance-identifier <db-name>` |
| Check ALB target health | `aws elbv2 describe-target-health --target-group-arn <arn>` |
| Check ElastiCache status | `aws elasticache describe-cache-clusters --cache-cluster-id <cache-name>` |

### GCP-based deployments (Cloud Run/Cloud SQL)

| Diagnosis action | Command |
|---|---|
| Check Cloud Run service | `gcloud run services describe <service> --region <region>` |
| View Cloud Run logs | `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=<service>" --limit 50 --freshness 10m` |
| Check Cloud SQL status | `gcloud sql instances describe <instance>` |

Adapt commands to the actual provider and tools from the IaC artifact. Use placeholder `<component-name>`, `<namespace>`, `<cluster>`, etc. that map to IaC resource names.

## Remediation steps

Remediation follows a priority order:

1. **Automated rollback** (if `auto: true`) — reference the `pipeline_config.rollback_procedure` from Stage 4:
   ```yaml
   - step: 1
     action: "Trigger automated rollback (recent deploy suspected)"
     command: "kubectl rollout undo deployment/<component-name> -n <namespace>"
     auto: true
   ```

2. **Scaling** (if load-related):
   ```yaml
   - step: 2
     action: "Scale up if load spike is the root cause"
     command: "kubectl scale deployment/<component-name> --replicas=<N> -n <namespace>"
     auto: false
   ```

3. **Dependency isolation** (if dependency failure):
   ```yaml
   - step: 3
     action: "Enable circuit breaker / disable failing dependency"
     command: "<feature flag or config change command>"
     auto: false
   ```

4. **Manual investigation** (if root cause unclear):
   ```yaml
   - step: 4
     action: "Investigate root cause using diagnosis steps above"
     command: "N/A — manual investigation"
     auto: false
   ```

Every runbook that involves rollback as a remediation step must set `rollback_ref` to the Pipeline Config's rollback procedure (e.g. `PL-001.rollback_procedure`).

## Escalation path with severity-based timeouts

| Severity | Level 1 timeout | Level 2 timeout | Level 3 timeout |
|---|---|---|---|
| **Critical** | 15 minutes | 30 minutes | 1 hour |
| **High** | 30 minutes | 1 hour | 4 hours |

```yaml
escalation_path:
  - level: 1
    contact: "on-call SRE"
    channel: "#incidents"
    timeout_minutes: 15
  - level: 2
    contact: "engineering lead"
    channel: "#incidents-escalation"
    timeout_minutes: 30
  - level: 3
    contact: "VP engineering"
    channel: "#incidents-critical"
    timeout_minutes: 60
```

## Communication template

Provide a template for internal and external communication:

### Internal communication

```markdown
**Incident**: <title>
**Severity**: <critical|high>
**Status**: Investigating | Identified | Monitoring | Mitigated | Resolved
**Impact**: <description of user-facing impact>
**Started**: <timestamp>
**On-call**: <engineer name>

### Timeline
- HH:MM — Alert triggered: <monitoring rule description>
- HH:MM — Investigation started
- HH:MM — Root cause identified: <cause>
- HH:MM — Remediation applied: <action taken>
- HH:MM — Incident resolved

### Action items
- [ ] <follow-up action 1>
- [ ] <follow-up action 2>
```

### External status page

```markdown
**<Service Name> — <Degraded Performance | Partial Outage | Major Outage>**

We are currently experiencing <brief description of impact>.
Our team is actively investigating and working to resolve the issue.

**Last updated**: <timestamp>
```

## Postmortem template

```markdown
## Incident Postmortem: <title>

### Summary
<1-2 sentence summary of the incident>

### Timeline
| Time (UTC) | Event |
|---|---|
| HH:MM | Alert triggered |
| HH:MM | On-call acknowledged |
| HH:MM | Root cause identified |
| HH:MM | Remediation applied |
| HH:MM | Incident resolved |

### Root cause
<Detailed explanation of what went wrong>

### Impact
- **Duration**: X minutes
- **Users affected**: <number or percentage>
- **SLO impact**: <error budget consumed>

### What went well
- <item>

### What went poorly
- <item>

### Action items
| Action | Owner | Priority | Due date |
|---|---|---|---|
| <action> | <owner> | <P0/P1/P2> | <date> |
```

## Report output

The subagent writes its output to the report file allocated by the main agent. The report body contains all runbook entries formatted as markdown, ready to be merged into the `DEVOPS-RB-*` artifact.

### Report frontmatter

```yaml
---
report_id: <assigned by main agent>
kind: incident
skill: devops
stage: incident
created_at: <timestamp>
target_refs:
  - DEVOPS-RB-001
verdict: pass | at_risk | fail
summary: "<one-line summary of what was generated>"
proposed_meta_ops:
  - cmd: set-progress
    artifact_id: DEVOPS-RB-001
    completed: 1
    total: 1
items:
  - id: 1
    severity: info
    classification: content_draft
    message: "<description of generated runbooks>"
---
```

Valid `classification` values for this stage: `content_draft`, `coverage_gap`, `escalation_gap`.

- `content_draft` — normal content generation output
- `coverage_gap` — a high/critical monitoring rule has no corresponding runbook
- `escalation_gap` — an escalation path is missing contacts or has no timeout defined

## Escalation conditions

Escalate (via report `verdict: fail` and appropriate classification) when:

- A **critical monitoring rule has no feasible automated remediation** and the manual remediation requires domain knowledge not captured in any artifact. Flag as `coverage_gap`.
- The **IaC environment information is insufficient** to construct concrete diagnosis commands (e.g. resource names, namespaces, or cluster identifiers are missing from the IaC artifact). Flag as `coverage_gap` with a note that the IaC artifact needs enrichment.
- An **escalation path cannot be defined** because no on-call rotation or contact information is available. Flag as `escalation_gap` with placeholder contacts that the user must fill.

Do **not** escalate for:

- Choosing between specific CLI tool versions (use the latest stable).
- Formatting of communication templates (use the templates above).
- Postmortem template structure (use the template above).
