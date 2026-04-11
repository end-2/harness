# Downstream Consumption Contract

What downstream skills (`deployment`, `operation`, `management`, `security`) expect to find in the four QA sections. Read this before transitioning any QA artifact to `approved`, so you can verify the hand-off is consumable.

## deployment — release gate and pipeline wiring

**Reads**: `QA-STRATEGY-*`, `QA-REPORT-*`.

- `QA-STRATEGY-*.test_strategy.environment_matrix` → which environments the deployment pipeline must provide (local / ci / staging / prod-like).
- `QA-STRATEGY-*.test_strategy.quality_gate_criteria` → the criteria that must hold for a release to be allowed. Deployment treats these as the merge / promote gate.
- `QA-REPORT-*.quality_gate.verdict` → the actual gate verdict for the most recent run. `pass` is the only verdict that allows a promote-to-prod step.
- `QA-REPORT-*.quality_gate.actuals` → the numbers shown on the deployment dashboard.

deployment will fail its run if: the Quality Report's verdict is not `pass`, or any environment in the strategy's matrix is not represented in the deployment plan, or `quality_gate.criteria` does not list a Must coverage threshold.

## operation — SLO baselines and runbook triggers

**Reads**: `QA-STRATEGY-*`, `QA-REPORT-*`, `QA-RTM-*`.

- `QA-REPORT-*.quality_report.nfr_results` → first-cut SLO baselines. The actual measured value becomes the SLO floor; the residual headroom from the target becomes the alert margin.
- `QA-STRATEGY-*.test_strategy.nfr_test_plan` → the load profile that produced the baseline; operation re-uses it as a synthetic monitor.
- `QA-RTM-*.rtm_rows[].coverage_status == partial` → uncovered behaviour is a runbook risk; operation lists those as "manual verification on every release".

operation will fail its run if: there are NFR results without a measured `actual`, or the residual risk list mentions a Must row that did not get a resolution recorded.

## management — coverage trend and onboarding

**Reads**: `QA-RTM-*`, `QA-REPORT-*`.

- `QA-RTM-*.rtm_rows` → the coverage roll-up by MoSCoW priority; management tracks the trend over time as a proxy for delivery maturity.
- `QA-REPORT-*.quality_report.recommendations` → the input to the next iteration's planning.
- `QA-REPORT-*.quality_report.residual_risks` → the candidate list for the technical debt register.

## security — security testing and vulnerability gates

**Reads**: `QA-SUITE-*`, `QA-REPORT-*`.

- `QA-SUITE-*.test_cases` with `re_refs` pointing at security-classified RE rows → the security baseline tests; security checks they are still passing in the latest report.
- `QA-REPORT-*.quality_gate.actuals.failed_tests` → if any security baseline test failed, security blocks the release independently.

security will fail its run if: a Must security RE row has no test case in any QA suite, or the latest Quality Report verdict is `fail` on a security NFR.

## Downstream linking

Before approving the Quality Report, for each downstream skill the QA artifacts will feed, add a downstream ref:

```
python ${SKILL_DIR}/scripts/artifact.py link QA-REPORT-001 --downstream DEPLOY-PLAN-001
python ${SKILL_DIR}/scripts/artifact.py link QA-RTM-001 --downstream MGMT-DEBT-001
```

If the downstream artifact does not exist yet, leave the downstream_ref list empty — the downstream skill will back-fill when it runs. What matters at QA approval time is that the upstream refs (back to RE / Arch / Impl) are complete and that the gate verdict is `pass`.
