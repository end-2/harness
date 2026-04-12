# RE Input Contract

Arch consumes three RE artifacts. This document is the exact parsing rule — what Arch reads out of RE, and how each piece becomes an architectural driver.

## Source artifacts

| RE artifact | Section | Location |
|-------------|---------|----------|
| `RE-REQ-*`  | requirements | `./artifacts/re/RE-REQ-*.md` + `.meta.yaml` |
| `RE-CON-*`  | constraints | `./artifacts/re/RE-CON-*.md` + `.meta.yaml` |
| `RE-QA-*`   | quality-attributes | `./artifacts/re/RE-QA-*.md` + `.meta.yaml` |

All three must be in phase `approved`. If any is still `draft`, `in_review`, or `revising`, stop and tell the user — running Arch on unstable input will produce decisions you will throw away.

In standalone runs, read these artifacts from `./artifacts/re/`. In orchestrated runs, Orch passes the exact RE artifact paths separately. Do not reinterpret `HARNESS_ARTIFACTS_DIR` as an upstream RE root; that variable still points to Arch's own output directory.

## RE → Arch mapping

### `RE-REQ-*` (requirements)

| RE field | How Arch uses it |
|----------|------------------|
| `functional_requirements[].id` | Becomes a row in `components[].re_refs`. Every FR must land on at least one component. |
| `functional_requirements[].dependencies` | First sketch of the component graph. FRs that depend on each other often live in the same component or across a narrow interface. |
| `functional_requirements[].priority` (MoSCoW) | Drives sequencing, not structure. `Must` FRs must be satisfiable on day 1. |
| `non_functional_requirements[].id` | Becomes a row in `components[].re_refs` and/or `decisions[].re_refs`. |
| `non_functional_requirements[].category` | Hints the driver type: `performance` → latency/throughput, `security` → auth/crypto/isolation, `scalability` → partitioning/sharding, `availability` → redundancy/failover. |
| `non_functional_requirements[].acceptance_criteria` | The raw material for scenarios in `review`. The metric (number + unit) is the pass/fail line. |

### `RE-CON-*` (constraints)

| RE field | How Arch uses it |
|----------|------------------|
| `constraints[].id` | Becomes `constraint_ref` in tech-stack rows and `re_refs` in decisions. |
| `constraints[].type` | `technical` → typically satisfied by tech-stack choices. `business` → often a cost/operational constraint. `regulatory` → must be satisfied by a named decision, not hand-waved. `environmental` → shapes infra choices. |
| `constraints[].flexibility: hard` | **Non-negotiable**. Any decision that violates one is dead. `review` rejects artifacts that do not satisfy every hard constraint. |
| `constraints[].flexibility: soft` | Strong preference. Prefer designs that satisfy these; if a design relaxes one, call it out. |
| `constraints[].flexibility: negotiable` | Open for relaxation if it unlocks a better design. Relaxations must be confirmed with the user and recorded. |
| `constraints[].rationale` | Helps Arch understand **why** the constraint exists — often the rationale is what matters, not the constraint as literally stated. |
| `constraints[].impact` | "what breaks if this is violated" — shows up in ADR consequences. |

### `RE-QA-*` (quality attribute priorities)

| RE field | How Arch uses it |
|----------|------------------|
| `quality_attributes[].rank` | **Rank order = architectural driver order**. Top-3 shape pattern selection; lower ranks shape secondary choices. |
| `quality_attributes[].metric` | The pass/fail line for `review` scenarios. Must be a number with a unit or a concrete scenario. |
| `quality_attributes[].trade_off_notes` | **Already settled in RE — do not re-debate.** These are forces Arch must respect, not options to reopen. |

## What Arch must NOT do

- **Add requirements.** If Arch feels the need for a requirement that RE did not capture, surface it to the user and send them back to `re`, do not silently add it.
- **Re-rank quality attributes.** The rank order is fixed. If you believe it is wrong, say so to the user and go back to `re`.
- **Reinterpret `hard` constraints as `negotiable`.** Hard is hard.
- **Ignore `trade_off_notes`.** RE already made the trade-off; Arch builds under it.

## What Arch is allowed to push back on

- **Missing metrics.** If a top-ranked quality attribute has no measurable metric, `review` cannot run scenarios. Send the user back to `re:review`.
- **Contradictory constraints.** If two `hard` constraints cannot both be satisfied (e.g. "must run on free-tier" vs "must have < 50ms p99 globally"), name the contradiction and send the user back to `re:analyze`.
- **Under-specified FR dependencies.** If the FR graph has cycles or orphans, Arch cannot draw a clean component graph. Call it out.

## Loading the RE artifacts

In practice, the agent reads the markdown for prose context and the `.meta.yaml` for machine-readable fields. When quoting a specific requirement or constraint in an arch artifact, always cite by id (`FR-003`, `NFR-001`, `CON-002`, `RE-QA-001`), so downstream skills can cross-reference without guessing.
