# Heavy Example — Threat Model Input

A microservices e-commerce platform handling PII and payment data. The upstream Arch and Impl artifacts that Sec reads at the start of `threat-model`.

## Arch artifacts (`./artifacts/arch/`)

`ARCH-DEC-001` — Architecture Decision: microservices on Kubernetes, event-driven communication via RabbitMQ, PostgreSQL per service, Redis for session/cache.

`ARCH-DEC-002` — API Gateway: Kong gateway with JWT validation and rate limiting at the edge.

`ARCH-COMP-001` — Component Structure:

| Component ID | Name | Type | Interfaces | Dependencies |
|-------------|------|------|------------|--------------|
| ARCH-COMP-001-gw | API Gateway | gateway | REST /api/*, WebSocket /ws | ARCH-COMP-001-auth, ARCH-COMP-001-order, ARCH-COMP-001-payment |
| ARCH-COMP-001-auth | Auth Service | service | REST /auth/*, gRPC internal | ARCH-COMP-001-authdb |
| ARCH-COMP-001-order | Order Service | service | REST /orders/*, gRPC internal | ARCH-COMP-001-orderdb, ARCH-COMP-001-payment, ARCH-COMP-001-notif |
| ARCH-COMP-001-payment | Payment Service | service | REST /payments/*, gRPC internal, webhook /callbacks | ARCH-COMP-001-paydb, external:stripe |
| ARCH-COMP-001-notif | Notification Service | service | gRPC internal, AMQP consumer | external:sendgrid, external:twilio |
| ARCH-COMP-001-authdb | Auth Database | store | SQL | — |
| ARCH-COMP-001-orderdb | Order Database | store | SQL | — |
| ARCH-COMP-001-paydb | Payment Database | store | SQL (encrypted at rest) | — |

`ARCH-TECH-001` — Technology Stack: Go 1.22 (auth, payment), Python 3.12/FastAPI (order, notification), Kong 3.6, PostgreSQL 16, Redis 7, RabbitMQ 3.13, Kubernetes 1.29, Helm, Terraform.

`ARCH-DIAG-001` — C4 Container diagram: 5 services, 3 databases, 1 message broker, 3 external systems (Stripe, SendGrid, Twilio).

**External interfaces**: 4 (REST API via gateway, WebSocket, Stripe webhook callbacks, admin dashboard).

## Impl artifacts (`./artifacts/impl/`)

`IMPL-MAP-001` through `IMPL-MAP-005`: one per service, mapping module paths to components.

```yaml
# Abridged — auth service
implementation_map:
  - id: IMPL-MAP-001-01
    component_ref: ARCH-COMP-001-auth
    module_path: services/auth/
    entry_point: services/auth/cmd/main.go
    interfaces_implemented: ["/auth/login", "/auth/register", "/auth/refresh", "/auth/verify"]
    re_refs: [FR-001, FR-002, FR-003]
```

`IMPL-CODE-001.external_dependencies` (abridged): `golang.org/x/crypto`, `github.com/golang-jwt/jwt/v5`, `github.com/lib/pq`, `github.com/stripe/stripe-go/v76`, `fastapi==0.109.0`, `sqlalchemy==2.0.25`, `pydantic==2.5.3`, `pika==1.3.2`.

`IMPL-IDR-001.decisions`: `[Repository pattern, CQRS for orders, Saga pattern for payment orchestration, Outbox pattern for reliable messaging]`.

`IMPL-GUIDE-001.conventions`: Go services use `golangci-lint`, Python services use `ruff`. All services containerised with distroless base images.

## RE context (via Arch refs)

`RE-CON-001` — Constraints: multi-tenant, HTTPS required, EU data residency.
`RE-CON-002` — Regulatory: GDPR applies (PII: name, email, address, phone).
`RE-CON-003` — Regulatory: PCI DSS SAQ-A applies (payment data handled by Stripe, but tokens stored locally).
`RE-QA-001` — Quality: API p95 < 300 ms, payment p95 < 500 ms.
`RE-QA-002` — Quality: 99.95% availability SLO.

Data sensitivity: PII (name, email, address, phone) in auth and order DBs; payment tokens in payment DB; session tokens in Redis.
