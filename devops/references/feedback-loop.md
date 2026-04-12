# Deploy → Observe Feedback Loop

This document is the verification checklist for the review stage. The feedback loop is the signature value of unifying Deploy and Observe into one skill — without it, DevOps is just a collection of config generators.

## Loop connections

| From | To | Connection | What to verify |
|------|----|------------|---------------|
| `strategy` | `monitor` | Deployment method determines monitoring metrics | Canary deploy → canary-vs-baseline comparison metric exists; Blue-green → both environments have health-check monitoring |
| `monitor` | `strategy` | SLO burn-rate triggers rollback | Every `rollback_trigger.condition` in Pipeline Config references a `monitoring_rules.id` that is connected to an `slo_definitions.id` |
| `slo` | `strategy` | Error budget drives deployment conservatism | If error budget < 25% remaining, deployment method should be more conservative (documented in strategy rationale) |
| `strategy` | `incident` | Rollback procedure feeds runbook remediation | Every runbook's `remediation_steps` that involves rollback references `pipeline_config.rollback_procedure` |
| `monitor` | `incident` | Alert conditions trigger runbooks | Every `monitoring_rules.id` with severity ≥ high has at least one `runbook_entries` with matching `monitoring_refs` |
| `log` | `monitor` | Log-based metrics feed monitoring rules | Any `monitoring_rules` of `type: log` has a corresponding `logging_config` entry that produces the metric |

## Checklist (used by review stage)

### Completeness checks
- [ ] Every `slo_definitions` entry has at least one `monitoring_rules` entry with `slo_refs` pointing to it
- [ ] Every `monitoring_rules` entry with severity ≥ high has at least one `runbook_entries` with `monitoring_refs` pointing to it
- [ ] Every `pipeline_config.rollback_trigger` condition references a valid `monitoring_rules.id`
- [ ] Every `runbook_entries` that mentions rollback references `pipeline_config.rollback_procedure`
- [ ] Every Arch component with type `service` or `gateway` has at least one SLO

### Consistency checks
- [ ] SLO burn-rate alert thresholds match between `slo_definitions.burn_rate_alert` and the corresponding `monitoring_rules.threshold`
- [ ] Rollback trigger thresholds are consistent with SLO error budgets
- [ ] Deployment method is appropriate for SLO availability target (≥ 99.9% → zero-downtime required)
- [ ] Log retention policy satisfies any RE regulatory constraints

### Traceability checks
- [ ] Every IaC module has `comp_refs` pointing to an `ARCH-COMP-*`
- [ ] Every pipeline build step traces to `IMPL-CODE-*.build_config` or `IMPL-GUIDE-*.build_commands`
- [ ] Every SLO traces to a RE quality attribute via `re_refs` (through Arch)
- [ ] Every deployment decision has `arch_refs` justifying it

## How to use this checklist

The review subagent reads this file and checks each item against the four DevOps artifacts. Each failed check becomes an `item` in the review report with a classification of `feedback_loop_gap`, `traceability_gap`, or `consistency_gap`. The main agent then routes the gap back to the responsible stage for fixing.
