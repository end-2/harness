# Workflow — Stage 4: refactor

## Role

Take the review report's auto-fixable issue list and transform the code to resolve them, without crossing Arch component boundaries. This stage **runs in a subagent**, so it focuses only on the issue list and the current source tree.

## Inputs to the subagent

- The review report produced by Stage 3.
- The current source tree.
- The four Impl section artifacts (for traceability updates).
- The four Arch artifacts (to enforce boundary respect).

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

1. **One change at a time.** Do not batch unrelated refactors into a single step.
2. **Preserve behaviour.** Never introduce new features or fix unrelated bugs while refactoring.
3. **Respect boundaries.** Before every edit, check the target file's Arch component via its `IMPL-MAP-*` entry. If the edit would cross the boundary, stop and escalate.
4. **Keep the build green.** After each step, the code must still compile / type-check. Do not leave half-migrated state.
5. **Update traceability immediately.** If a refactor moves a file, update the relevant `IMPL-MAP-*` entry's `internal_structure` and re-run:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/artifact.py set-progress <impl-map-id> --completed N --total M
   ```

## Recording the refactor

For each non-trivial refactor (anything more than a rename or a constant extraction), add an IDR block to the Implementation Decisions section:

- Title: "Refactor: <what changed>"
- Decision: the refactor name from Fowler's catalogue.
- Rationale: the review finding (severity + location) that triggered it.
- Refs: link upstream to the review finding's Arch ref if any:
  ```
  python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link <impl-idr-id> --upstream ARCH-DEC-002
  ```

Trivial refactors (rename a local variable, fix a magic number) can live in code only.

## Output

Return to the main agent:

1. The code changes (as a patch or as a list of file edits the main agent can Apply).
2. A diff-ready summary of IDR additions for the Implementation Decisions markdown.
3. Any issues that turned out to require boundary crossings and need escalation.

## Hand-off back to review

After the main agent applies the refactor subagent's output, re-enter Stage 3 (`review`) with a fresh subagent. Loop until the review report has only escalation-level items or is empty. Only then run `artifact.py approve` on each of the four Impl sections.
