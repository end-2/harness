# Detection Signature Catalog

This catalog lists the file patterns, dependency names, and code signatures used to detect technologies in Stage 2 (detect). Organized by category.

## Languages

Detection is primarily by file extension (handled in Stage 1). Stage 2 refines with version information from manifests.

| Language | Extensions | Version sources |
|----------|-----------|-----------------|
| TypeScript | `.ts`, `.tsx` | `tsconfig.json` target, `package.json` devDependencies.typescript |
| JavaScript | `.js`, `.jsx`, `.mjs`, `.cjs` | `package.json` engines.node |
| Python | `.py` | `pyproject.toml` python_requires, `setup.cfg`, `.python-version`, `runtime.txt` |
| Go | `.go` | `go.mod` go directive |
| Rust | `.rs` | `Cargo.toml` edition, `rust-toolchain.toml` |
| Java | `.java` | `pom.xml` java.version, `build.gradle` sourceCompatibility |
| Kotlin | `.kt`, `.kts` | `build.gradle.kts` kotlinOptions.jvmTarget |
| Ruby | `.rb` | `Gemfile` ruby version, `.ruby-version` |
| PHP | `.php` | `composer.json` require.php |
| C# | `.cs` | `*.csproj` TargetFramework |
| Swift | `.swift` | `Package.swift` swift-tools-version |
| Scala | `.scala` | `build.sbt` scalaVersion |
| Elixir | `.ex`, `.exs` | `mix.exs` elixir |

## Frameworks

### JavaScript / TypeScript ecosystem

| Framework | Dependency name | Config file | Code pattern |
|-----------|---------------|-------------|-------------|
| React | `react` | — | `import React`, `from 'react'`, JSX/TSX files |
| Next.js | `next` | `next.config.js/mjs/ts` | `import from 'next/'`, `pages/` or `app/` directory |
| Nuxt | `nuxt` | `nuxt.config.ts/js` | `import from '#app'`, `.nuxt/` |
| Vue | `vue` | `vue.config.js` | `.vue` files, `import from 'vue'` |
| Angular | `@angular/core` | `angular.json` | `@Component`, `@NgModule` decorators |
| Svelte | `svelte` | `svelte.config.js` | `.svelte` files |
| Express | `express` | — | `require('express')`, `app.get/post/put/delete` |
| Fastify | `fastify` | — | `require('fastify')`, `fastify.register` |
| NestJS | `@nestjs/core` | `nest-cli.json` | `@Module`, `@Controller`, `@Injectable` |
| Hono | `hono` | — | `import { Hono }`, `new Hono()` |

### Python ecosystem

| Framework | Package name | Config | Code pattern |
|-----------|-------------|--------|-------------|
| Django | `django` | `settings.py` | `INSTALLED_APPS`, `urlpatterns`, `from django` |
| Flask | `flask` | — | `from flask import`, `@app.route` |
| FastAPI | `fastapi` | — | `from fastapi import`, `@app.get/post` |
| Starlette | `starlette` | — | `from starlette` |
| SQLAlchemy | `sqlalchemy` | — | `from sqlalchemy`, `Base = declarative_base()` |
| Celery | `celery` | `celeryconfig.py` | `@celery.task`, `from celery import` |
| Pydantic | `pydantic` | — | `from pydantic import BaseModel` |

### Go ecosystem

| Framework | Module | Code pattern |
|-----------|--------|-------------|
| Gin | `github.com/gin-gonic/gin` | `gin.Default()`, `router.GET/POST` |
| Echo | `github.com/labstack/echo` | `echo.New()` |
| Fiber | `github.com/gofiber/fiber` | `fiber.New()` |
| GORM | `gorm.io/gorm` | `gorm.Open`, `db.Create/Find` |
| Chi | `github.com/go-chi/chi` | `chi.NewRouter()` |

### Java / Kotlin ecosystem

| Framework | Dependency | Code pattern |
|-----------|-----------|-------------|
| Spring Boot | `spring-boot-starter` | `@SpringBootApplication`, `@RestController` |
| Quarkus | `io.quarkus` | `@QuarkusMain`, `quarkus.` properties |
| Micronaut | `io.micronaut` | `@MicronautApplication` |

### Rust ecosystem

| Framework | Crate | Code pattern |
|-----------|-------|-------------|
| Actix-web | `actix-web` | `HttpServer::new`, `#[get]/#[post]` |
| Axum | `axum` | `Router::new().route()` |
| Tokio | `tokio` | `#[tokio::main]` |

## Databases

| Database | Detection signals |
|----------|-----------------|
| PostgreSQL | `pg`/`postgres` in deps, `DATABASE_URL` with `postgres://`, Prisma provider `postgresql`, `psycopg2` |
| MySQL | `mysql2`/`mysql` in deps, `DATABASE_URL` with `mysql://`, `pymysql` |
| MongoDB | `mongoose`/`mongodb` in deps, `MONGO_URI`, `pymongo` |
| Redis | `redis`/`ioredis` in deps, `REDIS_URL`, `redis-py` |
| SQLite | `sqlite3`/`better-sqlite3` in deps, `.sqlite`/`.db` files, Prisma provider `sqlite` |
| DynamoDB | `@aws-sdk/client-dynamodb`, `boto3` with dynamodb |
| Elasticsearch | `@elastic/elasticsearch`, `elasticsearch-py` |

## Test frameworks

| Framework | Detection signals |
|-----------|-----------------|
| Jest | `jest` in devDeps, `jest.config.*`, `__tests__/` |
| Vitest | `vitest` in devDeps, `vitest.config.*` |
| Mocha | `mocha` in devDeps, `.mocharc.*` |
| pytest | `pytest` in deps/devDeps, `pytest.ini`, `conftest.py`, `pyproject.toml [tool.pytest]` |
| Go testing | `*_test.go` files, `testing.T` parameter |
| JUnit | `junit` dependency, `@Test` annotations |
| RSpec | `rspec` in Gemfile, `.rspec`, `spec/` directory |
| Playwright | `@playwright/test`, `playwright.config.*` |
| Cypress | `cypress` in devDeps, `cypress.config.*`, `cypress/` directory |

## CI/CD

| System | Detection signals |
|--------|-----------------|
| GitHub Actions | `.github/workflows/*.yml` |
| GitLab CI | `.gitlab-ci.yml` |
| Jenkins | `Jenkinsfile` |
| CircleCI | `.circleci/config.yml` |
| Travis CI | `.travis.yml` |
| Azure Pipelines | `azure-pipelines.yml` |

## Container / Infrastructure

| Technology | Detection signals |
|-----------|-----------------|
| Docker | `Dockerfile`, `docker-compose.yml`, `.dockerignore` |
| Kubernetes | `k8s/` dir, files with `apiVersion: apps/v1`, Helm `Chart.yaml` |
| Terraform | `*.tf` files, `.terraform/` |
| AWS CDK | `cdk.json`, `@aws-cdk/*` dependencies |
| Pulumi | `Pulumi.yaml`, `pulumi` dependencies |
| Serverless Framework | `serverless.yml`, `serverless` dependency |
