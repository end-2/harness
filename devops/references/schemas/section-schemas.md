# Section Schemas

The four DevOps sections each carry their own structured block inside the metadata file. The block mirrors the tables in the paired markdown document — the markdown is the human-readable source of truth for prose, and the YAML block is what downstream skills and scripts parse.

Common metadata fields (`artifact_id`, `phase`, `approval`, …) are covered in [meta-schema.md](meta-schema.md).

## 1. `pipeline`

Block key: `pipeline_config`

```yaml
pipeline_config:
  platform: github-actions  # github-actions | jenkins | gitlab-ci
  trigger:
    branches: [main]
    tags: ["v*"]
    pull_requests: true
  stages:
    - name: build
      steps: [checkout, install, lint, test, build]
      environment: ci
      condition: always()
    - name: deploy-staging
      steps: [deploy, smoke-test]
      environment: staging
      condition: success() && branch == 'main'
  caching:
    dependency_key: pnpm-lock.yaml
    artifact_paths: [dist/, .next/]
  secrets:
    - name: AWS_ACCESS_KEY_ID
      source: github-secrets
      injection_method: env
    - name: DATABASE_URL
      source: vault
      injection_method: env
  environments:
    - name: staging
      promotion_rule: auto-on-green
      approval_required: false
    - name: production
      promotion_rule: manual-gate
      approval_required: true
  deployment_method: canary  # blue-green | canary | rolling | recreate
  deployment_rationale: "SLO >= 99.9% requires zero-downtime"
  rollback_trigger:
    conditions:
      - type: error_rate
        threshold: 5%
        slo_ref: SLO-001
      - type: latency_p99
        threshold: 500ms
        slo_ref: SLO-001
  rollback_procedure:
    steps:
      - Halt canary promotion
      - Route 100% traffic to stable version
      - Notify on-call channel
    verification: "Confirm error rate returns below SLO threshold"
    notification: "#deploy-alerts"
  impl_refs: [IMPL-CODE-001]
  arch_refs: [ARCH-COMP-001]
  config_files:
    - path: .github/workflows/ci.yml
      purpose: CI pipeline definition
    - path: .github/workflows/deploy.yml
      purpose: CD pipeline definition
```

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `platform` | yes | enum | CI/CD platform. One of `github-actions`, `jenkins`, `gitlab-ci`. |
| `trigger` | yes | object | `{branches, tags, pull_requests}` — events that start the pipeline. |
| `stages` | yes | list | `{name, steps[], environment, condition}` — ordered pipeline stages. |
| `caching` | optional | object | `{dependency_key, artifact_paths}` — cache strategy for build speed. |
| `secrets` | optional | list | `{name, source, injection_method}` — secrets the pipeline consumes. |
| `environments` | yes | list | `{name, promotion_rule, approval_required}` — target environments. |
| `deployment_method` | yes | enum | One of `blue-green`, `canary`, `rolling`, `recreate`. |
| `deployment_rationale` | yes | string | Why this deployment method was chosen; should cite SLO or constraint. |
| `rollback_trigger` | yes | object | `{conditions[]}` where each condition is `{type, threshold, slo_ref}`. |
| `rollback_procedure` | yes | object | `{steps[], verification, notification}` — how to roll back. |
| `impl_refs` | yes | list[string] | `IMPL-*` ids this pipeline builds/deploys. |
| `arch_refs` | yes | list[string] | `ARCH-*` ids that inform pipeline design. |
| `config_files` | optional | list | `{path, purpose}` — repo-relative paths to pipeline config files. |

## 2. `iac`

Block key: `infrastructure_code`

```yaml
infrastructure_code:
  tool: terraform  # terraform | ansible | helm | pulumi
  provider: aws  # aws | gcp | azure
  modules:
    - name: networking
      path: infra/modules/networking
      responsibility: VPC, subnets, and security groups
      inputs:
        - name: vpc_cidr
          type: string
          default: "10.0.0.0/16"
        - name: az_count
          type: number
          default: 3
      outputs:
        - name: vpc_id
          description: ID of the created VPC
        - name: subnet_ids
          description: List of private subnet IDs
    - name: compute
      path: infra/modules/compute
      responsibility: ECS cluster and task definitions
      inputs:
        - name: instance_type
          type: string
          default: t3.medium
      outputs:
        - name: cluster_arn
          description: ARN of the ECS cluster
  environments:
    - name: staging
      overrides:
        instance_type: t3.small
        az_count: 2
    - name: production
      overrides:
        instance_type: t3.large
        az_count: 3
  state_management:
    backend: s3
    locking: dynamodb
    drift_detection: weekly
  networking:
    vpc: 10.0.0.0/16
    subnets: [10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24]
    security_groups: [api-sg, db-sg, cache-sg]
    load_balancers: [api-alb]
  cost_estimate:
    environment: production
    monthly_range:
      min: 1200
      max: 1800
      currency: USD
  comp_refs: [ARCH-COMP-001]
  constraint_refs: [RE-CON-001]
  code_files:
    - path: infra/main.tf
      purpose: Root module composition
    - path: infra/variables.tf
      purpose: Input variable declarations
```

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `tool` | yes | enum | IaC tool. One of `terraform`, `ansible`, `helm`, `pulumi`. |
| `provider` | yes | enum | Cloud provider. One of `aws`, `gcp`, `azure`. |
| `modules` | yes | list | `{name, path, responsibility, inputs[], outputs[]}` — IaC modules. `inputs` items are `{name, type, default}`. `outputs` items are `{name, description}`. |
| `environments` | yes | list | `{name, overrides}` — per-environment variable overrides. |
| `state_management` | yes | object | `{backend, locking, drift_detection}` — how state is stored and protected. |
| `networking` | optional | object | `{vpc, subnets[], security_groups[], load_balancers[]}` — network topology. |
| `cost_estimate` | optional | object | `{environment, monthly_range: {min, max, currency}}` — projected cost range. |
| `comp_refs` | yes | list[string] | `ARCH-COMP-*` ids that this infrastructure supports. |
| `constraint_refs` | optional | list[string] | `RE-CON-*` ids (constraints) that inform infrastructure choices. |
| `code_files` | optional | list | `{path, purpose}` — repo-relative paths to IaC source files. |

## 3. `observability`

Block key: `observability_config`

```yaml
observability_config:
  slo_definitions:
    - id: SLO-001
      sli: "http_request_duration_seconds{quantile='0.99'}"
      target: 99.9
      window: 30d
      error_budget: 0.1
      burn_rate_alert:
        fast_window: 5m
        slow_window: 1h
        threshold: 14.4
      re_refs: [QA:performance]
  monitoring_rules:
    - id: MON-001
      type: metric  # metric | log | trace
      condition: "burn_rate > threshold"
      threshold: 14.4
      severity: critical  # critical | high | medium | low
      channel: pagerduty
      slo_refs: [SLO-001]
  dashboards:
    - id: DASH-001
      title: "Service Overview"
      panels:
        - title: Request Rate
          query: "rate(http_requests_total[5m])"
          visualization: timeseries
        - title: Error Rate
          query: "rate(http_requests_total{status=~'5..'}[5m])"
          visualization: timeseries
      format: grafana-json  # grafana-json | datadog-json
  logging_config:
    format: json
    level_default: info
    correlation_id:
      header: X-Request-ID
      propagation: w3c-tracecontext
    masking_rules:
      - field_pattern: "*.password"
        strategy: redact
      - field_pattern: "*.ssn"
        strategy: hash
    retention:
      hot_days: 7
      warm_days: 30
      archive_days: 365
  tracing_config:
    sampling_rate: 0.1
    propagation: w3c
    span_attributes:
      - key: service.name
        source: env
      - key: deployment.environment
        source: env
  qa_refs: [QA:performance, QA:availability]
  config_files:
    - path: monitoring/prometheus-rules.yml
      purpose: Alerting and recording rules
    - path: monitoring/grafana-dashboards/
      purpose: Dashboard JSON definitions
```

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `slo_definitions` | yes | list | `{id, sli, target, window, error_budget, burn_rate_alert, re_refs}`. `burn_rate_alert` is `{fast_window, slow_window, threshold}`. |
| `monitoring_rules` | yes | list | `{id, type, condition, threshold, severity, channel, slo_refs}`. `type` is one of `metric`, `log`, `trace`. `severity` is one of `critical`, `high`, `medium`, `low`. |
| `dashboards` | optional | list | `{id, title, panels[], format}`. `panels` items are `{title, query, visualization}`. `format` is one of `grafana-json`, `datadog-json`. |
| `logging_config` | yes | object | `{format, level_default, correlation_id, masking_rules[], retention}`. `correlation_id` is `{header, propagation}`. `masking_rules` items are `{field_pattern, strategy}`. `retention` is `{hot_days, warm_days, archive_days}`. |
| `tracing_config` | optional | object | `{sampling_rate, propagation, span_attributes[]}`. `span_attributes` items are `{key, source}`. |
| `qa_refs` | yes | list[string] | QA references (e.g. `QA:performance`, `QA:availability`) that these observability definitions satisfy. |
| `config_files` | optional | list | `{path, purpose}` — repo-relative paths to observability config files. |

## 4. `runbook`

Block key: `runbook_entries`

```yaml
runbook_entries:
  - id: RB-001
    title: "High Error Rate — API Service"
    trigger_condition: "MON-001 fires (burn rate > 14.4x)"
    severity: critical
    symptoms:
      - "5xx spike on /api/*"
      - "SLO burn rate alert"
    diagnosis_steps:
      - step: 1
        action: "Check deployment status"
        command: "kubectl rollout status"
      - step: 2
        action: "Check error logs"
        command: "kubectl logs -l app=api --tail=100"
    remediation_steps:
      - step: 1
        action: "Rollback if recent deploy"
        command: "kubectl rollout undo"
        auto: true
      - step: 2
        action: "Scale up if load spike"
        command: "kubectl scale --replicas=N"
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
    rollback_ref: PL-001.rollback_procedure
    monitoring_refs: [MON-001]
    slo_refs: [SLO-001]
    communication_template: |
      **Incident**: High error rate on API service
      **Status**: Investigating / Mitigated / Resolved
      **Impact**: ...
    postmortem_template: |
      ## Timeline
      ## Root Cause
      ## Impact
      ## Action Items
```

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | yes | string | `RB-NNN`, unique within this artifact. |
| `title` | yes | string | Short human-readable title of the incident scenario. |
| `trigger_condition` | yes | string | What fires this runbook; should reference a `MON-*` id. |
| `severity` | yes | enum | One of `critical`, `high`, `medium`, `low`. |
| `symptoms` | yes | list[string] | Observable indicators that this scenario is occurring. |
| `diagnosis_steps` | yes | list | `{step, action, command}` — ordered diagnostic actions. |
| `remediation_steps` | yes | list | `{step, action, command, auto}` — ordered fix actions. `auto` indicates whether the step can be automated. |
| `escalation_path` | yes | list | `{level, contact, channel, timeout_minutes}` — escalation tiers. |
| `rollback_ref` | optional | string | Reference to a pipeline rollback procedure (e.g. `PL-001.rollback_procedure`). |
| `monitoring_refs` | yes | list[string] | `MON-*` ids that trigger this runbook. |
| `slo_refs` | yes | list[string] | `SLO-*` ids that this runbook protects. |
| `communication_template` | optional | string | Markdown template for incident communication. |
| `postmortem_template` | optional | string | Markdown template for post-incident review. |
