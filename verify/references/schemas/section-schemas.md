# Section Schemas (Verify)

This document defines the section-specific structured fields in each Verify metadata file. These fields live alongside the common fields defined in [meta-schema.md](meta-schema.md).

## Environment Setup (`VERIFY-ENV-*`)

```yaml
environment_config:
  mode: light | heavy
  compose_file: docker-compose.verify.yml
  services:
    - name: string              # Docker service name
      type: application | infrastructure | observability
      image: string | null      # Docker image (for infrastructure/observability)
      build_path: string | null # Build context (for application services)
      ports: list[string]       # "host:container" format
      depends_on: list[string]  # Other service names
      health_check:
        endpoint: string | null   # HTTP health endpoint
        command: string | null    # Shell health command
        interval: string          # e.g. "10s"
        retries: int
      environment: list[string]   # KEY=value format
      component_ref: string | null # ARCH-COMP-* ID (for application services)
  observability_stack:
    prometheus:
      port: int
      scrape_targets: list[string]  # service:port
      rules_file: string            # path to alerting rules
    grafana:
      port: int
      dashboards_dir: string
      datasources: list[string]     # prometheus, loki, tempo
    loki: null | object             # null in light mode
      port: int
      log_drivers: list[string]     # services sending logs
    tempo: null | object            # null in light mode
      port: int
      receivers: list[string]       # otlp, etc.
  network_topology:
    networks:
      - name: string
        driver: string              # bridge
    exposed_ports:
      - service: string
        host_port: int
        container_port: int
  startup_order: list[string]       # service names in startup order
  instrumentation_status:
    metrics_endpoint: string | null
    structured_logging: bool | null
    trace_propagation: string | null  # "W3C Trace Context" or null
    gaps:
      - type: string               # missing_metrics, missing_logging, missing_tracing
        description: string
        suggestion: string
  impl_refs: list[string]          # IMPL-MAP-*, IMPL-CODE-*, IMPL-GUIDE-*
  devops_refs: list[string]        # DEVOPS-IAC-*, DEVOPS-OBS-*
  arch_refs: list[string]          # ARCH-COMP-* (indirect, via impl component_ref)
```

## Verification Scenario (`VERIFY-SC-*`)

```yaml
verification_scenarios:
  - id: string                    # SC-001, SC-101, SC-201, SC-301
    category: integration | failure | load | observability
    title: string
    description: string
    preconditions:
      - string                    # "All services healthy", "Database seeded"
    steps:
      - action: string           # "POST /api/v1/users", "docker stop postgres"
        type: http_request | fault_injection | recovery | metric_query | log_query | trace_query | db_query | load_injection
        payload: string | null    # Request body (for http_request)
        details: string | null    # Additional execution details
    expected_results:
      - type: response | metric | log | trace | dashboard
        condition: string         # "status == 201", "error_rate increases"
    evidence_type: list[string]   # Types of evidence to collect
    arch_refs: list[string]       # ARCH-DIAG-*, ARCH-COMP-*
    re_refs: list[string]         # FR-*, NFR-* (via Arch)
    slo_refs: list[string]        # SLO-* (from DEVOPS-OBS)
```

**ID conventions**:
- Integration: SC-001 through SC-099
- Failure: SC-101 through SC-199
- Load: SC-201 through SC-299
- Observability: SC-301 through SC-399

## Verification Report (`VERIFY-RPT-*`)

```yaml
verification_report:
  verdict: pass | pass_with_issues | fail
  scenario_results:
    - scenario_id: string         # SC-001
      status: pass | fail | skip
      duration_seconds: float
      evidence:
        - type: response | metric | log | trace | dashboard
          summary: string
          query: string | null    # PromQL, LogQL, trace ID
          value: any | null       # query result
  evidence_artifacts:
    - id: string                  # EVD-001
      type: response | metric_query | log_sample | trace | dashboard
      query: string | null        # what was executed
      result: string              # value or summary
      timestamp: string           # ISO 8601 UTC
  issues:
    - id: string                  # ISS-001
      severity: high | med | low
      category: impl | devops | arch | verify
      description: string
      root_cause: string
      resolution: string | null   # null if not fixed
      status: fixed | escalated | deferred
      scenario_refs: list[string] # SC-* that exposed this
      impl_refs: list[string]     # IMPL-* (if category == impl)
      devops_refs: list[string]   # DEVOPS-* (if category == devops)
      arch_refs: list[string]     # ARCH-* (if category == arch)
  environment_health:
    services:
      - name: string
        status: healthy | unhealthy | stopped
        restarts: int
        memory_mb: int
  slo_validation:
    - slo_id: string              # SLO-001
      sli_metric: string          # prometheus metric name
      metric_collected: bool
      sample_value: any           # numeric value or null
      threshold: string           # "99.9% availability"
      devops_refs: list[string]   # DEVOPS-OBS-*
  feedback:
    - target_skill: impl | devops | arch
      target_refs: list[string]   # artifact IDs in the target skill
      issue_refs: list[string]    # ISS-* from this report
      summary: string
  arch_refs: list[string]
  impl_refs: list[string]
  devops_refs: list[string]
  re_refs: list[string]
```
