# Config Stage - Settings and Template Management

The config stage handles configuration changes that affect how orch operates. It activates when the user requests changes to output paths, skill settings, or pipeline templates.

Keep this stage conservative. Orch may read `pipeline.meta.yaml` for defaults, but it should not promise a persistent config mutation unless the required file or command path is available in the current runtime.

## Configurable settings

### Output root path

The base directory for all run output. Default: `./harness-output/`

```
User: "save output to ./my-project-output/"
Action: Set `HARNESS_OUTPUT_ROOT` or pass `--output-root` to `run.py` commands
```

The output root applies to all subsequent runs. Existing runs stay in their original location.

### Skill enable/disable

Users can disable skills they do not need, preventing them from appearing in pipeline execution:

```
User: "skip security checks" or "disable sec"
Action: Record the preference and, if persistent config editing is supported in the current runtime, update `pipeline.meta.yaml`
Effect: Pipeline steps involving sec can be skipped in future runs
```

Disabling a skill does not delete it - it just skips it in pipeline execution. The user can re-enable it at any time.

### Pipeline template customisation

Users can modify predefined pipelines or create custom ones:

```
User: "I want full-sdlc but without devops"
Action: Create or update a custom pipeline entry only if persistent config editing is available
```

Custom pipelines, when present, are stored in `pipeline.meta.yaml` under `custom_pipelines`. `run.py init-run` can execute them once they exist.

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
| "set output to X" | Use `--output-root` for the active run; persist only if config editing is available |
| "disable <skill>" | Record the preference and persist only if config editing is available |
| "enable <skill>" | Remove the preference and persist only if config editing is available |
| "create pipeline <name> with <skills>" | Add a `custom_pipelines` entry only when a safe write path exists |
| "delete pipeline <name>" | Remove a `custom_pipelines` entry only when a safe write path exists |
| "set default pipeline to <name>" | Update `default_pipeline` only when a safe write path exists |
| "show config" | Print current configuration from `pipeline.meta.yaml` if present |
| "reset config" | Restore defaults only when a safe write path exists |

## Validation

After any config change, validate:

1. Output root path exists (or can be created) and is writable
2. Disabled skills don't break pipeline dependencies (warn if e.g. disabling `arch` in `full-sdlc`)
3. Custom pipeline steps reference valid skills and agents
4. No circular dependencies in custom pipelines
