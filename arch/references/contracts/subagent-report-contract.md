# Subagent → Main Handoff Contract (Arch)

Subagents in Arch (`adr`, `diagram`, `review`) do **not** return their findings in the message body. They write a **report file** under `${HARNESS_ARTIFACTS_DIR:-./artifacts/arch}/.reports/` and return only the file path plus a one-line summary. The main agent then reads, validates, and acts on the file.

This exists for three reasons:

1. **Clean-context guarantee is real.** If a subagent returns a long report in its message, the return value is injected wholesale into the main agent's context — defeating the point of spawning a subagent in the first place. A path + one-line summary is O(1) in context size.
2. **Deterministic parsing.** The report has a strict YAML frontmatter schema (below). The main agent parses the frontmatter programmatically via `artifact.py report show` instead of regexing free-form Markdown.
3. **Audit trail.** Reports accumulate under `.reports/` and can be re-read later (during a next iteration, during a revise loop, or by downstream skills that need to understand why a decision was made).

## File layout

```
artifacts/arch/
├── ARCH-DEC-001.md
├── ARCH-DEC-001.meta.yaml
├── ...
└── .reports/
    ├── adr-ARCH-DEC-001-20260411T140533Z.md
    ├── diagram-ARCH-DIAG-001-20260411T142015Z.md
    ├── review-ARCH-DEC-001-ARCH-COMP-001-ARCH-TECH-001-ARCH-DIAG-001-20260411T150422Z.md
    └── ...
```

Report IDs follow `<stage>-<scope>-<UTC timestamp>` where `scope` is a dash-joined list of target artifact IDs (or a symbolic name like `all` when the report spans every artifact).

## Frontmatter schema

Every report starts with YAML frontmatter delimited by `---`. The allocation script (`artifact.py report path`) writes a stub with the required skeleton; the subagent fills in the fields and appends a Markdown body.

```yaml
---
report_id: review-ARCH-DEC-001-ARCH-COMP-001-20260411T150422Z  # assigned by `report path`
kind: review                                     # adr-draft | diagram-draft | review
skill: arch                                      # enforced by the script
stage: review                                    # workflow stage that produced it
created_at: 2026-04-11T15:04:22Z
target_refs:                                     # which artifacts the report is about
  - ARCH-DEC-001
  - ARCH-COMP-001
  - ARCH-TECH-001
  - ARCH-DIAG-001
verdict: at_risk                                 # pass | at_risk | fail | n/a
summary: >-                                      # one line, required, non-empty
  3 scenarios pass, 1 at risk (NFR-003 p95); CON-002 satisfied; 1 untraced FR.
proposed_meta_ops:                               # optional; main applies if it agrees
  - cmd: link
    artifact_id: ARCH-DEC-001
    upstream: RE-QA-001
  - cmd: set-progress
    artifact_id: ARCH-COMP-001
    completed: 6
    total: 6
items:                                           # structured findings
  - id: 1
    severity: high                               # high | med | low | info
    classification: scenario_failure             # free-form, stage-specific (see below)
    location: ARCH-DEC-001#AD-003
    message: "NFR-003 p95 < 200ms is at risk under the chosen DB topology."
    suggested_fix: "Add a read replica or promote the search index to a dedicated service."
---
```

### Field rules

- `report_id`, `kind`, `skill`, `stage`, `created_at`, `target_refs`, `verdict`, `summary` are **required**.
- `summary` must be non-empty. An empty summary fails `artifact.py report validate` — this is intentional so subagents cannot "complete" a report by filling only the frontmatter shell.
- `target_refs` is a list even when a single artifact is targeted.
- `proposed_meta_ops` is a list of dicts; each has a `cmd` key matching one of `set-progress`, `set-phase`, `link`, `approve`. The main agent applies them by calling the corresponding `artifact.py` subcommand — **the subagent must never call `artifact.py` to change metadata directly.**
- `items` is a list of structured findings. The allowed `classification` values depend on the stage:
  - `adr` (kind `adr-draft`): `adr_drafted`, `context_missing`, `alternatives_missing`, `consequences_missing`
  - `diagram` (kind `diagram-draft`): `diagram_drafted`, `caption_missing`, `driver_untraced`
  - `review`: `scenario_pass`, `scenario_failure`, `hard_constraint_unsatisfied`, `traceability_gap`, `escalation`

## Body structure for `adr-draft` and `diagram-draft`

For `adr-draft` and `diagram-draft` reports, the **body is the artifact content the subagent produced** (ADR markdown blocks, or Mermaid diagrams with captions). The main agent reviews the body, merges it into the target artifact's `.md` file via `Edit`, and transitions the target artifact via the standard `artifact.py` subcommands. The subagent itself never writes to `<id>.md` — only to the report file.

## Body structure for `review`

For `review` reports the body expands on the `items` and presents the three-check summary expected by the user:

```markdown
# review report (arch/review)

## Summary
One paragraph expanding on the `summary` frontmatter field.

## Scenarios
| scenario | verdict | reason |
| --- | --- | --- |
| NFR-003 p95 < 200ms | at_risk | single-DB bottleneck under 200 rps |
| ... | ... | ... |

## Constraints
| constraint | satisfied by |
| --- | --- |
| CON-002 (AWS only) | AD-004 (ECS Fargate), ARCH-TECH-001 infra row |

## Traceability
X FRs mapped, Y NFRs mapped, Z decisions cited, W diagrams captioned. Any gaps listed.

## Risks and open items
Bullet list of the items that require a user call (mirrors `items` with `classification: escalation`).
```

## Main agent protocol

When spawning a subagent stage, the main agent:

1. Allocates a fresh report path:
   ```bash
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py report path \
       --kind review --stage review \
       --target ARCH-DEC-001 --target ARCH-COMP-001 \
       --target ARCH-TECH-001 --target ARCH-DIAG-001
   ```
   This prints the JSON `{report_id, path}` and pre-writes a stub with the required frontmatter skeleton.
2. Spawns the subagent, passing:
   - the allocated `path` (the subagent must write to this exact file),
   - the target artifact paths it should analyze/draft/review.
3. When the subagent finishes, the subagent's **message body is only** the report id + the one-line summary. The main agent:
   - Runs `artifact.py report validate <report_id>` — if it fails, the subagent's work is rejected and re-run.
   - Runs `artifact.py report show <report_id>` to read the full report.
   - For `adr-draft` / `diagram-draft`: applies the body content to the target artifact's `.md` via `Edit`.
   - For `review`: walks the user through `items` and decides which `proposed_meta_ops` to apply.
4. Phase transitions (`set-phase`, `approve`) are **never** included in `proposed_meta_ops` without the user's explicit go-ahead — the main agent is the only component allowed to gate those.

## Subagent protocol

When a subagent is invoked for a stage with this contract, it must:

1. Read the target artifacts it was given.
2. Do its drafting / verification work.
3. Write the final report into the path the main agent allocated — **overwrite** the stub, keeping the `report_id`, `kind`, `skill`, `stage`, and `created_at` fields intact.
4. Fill in `verdict`, a non-empty `summary`, the `items` list, and `proposed_meta_ops` (when applicable). Expand the body per the body-structure rules above.
5. Run `artifact.py report validate <path>` itself before returning, so the main agent never has to re-run on a broken report.
6. Return a short message of the form:
   ```
   report_id: review-ARCH-DEC-001-...-20260411T150422Z
   verdict: at_risk
   summary: 3 scenarios pass, 1 at risk (NFR-003 p95); CON-002 satisfied; 1 untraced FR.
   ```
   Do **not** paste the body content into the message. The main agent will load it from the file.

## Applies to both light and heavy modes

The file-based handoff is **uniform across light and heavy modes**. Light mode produces a shorter body (e.g. one ADR draft instead of ten, one sequence diagram instead of four), but the frontmatter fields and the allocation/validation flow are identical. Never inline a report in the message body "because the mode is light" — uniformity is the point.
