# Arch Input Contract

How the Impl skill reads the four Arch artifacts and turns each field into a code-generation directive. Read this before `generate` when you need to know what a specific Arch field is supposed to produce in code.

## Location and readiness

- Arch artifacts live in `./artifacts/arch/` (override with `HARNESS_ARTIFACTS_DIR`, which points at the parent `artifacts/` directory).
- The four sections must all be present:
  - `ARCH-DEC-*` — decisions
  - `ARCH-COMP-*` — components
  - `ARCH-TECH-*` — technology stack
  - `ARCH-DIAG-*` — diagrams
- Every one must be in phase `approved`. If any is in `draft` / `in_review` / `revising`, stop and tell the user — Impl must not run on unstable input.

Use `python ${SKILL_DIR}/../arch/scripts/artifact.py list` (or read the metadata files directly) to confirm. If only the Impl `artifact.py` is available locally, read the Arch YAML files with a small script that walks `./artifacts/arch/*.meta.yaml`.

## ARCH-DEC-* → code shape

| Arch field | Impl action |
|------------|-------------|
| `id` | Recorded in the IDR's `arch_refs` whenever the decision forces a code-level choice |
| `decision` | Drives the architectural shape of the code: layered / hexagonal / event-driven / CQRS / ... |
| `rationale` | Copied (or summarised) into IDR rationale where the decision lands in code |
| `trade_offs` | Preserved as a short inline comment at the enforcement point, or as IDR "Negative consequences" |
| `alternatives_considered` | Used to avoid regenerating rejected options if they look tempting from the code side |
| `re_refs` | Propagated into `IMPL-IDR-*.re_refs` so downstream skills can trace "why" back to RE |

**Pattern mandates**: if the `decision` text names a pattern (Repository, Hexagonal, Outbox, …), that pattern is mandatory and must be visible in the code. It is applied in Stage 2 and recorded as an IDR citing the ADR.

## ARCH-COMP-* → modules and interfaces

| Arch field | Impl action |
|------------|-------------|
| `id` | Recorded as `component_ref` on the corresponding `IM-xxx` entry |
| `name` | Base name for the module / package (snake_case or the detected convention) |
| `type` | Kind of module: library / service / CLI / worker / edge-function |
| `responsibility` | Single-sentence docstring at the top of the module's entry point, and the SRP test line during review |
| `interfaces` | Interface / trait / abstract class definitions with the exact method shape |
| `dependencies` | Directional import graph; any edge not listed here is a contract violation |
| `re_refs` | Recorded on the Implementation Map entry so RE traceability survives |

Interface protocols: when `interfaces` specifies a protocol (HTTP, gRPC, queue), generate the transport-specific glue *in addition to* the language-level interface, so the same component exposes both a typed contract and a wire contract.

## ARCH-TECH-* → dependency manifest

| Arch field | Impl action |
|------------|-------------|
| `category` | Slot in the manifest (language / runtime / framework / DB / messaging / cache / observability) |
| `choice` | Concrete library or service chosen. This is the **only** allowed set — nothing else may appear in `IMPL-CODE-*.external_dependencies` without a matching `ARCH-TECH-*.choice` |
| `rationale` | Recorded in the Implementation Guide's `conventions` or `prerequisites` section |
| `decision_ref` | When present, the tech choice inherits the ADR's constraints |
| `constraint_ref` | Must be visibly satisfied; `hard` constraints are non-negotiable |

Version selection: pick the latest stable release that satisfies every `constraint_ref`. Do not pin to a pre-release unless the constraint forces it.

## ARCH-DIAG-* → control and data flow

| Diagram type | Impl action |
|-------------|-------------|
| `c4-context` | Informational only; used to decide which external-system adapters must exist |
| `c4-container` | Confirms the multi-module decomposition; each container should correspond to an `IMPL-MAP-*` entry (or a group of them) |
| `sequence` | Method-call order inside the relevant handler must match. The review stage checks this directly |
| `data-flow` | The transformation pipeline must visit the same stages; pipeline code lives in the module(s) the diagram names |

## Traceability propagation

Every Implementation Map entry must link upstream to the Arch component:

```
python ${SKILL_DIR}/scripts/artifact.py link <impl-map-id> --upstream ARCH-COMP-001
```

Every IDR that applies a pattern must link upstream to the ADR (if mandatory) or at least to the component whose code it affects:

```
python ${SKILL_DIR}/scripts/artifact.py link <impl-idr-id> --upstream ARCH-DEC-002
```

Every `external_dependencies` row in Code Structure must carry a `tech_stack_ref` back to `ARCH-TECH-*`.

## When Arch is wrong

If an Arch decision is genuinely unrealisable (chosen framework cannot expose the required interface, chosen database cannot meet the `hard` NFR, two components' declared dependencies form an illegal cycle when taken literally), **do not** patch around it inside Impl. Stop, escalate to the user, and recommend they re-open Arch. Arch is the source of truth for structure.
