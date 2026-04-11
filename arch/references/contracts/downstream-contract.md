# Downstream Consumption Contract

Arch artifacts exist to be consumed by the rest of the Harness pipeline. This document lists what each downstream skill expects from the four arch sections, and what "good enough" looks like. The `review` stage uses this document as a checklist.

## Consumers at a glance

| Downstream skill | Primary section it reads | Secondary sections |
|------------------|--------------------------|--------------------|
| `impl:generate` | Component Structure, Technology Stack | Architecture Decisions |
| `qa:strategy` | Component Structure (interfaces, NFR refs) | Architecture Decisions, Diagrams (sequence) |
| `security:threat-model` | Architecture Decisions, Diagrams (data flow) | Component Structure, Technology Stack |
| `deployment:strategy` | Technology Stack (infra), Architecture Decisions | Component Structure |
| `operation:runbook` | Component Structure, Technology Stack | Diagrams |

## Per-consumer fitness checks

### `impl:generate`

Uses components as the list of things to generate, tech stack as the language/framework choice, and decisions as the design intent.

Requires:

- Every component has a clear `responsibility`, `interfaces` with direction and protocol, and at least one `re_refs` entry.
- The tech-stack `language` and `framework` rows are both present (or explicitly marked "none" with a reason).
- Every component lists its `dependencies` so `impl` can order generation.

Rejected by `review` if: a component lacks `re_refs`, an interface lacks a protocol, or `impl` would have to guess the language.

### `qa:strategy`

Derives test scope from components and test intent from NFRs mapped onto those components.

Requires:

- Every NFR in RE maps to at least one component (so QA knows *where* to test).
- At least one sequence diagram exists for the top-ranked quality-attribute flow (so QA knows *what* to test end-to-end).
- Every component's `interfaces` list is complete — those are the boundaries QA writes contract tests against.

Rejected by `review` if: an NFR has no component owner, or the top-ranked quality attribute has no sequence diagram.

### `security:threat-model`

Reads decisions for trust boundaries, data flow diagrams for information flow, and the tech stack for vulnerability surface.

Requires:

- Decisions that touch auth, crypto, isolation, or data residency are captured as ADRs (not buried in summary lines).
- A data-flow diagram exists when the system ingests or moves sensitive data.
- The tech-stack `auth` row is present, either as a chosen provider or as "none" with a reason.

Rejected by `review` if: sensitive data flows exist but no DFD, or an auth-touching decision is not an ADR.

### `deployment:strategy`

Reads the tech stack `infra` row(s) and any decisions that name a deployment shape.

Requires:

- The tech-stack `infra` row names a concrete target (e.g. "AWS ECS Fargate", "Fly.io", "on-prem Kubernetes on RHEL 9") and cites a constraint or decision.
- At least one decision spells out the deployment shape (single region / multi-region / single-az / active-passive / etc.).
- Every `environmental` constraint from RE is satisfied by a decision or infra choice.

Rejected by `review` if: the infra row is generic ("cloud") without a target, or an environmental constraint has no satisfier.

### `operation:runbook`

Derives SLOs and operational procedures from quality-attribute metrics mapped onto components.

Requires:

- Every top-ranked quality attribute has a component and a decision that "own" it.
- The tech-stack `observability` row is present.
- Components of type `store` and `queue` are explicitly named — those become the operational targets.

Rejected by `review` if: a top-ranked quality attribute has no owner, or observability is absent for a non-trivial system.

## The fitness-check routine

During `review`, walk this list consumer by consumer. For each row, point at the artifact id and field that satisfies the requirement. Holes are almost always one of:

1. A missing RE ref on a component → assign it.
2. A missing diagram for a critical flow → draw it.
3. A generic tech-stack entry → replace with a concrete choice or mark as "none".
4. A decision that should have been an ADR → promote it.

Do not approve until the fitness check is clean for every downstream skill the user intends to use next. If the user plans to skip, say, `security`, you can relax the security-specific checks — but tell the user explicitly which checks you are skipping and why.
