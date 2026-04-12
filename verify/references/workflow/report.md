# Report — Verification Report Generation Stage

**Role**: Aggregate all verification results into a structured report with upstream skill feedback and an overall verdict.

**Runs in**: subagent (clean context for objective aggregation).

## Entry conditions

- `execute` stage completed — scenario results available.
- `diagnose` stage completed (if any failures existed) — issues classified and (some) resolved.
- All evidence artifacts collected.

## Report structure

### 1. Executive summary

A one-paragraph summary including:
- Overall verdict.
- Scenario statistics (total, pass, fail, skip).
- Issue count (by severity and status).
- SLO metric validation results.

### 2. Scenario results

For each scenario, record:
- `scenario_id`: reference to `VERIFY-SC-*` scenario.
- `status`: `pass`, `fail`, or `skip`.
- `duration_seconds`: execution time.
- `evidence`: list of evidence references (EVD-001, etc.) with type and summary.

Order by category (integration → failure → load → observability), then by ID.

### 3. Evidence artifacts

Catalogue all collected evidence:
- `id`: EVD-001, EVD-002, ...
- `type`: response, metric_query, log_sample, trace, dashboard.
- `query` or `command`: what was executed to collect it.
- `result`: the value or summary.
- `timestamp`: when it was collected.

### 4. Issues

List all issues from the diagnose stage, including:
- Fixed issues (with resolution details).
- Escalated issues (with upstream artifact references).
- Deferred issues (with justification).

### 5. Environment health

Final state of the environment after all scenarios:
- Per-service: status, restart count, memory usage.
- Overall: any services that required manual intervention.

### 6. SLO metric validation

For each SLO in `DEVOPS-OBS-*.slo_definitions`:
- Is the SLI metric being collected by Prometheus?
- What is a sample value?
- Is the metric plausibly correct (non-zero, reasonable range)?

This validates that the DevOps observability setup will actually work in production — that the SLOs aren't just documentation but are backed by real metrics.

### 7. Upstream skill feedback

Classify all issues by the skill that should address them:

**Impl feedback**: code bugs, missing error handling, API contract issues.
**DevOps feedback**: observability config errors, missing metrics, wrong queries.
**Arch feedback**: structural issues (rare — usually escalated during diagnose).

Each feedback entry includes:
- The issue ID.
- The target artifact (e.g., `IMPL-CODE-001`).
- A summary of what needs to change.

### 8. SDLC traceability chain

For each verified scenario, trace the full chain:
```
RE requirement → Arch decision → Impl code → DevOps config → Verify evidence
```

This demonstrates that the SDLC pipeline produces working software — requirements are realised in architecture, implemented in code, operationalised in DevOps, and **verified at runtime**.

## Verdict logic

| Condition | Verdict |
|-----------|---------|
| All scenarios pass, no issues | `pass` |
| All scenarios pass (some after fixes), issues all resolved | `pass_with_issues` |
| At least one scenario still fails after diagnosis | `fail` |

## Output

The subagent writes the report to the allocated report file. The main agent creates the artifact:

```bash
python ${SKILL_DIR}/scripts/artifact.py init --section report
```

and merges the report body into `VERIFY-RPT-*.md`.

## Report frontmatter

```yaml
kind: report
classification values:
  - verdict_summary     # overall pass/fail assessment
  - impl_feedback       # issues to route to Impl skill
  - devops_feedback     # issues to route to DevOps skill
  - arch_feedback       # issues to route to Arch skill
  - traceability_gap    # SDLC chain breaks
  - slo_gap             # SLO metric not collectible
```

## Environment teardown

After the report is complete and the user has reviewed it:

```bash
docker compose -f docker-compose.verify.yml down -v
```

The `-v` flag removes volumes to ensure a clean state for future runs. Only tear down after the user confirms they don't need the environment running for further investigation.
