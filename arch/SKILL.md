---
name: arch
description: Turn the three RE artifacts (Requirements Spec, Constraints, Quality Attribute Priorities) into a four-section architecture artifact — Architecture Decisions, Component Structure, Technology Stack, and Diagrams (C4 / Mermaid) — through a technical-context dialogue with the user. Use this skill whenever the user starts a new system design, asks to revisit architecture after RE updates, mentions ADRs, picks technologies, draws C4/sequence/data-flow diagrams, or is about to invoke impl/qa/security/deployment/operation — even if they don't explicitly say "architecture".
---

# Arch — Architecture Skill

Arch is the second stage of the Harness pipeline. It consumes the three RE artifacts and produces a four-section architecture artifact that downstream skills (`impl`, `qa`, `security`, `deployment`, `operation`) can read directly.

If RE answered **"what are we building?"**, Arch answers **"how is it structured, and which technologies make that structure work?"**. The trade-offs between quality attributes (latency vs consistency, security vs usability, …) were already settled in RE — do **not** re-debate them. Arch focuses on the *technical* trade-offs that sit one layer below: pattern selection, component decomposition, technology choice, and the operational consequences of those choices.

The user is the only stakeholder. RE captured *requirements*, but it deliberately left out **technical context**: team size and skills, existing infrastructure, operational maturity, budget realities, legacy code, deployment targets. Arch must surface those gaps through dialogue before drafting anything substantial.

## Current state (injected at load)

!`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate`

The command above lists existing arch artifacts, their phase, approval state, and traceability integrity. Read it before deciding whether this run is a fresh start or a continuation of an in-progress design.

## Input / output contract

**Input**: the three approved RE artifacts in `./artifacts/re/` (or wherever `HARNESS_ARTIFACTS_DIR` points). Specifically:

- `RE-REQ-*` — functional and non-functional requirements
- `RE-CON-*` — constraints classified by `flexibility` (`hard` / `soft` / `negotiable`)
- `RE-QA-*` — ranked quality attributes with measurable metrics and trade-off notes

If any of those artifacts are missing or still in `draft` / `in_review`, stop and tell the user — Arch must not run on unstable input. Read [references/contracts/re-input-contract.md](references/contracts/re-input-contract.md) for the exact parsing rules.

**Output**: four section artifacts, each stored as a YAML metadata file plus a Markdown document under `./artifacts/arch/`:

1. **Architecture Decisions** — every significant decision with rationale, alternatives considered, technical trade-offs, and `re_refs` back to the RE items that drove it.
2. **Component Structure** — the components that make up the system, their responsibilities, interfaces, dependencies, and which FR/NFR each one carries.
3. **Technology Stack** — the chosen language / framework / database / messaging / infra entries with rationale and `constraint_ref` back to RE constraints.
4. **Diagrams** — C4 Context (always) and Container (heavy mode), plus sequence and data-flow diagrams as needed, all in Mermaid.

Each section is a pair `<section>.meta.yaml` + `<section>.md`. Metadata is the single source of truth and is **only** modified through `scripts/artifact.py`. Markdown holds the human-readable body and is edited directly, but only inside the scaffolding produced by `assets/templates/`.

Full schemas: read [references/schemas/section-schemas.md](references/schemas/section-schemas.md) and [references/schemas/meta-schema.md](references/schemas/meta-schema.md) when you need the exact field list.

Downstream consumption contract: read [references/contracts/downstream-contract.md](references/contracts/downstream-contract.md) before declaring the artifact ready, so you know what `impl`/`qa`/`security`/`deployment`/`operation` will actually look for.

## Adaptive depth

Arch's output depth follows RE's output density. Do **not** apply a heavy ADR + C4 + Container process to a single-feature CRUD app, and do not trivialise a genuinely distributed system.

| Mode | Trigger (from RE artifacts) | Output style |
|------|----------------------------|--------------|
| **light** | FR ≤ 5 **and** NFR ≤ 2 **and** quality attributes ≤ 3 | Architecture style recommendation + layer/directory guide + tech stack recommendation. C4 Context only. ADRs optional, only for the one or two truly load-bearing decisions. |
| **heavy** | FR > 5 **or** NFR > 2 **or** quality attributes > 3, **or** the user asks for formal architecture docs | Full component decomposition with interfaces, ADRs for every significant decision, C4 Context **and** Container, sequence diagrams for the top flows. |

Pick the mode at the **start** of `design`, after reading the RE artifacts. Tell the user which mode you chose and why. The user may override. Full rules: [references/adaptive-depth.md](references/adaptive-depth.md).

## Workflow (four stages)

```
RE artifacts (RE-REQ / RE-CON / RE-QA, all approved)
    │
    ▼
[1] design   → read RE, surface technical context, draft decisions/components/tech-stack
    │
    ▼
[2] adr      → record the load-bearing decisions as ADRs with RE refs
    │
    ▼
[3] diagram  → visualise the confirmed design (C4 + sequence + data-flow as needed)
    │
    ▼
[4] review   → validate against RE quality-attribute metrics as scenarios; final approval
```

Each stage has detailed behavior rules in `references/workflow/<stage>.md`. When you enter a stage, **Read that file first** and follow the rules there. SKILL.md only gives the summary.

The pipeline is **checkpoint-based**, not one-way. If a review scenario fails or the user disagrees with a decision, step back to `design` and re-iterate. In light mode, `adr` and the Container layer of `diagram` may be skipped — see `references/adaptive-depth.md`.

### Stage 1 — design

Load [references/workflow/design.md](references/workflow/design.md).

- Read the three RE artifacts. Treat the top-ranked quality attributes as **architectural drivers**, treat `hard` constraints as **non-negotiable**, and use FR `dependencies` as hints for component boundaries.
- Surface technical context the user has not yet provided: team size and language familiarity, existing infrastructure (cloud / on-prem / hybrid), operational maturity, budget shape (capex vs opex, free-tier vs enterprise), legacy code, deployment targets, compliance posture beyond what RE captured.
- Recommend an architecture style (monolith / modular monolith / microservices / event-driven / layered / serverless / …) with a one-paragraph rationale tied to the quality-attribute drivers. Show **why**, not just **what**.
- Decompose the system into components: name, single-sentence responsibility, interfaces (with direction and protocol), dependencies, and the FR/NFR IDs each component carries.
- Pick the technology stack item by item and tie each entry to a constraint or decision. Do not introduce a technology that has no anchor in RE or in a decision you can defend.
- Iterate with the user on every significant choice. Silent generation of an architecture document is a failure mode.

`design` is the first stage that **writes to disk**. Sequence, for each of the three structured sections (decisions, components, tech-stack):

1. Create the artifact pair from templates:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section decisions
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section components
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section tech-stack
   ```
2. Fill in the Markdown body by editing only the `.md` file — never touch `.meta.yaml` with Edit/Write.
3. Update structured state through the script:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-progress <id> --completed N --total M
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link         <id> --upstream RE-QA-001
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase    <id> in_review
   ```
4. Show each draft, collect feedback, revise, and loop.

### Stage 2 — adr

Load [references/workflow/adr.md](references/workflow/adr.md).

Take every load-bearing decision from `design` and record it in Michael Nygard ADR form: **Status / Context / Decision / Consequences**. Each ADR:

- has a stable id (`AD-001`, `AD-002`, …) inside the decisions artifact
- cites RE refs in the Context section (e.g. "driven by NFR-003 and the `hard` constraint CON-002")
- includes the alternatives considered as a small comparison table
- spells out the technical trade-offs the decision creates (what becomes harder, what becomes cheaper)

In **light** mode, write ADRs only for the one or two decisions whose reversal would force a rewrite. In **heavy** mode, write one ADR per significant decision.

ADRs live inside the decisions artifact's markdown. They are not a separate section.

### Stage 3 — diagram

Load [references/workflow/diagram.md](references/workflow/diagram.md).

Create the diagrams artifact and fill it with Mermaid code:

- **C4 Context** — always, even in light mode. Shows the system as a single box and the people / external systems it interacts with.
- **C4 Container** — heavy mode only. Shows the major runtime units inside the system and how they communicate.
- **Sequence** — for the top one or two end-to-end flows that exercise the architectural drivers (e.g. the high-traffic read path, the auth flow, the async write path).
- **Data flow** — when the system has non-trivial data movement (ingest, ETL, analytics).

Every diagram lives in a fenced ` ```mermaid ` block in `<id>.md`. Add a one-paragraph caption under each diagram explaining what it is showing and which RE drivers it answers to.

### Stage 4 — review

Load [references/workflow/review.md](references/workflow/review.md).

This stage is the bridge back to RE. It does three things:

1. **Scenario validation** — turn each top-ranked quality-attribute metric into a concrete scenario and walk the design through it. "p95 < 200ms over 1M rows" becomes "user U calls /search at concurrency C against the chosen DB; does the path components-API-gateway → service → DB plausibly meet 200ms?". Use [references/scenario-validation.md](references/scenario-validation.md) for the conversion template.
2. **Constraint compliance** — every `hard` constraint must be visibly satisfied by some decision or component. Every `negotiable` constraint that was relaxed must have a recorded justification.
3. **Traceability check** — every FR / NFR must map to at least one component, every decision must cite at least one RE ref, every tech stack entry must cite a decision or a constraint. Run `validate` one more time:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate
   ```

When the user approves, move each artifact to `approved`:
```
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <id> --approver <user> --notes "..."
```

Once decisions, components, tech-stack, and diagrams are all `approved`, Arch is done. Point the user at the next skill (`impl`, `qa`, `security`, `deployment`, `operation`) and stop.

## Script contract (mandatory)

**Never edit `*.meta.yaml` files directly.** All state changes — phase, progress, approval, traceability — must go through `scripts/artifact.py`. The script enforces:

- Schema validation (rejects unknown phases, missing fields).
- `updated_at` auto-refresh.
- Legal phase transitions only (`draft → in_review → revising → in_review → approved → superseded`). You cannot jump straight from `draft` to `approved`.
- Bidirectional `upstream_refs` / `downstream_refs` integrity (so a link from `AD-001` to `RE-QA-001` shows up on both sides).
- An `approval.history` audit trail with timestamps.

Available subcommands:

| Command | Purpose |
|---------|---------|
| `artifact.py init --section <name>` | Create a metadata + markdown pair from templates. `<name>` is one of `decisions`, `components`, `tech-stack`, `diagrams`. Returns the new `artifact_id`. |
| `artifact.py set-phase <id> <phase>` | Transition phase. |
| `artifact.py set-progress <id> --completed N --total M` | Update progress. |
| `artifact.py approve <id> --approver <name> [--notes ...]` | Transition approval state. |
| `artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | Add a traceability reference. Cross-skill refs (e.g. `RE-QA-001`) are allowed. |
| `artifact.py show <id>` | Pretty-print the metadata. |
| `artifact.py list` | List all arch artifacts in the project. |
| `artifact.py validate [<id>]` | Validate schema and traceability for one or all artifacts. |

The artifact directory defaults to `./artifacts/arch/` under the user's current working directory. Override with `HARNESS_ARTIFACTS_DIR`.

## A few non-negotiables

- **RE is the source of truth for requirements.** Do not invent requirements or relitigate quality-attribute trade-offs. If RE is wrong, send the user back to RE — do not patch around it inside Arch.
- **Dialogue first.** Surface technical context before drafting. A microservices recommendation against a two-person team with no Kubernetes experience is a failure.
- **Adaptive depth.** Light mode is not lazy — it is correct sizing. Do not write nine ADRs for a CRUD app.
- **Four sections, nothing more.** Arch stops at high-level structure. Internal class design and code organisation belong to `impl`.
- **Traceability.** Every decision cites RE refs. Every component carries FR/NFR IDs. Every tech entry cites a decision or constraint. If a row has no anchor, it does not belong in the artifact yet.
- **Scripts only for metadata.** If you ever feel tempted to `Edit` a `.meta.yaml`, stop — the right answer is almost always a subcommand of `artifact.py`.
