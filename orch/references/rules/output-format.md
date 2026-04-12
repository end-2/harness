# Output Format Rules — Artifact Structure Convention

These rules define the standard format for all artifacts produced within an orchestrated run.

## File pair convention

Every artifact consists of two files:

| File | Format | Purpose | Who edits |
|------|--------|---------|-----------|
| `<id>.meta.yaml` | YAML | Structured metadata: phase, approval, progress, traceability refs, timestamps | Only `scripts/artifact.py` |
| `<id>.md` | Markdown | Human-readable content: the actual deliverable | The skill agent, using Edit |

The metadata file name is always `<id>.meta.yaml` where `<id>` matches the `artifact_id` field inside the YAML.

## Metadata header fields (common across all skills)

```yaml
artifact_id: ARCH-DEC-001
section: decisions
phase: draft                    # draft | in_review | revising | approved | superseded
progress:
  completed: 3
  total: 5
approval:
  state: pending                # pending | approved | rejected | changes_requested
  approver: null
  approved_at: null
  history: []
upstream_refs: [RE-QA-001, RE-CON-002]
downstream_refs: [IMPL-MAP-001]
document_path: ARCH-DEC-001.md
created_at: "2026-04-12T10:30:00Z"
updated_at: "2026-04-12T10:42:15Z"
```

## Markdown document structure

Every `.md` artifact follows this structure:

```markdown
# <Section Title>

> Artifact: <id> | Phase: <phase> | Run: <run_id>

## <Subsection 1>
...content...

## <Subsection 2>
...content...
```

The header line (artifact ID, phase, run ID) helps humans orient themselves when reading artifacts outside of orch's context.

## Section counts per skill

Each skill produces a fixed number of section artifacts:

| Skill | Sections | Count |
|-------|----------|-------|
| ex | structure-map, tech-stack, component-relations, architecture-inference | 4 |
| re | requirements, constraints, quality-attributes | 3 |
| arch | decisions, components, tech-stack, diagrams | 4 |
| impl | implementation-map, code-structure, implementation-decisions, implementation-guide | 4 |
| qa | strategy, tests, traceability, report | 4 |
| sec | threat-model, vulnerabilities, recommendations, compliance | 4 |
| devops | pipeline, iac, observability, runbooks | 4 |
| verify | environment, scenario, report | 3 |

## Reports directory

Subagent handoff reports go to `<HARNESS_ARTIFACTS_DIR>/.reports/`. These are internal working files (not final artifacts) used by the skill's main agent to integrate subagent outputs. They follow the subagent report contract defined in each skill's `references/contracts/subagent-report-contract.md`.
