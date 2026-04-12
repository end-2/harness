# Downstream Consumption Contract

RE artifacts exist to be consumed by the rest of the Harness pipeline. This document lists what each downstream skill expects from the three RE sections, and what "good enough" looks like. The `review` stage uses this document as a checklist.

## Consumers at a glance

| Downstream skill | Primary section it reads | Secondary sections |
|------------------|--------------------------|--------------------|
| `arch:design` | Quality Attribute Priorities | Requirements Spec (NFRs), Constraints |
| `impl:generate` | Requirements Spec (FRs) | Constraints |
| `qa:strategy` | Requirements Spec (acceptance criteria) | Quality Attribute Priorities |
| `sec:threat-model` | Constraints (regulatory), Quality Attribute Priorities (security) | Requirements Spec |
| `devops:iac` | Constraints (environmental) | Quality Attribute Priorities (availability) |
| `devops:slo` | Quality Attribute Priorities (measurable metrics) | Requirements Spec (NFRs) |

## Per-consumer fitness checks

### `arch:design`

Uses the top-ranked quality attributes as **architectural drivers** — the forces that shape pattern choice.

Requires:

- A strictly ordered ranking of 3–6 quality attributes. No ties.
- Each of the top-3 attributes has a concrete measurable metric.
- Each of the top-3 attributes has trade-off notes.
- All `hard` constraints are explicit and have a rationale — `arch` treats them as non-negotiable drivers.

Rejected by `review` if: an attribute lacks a metric, two attributes tie for the same rank, or a `hard` constraint has no rationale.

### `impl:generate`

Uses functional requirements as a work list and constraints as build-time boundaries.

Requires:

- Every `Must` FR has at least one acceptance criterion.
- Every `Must` FR is implementable — infeasibility should have been caught in `analyze`.
- Scope boundary is explicit: what is `Won't` (out of scope) is spelled out, not just omitted.
- `technical` constraints are listed (language, framework, runtime).

Rejected by `review` if: a `Must` has no acceptance criterion, or the scope boundary is silent on an obvious extension the user might otherwise expect.

### `qa:strategy`

Derives test strategy from acceptance criteria.

Requires:

- Every FR has at least one acceptance criterion that can be turned into a test case.
- Every NFR has a **measurable** acceptance criterion (number + unit).
- Performance-related quality attributes have scenarios or test targets explicit enough to design a load test.

Rejected by `review` if: an FR's acceptance criterion is subjective ("it should feel fast"), or an NFR is un-measurable.

### `sec:threat-model`

Derives threat categories and mitigations from regulatory constraints and the security quality attribute.

Requires:

- Regulatory constraints (GDPR, HIPAA, PCI-DSS, SOC2, …) are explicit if applicable, with rationale.
- The `security` quality attribute has a description specific to this project (not just "be secure"), with at least one metric ("all PII encrypted at rest with KMS-managed keys", "no public S3 buckets").
- Any FR that touches auth, payment, PII, or external integrations flags this in its description.

Rejected by `review` if: a user mentioned "PII" or "payments" in elicit but no security/regulatory item made it to the artifact.

### `devops:iac`

Derives infrastructure topology and deployment environment shape from environmental constraints and availability targets.

Requires:

- Environmental constraints are explicit: regions, compliance zones, cloud vendor restrictions, on-prem requirements.
- The `availability` quality attribute (if listed) has an uptime target and a blast-radius scenario.

Rejected by `review` if: the user mentioned a deployment region or compliance zone but it did not land as a constraint.

### `devops:slo`

Turns measurable quality-attribute metrics into SLOs.

Requires:

- Every quality attribute in the artifact has a metric specific enough to become an SLI (e.g. "p95 latency over /search"), not just "200ms response time" with no endpoint.
- The user has either confirmed SLO targets or explicitly delegated them to `devops`.

Rejected by `review` if: the metric is too abstract to become an SLI.

## Running the fitness check in `review`

During `review`, walk each consumer above and ask the user or yourself: *given only the three RE artifacts, could this skill start working today?* For each "no", decide whether to:

1. Fix in place (add the missing metric, add the missing rationale, tighten the acceptance criterion).
2. Loop back to `analyze` or `elicit` if the gap is a user-decision gap.
3. Defer with a recorded reason in the Open Questions section, and tell the user which downstream skill will be weakened by the deferral.

Do not approve the artifact while any consumer is blocked. A silent downstream failure is more expensive than an extra review round.
