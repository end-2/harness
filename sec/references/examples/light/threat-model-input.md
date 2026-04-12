# Light Example — Threat Model Input

A simple "bookmark manager" REST API. The upstream Arch and Impl artifacts that Sec reads at the start of `threat-model`.

## Arch artifacts (`./artifacts/arch/`)

`ARCH-DEC-001` — Architecture Decision: monolith, Express.js on Node 20. Single deployment unit, no inter-service communication.

`ARCH-COMP-001` — Component Structure:

| Component ID | Name | Type | Interfaces | Dependencies |
|-------------|------|------|------------|--------------|
| ARCH-COMP-001-api | API Gateway | gateway | REST /bookmarks, REST /auth | ARCH-COMP-001-db |
| ARCH-COMP-001-db | Bookmark Store | store | SQL queries | — |

`ARCH-TECH-001` — Technology Stack: Node 20, Express 4.18, PostgreSQL 15, JWT for auth.

`ARCH-DIAG-001` — C4 Context diagram (not reproduced here): single box "Bookmark API" with one external actor "User" and one external system "none".

**External interfaces**: 1 (REST API exposed to authenticated users).

## Impl artifacts (`./artifacts/impl/`)

`IMPL-MAP-001`:

```yaml
implementation_map:
  - id: IMPL-MAP-001-01
    component_ref: ARCH-COMP-001-api
    module_path: src/routes/
    entry_point: src/app.js
    re_refs: [FR-001, FR-002, FR-003, FR-004]
  - id: IMPL-MAP-001-02
    component_ref: ARCH-COMP-001-db
    module_path: src/db/
    entry_point: src/db/pool.js
    re_refs: [FR-001, FR-002, FR-003, FR-004]
```

`IMPL-CODE-001.external_dependencies`: `express@4.18.2`, `pg@8.11.3`, `jsonwebtoken@9.0.2`, `helmet@7.1.0`, `dotenv@16.3.1`.
`IMPL-IDR-001.decisions`: `[Repository pattern for DB access, middleware chain for auth]`.
`IMPL-GUIDE-001.conventions`: ESLint, Jest for testing, `.env` for config.

## RE context (via Arch refs)

`RE-CON-001` — Constraints: single-tenant, no PII beyond email, HTTPS required.
`RE-QA-001` — Quality: latency p95 < 200 ms, error rate < 0.5%.

No regulatory constraints specified (no GDPR, PCI DSS, or HIPAA triggers).
