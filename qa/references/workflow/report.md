# Workflow — Stage 4: report

## Role

Run the test suite, collect coverage and NFR actuals, fill the Quality Report section, and call `gate-evaluate` to drive the verdict and the approval state. **Run as a subagent.** The subagent does not call `gate-evaluate` itself — it emits the meta op and the main agent runs it.

## Inputs

- The approved `QA-STRATEGY-*` (for the gate criteria).
- The approved `QA-SUITE-*` artifacts and the actual test source files.
- The approved `QA-RTM-*` (for requirements coverage).
- The RE / Arch / Impl artifacts (for NFR targets and run commands).
- A pre-allocated report path from `artifact.py report path --kind report --stage report --scope all`.

## What the subagent does

1. **Run the suite.** Use `IMPL-GUIDE-*.run_commands` (or the test runner pinned in `IMPL-CODE-*.external_dependencies`) to execute every test file. Capture the per-file pass/fail counts and the framework's coverage output. If the framework cannot run in the current environment (missing dependency, missing service), the subagent's verdict is `fail` with a clear reason in the summary — it does not silently skip.

2. **Compute code coverage.** Per Impl module (one row per `IMPL-MAP-*.module_path`) plus the project total. Lines and branches at minimum.

3. **Compute requirements coverage.** Re-read the RTM (or include the output of `rtm-gap-report` in the report body) and break it down by MoSCoW priority into `total / covered / partial / uncovered`.

4. **Measure NFRs.** For every `RE-QA-*.metric` in scope, run the scenario from the strategy's NFR plan and record `target`, `actual`, and `pass`. The pass rule is straightforward: parse the target text (e.g. `"p95 < 200 ms"`, `"99.9% availability"`) and compare. When the target uses an operator like `<`, `<=`, `>`, `>=`, apply it directly; when it is "X% over Y window", compute the rate over the run window.

5. **Build the residual risk list.** Every `partial` / `uncovered` row in the RTM that is not Must goes here. Must rows that escalated and were resolved by the user must also appear with the resolution recorded.

6. **Draft the Quality Report markdown body.** Use the template from `assets/templates/quality-report.md.tmpl`. Do **not** write a verdict — leave the verdict and quality_gate sections to be populated by `gate-evaluate`.

7. **Emit `proposed_meta_ops`.** The subagent does not write to `*.meta.yaml`. Instead it emits an op list that the main agent applies:
   ```yaml
   proposed_meta_ops:
     - op: write-quality-report-actuals
       artifact_id: QA-REPORT-001
       quality_gate:
         actuals:
           code_coverage: 0.84
           requirements_coverage_must: 1.00
           failed_tests: 0
           nfr_results:
             - metric_id: RE-QA-001
               target: "p95 < 200 ms"
               actual: "148 ms"
               pass: true
       quality_report:
         code_coverage:
           by_module:
             - module: src/auth/
               lines: 0.92
               branches: 0.87
           total: { lines: 0.84, branches: 0.78 }
         residual_risks:
           - re_id: FR-014
             priority: should
             status: partial
             reason: "IdP stub not in CI; deferred"
     - op: gate-evaluate
       artifact_id: QA-REPORT-001
   ```

8. **Return** only `report_id + verdict + summary`. The verdict mirrors the test run result (`pass` if all tests passed, `fail` if any failed, `at_risk` if there are accepted Should/Could gaps but no failures), not the eventual gate verdict — the gate verdict is `gate-evaluate`'s job.

## What the main agent does after the subagent returns

1. Read the report via `artifact.py report show <report_id>`.
2. Validate it via `artifact.py report validate <report_id>`.
3. Walk the `proposed_meta_ops` and apply them in order:
   - For `write-quality-report-actuals`, the main agent applies the payload through `artifact.py set-block`, once for `quality_report` and once for `quality_gate.actuals`. Keep the payload minimal — only the keys named in the op.
   - For `gate-evaluate`, run:
     ```
     python ${SKILL_DIR}/scripts/artifact.py gate-evaluate QA-REPORT-001
     ```
4. Read the gate output. The verdict is one of:
   - `pass` → Quality Report is `approved`. Hand off to `deployment`.
   - `fail` → Quality Report is `rejected`. Loop back to `generate` (or `review`) to close the failing criteria.
   - `escalated` → Quality Report is `escalated`. Show the user the unresolved Must gaps and wait for direction.
5. Edit the markdown body to render the gate verdict and the executive summary.
6. Link the report downstream when the user moves on to `deployment`:
   ```
   python ${SKILL_DIR}/scripts/artifact.py link QA-REPORT-001 --downstream DEPLOY-PLAN-001
   ```

## Re-runs

A Quality Report can be re-evaluated. The flow is:

1. Reset the actuals (delete the previous values from `quality_gate.actuals`).
2. Run the subagent again.
3. Apply the new `proposed_meta_ops`.
4. Re-run `gate-evaluate`.

The script tracks the verdict history in `approval.history`, so re-runs are auditable. Do not delete history rows.

## Escalation

Escalate to the user when:

- The test runner cannot execute at all (build broken, env vars missing, dependency unresolvable).
- An NFR scenario requires infrastructure the project does not have (load gen, real third-party service).
- A Must requirement remains uncovered after Stage 3 already escalated and the user did not provide a resolution.

Do **not** escalate for:

- Failing tests — record them as `failed_tests` in actuals and let `gate-evaluate` fail the gate normally.
- Slow tests, ugly output formatting, or coverage reporters that need a flag — pick the right invocation and proceed.
