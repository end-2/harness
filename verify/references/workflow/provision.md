# Provision — Environment Provisioning Stage

**Role**: Transform Impl source code and DevOps infrastructure/observability artifacts into a working Docker Compose local environment.

**Runs in**: main agent (requires user interaction for environment issues).

## Entry conditions

- All Impl artifacts (`IMPL-MAP-*`, `IMPL-CODE-*`, `IMPL-IDR-*`, `IMPL-GUIDE-*`) are in `approved` phase.
- All DevOps artifacts (`DEVOPS-PL-*`, `DEVOPS-IAC-*`, `DEVOPS-OBS-*`, `DEVOPS-RB-*`) are in `approved` phase.
- Docker daemon is running and accessible.

If any artifact is not approved, stop and tell the user.

## Adaptive depth decision

Read the upstream artifacts and determine the mode **before generating anything**:

- Count Arch components (via `IMPL-MAP-*.component_ref` unique values).
- Check if multi-environment is indicated (via `DEVOPS-IAC-*.environments`).
- If components ≤ 3 and single environment → **light** mode.
- Otherwise → **heavy** mode.

Tell the user which mode you chose and why. Read [adaptive-depth.md](../adaptive-depth.md) for the full rule set.

## Service mapping rules

### Application services

For each `IMPL-MAP-*` entry:

1. Read `component_ref` → find the corresponding `ARCH-COMP-*.type`.
2. If `type == service` → create an application container.
3. Build context: `IMPL-MAP-*.module_path`.
4. Entry point: derive from `IMPL-GUIDE-*.run_commands` or the Dockerfile if present.
5. Ports: derive from `ARCH-COMP-*.interfaces` (look for HTTP endpoints, gRPC ports).
6. Environment variables: from `IMPL-CODE-*.environment_config` — transform to Docker env format, replacing hostnames with Docker service names (e.g., `localhost:5432` → `postgres:5432`).

### Infrastructure services

For each entry in `IMPL-CODE-*.external_dependencies`:

1. Map the dependency type to a Docker image:
   - PostgreSQL → `postgres:16`
   - Redis → `redis:7-alpine`
   - RabbitMQ → `rabbitmq:3-management`
   - MongoDB → `mongo:7`
   - Kafka → `confluentinc/cp-kafka:latest` + `confluentinc/cp-zookeeper:latest`
2. Configure with sensible development defaults (non-production passwords, basic auth).
3. Add health checks appropriate to the service type.

### Observability stack

Read `DEVOPS-OBS-*` to provision the observability layer:

**Prometheus** (both modes):
- Generate `monitoring/prometheus.yml` with scrape targets for all application services.
- Copy `DEVOPS-OBS-*.monitoring_rules` into `monitoring/alerts.yml`.
- Scrape interval: 5s for local verification (faster feedback than production).

**Grafana** (both modes):
- Provision datasource config pointing to Prometheus (and Loki/Tempo in heavy mode).
- Copy `DEVOPS-OBS-*.dashboards` into `monitoring/dashboards/`.
- Enable anonymous admin access for frictionless local use.

**Loki** (heavy mode only):
- Configure log collection from application services via Docker log driver.
- Set up LogQL-ready indexing.

**Tempo** (heavy mode only):
- Configure OTLP receivers (gRPC on 4317, HTTP on 4318).
- Wire application services' `OTEL_EXPORTER_OTLP_ENDPOINT` to Tempo.

## Docker network configuration

- Create a single bridge network (`verify-net`) for all services.
- All services join this network, enabling DNS-based service discovery.
- Expose only necessary ports to the host (application endpoints, Grafana, Prometheus).

## Startup order

Derive from the Arch component dependency graph (via `ARCH-COMP-*.dependencies`):

1. Infrastructure services with no dependencies first (databases, caches, queues).
2. Application services that depend only on infrastructure.
3. Application services that depend on other application services.

Use `depends_on` with `condition: service_healthy` to enforce startup ordering via health checks.

## Health checks

For each service, configure a health check:

- **Application services**: use the health endpoint from `ARCH-COMP-*.interfaces` (typically `GET /health` or `GET /actuator/health`).
- **Databases**: use native readiness commands (`pg_isready`, `redis-cli ping`, `mongosh --eval 'db.runCommand("ping")'`).
- **Message queues**: use management API or native health commands.
- **Observability services**: use their built-in health/ready endpoints.

## Output

Create the Environment Setup artifact:

```bash
python ${SKILL_DIR}/scripts/artifact.py init --section environment
```

Fill in:
1. The markdown body (`VERIFY-ENV-*.md`) with service details, network topology, startup order.
2. The structured metadata fields via `set-progress` and `link`.
3. The actual files: `docker-compose.verify.yml`, `monitoring/prometheus.yml`, `monitoring/grafana/provisioning/`, dashboard files.

## Escalation conditions

- **Docker daemon not running**: tell the user to start Docker.
- **Required ports occupied**: list the conflicting ports and suggest alternatives.
- **Insufficient resources**: warn if the host has < 4GB available memory (rough heuristic for a full stack).
- **Impl code fails to build**: report the build error with the specific `IMPL-MAP-*` entry and suggest the user fix it in the Impl skill.
- **Missing Dockerfile or build config**: if `IMPL-GUIDE-*.build_commands` doesn't produce a valid Docker build, escalate.
