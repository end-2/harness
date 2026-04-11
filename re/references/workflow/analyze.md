# Workflow Stage 2 — Analyze

## Role

Take the candidate set from `elicit` and stress-test it for **completeness**, **consistency**, and **feasibility**. Surface conflicts, gaps, and infeasible items. For every issue that needs a human decision, frame it as an explicit choice with consequences and bring it to the user. Do not silently pick sides.

Analyze ends when the candidate set is reconciled — every conflict has a decision, every gap has either a fix or an explicit "deferred", and every item is achievable within known constraints.

## Core capabilities

### 1. Conflict detection

Look for pairs or groups of candidates that cannot simultaneously be true:

- **Performance vs cost** — "p95 < 50ms" with "must run on the free tier"
- **Security vs usability** — "passwordless magic link" with "no external email dependency"
- **Consistency vs availability** — "always the latest data" with "works offline"
- **Scope vs timeline** — "full mobile parity" with "ship in two weeks"
- **Flexibility vs constraint** — "pluggable auth providers" with "single regulatory-approved IdP"

Present each conflict as a short paragraph: the two items, why they conflict, and what a decision would look like.

### 2. Gap detection

For every functional requirement, ask:

- What happens on the error path? What does the user see?
- What is the boundary condition? (empty, one, max)
- Is there a permission/authorization rule implied?
- Is there a data retention or deletion rule implied?
- Is there an audit or observability need?

For every quality attribute, ask:

- Is there a **measurable** target? If not, propose one and confirm.
- What scenario verifies it? (stimulus, environment, expected response)
- What is it traded against?

For every constraint, ask:

- Is the rationale explicit? A constraint without rationale is a ticking bomb.
- What is its flexibility? `hard`, `soft`, or `negotiable`?

### 3. Feasibility assessment

Check each candidate against:

- **Technical**: is there a known implementation path on the stated stack?
- **Time**: can it ship within the stated timeline?
- **Cost**: does it fit the stated budget or cost envelope?
- **Team**: does the user's team have the skills (ask if unclear)?

If something is infeasible, name the infeasibility and propose either a scope reduction, a budget/time ask, or a technology swap. Do not hide infeasibility behind a "Won't" priority.

### 4. Dependency analysis

Build a dependency view: which FR depends on which, which NFR depends on which, which candidates conflict. You do not need a full graph — a compact adjacency list is enough. Use it to:

- Order user decisions (resolve root conflicts before leaf conflicts)
- Spot chains where removing one item cascades
- Spot items that are blocked on a prior decision

### 5. Trade-off presentation

For every quality-attribute conflict, present a **choice** with consequences, not a recommendation:

> "Option A: prioritise latency (< 200ms p95). This costs us offline support, because we will require a live connection to the cache. Users in weak-signal areas will see errors.
>
> Option B: prioritise offline support. This costs us latency, because local writes will reconcile on reconnect, which can take seconds.
>
> Which matters more for the primary user base?"

The user picks. You record the decision and the rationale in the candidate set for the `spec` stage to pick up.

In **light** mode, a compact bulleted list of trade-offs is enough and you may skip the full matrix.

### 6. Issue ledger for user decisions

Keep a running list of things only the user can decide:

```
DECISIONS_NEEDED
  1. Conflict: NFR-offline vs NFR-latency. Options A/B above.
  2. Gap: no retention policy for user uploads. Default 90 days?
  3. Feasibility: "realtime collab" not shippable in 2 weeks. Cut, defer, or extend?
```

Walk the user through this list at the end of analyze. Nothing moves to `spec` until the ledger is empty (either resolved or explicitly deferred with a recorded reason).

## Interaction model

Present findings → user confirms or chooses → update candidate set → repeat until the decision ledger is empty.

## Inputs

- Candidate set from `elicit`
- Mode recommendation (light / heavy)

## Outputs of this stage

- Reconciled candidate set (no known conflicts, no known gaps, feasible)
- Quality-attribute priorities in a tentative ranking, with decisions recorded
- A short "analysis notes" scratch section to be merged into the markdown bodies during `spec`
- A list of items explicitly **deferred** with a recorded reason (these become Open Questions in the final artifact)

Still no disk writes. That starts in `spec`.

## Common anti-patterns

- **Silent tie-breaking** — picking a side on a trade-off without telling the user.
- **False completeness** — assuming the elicit candidate set was already complete.
- **Premature optimisation** — suggesting architectural fixes before the requirements are reconciled. That is `arch`'s job, not yours.
- **Matrix bloat** — building a huge trade-off matrix in light mode. A bulleted list is fine.
- **Infeasibility denial** — accepting an impossible scope because the user asked for it. Name it and propose an alternative.
