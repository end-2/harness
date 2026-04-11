# Adaptive Depth — Light vs Heavy Mode

RE runs in one of two modes. The mode is decided at the end of `elicit` based on the size and complexity of the candidate set, and may be overridden by the user at any time.

## Mode selection rule

| Signal | Light | Heavy |
|--------|-------|-------|
| Functional requirements | ≤ 5 | > 5 |
| Non-functional requirements | ≤ 2 | > 2 |
| Quality attributes ranked | ≤ 3 | > 3 |
| Integration surfaces | 0–1 | 2+ |
| Regulatory context mentioned | no | yes |
| User asked for "formal SRS" | — | yes |

If **any** of the "Heavy" conditions apply, run in heavy mode. Otherwise run in light mode.

Tell the user explicitly which mode you chose and why, at the end of `elicit`:

> "Given a single feature with 3 FRs and no regulatory context, I am running RE in **light mode**: User Story + Acceptance Criteria, short trade-off bullets, no scenarios. Tell me if you want the heavy process instead."

## What light mode skips

- Full trade-off matrix in `analyze` — a short bulleted list of trade-offs is enough.
- Architectural scenarios in the quality-attribute document.
- Multi-paragraph rationale sections in the quality-attribute document.
- Cross-section traceability matrices (still record `upstream_refs` / `downstream_refs` on each artifact, just do not build a separate matrix document).

## What light mode still enforces

Everything that affects correctness. Do not compromise on these:

- Every FR has at least one acceptance criterion.
- Every NFR has a **measurable** acceptance criterion (number + unit).
- Every constraint has a rationale.
- Every quality attribute has a metric and trade-off notes.
- SMART check and downstream fitness check in `review` run in full.
- All three section artifacts are produced — there is no "skip the constraints artifact" variant.

## What heavy mode adds

- IEEE 830 / ISO 29148-style sectioning in the requirements document.
- A full trade-off matrix in `analyze` with explicit option tables per conflict.
- Architectural scenarios per top-3 quality attribute (stimulus, environment, expected response, response measure).
- A paragraph of narrative rationale for the top-3 quality attribute ranking.
- Detailed structured YAML mirrors of the markdown tables in `*.meta.yaml` for every row (so downstream skills can parse without re-scanning prose).

## User override

The user may say "do the full process" or "keep it light". Honour the override, but if the override contradicts the signals (e.g. user asks for light mode on a complex system with regulatory items), warn them once:

> "You asked for light mode, but the request involves PII and 8 functional requirements. Heavy mode would give `security:threat-model` and `qa:strategy` more to work with. Light mode is fine if you prefer speed — your call."

Then proceed with the user's choice.

## Mode transitions mid-run

If during `analyze` you discover the candidate set is actually much larger than `elicit` suggested, you may upgrade light → heavy. Tell the user:

> "The candidate set grew during analysis (we're now at 8 FRs and 4 quality attributes). Upgrading to heavy mode so we don't lose decisions in the final artifact."

Downgrades (heavy → light) should be rare and require explicit user agreement, because you would be dropping sections the user already invested in.
