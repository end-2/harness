# RE Input Contract

How the DevOps skill consumes RE quality attributes and constraints — indirectly, through Arch's `re_refs` and `constraint_ref` chains — and transforms them into SLI/SLO definitions, IaC constraints, and monitoring priorities. Read this before `slo` when you need to understand how an RE quality attribute becomes a concrete DevOps deliverable.

## Indirect access model

DevOps does **not** read RE artifacts directly. RE quality attributes and constraints reach DevOps through two Arch relay fields:

- **`re_refs`** — present on `ARCH-DEC-*`, `ARCH-COMP-*`, and propagated through `IMPL-IDR-*`. Each `re_ref` points to an `RE-QA-*` (quality attribute) or `RE-CON-*` (constraint) artifact. DevOps resolves these references by reading the Arch artifact's `re_refs` list and then looking up the referenced RE metadata in `./artifacts/re/`.
- **`constraint_ref`** — present on `ARCH-TECH-*`. Each `constraint_ref` points to an `RE-CON-*` artifact that imposes hard or soft constraints on the technology choice. DevOps reads these to determine non-negotiable IaC parameters.

This indirection is intentional: Arch already filtered, prioritised, and reconciled the RE requirements into architectural decisions. DevOps inherits that reconciled view rather than re-interpreting raw RE.

To resolve references, walk the chain:

```
# Find all re_refs across Arch artifacts
python ${SKILL_DIR}/../arch/scripts/artifact.py list   # get Arch artifact IDs
python ${SKILL_DIR}/../arch/scripts/artifact.py show <arch-id>   # read re_refs field
# Then read the referenced RE artifact
cat ./artifacts/re/<re-id>.meta.yaml
```

## RE quality attributes → SLI/SLO mapping

Each RE quality attribute (`RE-QA-*`) referenced by an Arch artifact must produce at least one SLI in the Observability artifact. The transformation depends on whether the attribute is quantitative or qualitative.

### Quantitative attributes (direct mapping)

When the RE quality attribute includes a measurable `metric` with a numeric threshold, it maps directly to an SLI and SLO:

| RE metric pattern | SLI | SLO target | Error budget |
|-------------------|-----|------------|--------------|
| `"response time < 200ms"` | `http_request_duration_seconds{quantile="0.99"}` | 99th percentile < 200ms | 1% of requests may exceed 200ms in the SLO window |
| `"availability >= 99.9%"` | `1 - (error_responses / total_responses)` | >= 99.9% over 30-day rolling window | 43.2 minutes downtime per 30 days |
| `"throughput >= 1000 rps"` | `rate(http_requests_total[5m])` | >= 1000 requests/second sustained | Alert when sustained rate drops below threshold |
| `"error rate < 0.1%"` | `rate(http_responses_5xx[5m]) / rate(http_responses_total[5m])` | < 0.1% over 30-day rolling window | 0.1% of total request budget |
| `"data freshness < 5s"` | `time() - last_successful_sync_timestamp` | Lag < 5 seconds at 99th percentile | 1% of observations may exceed 5s lag |
| `"startup time < 30s"` | `container_start_duration_seconds` | < 30 seconds at 95th percentile | Affects deployment strategy (rolling update batch size) |

### Qualitative attributes (proxy mapping)

When the RE quality attribute is qualitative (e.g. "high user satisfaction", "easy to maintain", "secure by default"), it cannot map directly to an SLI. DevOps must derive proxy indicators:

| RE qualitative pattern | Proxy SLI | Rationale |
|------------------------|-----------|-----------|
| `"high user satisfaction"` | Apdex score based on response time thresholds | User satisfaction correlates with perceived performance |
| `"reliable"` / `"dependable"` | Availability SLI + error rate SLI | Reliability is the composite of uptime and correctness |
| `"scalable"` | Resource utilisation headroom (CPU/memory < 70% at peak) | Scalability means the system handles growth without degradation |
| `"performant"` | Latency P50/P95/P99 SLIs | Performance is measured by response time distribution |
| `"secure"` | No SLI (security is a constraint, not an SLO) — but flag for the `security` skill | Security attributes drive IaC constraints, not SLOs |

**Escalation condition**: if a qualitative attribute has no reasonable proxy, present the options to the user and ask them to pick a measurable proxy or confirm the attribute is a constraint rather than an SLO target.

### SLO derivation rules

1. **One SLO per measurable quality attribute per affected component.** If `ARCH-COMP-003` carries `re_refs: [RE-QA-001, RE-QA-002]`, it gets at least two SLOs.
2. **Error budget calculation**: `error_budget = 1 - SLO_target`. For a 99.9% availability SLO over 30 days, the budget is 43.2 minutes.
3. **Multi-window burn-rate alerting**: each SLO gets at least two burn-rate alert windows (fast: 5m/1h for detecting rapid degradation; slow: 30m/6h for detecting gradual drift). The thresholds derive from Google SRE's multi-window, multi-burn-rate approach.
4. **SLO window**: default to 30-day rolling unless the RE attribute specifies otherwise.

## RE constraints → IaC constraints

Each RE constraint (`RE-CON-*`) referenced via `constraint_ref` translates into a non-negotiable IaC parameter. The constraint's `type` and `hardness` determine how it is applied.

### Hard constraints (non-negotiable)

| RE constraint pattern | IaC parameter | Effect |
|-----------------------|---------------|--------|
| Cloud provider lock (`"AWS only"`, `"GCP only"`) | `provider` block in Terraform, all resource types scoped to that provider | No resources from other providers may appear in the IaC |
| Region lock (`"eu-west-1"`, `"us-east-1 only"`) | `region` / `location` parameter on every resource | All resources provisioned in the specified region. Multi-region requires explicit Arch approval |
| Compliance (`"SOC2"`, `"HIPAA"`, `"GDPR"`) | Encryption at rest enabled on all storage, encryption in transit (TLS) on all endpoints, audit logging enabled | Non-negotiable security baseline applied to every resource |
| Data residency (`"data must stay in EU"`) | Storage resources restricted to EU regions, cross-region replication disabled or restricted | Pipeline must validate no data leaves the specified boundary |
| Regulatory log retention (`"logs retained 7 years"`) | Log storage lifecycle policy set to the required retention period | CloudWatch/S3 lifecycle rules, or equivalent, enforce the retention |

### Soft constraints (recorded, not enforced)

Soft constraints are recorded as comments in the IaC modules and as `notes` in the metadata. They guide decisions but do not block generation. Example: `"prefer spot instances"` becomes a comment in the compute module recommending spot/preemptible instances, but the module still works without them.

### Regulatory constraint → log retention mapping

Regulatory constraints deserve special attention because they affect both IaC and observability:

```
RE-CON: "GDPR compliance required"
  → IaC: encryption at rest on all storage, TLS on all endpoints
  → Observability: PII masking in logs, data retention policy in log config
  → Runbook: data subject access request (DSAR) procedure

RE-CON: "audit trail required for 7 years"
  → IaC: S3 bucket with lifecycle policy (7-year retention, Glacier transition)
  → Observability: audit log pipeline separate from operational logs
  → Runbook: audit log retrieval procedure
```

## Priority → monitoring priority

RE quality attributes carry a `priority` (or are ordered by priority in the RE artifact set). Higher-priority attributes get tighter monitoring:

| RE priority | Burn-rate alert sensitivity | Dashboard placement | Runbook depth |
|-------------|----------------------------|--------------------|--------------| 
| **critical** / **P0** | Fast window: 2m/10m (14.4x burn rate). Page immediately on breach. | Top of the primary dashboard, always visible | Full runbook with automated remediation steps and escalation to on-call |
| **high** / **P1** | Fast window: 5m/1h (6x burn rate). Page within 5 minutes of sustained breach. | Primary dashboard, second row | Detailed runbook with manual remediation and escalation path |
| **medium** / **P2** | Slow window: 30m/6h (3x burn rate). Ticket, no page. | Secondary dashboard or collapsed panel | Standard runbook with diagnosis steps and remediation guidance |
| **low** / **P3** | Slow window: 6h/3d (1x burn rate). Weekly review only. | Reporting dashboard, not real-time | Brief runbook or reference to general procedures |

**Priority inheritance**: when an Arch component carries multiple `re_refs` with different priorities, the component's monitoring inherits the **highest** priority among them. A component with one P0 and two P2 quality attributes gets P0-level burn-rate alerting on all its SLOs.

## Common RE → DevOps transformation table

End-to-end reference showing how RE patterns flow through Arch into DevOps deliverables:

| RE artifact | Arch relay | DevOps output |
|-------------|------------|---------------|
| `RE-QA: "P99 latency < 200ms"` | `ARCH-COMP.re_refs → RE-QA-001` | SLI: `http_request_duration_seconds{q="0.99"} < 0.2` → SLO: 99th pct < 200ms, 30d window → burn-rate alert: 5m/1h at 6x → dashboard: latency heatmap → runbook: latency degradation |
| `RE-QA: "availability >= 99.95%"` | `ARCH-DEC.re_refs → RE-QA-002` | SLI: success ratio → SLO: >= 99.95%, 30d → error budget: 21.6 min/30d → deployment strategy: blue-green (protects budget) → rollback trigger: budget burn > 2x |
| `RE-QA: "handle 10x traffic spike"` | `ARCH-COMP.re_refs → RE-QA-003` | SLI: resource utilisation headroom → IaC: auto-scaling policy (min/max/target) → monitor: scaling event metric → runbook: capacity planning review |
| `RE-CON: "AWS eu-west-1 only"` (hard) | `ARCH-TECH.constraint_ref → RE-CON-001` | IaC: `provider.aws.region = "eu-west-1"`, all resources in eu-west-1 → pipeline: deployment targets locked to eu-west-1 |
| `RE-CON: "SOC2 compliance"` (hard) | `ARCH-TECH.constraint_ref → RE-CON-002` | IaC: encryption at rest + TLS everywhere → observability: audit log pipeline, 1-year retention → runbook: compliance audit procedure |
| `RE-CON: "budget < $500/month"` (soft) | `ARCH-TECH.constraint_ref → RE-CON-003` | IaC: cost tags on all resources, right-sizing recommendations in comments → monitor: cost alert at 80% budget → runbook: cost optimisation checklist |
| `RE-QA: "easy to debug"` (qualitative) | `ARCH-COMP.re_refs → RE-QA-004` | Proxy SLI: trace completeness (% of requests with full trace) → structured logging with correlation IDs → dashboard: trace search panel |

## Traceability propagation

Every SLO definition must link upstream through Arch to the RE quality attribute:

```
python ${SKILL_DIR}/scripts/artifact.py link <devops-obs-id> --upstream ARCH-DEC-001
# The chain is: RE-QA-001 → ARCH-DEC-001 (via re_refs) → DEVOPS-OBS-001 (via upstream_refs)
```

Every IaC constraint derived from an RE constraint must link upstream to the Arch tech-stack entry that carries the `constraint_ref`:

```
python ${SKILL_DIR}/scripts/artifact.py link <devops-iac-id> --upstream ARCH-TECH-003
# The chain is: RE-CON-001 → ARCH-TECH-003 (via constraint_ref) → DEVOPS-IAC-001 (via upstream_refs)
```

DevOps does not link directly to `RE-*` artifacts. The Arch layer is always the intermediary. If an RE quality attribute has no Arch artifact carrying its `re_ref`, it was deliberately excluded by Arch and DevOps must not resurrect it.

## When RE is unreachable through Arch

If an Arch artifact's `re_refs` point to an `RE-*` artifact that does not exist or cannot be read, treat it as a broken traceability link. Log a warning, generate the DevOps artifact without the SLO (marking it as `incomplete` in the metadata), and escalate to the user. Do not fabricate quality attribute values.
