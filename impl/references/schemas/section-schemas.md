# Section Schemas

The four Impl sections each carry their own structured block inside the metadata file. The block mirrors the tables in the paired markdown document — the markdown is the human-readable source of truth for prose, and the YAML block is what downstream skills and scripts parse.

Common metadata fields (`artifact_id`, `phase`, `approval`, …) are covered in [meta-schema.md](meta-schema.md).

## 1. `implementation-map`

Block key: `implementation_map`

```yaml
implementation_map:
  - id: IM-001                 # unique within this artifact
    component_ref: ARCH-COMP-001
    module_path: src/auth/
    entry_point: src/auth/index.ts
    internal_structure: |
      src/auth/
      ├── index.ts
      ├── service.ts
      └── repository.ts
    interfaces_implemented:
      - arch_interface: IAuthService
        file: src/auth/service.ts
        notes: null
    arch_refs: [ARCH-COMP-001, ARCH-DEC-002]
    re_refs: [FR-002, NFR-003]
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | `IM-NNN`, unique within this artifact |
| `component_ref` | yes | The `ARCH-COMP-*` id this entry realises |
| `module_path` | yes | Repo-relative directory or file that contains the component's code |
| `entry_point` | yes | The single file that is "the front door" of the module |
| `internal_structure` | yes | 2–3 level directory tree as a string |
| `interfaces_implemented` | yes | List of `{arch_interface, file, notes}` triples; at least one entry |
| `arch_refs` | yes | Arch ids that back this mapping |
| `re_refs` | optional | RE ids reached via Arch's `re_refs` |

## 2. `code-structure`

Block key: `code_structure` (singular — this section is not a list)

```yaml
code_structure:
  project_root: ./
  directory_layout: |
    .
    ├── src/
    │   ├── auth/
    │   ├── api/
    │   └── shared/
    ├── tests/
    └── package.json
  module_dependencies:
    - from: src/api
      to: src/auth
      kind: import
    - from: src/api
      to: src/shared
      kind: import
  external_dependencies:
    - name: fastapi
      version: 0.110.0
      purpose: HTTP framework
      tech_stack_ref: ARCH-TECH-001
  build_config:
    - file: pyproject.toml
      purpose: build metadata and dependency pinning
    - file: Dockerfile
      purpose: container image build
  environment_config:
    - name: DATABASE_URL
      purpose: primary DB connection
      required: true
```

| Field | Required | Description |
|-------|----------|-------------|
| `project_root` | yes | Repo-relative root of the generated project |
| `directory_layout` | yes | Tree as a string, 2–3 levels |
| `module_dependencies` | yes | Edge list `{from, to, kind}` where `kind` ∈ `import`, `runtime`, `build`, `test` |
| `external_dependencies` | yes | `{name, version, purpose, tech_stack_ref}` — every row must have a tech-stack ref |
| `build_config` | yes | `{file, purpose}` rows for every build/pack file |
| `environment_config` | optional | `{name, purpose, required}` rows for env vars and config files |

## 3. `implementation-decisions`

Block key: `implementation_decisions`

```yaml
implementation_decisions:
  - id: IDR-001
    title: Repository pattern per aggregate
    decision: Introduce one repository per DDD aggregate root.
    rationale: |
      ARCH-DEC-002 mandates hexagonal layering but does not name the
      data-access shape. The domain has three aggregates with diverging
      persistence needs.
    alternatives_considered:
      - option: Single generic repository<T>
        pros: [less code]
        cons: [leaks persistence details into domain]
        rejected_reason: would violate the hexagonal boundary Arch asks for
    pattern_applied: Repository
    arch_refs: [ARCH-DEC-002]
    re_refs: [NFR-003]
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | `IDR-NNN`, unique within this artifact |
| `title` | yes | Short human-readable title |
| `decision` | yes | One paragraph describing the chosen approach |
| `rationale` | yes | Why. Must cite refs where applicable |
| `alternatives_considered` | optional | List of `{option, pros, cons, rejected_reason}` |
| `pattern_applied` | optional | GoF or stack-idiomatic pattern name; null if none |
| `arch_refs` | yes (at least one) | Must anchor to an `ARCH-*` id |
| `re_refs` | optional | RE ids reached via Arch |

**Rule**: every IDR must cite at least one `ARCH-*` ref. An IDR with no Arch anchor is a smell — the decision either belongs in Arch (escalate) or is too small to record (drop it).

## 4. `implementation-guide`

Block key: `implementation_guide` (singular — this section is not a list)

```yaml
implementation_guide:
  prerequisites:
    - tool: Node.js
      version: 20.x
      notes: null
    - tool: Docker
      version: 24+
      notes: for local DB
  setup_steps:
    - Clone the repository
    - Install dependencies with pnpm install
    - Copy .env.example to .env and fill in values
    - Run database migrations
  build_commands:
    - pnpm build
  run_commands:
    - pnpm dev
  conventions:
    naming: camelCase files, PascalCase classes
    error_handling: Result<T,E> via neverthrow
    logging: structured JSON via pino
    tests: co-located under __tests__/
  extension_points:
    - goal: Add a new auth provider
      touch_point: src/auth/providers/
      notes: implement IAuthProvider
```

| Field | Required | Description |
|-------|----------|-------------|
| `prerequisites` | yes | `{tool, version, notes}` rows |
| `setup_steps` | yes | Ordered list of shell-level actions |
| `build_commands` | yes | One or more shell commands |
| `run_commands` | yes | One or more shell commands |
| `conventions` | yes | Free-form object; keys should include at least `naming`, `error_handling`, `logging`, `tests` when detectable |
| `extension_points` | optional | `{goal, touch_point, notes}` rows |
