# Verify → Downstream Consumption Contract

This document defines what downstream skills and processes expect from Verify artifacts. Read this before declaring artifacts ready.

## Consumers and what they look for

### DevOps Review

**Consumes**: `VERIFY-RPT-*.feedback[]` where `target_skill == "devops"`.

Looks for:
- Observability config errors (wrong metric names, broken PromQL, dashboard issues).
- SLO metric validation failures (`slo_validation[].metric_collected == false`).
- Logging config issues (format mismatch, missing masking).

**Action**: updates `DEVOPS-OBS-*` based on feedback, then Verify re-runs.

### Impl Refactor

**Consumes**: `VERIFY-RPT-*.feedback[]` where `target_skill == "impl"`.

Looks for:
- Code bugs found during integration testing.
- Missing error handlers.
- API contract mismatches.

**Action**: routes issues to `impl:refactor`, then Verify re-runs.

### Arch Review

**Consumes**: `VERIFY-RPT-*.feedback[]` where `target_skill == "arch"`.

Looks for:
- Component interface mismatches.
- Dependency problems.
- Structural issues that can't be fixed at the code level.

**Action**: escalates to Arch for design review. Rare in practice.

### Sec Audit

**Consumes**: `VERIFY-RPT-*` (full report).

Looks for:
- Runtime security evidence (log masking working, no sensitive data in responses).
- Environment security posture (no hardcoded secrets, no open debug endpoints).

**Action**: uses Verify evidence as input to security audit.

### Orch Status

**Consumes**: `VERIFY-RPT-*.verdict` and artifact phases.

Looks for:
- All three Verify artifacts in `approved` phase.
- Verdict is `pass` or `pass_with_issues`.

**Action**: marks the SDLC pipeline as complete (RE → Arch → Impl → QA → DevOps → Verify → done).

## What must be present in approved artifacts

### VERIFY-ENV-* (Environment Setup)

- [ ] All application services from `IMPL-MAP-*` are represented.
- [ ] All infrastructure dependencies from `IMPL-CODE-*` are included.
- [ ] Observability stack matches the adaptive depth mode.
- [ ] Health checks are configured for every service.
- [ ] `upstream_refs` include all consumed Impl and DevOps artifact IDs.

### VERIFY-SC-* (Verification Scenarios)

- [ ] At least one integration scenario per Arch sequence diagram.
- [ ] At least one failure scenario (light mode) or one per dependency (heavy mode).
- [ ] Observability scenarios for SLO metric validation.
- [ ] Every scenario has `arch_refs` or `devops_refs` tracing to its source.

### VERIFY-RPT-* (Verification Report)

- [ ] `verdict` is set (`pass`, `pass_with_issues`, or `fail`).
- [ ] Every scenario has a result (`pass`, `fail`, `skip`) with evidence.
- [ ] Every issue has a `category` (impl/devops/arch/verify) and upstream refs.
- [ ] SLO validation results for every SLO in `DEVOPS-OBS-*`.
- [ ] Feedback entries for every non-verify issue.
- [ ] SDLC traceability chain for key scenarios.
