# Workflow — Stage 4: refactor

## Role

Take the review report's auto-fixable issue list and transform the code to resolve them, without crossing Arch component boundaries. This stage **runs in a subagent**, so it focuses only on the issue list and the current source tree.

The subagent **does not edit source files or Impl sections directly**. It writes a `refactor` report file whose body includes concrete diffs (patches), and returns only `report_id + verdict + summary`. The main agent then applies the patches via `Edit`/`Write` and runs any `proposed_meta_ops`. See [../contracts/subagent-report-contract.md](../contracts/subagent-report-contract.md) for the full handoff protocol.

## Inputs to the subagent

- The review report (pass the `report_id`; the subagent loads it via `artifact.py report show <report_id>`).
- The current source tree.
- The four Impl section artifact paths (read-only; for traceability references).
- The four Arch artifact paths (to enforce boundary respect).
- The **allocated report file path** for this refactor pass (the main agent called `artifact.py report path --kind refactor --stage refactor --scope all`).

## Scope

- **In scope**: any refactor that stays inside a single Arch component's `module_path`, or that only touches interfaces Arch already declares.
- **Out of scope**: any refactor that would move responsibility across `ARCH-COMP-*`, add a new cross-component dependency, or break an Arch-declared interface. Those are Arch-contract issues — escalate back to the main agent, do not apply them silently.

## Vocabulary — Fowler's catalogue

Use the standard refactoring names so the IDRs and commit messages read consistently.

| Refactor | When |
|----------|------|
| **Extract Method** | A block of code in a long method has a clear single purpose |
| **Inline Method** | A method's body is as clear as its name; the indirection is dead weight |
| **Extract Variable** | A complex sub-expression appears more than once or obscures intent |
| **Introduce Parameter Object** | A group of parameters are always passed together |
| **Replace Conditional With Polymorphism** | A type-tag switch exists in more than one place |
| **Move Method / Move Field** | Data and the method that uses it live in different classes |
| **Extract Class** | A class has grown multiple responsibilities |
| **Replace Magic Number With Symbolic Constant** | Bare numeric literals with domain meaning |
| **Decompose Conditional** | A long boolean expression whose meaning is not obvious |
| **Remove Dead Code** | Code is never reached or never referenced |

## Safety rules

1. **One change at a time.** Do not batch unrelated refactors into a single diff hunk — keep each `items[]` entry's patch self-contained so the main agent can apply them one by one and reject individual ones if needed.
2. **Preserve behaviour.** Never introduce new features or fix unrelated bugs while refactoring.
3. **Respect boundaries.** Before proposing a patch, check the target file's Arch component via its `IMPL-MAP-*` entry. If the change would cross the boundary, **do not** write the patch — emit an item with `classification: boundary_escalation` instead.
4. **Keep the proposed build green.** Any patch you propose must leave the code compiling / type-checking after application. Do not propose half-migrated state.
5. **Flag traceability updates in meta ops.** If a refactor moves a file, do **not** call `artifact.py set-progress` yourself — propose it in `proposed_meta_ops`:
   ```yaml
   proposed_meta_ops:
     - cmd: set-progress
       artifact_id: IMPL-MAP-001
       completed: 5
       total: 6
   ```

## Recording the refactor

For each non-trivial refactor (anything more than a rename or a constant extraction), emit an item with `classification: idr_added` and include the IDR block markdown in the report body's "IDRs to merge" section. The main agent will apply it to the Implementation Decisions section's `.md` file. To link the IDR to an Arch ref, emit the link as a proposed meta op:

```yaml
proposed_meta_ops:
  - cmd: link
    artifact_id: IMPL-IDR-001
    upstream: ARCH-DEC-002
```

Trivial refactors (rename a local variable, fix a magic number) can live in code only and do not need an IDR item.

## Report handoff (mandatory)

- `kind: refactor`
- `stage: refactor`
- `target_refs`: the four Impl section IDs
- `verdict`: `pass` when all auto-fixable issues are resolved and no escalations remain, `at_risk` when some issues required boundary escalation
- `summary`: one line, e.g. `4 refactors applied (3 Extract Method, 1 Extract Class), 1 boundary escalation.`
- `items`: one entry per refactor applied or escalation raised. Classifications: `refactor_applied`, `idr_added`, `boundary_escalation`.

### Body structure

```markdown
# refactor report (impl/refactor)

## Summary
One paragraph expanding on the `summary` field.

## Applied refactors
1. **Extract Class: SessionStore** — resolved review item #1 in <previous review report_id>.
   - Files: src/auth/service.ts, src/auth/session_store.ts (new)
   - IDR added: see IDRs to merge below

## Patches
```diff
--- a/src/auth/service.ts
+++ b/src/auth/service.ts
@@ ...
```

## IDRs to merge into IMPL-IDR-*.md
### IDR-011 — Extract SessionStore
**Decision:** Extract Class → SessionStore
**Rationale:** review item #1 (SRP violation)
...

## Escalations
Issues that would require crossing an Arch boundary and so could not be auto-fixed. Each matches an `items[]` entry with `classification: boundary_escalation`.
```

## Hand-off back to review

The subagent returns `report_id + verdict + summary` only. The main agent:

1. Runs `artifact.py report validate <report_id>`.
2. Reads the body via `artifact.py report show <report_id>`.
3. Applies each patch via `Edit`/`Write`, keeping the build green between patches (if any patch fails, escalate the specific item to the user instead of forcing the rest).
4. Pastes the "IDRs to merge" section into `IMPL-IDR-*.md`.
5. Runs each entry from `proposed_meta_ops`.
6. Re-enters Stage 3 (`review`) with a fresh subagent and a fresh report path.

Loop until the review report has only escalation-level items or is empty. Only then run `artifact.py approve` on each of the four Impl sections.
