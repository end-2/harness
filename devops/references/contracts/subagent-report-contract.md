# Subagent → Main Handoff Contract (DevOps)

Subagents in DevOps (`monitor`, `log`, `incident`, `review`) do **not** return their findings in the message body. They write a **report file** under `${HARNESS_ARTIFACTS_DIR:-./artifacts/devops}/.reports/` and return only the file path plus a one-line summary. The main agent then reads, validates, and acts on the file.

This exists for three reasons:

1. **Clean-context guarantee.** If a subagent returns a long report in its message, the return value is injected wholesale into the main agent's context — defeating the point of spawning a subagent in the first place. A path + one-line summary is O(1) in context size.
2. **Deterministic parsing.** The report has a strict YAML frontmatter schema (below). The main agent parses the frontmatter programmatically via `artifact.py report show` instead of regexing free-form Markdown.
3. **Audit trail.** Reports accumulate under `.reports/` and can be re-read later (during the next review loop, during a revise pass, or by a downstream skill like `security` or `management`).

## File layout

```
artifacts/devops/
├── DEVOPS-PL-001.md
├── DEVOPS-PL-001.meta.yaml
├── DEVOPS-IAC-001.md
├── DEVOPS-IAC-001.meta.yaml
├── DEVOPS-OBS-001.md
├── DEVOPS-OBS-001.meta.yaml
├── DEVOPS-RB-001.md
├── DEVOPS-RB-001.meta.yaml
├── ...
└── .reports/
    ├── monitor-all-20260412T100000Z.md
    ├── log-all-20260412T103000Z.md
    ├── incident-all-20260412T110000Z.md
    ├── review-all-20260412T120000Z.md   # review pass after content stages
    └── ...
```

Report IDs follow `<stage>-<scope>-<UTC timestamp>`. For DevOps the scope is usually `all` because monitor, log, incident, and review span the full set of DevOps artifacts.

## Frontmatter schema

Every report starts with YAML frontmatter delimited by `---`. The allocation script (`artifact.py report path`) writes a stub with the required skeleton; the subagent fills in the fields and appends a Markdown body.

```yaml
---
report_id: monitor-all-20260412T100000Z          # assigned by `report path`
kind: monitor                                    # monitor | log | incident | review
skill: devops                                    # enforced by the script
stage: monitor                                   # workflow stage that produced it
created_at: 2026-04-12T10:00:00Z
target_refs:                                     # DevOps artifacts under review
  - DEVOPS-OBS-001
  - DEVOPS-PL-001
verdict: pass                                    # pass | at_risk | fail | n/a
summary: >-                                      # one line, required, non-empty
  Generated 5 alerting rules from 3 SLOs, 2 dashboards, distributed tracing config.
proposed_meta_ops:                               # optional; main applies if it agrees
  - cmd: set-progress
    artifact_id: DEVOPS-OBS-001
    completed: 3
    total: 4
items:                                           # structured findings
  - id: 1
    severity: info                               # high | med | low | info
    classification: content_draft                # stage-specific (see below)
    message: "Alerting rules for SLO-001 through SLO-003"
---
```

### Field rules

- `report_id`, `kind`, `skill`, `stage`, `created_at`, `target_refs`, `verdict`, `summary` are **required**.
- `summary` must be non-empty. An empty summary fails `artifact.py report validate`.
- `target_refs` is a list even when a single artifact is targeted.
- `proposed_meta_ops` is a list of dicts. In DevOps reports only `set-progress` and `link` are allowed; phase transitions and approvals remain main-agent-only. The main agent applies accepted ops by calling the corresponding `artifact.py` subcommand — **the subagent must never call `artifact.py` to change metadata directly.**
- `items` is a list of structured findings and must contain at least one item. Allowed `classification` values depend on the stage:
  - `monitor`: `content_draft`, `slo_gap`, `strategy_mismatch`
  - `log`: `content_draft`, `compliance_gap`, `masking_gap`
  - `incident`: `content_draft`, `coverage_gap`, `escalation_gap`
  - `review`: `feedback_loop_gap`, `traceability_gap`, `consistency_gap`, `security_concern`, `cost_concern`, `escalation`

### For content-producing stages (monitor, log, incident)

The report body contains the actual markdown content that the main agent should merge into the corresponding artifact `.md` file. The subagent does **not** edit artifact files directly.

### For review

The report body contains a structured verification report with the feedback-loop checklist results. Items with classification `feedback_loop_gap` or `traceability_gap` are routed back to the responsible stage. Items with `escalation` go to the user.

## Main agent protocol

When spawning a subagent stage, the main agent:

1. Allocates a fresh report path:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py report path \
       --kind monitor --stage monitor --scope all
   ```
   This prints the JSON `{report_id, path}` and pre-writes a stub with the required frontmatter skeleton.
2. Spawns the subagent, passing:
   - the allocated `path` (the subagent must write to this exact file),
   - the DevOps artifacts, upstream references, and any source/config trees.
3. When the subagent finishes, the subagent's **message body is only** the report id + the one-line summary. The main agent:
   - Runs `artifact.py report validate <report_id>` — if it fails, the subagent's work is rejected and re-run.
   - Runs `artifact.py report show <report_id>` to read the full report.
   - For content-producing stages (`monitor`, `log`, `incident`): merges the report body content into the corresponding artifact `.md` file, applies any accepted `proposed_meta_ops`.
   - If `monitor` and `log` ran in parallel, reconciles both reports into one final Observability artifact before starting `incident`.
   - For `review`: classifies findings, routes `feedback_loop_gap` and `traceability_gap` items back to the responsible stage, escalates `escalation` items to the user.
4. Phase transitions (`set-phase`, `approve`) are **not** valid `proposed_meta_ops` in DevOps. The main agent is the only component allowed to move phases or approvals.

## Subagent protocol

When a subagent is invoked for a stage with this contract, it must:

1. Read the target artifacts and any upstream references it was given.
2. Do its content generation or verification work.
3. Write the final report into the path the main agent allocated — **overwrite** the stub, keeping the `report_id`, `kind`, `skill`, `stage`, and `created_at` fields intact.
4. Fill in `verdict`, a non-empty `summary`, the `items` list, and `proposed_meta_ops` (when applicable). Expand the body per the body-structure rules above.
5. Run `artifact.py report validate <path>` itself before returning.
6. Return a short message of the form:
   ```
   report_id: monitor-all-20260412T100000Z
   verdict: pass
   summary: Generated 5 alerting rules from 3 SLOs, 2 dashboards, distributed tracing config.
   ```
   Do **not** paste the body content into the message. The main agent will load it from the file.

## Applies to both light and heavy modes

The file-based handoff is **uniform across light and heavy modes**. Light mode produces a shorter body and fewer `items`, but the frontmatter fields and the allocation/validation flow are identical. Never inline a report in the message body "because the mode is light" — uniformity is the point.
