# Workflow — Stage 1: strategy

## Role

Read the approved RE, Arch, and Impl artifacts and produce the Test Strategy section: scope, pyramid, NFR plan, environment matrix, test-double strategy, quality-gate criteria. This is the only stage that picks the adaptive mode and that decides what counts as "in scope" for the rest of the run.

## Inputs

- `RE-SPEC-*` — every FR/NFR with `acceptance_criteria`, `priority`, `dependencies`. The MoSCoW priority is the gate for inclusion.
- `RE-CON-*` — constraints; the `type=regulatory` and `flexibility=hard` rows drive the environment matrix and the compliance test set.
- `RE-QA-*` — quality attribute priorities; every row with a `metric` becomes one NFR test scenario.
- `ARCH-DEC-*` — pattern hints (event-driven, microservice, layered, hexagonal, …) drive test style.
- `ARCH-COMP-*` — interfaces are the integration boundary; dependencies drive the test-double seam map.
- `ARCH-TECH-*` — the technology set fixes the testing framework choice.
- `ARCH-DIAG-*` — sequence and data-flow diagrams point at the e2e scenario list.
- `IMPL-MAP-*` — `module_path` is the test-file location anchor; `interfaces_implemented` is the contract surface.
- `IMPL-CODE-*` — `module_dependencies` shows the seam graph; `external_dependencies` lists what must be doubled.
- `IMPL-IDR-*` — `pattern_applied` flips testability rules per pattern (Repository → fakes at the seam, Strategy → one test per strategy, Decorator → wrapped behaviour preservation).
- `IMPL-GUIDE-*` — `conventions.tests` says where tests live; `run_commands` says how to run them.

## Mode selection

Pick the mode at the very start, before any further work:

| Signal | Mode |
|--------|------|
| Impl ran in light mode (≤ 2 IDRs, single project scaffold, brief Implementation Guide). | **light** |
| Impl ran in heavy mode (multi-module, full Mermaid dependency graph, several IDRs). | **heavy** |

Tell the user which mode you chose and which signal you used. The user may override by saying "run QA in heavy mode" or "run QA in light mode" — record the override in the Test Strategy document.

## Deriving the strategy

### Scope

- Every `RE-SPEC-*` row with `priority` of `must` or `should` is in scope. `could` rows go in scope only when an Impl module exists for them. `wont` rows are explicitly listed in the "out of scope" table with the RE id and the reason.
- Every `RE-CON-*` row with `type: regulatory` is in scope as a compliance test target.
- Every `RE-QA-*` row with a `metric` is in scope as an NFR test target.

### Pyramid

Default ratios:

| Mode | unit | integration | e2e | contract | nfr |
|------|------|-------------|-----|----------|-----|
| light | 70% | 25% | 5% | as needed | one per metric |
| heavy | 60% | 25% | 10% | as ARCH-DEC requires | one per metric, with load profile |

Adjust from defaults when the architecture demands it: a microservice topology pushes contract tests up, an event-driven pipeline pushes integration tests up, a CRUD scaffold pushes the unit ratio higher.

### NFR test plan

For every `RE-QA-*` row with a `metric`, write one row in the NFR plan with `metric_ref`, `attribute`, the verbatim `target`, a concrete `scenario` (load profile or stress shape), and the `tooling` you will use. The tooling must be in `ARCH-TECH-*` or trivially installable from there — do not invent a stack.

### Environment matrix

For every distinct environment that any `RE-CON-*` or `ARCH-TECH-*` row implies, add a row with the environment name, its purpose, and the constraint refs that pinned it. Defaults: `local` (unit + integration), `ci` (full suite), `staging` (e2e + nfr).

### Test-double strategy

Walk every `IMPL-CODE-*.external_dependencies` row and pick a default seam: real / in-memory fake / contract test + recorded fixtures / mock at the boundary. Cite the IDR if Impl already chose for you.

### Quality gate criteria

Default values, adjusted only with explicit reason:

| Criterion | Default | Notes |
|-----------|---------|-------|
| `code_coverage_min` | 0.80 | drop to 0.70 in light mode if Impl is < 1k LOC |
| `requirements_coverage_must_min` | 1.00 | non-negotiable for Must |
| `max_failed_tests` | 0 | non-negotiable |
| `nfr_results` | every NFR row must `pass: true` | per `RE-QA-*.metric` |

These values later populate `quality_gate.criteria` in the Quality Report metadata via `artifact.py set-block` before Stage 4 runs `gate-evaluate`.

## Output — the Test Strategy section

Create the artifact pair via `artifact.py init`, edit the markdown body, link upstream to every RE / Arch / Impl id you cited, set progress, and transition to `in_review`. Sequence:

```
python ${SKILL_DIR}/scripts/artifact.py init --section test-strategy
# edit QA-STRATEGY-001.md only — never *.meta.yaml
python ${SKILL_DIR}/scripts/artifact.py set-block QA-STRATEGY-001 --field test_strategy --from /tmp/test-strategy.yaml
python ${SKILL_DIR}/scripts/artifact.py link QA-STRATEGY-001 --upstream RE-SPEC-001
python ${SKILL_DIR}/scripts/artifact.py link QA-STRATEGY-001 --upstream RE-QA-001
python ${SKILL_DIR}/scripts/artifact.py link QA-STRATEGY-001 --upstream ARCH-COMP-001
python ${SKILL_DIR}/scripts/artifact.py link QA-STRATEGY-001 --upstream IMPL-MAP-001
python ${SKILL_DIR}/scripts/artifact.py link QA-STRATEGY-001 --upstream IMPL-CODE-001
python ${SKILL_DIR}/scripts/artifact.py set-progress QA-STRATEGY-001 --completed 6 --total 6
python ${SKILL_DIR}/scripts/artifact.py set-phase QA-STRATEGY-001 in_review
```

Stage 1 is the only stage where the user routinely sees a draft before the next stage starts — pause here long enough for the mode and quality-gate defaults to be confirmed.

## Escalation

Escalate only when:

- An upstream artifact is missing, unreadable, or not yet `approved`.
- RE has no acceptance criteria at all (the system is too vague to test).
- The user-overridden mode contradicts the Impl mode in a way that would force fabricating fields (e.g. heavy QA on a light Impl with no Implementation Map entries).

Do **not** escalate for:

- Unknown convention defaults — pull from Impl or fall back to stack idioms.
- Disagreements about pyramid ratios — pick the default and let the user override in review.
- Missing tooling that has an obvious in-stack equivalent.
