# Artifact Templates

Every skill agent produces a **pair** of files:

- `meta.json` — structured metadata: progress, approval, refs, and a
  skill-specific `data` payload. Mutated only via `scripts/artifact`.
- `body.md` — human-readable narrative (analysis, prose, diagrams).
  Scaffolded from a per-agent template in this directory and then edited
  by the agent with its normal Read/Edit tools.

Both files live under:

```
runs/<run_id>/<skill>/<agent>[-NN]/
```

## `meta.json` schema (v1)

```json
{
  "schema_version": 1,
  "artifact_id": "<skill>-<agent>-NN",
  "run_id": "YYYYMMDD-HHMMSS-<slug>",
  "skill": "arch",
  "agent": "design",
  "title": "…",
  "template": "arch/design",
  "body_path": "body.md",
  "created_at": "ISO-8601 UTC",
  "updated_at": "ISO-8601 UTC",
  "progress": "draft|in_progress|review|approved|rejected|blocked",
  "approval": {
    "verdict": null,
    "approver": null,
    "approved_at": null,
    "notes": null
  },
  "refs": {
    "re_refs": [],
    "upstream": [],
    "downstream": []
  },
  "data": {}
}
```

- `approval.verdict` ∈ `null | APPROVED | CONDITIONAL | REJECTED`
- `data` is the skill/agent-specific extension point. Its shape mirrors the
  `output:` block in the owning skill's `skills.yaml`. Agents push payloads
  via `artifact set --data-file patch.json`.

## Template contract

Every template in this directory is a markdown skeleton. At scaffold time,
`scripts/artifact init` substitutes the following placeholders:

- `{{title}}`
- `{{artifact_id}}`
- `{{run_id}}`
- `{{skill}}`
- `{{agent}}`

Body files should narrate: context, analysis, rationale, trade-offs, and
diagrams. **Do not** duplicate structured data already stored in
`meta.json.data`; link to it instead.

## CLI quick reference

```
scripts/artifact init --skill arch --agent design --title "Checkout redesign"
scripts/artifact path  <artifact_id> --run-id <id> --body
scripts/artifact get   <artifact_id> --run-id <id> [--field approval.verdict]
scripts/artifact set   <artifact_id> --run-id <id> --progress review
scripts/artifact set   <artifact_id> --run-id <id> --verdict APPROVED --approver lead
scripts/artifact list  [--run-id <id>] [--skill arch] [--progress review]
scripts/artifact validate <artifact_id> --run-id <id>
```
