# Workflow Stage 4 — Review

## Role

Validate the `design` output against the RE artifacts as concrete scenarios, verify constraint compliance, check traceability, and get explicit user approval on the full set of arch artifacts.

`review` is a compressed ATAM. Traditional ATAM takes days and a room full of stakeholders. Here you have RE as the stakeholder proxy and the user as the tie-breaker, and the quality attributes are already ranked — you are doing scenario walkthroughs, not workshops.

## Three checks

### 1. Scenario validation (RE metric → walkthrough)

For each top-ranked quality attribute in `RE-QA-*`, turn its metric into a concrete scenario and walk the design through it. Use the template in [../scenario-validation.md](../scenario-validation.md).

Example:

- RE metric: `NFR-003 — p95 response time < 200ms for /search over 1M rows`
- Scenario: "A single user calls `/search?q=foo` during normal load (~200 rps) against the configured Postgres read replica. Does the path API Gateway → Search Service → Postgres read replica plausibly complete within 200ms?"
- Walkthrough: count hops, identify the slow one (usually the DB query), check if the tech stack choice (index strategy, connection pool) and the component layout (read replica vs primary) support the target.
- Verdict: `pass` / `at risk` / `fail`, with the reason named.

Do this for **every top-ranked quality attribute**. In light mode, one scenario per top-3 attribute is fine. In heavy mode, add stress scenarios (peak load, failure, degraded dependency).

Failing scenarios are not silent: surface them to the user, explain what would need to change to pass, and loop back to `design` if the user decides to adjust.

### 2. Constraint compliance

Walk every `hard` constraint in `RE-CON-*` and point at the decision or component that satisfies it. "CON-002: must run on the existing AWS account → satisfied by AD-004 (AWS ECS Fargate) and the infra row in ARCH-TECH-001". If a hard constraint has no satisfier, the review fails.

For `negotiable` constraints that were relaxed, record a one-line justification. "CON-005 (budget ≤ $500/mo) was relaxed to ~$650/mo because of the DR replica requirement; confirmed with user on 2026-04-11".

### 3. Traceability

Run the script:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate
```

Then verify by hand:

- Every FR and NFR from `RE-REQ-*` maps to at least one component (`ARCH-COMP-*.components[].re_refs`).
- Every architecture decision in `ARCH-DEC-*` cites at least one RE ref.
- Every entry in the tech stack cites either a decision ref or a constraint ref.
- Every diagram caption names the driver/decision it answers to.

Holes here are almost always a sign that either RE is incomplete (send the user back) or `design` skipped a requirement (loop back to `design`).

## Presenting the review to the user

Structure the review report as four sections:

1. **Scenarios** — one line per scenario: "Scenario / verdict / reason".
2. **Constraints** — one line per hard constraint: "constraint / satisfied by".
3. **Traceability** — "X FRs mapped, Y NFRs mapped, Z decisions cited, W diagrams captioned". Any gaps listed.
4. **Risks and open items** — anything the user must explicitly accept before approval. This is the important section.

Do not approve silently. Wait for the user to say "go ahead" (or equivalent) before transitioning. When they approve:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve ARCH-DEC-001  --approver <user> --notes "..."
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve ARCH-COMP-001 --approver <user> --notes "..."
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve ARCH-TECH-001 --approver <user> --notes "..."
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve ARCH-DIAG-001 --approver <user> --notes "..."
```

Each approval requires the artifact to already be in `in_review`. If any is still in `draft`, move it to `in_review` first — or, more likely, loop back and finish it.

## When review fails

- **A scenario fails under load** → loop to `design` and revisit pattern / tech choice.
- **A hard constraint is not satisfied** → loop to `design` and add a satisfier.
- **Traceability hole on a FR** → loop to `design` and assign the FR to a component. If no component fits, you are missing a component.
- **Traceability hole on an NFR** → the NFR is not being addressed. Either add a decision that addresses it, or loop back to RE because the NFR is untestable as stated.

Never paper over a review failure with wording. The whole point of this stage is to surface things.

## Outputs of this stage

All four artifacts in phase `approved`, linked, and with a clean `validate` run. Handoff message to the user pointing at the next skills:

- `impl` — now has components, tech stack, and decisions to generate from.
- `qa` — has NFR metrics mapped to components to derive test strategy.
- `security` — has decisions and tech-stack rows for threat modeling.
- `deployment` — has infra rows and constraints to plan deployment.
- `operation` — has quality-attribute metrics to turn into SLOs.

## Common anti-patterns

- **Approving before scenarios pass**. An arch that fails its own review is not "done, with caveats" — it is not done.
- **Silent approval**. The user must say yes. You do not transition on their behalf.
- **Rewording instead of fixing**. If a scenario fails, change the design, not the description.
