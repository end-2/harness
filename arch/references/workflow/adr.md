# Workflow Stage 2 — ADR

## Role

Take every load-bearing decision from `design` and draft it as an Architecture Decision Record (Michael Nygard form) that the main agent will merge into `ARCH-DEC-*.md`. ADRs are not a separate artifact — once merged, they live in `ARCH-DEC-*.md` under the "Architecture Decision Records" section.

An ADR exists so that, six months from now, a new engineer looking at the codebase can answer "why is it like this?" without a meeting. That means it has to capture the **forces** at play (what RE items pushed the decision), the **alternatives** that were tossed, and the **consequences** that the decision creates. Without those three, it is not an ADR, it is a note.

`adr` runs as a **subagent**. It does **not** edit `ARCH-DEC-*.md` directly. Instead, it writes the ADR markdown blocks into an `adr-draft` report file; the main agent reads the report and applies the blocks to the decisions artifact via `Edit`. See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full handoff protocol.

## Which decisions deserve an ADR

Not every choice is ADR-worthy. Use this test:

> If we reversed this decision, would we have to rewrite or re-deploy something substantial?

If yes, write an ADR. If no, leave it in the decisions summary table with a one-line rationale and move on.

- **Light mode**: one or two ADRs for the truly load-bearing decisions (the architecture style, usually the persistence strategy). That is enough.
- **Heavy mode**: one ADR per significant decision. Usually that lands between five and twelve ADRs for a medium system.

Err on the side of fewer, fatter ADRs. Nine thin ADRs for a CRUD app is noise.

## The four Nygard fields

### Status

One of `Proposed`, `Accepted`, `Deprecated`, `Superseded by AD-NNN`. While `design` iterates, status is `Proposed`. It moves to `Accepted` after `review` closes. If a later iteration replaces a decision, mark the old one `Superseded by AD-<new>` and do not delete it — the history is the whole point.

### Context

The forces. Cite RE refs explicitly.

> Driven by NFR-003 (p95 < 200ms for /search over 1M rows) and the top-ranked quality attribute RE-QA-001 (performance, rank 1). The constraint CON-002 (must run on the existing AWS account, no Kubernetes) rules out self-hosted data planes. The team has strong Python experience and no Go experience (technical context, captured in design dialogue 2026-04-11).

Bad context is generic: "We need a fast system." Good context names the forces and points at where they came from.

### Decision

The chosen option, in one paragraph, in plain language. No hedging. If you need to hedge, the decision is not ready.

### Consequences

Honest list of **positive**, **negative**, and **risks**. A decision with only upsides is a decision that has not been thought through.

- **Positive**: what gets easier or cheaper because of this decision.
- **Negative**: what gets harder, what you give up.
- **Risks**: what could go wrong later, especially under load, under failure, or under a future requirement change.

## Alternatives table

Below the four Nygard fields, include a small comparison table of the alternatives that were seriously considered. Two to four rows is right; ten rows means most of them were not serious.

| Alternative | Pros | Cons | Why rejected |
|-------------|------|------|--------------|
| ... | ... | ... | ... |

The `Why rejected` column is the one that matters. Future readers will want to know why the thing they are now tempted by was passed over.

## Traceability

Every ADR populates the `architecture_decisions[].re_refs` field in the structured YAML mirror of the decisions artifact. You may edit that list directly inside `*.meta.yaml`? — **no**. The subagent does not touch metadata at all; it emits `proposed_meta_ops` (e.g. `link` suggestions) in the report frontmatter, and the main agent applies them via `artifact.py link`.

If a new ADR depends on an existing one, or supersedes one, record the cross-ref as a proposed meta op:

```yaml
proposed_meta_ops:
  - cmd: link
    artifact_id: ARCH-DEC-001     # the decisions artifact
    upstream: ARCH-DEC-002         # another decisions artifact it depends on
```

## Report handoff (mandatory)

- `kind: adr-draft`
- `stage: adr`
- `target_refs`: the decisions artifact ID the ADRs will be merged into
- `verdict`: `pass` when the draft is ready to merge; `at_risk` when you need the user to confirm an ambiguous context before merging
- `summary`: one line, e.g. `3 ADRs drafted — AD-001 (modular monolith), AD-002 (Postgres), AD-003 (Redis read-through).`
- `items`: one entry per ADR, `classification: adr_drafted`; use `classification: context_missing | alternatives_missing | consequences_missing` for the rare case where you cannot finish an ADR and need to flag it back.

### Body structure

The body **is** the ADR markdown the main agent will paste into `ARCH-DEC-*.md`. Structure it so the main agent can copy entire blocks:

```markdown
# adr-draft report (arch/adr)

## Summary
One paragraph expanding on the `summary` field.

## ADRs to merge into ARCH-DEC-001.md

### AD-001 — Modular monolith with a separate read replica

**Status:** Proposed
**Context:** Driven by NFR-003 ... (forces, RE refs).
**Decision:** ...
**Consequences:**
- Positive: ...
- Negative: ...
- Risks: ...

**Alternatives considered**

| Alternative | Pros | Cons | Why rejected |
| ... | ... | ... | ... |

### AD-002 — ...
```

Each ADR is a self-contained block so the main agent can either paste the whole section or copy AD-NNN entries individually.

## Outputs of this stage

- A report file written to the allocated path, passing `artifact.py report validate`, with the ADR markdown blocks in the body.
- A short return message: `report_id`, `verdict`, `summary`.
- No writes to `ARCH-DEC-*.md` or its metadata — the main agent merges the body into the artifact and, if needed, applies the `proposed_meta_ops`.

## Common anti-patterns

- **ADRs without Context**. Without the forces, the decision is unfalsifiable.
- **ADRs with generic pros/cons**. "Postgres is mature and widely supported" is not rationale, it is a commercial.
- **Too many ADRs**. One per load-bearing decision, not one per opinion.
- **Deleting old ADRs on change**. Supersede, do not delete. The audit trail is the point.
