# Workflow Stage 2 — ADR

## Role

Take every load-bearing decision from `design` and record it as an Architecture Decision Record (Michael Nygard form) inside the decisions artifact's markdown. ADRs are not a separate artifact — they live in `ARCH-DEC-*.md` under the "Architecture Decision Records" section.

An ADR exists so that, six months from now, a new engineer looking at the codebase can answer "why is it like this?" without a meeting. That means it has to capture the **forces** at play (what RE items pushed the decision), the **alternatives** that were tossed, and the **consequences** that the decision creates. Without those three, it is not an ADR, it is a note.

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

Every ADR populates the `architecture_decisions[].re_refs` field in the structured YAML mirror of the decisions artifact. You may edit that list directly inside `*.meta.yaml`? — **no**. Use the markdown as the source of truth during iteration, and only bring it into the structured block when `review` finalises the section. For any state change (`phase`, `progress`, `approval`), use `artifact.py`.

If a new ADR depends on an existing one, or supersedes one, add a cross-ref with `link`:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link <decisions-id> --upstream <other-decisions-id>
```

## Outputs of this stage

- The decisions artifact's markdown has an ADR section populated.
- Each ADR cites RE refs in its Context.
- The decision summary table at the top is consistent with the ADR bodies.
- Status of each ADR is `Proposed` (still in `in_review` until the `review` stage).

## Common anti-patterns

- **ADRs without Context**. Without the forces, the decision is unfalsifiable.
- **ADRs with generic pros/cons**. "Postgres is mature and widely supported" is not rationale, it is a commercial.
- **Too many ADRs**. One per load-bearing decision, not one per opinion.
- **Deleting old ADRs on change**. Supersede, do not delete. The audit trail is the point.
