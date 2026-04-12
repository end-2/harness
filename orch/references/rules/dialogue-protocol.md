# Dialogue Protocol — Signal Structure for User Communication

This protocol defines the exact structure of `needs_user_input` and `user_response` signals used for skill-user communication through orch's relay stage.

## `needs_user_input` signal (skill -> orch)

```yaml
needs_user_input:
  # Required fields
  skill: "arch"                    # Which skill is asking
  agent: "design"                  # Which agent within the skill
  step_index: 3                    # Pipeline step index
  question_type: "choice"          # open | choice | confirmation
  question: "Which deployment model fits your constraints?"

  # Conditional fields
  choices:                         # Required for question_type: choice
    - label: "Monolith"
      description: "Single deployable unit. Simpler operations, lower initial complexity."
    - label: "Modular monolith"
      description: "Logical module separation, single deployment. Good balance of structure and simplicity."
    - label: "Microservices"
      description: "Independent services. Maximum flexibility, higher operational complexity."

  # Optional fields
  context: "Based on RE-QA-001 (scalability) and CON-002 (team size: 3 developers), I need to choose an architecture style."
  default: "Modular monolith"      # Used when user skips
  urgency: "normal"                # normal | high
  metadata:                        # Any additional structured data the skill needs to pass
    related_artifacts: ["RE-QA-001", "RE-CON-002"]
    current_phase: "design"
```

### Validation rules for the signal

- `skill` and `agent` must match the currently executing step
- `question_type` must be one of: `open`, `choice`, `confirmation`
- `question` must be a non-empty string
- `choices` must be present and non-empty when `question_type` is `choice`
- Each choice must have a `label` (and optionally `description`)

## `user_response` signal (orch -> skill)

```yaml
user_response:
  # For open questions
  answer: "Let's go with a modular monolith. Our team is small and we want to keep ops simple."

  # For choice questions
  choice_index: 1                  # 0-based index into the choices array
  answer: "Modular monolith"       # Also include the label for readability

  # For confirmation questions
  answer: "approved"               # or "rejected" or free text explaining the decision

  # Common fields
  skipped: false                   # true if user said "skip" / "use default"
  conversation_summary: |
    Turn 1: Discussed deployment model. User chose modular monolith
    citing small team size (3 devs) and desire for simple operations.
```

### Response interpretation rules

| question_type | User input | Response mapping |
|---------------|-----------|------------------|
| open | Free text | `answer: <text>` |
| choice | Number (1-based from user, converted to 0-based) | `choice_index: N-1, answer: <label>` |
| choice | Label text | `choice_index: <matching index>, answer: <text>` |
| choice | Free text not matching a choice | `answer: <text>` (skill should interpret) |
| confirmation | "yes" / "ok" / "approve" | `answer: "approved"` |
| confirmation | "no" / "reject" | `answer: "rejected"` |
| confirmation | Free text | `answer: <text>` (skill should interpret) |
| any | "skip" / "default" | `skipped: true` |

## Conversation summary format

The `conversation_summary` field provides context continuity across relay rounds. It is a condensed history of the dialogue so far, written from the user's perspective.

Format: one line per turn, prefixed with the turn number.

```
Turn 1: User wants a web-based SaaS for project management
Turn 2: Target audience is small teams (5-20 people). Must support Kanban and Gantt views.
Turn 3: User chose PostgreSQL for data store. Budget is free-tier cloud (AWS/GCP).
Turn 4: User confirmed 3-person dev team, all full-stack JS/TS. No Kubernetes experience.
```

The summary should capture **decisions made**, not questions asked. Keep each line under 120 characters. When the summary exceeds 10 lines, compress older turns into a single "Context established" line and keep the recent 5-7 turns detailed.

## Error signals

If a skill encounters an error that prevents it from continuing (not a user-input need), it should return an error instead of `needs_user_input`:

```yaml
skill_error:
  skill: "impl"
  agent: "generate"
  step_index: 4
  error_type: "missing_upstream"   # missing_upstream | invalid_state | tool_failure | timeout
  message: "Cannot find approved ARCH-DEC artifacts in the upstream path"
  recoverable: true                # Can the pipeline retry after fixing?
  suggestion: "Ensure arch:design has completed and artifacts are approved"
```
