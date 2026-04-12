# Subagent → Main Handoff Contract (Verify)

Subagents in Verify (`scenario`, `report`) do **not** return their findings in the message body. They write a **report file** under `${HARNESS_ARTIFACTS_DIR:-./artifacts/verify}/.reports/` and return only the file path plus a one-line summary. The main agent then reads, validates, and acts on the file.

This exists for three reasons:

1. **Clean-context guarantee.** If a subagent returns a long report in its message, the return value is injected wholesale into the main agent's context — defeating the point of spawning a subagent. A path + one-line summary is O(1) in context size.
2. **Deterministic parsing.** The report has a strict YAML frontmatter schema (below). The main agent parses the frontmatter programmatically via `artifact.py report show` instead of regexing free-form Markdown.
3. **Audit trail.** Reports accumulate under `.reports/` and can be re-read later (during re-runs, or by downstream skills like `sec` or `orch`).

## File layout

```
artifacts/verify/
├── VERIFY-ENV-001.md
├── VERIFY-ENV-001.meta.yaml
├── VERIFY-SC-001.md
├── VERIFY-SC-001.meta.yaml
├── VERIFY-RPT-001.md
├── VERIFY-RPT-001.meta.yaml
└── .reports/
    ├── scenario-all-20260412T100000Z.md
    ├── report-all-20260412T120000Z.md
    └── ...
```

## Frontmatter schema

Every report starts with YAML frontmatter delimited by `---`. The allocation script (`artifact.py report path`) writes a stub with the required skeleton; the subagent fills in the fields and appends a Markdown body.

```yaml
---
report_id: scenario-all-20260412T100000Z
kind: scenario
skill: verify
stage: scenario
created_at: 2026-04-12T10:00:00Z
target_refs:
  - VERIFY-SC-001
verdict: pass
summary: >-
  Derived 8 verification scenarios from 3 Arch sequence diagrams, 2 failure paths, and 3 observability checks.
proposed_meta_ops:
  - cmd: set-progress
    artifact_id: VERIFY-SC-001
    completed: 8
    total: 8
items:
  - id: 1
    severity: info
    classification: content_draft
    message: "8 scenarios derived: 3 integration, 2 failure, 3 observability"
---
```

### Field rules

- `report_id`, `kind`, `skill`, `stage`, `created_at`, `target_refs`, `verdict`, `summary` are **required**.
- `summary` must be non-empty. An empty summary fails `artifact.py report validate`.
- `target_refs` is a list even when a single artifact is targeted.
- `proposed_meta_ops` is a list of dicts; each has a `cmd` key matching one of `set-progress`, `set-phase`, `link`, `approve`. The main agent applies them by calling the corresponding `artifact.py` subcommand.
- `items` is a list of structured findings. Allowed `classification` values depend on the stage:
  - `scenario`: `content_draft`, `coverage_gap`, `source_ambiguity`
  - `report`: `verdict_summary`, `impl_feedback`, `devops_feedback`, `arch_feedback`, `traceability_gap`, `slo_gap`

### For scenario stage

The report body contains the scenario definitions (markdown tables and details) that the main agent should merge into `VERIFY-SC-*.md`.

### For report stage

The report body contains the full verification report (results, evidence, issues, SLO validation, feedback, traceability chain) that the main agent should merge into `VERIFY-RPT-*.md`.

## Main agent protocol

1. Allocate a fresh report path:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py report path \
       --kind scenario --stage scenario --scope all
   ```
2. Spawn the subagent, passing the allocated `path` and all necessary input artifacts.
3. When the subagent finishes, validate: `artifact.py report validate <report_id>`.
4. Read the full report: `artifact.py report show <report_id>`.
5. Merge content into the corresponding artifact `.md` file.
6. Apply `proposed_meta_ops` via `artifact.py` subcommands.

## Subagent protocol

1. Read the target artifacts and upstream references.
2. Do the content generation work.
3. Write the final report into the allocated path — **overwrite** the stub, keeping `report_id`, `kind`, `skill`, `stage`, and `created_at` intact.
4. Fill in `verdict`, `summary`, `items`, and `proposed_meta_ops`.
5. Run `artifact.py report validate <path>` before returning.
6. Return only:
   ```
   report_id: scenario-all-20260412T100000Z
   verdict: pass
   summary: Derived 8 verification scenarios from 3 Arch sequence diagrams.
   ```

## Applies to both light and heavy modes

The file-based handoff is **uniform across light and heavy modes**. Light mode produces fewer scenarios and shorter reports, but the frontmatter fields and the allocation/validation flow are identical.
