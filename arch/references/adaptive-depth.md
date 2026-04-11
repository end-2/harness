# Adaptive Depth

Arch's output depth follows RE's output density. The goal is to size the artifact to the problem, not to ceremony.

## Mode decision

Inspect the RE artifacts at the start of `design`.

| Metric | Light mode | Heavy mode |
|--------|-----------|-----------|
| Functional requirements | ≤ 5 | > 5 |
| Non-functional requirements | ≤ 2 | > 2 |
| Ranked quality attributes | ≤ 3 | > 3 |

**Light mode** triggers only if **all three** metrics are within the light bounds. If *any* is over, use heavy mode. The user may override in either direction — and should, if they have a strong reason.

## What changes between modes

### `design` stage

|  | Light | Heavy |
|--|-------|-------|
| Architecture style | Recommended + one-paragraph rationale | Recommended + rationale + at least one credible alternative discussed |
| Component decomposition | Shallow (typically 3–5 components) | Deep (as many as the system requires, with interfaces fully specified) |
| Tech stack | Language, framework, primary store, deploy target | Full stack including messaging, observability, auth, cache, secrets, CI/CD target |
| Technical context dialogue | 3–5 questions | 5–10 questions |

### `adr` stage

|  | Light | Heavy |
|--|-------|-------|
| Number of ADRs | 1–2, only for the truly load-bearing decisions | One per significant decision, typically 5–12 |
| ADR depth | Status / Context / Decision / Consequences, short | Same form, but Context and Consequences are more thorough, and an Alternatives table is always present |

### `diagram` stage

|  | Light | Heavy |
|--|-------|-------|
| C4 Context | ✅ always | ✅ always |
| C4 Container | ❌ skip | ✅ always |
| Sequence | One for the primary flow | One per top end-to-end flow |
| Data flow | Only if data movement is non-trivial | Only if data movement is non-trivial |

### `review` stage

|  | Light | Heavy |
|--|-------|-------|
| Scenario validation | One scenario per top-3 quality attribute | One scenario per top-3 quality attribute plus stress/failure scenarios |
| Constraint compliance | Every `hard` constraint verified | Every `hard` constraint verified, every relaxed `negotiable` justified |
| Traceability | Script validate + spot check | Script validate + full walkthrough |

## When to switch mid-flight

If you started in light mode and realise the problem has grown (new NFRs surface during design, or the user adds a major requirement), switch to heavy mode. Tell the user you are switching and why, and re-open the sections you already drafted to fill in the heavy-mode content.

Downgrading from heavy to light is rarely right. If you catch yourself wanting to skip ADRs or diagrams, the better move is to make them smaller, not to skip them.

## Do not confuse "light" with "lazy"

Light mode is **correctly sized**, not abbreviated. Every RE ref must still map. Every decision must still cite a driver. Every component must still carry an FR/NFR. The difference is the number of things, not the rigour of each thing.
