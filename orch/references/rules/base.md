# Base Rules — Common Behaviour for All Spawned Skills

These rules apply to every content skill spawned by orch. They are injected into the skill's context at spawn time.

## You are running inside an orchestrated pipeline

You have been spawned by the orch skill as part of a managed run. This means:

1. **Write artifacts to `HARNESS_ARTIFACTS_DIR`**. This environment variable points to your skill-specific output directory within the run tree (e.g., `harness-output/runs/20260412-103000-a1b2/arch/`). Do not write to `./artifacts/<skill>/` — that path is for standalone (non-orch) usage.

2. **Use `HARNESS_RUN_ID`** in any logs or references where a run identifier is useful. This is the ID of the current orchestrated run.

3. **Follow your SKILL.md as normal**. Orch does not change how your skill works — it only sets where artifacts go and provides upstream context. Your workflow stages, adaptive depth rules, and script contracts all apply unchanged.

## Artifact format compliance

Every artifact you produce must be a pair:
- `<id>.meta.yaml` — structured metadata (phase, approval, traceability). Only modify via your `scripts/artifact.py`.
- `<id>.md` — human-readable content. Edit directly using templates from `assets/templates/`.

The metadata file is the single source of truth. The markdown is the human-readable rendering.

## Upstream traceability

You will receive upstream artifact references from orch (the outputs of skills that ran before you in the pipeline). For every artifact you create:

1. Link to relevant upstream artifacts:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py link <your-id> --upstream <upstream-id>
   ```
2. Reference upstream IDs in your markdown content where appropriate (e.g., "This decision is driven by RE-QA-001")

Traceability is not optional — it is how the pipeline maintains coherence from requirements through verification.

## Escalation protocol

If you encounter a situation where you cannot proceed without user input, signal `needs_user_input`. Orch's relay stage will mediate the conversation. See the escalation protocol reference for details on when and how to signal.

Do not attempt to interact with the user directly in ways that bypass orch's relay mechanism. Your output should be artifacts and, when necessary, structured escalation signals.

## Completion protocol

When your assigned stage is complete:

1. Ensure all artifacts are written to `HARNESS_ARTIFACTS_DIR`
2. Ensure all `.meta.yaml` files are in the correct phase (typically `in_review` or `approved`)
3. Ensure all upstream links are recorded
4. Return a summary of what you produced: artifact IDs, phase states, and any issues encountered
