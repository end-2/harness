# Pipeline Schema — `pipeline.meta.yaml`

Defines the structure of the orch-level pipeline configuration file, stored at `<output-root>/pipeline.meta.yaml`.

## Top-level fields

```yaml
# Configuration
output_root: "./harness-output/"       # Default output root path
disabled_skills: []                    # List of skill IDs to skip in pipeline execution
default_pipeline: "full-sdlc"         # Pipeline used when user doesn't specify

# Custom pipelines (user-defined)
custom_pipelines:
  my-pipeline:
    description: "Custom pipeline for my workflow"
    steps:
      - {skill: re, agent: elicit}
      - {skill: arch, agent: design}
      - {skill: impl, agent: generate}

# State tracking
active_run: null                       # Current active run ID, or null if idle
updated_at: "2026-04-12T10:00:00Z"    # ISO 8601 UTC
```

## Custom pipeline step schema

Each step in a custom pipeline:

```yaml
skill: "arch"                     # Required: skill ID
agent: "design"                   # Optional: specific agent (defaults to skill's primary)
parallel_group: "group-name"      # Optional: group name for parallel execution
```

## Predefined pipelines

These are built into `run.py` and cannot be modified or deleted through config:

- `full-sdlc`
- `full-sdlc-existing`
- `new-feature`
- `new-feature-existing`
- `security-gate`
- `security-gate-existing`
- `quick-review`
- `explore`
- `integration-verify`
- `integration-verify-existing`

## Validation rules

1. `disabled_skills` entries must be valid skill IDs
2. `default_pipeline` must be a predefined or custom pipeline name
3. Custom pipeline steps must reference valid skills
4. Custom pipelines cannot use the same name as a predefined pipeline
5. A custom pipeline must have at least one step
6. `active_run` must be null or a valid run ID
