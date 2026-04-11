# Light Example — Strategy Input

A small CRUD service: a "todo list" REST API. The upstream artifacts that QA reads at the start of `strategy`.

## RE artifacts (`./artifacts/re/`)

`RE-SPEC-001` — Functional requirements:

| ID | Title | Priority | Acceptance criteria |
|----|-------|----------|---------------------|
| FR-001 | Create a todo | must | AC-1: POST /todos with `{title}` returns 201 + id; AC-2: empty title returns 400 |
| FR-002 | List todos | must | AC-1: GET /todos returns the user's todos in created_at order |
| FR-003 | Mark a todo done | must | AC-1: PATCH /todos/{id} `{done: true}` toggles state; AC-2: unknown id returns 404 |
| FR-004 | Delete a todo | should | AC-1: DELETE /todos/{id} returns 204; AC-2: idempotent on second call |
| FR-005 | Bulk export to CSV | wont | Deferred to v2 |

`RE-CON-001` — Constraints: single-tenant, SQLite for v1, Python 3.12.

`RE-QA-001` — Quality requirements:

| ID | Attribute | Metric | Target |
|----|-----------|--------|--------|
| RE-QA-001 | latency | p95 | < 100 ms on /todos |
| RE-QA-002 | reliability | error rate | < 0.1% over 24h |

## Arch artifacts (`./artifacts/arch/`)

Light Arch — `ARCH-DEC-001` has 1 ADR ("monolith, FastAPI"), `ARCH-COMP-001` has 2 components (`api`, `storage`), no Container diagram. → QA inherits **light** mode.

## Impl artifacts (`./artifacts/impl/`)

`IMPL-MAP-001`:

```yaml
implementation_map:
  - id: IMPL-MAP-001-01
    component_ref: ARCH-COMP-001-api
    module_path: src/api/
    entry_point: src/api/main.py
    re_refs: [FR-001, FR-002, FR-003, FR-004]
  - id: IMPL-MAP-001-02
    component_ref: ARCH-COMP-001-storage
    module_path: src/storage/
    entry_point: src/storage/repo.py
    re_refs: [FR-001, FR-002, FR-003, FR-004]
```

`IMPL-CODE-001.external_dependencies`: `sqlite3` (stdlib), `fastapi`, `pydantic`.
`IMPL-IDR-001.decisions`: `[Repository pattern for storage]`.
`IMPL-GUIDE-001.conventions.tests`: pytest, mirrored layout under `tests/`.
