# Workflow — Stage 3: review

## Role

Verify the generated code and the four Impl sections along two axes — **Arch compliance** and **clean code** — and produce a structured issue list that the `refactor` stage can consume. This stage **runs in a subagent** so the review sees the code with fresh eyes.

The subagent **does not return the report in its message body** and **does not edit any Impl section** or source file. It writes a report file and returns only `report_id + verdict + summary`. See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full handoff protocol.

## Inputs to the subagent

Pass the following into the subagent as its only input:

- `./artifacts/arch/` — the four Arch artifacts (for compliance checks)
- `./artifacts/impl/` — the four Impl section artifacts (for traceability checks)
- the project source tree — the code to review
- the **allocated report file path** (the main agent called `artifact.py report path --kind review --stage review --scope all` before spawning this subagent)

## Axis 1 — Arch compliance

Walk each Arch artifact and confirm it shows up in the code.

### Component boundaries (ARCH-COMP-*)

- Every `ARCH-COMP-*.interfaces` entry must have a corresponding implementation file listed in an `IMPL-MAP-*` entry.
- The code's import graph must match `ARCH-COMP-*.dependencies`. Any import that crosses a boundary Arch did not declare is a **Contract violation** (severity: high, not auto-fixable).
- Each component's actual source must fit inside its mapped `module_path`. Leaked files are either misplaced (auto-fix: move them) or genuine boundary violations (escalate).

### Decisions (ARCH-DEC-*)

- Patterns explicitly named in an ADR must be visibly present. If an ADR says "hexagonal", there must be ports and adapters; if it says "repository per aggregate", there must be repository modules.
- Trade-off text from the ADR should be reflected either as inline comments at the enforcement point or as IDR references in `IMPL-IDR-*`.

### Technology stack (ARCH-TECH-*)

- Every dependency in `IMPL-CODE-*.external_dependencies` must map to an `ARCH-TECH-*.choice`. Any dependency with no Arch anchor is a **Contract violation**.
- Version selection must respect `ARCH-TECH-*.constraint_ref` (e.g. "must run on Java 17" rules out Java 21-only libraries).

### Diagrams (ARCH-DIAG-*)

- Sequence diagrams: the method-call order in the corresponding handler should match. Out-of-order or missing steps are issues.
- Data-flow diagrams: the transformation pipeline in the code must visit the same stages.

### RE constraints (via `constraint_ref`)

- Every `hard` RE constraint reachable via Arch's `constraint_ref` must be visibly satisfied by some line of code. Record the file:line as evidence in the review report.

## Axis 2 — Clean code

- **SOLID** — flag SRP violations, unnecessary concretions in place of abstractions, interface-segregation breaches.
- **Readability** — name length vs scope, magic numbers, deeply nested conditionals.
- **Naming consistency** — does the code match the conventions recorded in `IMPL-GUIDE-*.conventions`?
- **Complexity** — cyclomatic > 10 or cognitive complexity > 15 on a function is a smell. Flag, don't auto-reject.
- **Bug smells** — off-by-one, unclosed resources, ignored errors, nullable misuse, race conditions in shared state.
- **OWASP-level baseline security** — SQL string concatenation, missing input validation at trust boundaries, hardcoded secrets, unsafe deserialisation. Deep threat modelling is the `security` skill's job; this is only the baseline sanity check.

## Report handoff (mandatory)

Fill the frontmatter and body of the allocated report file per the contract:

- `kind: review`
- `stage: review`
- `target_refs`: the four Impl section IDs (`IMPL-MAP-*`, `IMPL-CODE-*`, `IMPL-IDR-*`, `IMPL-GUIDE-*`)
- `verdict`: `pass` when there are no findings, `at_risk` when there are auto-fixable issues only, `fail` when there are contract violations the main agent must escalate to the user
- `summary`: one line, e.g. `2 contract violations (auth→billing), 7 auto-fixable smells, 1 hardcoded secret.`
- `items`: one entry per finding. Include `location` (`file:line` or `IMPL-*#anchor`), `arch_ref` where applicable, `classification ∈ {contract_violation, clean_code, security_baseline, traceability_gap, escalation}`, `severity ∈ {high, med, low, info}`, `message`, `suggested_fix`.
- `proposed_meta_ops`: optional. Small `link` suggestions the main agent can apply are fine; **never** propose `set-phase` or `approve`.

### Body structure

```markdown
# review report (impl/review)

## Summary
- Contract violations: N
- Auto-fixable clean-code: N
- Auto-fixable security-baseline: N
- Arch refs checked: N

## Contract violations (escalate to user)
1. **[HIGH] Boundary crossing** — `src/api/auth.ts:42` imports `src/billing/internal/...`, which Arch does not declare.
   - Arch ref: ARCH-COMP-002, ARCH-COMP-005
   - Suggested fix: needs Arch update or a new interface in ARCH-COMP-002.

## Auto-fixable issues (route to refactor)
1. **[MED] SRP** — `src/auth/service.ts` — service mixes token minting and session storage; extract `SessionStore`.
2. **[LOW] Naming** — `src/api/handlers.ts:118` — function `doStuff` should be `resolveUser` per detected conventions.

## Traceability
- Every ARCH-COMP has at least one IMPL-MAP entry: yes / no
- Every IMPL-IDR cites an Arch or RE ref: yes / no
```

Each body item must correspond to exactly one `items[]` entry in the frontmatter — keep the IDs in sync so the main agent can route findings programmatically.

Classification drives routing (applied by the main agent after reading the report):

- **Contract violations** → the main agent shows them to the user with the relevant Arch ref. Do not auto-refactor across Arch boundaries.
- **Auto-fixable issues** → the main agent hands the issue list to `refactor`.

## Traceability gate

Before writing the report body, run:

```
python ${SKILL_DIR}/scripts/artifact.py validate
```

and ensure there are no schema or traceability errors. A validation failure is itself a review finding (add an item with `classification: traceability_gap`).

## Subagent protocol

Before returning, validate the report itself:

```
python ${SKILL_DIR}/scripts/artifact.py report validate <report_id>
```

Return to the main agent only the `report_id`, `verdict`, and `summary` — never the full body. The main agent reads the body via `artifact.py report show <report_id>`, routes the issue list, and — after the `refactor` loop settles — uses `artifact.py approve` to finalise the four Impl sections.
