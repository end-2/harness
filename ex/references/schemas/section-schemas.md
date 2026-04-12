# Section Schemas

Each of the four Ex sections has section-specific fields in its `*.meta.yaml` file, in addition to the common fields documented in [meta-schema.md](meta-schema.md).

## 1. Structure Map (`structure-map`)

| Field | Type | Description |
|-------|------|-------------|
| `project_root` | string | Absolute path to the analyzed project |
| `file_count` | object | `{total: int, by_category: {source: int, config: int, test: int, ...}}` |
| `directory_conventions` | list[string] | Detected naming/organizational conventions |
| `entry_points` | list[object] | `[{file: string, role: string, evidence: string}]` |
| `config_files` | list[object] | `[{file: string, role: string, evidence: string}]` |
| `ignored_patterns` | list[string] | Exclusion patterns applied during scan |
| `depth_mode` | string | `lite` or `heavy` |
| `depth_evidence` | string | Reasoning for mode selection (metric values and threshold comparison) |

## 2. Tech Stack (`tech-stack`)

| Field | Type | Description |
|-------|------|-------------|
| `technologies` | list[object] | Array of detected technologies |

Each technology entry:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, e.g., `TS-001` |
| `category` | string | One of: `language`, `framework`, `database`, `messaging`, `build`, `test`, `lint`, `ci`, `container`, `infra` |
| `name` | string | Technology name, e.g., `TypeScript`, `Next.js`, `PostgreSQL` |
| `version` | string or null | Detected version from manifests |
| `evidence` | string | Which file/pattern confirmed the detection |
| `role` | string | Inferred role in the project, e.g., `primary language`, `web framework`, `ORM` |
| `config_location` | string or null | Path to the relevant configuration file |

## 3. Components (`components`)

| Field | Type | Description |
|-------|------|-------------|
| `components` | list[object] | Array of detected components/modules |
| `circular_dependencies` | list[object] | `[{cycle: list[string], description: string}]` |
| `cross_cutting_concerns` | list[object] | `[{concern: string, implementation: string, components: list[string]}]` |

Each component entry:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, e.g., `CM-001` |
| `name` | string | Component/module name |
| `path` | string | Filesystem path relative to project root |
| `type` | string | One of: `service`, `library`, `handler`, `model`, `config`, `util`, `test` |
| `responsibility` | string | Inferred core responsibility |
| `dependencies_internal` | list[string] | Component IDs this component depends on |
| `dependencies_external` | list[string] | External package names |
| `dependents` | list[string] | Component IDs that depend on this component |
| `api_surface` | list[object] | `[{type: string, endpoint: string, methods: list[string]}]` |
| `patterns_detected` | list[string] | Design patterns found, e.g., `Repository`, `Factory`, `Middleware` |

## 4. Architecture (`architecture`)

| Field | Type | Description |
|-------|------|-------------|
| `architecture_style` | string | One of: `monolithic`, `modular-monolith`, `microservices`, `serverless`, `layered`, `hexagonal`, `event-driven` |
| `style_confidence` | string | `high`, `medium`, or `low` |
| `style_evidence` | string | Structural signals that led to the conclusion |
| `layer_structure` | list[object] | `[{layer: string, components: list[string], responsibility: string}]` |
| `communication_patterns` | list[object] | `[{pattern: string, evidence: string, components: list[string]}]` |
| `data_stores` | list[object] | `[{name: string, type: string, access_pattern: string, components: list[string], evidence: string}]` |
| `cross_cutting_concerns` | list[object] | `[{concern: string, pattern: string, evidence: string}]` |
| `test_patterns` | object | `{unit_framework, integration_tests, e2e_tests, coverage_config, test_organization}` |
| `build_deploy_patterns` | object | `{build_tool, container, ci_cd, iac, deploy_target}` |
| `token_budget_summary` | object | `{target_budget: int, actual_estimate: int, compressions_applied: list[string]}` |
