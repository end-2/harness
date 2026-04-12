# Subagent → Main Handoff Contract (Impl)

Subagents in Impl (`review`, `refactor`) do **not** return their findings in the message body. They write a **report file** under `${HARNESS_ARTIFACTS_DIR:-./artifacts/impl}/.reports/` and return only `report_id + verdict + summary`. The main agent then reads, validates, and acts on the file.

This exists for three reasons:

1. **Clean-context guarantee is real.** If a subagent returns a long report in its message, the return value is injected wholesale into the main agent's context — defeating the point of spawning a subagent in the first place. A report id + short summary is O(1) in context size.
2. **Deterministic parsing.** The report has a strict YAML frontmatter schema (below). The main agent parses the frontmatter programmatically via `artifact.py report show` instead of regexing free-form Markdown.
3. **Audit trail.** Reports accumulate under `.reports/` and can be re-read later (during the next refactor loop, during a revise pass, or by a downstream skill like `qa` or `security`).

## File layout

```
artifacts/impl/
├── IMPL-MAP-001.md
├── IMPL-MAP-001.meta.yaml
├── ...
└── .reports/
    ├── review-all-20260411T160011Z.md
    ├── refactor-all-20260411T161544Z.md
    ├── review-all-20260411T162830Z.md   # second review pass after the refactor
    └── ...
```

Report IDs follow `<stage>-<scope>-<UTC timestamp>`. For Impl the scope is usually `all` because review and refactor span the full source tree + all four Impl sections.

## Frontmatter schema

Every report starts with YAML frontmatter delimited by `---`. The allocation script (`artifact.py report path`) writes a stub with the required skeleton; the subagent fills in the fields and appends a Markdown body.

```yaml
---
report_id: review-all-20260411T160011Z           # assigned by `report path`
kind: review                                     # review | refactor
skill: impl                                      # enforced by the script
stage: review                                    # workflow stage that produced it
created_at: 2026-04-11T16:00:11Z
target_refs:                                     # Impl sections + Arch refs under review
  - IMPL-MAP-001
  - IMPL-CODE-001
  - IMPL-IDR-001
  - IMPL-GUIDE-001
verdict: at_risk                                 # pass | at_risk | fail | n/a
summary: >-                                      # one line, required, non-empty
  2 contract violations (auth→billing boundary), 7 auto-fixable smells, 1 hardcoded secret.
proposed_meta_ops:                               # optional; main applies if it agrees
  - cmd: set-progress
    artifact_id: IMPL-MAP-001
    completed: 5
    total: 6
  - cmd: link
    artifact_id: IMPL-IDR-001
    upstream: ARCH-DEC-002
items:                                           # structured findings
  - id: 1
    severity: high                               # high | med | low | info
    classification: contract_violation           # free-form, stage-specific (see below)
    location: src/api/auth.ts:42
    arch_ref: ARCH-COMP-002
    message: >-
      auth module imports src/billing/internal/*, crossing a boundary Arch does
      not declare.
    suggested_fix: needs an Arch update or a new interface in ARCH-COMP-002
  - id: 2
    severity: med
    classification: clean_code
    location: src/auth/service.ts
    message: SRP — service mixes token minting and session storage
    suggested_fix: Extract Class → SessionStore
---
```

### Field rules

- `report_id`, `kind`, `skill`, `stage`, `created_at`, `target_refs`, `verdict`, `summary` are **required**.
- `summary` must be non-empty. An empty summary fails `artifact.py report validate`.
- `target_refs` is a list even when a single artifact is targeted.
- `proposed_meta_ops` is a list of dicts. Allowed commands depend on the stage:
  - `review`: `link` only
  - `refactor`: `link`, `set-progress`
  The main agent applies them by calling the corresponding `artifact.py` subcommand — **the subagent must never call `artifact.py` to change metadata directly.**
- `items` is a list of structured findings.
  - `review` items must include `id`, `severity`, `classification`, `location`, `message`, and `suggested_fix`. `arch_ref` is optional when no single Arch anchor applies.
  - `refactor` items must include `id`, `classification`, and `message`. `location`, `suggested_fix`, and `arch_ref` are optional.
  Allowed `classification` values depend on the stage:
  - `review`: `contract_violation`, `clean_code`, `security_baseline`, `traceability_gap`, `escalation`
  - `refactor`: `refactor_applied`, `idr_added`, `boundary_escalation`

## Body structure

For `review`:

```markdown
# review report (impl/review)

## Summary
One paragraph expanding on the `summary` frontmatter field.

## Contract violations (escalate to user)
1. **[HIGH] Boundary crossing** — `src/api/auth.ts:42` imports `src/billing/internal/...`.
   - Arch ref: ARCH-COMP-002, ARCH-COMP-005
   - Suggested fix: needs Arch update or a new interface in ARCH-COMP-002.

## Auto-fixable issues (route to refactor)
1. **[MED] SRP** — `src/auth/service.ts` — extract `SessionStore`.
2. **[LOW] Naming** — `src/api/handlers.ts:118` — `doStuff` → `resolveUser`.

## Traceability
- Every ARCH-COMP has at least one IMPL-MAP entry: yes / no
- Every IMPL-IDR cites an Arch or RE ref: yes / no
```

For `refactor`:

```markdown
# refactor report (impl/refactor)

## Summary
One paragraph expanding on the `summary` frontmatter field.

## Applied refactors
1. **Extract Class: SessionStore** — resolved review item #1 in <previous-review-report-id>.
   - Files: src/auth/service.ts, src/auth/session_store.ts (new)
   - IDR added: IDR-011
2. ...

## Patches
```diff
--- a/src/auth/service.ts
+++ b/src/auth/service.ts
@@ ...
```
(Inline patches the main agent can `git apply` or translate into `Edit` calls.)

## Escalations
Issues that would require crossing an Arch boundary and so could not be auto-fixed. Each item corresponds to an `items[]` entry with `classification: boundary_escalation`.
```

The `refactor` body's **patches section is authoritative** — the main agent reads it and applies the changes with `Edit`/`Write`. The subagent does **not** write source files directly; it proposes patches in the report.

## Main agent protocol

When spawning a subagent stage, the main agent:

1. Allocates a fresh report path:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py report path \
       --kind review --stage review --scope all
   ```
   This prints the JSON `{report_id, path}` and pre-writes a stub with the required frontmatter skeleton.
2. Spawns the subagent, passing:
   - the allocated `path` (the subagent must write to this exact file),
   - the Impl section artifacts, the Arch artifacts, and the source tree root.
3. When the subagent finishes, the subagent's **message body is only** the report id + verdict + one-line summary. The main agent:
   - Runs `artifact.py report validate <report_id>` — if it fails, the subagent's work is rejected and re-run.
   - Runs `artifact.py report show <report_id>` to read the full report.
   - For `review`: classifies findings, escalates contract violations to the user, feeds auto-fixable items to `refactor`.
   - For `refactor`: applies the patches via `Edit`/`Write`, applies any `proposed_meta_ops` (like updated Implementation Map progress), then re-enters `review`.
4. Phase transitions (`set-phase`, `approve`) are **never** included in `proposed_meta_ops`; the main agent is the only component allowed to gate those.

## Subagent protocol

When a subagent is invoked for a stage with this contract, it must:

1. Read the target artifacts and source tree it was given.
2. Do its verification or transformation work.
3. Write the final report into the path the main agent allocated — **overwrite** the stub, keeping the `report_id`, `kind`, `skill`, `stage`, and `created_at` fields intact.
4. Fill in `verdict`, a non-empty `summary`, the `items` list, and `proposed_meta_ops` (when applicable). Expand the body per the body-structure rules above — including the patches section for `refactor`.
5. Run `artifact.py report validate <path>` itself before returning.
6. Return a short message of the form:
   ```
   report_id: review-all-20260411T160011Z
   verdict: at_risk
   summary: 2 contract violations, 7 auto-fixable smells, 1 hardcoded secret.
   ```
   Do **not** paste the body content into the message. The main agent will load it from the file.

## Applies to both light and heavy modes

The file-based handoff is **uniform across light and heavy modes**. Light mode produces a shorter body and fewer `items`, but the frontmatter fields and the allocation/validation flow are identical. Never inline a report in the message body "because the mode is light" — uniformity is the point.
