# Workflow Stage 4 — Review

## Role

Verify that the three `in_review` artifacts produced by `spec` are good enough to hand off to downstream skills. Catch mistakes you (or the user) missed during drafting, flag anything that needs a human decision, and — once everything is clean — move the artifacts to `approved`.

This is the last gate before downstream consumption. If something leaves `review` in a broken state, `arch` and `qa` will quietly produce broken derivatives. Do not wave things through.

## Core capabilities

### 1. SMART check on every requirement

For each FR and NFR, verify:

- **Specific**: no vague verbs ("support", "handle", "deal with") without a direct object
- **Measurable**: at least one acceptance criterion is objectively verifiable
- **Achievable**: feasibility was already confirmed in `analyze` — if you find a newly infeasible item, push back to `analyze`
- **Relevant**: it traces to a user utterance or a derived consequence thereof
- **Testable**: `qa` could, in principle, derive at least one test

Flag anything that fails. For NFRs, the common failure is a missing number. "Fast" is not a metric; "p95 < 200ms for /search over 1M rows" is.

### 2. Constraint mutual consistency

Cross-check every constraint pair. Look for:

- Two `hard` constraints that cannot simultaneously hold
- A `hard` constraint that contradicts a `Must` requirement
- A `regulatory` constraint without a cited regulation or rationale
- A missing `rationale` field — every constraint must explain *why* it exists

### 3. Quality attribute coherence

Verify:

- Every attribute has a **measurable metric**
- Every attribute has **trade-off notes** that name what is sacrificed
- The top-3 attributes have a narrative **rationale** in section 2 of the markdown
- No two attributes tied at the same rank — ranking must be total, not partial

### 4. Traceability check

Run:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate
```

This checks schema compliance, bidirectional `upstream_refs` / `downstream_refs` integrity, phase and approval states, and that every `document_path` exists. Do not proceed while there are errors.

### 5. Downstream fitness check

Read [../contracts/downstream-contract.md](../contracts/downstream-contract.md) and check each consumer in turn:

- **`arch:design`** — does the requirements set give enough to derive architectural drivers? Are the top-3 quality attributes concrete enough to pick patterns?
- **`qa:strategy`** — does every FR have at least one acceptance criterion that `qa` can turn into a test case?
- **`impl:generate`** — is the scope boundary clear enough that `impl` knows what *not* to build?
- **`security:threat-model`** — are the regulatory constraints and security quality attribute concrete enough to seed STRIDE/LINDDUN?
- **`deployment:strategy`** — are the environmental constraints (regions, uptime, compliance zones) recorded?
- **`operation:slo`** — are the measurable targets specific enough to become SLOs?

If the answer to any of these is "not really", write down what is missing, bring it to the user, and either fix it in place or loop back to the relevant earlier stage.

### 6. Escalate human decisions

Some issues you cannot fix on your own. Examples:

- A `hard` constraint that the user did not explicitly confirm
- A quality-attribute ranking that would change the architecture significantly
- A `Must` requirement that the user casually dropped into the chat but never confirmed as non-negotiable
- A missing acceptance criterion on a `Must` item

Bring each escalation to the user with a compact summary and a specific question. Do not approve the artifact until these are resolved.

## Approval

Once all artifacts pass validate + downstream fitness and the user is satisfied:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <RE-REQ-id> --approver <user> --notes "…"
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <RE-CON-id> --approver <user> --notes "…"
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <RE-QA-id>  --approver <user> --notes "…"
```

The script rejects approval unless the artifact is in `in_review`. If an artifact slipped back to `revising`, transition it to `in_review` first, then approve.

After approval, point the user at the next Harness skill (typically `arch`) and exit. Do not keep iterating on approved artifacts in the same turn — if the user wants changes, they can re-enter RE and you will start a new revision cycle.

## Inputs

- Three artifacts in phase `in_review` (from `spec`)
- Mode (light / heavy) — a light-mode review may omit the trade-off narrative and scenarios, but SMART and downstream-fitness checks are non-negotiable in either mode

## Outputs of this stage

- All three artifacts in phase `approved` with `approval.state = approved`
- A clean `validate` report
- A short review report surfaced to the user listing: issues found, issues fixed, issues deferred with reason, and the next skill to invoke

## Common anti-patterns

- **Rubber-stamping** — running `approve` without actually checking SMART / downstream fitness. The gate exists for a reason.
- **Silent fixes** — editing the markdown to "fix" something the user should have decided. Escalate instead.
- **Skipping `validate`** — trusting your own eyes. The script catches traceability mistakes you will miss.
- **Blocking on perfection** — refusing to approve because of a minor issue the user has already accepted. Approve with notes instead.
- **Approving out of `draft`** — the script will stop you. If you find yourself trying, go back to `spec`.
