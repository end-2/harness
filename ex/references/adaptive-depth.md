# Adaptive Depth Rules

Ex uses a single SKILL.md entry point and selects analysis depth automatically based on project complexity. The user can override with `--depth lite` or `--depth heavy`.

## Complexity metrics

| Metric | How measured | Lite threshold | Heavy threshold |
|--------|-------------|---------------|-----------------|
| Source file count | Count files classified as "source code" in Stage 1 | <= 50 | > 50 |
| Distinct languages | Count unique languages by file extension | 1 | > 1 |
| Frameworks detected | Count frameworks identified in Stage 2 | <= 1 | > 1 |
| Max directory depth | Deepest nesting level under `project_root` (excluding excluded dirs) | <= 3 | > 3 |

## Mode selection rule

- If **all four** metrics fall within lite thresholds → **lite** mode
- If **any** metric exceeds its lite threshold → **heavy** mode
- User override (`--depth`) takes precedence over auto-detection

Always record: the four metric values, which threshold was exceeded (if any), and the final mode decision.

## What changes between modes

| Stage | Lite behavior | Heavy behavior |
|-------|--------------|----------------|
| **scan** | Full scan (identical) | Full scan (identical) |
| **detect** | Full detection, but condensed output — group minor tools, skip detailed version reporting for secondary tools | Full detection with all details |
| **analyze** | Skip import analysis entirely. Infer components from top-level directories only. Skip architecture style inference, circular dependency detection, cross-cutting concern analysis. | Full import graph, component boundary inference, architecture style inference, circular dep detection, cross-cutting concern analysis. |
| **map** | Produce simplified 4-section output. Components section has directory-based cards only (no dependency graph). Architecture section notes "lite mode — architecture inference skipped." | Full 4-section output with all details. |

## Edge cases

- **Monorepo with multiple packages**: treat the entire monorepo as heavy, even if individual packages are small. The inter-package dependency analysis is what makes heavy mode valuable here.
- **Single large file**: a project with 10 files but one 5000-line file is still lite by file count. The depth mode is about structural complexity, not code volume.
- **Generated code directories**: if a large number of files are generated (e.g., `generated/`, `__generated__/`), exclude them from the file count for mode selection purposes but note their existence.
- **`--focus` flag**: when focusing on a subdirectory, compute metrics for that subdirectory only, not the whole project. This often results in lite mode even for large projects.
