# Downstream Consumption Contract

What downstream skills (`security`, `management`, operations consumers) expect to find in the four DevOps category artifacts. Read this before transitioning any DevOps artifact to `approved`.

## security — pipeline and IaC security audit

**Reads**: `DEVOPS-PL-*`, `DEVOPS-IAC-*`, `DEVOPS-OBS-*`.

- `DEVOPS-PL-*.pipeline_config.secrets` → verify no secrets hardcoded, proper injection method
- `DEVOPS-PL-*.pipeline_config.stages` → verify security scan stages exist (SAST, dependency audit)
- `DEVOPS-IAC-*.infrastructure_code.modules` → IaC security scan targets (Terraform/Helm)
- `DEVOPS-IAC-*.infrastructure_code.networking.security_groups` → verify least-privilege network rules
- `DEVOPS-OBS-*.observability_config.logging_config.masking_rules` → verify PII/sensitive data masking compliance

security will flag if: secrets management is missing, IaC has overly permissive security groups, logging lacks masking for compliance-required fields.

## management — release planning and risk

**Reads**: `DEVOPS-PL-*`, `DEVOPS-IAC-*`, `DEVOPS-OBS-*`.

- `DEVOPS-PL-*.pipeline_config.environments` → release promotion chain and approval gates
- `DEVOPS-IAC-*.infrastructure_code.cost_estimate` → budget planning per environment
- `DEVOPS-OBS-*.observability_config.slo_definitions` → SLO achievement reporting
- `DEVOPS-IAC-*.infrastructure_code.state_management` → infrastructure drift risk

management will flag if: cost estimates are missing for production environments, or SLO targets have no historical baseline.

## qa — quality gate integration

**Reads**: `DEVOPS-PL-*`, `DEVOPS-OBS-*`.

- `DEVOPS-PL-*.pipeline_config.stages` → verify test stages exist and run before deploy
- `DEVOPS-OBS-*.observability_config.slo_definitions` → quality gate SLO criteria

## operations — handoff

**Reads**: `DEVOPS-RB-*`, `DEVOPS-OBS-*`, `DEVOPS-IAC-*`.

- `DEVOPS-RB-*.runbook_entries` → operational procedures for incident response
- `DEVOPS-OBS-*.observability_config` → monitoring and alerting setup to maintain
- `DEVOPS-IAC-*.infrastructure_code` → infrastructure to operate

operations will flag if: runbooks lack actual diagnostic commands, or escalation paths have no contacts defined.

## Downstream linking

Before approving, add downstream refs:
```
python ${SKILL_DIR}/scripts/artifact.py link <devops-pl-id> --downstream SEC-AUDIT-001
```
If downstream artifacts don't exist yet, leave downstream_refs empty — downstream skills will back-fill.
