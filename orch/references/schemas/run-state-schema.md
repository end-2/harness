# Run State Schema — `run.meta.yaml`

Defines the structure of the canonical run state file.

## Top-level fields

```yaml
# Required
run_id: "20260412-103000-a1b2"        # Format: YYYYMMDD-HHmmss-<4hex>
pipeline: "full-sdlc"                  # Pipeline name or "single:<skill>:<agent>"
output_root: "./harness-output/"       # Absolute or relative path
status: "running"                      # pending | running | paused | completed | failed | cancelled
created_at: "2026-04-12T10:30:00Z"    # ISO 8601 UTC
updated_at: "2026-04-12T10:42:15Z"    # ISO 8601 UTC, auto-updated by run.py

# Optional (populated during/after execution)
ended_at: "2026-04-12T11:15:00Z"      # Set on complete/cancel

# Required collections
steps: []                              # Pipeline step definitions (see below)
dialogue_history: []                   # Conversation summary per step
errors: []                             # Error records
```

## Status transitions

```
pending --> running --> completed
    |          |
    |          +--> paused --> running
    |          |
    |          +--> failed --> running (retry)
    |          |
    |          +--> cancelled
    |
    +--> cancelled
```

## Step schema

Each entry in `steps[]`:

```yaml
index: 0                           # Position in the pipeline
skill: "arch"                      # Skill ID
agent: "design"                    # Agent within the skill
status: "completed"                # pending | running | completed | failed | skipped
parallel_group: "post-impl"       # Optional: group name for parallel execution
artifacts: ["ARCH-DEC-001"]        # Artifact IDs produced by this step
updated_at: "2026-04-12T10:35:00Z" # Last state change timestamp
```

### Step status transitions

```
pending --> running --> completed
    |          |
    |          +--> failed --> running (retry)
    |
    +--> skipped
```

## Dialogue history entry

Each entry in `dialogue_history[]`:

```yaml
step_index: 3
skill: "arch"
agent: "design"
turn: 1
summary: "User chose PostgreSQL over MongoDB, citing team expertise"
timestamp: "2026-04-12T10:36:00Z"
```

## Error entry

Each entry in `errors[]`:

```yaml
type: "step_failure"           # step_failure | cancellation | validation_error | timeout
step_index: 5                  # Optional: which step failed
skill: "qa"                    # Optional: which skill
message: "QA generation failed: missing upstream IMPL artifacts"
timestamp: "2026-04-12T10:50:00Z"
reason: ""                     # For cancellation type
```

## Validation rules

1. `run_id` must match `YYYYMMDD-HHmmss-[a-f0-9]{4}` pattern
2. `pipeline` must be a known pipeline name or match `single:<skill>[:<agent>]`
3. `status` must be one of the defined values
4. `steps` must be a non-empty list of valid step objects
5. Each step's `skill` must be a registered skill ID
6. Step indices must be sequential starting from 0
7. No two steps in the same parallel group can reference the same skill (conflict risk)
8. `created_at` and `updated_at` must be valid ISO 8601 UTC timestamps
9. If `status` is `completed` or `cancelled`, `ended_at` must be present
