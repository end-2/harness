# Section Schemas

The four arch sections. Each section has a markdown body (the source of truth during iteration) and a structured YAML mirror inside `*.meta.yaml` that downstream skills parse.

## 1. Architecture Decisions (`decisions`)

Markdown: `ARCH-DEC-<N>.md` — decision summary table + ADRs.
Metadata mirror: `architecture_decisions[]`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `AD-NNN`, sequential, zero-padded. |
| `title` | string | One-line name. |
| `status` | enum | `Proposed` / `Accepted` / `Deprecated` / `Superseded by AD-NNN`. |
| `decision` | string | One-paragraph plain statement of the chosen option. |
| `rationale` | string | Why this option, referencing the forces named in Context. |
| `alternatives_considered` | list | Each entry: `option`, `pros`, `cons`, `rejected_reason`. |
| `trade_offs` | string | Honest list of positive/negative/risks consequences. |
| `re_refs` | list[string] | RE ids that drove the decision (`NFR-003`, `CON-002`, `RE-QA-001`, …). Non-empty. |

## 2. Component Structure (`components`)

Markdown: `ARCH-COMP-<N>.md` — overview, components table, component details.
Metadata mirror: `components[]`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `COMP-NNN`, sequential. |
| `name` | string | Short name that will appear in diagrams and code. |
| `responsibility` | string | Single-sentence responsibility. If it needs two sentences, it is two components. |
| `type` | enum | `service` / `library` / `gateway` / `store` / `queue` / `job`. |
| `interfaces` | list | Each entry: `name`, `direction` (`inbound`/`outbound`), `protocol`, `description`. |
| `dependencies` | list[string] | Other `COMP-NNN` ids. Not languages or libraries. |
| `re_refs` | list[string] | FR/NFR ids this component is responsible for. Non-empty. |

## 3. Technology Stack (`tech-stack`)

Markdown: `ARCH-TECH-<N>.md` — stack table + notes.
Metadata mirror: `technology_stack[]`

| Field | Type | Description |
|-------|------|-------------|
| `category` | enum | `language` / `framework` / `database` / `messaging` / `infra` / `observability` / `auth` / `other`. |
| `choice` | string | Concrete name and version or "none" with a reason. |
| `rationale` | string | Why this technology. |
| `decision_ref` | string \| null | Related `AD-NNN`, if any. |
| `constraint_ref` | string \| null | Related `CON-NNN`, if any. |

At least one of `decision_ref` or `constraint_ref` must be set per row.

## 4. Diagrams (`diagrams`)

Markdown: `ARCH-DIAG-<N>.md` — one section per diagram, each a Mermaid fenced block plus a caption.
Metadata mirror: `diagrams[]`

| Field | Type | Description |
|-------|------|-------------|
| `type` | enum | `c4-context` / `c4-container` / `sequence` / `data-flow`. |
| `title` | string | Diagram title. |
| `format` | enum | `mermaid` (only format currently supported). |
| `description` | string | What the diagram shows, in prose. |
| `re_refs` | list[string] | Which RE drivers or AD ids the diagram answers to. |

## Convention: markdown first, structured block second

During iteration, the markdown body is authoritative. When a section reaches `in_review` and you need the structured block for downstream parsing, copy the finished rows into the `*.meta.yaml` structured block. Never try to keep the two perfectly in sync mid-iteration — that creates merge-conflict friction with no benefit. The structured block becomes authoritative only after `approve`.
