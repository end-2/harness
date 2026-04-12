# Adaptive Depth — Light vs Heavy Mode

Verify output depth follows Arch/Impl mode. The goal is correct sizing: a single-service app doesn't need a full observability stack, and a distributed system needs more than a health check.

## Detection rules (in order)

1. Read `IMPL-MAP-*` entries and count unique `component_ref` values → count of Arch components.
2. Check `DEVOPS-IAC-*.environments[]` length → multi-environment indicator.
3. Check if `ARCH-DIAG-*` includes a C4 Container diagram (via Impl/DevOps refs) → distributed system indicator.

| Condition | Mode |
|-----------|------|
| Arch components ≤ 3 **and** single environment **and** no Container diagram | **light** |
| Arch components > 3 **or** multi-environment **or** Container diagram present | **heavy** |

## Light mode

**Observability stack**: Prometheus + Grafana only. No Loki, no Tempo.

**Scenarios**:
- 1 integration scenario (primary happy path).
- 1 failure scenario (primary dependency unavailability).
- 1 observability scenario (SLO metric collection check).
- 0–1 load scenario (optional, only if an SLO has a latency target).
- **Total**: 3-4 scenarios.

**Evidence collection**:
- HTTP responses.
- Prometheus metric queries.
- Docker logs (no Loki, use `docker compose logs` directly).
- No distributed tracing verification.

**Report depth**:
- Scenario results with basic evidence.
- Issue list (if any).
- SLO metric validation.
- Minimal feedback section.

## Heavy mode

**Observability stack**: Prometheus + Grafana + Loki + Tempo. Full stack.

**Scenarios**:
- One integration scenario per Arch sequence diagram.
- One failure scenario per component dependency (unavailability + latency + error).
- 1 load scenario (concurrent burst).
- Comprehensive observability scenarios: SLO metrics, alert rules, dashboards, log format, masking, trace propagation, runbook triggers.
- **Total**: comprehensive.

**Evidence collection**:
- HTTP responses.
- Prometheus metric queries (PromQL).
- Loki log queries (LogQL).
- Tempo trace lookups (trace ID, span tree).
- Grafana dashboard rendering confirmation.

**Report depth**:
- Full scenario results with rich evidence.
- Detailed issue list with root-cause analysis.
- SLO metric validation with sample values.
- Comprehensive upstream feedback.
- Full SDLC traceability chain.

## Both modes share

- Docker Compose as the runtime environment.
- Health check validation for all services.
- `artifact.py` metadata management.
- Subagent delegation for scenario derivation and report generation.
- File-based handoff contract.
- Same verdict logic (pass / pass_with_issues / fail).

**Important**: light mode is not lazy — it is correct sizing. Heavy mode is not over-engineering — it is comprehensive coverage for systems that need it. Both are production-shaped in intent; mode controls overhead, not quality.
