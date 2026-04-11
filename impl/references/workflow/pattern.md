# Workflow — Stage 2: pattern

## Role

Evaluate pattern-application opportunities in the code written by `generate`, apply the ones that earn their keep, and record each application as an IDR in the Implementation Decisions section.

## Two classes of patterns

### Mandatory — named in Arch

If `ARCH-DEC-*` explicitly names a pattern (e.g. "hexagonal ports-and-adapters", "repository per aggregate", "event sourcing for the orders service"), that pattern **must** be visible in the code. Apply it mechanically. Record the application as an IDR that cites the ADR:

```
python ${CLAUDE_SKILL_DIR}/scripts/artifact.py link <impl-idr-id> --upstream ARCH-DEC-002
```

If applying the pattern is impossible in the chosen stack, this is an Arch-contract conflict — escalate instead of silently skipping.

### Discretionary — not named in Arch

For patterns not named in Arch, apply them only when the problem shape clearly matches. Judgement, not reflex. Concrete triggers:

| Pattern | Trigger |
|---------|---------|
| **Repository** | Data access code leaks into business logic, or the same query shape appears in more than one module |
| **Factory** | Object creation logic is duplicated, or construction needs to vary by configuration |
| **Strategy** | A long `if/elif` or `switch` on a type-flag field; two or more behaviours that are selected at runtime |
| **Adapter** | An external library's interface does not match the shape Arch interfaces want |
| **Observer / Publisher-Subscriber** | Cross-component notifications that must not introduce a hard dependency |
| **Decorator** | Cross-cutting concerns (logging, retries, caching) that would otherwise duplicate across call sites |
| **Template Method** | Multiple implementations share the same skeleton with a few variation points |

Do **not** apply a pattern just because it is well-known. Over-application is a failure mode: an unnecessary `Factory` for an object that only gets constructed in one place is a debt, not an asset. When you *consider* a pattern and reject it, it is useful to note that rejection in the IDR too — future maintainers benefit from knowing a pattern was considered and why it was turned down.

## Anti-patterns

As you walk through the code from `generate`, also look for:

- **God objects** — a class that owns more than one Arch component's responsibility. Split it.
- **Shotgun surgery** — a single logical change that forces edits in many files. Extract or consolidate.
- **Feature envy** — a method that reaches into another object's fields more than its own. Move it.
- **Primitive obsession** — a string or integer that carries a semantic meaning across many functions. Introduce a value type.

Treat anti-pattern removal as a pattern application: apply the fix, write an IDR that describes the smell and the fix.

## Recording an IDR

Use the Implementation Decisions section (`IMPL-IDR-*`) written by `generate`. For each pattern applied or rejected:

1. Add an IDR block to the markdown with id, title, decision, rationale, alternatives, `pattern_applied`, and refs.
2. `artifact.py set-progress <impl-idr-id> --completed N --total M` as IDR count grows.
3. `artifact.py link <impl-idr-id> --upstream <arch-or-re-ref>` for every anchor.
4. Keep phase at `in_review` throughout.

## Escalation

No user escalation in this stage. Arch-mandated patterns are mandatory; discretionary patterns are a judgement call for the agent and are fully recorded in IDRs for later review.
