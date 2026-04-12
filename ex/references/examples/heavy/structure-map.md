# Project Structure Map

## 1. Overview

Project root: `/home/user/projects/ecommerce-platform`. 187 source files, heavy mode selected (2 languages, 3 frameworks, max depth 5, 187 files).

## 2. Directory Tree

```
ecommerce-platform/
├── apps/
│   ├── web/                          (Next.js frontend)
│   │   ├── src/
│   │   │   ├── app/                  (App Router pages)
│   │   │   │   ├── (auth)/{login,register,forgot-password}/page.tsx
│   │   │   │   ├── (shop)/{products,cart,checkout,...3 more}/page.tsx
│   │   │   │   ├── admin/{dashboard,orders,products,...4 more}/page.tsx
│   │   │   │   └── api/{auth,products,orders,...5 more}/route.ts
│   │   │   ├── components/{ui,layout,forms,...8 more}/ (42 components)
│   │   │   ├── lib/{api,auth,utils,hooks}/
│   │   │   └── stores/{cart,user,ui}.ts
│   │   ├── public/
│   │   ├── next.config.mjs
│   │   └── package.json
│   └── api/                          (Express backend)
│       ├── src/
│       │   ├── index.ts              (server entry)
│       │   ├── routes/{auth,products,orders,users,payments}.ts
│       │   ├── services/{auth,product,order,user,payment,email}.ts
│       │   ├── models/{user,product,order,payment,category}.ts
│       │   ├── middleware/{auth,validation,rateLimit,errorHandler}.ts
│       │   ├── jobs/{orderProcessor,emailSender,inventorySync}.ts
│       │   └── utils/{logger,crypto,pagination}.ts
│       ├── prisma/
│       │   ├── schema.prisma
│       │   └── migrations/ (12 files)
│       └── package.json
├── packages/
│   └── shared/                       (shared types/utils)
│       ├── src/{types,validators,constants}/
│       └── package.json
├── docker-compose.yml
├── .github/workflows/{ci,deploy}.yml
├── package.json                      (workspace root)
├── turbo.json
└── README.md
```

## 3. File Classification

| Category | Count | Examples |
|----------|-------|---------|
| Source code | 132 | `apps/web/src/app/`, `apps/api/src/` |
| Configuration | 18 | `package.json` (x3), `tsconfig.json` (x3), `prisma/schema.prisma` |
| Test | 24 | `apps/api/src/**/*.test.ts`, `apps/web/src/**/*.test.tsx` |
| Documentation | 3 | `README.md`, `docs/api.md`, `CONTRIBUTING.md` |
| Build artifact | 0 | (excluded) |
| Static asset | 10 | `apps/web/public/` images and icons |

## 4. Entry Points

| File | Role | Evidence |
|------|------|----------|
| `apps/web/src/app/layout.tsx` | Frontend root | Next.js App Router root layout |
| `apps/api/src/index.ts` | Backend server | Express `app.listen()`, `src/index.ts` convention |
| `apps/api/src/jobs/orderProcessor.ts` | Background worker | Bull queue processor setup |

## 5. Configuration Files

| File | Role | Evidence |
|------|------|----------|
| `package.json` (root) | Workspace manager | `"workspaces"` field, Turborepo config |
| `turbo.json` | Build orchestrator | Turborepo pipeline config |
| `apps/api/prisma/schema.prisma` | Database schema | Prisma ORM schema definition |
| `docker-compose.yml` | Service orchestration | PostgreSQL + Redis + app services |
| `.github/workflows/ci.yml` | CI pipeline | GitHub Actions, runs tests + lint |
| `.github/workflows/deploy.yml` | CD pipeline | GitHub Actions, deploys to AWS |
| *5 more config files* | *Linter, formatter, TypeScript* | *ESLint, Prettier, tsconfig.json* |

## 6. Ignored Patterns

- `node_modules/`, `.git/`, `.next/`, `dist/`, `coverage/`, `.turbo/`, `.env`
