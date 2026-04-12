# Adaptive Depth

DevOps runs in one of two modes — **light** or **heavy** — and the mode drives how much of the 8-stage workflow produces. The goal is correct sizing.

## How the mode is decided

DevOps mode is inherited from Arch/Impl mode. Detection signals (check in order):
1. If `ARCH-DIAG-*` has a Container diagram → heavy
2. Or if `ARCH-COMP-*.components` has more than 3 entries → heavy
3. Or if multiple deployment environments are specified in Arch/Impl → heavy
4. Otherwise → light

Tell user which mode and why. User may override.

## What light mode means

Light mode is correct for a small system, not lazy.

| Stage | Light mode action |
|-------|------------------|
| slo | ≤ 3 core SLOs (availability, latency, error rate). Simple error budgets. Skip multi-window burn-rate. |
| iac | Single environment, single module. Skip environment overrides, drift detection, cost estimation. |
| pipeline | Single pipeline with build+test+deploy stages. Skip matrix builds, multi-environment promotion. |
| strategy | Simple rolling or recreate deployment. Skip canary/blue-green unless SLO demands zero-downtime. |
| monitor | Basic alerting rules for core SLOs. Simple dashboard. Skip RED/USE framework, distributed tracing. |
| log | Standard structured logging config. Skip per-service namespace customization, complex masking rules. |
| incident | 1-2 critical runbooks only (service down, deploy failure). Skip per-alert runbooks. |
| review | Feedback loop check + basic traceability. Skip deep security/cost analysis. |

## What heavy mode means

| Stage | Heavy mode action |
|-------|------------------|
| slo | Comprehensive SLOs per component/service. Multi-window burn-rate alerts. Error budget policies. |
| iac | Multi-environment modules with overrides. Full networking (VPC, subnets, security groups). State management with drift detection. Cost estimates. |
| pipeline | Multi-stage with environment promotion gates. Matrix builds, parallel steps, caching optimization. Security scanning stage. |
| strategy | Canary or blue-green with traffic shaping. Automated rollback tied to SLO burn-rate. Deploy ordering from dependency graph. |
| monitor | Full RED/USE metrics. Grafana/Datadog dashboards per service. Distributed tracing with sampling. Canary-vs-baseline comparison metrics. |
| log | Per-service log namespaces. Correlation ID propagation. PII masking rules from RE constraints. Log-based metrics feeding into monitoring. |
| incident | One runbook per alert/failure scenario. Detailed diagnosis with actual commands. Escalation paths with timeouts. Postmortem and communication templates. |
| review | Full feedback-loop integrity. Deep traceability. Security best-practice check. Cost optimization review. Environment consistency. |

## Mode is not about quality

Both modes produce production-shaped output. Mode controls how much operational structure accompanies the core artifacts. Light-mode DevOps still respects Arch boundaries, still creates SLOs, still runs the review. It just doesn't generate 20 alerting rules when 3 would cover the actual SLOs.
