# Technology Stack Detection

## 1. Overview

14 technologies detected. TypeScript is the sole language across frontend and backend. Next.js + Express dual-app architecture with Prisma ORM and PostgreSQL.

## 2. Languages

| ID | Name | Version | Evidence | Config Location |
|----|------|---------|----------|-----------------|
| TS-001 | TypeScript | 5.4.2 | All `package.json` devDependencies | `tsconfig.json` (x3) |

## 3. Frameworks & Libraries

| ID | Name | Version | Role | Evidence | Config Location |
|----|------|---------|------|----------|-----------------|
| TS-002 | Next.js | 14.1.0 | Frontend framework | `apps/web/package.json`, `next.config.mjs` | `next.config.mjs` |
| TS-003 | React | 18.2.0 | UI library | `apps/web/package.json`, JSX/TSX files | — |
| TS-004 | Express | 4.18.2 | Backend framework | `apps/api/package.json`, `src/index.ts` | — |
| TS-005 | Prisma | 5.9.1 | ORM | `apps/api/package.json`, `prisma/schema.prisma` | `prisma/schema.prisma` |
| TS-006 | Zustand | 4.5.0 | State management | `apps/web/package.json`, `src/stores/*.ts` | — |
| TS-007 | Bull | 4.12.2 | Job queue | `apps/api/package.json`, `src/jobs/` | — |
| TS-008 | Zod | 3.22.4 | Schema validation | `packages/shared/package.json`, validator imports | — |

## 4. Databases & Data Stores

| ID | Name | Version | Access Pattern | Evidence | Config Location |
|----|------|---------|---------------|----------|-----------------|
| TS-009 | PostgreSQL | 15 | ORM (Prisma) | `prisma/schema.prisma` provider, `docker-compose.yml` | `.env` DATABASE_URL |
| TS-010 | Redis | 7 | Direct client (ioredis) + Bull queue backend | `apps/api/package.json`, `docker-compose.yml` | `.env` REDIS_URL |

## 5. Build & Development Tools

| ID | Name | Version | Role | Evidence |
|----|------|---------|------|----------|
| TS-011 | Turborepo | 1.12.4 | Monorepo build orchestration | `turbo.json`, root `package.json` |
| TS-012 | ESLint + Prettier | 8.56 / 3.2 | Linter + formatter | `.eslintrc.json`, `.prettierrc` |

## 6. Testing

| ID | Name | Version | Type | Evidence |
|----|------|---------|------|----------|
| TS-013 | Jest | 29.7.0 | Unit + integration | `jest.config.ts` in api + web, `*.test.ts` files |

## 7. CI/CD & Infrastructure

| ID | Name | Version | Role | Evidence |
|----|------|---------|------|----------|
| TS-014 | GitHub Actions | — | CI/CD | `.github/workflows/{ci,deploy}.yml` |
| TS-015 | Docker / Docker Compose | — | Container orchestration | `docker-compose.yml`, `Dockerfile` per app |

## 8. Technology Relationships

- Next.js (TS-002) uses React (TS-003) for rendering and Zustand (TS-006) for client state
- Express (TS-004) uses Prisma (TS-005) to access PostgreSQL (TS-009)
- Bull (TS-007) uses Redis (TS-010) as its queue backend
- Zod (TS-008) provides shared validation schemas consumed by both web and api apps
- Turborepo (TS-011) orchestrates builds across all workspace packages
