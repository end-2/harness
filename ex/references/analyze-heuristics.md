# Analysis Heuristics

This document describes the heuristics used in Stage 3 (analyze) to infer component boundaries, determine architecture style, and identify structural patterns.

## Component boundary inference

### Directory-based heuristics

1. **Feature directories**: directories under `src/features/`, `src/modules/`, `src/domains/`, `src/packages/` — each is a component.
2. **Layer directories**: `src/controllers/`, `src/services/`, `src/models/`, `src/repositories/` — each is a layer-component, not a domain-component.
3. **Monorepo packages**: entries in `workspaces` (npm), `[workspace]` (Cargo), Go workspace modules — each is a component.
4. **Top-level grouping**: if none of the above apply, top-level directories under `src/` (or project root if no `src/`) form candidate components.

### Cohesion/coupling heuristics

- **High cohesion**: > 60% of imports within a directory point to other files in the same directory → strong component boundary.
- **Low coupling**: < 20% of imports cross into other candidate components → well-defined boundary.
- **Barrel files**: an `index.ts`/`__init__.py`/`mod.rs` that re-exports from siblings signals an intentional module boundary.
- **Package boundary files**: `package.json`, `go.mod`, `Cargo.toml` within a subdirectory = definitive component boundary.

### Component type inference

| Type | Signals |
|------|---------|
| **service** | Contains business logic, depends on models/repositories, has no direct HTTP handling |
| **handler** | HTTP route handlers, controller files, API endpoint definitions |
| **model** | Data structures, database entities, schema definitions |
| **library** | Reusable code with no side effects, exported functions/classes |
| **config** | Configuration loading, environment variable parsing |
| **util** | Small helper functions, no domain logic |
| **test** | Test files, test utilities, fixtures |

## Architecture style inference

### Monolithic signals
- Single `package.json`/`go.mod`/`Cargo.toml` at root
- Single `Dockerfile` or no Dockerfile
- Shared database access from multiple modules
- No service-to-service communication patterns
- **Confidence boost**: single deployment config (one `Procfile`, one `Dockerfile`)

### Modular monolith signals
- Single deployment unit BUT clear module boundaries
- Barrel files or explicit public APIs per module
- Internal module dependencies go through defined interfaces
- **Confidence boost**: linting rules enforcing import boundaries (e.g., `eslint-plugin-boundaries`)

### Microservices signals
- Multiple `Dockerfile`s or `docker-compose.yml` with multiple services
- Separate `package.json`/`go.mod` per service directory
- API gateway configuration
- Inter-service communication: HTTP clients, gRPC stubs, message queue producers/consumers
- **Confidence boost**: Kubernetes manifests per service, separate CI pipelines

### Serverless signals
- `serverless.yml` or cloud function config files
- Handler files mapped to individual functions
- Event source mappings (S3, SQS, API Gateway triggers)
- **Confidence boost**: no long-running process setup, no server bootstrap code

### Layered signals
- Clear directory hierarchy: `presentation/` -> `application/` -> `domain/` -> `infrastructure/`
- Or: `controllers/` -> `services/` -> `models/` -> `repositories/`
- Imports only flow "downward" (presentation imports business, never the reverse)
- **Confidence boost**: consistent one-directional dependency flow

### Hexagonal / Clean Architecture signals
- `domain/` or `core/` directory with zero external imports
- `ports/` and `adapters/` directories (or equivalent naming)
- Interfaces defined in domain, implemented in infrastructure
- Dependency inversion: domain defines interfaces, outer layers implement
- **Confidence boost**: dependency injection container configuration

### Event-driven signals
- Message queue configuration (RabbitMQ, Kafka, SQS, NATS)
- Event/command definitions as data structures
- Event handlers/processors
- CQRS patterns: separate read/write models
- **Confidence boost**: event sourcing (event store, event replay logic)

## Confidence levels

| Level | Criteria |
|-------|---------|
| **High** | Multiple strong signals from different sources (directory structure + dependency pattern + config files) |
| **Medium** | Some signals present but incomplete, or signals from a single source only |
| **Low** | Weak or ambiguous signals, mixed patterns suggesting transition or hybrid approach |

When confidence is low, note the ambiguity explicitly: "The codebase shows elements of both layered and hexagonal architecture, possibly in transition. Layered signals are stronger in the API layer; hexagonal signals appear in the domain core."

## Cross-cutting concern detection

| Concern | Detection signals |
|---------|-----------------|
| **Authentication** | JWT libraries, passport/auth middleware, `@Authenticated` decorators, OAuth config, session management |
| **Authorization** | RBAC/ABAC patterns, permission checks, guard classes, policy files |
| **Logging** | Logger configuration files, structured logging libraries (winston, pino, loguru, zap), log level management |
| **Error handling** | Global error handler middleware, custom error classes, error boundary components, try/catch patterns in entry points |
| **Validation** | Validation libraries (joi, zod, pydantic), request validation middleware, schema validation |
| **Caching** | Cache configuration, Redis/memcached for caching, HTTP cache headers, memoization decorators |
| **Monitoring** | APM agents (DataDog, New Relic, Sentry), metrics collection, health check endpoints, OpenTelemetry |
| **Rate limiting** | Rate limiter middleware, throttle configuration |
| **CORS** | CORS middleware configuration, allowed origins lists |
