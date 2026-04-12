# Technology Stack Detection

## 1. Overview

6 technologies detected. Dominant language: TypeScript. Single web framework (Express) with SQLite for persistence.

## 2. Languages

| ID | Name | Version | Evidence | Config Location |
|----|------|---------|----------|-----------------|
| TS-001 | TypeScript | 5.3.3 | `package.json` devDependencies | `tsconfig.json` |

## 3. Frameworks & Libraries

| ID | Name | Version | Role | Evidence | Config Location |
|----|------|---------|------|----------|-----------------|
| TS-002 | Express | 4.18.2 | Web framework | `package.json` dependencies, `src/index.ts` imports | — |
| TS-003 | better-sqlite3 | 9.4.3 | Database driver | `package.json` dependencies | — |

## 4. Databases & Data Stores

| ID | Name | Version | Access Pattern | Evidence | Config Location |
|----|------|---------|---------------|----------|-----------------|
| TS-004 | SQLite | — | Direct driver (better-sqlite3) | `package.json` dependencies, `src/models/todo.ts` imports | `.env.example` DATABASE_PATH |

## 5. Build & Development Tools

| ID | Name | Version | Role | Evidence |
|----|------|---------|------|----------|
| TS-005 | ESLint | 8.56.0 | Linter | `package.json` devDependencies, `.eslintrc.json` |

## 6. Testing

| ID | Name | Version | Type | Evidence |
|----|------|---------|------|----------|
| TS-006 | Jest | 29.7.0 | Unit/integration | `package.json` devDependencies, `jest.config.ts` |

## 7. CI/CD & Infrastructure

| ID | Name | Version | Role | Evidence |
|----|------|---------|------|----------|
| TS-007 | Docker | — | Container | `Dockerfile` at project root |

## 8. Technology Relationships

- Express (TS-002) serves as the HTTP framework, with routes in `src/routes/`
- better-sqlite3 (TS-003) provides direct SQLite access from the model layer
