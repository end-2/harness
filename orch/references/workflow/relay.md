# Relay Stage — User-Skill Dialogue Mediation

The relay stage mediates communication between a running skill and the user. It activates when a skill signals `needs_user_input` during pipeline execution.

## When relay activates

A skill signals `needs_user_input` when it needs information that only the user can provide. This happens in two contexts:

1. **Dialogue skills** (re:elicit, re:analyze, re:spec, arch:design): These are inherently interactive — they surface requirements, explore trade-offs, and refine designs through conversation. `needs_user_input` is their primary operating mode.

2. **Automatic skills** (ex, impl, qa, sec, devops, verify): These normally run without interaction but may escalate when they encounter ambiguity, missing context, or decisions that exceed their scope.

## Signal structure

### `needs_user_input` (from skill to orch)

```yaml
needs_user_input:
  skill: arch
  agent: design
  step_index: 3
  question_type: open | choice | confirmation
  question: "Human-readable question text"
  choices:              # only for question_type: choice
    - label: "Option A"
      description: "..."
    - label: "Option B"
      description: "..."
  context: "Brief context about what the skill is working on"
  default: "Default answer if user skips"  # optional
```

### `user_response` (from orch back to skill)

```yaml
user_response:
  answer: "The user's answer text"
  choice_index: 0       # only for question_type: choice
  skipped: false        # true if user said "skip" or "use default"
  conversation_summary: "Brief summary of dialogue so far for context continuity"
```

## Relay behaviour

### Presenting questions to the user

Transform the structured `needs_user_input` signal into natural conversation:

- **open**: Present the question directly. Include the context so the user understands what the skill needs.
- **choice**: Present numbered options with descriptions. Example:
  ```
  The architecture skill needs your input:

  Which deployment model fits your team?
  1. Monolith — single deployable, simpler ops
  2. Modular monolith — logical separation, single deploy
  3. Microservices — independent services, complex ops

  (Type a number, or explain your preference)
  ```
- **confirmation**: Present as a yes/no with context. Example:
  ```
  The architecture skill proposes using PostgreSQL for the primary datastore
  (driven by your requirement for ACID transactions and the team's existing expertise).

  Approve? (yes/no/suggest alternative)
  ```

### Interpreting user responses

| User says | Interpretation |
|-----------|---------------|
| A number (1, 2, 3) | Choice selection → `choice_index` |
| "yes", "ok", "approve", "looks good" | Confirmation → `answer: "approved"` |
| "no", "reject", "change" | Rejection → `answer: "rejected"` |
| "skip", "default", "whatever" | Skip → `skipped: true`, use `default` if available |
| Free text | Open answer → `answer: <text>` |
| "back", "redo", "wait" | Pause → do not send response yet, ask for clarification |

### Conversation summary

Maintain a running summary of the dialogue for context continuity. After each relay round:

1. Append a one-line summary to the run's `dialogue_history` in `run.meta.yaml`
2. Include a condensed conversation summary in the `user_response` so the skill can maintain context without re-reading the full history

Format:
```
Step 3 (arch:design) Turn 1: User chose PostgreSQL over MongoDB, citing team expertise
Step 3 (arch:design) Turn 2: User confirmed microservices architecture for the auth and billing domains
```

## Multi-turn dialogue

Some skills (especially re and arch) require multiple rounds of dialogue. Relay handles this as a loop:

```
while skill has not completed:
    receive needs_user_input from skill
    present to user
    collect user response
    package as user_response
    send back to skill
    update dialogue_history
```

The pipeline stage manages this loop — relay is stateless and handles one round at a time.

## Error cases

| Situation | Action |
|-----------|--------|
| User wants to abort the dialogue | Send `user_response` with `answer: "abort"`. The skill should gracefully save progress and exit. |
| User wants to skip the entire skill | Mark the step as `skipped` via `run.py update-state`. Proceed to next step. |
| Skill sends malformed signal | Log the error, ask the user to interpret what the skill needs |
| User response is ambiguous | Ask for clarification before sending to the skill |
