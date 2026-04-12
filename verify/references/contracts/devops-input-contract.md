# DevOps → Verify Input Contract

This document defines how Verify consumes DevOps artifacts to provision the observability stack and derive verification scenarios.

## DEVOPS-OBS-* → Observability Stack

| DevOps field | Verify usage |
|-------------|-------------|
| `observability_config.slo_definitions[]` | Load into Prometheus for metric collection validation. Each SLO becomes an observability verification scenario. |
| `observability_config.monitoring_rules[]` | Load as Prometheus alerting rules. Verify syntax and (where possible) trigger condition. |
| `observability_config.dashboards[]` | Load into Grafana for rendering validation. Check that panels show data when metrics exist. |
| `observability_config.logging_config.format` | Validate application log output matches this format. |
| `observability_config.logging_config.correlation_id` | Verify correlation ID propagation across services. |
| `observability_config.logging_config.masking[]` | Verify sensitive data is masked in log output. |
| `observability_config.tracing_config.propagation` | Verify trace context header propagation (W3C Trace Context). |
| `observability_config.tracing_config.sampling_rate` | Configure Tempo/Jaeger sampling in the local stack. |
| `observability_config.config_files[]` | Actual config file paths to load into the observability stack. |

## DEVOPS-IAC-* → Infrastructure Mapping

| DevOps field | Verify usage |
|-------------|-------------|
| `infrastructure_code.modules[]` | Map IaC modules to Docker Compose services (cloud resources → local equivalents). |
| `infrastructure_code.networking` | Derive Docker network topology. |
| `infrastructure_code.environments[]` | Determine if multi-environment (triggers heavy mode). |

## DEVOPS-PL-* → Deployment Verification

| DevOps field | Verify usage |
|-------------|-------------|
| `pipeline_config.deployment_method` | Inform deployment-related scenarios (canary → version comparison, blue-green → switch test). |
| `pipeline_config.rollback_trigger` | Create scenarios that reproduce rollback conditions. |

## DEVOPS-RB-* → Runbook Reproduction

| DevOps field | Verify usage |
|-------------|-------------|
| Runbook `trigger_condition` | Create failure scenarios that reproduce the trigger. |
| Runbook `diagnosis_steps` | Verify that diagnosis commands work in the local environment. |
| Runbook `remediation_steps` | Verify that remediation steps are executable (where safe). |

## Validation rules

Before provisioning, Verify checks:

1. `DEVOPS-OBS-*` exists and has `slo_definitions` (at least one SLO).
2. `monitoring_rules[]` use valid PromQL syntax.
3. `dashboards[]` reference metrics that application services should expose.
4. If `logging_config.masking` is set, the masking patterns are testable.
5. If `tracing_config` is set, the sampling rate and propagation format are specified.

If validation fails, Verify stops and tells the user which DevOps artifact needs attention.
