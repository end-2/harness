# Token Budget Management

The final 4-section output from Ex must fit within a token budget (default 4000, configurable with `--budget`). This document defines how to maximize information density within the budget.

## Priority hierarchy

When the budget is tight, compress or omit lower-priority information first:

| Priority | Content | Rationale |
|----------|---------|-----------|
| **P0 (never cut)** | Entry points, API surfaces, architecture style | These are the first things downstream skills need |
| **P1 (compress last)** | Component boundaries, primary tech stack, layer structure | Core structural understanding |
| **P2 (compress early)** | Internal dependency details, secondary tech stack items, test patterns | Useful but reconstructable |
| **P3 (omit if needed)** | Detailed config file listings, exhaustive pattern catalogs, build tool versions | Nice to have, easy to look up |

## Compression techniques

### 1. Repetitive pattern grouping

When multiple files share a structure, group them:

```
# Before (wasteful)
src/components/Header/index.tsx
src/components/Footer/index.tsx
src/components/Nav/index.tsx
src/components/Sidebar/index.tsx
... (15 more)

# After (compressed)
src/components/{Header,Footer,Nav,Sidebar,...15 more}/index.tsx
```

### 2. Directory summary

For large directories, show count instead of listing:

```
# Before
migrations/
  001_init.sql
  002_add_users.sql
  ... (45 more)

# After
migrations/ (47 SQL files)
```

### 3. Table truncation

For tables with many rows, show the most important entries and summarize the rest:

```markdown
| ID | Name | Role |
|----|------|------|
| TS-001 | TypeScript | Primary language |
| TS-002 | Next.js | Web framework |
| TS-003 | Prisma | ORM |
| ... | *7 more technologies* | *build tools, linters, formatters* |
```

### 4. Hierarchical detail

- **Core components**: full detail (all fields in the component card)
- **Utility components**: one-line summary (`utils/ — 12 helper modules for string, date, validation`)
- **Test components**: mention existence and framework, skip listing individual test files

### 5. Section-level compression

If severely over budget:
1. Merge "Build & Development Tools" into a single line in tech stack
2. Collapse cross-cutting concerns into a comma-separated list instead of a table
3. Replace the mermaid dependency graph with a text-based summary of key edges
4. Remove the "Ignored Patterns" section from structure map

## Budget estimation

Approximate token counts for planning (actual counts vary):

| Content type | ~Tokens per item |
|-------------|-----------------|
| Table row (5 columns) | 20-30 |
| Component card (full) | 80-120 |
| Component card (summary) | 15-25 |
| Directory tree line | 5-10 |
| Mermaid graph edge | 8-12 |
| Section header + intro paragraph | 30-50 |

## Budget allocation guide

For the default 4000-token budget:

| Section | Lite allocation | Heavy allocation |
|---------|----------------|-----------------|
| Structure Map | ~1200 (30%) | ~800 (20%) |
| Tech Stack | ~800 (20%) | ~800 (20%) |
| Components | ~1200 (30%) | ~1200 (30%) |
| Architecture | ~800 (20%) | ~1200 (30%) |

In lite mode, structure map gets more budget because components are simplified. In heavy mode, architecture inference gets more budget because it contains richer analysis.

## Token budget summary field

The `architecture.md` artifact includes a "Token Budget Summary" section. Fill it with:
- Target budget (from `--budget` or default)
- Estimated actual token count of the complete output
- List of compressions applied (e.g., "Grouped 18 component files", "Truncated tech stack table from 15 to 5 entries")
