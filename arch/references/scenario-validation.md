# Scenario Validation

Arch's `review` stage validates the design by turning each top-ranked quality-attribute metric from `RE-QA-*` into a concrete scenario and walking the design through it. This is a compressed form of ATAM's scenario walkthrough: fewer actors, a single decider, but the same logic.

A scenario is **not** a test case. It is a thought experiment against the artifact: given the chosen components and tech stack, can the top driver plausibly meet its metric? The answer is a judgment — but it is a judgment made in the open, with the trade path explicitly visible.

## The conversion template

For each top-ranked quality attribute, fill in this template:

```
Quality attribute : <name>, rank <N>
RE metric         : <verbatim from RE-QA-XXX.quality_attributes[].metric>
Source            : RE-QA-<id>.<field> or NFR-<id>.acceptance_criteria

Stimulus          : <what triggers the scenario — user action, system event, failure>
Environment       : <normal load / peak / degraded / failover / startup>
Response          : <what the system should do>
Response measure  : <the RE metric, restated in operational terms>

Path through design:
  1. <component A> — <role in the scenario, latency/throughput/security budget>
  2. <component B> — ...
  3. <component C> — ...

Pass condition    : <response measure, as a concrete threshold>
Verdict           : pass | at risk | fail
Reasoning         : <one paragraph naming the slow/risky hop and why it is or is not within budget>
```

## Example — performance

```
Quality attribute : performance, rank 1
RE metric         : p95 response time < 200ms for /search over 1M rows
Source            : NFR-003.acceptance_criteria

Stimulus          : A logged-in user calls GET /search?q=foo
Environment       : Normal load, ~200 rps, warm cache
Response          : Return top-20 results as JSON
Response measure  : p95 end-to-end latency at the API boundary

Path through design:
  1. API Gateway (COMP-001) — TLS termination + auth check, ~5ms budget
  2. Search Service (COMP-002) — query translation + fan-out, ~15ms budget
  3. Postgres read replica (COMP-005) — indexed query on `search_gin_idx`, target ~120ms
  4. Redis cache (COMP-004) — first-hop cache for hot terms, ~2ms when hit

Pass condition    : p95 ≤ 200ms
Verdict           : at risk
Reasoning         : The DB step is the tall pole. On a cold cache at 1M rows with the
                    configured index, p95 is plausibly 150–180ms in isolation, which
                    leaves a thin margin once network and gateway are added. AD-003
                    (cache-aside with Redis) hides most of the cost, but the cold-start
                    scenario is where it can fail. Recommend explicit warm-up or a
                    stricter index (trigram + covering index) — surface to user.
```

The verdict is a real judgment. "at risk" is not a failure; it is a flag that the user must acknowledge or fix.

## Example — availability

```
Quality attribute : availability, rank 2
RE metric         : 99.9% uptime per month (~43 minutes downtime budget)
Source            : RE-QA-002.metric

Stimulus          : A single availability zone becomes unreachable
Environment       : Peak load (2x normal)
Response          : Serve reads, defer non-critical writes, never corrupt data
Response measure  : Successful request rate ≥ 99% during the outage

Path through design:
  1. Load Balancer (COMP-000) — health checks drop the dead AZ within 30s
  2. API Gateway (COMP-001) — stateless, replicated across the remaining 2 AZs
  3. Search Service (COMP-002) — stateless, replicated
  4. Postgres primary (COMP-005a) — if in the failed AZ, promotes the standby
  5. Queue (COMP-006) — buffers non-critical writes during promotion

Pass condition    : Loss window ≤ 60s and success rate ≥ 99% end-to-end
Verdict           : pass (with assumption)
Reasoning         : Assumes AD-007 (automatic standby promotion) is actually wired up
                    and tested in deployment. Flag to user: this is untested until
                    deployment:strategy runs a failover drill.
```

## Scoring rules

- **pass** — the design clearly meets the metric under the stated environment.
- **at risk** — the design probably meets the metric, but the margin is thin or depends on an assumption that is worth naming out loud.
- **fail** — the design does not meet the metric. `review` fails; loop back to `design`.

A scenario that ends in "at risk" is a conversation with the user. They may accept the risk, or they may decide to tighten the design. Either outcome is fine — the unacceptable outcome is silently classifying it as "pass".

## One scenario per top-3, minimum

In light mode, run at least one scenario per top-3 quality attribute. In heavy mode, add stress scenarios (10x load, degraded dependency, full failover) for whichever driver is most sensitive. More than six total scenarios in a single review is usually noise — pick the ones that actually separate the design from its alternatives.
