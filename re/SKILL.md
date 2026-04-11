---
name: re
description: Turn vague user requests into a three-section requirements artifact (Requirements Spec, Constraints, Quality Attribute Priorities) through multi-turn dialogue, then hand off to downstream skills. Use this skill whenever the user kicks off a new project, asks to revisit requirements, mentions unclear scope, or is about to invoke arch/impl/qa/security/deployment/operation skills — even if they do not explicitly say "requirements".
---

# RE — Requirements Engineering Skill

RE is the top of the Harness pipeline. It takes a natural-language request from a single user and, through an interactive dialogue, produces a structured artifact that downstream skills (`arch`, `impl`, `qa`, `security`, `deployment`, `operation`) can consume directly.

The user is the only stakeholder. Their input will be incomplete and ambiguous, and they often do not yet know exactly what they want. Your job is therefore not to silently generate a document, but to actively detect ambiguity, ask targeted questions, confirm understanding, and iteratively refine — until the user is satisfied.

## Current state (injected at load)

!`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate`

The command above lists existing artifacts, their phase, approval state, and traceability integrity. Read it before deciding whether this run is a fresh start or a continuation of an in-progress conversation.

## Input / output contract

**Input**: `$ARGUMENTS` — the user's initial prompt. Anything from "build me a shopping mall" to a full RFP.

**Output**: three section artifacts, each stored as a YAML metadata file plus a Markdown document:

1. **Requirements Specification** — functional and non-functional requirements with verifiable acceptance criteria.
2. **Constraints** — technical, business, regulatory, and environmental constraints, classified by flexibility (`hard` / `soft` / `negotiable`).
3. **Quality Attribute Priorities** — ranked quality attributes (performance, security, scalability, availability, maintainability, usability, …) with measurable targets and explicit trade-off notes.

Each section is a pair `<section>.meta.yaml` + `<section>.md`. Metadata is the single source of truth and is **only** modified through `scripts/artifact.py`. Markdown holds the human-readable body and is edited directly, but only inside the scaffolding produced by `assets/templates/`.

Full schemas: read [references/schemas/section-schemas.md](references/schemas/section-schemas.md) and [references/schemas/meta-schema.md](references/schemas/meta-schema.md) when you need the exact field list.

Downstream consumption contract: read [references/contracts/downstream-contract.md](references/contracts/downstream-contract.md) before declaring the artifact ready, so you know what `arch`/`impl`/`qa`/`security`/`deployment`/`operation` will actually look for.

## Adaptive depth

The depth of the final artifact adapts to input complexity. Do **not** apply a heavy SRS process to a single-feature request.

| Mode | Trigger | Output style |
|------|---------|--------------|
| **light** | FR ≤ 5, NFR ≤ 2, quality attributes ≤ 3 | User Story + Acceptance Criteria. Skip the trade-off matrix in `analyze`. |
| **heavy** | anything larger, or the user asks for formal SRS | IEEE 830 / ISO 29148-style SRS, trade-off analysis, traceability matrix. |

Pick the mode at the **end** of `elicit`, once you have a rough count of candidates. The user may override the mode at any time. Full rules: [references/adaptive-depth.md](references/adaptive-depth.md).

## Workflow (four stages)

```
user request ($ARGUMENTS)
    │
    ▼
[1] elicit   → detect ambiguity, ask, refine candidates
    │
    ▼
[2] analyze  → find conflicts, gaps, infeasibility, present trade-offs
    │
    ▼
[3] spec     → draft the three sections, iterate on user feedback
    │
    ▼
[4] review   → SMART check, downstream fitness check, final approval
```

Each stage has detailed behavior rules in `references/workflow/<stage>.md`. When you enter a stage, **Read that file first** and follow the rules there. SKILL.md only gives the summary.

The pipeline is **checkpoint-based**, not one-way. At any point, if the user disagrees or you realize a prior assumption was wrong, step back to an earlier stage and re-refine.

### Subagent delegation (hybrid)

Stages split between the **main agent** (which talks to the user) and isolated **subagents** (which work in a clean context window):

| Stage | Runs in | Why |
|-------|---------|-----|
| 1. elicit | main | needs multi-turn dialogue with the user |
| 2. analyze | **subagent** | pure analysis over a settled candidate set — a clean context catches more conflicts/gaps than the dialogue-laden main context |
| 3. spec | main | drafting + user feedback loop, plus the only stage that writes to disk |
| 4. review | **subagent** | pure verification over a settled draft — a clean context catches more SMART / downstream-fitness gaps |

**Sequencing rule (mandatory):** the four stages have a hard order — `elicit → analyze → spec → review` — and the two subagent stages must each run *after* their predecessor finishes. **Never spawn analyze and review in parallel**, never spawn analyze before elicit has produced a candidate set, and never spawn review before spec has produced a draft. Each subagent is a single Agent invocation (not multiple parallel calls) and receives the prior stage's output as its only input.

**File-based handoff (light and heavy both):** every subagent writes its findings to a **report file** under `./artifacts/re/.reports/` and returns only `report_id + verdict + summary` in its message. The main agent then reads the file, validates it, walks the user through the findings, and applies any `proposed_meta_ops`. This keeps the main context O(1) in size regardless of report length and gives downstream iterations a durable audit trail. **Never** let a subagent return its report inline in the message body, and **never** let a subagent call `artifact.py set-phase / approve` — phase transitions are main-agent-only. Read [references/contracts/subagent-report-contract.md](references/contracts/subagent-report-contract.md) for the frontmatter schema and protocol, including the per-stage allowed `classification` values.

Before spawning any subagent, the main agent allocates the report path:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py report path \
    --kind <analyze|review|spec-review> --stage <analyze|review> \
    --target <artifact-id> [--target ...]
```

and passes the printed `path` to the subagent as one of its inputs.

### Stage 1 — elicit

Load [references/workflow/elicit.md](references/workflow/elicit.md).

- Parse `$ARGUMENTS` as the starting point. Detect what is missing: target users, scope boundaries, success criteria, performance expectations, data volume, regulatory context, deployment constraints.
- Generate **targeted** questions. Batch related questions together; do not pepper the user with one question at a time, and do not ask everything at once.
- Represent stakeholders the user has not considered — operators, security reviewers, end users, support staff — by asking questions from their perspective.
- Track "confirmed" vs "open" items in your working memory so you never ask the same thing twice.
- Periodically summarise "here is what I have so far" and ask for confirmation.
- Exit when the user signals they have nothing more to add, **or** when you have enough to draft a first pass and a further question would feel like padding.

Output of this stage: candidate requirements, candidate constraints, candidate quality attributes, and a list of open questions for later stages. Nothing is persisted to disk yet.

### Stage 2 — analyze

**Run this stage as a subagent.** First allocate a report path (`artifact.py report path --kind analyze --stage analyze --target <req-id> [...]`), then spawn a single `general-purpose` Agent with the elicit output (candidate requirements, constraints, quality attributes, open questions) **and the allocated report path** as its only inputs. Do not run it in parallel with anything else, and do not let it talk to the user — it writes its findings to the report file (conflicts, gaps, infeasibility, decisions the user must make) and returns only `report_id + verdict + summary`. The main agent then validates and reads the report and walks the user through it. The point is to give the analyzer a clean context window that is not polluted by the elicit dialogue, and to keep the main context O(1) in size regardless of report length.

Load [references/workflow/analyze.md](references/workflow/analyze.md).

- Look for conflicts (e.g. "< 50ms latency" vs "runs on a shared free-tier DB"), gaps (e.g. no error handling requirement), and infeasibility (budget/time/tech).
- Build a dependency view of the candidates. Identify which quality attributes trade off against each other given the candidates (latency vs consistency, security vs usability, …).
- For every issue that needs a human decision, write it as a **choice** with consequences: "Option A sacrifices X; Option B sacrifices Y; which matters more?" Do not silently pick one.
- In **light** mode you may skip the full trade-off matrix; a short bulleted list is enough.

Bring the user through the decisions before moving on. The output of this stage is a reconciled candidate set ready to be formally specified.

### Stage 3 — spec

Load [references/workflow/spec.md](references/workflow/spec.md).

This is the first stage that **writes to disk**. Sequence, for each of the three sections:

1. Create the artifact pair from templates:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section requirements
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section constraints
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section quality-attributes
   ```
   Each call copies a `*.md.tmpl` + `*.meta.yaml.tmpl` from `assets/templates/` into the project's artifact directory and returns the generated `artifact_id`.
2. Fill in the Markdown body by editing only the `.md` file — never touch `.meta.yaml` with Edit/Write.
3. Update structured state through the script:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-progress <id> --completed N --total M
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase    <id> in_review
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link         <id> --upstream user-prompt
   ```
4. Show the draft to the user, collect feedback, revise, and loop until they are satisfied with that section.

Adaptive-depth rules for this stage are in `references/adaptive-depth.md`. In light mode, a compact User Story + Acceptance Criteria layout is fine; in heavy mode, follow the IEEE-830 sectioning built into the template.

### Stage 4 — review

**Run this stage as a subagent.** First allocate a report path (`artifact.py report path --kind review --stage review --target <req-id> --target <con-id> --target <qa-id>`), then spawn a single `general-purpose` Agent with the three drafted artifacts (paths to the `.md` + `.meta.yaml` pairs) and the allocated report path as its input. It runs the SMART check, the constraint-consistency check, and the downstream-fitness check in a clean context, then writes a structured report file and returns only `report_id + verdict + summary`. The main agent reads the report, applies fixes (or routes back to spec / analyze) and only then runs `artifact.py approve`. Do not spawn it in parallel with anything else, and do not start it before all three artifacts are in `in_review`.

Load [references/workflow/review.md](references/workflow/review.md).

- Verify each requirement against SMART (Specific, Measurable, Achievable, Relevant, Testable). Flag any "fast" or "scalable" without a number behind it.
- Check constraint mutual consistency and requirement-constraint alignment.
- Check that every quality attribute has a measurable target and an explicit trade-off note.
- Run the **downstream fitness check** described in [references/contracts/downstream-contract.md](references/contracts/downstream-contract.md): is there enough information for `arch` to derive drivers, for `qa` to derive test strategy, for `security` to derive a threat model?
- Run `python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` one more time to confirm schema and traceability are clean.
- Escalate anything you cannot decide alone. When the user approves:
  ```
  python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <id> --approver <user> --notes "..."
  ```
  This transitions the artifact to `approved` and records the history.

Once all three artifacts are `approved`, RE is done. Point the user at the next skill (`arch`, `qa`, `impl`, …) and stop.

## Script contract (mandatory)

**Never edit `*.meta.yaml` files directly.** All state changes — phase, progress, approval, traceability — must go through `scripts/artifact.py`. The script enforces:

- Schema validation (rejects unknown phases, missing fields).
- `updated_at` auto-refresh.
- Legal phase transitions only (`draft → in_review → revising → in_review → approved → superseded`). You cannot jump straight from `draft` to `approved`.
- Bidirectional `upstream_refs` / `downstream_refs` integrity.
- An `approval.history` audit trail with timestamps.

Available subcommands:

| Command | Purpose |
|---------|---------|
| `artifact.py init --section <name>` | Create a metadata + markdown pair from templates. Returns the new `artifact_id`. |
| `artifact.py set-phase <id> <phase>` | Transition phase. |
| `artifact.py set-progress <id> --completed N --total M` | Update progress. |
| `artifact.py approve <id> --approver <name> [--notes ...]` | Transition approval state. |
| `artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | Add a traceability reference. |
| `artifact.py show <id>` | Pretty-print the metadata. |
| `artifact.py list` | List all artifacts in the project. |
| `artifact.py validate [<id>]` | Validate schema and traceability for one or all artifacts. |
| `artifact.py report path --kind <k> --stage <s> [--target <id> ...]` | Allocate a fresh subagent handoff report file with the required frontmatter stub. Returns `{report_id, path}`. |
| `artifact.py report list [--kind <k>] [--stage <s>] [--target <id>]` | List reports, newest first. |
| `artifact.py report show <report_id>` | Print a report (frontmatter + body). |
| `artifact.py report validate <report_id-or-path>` | Validate a report's frontmatter against the handoff contract. |

The artifact directory defaults to `./artifacts/re/` under the user's current working directory. Override with the `HARNESS_ARTIFACTS_DIR` environment variable when needed. Subagent reports live under `<artifacts-dir>/.reports/`.

## A few non-negotiables

- **Dialogue first.** If the user's request is ambiguous, ask questions before you draft anything. Silent generation of an SRS from a one-line prompt is a failure mode, not a feature.
- **Adaptive depth.** Do not force heavy process on a single-feature request; do not trivialise a genuinely complex system. Pick the mode consciously and tell the user which mode you chose and why.
- **Three sections, nothing more.** RE stops at high-level requirements. Do not sneak in architecture decisions or implementation details — those belong to `arch` and `impl`.
- **Traceability.** Every requirement, constraint, and quality attribute gets a stable ID (`FR-001`, `NFR-001`, `CON-001`, `QA-001`). Record the user's utterance as `upstream_refs` so downstream skills can trace decisions back to the source.
- **Scripts only for metadata.** If you ever feel tempted to `Edit` a `.meta.yaml`, stop — the right answer is almost always a subcommand of `artifact.py`.
- **Subagent reports go to files, not messages.** Every subagent stage allocates a report path via `artifact.py report path` before spawning, the subagent writes the findings to that file, and returns only `report_id + verdict + summary`. This applies in both light and heavy modes — uniformity is the point. Subagents never call `artifact.py set-phase`, `set-progress`, `link`, or `approve` directly; they emit `proposed_meta_ops` in the report frontmatter and the main agent applies them.
