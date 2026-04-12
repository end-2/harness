# Workflow Stage 4 — Review

## Role

Verify that the three `in_review` artifacts produced by `spec` are good enough to hand off to downstream skills. Catch mistakes you (or the user) missed during drafting, flag anything that needs a human decision, and — once everything is clean — have the main agent move the artifacts to `approved`.

This is the last gate before downstream consumption. If something leaves `review` in a broken state, `arch` and `qa` will quietly produce broken derivatives. Do not wave things through.

`review` runs as a **subagent**, so it does not talk to the user directly and it does not call `artifact.py approve` itself — it writes a report file and the main agent applies the verdict. Read [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full handoff protocol.

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
python ${SKILL_DIR}/scripts/artifact.py validate
```

This checks common metadata, section payload completeness for review-ready artifacts, bidirectional `upstream_refs` / `downstream_refs` integrity, phase and approval states, and that every `document_path` exists. Do not proceed while there are errors.

### 5. Downstream fitness check

Read [../contracts/downstream-contract.md](../contracts/downstream-contract.md) and check each consumer in turn:

- **`arch:design`** — does the requirements set give enough to derive architectural drivers? Are the top-3 quality attributes concrete enough to pick patterns?
- **`qa:strategy`** — does every FR have at least one acceptance criterion that `qa` can turn into a test case?
- **`impl:generate`** — is the scope boundary clear enough that `impl` knows what *not* to build?
- **`sec:threat-model`** — are the regulatory constraints and security quality attribute concrete enough to seed STRIDE/LINDDUN?
- **`devops:iac`** — are the environmental constraints (regions, uptime, compliance zones, cloud restrictions) recorded?
- **`devops:slo`** — are the measurable targets specific enough to become SLOs?

If the answer to any of these is "not really", write down what is missing, bring it to the user, and either fix it in place or loop back to the relevant earlier stage.

### 6. Escalate human decisions

Some issues you cannot fix on your own. Examples:

- A `hard` constraint that the user did not explicitly confirm
- A quality-attribute ranking that would change the architecture significantly
- A `Must` requirement that the user casually dropped into the chat but never confirmed as non-negotiable
- A missing acceptance criterion on a `Must` item

Bring each escalation to the user with a compact summary and a specific question. Do not approve the artifact until these are resolved.

## Report handoff (mandatory)

All findings go into the allocated report file — **not** into the return message. Fill the frontmatter and body per the contract:

- `kind: review`
- `stage: review`
- `target_refs`: the three `in_review` artifact IDs
- `verdict`: `pass` if everything is clean and the main agent can approve after the user says go, `at_risk` if there are fixable issues the main agent must address before approval, `fail` if something must go back to `spec` or `analyze`
- `summary`: one line, e.g. `SMART-clean except NFR-002 missing metric; 1 traceability gap on FR-004; downstream fitness OK.`
- `items`: each finding as a single item. Use `classification ∈ {smart_violation, constraint_inconsistency, traceability_gap, downstream_fitness, escalation}`.
- `proposed_meta_ops`: optional. Small fixes that the main agent can apply directly (e.g. a missing `link` between RE-REQ and RE-CON). **Never** propose `set-phase` or `approve` here — those are the main agent's call after user go-ahead.

### Body structure

```markdown
# review report (re/review)

## Summary
One paragraph expanding on the `summary` field.

## SMART check
Per-requirement pass/fail, with the specific reason on failures.

## Constraint consistency
Cross-checks between constraint pairs and between constraints and `Must` requirements.

## Quality attribute coherence
Per-QA check for metric, trade-off notes, and top-3 rationale.

## Traceability
Findings from the `artifact.py validate` run plus anything the subagent spotted by eye.

## Downstream fitness
One bullet per downstream skill (`arch:design`, `qa:strategy`, `impl:generate`, `sec:threat-model`, `devops:iac`, `devops:slo`) — does the artifact carry enough for that consumer?

## Escalations
Bullet list of items only the user can resolve (mirrors `items[]` with `classification: escalation`).
```

## Approval (main agent only)

The review subagent **never** calls `artifact.py approve`. When its report comes back with `verdict: pass` (or `at_risk` after the main agent has fixed the auto-fixable items and the user has accepted the rest), the main agent runs:

```bash
python ${SKILL_DIR}/scripts/artifact.py approve <RE-REQ-id> --approver <user> --notes "…"
python ${SKILL_DIR}/scripts/artifact.py approve <RE-CON-id> --approver <user> --notes "…"
python ${SKILL_DIR}/scripts/artifact.py approve <RE-QA-id>  --approver <user> --notes "…"
```

The script rejects approval unless the artifact is in `in_review`. If an artifact slipped back to `revising`, the main agent transitions it to `in_review` first, then approves.

After approval, the main agent points the user at the next Harness skill (typically `arch`) and exits. Do not keep iterating on approved artifacts in the same turn — if the user wants changes, they can re-enter RE and start a new revision cycle.

## Inputs

- Three artifact paths in phase `in_review` (from `spec`)
- Mode (light / heavy) — a light-mode review may omit the trade-off narrative and scenarios, but SMART and downstream-fitness checks are non-negotiable in either mode
- The allocated report file path

## Outputs of this stage

- A report file written to the allocated path, passing `artifact.py report validate`.
- A short return message: `report_id`, `verdict`, `summary` (and nothing else).
- No `artifact.py` state mutations — those are the main agent's responsibility after it reads the report and walks the user through the escalations.

## Common anti-patterns

- **Rubber-stamping** — running `approve` without actually checking SMART / downstream fitness. The gate exists for a reason.
- **Silent fixes** — editing the markdown to "fix" something the user should have decided. Escalate instead.
- **Skipping `validate`** — trusting your own eyes. The script catches traceability mistakes you will miss.
- **Blocking on perfection** — refusing to approve because of a minor issue the user has already accepted. Approve with notes instead.
- **Approving out of `draft`** — the script will stop you. If you find yourself trying, go back to `spec`.
