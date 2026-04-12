# Stage 4 — Map: Detailed Behavior Rules

## Purpose

Integrate the results from Stages 1-3 into the final 4-section output, apply token budget management, create artifact pairs from templates, fill in the markdown bodies, register downstream injection references, and present the results to the user.

## Prerequisites

All three prior stages must be complete:
- Stage 1 (scan): directory tree, file classification, entry points, config files, depth mode
- Stage 2 (detect): technology stack list with evidence
- Stage 3 (analyze): component list, architecture inference, cross-cutting concerns

## Execution sequence

### 1. Apply token budget

The target token budget (default 4000, overridable with `--budget`) constrains how much detail the final output contains. Apply these compression strategies in priority order:

Read [references/token-budget.md](../token-budget.md) for the full rule set. Summary:

1. **Priority-based selection**: entry points/APIs > component structure > tech stack > detailed dependencies
2. **Repetitive pattern grouping**: `components/{Header,Footer,Nav,...12 more}/index.tsx`
3. **Hierarchical detail**: important modules get full detail; utilities and configs get one-line summaries
4. **Threshold truncation**: if a list exceeds N items, show top items + "... and M more"

Estimate the token count of each section draft. If the total exceeds the budget, compress the lowest-priority sections first.

### 2. Create artifact pairs

Initialize all four sections from templates using `artifact.py`:

```bash
python ${SKILL_DIR}/scripts/artifact.py init --section structure-map
python ${SKILL_DIR}/scripts/artifact.py init --section tech-stack
python ${SKILL_DIR}/scripts/artifact.py init --section components
python ${SKILL_DIR}/scripts/artifact.py init --section architecture
```

Each call copies the template pair from `assets/templates/` into the artifacts directory and returns the generated `artifact_id`. Record all four IDs.

### 3. Fill markdown bodies

For each section, edit **only the `.md` file** (never the `.meta.yaml`). Fill in the template placeholders with the analysis results:

**structure-map.md**: Populate from Stage 1 output.
- Overview: project root, file count, depth mode
- Directory tree: the compressed tree representation
- File classification table: counts and examples per category
- Entry points table: file, role, evidence
- Config files table: file, role, evidence
- Ignored patterns list

**tech-stack.md**: Populate from Stage 2 output.
- Overview: technology count, dominant language
- Languages table: sorted by file count (primary first)
- Frameworks table: with role and evidence
- Databases table: with access pattern
- Build tools, testing, CI/CD tables
- Technology relationships

**components.md**: Populate from Stage 3 output.
- Overview: component count, dominant patterns
- Component cards: one per component with all fields
- Mermaid dependency graph
- API surfaces table
- Circular dependencies (if any)
- Cross-cutting concerns table

**architecture.md**: Populate from Stage 3 output.
- Overview: inferred style and confidence
- Architecture style with evidence
- Layer structure (if detected)
- Communication patterns
- Data stores
- Cross-cutting concerns
- Test patterns
- Build/deploy patterns
- Token budget summary: target, actual, compressions applied

### 4. Cross-section consistency check

Before finalizing, verify:
- Component IDs referenced in `architecture.md` exist in `components.md`
- Technology IDs referenced in `components.md` exist in `tech-stack.md`
- File paths referenced across sections are consistent
- Entry points listed in `structure-map.md` appear as components or within components

Fix any inconsistencies before proceeding.

### 5. Update metadata through scripts

For each of the four artifact IDs:

```bash
# Update progress
python ${SKILL_DIR}/scripts/artifact.py set-progress <id> --completed 1 --total 1

# Transition to in_review
python ${SKILL_DIR}/scripts/artifact.py set-phase <id> in_review

# Register downstream injection targets
python ${SKILL_DIR}/scripts/artifact.py link <id> --downstream re
python ${SKILL_DIR}/scripts/artifact.py link <id> --downstream arch
python ${SKILL_DIR}/scripts/artifact.py link <id> --downstream impl
python ${SKILL_DIR}/scripts/artifact.py link <id> --downstream qa
python ${SKILL_DIR}/scripts/artifact.py link <id> --downstream sec
```

The specific downstream links per section are defined in [references/contracts/downstream-injection-contract.md](../contracts/downstream-injection-contract.md). Not every section links to every downstream skill — follow the contract.

### 6. Final validation

Run:
```bash
python ${SKILL_DIR}/scripts/artifact.py validate
```

Confirm zero validation errors before reporting to the user.

### 7. Report to user

Present a concise summary:

1. **Depth mode**: which was selected (lite/heavy) and why (the metrics)
2. **Key findings**: dominant language, architecture style, notable patterns, any concerns (circular deps, missing tests, etc.)
3. **Output paths**: absolute paths to all 8 files (4 `.md` + 4 `.meta.yaml`)
4. **Next steps**: which downstream skills can now consume this context, with suggestions:
   - "Run `re` to define requirements in the context of this codebase"
   - "Run `arch` to review or extend the architecture"
   - "Run `sec` to perform a security audit with the component map as input"
   - "Run `qa` to plan tests based on detected patterns"

Keep the summary concise. The detailed analysis lives in the artifacts.

## Script usage reminders

- **All metadata changes** go through `${SKILL_DIR}/scripts/artifact.py`. Never edit `*.meta.yaml` directly.
- **Markdown bodies** are the only files you edit directly, and only within the scaffolding from templates.
- Use `artifact.py show <id>` if you need to inspect metadata state.
- Use `artifact.py validate` to confirm everything is clean before reporting.
