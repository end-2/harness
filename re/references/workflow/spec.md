# Workflow Stage 3 — Spec

## Role

Turn the reconciled candidate set from `analyze` into **three persisted artifacts** — one per section — in a form that downstream skills can consume directly. This is the first stage that writes to disk.

The output of `spec` is three paired files per section:

- `RE-REQ-<n>.meta.yaml` + `RE-REQ-<n>.md`
- `RE-CON-<n>.meta.yaml` + `RE-CON-<n>.md`
- `RE-QA-<n>.meta.yaml`  + `RE-QA-<n>.md`

Metadata goes **only** through `scripts/artifact.py`. Markdown bodies are edited in place, inside the scaffolding the templates provide.

## Sequence per section

Follow this exact sequence for each of the three sections. Do them one section at a time — finish requirements before starting constraints, finish constraints before starting quality attributes. This makes iteration cheaper and keeps traceability linear.

### Step 1 — init

```bash
python ${SKILL_DIR}/scripts/artifact.py init --section requirements
```

This copies the template pair into the artifact directory and assigns an `artifact_id`. Capture the returned id; you will reuse it in every subsequent command for this section.

### Step 2 — draft the markdown

Open the generated `*.md` file and fill in the tables. Use the IDs you reserved during `analyze`. Every row must satisfy:

- **Specific**: a human on another team can understand it without asking
- **Measurable**: an acceptance criterion exists that can be objectively checked
- **Achievable**: you already confirmed feasibility in `analyze`
- **Relevant**: it maps to something the user actually cares about
- **Testable**: `qa` can derive at least one test from it

For NFRs, the acceptance criterion must be a number with a unit, not an adjective. "< 200ms p95 over 1M rows" is acceptable. "fast" is not.

### Step 3 — update structured state via script

Once the markdown table has real rows, record progress and traceability:

```bash
python ${SKILL_DIR}/scripts/artifact.py set-progress <id> --completed 0 --total <row-count>
python ${SKILL_DIR}/scripts/artifact.py link         <id> --upstream "user-prompt:$ARGUMENTS"
```

As the user confirms items, bump `--completed`. This gives both you and the user a visible progress signal.

**Important**: structured fields inside the `.meta.yaml` (`functional_requirements`, `non_functional_requirements`, `constraints`, `quality_attributes`) are the machine-readable mirror of the markdown tables. In the current script these fields are seeded by `init` but not automatically kept in sync with the markdown. When you need to update them, you may edit the structured lists *only*; never edit `phase`, `progress`, `approval`, `upstream_refs`, `downstream_refs`, `document_path`, `updated_at`, or any other field the script manages. If you are unsure, treat the entire file as off-limits and do everything through `artifact.py`.

### Step 4 — present to user, iterate

Show the draft. Ask for specific feedback: "anything wrong with FR-003?", "is the p95 target of 200ms actually what you meant, or looser?". Revise. Loop until the user is happy with *that section*.

### Step 5 — transition to in_review

```bash
python ${SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
```

This marks the section as awaiting review. Keep it in `in_review` until the `review` stage approves it.

## Section-specific notes

### Requirements Specification

- FR IDs are `FR-NNN`, NFR IDs are `NFR-NNN`. Zero-padded, sequential.
- Use **MoSCoW** priorities (`Must`, `Should`, `Could`, `Won't`). Every "Must" is a commitment — be sure.
- Every row has at least one **acceptance criterion**. Multiple are fine; format as a bullet list inside the cell.
- Capture dependencies between FRs using the `Dependencies` column — this feeds `arch` and `impl` later.

### Constraints

- Constraint IDs are `CON-NNN`.
- Use four types: `technical`, `business`, `regulatory`, `environmental`.
- Every constraint must have a **rationale** ("why is this here?") and an **impact** ("what breaks if we violate it?"). A constraint without a rationale is an accident waiting to happen.
- `flexibility` is `hard` for legal/contractual items, `soft` for strong preferences, `negotiable` for anything the user said "probably" about.

### Quality Attribute Priorities

- Pick at most 5–6 attributes. A ranking with 20 entries is not a ranking.
- Rank 1 is the top priority. Downstream `arch` reads rank order directly to pick drivers.
- Every attribute must have a **measurable metric** — a unit, a number, a scenario. "Fast" and "scalable" are rejected.
- The `trade_off_notes` column is non-optional. Write what *lower-ranked* attributes are sacrificed when this one is enforced.

## Adaptive depth

- **Light mode**: keep tables short. User Story + one or two acceptance criteria per FR is enough. Skip the scenarios section of the quality-attribute template if you cannot think of a meaningful scenario.
- **Heavy mode**: fill every section of every template. Include scenarios for at least the top 3 quality attributes. Use the structured YAML lists as the machine-readable mirror of the markdown tables so `arch` and `qa` can parse without re-scanning the prose.

Full rules: `references/adaptive-depth.md`.

## Outputs of this stage

Three artifact pairs on disk, all in phase `in_review`, with:

- markdown tables filled
- `progress` reflecting completion
- `upstream_refs` pointing at the user prompt (and any prior RE artifacts in the project)
- empty `downstream_refs` (those are populated by downstream skills or by `review` when you cross-link artifacts)

## Common anti-patterns

- **Editing `*.meta.yaml` directly** — the skill contract forbids this. Use `artifact.py`.
- **Drafting all three sections in parallel** — iteration gets tangled. Finish one, then the next.
- **Skipping measurable targets** — "fast", "secure", "scalable" as NFR values. Rejected at review.
- **Re-deriving decisions from analyze** — trust the reconciled candidate set. If you disagree with it, loop back to `analyze`, don't re-debate in `spec`.
- **Over-annotating** — filling every cell with prose. Tables are tables.
