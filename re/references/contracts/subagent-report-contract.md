# Subagent → Main Handoff Contract (RE)

Subagents in RE (`analyze`, `review`) do **not** return their findings in the message body. They write a **report file** under `${HARNESS_ARTIFACTS_DIR:-./artifacts/re}/.reports/` and return only `report_id + verdict + summary`. The main agent then reads, validates, and acts on the file.

This exists for three reasons:

1. **Clean-context guarantee is real.** If a subagent returns a long report in its message, the return value is injected wholesale into the main agent's context — defeating the point of spawning a subagent in the first place. A short `report_id + verdict + summary` return is O(1) in context size.
2. **Deterministic parsing.** The report has a strict YAML frontmatter schema (below). The main agent parses the frontmatter programmatically via `artifact.py report show` instead of regexing free-form Markdown.
3. **Audit trail.** Reports accumulate under `.reports/` and can be re-read later (during a next iteration, during a revise loop, or by a downstream skill that needs to understand why a decision was made).

## File layout

```
artifacts/re/
├── RE-REQ-001.md
├── RE-REQ-001.meta.yaml
├── ...
└── .reports/
    ├── analyze-RE-REQ-001-20260411T135106Z.md
    ├── review-RE-REQ-001-RE-CON-001-RE-QA-001-20260411T144522Z.md
    └── ...
```

Report IDs follow `<stage>-<scope>-<UTC timestamp>` where `scope` is a dash-joined list of target artifact IDs (or a symbolic name like `all` when the report spans every artifact).

## Frontmatter schema

Every report starts with YAML frontmatter delimited by `---`. The allocation script (`artifact.py report path`) writes a stub with the required skeleton; the subagent fills in the fields and appends a Markdown body.

```yaml
---
report_id: analyze-RE-REQ-001-20260411T135106Z  # assigned by `report path`
kind: analyze                                    # analyze | review | spec-review
skill: re                                        # enforced by the script
stage: analyze                                   # workflow stage that produced it
created_at: 2026-04-11T13:51:06Z
target_refs:                                     # which artifacts the report is about
  - RE-REQ-001
verdict: at_risk                                 # pass | at_risk | fail | n/a
summary: >-                                      # one line, required, non-empty
  3 conflicts, 2 gaps, 1 infeasibility found — NFR-002 blocks ship on current budget.
proposed_meta_ops:                               # optional; main applies if it agrees
  - cmd: set-progress
    artifact_id: RE-REQ-001
    completed: 5
    total: 7
  - cmd: link
    artifact_id: RE-REQ-001
    upstream: RE-CON-002
items:                                           # structured findings
  - id: 1
    severity: high                               # high | med | low | info
    classification: conflict                     # free-form, stage-specific (see below)
    location: RE-REQ-001#NFR-002                 # artifact_id[#anchor] or file:line
    message: "NFR-002 requires <50ms p95 but CON-003 pins free-tier DB."
    suggested_fix: "Either relax NFR-002 to <200ms or upgrade DB tier."
---
```

### Field rules

- `report_id`, `kind`, `skill`, `stage`, `created_at`, `target_refs`, `verdict`, `summary` are **required**.
- `summary` must be non-empty. An empty summary fails `artifact.py report validate` — this is intentional so subagents cannot "complete" a report by filling only the frontmatter shell.
- `target_refs` is a list even when a single artifact is targeted.
- `proposed_meta_ops` is a list of dicts; each has a `cmd` key matching one of `set-progress`, `set-phase`, `link`, `approve`. The main agent applies them by calling the corresponding `artifact.py` subcommand — **the subagent must never call `artifact.py` to change metadata directly.**
- `items` is a list of structured findings. The allowed `classification` values depend on the stage:
  - `analyze`: `conflict`, `gap`, `infeasibility`, `dependency`, `tradeoff`
  - `review`: `smart_violation`, `constraint_inconsistency`, `traceability_gap`, `downstream_fitness`, `escalation`
  - `spec-review`: same as `review`

## Body structure

Below the frontmatter, write a Markdown body that expands on the `items`. The body is for humans (and for the main agent's summary to the user); the frontmatter is for programmatic parsing. Typical structure:

```markdown
# analyze report (re/analyze)

## Summary
One paragraph expanding on the `summary` frontmatter field.

## Findings
### 1. [HIGH] Conflict — NFR-002 vs CON-003
Long-form explanation of the conflict, the options, and the recommended decision.
(Cross-references the item with id=1 in the frontmatter.)

### 2. ...

## Decisions needed from the user
Bullet list of the items that require a user call.
```

## Main agent protocol

When spawning a subagent stage, the main agent:

1. Allocates a fresh report path:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py report path \
       --kind analyze --stage analyze \
       --target RE-REQ-001 --target RE-CON-001 --target RE-QA-001
   ```
   This prints the JSON `{report_id, path}` and pre-writes a stub with the required frontmatter skeleton.
2. Spawns the subagent, passing:
   - the allocated `path` (the subagent must write to this exact file),
   - the target artifact paths it should analyze/review.
3. When the subagent finishes, the subagent's **message body is only** the report id + the one-line summary. The main agent:
   - Runs `artifact.py report validate <report_id>` — if it fails, the subagent's work is rejected and re-run.
   - Runs `artifact.py report show <report_id>` to read the full report.
   - Parses `items` and `proposed_meta_ops` from the frontmatter.
   - Walks the user through the findings (one section at a time), decides which `proposed_meta_ops` to apply, and applies them via the standard `artifact.py` subcommands.
4. Phase transitions (`set-phase`, `approve`) are **never** included in `proposed_meta_ops` without the user's explicit go-ahead — the main agent is the only component allowed to gate those.

## Subagent protocol

When a subagent is invoked for a stage with this contract, it must:

1. Read the target artifacts it was given.
2. Do its analysis or verification work.
3. Write the final report into the path the main agent allocated — **overwrite** the stub, keeping the `report_id`, `kind`, `skill`, `stage`, and `created_at` fields intact.
4. Fill in `verdict`, a non-empty `summary`, the `items` list, and `proposed_meta_ops` (when applicable). Expand the body with the human-readable explanation.
5. Run `artifact.py report validate <path>` itself before returning, so the main agent never has to re-run on a broken report.
6. Return a short message of the form:
   ```
   report_id: analyze-RE-REQ-001-20260411T135106Z
   verdict: at_risk
   summary: 3 conflicts, 2 gaps, 1 infeasibility found — NFR-002 blocks ship on current budget.
   ```
   Do **not** paste the body content into the message. The main agent will load it from the file.

## Applies to both light and heavy modes

The file-based handoff is **uniform across light and heavy modes**. Light mode produces a shorter body and possibly empty `proposed_meta_ops`, but the frontmatter fields and the allocation/validation flow are identical. Never inline a report in the message body "because the mode is light" — uniformity is the point.
