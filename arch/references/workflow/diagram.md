# Workflow Stage 3 — Diagram

## Role

Visualise the design the user has already agreed to. `diagram` is **not** where decisions get made — by the time you enter this stage, `design` should be settled. If you find yourself wanting to change a component or a pattern while drawing, stop and have the main agent loop back to `design`.

All diagrams go into a single diagrams artifact (`ARCH-DIAG-*`) and are written as Mermaid fenced code blocks in the markdown body.

`diagram` runs as a **subagent**. It does **not** `init` the diagrams artifact, `link` it, or change its phase — those are the main agent's responsibility. The subagent writes the diagram markdown into a `diagram-draft` report file; the main agent then:

1. runs `artifact.py init --section diagrams` (if no diagrams artifact exists yet),
2. pastes the report body into `ARCH-DIAG-*.md`,
3. applies the `proposed_meta_ops` from the report frontmatter (`link` to components and tech-stack, `set-phase` to `in_review`).

See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full handoff protocol.

## Which diagrams to produce

| Diagram | Light mode | Heavy mode | Purpose |
|---------|-----------|-----------|---------|
| **C4 Context** | ✅ always | ✅ always | Shows the system as a single box and the people / external systems around it. Answers "where does this thing live in the world?" |
| **C4 Container** | ❌ skip | ✅ always | Shows the major runtime units inside the system and how they talk. Answers "what are the moving parts?" |
| **Sequence** | ✅ one for the primary flow | ✅ one per top end-to-end flow | Shows how components collaborate across time for a given flow. Answers "how does request X actually run?" |
| **Data flow** | Only if data movement is non-trivial | Only if data movement is non-trivial | Shows where data comes from, where it lives, and where it goes. Answers "what happens to the data?" |

Do not draw diagrams that do not answer a question. An extra diagram that nobody will read is waste.

## C4 Context

- The system is a single box in the middle.
- Put users (personae) on the left and external systems (upstream feeds, third-party APIs, payment providers, auth providers, mail, SMS) around the outside.
- Every relationship has a verb and a technology: `uses [HTTPS]`, `publishes to [webhook]`, `pulls metrics from [OTel]`.

Caption this diagram with the RE drivers it answers to — usually the primary users from `RE-REQ` and any `environmental` constraints from `RE-CON`.

## C4 Container (heavy mode)

- One container per major runtime unit from the components artifact. Databases, caches, and queues are separate containers.
- Labels: name, framework / runtime, one-line responsibility.
- Every relationship gets a protocol (`HTTPS/JSON`, `gRPC`, `Kafka`, `SQL over TLS`).
- If the picture does not fit on a laptop screen, it is too big — collapse similar containers.

Caption this diagram with the decisions it materialises. "This container view implements AD-001 (modular monolith with a separate read replica)" is a useful caption.

## Sequence

- Pick the flow that **exercises the top-ranked quality-attribute driver**. If performance is rank 1, draw the hot read path. If availability is rank 1, draw the failover path. If security is rank 1, draw the auth path.
- Keep it under ten actors and under fifteen messages. A wall of `->>` arrows is not a diagram.
- Annotate the critical hop (the one the driver cares about) with a note: `Note right of DB: target < 150ms` makes the scenario visible in the picture.

Caption with the RE ref and the target metric: "Validates NFR-003 p95 < 200ms". This caption is the link the `review` stage uses.

## Data flow

Use a Mermaid `flowchart` when the system moves data in a non-trivial way — ingest pipelines, analytics, ETL, event buses with multiple consumers. A simple HTTP-to-DB round trip does not need a DFD; the sequence diagram already tells that story.

## Captions are part of the diagram

Every code block gets a caption paragraph below it. The caption has two jobs:

1. Say what the diagram shows (what a reader who did not ask for it should understand).
2. Say which RE drivers or decisions it answers to (so `review` can tie the picture back to the requirements).

A diagram without a caption is ambiguous, and ambiguous diagrams get misread.

## Report handoff (mandatory)

- `kind: diagram-draft`
- `stage: diagram`
- `target_refs`: the diagrams artifact ID (after the main agent has allocated it), or an empty list with `scope: diagrams-draft` when the diagrams artifact does not exist yet
- `verdict`: `pass` when the drafts are ready to merge
- `summary`: one line, e.g. `Context + Container + 1 sequence (hot read path, NFR-003) drafted.`
- `items`: one entry per produced diagram, `classification: diagram_drafted`; use `caption_missing` or `driver_untraced` for any diagram you cannot finish.
- `proposed_meta_ops`: the `link` operations the main agent should apply (`--upstream` to the components artifact and the tech-stack artifact), and optionally `set-phase <diagrams-id> in_review`.

### Body structure

The body **is** the markdown the main agent will paste into `ARCH-DIAG-*.md`. Structure it so each diagram is self-contained:

```markdown
# diagram-draft report (arch/diagram)

## Summary
One paragraph expanding on the `summary` field.

## C4 Context

```mermaid
C4Context
title System Context
...
```

*Shows ... and answers to RE-REQ (primary users) and CON-001 (environmental).*

## C4 Container (heavy mode only)
...

## Sequence — primary read path

```mermaid
sequenceDiagram
...
```

*Validates NFR-003 p95 < 200ms.*
```

## Outputs of this stage

- A report file written to the allocated path, passing `artifact.py report validate`, with every required diagram in the body.
- A short return message: `report_id`, `verdict`, `summary`.
- The main agent applies the body to `ARCH-DIAG-*.md` and runs the proposed meta ops (`link` + `set-phase in_review`).

## Common anti-patterns

- **Drawing to decide**. Diagrams record decisions; they do not make them. If you catch yourself debating a component while drawing, you belong in `design`.
- **Missing captions**. The picture is not self-explanatory, no matter how clean the Mermaid looks.
- **Diagrams that duplicate each other**. A Context diagram and a Container diagram should show different information, not the same thing at different zoom levels without new content.
- **Sequence diagrams that exercise nothing**. Pick a flow that tests a driver; avoid "here is a generic CRUD request".
