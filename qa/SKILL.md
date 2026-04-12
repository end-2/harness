---
name: qa
description: Turn approved RE, Arch, and Impl artifacts into the four QA section artifacts — Test Strategy, Test Suite, Requirements Traceability Matrix (RTM), and Quality Report — plus the actual test code under the project tree. Use this skill whenever the user is ready to verify an implementation against the requirements that drove it, asks to plan a test strategy from approved Impl + Arch + RE artifacts, wants tests generated against component boundaries and acceptance criteria, asks for a coverage / RTM gap analysis, or wants a quality-gate verdict before handing off to deployment — even if they don't explicitly say "QA" or "testing".
---

# QA — Quality Assurance Skill

QA is the fourth stage of the Harness pipeline. It consumes the approved RE, Arch, and Impl artifacts and produces (a) actual test code under the project tree and (b) four QA section artifacts that downstream skills (`deployment`, `operation`, `management`, `security`) can read directly.

If RE answered **"what are we building?"**, Arch answered **"how is it structured?"**, and Impl answered **"what does the realising code look like?"**, QA answers **"how do we know that code actually satisfies what RE asked for?"**. The trade-offs between scope, technique, and depth were already constrained by RE priorities, Arch boundaries, and Impl module layout — do **not** re-debate them. QA is an **automatic execution + exception escalation** model: mechanically derive strategy, suite, RTM, and gate verdict from the upstream artifacts, and only escalate to the user when a `must` requirement has a coverage gap that cannot be closed automatically.

## Current state (injected at load)

!`python ${SKILL_DIR}/scripts/artifact.py validate`

!`python ${SKILL_DIR}/scripts/artifact.py rtm-gap-report`

The first command lists existing QA artifacts with their phase, approval state, and traceability integrity. The second prints the current RTM gap roll-up grouped by MoSCoW priority. Read both before deciding whether this run is a fresh strategy pass, a continuation of suite generation, a re-review after a refactor, or just a quality-report regeneration.

## Input / output contract

**Input**: the approved RE, Arch, and Impl artifacts under the standard standalone locations `./artifacts/re/`, `./artifacts/arch/`, and `./artifacts/impl/`. In orchestrated runs, Orch passes the exact upstream artifact paths as context. `HARNESS_ARTIFACTS_DIR` still points to QA's own output directory. Specifically:

- `RE-SPEC-*` — Requirements Specification (FRs and NFRs with `acceptance_criteria`, `priority`, `dependencies`)
- `RE-CON-*` — Constraints (`type`, `flexibility`, `rationale`)
- `RE-QA-*` — Quality Attribute Priorities (`attribute`, `priority`, `metric`)
- `ARCH-DEC-*`, `ARCH-COMP-*`, `ARCH-TECH-*`, `ARCH-DIAG-*` — the four Arch sections
- `IMPL-MAP-*`, `IMPL-CODE-*`, `IMPL-IDR-*`, `IMPL-GUIDE-*` — the four Impl sections

If any required artifact is missing, unreadable, or still in `draft` / `in_review` / `revising`, stop and tell the user — QA must not run on unstable input. Read [references/contracts/re-input-contract.md](references/contracts/re-input-contract.md), [references/contracts/arch-input-contract.md](references/contracts/arch-input-contract.md), and [references/contracts/impl-input-contract.md](references/contracts/impl-input-contract.md) for the exact field-by-field mapping each upstream skill exposes.

**Output**: four section artifacts under `./artifacts/qa/`, each stored as a YAML metadata file plus a Markdown document, **plus** the actual test source files under the project tree:

1. **Test Strategy** (`QA-STRATEGY-*`) — scope, pyramid ratios, NFR test plan, environment matrix, test-double strategy, quality-gate criteria, with `re_refs` / `arch_refs` / `impl_refs` to every input that justified a choice.
2. **Test Suite** (`QA-SUITE-*`) — generated test cases grouped into suites, each case in Given-When-Then form with a `technique` tag, an `acceptance_criteria_ref` back to RE, and the path of the actual test file under the project tree.
3. **Requirements Traceability Matrix** (`QA-RTM-*`) — one row per RE requirement, with the chain `re_id → arch_refs → impl_refs → test_refs` and a `coverage_status` of `covered` / `partial` / `uncovered`. RTM rows are first-class metadata; they are managed exclusively through `rtm-upsert`.
4. **Quality Report** (`QA-REPORT-*`) — code coverage, requirements coverage, NFR measured-vs-target, the `quality_gate` block with `criteria` and `actuals`, the residual risk list, and recommendations. The gate verdict drives `approval.state` automatically via `gate-evaluate`.

Each of the four sections is a pair `<id>.meta.yaml` + `<id>.md`. Metadata is the single source of truth for state, traceability, RTM rows, and gate criteria — and it is **only** modified through `scripts/artifact.py`. Markdown holds the human-readable body and is edited directly, but only inside the scaffolding produced by `assets/templates/`. The actual test source files under the project tree are **not** governed by the metadata/document split — they are ordinary source that the agent creates and edits with Write / Edit directly.

Full schemas: read [references/schemas/section-schemas.md](references/schemas/section-schemas.md) and [references/schemas/meta-schema.md](references/schemas/meta-schema.md) when you need the exact field list.

Downstream consumption contract: read [references/contracts/downstream-contract.md](references/contracts/downstream-contract.md) before declaring the artifacts ready, so you know what `deployment` / `operation` / `management` / `security` will actually look for.

## Adaptive depth

QA's output depth follows Impl's mode (which itself follows Arch's). Do **not** apply a full pyramid + NFR plan + RTM + formal quality gate to a single-feature CRUD prototype, and do not trivialise verification of a genuinely distributed system.

| Mode | Trigger (from upstream artifacts) | Output style |
|------|----------------------------------|--------------|
| **light** | Impl ran in light mode (single project scaffold, 0–2 IDRs, brief Implementation Guide). | Core unit tests + an acceptance-criteria checklist rendered into the Test Suite document. RTM is still produced but kept compact (one row per FR/NFR, no per-criterion explosion). NFR plan only if RE has explicit `metric` values. Quality Report is short but the `quality_gate` block is still filled in. |
| **heavy** | Impl ran in heavy mode (multi-module project, one IDR per significant decision, full Code Structure with Mermaid graph). | Full test pyramid (unit / integration / e2e / contract / nfr), one Test Suite per Arch component or tight grouping, full RTM with per-`acceptance_criteria` rows where they exist, NFR test scenarios derived from every `RE-QA-*.metric`, full Quality Report with code-coverage breakdown, NFR actuals vs targets, residual risks, and recommendations. |

Pick the mode at the **start** of `strategy`, after reading the upstream artifacts. Tell the user which mode you chose and which signal you used. The user may override. Full rules: [references/adaptive-depth.md](references/adaptive-depth.md).

## Workflow (four stages)

```
RE artifacts (RE-SPEC / RE-CON / RE-QA, all approved)
Arch artifacts (ARCH-DEC / ARCH-COMP / ARCH-TECH / ARCH-DIAG, all approved)
Impl artifacts (IMPL-MAP / IMPL-CODE / IMPL-IDR / IMPL-GUIDE, all approved)
    │
    ▼
[1] strategy  → derive scope, pyramid, NFR plan, environment matrix,
    │           test-double strategy, and quality-gate criteria from the
    │           upstream artifacts. Mode chosen here.
    ▼
[2] generate  → for every requirement in scope, write Given-When-Then test
    │           cases, emit the actual test source files, and record each
    │           case in the Test Suite section with full re/arch/impl refs.
    ▼
[3] review    → build / refresh the RTM, classify every gap, and route
    │
    ├── covered / Should-or-lower gap ──→ accept (record as residual risk)
    ├── Must gap, auto-fixable ──→ back to [2] generate (targeted)
    └── Must gap, unfixable ──→ escalate to user
    │
    ▼
[4] report    → run the test suite, collect actuals, fill the Quality Report,
                call gate-evaluate to drive approval.state. Hand off to
                deployment.
```

Each stage has detailed behaviour rules in `references/workflow/<stage>.md`. When you enter a stage, **Read that file first** and follow the rules there. SKILL.md only gives the summary.

The pipeline is **checkpoint-based**, not one-way. `review` routes auto-fixable Must gaps back into `generate` and re-enters `review` after each generation pass. Should / Could / Won't gaps are accepted as residual risk — they appear in the Quality Report but never escalate. Only **unfixable Must gaps** (e.g. an RE requirement whose verification needs infrastructure that does not exist in the project) escalate back to the user.

### Subagent delegation (hybrid)

QA splits stages between the **main agent** (which talks to the user and writes test source code + section markdown) and isolated **subagents** (which work in a clean context window):

| Stage | Runs in | Why |
|-------|---------|-----|
| 1. strategy | main | needs to talk to the user about mode selection and quality-gate defaults; touches all four Impl sections to size the work |
| 2. generate | main | writes test source files and the Test Suite markdown together; conflicts with existing tests must surface to the user in real time |
| 3. review | **subagent** | pure verification (RTM completeness, coverage classification, traceability integrity) over settled code — a clean context catches more gaps |
| 4. report | **subagent** | runs the test suite, parses results, computes coverage, and assembles the Quality Report draft over a known artifact set — benefits from a clean context free of the generation dialogue |

**Sequencing rule (mandatory):** the stages have a hard order — `strategy → generate → review → generate → review → … → report` — because each consumes the previous one's output. Never spawn these subagents in parallel, and never start one before its predecessor has finished writing to disk.

**File-based handoff (light and heavy both):** `review` and `report` each write their output to a **report file** under `./artifacts/qa/.reports/` and return only `report_id + verdict + summary` in their message. For `review` the body is a structured RTM-gap list (one item per uncovered/partial requirement, with `gap_type` and a suggested generation directive). For `report` the body is the Quality Report draft (coverage tables, NFR actuals, gate evaluation result) plus any `proposed_meta_ops` (e.g. `rtm-upsert`, `write-quality-report-actuals`, `gate-evaluate`). The main agent reads the report via `artifact.py report show`, validates it, applies any meta ops, and acts. Subagents **never** edit `*.meta.yaml` directly and **never** call `artifact.py init / set-block / set-phase / approve / link / rtm-upsert / gate-evaluate` themselves — they emit `proposed_meta_ops` in the report frontmatter and the main agent applies them. Read [references/contracts/subagent-report-contract.md](references/contracts/subagent-report-contract.md) for the frontmatter schema and per-stage fields.

Before spawning any subagent, the main agent allocates the report path:

```bash
python ${SKILL_DIR}/scripts/artifact.py report path \
    --kind <review|report> --stage <review|report> --scope all
```

and passes the printed `path` to the subagent as one of its inputs.

Inside `generate` itself, the four sections must be created **in order**: `test-strategy → test-suite → rtm → quality-report`, because each later section references artifacts the earlier ones produced.

### Stage 1 — strategy

Load [references/workflow/strategy.md](references/workflow/strategy.md).

- Read the RE / Arch / Impl artifacts. Treat `RE-SPEC-*.acceptance_criteria` as the authoritative source of test cases, `RE-SPEC-*.priority` as the MoSCoW gate (Must = mandatory coverage, Should = best-effort, Could/Won't = explicitly out of scope), and `RE-QA-*.metric` as the binding NFR target. From Arch, treat `ARCH-COMP-*.interfaces` as the integration boundary and `ARCH-DEC-*.decision` as the pattern hint for test style (event-driven → async message tests, microservices → contract tests, layered → layer-boundary integration tests). From Impl, treat `IMPL-MAP-*.module_path` as the test-file location anchor, `IMPL-CODE-*.module_dependencies` as the test-double seam map, and `IMPL-IDR-*.pattern_applied` as the per-pattern testability rule.
- Pick adaptive mode (see above) and tell the user.
- Draft the Test Strategy section: scope, pyramid ratios, NFR test plan, environment matrix, test-double strategy, quality-gate criteria.

`strategy` is the first stage that **writes to disk**. Sequence:

1. Create the artifact pair from templates:
   ```
   python ${SKILL_DIR}/scripts/artifact.py init --section test-strategy
   ```
2. Fill in the Markdown body by editing only the `.md` file — never touch `.meta.yaml` with Edit/Write.
3. Update structured state through the script:
   ```
   python ${SKILL_DIR}/scripts/artifact.py set-block    <id> --field test_strategy --from /tmp/test-strategy.yaml
   python ${SKILL_DIR}/scripts/artifact.py set-progress <id> --completed N --total M
   python ${SKILL_DIR}/scripts/artifact.py link         <id> --upstream RE-SPEC-001
   python ${SKILL_DIR}/scripts/artifact.py link         <id> --upstream IMPL-MAP-001
   python ${SKILL_DIR}/scripts/artifact.py set-phase    <id> in_review
   ```

**Escalation condition**: escalate to the user only when an upstream artifact is missing or incoherent, or when the project is so small that QA cannot be meaningfully scoped (e.g. RE has no acceptance criteria at all).

### Stage 2 — generate

Load [references/workflow/generate.md](references/workflow/generate.md).

- For every in-scope FR / NFR, convert each `acceptance_criteria` into one or more Given-When-Then test cases. Pick a `technique` deliberately: `boundary_value`, `equivalence_partition`, `decision_table`, `state_transition`, `property_based`, or `example_based` for everything else.
- Map each case to the right test type: `unit` (Impl module-level), `integration` (Arch interface boundaries), `e2e` (Arch sequence diagrams), `contract` (microservice or external API boundary), `nfr` (RE `metric` target).
- Write the actual test files under the project tree using the testing framework recorded in `IMPL-CODE-*.external_dependencies` (or `ARCH-TECH-*` if Impl has not yet pinned one). Place tests where `IMPL-GUIDE-*.conventions.tests` says they belong; fall back to the stack idiom only when no convention is detectable.
- Record every test case in the Test Suite metadata block with `re_refs`, `arch_refs`, `impl_refs`, and the `acceptance_criteria_ref` of the criterion it verifies by writing `test_suite` through `artifact.py set-block`. After each suite, immediately call `rtm-upsert` to update the RTM row for the requirements that just gained coverage.

Stage 2 sequence:

1. `artifact.py init --section test-suite` (one Test Suite artifact per Arch component group, or a single one in light mode).
2. `artifact.py init --section rtm` (only once — the RTM is project-wide).
3. Edit the suite `.md` files via Edit. Never Edit `.meta.yaml`.
4. Write the actual test files with Write/Edit. They are not tracked by `artifact.py`.
5. Write the structured suite payload through the script:
   ```
   python ${SKILL_DIR}/scripts/artifact.py set-block <suite-id> --field test_suite --from /tmp/test-suite.yaml
   ```
6. After each suite is filled in, refresh the RTM:
   ```
   python ${SKILL_DIR}/scripts/artifact.py rtm-upsert \
       --re-id FR-001 --test-refs QA-SUITE-001:TS-001-C01 \
       --arch-refs ARCH-COMP-001 --impl-refs IMPL-MAP-001 \
       --status covered
   ```
7. Add traceability:
   ```
   python ${SKILL_DIR}/scripts/artifact.py link <suite-id> --upstream IMPL-MAP-001
   python ${SKILL_DIR}/scripts/artifact.py link <suite-id> --upstream RE-SPEC-001
   ```
8. When the suite draft is complete: `artifact.py set-phase <id> in_review`.

**Escalation condition**: escalate when an Arch decision implies a test type the project cannot run (e.g. a microservice contract test without any contract framework, or an NFR metric that requires load infrastructure that does not exist) and you cannot fall back to a smaller equivalent.

### Stage 3 — review

**Run this stage as a subagent.** First allocate a report path (`artifact.py report path --kind review --stage review --scope all`), then spawn a single `general-purpose` Agent with the generated test sources, the four QA section artifacts, the upstream RE / Arch / Impl artifacts, **and the allocated report path** as its input. Its job is to write a structured RTM-gap report file: one item per uncovered/partial requirement with `re_id`, `priority`, `gap_type` (`missing_test`, `partial_criteria`, `weak_assertion`, `missing_nfr_scenario`, `traceability_break`), and a suggested fix. The subagent returns only `report_id + verdict + summary`; the main agent reads the report via `artifact.py report show`, routes items, and acts. Do not run it in parallel with `generate`, and do not start it before `generate` has finished writing.

Load [references/workflow/review.md](references/workflow/review.md).

The review runs along three axes:

1. **Requirements coverage** — every `RE-SPEC-*` requirement (FR + NFR) has at least one test case linked to it via the RTM, every `acceptance_criteria` has a matching `acceptance_criteria_ref`, and every `RE-QA-*` quality attribute with a `metric` has a corresponding NFR test scenario.
2. **Test strength** — assertions are non-vacuous, boundary cases exist where the technique demands them, the test does not silently pass on a stub, and there are no obvious flaky patterns (time, ordering, external dependency without a fake).
3. **Traceability** — every test case can be walked back through `impl_refs → arch_refs → re_refs` to a single root requirement; every Implementation Map entry has at least one test case targeting it; every NFR metric has a measurement scenario.

Classification drives routing:
- `covered` and Should/Could/Won't gaps → accept; record as residual risk in the Quality Report.
- Must gaps with a clear fix path → route back to `generate` with a targeted directive.
- Must gaps with no fix path inside the project as it stands → **escalate to the user**, citing the RE id and the missing piece.

After the review is consumed, refresh the RTM via `rtm-upsert` for every row whose status changed.

### Stage 4 — report

**Run this stage as a subagent.** First allocate a report path (`artifact.py report path --kind report --stage report --scope all`), then spawn a single `general-purpose` Agent with the test sources, the QA section artifacts (read-only), the upstream RE / Arch / Impl artifacts, and the allocated report path. Its job is to actually run the test suite (using `IMPL-GUIDE-*.run_commands` and the testing framework), collect coverage, compare NFR actuals against `RE-QA-*.metric` targets, draft the Quality Report body, and emit the `proposed_meta_ops` needed to update the report metadata and call `gate-evaluate`. It does **not** call `gate-evaluate` itself.

Load [references/workflow/report.md](references/workflow/report.md).

- Code coverage: per-module line + branch numbers, plus the project total.
- Requirements coverage: derived from the RTM via `rtm-gap-report`.
- NFR actuals: one row per `RE-QA-*` metric with target, measured value, and pass/fail.
- Residual risk list: every `partial` / `uncovered` row from the RTM that was *accepted* during review (Should / Could / Won't). Must gaps that escalated and were resolved by the user must also appear with their resolution noted.
- Quality gate: the `quality_gate` block in the Quality Report metadata holds `criteria` (from strategy) and `actuals` (from this stage). Run `gate-evaluate` to apply the verdict:
  ```
  python ${SKILL_DIR}/scripts/artifact.py gate-evaluate <quality-report-id>
  ```
  - Verdict `pass` → `approval.state` transitions to `approved`, `phase` to `approved`.
  - Verdict `fail` → `approval.state` transitions to `rejected`.
  - Verdict `escalated` (an unresolved Must gap is still present) → `approval.state` transitions to `escalated` and the report body must list which Must requirements are blocking.

When the Quality Report is `approved`, point the user at the next skill (`deployment`, `operation`, `management`, `security`) and stop.

## Script contract (mandatory)

**Never edit `*.meta.yaml` files directly.** All state changes — phase, progress, section payloads, approval, traceability, RTM rows, quality-gate evaluation — must go through `scripts/artifact.py`. The script enforces:

- Schema validation (rejects unknown phases, missing fields, unknown coverage statuses).
- `updated_at` auto-refresh.
- Legal phase transitions only (`draft → in_review → revising → in_review → approved → superseded`). You cannot jump straight from `draft` to `approved`.
- Section-payload writes through `set-block` (`test_strategy`, `test_suite`, `quality_report`, `quality_gate.criteria`, `quality_gate.actuals`) so the validator can reject malformed structured metadata before it lands on disk.
- Bidirectional `upstream_refs` / `downstream_refs` integrity (so a link from `QA-SUITE-001` to `IMPL-MAP-001` shows up on both sides when both live under the same artifacts directory).
- An `approval.history` audit trail with timestamps.
- RTM rows are first-class metadata: `rtm-upsert` is the only way to add or change a row, and `rtm-gap-report` is the only blessed source of the gap roll-up that strategy / report consume.
- `gate-evaluate` is the only legal way to transition a Quality Report's `approval.state` based on test results — direct `approve` calls on a Quality Report are refused.

Available subcommands:

| Command | Purpose |
|---------|---------|
| `artifact.py init --section <name>` | Create a metadata + markdown pair from templates. `<name>` is one of `test-strategy`, `test-suite`, `rtm`, `quality-report`. Returns the new `artifact_id`. |
| `artifact.py set-block <id> --field <field> (--from <path> \| --value <yaml-or-json>)` | Replace a structured metadata block (`test_strategy`, `test_suite`, `quality_report`, `quality_gate.criteria`, or `quality_gate.actuals`) through the script. |
| `artifact.py set-phase <id> <phase>` | Transition phase. |
| `artifact.py set-progress <id> --completed N --total M` | Update progress. |
| `artifact.py approve <id> --approver <name> [--state <s>] [--notes ...]` | Transition approval state. Refuses Quality Report ids — use `gate-evaluate`. |
| `artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | Add a traceability reference. Cross-skill refs (`RE-*`, `ARCH-*`, `IMPL-*`, `DEPLOY-*`, …) are allowed. |
| `artifact.py rtm-upsert --re-id <id> [--arch-refs ...] [--impl-refs ...] [--test-refs ...] --status <s> [--gap <text>]` | Insert or update the RTM row for a requirement. Status is `covered` / `partial` / `uncovered`. |
| `artifact.py rtm-gap-report` | Print the RTM gap roll-up grouped by MoSCoW priority. Used both as a load-time context injector and as the source for the Quality Report. |
| `artifact.py gate-evaluate <quality-report-id>` | Read the report's `quality_gate.criteria` and `quality_gate.actuals`, compute the verdict, and transition `approval.state` accordingly. |
| `artifact.py show <id>` | Pretty-print the metadata. |
| `artifact.py list` | List all QA artifacts in the project. |
| `artifact.py validate [<id>]` | Validate schema and traceability for one or all artifacts. |
| `artifact.py report path --kind <k> --stage <s> [--scope all]` | Allocate a fresh subagent handoff report file with the required frontmatter stub. Returns `{report_id, path}`. |
| `artifact.py report list [--kind <k>] [--stage <s>] [--target <id>]` | List subagent handoff reports, newest first. |
| `artifact.py report show <report_id>` | Print a report (frontmatter + body). |
| `artifact.py report validate <report_id-or-path>` | Validate a report's frontmatter against the handoff contract. |

The artifact directory defaults to `./artifacts/qa/` under the user's current working directory. Override with `HARNESS_ARTIFACTS_DIR`. Test source files are **not** tracked by this script — they live under the project tree and are edited directly. Subagent reports live under `<artifacts-dir>/.reports/`.

## A few non-negotiables

- **RE/Arch/Impl are the source of truth.** Do not invent requirements, expand scope beyond MoSCoW Must/Should, or test code paths that no Implementation Map entry covers. If something is missing upstream, send the user back upstream — do not patch around it inside QA.
- **Automatic execution, exception escalation.** Do not ask the user for test framework, test layout, or coverage targets — read them from `IMPL-CODE-*` / `IMPL-GUIDE-*` / `ARCH-TECH-*`, and fall back to stack idioms only when nothing is detectable. Escalate only when a Must requirement has an unfixable coverage gap.
- **Adaptive depth.** Light mode is not lazy — it is correct sizing. Do not write a full pyramid + NFR plan + RTM-per-criterion for a CRUD scaffold.
- **Four sections, nothing more.** QA stops at tests + the four sections. Pipeline wiring belongs to `deployment`; deep threat modelling belongs to `security`; SLO definitions belong to `operation`.
- **Traceability.** Every test case cites at least one `RE-*` ref via `acceptance_criteria_ref` (directly or transitively through the RTM). If a case has no anchor, it does not belong in the suite yet.
- **Scripts only for metadata.** If you ever feel tempted to `Edit` a `.meta.yaml`, stop — the right answer is almost always a subcommand of `artifact.py`. RTM rows in particular are *only* edited through `rtm-upsert`.
- **Subagent reports go to files, not messages.** `review` and `report` each allocate a report path via `artifact.py report path` before spawning, write the findings (and, for `report`, the actual coverage / NFR tables) to that file, and return only `report_id + verdict + summary`. Subagents never call `artifact.py set-phase / approve / rtm-upsert / gate-evaluate`; they emit `proposed_meta_ops` and the main agent applies them.
