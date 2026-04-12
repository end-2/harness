# Project Structure Map

## 1. Overview

Project root: `/home/user/projects/todo-api`. 18 source files, lite mode selected (single language, single framework, depth <= 3, files <= 50).

## 2. Directory Tree

```
todo-api/
├── src/
│   ├── index.ts          (app entry)
│   ├── routes/
│   │   ├── todos.ts
│   │   └── health.ts
│   ├── models/
│   │   └── todo.ts
│   ├── middleware/
│   │   ├── auth.ts
│   │   └── errorHandler.ts
│   └── utils/
│       └── logger.ts
├── tests/
│   ├── todos.test.ts
│   └── health.test.ts
├── package.json
├── tsconfig.json
├── Dockerfile
├── .env.example
├── .eslintrc.json
├── jest.config.ts
└── README.md
```

## 3. File Classification

| Category | Count | Examples |
|----------|-------|---------|
| Source code | 7 | `src/index.ts`, `src/routes/todos.ts`, `src/models/todo.ts` |
| Configuration | 5 | `package.json`, `tsconfig.json`, `.eslintrc.json`, `jest.config.ts`, `.env.example` |
| Test | 2 | `tests/todos.test.ts`, `tests/health.test.ts` |
| Documentation | 1 | `README.md` |
| Build artifact | 0 | — |
| Static asset | 0 | — |

## 4. Entry Points

| File | Role | Evidence |
|------|------|----------|
| `src/index.ts` | Application bootstrap | Named `index.ts` in `src/`, contains Express `app.listen()` |
| `Dockerfile` | Container entry | `CMD ["node", "dist/index.js"]` |

## 5. Configuration Files

| File | Role | Evidence |
|------|------|----------|
| `package.json` | Package manager | npm manifest at project root |
| `tsconfig.json` | TypeScript compiler | TypeScript config |
| `.eslintrc.json` | Linter | ESLint configuration |
| `jest.config.ts` | Test framework | Jest configuration |
| `.env.example` | Environment variables | Environment template |
| `Dockerfile` | Container | Docker build definition |

## 6. Ignored Patterns

- `node_modules/`, `.git/`, `dist/`, `coverage/`
