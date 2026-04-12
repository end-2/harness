# Escalation Protocol — When and How to Signal `needs_user_input`

This protocol defines when skills should escalate to the user via orch's relay mechanism, and when they should proceed autonomously.

## Skill categorisation

Skills fall into two categories based on their interaction model:

### Dialogue skills (frequent escalation expected)

These skills are inherently interactive — their job involves surfacing information the user must decide on:

| Skill:Agent | Typical escalation points |
|-------------|--------------------------|
| re:elicit | Every requirement area: "What are your functional needs for X?" |
| re:analyze | Conflicts or ambiguities in requirements |
| re:spec | Prioritisation of quality attributes |
| re:review | Review findings that need user judgment |
| arch:design | Technical context gaps, architecture style choice, component trade-offs |
| sec:threat-model | Risk acceptance decisions, compliance scope |

For dialogue skills, escalation is the **normal operating mode**. Signal `needs_user_input` at every semantic boundary — each distinct question or decision point. Do not batch multiple unrelated questions into one signal.

### Automatic skills (rare escalation expected)

These skills normally run to completion without user interaction:

| Skill:Agent | Escalation only when |
|-------------|---------------------|
| ex:* | Ambiguous project structure, cannot determine entry points |
| impl:generate | Upstream architecture is ambiguous, multiple valid implementations |
| qa:generate | Cannot derive test scenarios from upstream artifacts |
| sec:audit | Critical vulnerability found that requires immediate decision |
| sec:compliance | Compliance framework selection needed |
| devops:pipeline | Deployment target ambiguous |
| verify:* | Environment cannot start, upstream artifacts contradictory |

For automatic skills, escalation is **exceptional**. Only signal `needs_user_input` when:
1. A required upstream artifact is missing or contradictory
2. Multiple valid approaches exist and the choice has significant downstream impact
3. A critical finding requires immediate user attention (e.g., security vulnerability)
4. The environment or tooling is unavailable

## Signal structure

When signalling `needs_user_input`, include:

```yaml
needs_user_input:
  question_type: open | choice | confirmation
  question: "Clear, specific question"
  context: "What you're working on and why you need this answer"
  choices: []           # for choice type: list of {label, description}
  default: ""           # optional: what to use if user skips
  urgency: normal | high  # high = blocks further progress entirely
```

### Question types

- **open**: Free-text answer needed. Use for gathering requirements, technical context, or preferences.
- **choice**: Select from predefined options. Use when you've narrowed it down to specific alternatives.
- **confirmation**: Yes/no approval. Use for validating a proposed approach before committing.

## What NOT to escalate

Do not signal `needs_user_input` for:

- Decisions within your skill's documented scope and rules
- Standard template or format choices already defined by your SKILL.md
- Information already available in upstream artifacts
- Progress updates (just write them to the artifact)
- Technical implementation details that have a single obvious answer
