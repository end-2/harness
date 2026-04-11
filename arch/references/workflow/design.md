# Workflow Stage 1 — Design

## Role

Turn the three RE artifacts (`RE-REQ-*`, `RE-CON-*`, `RE-QA-*`) plus the technical context you gather from the user into three persisted arch artifacts: **Architecture Decisions**, **Component Structure**, and **Technology Stack**. This is the first stage that writes to disk.

`design` owns the hard work. `adr`, `diagram`, and `review` are refinements and checks on what `design` produces.

## Before you write anything

Read the RE artifacts first. Specifically:

1. **Top-ranked quality attributes** (`RE-QA-*`, rank order) → these are your **architectural drivers**. The top-3 shape pattern choice. Do not rank them again; RE already did.
2. **`hard` constraints** (`RE-CON-*` with `flexibility: hard`) → non-negotiable. Any decision that violates one is dead on arrival.
3. **Non-functional requirements with measurable metrics** (`RE-REQ-*` NFRs) → these turn into scenarios in the `review` stage, so you need to keep them in mind while designing.
4. **Functional requirements and their `dependencies`** → the FR dependency graph is the first sketch of the component graph.

If any of those artifacts are missing, in `draft`, or in `in_review`, stop. Arch must not run on unstable input. Send the user back to `re` and explain what is missing.

## Technical context dialogue

RE deliberately omits technical context. You cannot pick a pattern or a stack without it. Before drafting, get answers to at least these:

- **Team**: how many engineers, what languages they know, how comfortable they are with distributed systems, cloud, infrastructure-as-code.
- **Existing infrastructure**: is there a cloud account already? A legacy codebase? A Kubernetes cluster? A DBA team?
- **Operational maturity**: who is on call? Is there an SRE practice? How mature is observability?
- **Budget shape**: rough cost envelope, capex vs opex, free-tier vs enterprise tolerance.
- **Deployment targets**: cloud only, on-prem, hybrid, air-gapped, mobile, embedded.
- **Compliance posture beyond RE**: any auditor, customer, or regulator who gets a say that was not captured in RE.

Batch these questions. Do not ask one at a time, and do not ask all twenty at once. Usually three to five targeted questions are enough to unblock the next decision.

## Mode selection

At the start of `design`, pick **light** or **heavy** based on RE's output density (see `references/adaptive-depth.md`) and tell the user which one you chose and why. The user may override.

## The three drafts

Work one section at a time. Finish decisions before components, finish components before tech-stack. This is not bureaucracy — each section feeds the next, and doing them in parallel creates contradictions you will have to fix anyway.

### Decisions draft

1. For each architectural driver (top quality attribute), pick a pattern and name it explicitly. "Read-heavy, low-latency, single region" → "CQRS read path with a read replica" or "cache-aside with Redis in front of Postgres".
2. Write one decision entry per load-bearing choice: architecture style, persistence strategy, communication style (sync vs async), deployment shape.
3. Every decision cites `re_refs`. If a decision has no RE anchor, you are either inventing a requirement or the RE artifact missed one — stop and check.
4. List the alternatives considered honestly. Two good alternatives per decision is usually the right amount; listing every possibility is noise.

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section decisions
# fill in the .md
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-progress <id> --completed 0 --total <n>
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link         <id> --upstream RE-QA-001
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase    <id> in_review
```

### Components draft

1. Start from the decisions. A "CQRS read path" implies a write service, a read service, a projection builder, and a read store. Name them.
2. Every component has a **single-sentence responsibility**. If you cannot fit it in one sentence, it is probably two components.
3. Every component carries at least one FR or NFR in its `re_refs`. If nothing maps to it, it should not exist yet.
4. Every component lists its **interfaces** with direction (inbound/outbound) and protocol. This is what `impl` and `qa` consume.
5. Dependencies are component-to-component only. "Depends on Postgres" is not a dependency — Postgres appears as a component (`type: store`) or as a line item in the tech stack.

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section components
# fill in the .md, then:
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link <id> --upstream <decisions-id>
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
```

### Tech-stack draft

1. Walk the stack categories (language, framework, database, messaging, infra, observability, auth) and pick one per category — or explicitly mark it as "none" with a reason.
2. Every row cites either a `decision_ref` (AD-NNN) or a `constraint_ref` (CON-NNN), or both. If you cannot cite either, you do not have a reason to pick that technology yet.
3. Prefer boring technology when the quality-attribute drivers allow it. Novel technology is justified by a specific constraint or driver, not by preference.
4. Do not invent operational requirements that contradict the user's stated operational maturity. If the team has never run Kafka, picking Kafka is a decision you must surface to the user with eyes open, not a silent assumption.

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section tech-stack
# fill in the .md, then:
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link <id> --upstream <decisions-id>
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
```

## Iteration with the user

Show each draft when it is done. Ask for specific feedback, not "what do you think?". Good prompts:

- "I picked a modular monolith over microservices because your team is three people and your deploy target is a single VPS. Does that match reality?"
- "I put the analytics path on a separate read replica. Is nightly lag acceptable, or do you need the dashboard to be near-real-time?"
- "Postgres vs DynamoDB: I picked Postgres because the query patterns in FR-004 and FR-007 are relational. Agree?"

Revise and loop until the user is happy with that section. Then move on.

## Outputs of this stage

Three artifact pairs on disk, all in phase `in_review`, with:

- markdown bodies filled
- `progress` reflecting completion
- `upstream_refs` pointing at the relevant RE artifacts and (for components/tech-stack) at the decisions artifact
- empty `downstream_refs` — those are populated when `diagram` and `review` cross-link

## Common anti-patterns

- **Designing before reading RE**. You will pick the wrong drivers and re-debate trade-offs RE already closed.
- **Skipping the technical context dialogue**. The result is an architecture that looks good on paper and fails in contact with the team.
- **Writing decisions without `re_refs`**. Decisions without an anchor are preferences; they will not survive review.
- **Picking technology to pick technology**. Every row in the stack needs an anchor.
- **Editing `*.meta.yaml` directly**. Use `artifact.py`. Always.
