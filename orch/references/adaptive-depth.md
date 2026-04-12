# Adaptive Depth — Single Dispatch vs Pipeline Routing

Orch auto-selects between lightweight single dispatch and full pipeline execution based on the user's request. This document defines the decision rules.

## Decision matrix

| Signal | Single dispatch | Pipeline |
|--------|----------------|----------|
| User names one skill | Yes | — |
| User describes a task fitting one skill's domain | Yes | — |
| User asks to "build from scratch" or "create a system" | — | Yes |
| User asks for multiple skills by name | — | Yes |
| User mentions a pipeline name | — | Yes |
| User says "full SDLC" / "end to end" | — | Yes |
| Request implies cross-skill dependency | — | Yes |
| Ambiguous (could be either) | Start with dispatch, escalate if needed | — |

## Single dispatch mode

**When**: The request maps cleanly to one skill and one agent.

**Behaviour**:
- Pipeline is set to `single:<skill>:<agent>` (e.g., `single:ex:scan`)
- Run metadata has exactly one step
- No upstream/downstream artifact handoff needed
- Minimal overhead — almost equivalent to the user calling the skill directly

**Examples**:
- "Explore this codebase" → `single:ex:scan` (or the full `explore` pipeline if user wants all 4 stages)
- "Review the architecture" → `single:arch:review`
- "Run a security audit" → `single:sec:audit`
- "Generate tests" → `single:qa:generate`

**Ambiguity resolution**: When a request could be single dispatch or pipeline, prefer single dispatch if:
- The user's language is specific ("do X") rather than broad ("handle everything")
- No cross-skill dependency is implied
- The request mentions a specific skill or agent by name

## Pipeline mode

**When**: The request requires coordination across multiple skills.

**Behaviour**:
- Select a predefined pipeline or build a dynamic sequence
- Full run lifecycle with multi-step tracking
- Artifact handoff between skills
- Dialogue relay for interactive skills

**Pipeline selection priority**:

1. **Exact match**: User names a pipeline → use it
2. **Intent match**: Map the request to the closest predefined pipeline
3. **Existing project detection**: If code exists, prefer `-existing` variants
4. **Dynamic construction**: Build a custom sequence if no predefined pipeline fits

## Existing project detection

Prefer `-existing` pipeline variants when any of these signals are present:

| Signal | Weight |
|--------|--------|
| Source code files in working directory (`.py`, `.js`, `.ts`, `.java`, `.go`, etc.) | Strong |
| `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`, etc. exist | Strong |
| User says "existing", "current", "this project", "add to" | Strong |
| Git history exists with substantive commits | Moderate |
| Prior `ex` artifacts exist | Strong |
| Only config files (`.gitignore`, `README.md`) | Weak (probably new project) |

When signals conflict, ask the user: "I see some files here — is this an existing project you want to extend, or a new project you're starting?"

## Dynamic pipeline construction

When no predefined pipeline fits:

1. Identify the skills needed from the request
2. Order them by dependency (ex → re → arch → impl → [qa, sec, devops] → verify)
3. Remove unnecessary skills (if user doesn't need security, skip sec)
4. Identify parallelisable groups (skills at the same dependency level)
5. Present the proposed pipeline to the user for confirmation

Example: "I need requirements and then implementation, but skip architecture"
→ Dynamic pipeline: `re:elicit → re:spec → impl:generate`

Always confirm dynamic pipelines with the user before executing.
