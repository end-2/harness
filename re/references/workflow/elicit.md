# Workflow Stage 1 — Elicit

## Role

Turn the user's natural-language request into a structured set of **candidates**: candidate functional requirements, candidate non-functional requirements, candidate constraints, candidate quality attributes, and a list of open questions. Nothing is persisted to disk yet — this stage is entirely a working-memory pass.

You are not a passive transcriber. A user who can write "build me X" in one line almost always has unspoken assumptions, unstated scope boundaries, and missing success criteria. Your job is to surface those gaps *proactively*, in a way that feels like a productive conversation rather than a form.

## Core capabilities

### 1. Ambiguity detection

Read `$ARGUMENTS` and name the things it does *not* say. Categories to check:

- **Target user** — who uses this? one role or many?
- **Scope boundary** — what is explicitly out of scope? ("just the API, not a UI")
- **Success criteria** — how will the user know it works? what do they measure?
- **Performance expectations** — latency, throughput, concurrent users, data volume
- **Data model** — what data exists, where it comes from, who owns it
- **Regulatory / legal context** — PII, HIPAA, GDPR, SOC2, payment data
- **Operational context** — who runs it, where it is deployed, what the uptime expectation is
- **Failure behavior** — what happens on partial failures, what the user sees, how recovery works
- **Existing systems** — what it must integrate with, and what is allowed to change

For each category, classify what `$ARGUMENTS` told you: *confirmed*, *implied*, or *missing*. Focus questions on missing first, then implied.

### 2. Adaptive question strategy

The question depth should match the request's specificity:

| Input type | Example | Strategy |
|------------|---------|----------|
| **High-level** | "build a shopping mall" | broad exploratory questions on scope, users, MVP boundary |
| **Mid-level** | "OAuth2 login with GitHub and Google" | targeted detail questions on flows, token lifetime, session model |
| **Detailed** | multi-paragraph spec | edge cases, error handling, failure modes, boundary conditions |

Ask in **batches**, not one-at-a-time. A good batch is 3–7 related questions the user can answer in one pass. Group them with a short heading so the user understands *why* you are asking.

Do not ask for everything at once either. If you dump 30 questions on a user, they will answer the easy ones and ignore the hard ones. Prioritise questions by decision impact: a question whose answer changes the architecture is worth more than a question whose answer changes a label.

### 3. Progressive refinement

Each conversational turn should leave the candidate list more specific than before. Track two lists in your working memory:

```
CONFIRMED  — items the user has explicitly agreed to, or directly stated
OPEN       — items still ambiguous, contingent, or unasked
```

When you generate the next batch of questions, pull from OPEN only. Never re-ask a CONFIRMED item. If the user walks back an answer, move the item from CONFIRMED back to OPEN and record why.

### 4. Stakeholder perspective taking

The user in the chat window is one stakeholder. Real projects have many. Ask questions *as if* you were:

- **The end user**: "Is there a first-time experience or does the user land straight in the main view?"
- **The operator**: "Who will be on-call, and what do they need to see when something breaks?"
- **A security reviewer**: "What is the blast radius if an account is compromised?"
- **A support rep**: "How do you tell a user why their upload failed?"

You do not need to literally role-play; just make sure these perspectives each got a question.

### 5. Confirmation and summarisation

Every few turns, show the user a compact summary:

> **Here is what I have so far**
> - FR candidates: …
> - NFR candidates: …
> - Constraints: …
> - Quality attributes (unranked): …
> - Still open: …

Ask them to confirm or correct. This prevents drift and gives the user a clear "we are done" moment.

### 6. Knowing when to exit

Exit `elicit` when any of these are true:

- The user says "that's enough" or equivalent.
- You have a confirmed candidate set that is *internally consistent* and another question would feel like padding.
- You hit the edge of your judgment and need `analyze` to break a tie.

Before leaving, classify the run as **light** or **heavy** (see `references/adaptive-depth.md`) and tell the user which mode you are choosing and why.

## Interaction model

Multi-turn. The user is in the loop. Silent generation of requirements from a one-line prompt is a failure mode.

## Inputs

- `$ARGUMENTS` — the user's initial prompt.
- Any prior artifacts already in the project (check `artifact.py list`).

## Outputs of this stage

Held only in working memory and surfaced to the user as summaries:

- Candidate FR list (each with tentative ID, title, priority hint, rough acceptance criterion)
- Candidate NFR list (each with category, title, tentative metric)
- Candidate constraints (with type and rationale)
- Candidate quality attributes (unranked is fine; ranking happens in `analyze`)
- Open questions list — what remains undecided
- A provisional **mode** recommendation (light / heavy)

Nothing goes to disk yet. Disk writes start in `spec`.

## Common anti-patterns

- **Silent generation** — producing a full SRS from a one-line prompt. If you catch yourself doing this, stop and ask questions.
- **Single-question pestering** — one question per turn, dragging the conversation out. Batch.
- **Unbounded interview** — asking every question from every perspective. Prioritise.
- **Mode inflation** — treating every request as heavy. A single feature does not need IEEE 830.
- **Premature specification** — writing FR-001 with acceptance criteria before the user has even confirmed scope.
