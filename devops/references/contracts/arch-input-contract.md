# Arch Input Contract

How the DevOps skill reads the four Arch artifacts and turns each field into an infrastructure, pipeline, or observability directive. Read this before `slo` or `iac` when you need to know what a specific Arch field is supposed to produce in DevOps output.

## Location and readiness

- Arch artifacts live in the standalone location `./artifacts/arch/`. In orchestrated runs, Orch passes the exact upstream Arch artifact paths separately. `HARNESS_ARTIFACTS_DIR` still points to DevOps's own output directory.
- The four sections must all be present:
  - `ARCH-DEC-*` — decisions
  - `ARCH-COMP-*` — components
  - `ARCH-TECH-*` — technology stack
  - `ARCH-DIAG-*` — diagrams
- Every one must be in phase `approved`. If any is in `draft` / `in_review` / `revising`, stop and tell the user — DevOps must not run on unstable input.

Use `python ${SKILL_DIR}/../arch/scripts/artifact.py list` (or read the metadata files directly) to confirm. If Orch provided a different upstream directory, walk that directory instead of assuming `./artifacts/arch/`.

## ARCH-DEC-* → deployment shape

| Arch field | DevOps action |
|------------|---------------|
| `id` | Recorded in `DEVOPS-PL-*.upstream_refs` and `DEVOPS-IAC-*.upstream_refs` whenever the decision forces a deployment-level choice |
| `decision` | Drives the deployment unit shape: monolith → single pipeline/single deploy target; microservices → per-service pipeline/per-service deploy target; modular monolith → single pipeline with module-aware health checks |
| `rationale` | Summarised in the IaC module header comment and in the Pipeline Config's strategy rationale section |
| `trade_offs` | Inform deployment method selection: trade-offs favouring availability → blue-green/canary; trade-offs favouring simplicity → rolling update; trade-offs favouring cost → in-place |
| `alternatives_considered` | Used to avoid regenerating rejected deployment approaches if they resurface during strategy selection |
| `re_refs` | Propagated into DevOps artifacts so downstream skills can trace "why" back to RE quality attributes. Every `re_ref` on a deployment-shaping decision must appear on at least one `DEVOPS-OBS-*.slo_definitions` entry or `DEVOPS-IAC-*.upstream_refs` |

**Deployment unit rule**: if the `decision` text names a deployment topology (monolith, per-service, sidecar, serverless), that topology is mandatory and must be reflected in the IaC modules and pipeline structure. It is applied in Stage 2 (iac) and Stage 3 (pipeline) and recorded in their upstream refs.

## ARCH-COMP-* → infra resources

| Arch field | DevOps action |
|------------|---------------|
| `id` | Recorded as `upstream_refs` on the corresponding `DEVOPS-IAC-*` module or resource block |
| `name` | Base name for the IaC module, Kubernetes deployment, or cloud resource (kebab-case or the detected convention) |
| `type` | Maps to cloud resource category: `service` → compute (ECS task, K8s deployment, Lambda), `store` → database (RDS, DynamoDB), `queue` → messaging (SQS, RabbitMQ), `gateway` → load-balancer (ALB, API Gateway, Ingress) |
| `responsibility` | Single-sentence description in the IaC module comment and the resource tag `Description` |
| `interfaces` | Determine health check endpoints: HTTP interfaces → HTTP health check path, gRPC interfaces → gRPC health check service, queue consumers → queue depth metric check. Each interface with a protocol also gets a corresponding port/listener in the load-balancer or service mesh config |
| `dependencies` | Determine deploy order (topological sort of the dependency graph) and service mesh routing rules. Any dependency edge creates a network policy allowing traffic between the two components |
| `re_refs` | Propagated to the IaC module and to the SLO definitions that cover this component |

**Deploy order rule**: `dependencies` define the deploy graph. Components with no inbound dependencies deploy first. Circular dependencies are an Arch contract violation — escalate to the user. The pipeline's deployment stages must respect this ordering.

**Service mesh rule**: when two components declare a dependency, the IaC must include the corresponding service discovery entry and network policy. If the dependency crosses a trust boundary (different `type` categories), add mTLS configuration.

## ARCH-TECH-* → cloud resources

| Arch field | DevOps action |
|------------|---------------|
| `category` | Slot in the IaC module set (language/runtime → container base image, framework → build tooling, DB → managed database, messaging → managed queue, cache → managed cache, observability → monitoring stack) |
| `choice` | Maps to a concrete managed service. This is the **only** allowed set — nothing else may appear in `DEVOPS-IAC-*` resource definitions without a matching `ARCH-TECH-*.choice`. Common mappings: PostgreSQL → RDS/Cloud SQL, Redis → ElastiCache/Memorystore, RabbitMQ → AmazonMQ/CloudAMQP, Kafka → MSK/Confluent Cloud, MongoDB → DocumentDB/Atlas |
| `rationale` | Recorded in the IaC module's header comment to explain why this specific managed service was selected |
| `decision_ref` | When present, the tech choice inherits the ADR's deployment constraints (e.g. an ADR mandating event sourcing constrains the DB to support append-only streams) |
| `constraint_ref` | Must be visibly satisfied in IaC. `hard` constraints enforce provider locks (e.g. "AWS only" → no GCP resources), region locks (e.g. "eu-west-1" → all resources in that region), and compliance requirements (e.g. "SOC2" → encryption at rest enabled). Soft constraints are recorded as comments |

**Service selection rule**: pick the managed service that matches the `choice` on the target cloud provider. If no managed equivalent exists, escalate to the user with self-hosting vs alternative options — do not silently substitute.

## ARCH-DIAG-* → topology

| Diagram type | DevOps action |
|-------------|---------------|
| `c4-context` | Informational only; used to identify external system integrations that require egress rules, API keys, or webhook endpoints in the IaC |
| `c4-container` | Determines the deployment topology: each container maps to a deploy unit in the IaC and a stage in the pipeline. The container boundaries define the network segmentation (VPC subnets, security groups, K8s namespaces) |
| `data-flow` | Identifies monitoring points: each transformation stage in the flow gets a metric (throughput, latency, error rate). Queue-backed flows get depth and age metrics. The data-flow stages map to distributed tracing span names |
| `sequence` | Identifies distributed tracing spans: each inter-component call in the sequence becomes a trace span with timing. The sequence also determines health-check dependency chains (if A calls B calls C, A's health check must verify B's reachability) |

**Topology consistency rule**: the `c4-container` diagram and the `ARCH-COMP-*` entries must agree on the number and boundaries of deploy units. If they diverge, treat the component list as authoritative and flag the diagram inconsistency to the user.

## Traceability propagation

Every IaC module must link upstream to the Arch component it provisions:

```
python ${SKILL_DIR}/scripts/artifact.py link <devops-iac-id> --upstream ARCH-COMP-001
```

Every Pipeline Config must link upstream to the Arch decision that shaped the deployment unit:

```
python ${SKILL_DIR}/scripts/artifact.py link <devops-pl-id> --upstream ARCH-DEC-001
```

Every Observability SLO entry must carry an upstream ref to the Arch decision or component whose `re_refs` it derives from:

```
python ${SKILL_DIR}/scripts/artifact.py link <devops-obs-id> --upstream ARCH-DEC-002
```

Every `re_ref` found on an Arch artifact that influences a DevOps deliverable must be traceable through the chain: `RE-* → ARCH-* → DEVOPS-*`. If a DevOps artifact has no upstream Arch anchor, it does not belong yet.

## When Arch is wrong

If an Arch decision is genuinely unrealisable at the infrastructure level (chosen technology has no managed service on the target cloud, two components' declared dependencies create a circular deploy order, the deployment topology contradicts the component structure, a hard constraint conflicts with the chosen cloud provider), **do not** patch around it inside DevOps. Stop, escalate to the user, and recommend they re-open Arch. Arch is the source of truth for structure.
