# Config Stage — Settings and Template Management

The config stage handles configuration changes that affect how orch operates. It activates when the user requests changes to output paths, skill settings, or pipeline templates.

## Configurable settings

### Output root path

The base directory for all run output. Default: `./harness-output/`

```
User: "save output to ./my-project-output/"
Action: Set HARNESS_OUTPUT_ROOT or pass --output-root to run.py commands
```

The output root applies to all subsequent runs. Existing runs stay in their original location.

### Skill enable/disable

Users can disable skills they don't need, preventing them from appearing in pipeline execution:

```
User: "skip security checks" or "disable sec"
Action: Record in pipeline.meta.yaml that sec is disabled
Effect: Pipeline steps involving sec are auto-marked as skipped
```

Disabling a skill does not delete it — it just skips it in pipeline execution. The user can re-enable at any time.

### Pipeline template customisation

Users can modify predefined pipelines or create custom ones:

```
User: "I want full-sdlc but without devops"
Action: Create a custom pipeline based on full-sdlc minus the devops step
```

Custom pipelines are stored in `pipeline.meta.yaml` under `custom_pipelines`.

## Configuration storage

Settings are stored in `<output-root>/pipeline.meta.yaml`:

```yaml
output_root: ./harness-output/
disabled_skills: []
custom_pipelines:
  my-pipeline:
    steps:
      - {skill: re, agent: elicit}
      - {skill: re, agent: spec}
      - {skill: arch, agent: design}
      - {skill: impl, agent: generate}
default_pipeline: full-sdlc
```

## Config operations

| User request | Action |
|-------------|--------|
| "set output to X" | Update `output_root` in pipeline.meta.yaml |
| "disable <skill>" | Add skill to `disabled_skills` |
| "enable <skill>" | Remove skill from `disabled_skills` |
| "create pipeline <name> with <skills>" | Add to `custom_pipelines` |
| "delete pipeline <name>" | Remove from `custom_pipelines` (predefined ones cannot be deleted) |
| "set default pipeline to <name>" | Update `default_pipeline` |
| "show config" | Print current configuration |
| "reset config" | Restore defaults |

## Validation

After any config change, validate:

1. Output root path exists (or can be created) and is writable
2. Disabled skills don't break pipeline dependencies (warn if e.g. disabling `arch` in `full-sdlc`)
3. Custom pipeline steps reference valid skills and agents
4. No circular dependencies in custom pipelines
