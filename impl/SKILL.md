---
name: impl
description: Turn the four-section Arch artifact (Architecture Decisions, Component Structure, Technology Stack, Diagrams) into real source code plus the four Impl sections — Implementation Map, Code Structure, Implementation Decisions, Implementation Guide. Use this skill whenever the user is ready to move from architecture to code, asks to scaffold a project from an approved Arch design, wants code generated against component boundaries and a chosen tech stack, asks for a code review against Arch decisions, requests a refactor that must respect component boundaries, or is about to invoke qa/security/deployment — even if they don't explicitly say "implementation".
---

# Impl — Implementation Skill

Impl is the third stage of the Harness pipeline. It consumes the four approved Arch artifacts and produces (a) actual source code under the project tree and (b) four Impl section artifacts that downstream skills (`qa`, `security`, `deployment`, `operation`, `management`) can read directly.

If RE answered **"what are we building?"** and Arch answered **"how is it structured?"**, Impl answers **"what does the code that realises that structure actually look like?"**. The trade-offs between components, technologies, and patterns were already settled in Arch — do **not** re-debate them. Impl is an **automatic execution + exception escalation** model: mechanically turn Arch decisions into code, and only escalate to the user when an Arch decision is genuinely unrealisable at the code level.

## Current state (injected at load)

!`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate`

The command above lists existing impl artifacts, their phase, approval state, and traceability integrity. Read it before deciding whether this run is a fresh start, a continuation of in-progress generation, or a re-review / refactor pass over already-generated code.

## Input / output contract

**Input**: the four approved Arch artifacts in `./artifacts/arch/` (or wherever `HARNESS_ARTIFACTS_DIR` points). Specifically:

- `ARCH-DEC-*` — Architecture Decisions (ADRs) and the structured decision table
- `ARCH-COMP-*` — Component Structure (responsibilities, interfaces, dependencies, FR/NFR refs)
- `ARCH-TECH-*` — Technology Stack (language / framework / DB / infra with constraint refs)
- `ARCH-DIAG-*` — Diagrams (C4 Context/Container, sequence, data-flow)

If any of those artifacts are missing, unreadable, or still in `draft`/`in_review`, stop and tell the user — Impl must not run on unstable input. RE artifacts are not consumed directly; Impl reaches RE only through Arch's `re_refs` / `constraint_ref` chains. Read [references/contracts/arch-input-contract.md](references/contracts/arch-input-contract.md) for the exact mapping from Arch fields to code-generation directives.

**Output**: four section artifacts under `./artifacts/impl/`, each stored as a YAML metadata file plus a Markdown document, **plus** the actual source files under the project tree:

1. **Implementation Map** (`IMPL-MAP-*`) — every Arch component mapped to a concrete module path, entry point, internal structure, and interface implementation file, with `arch_refs` back to `ARCH-COMP-*`.
2. **Code Structure** (`IMPL-CODE-*`) — the generated project's directory layout, module dependency graph, external dependencies with versions, build and environment configuration.
3. **Implementation Decisions** (`IMPL-IDR-*`) — every code-level decision recorded as an IDR with rationale, alternatives, applied pattern (if any), and both `arch_refs` and `re_refs`.
4. **Implementation Guide** (`IMPL-GUIDE-*`) — prerequisites, setup/build/run commands, detected conventions, and extension points.

Each of the four sections is a pair `<id>.meta.yaml` + `<id>.md`. Metadata is the single source of truth for state and traceability and is **only** modified through `scripts/artifact.py`. Markdown holds the human-readable body and is edited directly, but only inside the scaffolding produced by `assets/templates/`. The actual source code under the project tree is **not** governed by the metadata/document split — it is ordinary source that the agent creates and edits with Write / Edit directly.

Full schemas: read [references/schemas/section-schemas.md](references/schemas/section-schemas.md) and [references/schemas/meta-schema.md](references/schemas/meta-schema.md) when you need the exact field list.

Downstream consumption contract: read [references/contracts/downstream-contract.md](references/contracts/downstream-contract.md) before declaring the artifact ready, so you know what `qa` / `security` / `deployment` / `operation` / `management` will actually look for.

## Adaptive depth

Impl's output depth follows Arch's mode. Do **not** apply a heavy multi-module scaffold with full IDR records to a single-feature CRUD prototype, and do not trivialise a genuinely distributed system.

| Mode | Trigger (from Arch artifacts) | Output style |
|------|------------------------------|--------------|
| **light** | Arch ran in light mode (style recommendation + directory guide, C4 Context only, ≤ 2 ADRs) | Single project scaffold, core modules implemented, inline implementation notes instead of formal IDRs, minimal Implementation Decisions artifact (0–2 IDRs), Implementation Guide kept short. |
| **heavy** | Arch ran in heavy mode (full component decomposition with interfaces, ADRs per significant decision, Container + sequence diagrams) | Multi-module project structure, interface-contract code per component, one IDR per significant code-level decision, full Implementation Map + Code Structure + Guide, explicit refactor pass. |

Pick the mode at the **start** of `generate`, after reading the Arch artifacts. Tell the user which mode you chose and why. The user may override. Full rules: [references/adaptive-depth.md](references/adaptive-depth.md).

## Workflow (four stages)

```
Arch artifacts (ARCH-DEC / ARCH-COMP / ARCH-TECH / ARCH-DIAG, all approved)
    │
    ▼
[1] generate  → auto-detect codebase conventions, scaffold project, realise
    │           every component in code, draft the four Impl sections
    ▼
[2] pattern   → evaluate and apply patterns (mandatory ones from Arch,
    │           optional ones by problem-fit), record each as an IDR
    ▼
[3] review    → verify Arch-decision compliance + clean-code quality;
    │           emit issue list with severities
    │
    ├── auto-fixable issues ──→ [4] refactor ──→ back to [3] review
    │
    ├── Arch-contract violations ──→ escalate to user
    │
    ▼
Final artifacts (four sections + source tree) → hand off to qa / security / deployment
```

Each stage has detailed behavior rules in `references/workflow/<stage>.md`. When you enter a stage, **Read that file first** and follow the rules there. SKILL.md only gives the summary.

The pipeline is **checkpoint-based**, not one-way. `review` routes auto-fixable issues into `refactor` and re-enters `review` after each refactor pass. Only **Arch-contract violations** (component-boundary crossings that cannot be fixed without changing Arch, unrealisable interfaces, forbidden technology use) escalate back to the user.

### Subagent delegation (hybrid)

Impl splits stages between the **main agent** (which talks to the user and writes source code + section markdown) and isolated **subagents** (which work in a clean context window):

| Stage | Runs in | Why |
|-------|---------|-----|
| 1. generate | main | needs access to the existing codebase, writes source files and the four Impl section markdowns, and is the only stage where surprising conflicts with the existing code must be surfaced to the user in real time |
| 2. pattern | main | pattern application is tightly interleaved with generated code and must update the same markdown files; keeping it in the main context avoids churn |
| 3. review | **subagent** | pure verification (Arch compliance + clean-code checks) over settled code — a clean context catches more gaps and produces a tighter issue list |
| 4. refactor | **subagent** | focused code transformation over a known issue list, bounded by Arch component boundaries — benefits from a clean context free of the generation dialogue |

**Sequencing rule (mandatory):** the stages have a hard order — `generate → pattern → review → refactor → review → …` — because each consumes the previous one's output. `pattern` reads the code written by `generate`. `review` reads code + all four Impl sections. `refactor` reads the review report and the current code. Never spawn these subagents in parallel, and never start one before its predecessor has finished writing to disk.

Inside `generate` itself, the four sections must be created **in order**: `implementation-map → code-structure → implementation-decisions → implementation-guide`, because each later section references artifacts the earlier ones produced.

### Stage 1 — generate

Load [references/workflow/generate.md](references/workflow/generate.md).

- Read the four Arch artifacts. Treat `ARCH-COMP-*` as the authoritative component boundary, `ARCH-DEC-*` as non-negotiable structural decisions, and `ARCH-TECH-*` as the mandatory technology set. `ARCH-DIAG-*` (sequence / data-flow) drives the method-call order you implement.
- **Detect the existing codebase context automatically, without asking the user**: existing conventions (naming, directory layout, formatter config), dependency manifests (`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, …), build and run config (`Dockerfile`, `Makefile`, CI files), the idiomatic error-handling and logging style for the chosen stack. If there is no existing codebase, fall back to the stack's idiomatic defaults.
- Scaffold the project directory, generate the interface/type contracts from `ARCH-COMP-*.interfaces`, then implement each component in turn. Import graph must match `ARCH-COMP-*.dependencies`.
- Draft the four Impl sections as you go: Implementation Map entries are created as each component becomes real; Code Structure is updated as the tree grows; Implementation Decisions captures code-level choices not settled by Arch; Implementation Guide records prerequisites / setup / build / run / conventions / extension points.

`generate` is the first stage that **writes to disk**. Sequence, for each of the four sections:

1. Create the artifact pair from templates:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section implementation-map
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section code-structure
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section implementation-decisions
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section implementation-guide
   ```
2. Fill in the Markdown body by editing only the `.md` file — never touch `.meta.yaml` with Edit/Write.
3. Update structured state through the script:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-progress <id> --completed N --total M
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link         <id> --upstream ARCH-COMP-001
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase    <id> in_review
   ```
4. Write the actual source files under the project tree with Write/Edit. Source files are not tracked by `artifact.py`.

**Escalation condition**: escalate to the user only when an Arch decision cannot be realised at the code level — e.g. a chosen framework cannot expose the interface shape Arch specified, or the existing codebase and the Arch decision are in unresolvable conflict. Small code-level choices are recorded as IDRs, not escalated.

### Stage 2 — pattern

Load [references/workflow/pattern.md](references/workflow/pattern.md).

- Patterns explicitly named in `ARCH-DEC-*` are **mandatory**: apply them and record the application as an IDR citing the ADR.
- Patterns not named in Arch are **discretionary**: apply them only when the problem shape clearly matches (Repository when data access leaks across layers, Strategy when you see a long `if/elif` ladder on a type field, etc.), and record every application as an IDR with the rationale and the trade-off.
- Over-application is a failure mode: the absence of a pattern is often the right call. Warn in the IDR when you deliberately chose *not* to apply one.
- Update the Implementation Decisions section after every pattern application:
  ```
  python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link <impl-idr-id> --upstream ARCH-DEC-002
  ```

No user escalation in this stage — Arch-mandated patterns must be applied, and discretionary patterns are recorded with their rationale.

### Stage 3 — review

**Run this stage as a subagent.** Spawn a single `general-purpose` Agent with the generated source tree, the four Impl section artifacts, and the four Arch artifacts as its input. Its job is to produce a structured review report: a list of issues with file:line locations, a severity, a classification (Arch-contract violation / clean-code smell / security smell), and a suggested fix. It returns the report for the main agent to act on. Do not run it in parallel with `refactor`, and do not start it before `pattern` has finished.

Load [references/workflow/review.md](references/workflow/review.md).

The review runs along two axes:

1. **Arch compliance** — component boundaries respected, interfaces implemented as specified, only technologies from `ARCH-TECH-*` used, Arch-mandated patterns present, sequence/data-flow diagrams realised in the corresponding code paths, `hard` RE constraints (reached via `constraint_ref`) visibly satisfied.
2. **Clean code** — SOLID, readability, naming consistency with detected conventions, cyclomatic / cognitive complexity, obvious bug smells, OWASP-level baseline security (deep security analysis belongs to the `security` skill).

Classification drives routing:
- Clean-code and security-baseline issues that can be fixed without crossing component boundaries → route to `refactor`.
- Arch-contract violations (component boundary crossings, forbidden technology use, missing Arch-mandated pattern, unrealisable interface) → **escalate to the user** with the Arch ref that is being violated.

### Stage 4 — refactor

**Run this stage as a subagent.** Spawn a single `general-purpose` Agent with the review report and the current source tree as its input. Its job is to apply fixes for the auto-fixable issues while respecting Arch component boundaries, and to return either the final code changes or a concrete patch. Do not run it in parallel with `review`, and do not start it before `review` has produced a report.

Load [references/workflow/refactor.md](references/workflow/refactor.md).

- Use Martin Fowler's catalogue (Extract Method, Move Field, Replace Conditional With Polymorphism, …) as the vocabulary.
- **Respect Arch boundaries**: a refactor that would require moving code across `ARCH-COMP-*` is out of scope — escalate instead.
- **Maintain traceability**: after any refactor that moves files, re-run `link` / `set-progress` on the affected Implementation Map entry so the mapping stays accurate, and update the Markdown body to match.
- Record non-trivial refactors as IDRs so the reasoning survives the code change.
- After applying fixes, hand control back to `review` for another pass. Loop until `review` produces a clean report or only leaves escalation-level items.

When the review report is clean and the user approves, transition each Impl artifact to `approved`:
```
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <id> --approver <user> --notes "..."
```

Once `IMPL-MAP-*`, `IMPL-CODE-*`, `IMPL-IDR-*`, and `IMPL-GUIDE-*` are all `approved`, Impl is done. Point the user at the next skill (`qa`, `security`, `deployment`, `operation`, `management`) and stop.

## Script contract (mandatory)

**Never edit `*.meta.yaml` files directly.** All state changes — phase, progress, approval, traceability — must go through `scripts/artifact.py`. The script enforces:

- Schema validation (rejects unknown phases, missing fields).
- `updated_at` auto-refresh.
- Legal phase transitions only (`draft → in_review → revising → in_review → approved → superseded`). You cannot jump straight from `draft` to `approved`.
- Bidirectional `upstream_refs` / `downstream_refs` integrity (so a link from `IMPL-MAP-001` to `ARCH-COMP-001` shows up on both sides when both live under the same artifacts directory).
- An `approval.history` audit trail with timestamps.

Available subcommands:

| Command | Purpose |
|---------|---------|
| `artifact.py init --section <name>` | Create a metadata + markdown pair from templates. `<name>` is one of `implementation-map`, `code-structure`, `implementation-decisions`, `implementation-guide`. Returns the new `artifact_id`. |
| `artifact.py set-phase <id> <phase>` | Transition phase. |
| `artifact.py set-progress <id> --completed N --total M` | Update progress. |
| `artifact.py approve <id> --approver <name> [--notes ...]` | Transition approval state. |
| `artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | Add a traceability reference. Cross-skill refs (e.g. `ARCH-COMP-001`, `RE-QA-001`) are allowed. |
| `artifact.py show <id>` | Pretty-print the metadata. |
| `artifact.py list` | List all impl artifacts in the project. |
| `artifact.py validate [<id>]` | Validate schema and traceability for one or all artifacts. |

The artifact directory defaults to `./artifacts/impl/` under the user's current working directory. Override with `HARNESS_ARTIFACTS_DIR`. Source code files are **not** tracked by this script — they live under the project tree and are edited directly.

## A few non-negotiables

- **Arch is the source of truth for structure.** Do not invent components, rename interfaces, or swap technologies. If Arch is wrong, send the user back to Arch — do not patch around it inside Impl.
- **Automatic execution, exception escalation.** Do not ask the user for coding conventions, dependency policy, or error-handling style — detect them from the existing codebase or fall back to stack idioms. Escalate only when Arch cannot be realised.
- **Adaptive depth.** Light mode is not lazy — it is correct sizing. Do not write nine IDRs for a CRUD scaffold.
- **Four sections, nothing more.** Impl stops at code + the four sections. Test generation belongs to `qa`; deep threat modeling belongs to `security`; deployment config belongs to `deployment`.
- **Traceability.** Every Implementation Map entry cites an Arch component. Every IDR cites at least one Arch or RE ref (via Arch). If a row has no anchor, it does not belong in the artifact yet.
- **Scripts only for metadata.** If you ever feel tempted to `Edit` a `.meta.yaml`, stop — the right answer is almost always a subcommand of `artifact.py`.
