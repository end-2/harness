# Section Schemas — Three-Section Artifact

The RE skill produces exactly three section artifacts. Each has a section-specific set of fields inside its `*.meta.yaml` file (documented here) and a matching markdown document (documented in [`assets/templates/`](../../assets/templates/)).

Common metadata fields are in [meta-schema.md](meta-schema.md).

## 1. Requirements Specification (`section: requirements`)

### Functional requirements

Key: `functional_requirements` (list of mappings).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | `FR-NNN`, zero-padded sequential. |
| `title` | string | yes | Short, imperative. |
| `description` | string | yes | One or two sentences. |
| `priority` | string | yes | MoSCoW: `Must`, `Should`, `Could`, `Won't`. |
| `acceptance_criteria` | list[string] | yes | Each item is objectively verifiable. Minimum one. |
| `source` | string | yes | Where it came from: user utterance, derived consequence, etc. |
| `dependencies` | list[string] | no | Other FR/NFR IDs this depends on. |

### Non-functional requirements

Key: `non_functional_requirements` (list of mappings).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | `NFR-NNN`. |
| `category` | string | yes | `performance` / `security` / `scalability` / `availability` / `maintainability` / `usability` / `compliance` / etc. |
| `title` | string | yes | Short. |
| `description` | string | yes | One or two sentences. |
| `priority` | string | yes | MoSCoW. |
| `acceptance_criteria` | list[string] | yes | At least one item with a **number** and **unit**. |
| `source` | string | yes | Same as FR. |

## 2. Constraints (`section: constraints`)

Key: `constraints` (list of mappings).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | `CON-NNN`. |
| `type` | string | yes | `technical` / `business` / `regulatory` / `environmental`. |
| `title` | string | yes | Short. |
| `description` | string | yes | One or two sentences. |
| `rationale` | string | yes | *Why* this constraint exists. Non-optional — a constraint without a rationale gets rejected in `review`. |
| `impact` | string | yes | What breaks if the constraint is violated. |
| `flexibility` | string | yes | `hard` / `soft` / `negotiable`. |

## 3. Quality Attribute Priorities (`section: quality-attributes`)

Key: `quality_attributes` (list of mappings).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `attribute` | string | yes | `performance` / `security` / `scalability` / `availability` / `maintainability` / `usability` / etc. |
| `priority` | int | yes | 1 is highest. Must form a strict total order — no ties. |
| `description` | string | yes | What this attribute means for *this* project. |
| `metric` | string | yes | Measurable target with a unit. "p95 < 200ms over 1M rows", not "fast". |
| `trade_off_notes` | string | yes | What lower-ranked attributes are sacrificed for this one. |

## Cross-section references

- Constraints frequently reference requirements (e.g. a regulatory constraint that drives an NFR). Record these using `upstream_refs` / `downstream_refs` in the common metadata.
- Quality attributes frequently reference NFRs (they are typically the measurable target of the NFR). When a QA drives an NFR, link them both ways.
- `artifact.py link` handles the reciprocal update when both sides exist.

## Validation rules

`artifact.py validate` enforces only the common metadata schema today. Section-specific structure is *not* machine-checked; the `review` stage is responsible for checking it by reading the artifact and walking the fields above. If future versions want machine validation, add a JSON Schema per section and load it in `_validate_meta`.
