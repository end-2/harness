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

`analyze` runs as a **subagent**, so it does not talk to the user directly. It produces a **report file** that the main agent reads and walks the user through. See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full handoff protocol — the rules below are the analyze-specific slice of that contract.

Present findings (in the report) → main agent walks user → user confirms or chooses → main agent updates the candidate set for `spec` → loop if anything shifted.

## Inputs

- Candidate set from `elicit` (passed in by the main agent)
- Mode recommendation (light / heavy)
- The allocated report file path (the main agent called `artifact.py report path --kind analyze --stage analyze` before spawning this subagent)

## Report handoff (mandatory)

All findings go into the report file — **not** into the return message. Fill the frontmatter and body per the contract:

- `kind: analyze`
- `stage: analyze`
- `verdict`: `pass` (nothing to decide), `at_risk` (conflicts or gaps found), `fail` (infeasibility that blocks ship), or `n/a`
- `summary`: one line, e.g. `3 conflicts, 2 gaps, 1 infeasibility — NFR-002 blocks ship on current budget.`
- `items`: each conflict, gap, infeasibility, dependency hint, or trade-off as a single item. Use `classification ∈ {conflict, gap, infeasibility, dependency, tradeoff}`.
- `proposed_meta_ops`: usually empty — `analyze` does not write artifacts yet, so it has nothing to propose. Leave the list empty unless you want to suggest a `link` the main agent should add later during `spec`.

### Body structure

```markdown
# analyze report (re/analyze)

## Summary
One paragraph expanding on the `summary` field.

## Conflicts
Long-form explanation of each conflict with options, consequences, and the recommended decision — matching `items[]` entries with `classification: conflict`.

## Gaps
Long-form per `classification: gap` item.

## Infeasibilities
Long-form per `classification: infeasibility` item.

## Decisions needed from the user
Bullet list of the items the user must resolve before `spec` can start (mirrors the ledger below).
```

## Decision ledger

Inside the body, end with a compact ledger matching the high-severity `items`:

```
DECISIONS_NEEDED
  1. Conflict: NFR-offline vs NFR-latency. Options A/B above.
  2. Gap: no retention policy for user uploads. Default 90 days?
  3. Feasibility: "realtime collab" not shippable in 2 weeks. Cut, defer, or extend?
```

Nothing moves to `spec` until the main agent has walked the user through this ledger and every entry is either resolved or explicitly deferred with a recorded reason.

## Outputs of this stage

- A report file written to the allocated path, passing `artifact.py report validate`.
- A short return message: `report_id`, `verdict`, `summary` (and nothing else).
- No artifact `.md` or `.meta.yaml` changes. Disk writes against the artifact pairs start in `spec`.

## Common anti-patterns

- **Silent tie-breaking** — picking a side on a trade-off without telling the user.
- **False completeness** — assuming the elicit candidate set was already complete.
- **Premature optimisation** — suggesting architectural fixes before the requirements are reconciled. That is `arch`'s job, not yours.
- **Matrix bloat** — building a huge trade-off matrix in light mode. A bulleted list is fine.
- **Infeasibility denial** — accepting an impossible scope because the user asked for it. Name it and propose an alternative.
