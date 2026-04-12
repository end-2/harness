# Architecture Inference

## 1. Overview

Lite mode — architecture style inference is based on directory structure only (import analysis was skipped). The project shows clear layered signals with medium confidence.

## 2. Architecture Style

| Field | Value |
|-------|-------|
| **Style** | layered |
| **Confidence** | medium |
| **Evidence** | Directory structure shows routes -> models separation. Single deployment unit (one Dockerfile). Lite mode — deeper analysis not performed. |

## 3. Layer Structure

| Layer | Components | Responsibility |
|-------|-----------|----------------|
| API / Presentation | CM-001 (Routes) | HTTP request handling |
| Business / Domain | CM-002 (Models) | Data logic |
| Cross-cutting | CM-003 (Middleware) | Auth, error handling |

## 4. Communication Patterns

| Pattern | Evidence | Components Involved |
|---------|----------|-------------------|
| REST | Express route definitions in `src/routes/` | CM-001 |

## 5. Data Stores

| Store | Type | Access Pattern | Components | Evidence |
|-------|------|---------------|-----------|----------|
| SQLite | RDBMS (embedded) | Direct driver (better-sqlite3) | CM-002 | `package.json` dependency, `.env.example` DATABASE_PATH |

## 6. Cross-Cutting Concerns

| Concern | Pattern | Evidence |
|---------|---------|----------|
| Authentication | Middleware | `src/middleware/auth.ts` |
| Error Handling | Middleware | `src/middleware/errorHandler.ts` |
| Logging | Utility module | `src/utils/logger.ts` |

## 7. Test Patterns

| Aspect | Value | Evidence |
|--------|-------|----------|
| **Unit test framework** | Jest | `jest.config.ts` |
| **Integration tests** | Present (likely) | `tests/todos.test.ts` may use supertest |
| **E2E tests** | Absent | No Playwright/Cypress config |
| **Coverage config** | Absent | No coverage config found |
| **Test organization** | Separate | `tests/` directory at root |

## 8. Build & Deploy Patterns

| Aspect | Value | Evidence |
|--------|-------|----------|
| **Build tool** | tsc (TypeScript compiler) | `tsconfig.json` |
| **Container** | Docker | `Dockerfile` at root |
| **CI/CD** | Not detected | No CI config files found |
| **IaC** | Not detected | No Terraform/CDK files |
| **Deploy target** | Container-based (inferred) | Dockerfile present |

## 9. Token Budget Summary

| Metric | Value |
|--------|-------|
| **Target budget** | 4000 tokens |
| **Actual estimate** | ~1800 tokens |
| **Compression applied** | None needed — lite mode output is naturally compact |
