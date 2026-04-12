# Architecture Inference

## 1. Overview

Modular monolith with high confidence. The project is a monorepo with two deployable applications (Next.js frontend, Express backend) sharing code through a shared package. The backend follows a clear layered architecture (routes -> services -> models). Despite the monorepo structure, this is not microservices — both apps share a single database and there is no inter-service communication protocol.

## 2. Architecture Style

| Field | Value |
|-------|-------|
| **Style** | modular-monolith |
| **Confidence** | high |
| **Evidence** | Monorepo with workspace packages, single shared PostgreSQL database, no inter-service HTTP/gRPC calls between web and api (web calls api's REST endpoints as a client, not as a peer service). Clear module boundaries via packages/ and apps/. Turborepo orchestrates as a single build. |

## 3. Layer Structure

Backend (`apps/api/`) follows strict layering:

| Layer | Components | Responsibility |
|-------|-----------|----------------|
| Presentation | CM-002 (API Routes) | HTTP handling, request validation, response formatting |
| Business | CM-003 (Services) | Domain logic, orchestration, external integrations |
| Data | CM-004 (Models/Prisma) | Database access, schema, migrations |
| Cross-cutting | CM-005 (Middleware) | Auth, rate limiting, error handling |
| Background | CM-006 (Jobs) | Async processing via Bull queues |

Frontend (`apps/web/`) follows Next.js App Router conventions (pages -> components -> stores -> lib).

## 4. Communication Patterns

| Pattern | Evidence | Components Involved |
|---------|----------|-------------------|
| REST (client -> server) | Next.js app calls Express API via `fetch` in `lib/api/` | CM-001 -> CM-002 |
| REST (API endpoints) | Express route definitions | CM-002 |
| Queue (async jobs) | Bull queue with Redis backend | CM-003 -> CM-006 |
| Webhook (external) | Stripe webhook endpoint | External -> CM-002 |

## 5. Data Stores

| Store | Type | Access Pattern | Components | Evidence |
|-------|------|---------------|-----------|----------|
| PostgreSQL | RDBMS | ORM (Prisma) | CM-004 | `prisma/schema.prisma` provider, `docker-compose.yml` |
| Redis | In-memory | Direct client + Bull queue backend | CM-006 | `docker-compose.yml`, ioredis dependency |

## 6. Cross-Cutting Concerns

| Concern | Pattern | Evidence |
|---------|---------|----------|
| Authentication | JWT middleware | `apps/api/src/middleware/auth.ts`, jsonwebtoken dependency |
| Validation | Schema validation (Zod) | `packages/shared/src/validators/`, used in route middleware |
| Rate limiting | Express middleware | `apps/api/src/middleware/rateLimit.ts`, express-rate-limit |
| Error handling | Centralized middleware | `apps/api/src/middleware/errorHandler.ts` |
| Logging | Structured (Winston) | `apps/api/src/utils/logger.ts`, winston dependency |

## 7. Test Patterns

| Aspect | Value | Evidence |
|--------|-------|----------|
| **Unit test framework** | Jest | `jest.config.ts` in api and web |
| **Integration tests** | Present | `*.test.ts` files with supertest in api |
| **E2E tests** | Absent | No Playwright/Cypress config |
| **Coverage config** | Absent | No coverage threshold config |
| **Test organization** | Colocated | Tests alongside source files (`*.test.ts` next to `*.ts`) |

## 8. Build & Deploy Patterns

| Aspect | Value | Evidence |
|--------|-------|----------|
| **Build tool** | Turborepo + tsc | `turbo.json`, `tsconfig.json` |
| **Container** | Docker Compose (multi-service) | `docker-compose.yml` with app + postgres + redis |
| **CI/CD** | GitHub Actions | `.github/workflows/{ci,deploy}.yml` |
| **IaC** | Not detected | No Terraform/CDK files |
| **Deploy target** | Container-based, likely AWS (inferred from deploy workflow) | `.github/workflows/deploy.yml` references ECR |

## 9. Token Budget Summary

| Metric | Value |
|--------|-------|
| **Target budget** | 4000 tokens |
| **Actual estimate** | ~3800 tokens |
| **Compression applied** | Grouped 42 web components into summary, truncated migration file listing (12 -> count only), collapsed config files table from 12 to 7 entries |
