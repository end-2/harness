# Workflow Stage 3 — Diagram

## Role

Visualise the design the user has already agreed to. `diagram` is **not** where decisions get made — by the time you enter this stage, `design` should be settled. If you find yourself wanting to change a component or a pattern while drawing, stop and loop back to `design`.

All diagrams go into a single diagrams artifact (`ARCH-DIAG-*`) and are written as Mermaid fenced code blocks in the markdown body.

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section diagrams
# fill in the .md, then:
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link <id> --upstream <components-id>
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link <id> --upstream <tech-stack-id>
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
```

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

## Outputs of this stage

- Diagrams artifact in `in_review`, `upstream_refs` pointing at the components and tech-stack artifacts.
- Every required diagram (per mode) present.
- Every diagram captioned with both "what it shows" and "which driver/decision it answers to".

## Common anti-patterns

- **Drawing to decide**. Diagrams record decisions; they do not make them. If you catch yourself debating a component while drawing, you belong in `design`.
- **Missing captions**. The picture is not self-explanatory, no matter how clean the Mermaid looks.
- **Diagrams that duplicate each other**. A Context diagram and a Container diagram should show different information, not the same thing at different zoom levels without new content.
- **Sequence diagrams that exercise nothing**. Pick a flow that tests a driver; avoid "here is a generic CRUD request".
