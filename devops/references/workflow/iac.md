# Workflow — Stage 2: Infrastructure Code

## Role

Transform Arch component structure and technology stack into IaC (Infrastructure as Code) modules that provision the cloud resources needed to run the system. This stage reads the Arch artifacts to determine *what* to provision and *how* to connect it, producing Terraform modules (or equivalent) that are environment-aware, cost-estimated, and fully traceable to the Arch components they support.

## Inputs

- **ARCH-COMP-\*** — component list with `name`, `type`, `responsibility`, `interfaces`, `dependencies`, and `re_refs`. Each component maps to one or more cloud resources. The `dependencies` field determines network topology and security group rules.
- **ARCH-TECH-\*** — technology stack with `category`, `choice`, `rationale`, `decision_ref`, and `constraint_ref`. Each `choice` maps to a concrete managed service on the target cloud.
- **ARCH-DIAG-\*** — specifically `c4-container` diagrams, which define the deployment topology and network segmentation boundaries.
- **RE constraints** (indirect via Arch `constraint_ref`) — hard constraints drive provider locks, region locks, and compliance requirements (encryption at rest, data residency).

Read [../contracts/arch-input-contract.md](../contracts/arch-input-contract.md) for the full Arch field mapping before beginning this stage.

## Component type to cloud resource mapping

| ARCH-COMP `type` | Cloud resource category | AWS | GCP | Azure |
|---|---|---|---|---|
| `service` | Compute | ECS Fargate / EKS | Cloud Run / GKE | App Service / AKS |
| `store` | Database | RDS / DynamoDB / DocumentDB | Cloud SQL / Firestore / Bigtable | Azure SQL / Cosmos DB |
| `queue` | Messaging | SQS / SNS / MSK | Pub/Sub / Cloud Tasks | Service Bus / Event Hubs |
| `gateway` | Load balancer + API gateway | ALB + API Gateway | Cloud Load Balancing + API Gateway | Application Gateway + API Management |
| `cache` | In-memory cache | ElastiCache (Redis/Memcached) | Memorystore | Azure Cache for Redis |

The specific managed service within each category is determined by `ARCH-TECH-*.choice`. For example, if `ARCH-TECH` specifies `choice: PostgreSQL`, the database resource is RDS PostgreSQL (AWS), Cloud SQL PostgreSQL (GCP), or Azure Database for PostgreSQL. If the `choice` has no managed equivalent on the target cloud, escalate (see Escalation conditions).

## Terraform module structure

Organize IaC into modules that mirror the Arch component boundaries:

```
infra/
├── main.tf                    # Root composition — wires modules together
├── variables.tf               # Top-level input variables
├── outputs.tf                 # Exported values for pipeline consumption
├── backend.tf                 # State management configuration
├── environments/
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── production.tfvars
└── modules/
    ├── networking/            # VPC, subnets, security groups, NAT
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── <component-name>/      # One module per ARCH-COMP
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── ...
```

**Module naming rule**: each `ARCH-COMP-*.name` becomes a module directory name in kebab-case (or the project's detected convention). The module's header comment must reference the `ARCH-COMP-*` id and `responsibility`.

## Environment variable overrides

Define three standard environments unless the Arch or RE constraints specify otherwise:

| Environment | Purpose | Sizing strategy |
|---|---|---|
| `dev` | Development and local testing | Minimum viable (smallest instance types, single AZ, reduced replicas) |
| `staging` | Pre-production validation | Production-like topology, reduced scale |
| `production` | Live traffic | Full scale per RE capacity constraints |

Overrides are expressed as `.tfvars` files. Each environment file overrides only the variables that differ (instance type, replica count, AZ count, feature flags). The base configuration in `variables.tf` uses production defaults so that omitting an override is safe.

## State management

Configure remote state with locking to prevent concurrent modification:

| Backend | Locking mechanism | Configuration |
|---|---|---|
| AWS S3 | DynamoDB table | `backend "s3" { bucket, key, region, dynamodb_table, encrypt = true }` |
| GCP GCS | Built-in | `backend "gcs" { bucket, prefix }` |
| Azure Blob | Built-in lease | `backend "azurerm" { resource_group_name, storage_account_name, container_name, key }` |

State management must include:

- **Encryption at rest**: always enabled (S3 SSE, GCS default encryption, Azure Storage encryption).
- **Versioning**: enabled on the state bucket for rollback capability.
- **Drift detection**: scheduled (weekly minimum) via `terraform plan` in CI with no-apply, alerting on any drift.
- **State isolation**: one state file per environment to prevent cross-environment blast radius.

## Networking

Derive the network topology from `ARCH-COMP-*.dependencies`:

1. **VPC/VNet**: one per environment. CIDR block sized to accommodate all components plus growth headroom (minimum /16 for production).
2. **Subnets**: at minimum, public (load balancers, gateways) and private (services, stores). If Arch has components of `type: store`, add a dedicated data subnet with no internet route.
3. **Security groups / NSGs**: one per component. Inbound rules derived from `ARCH-COMP-*.dependencies` — if component A depends on component B, B's security group allows inbound from A on the relevant port. Default deny all other inbound.
4. **Load balancers**: one per `type: gateway` component. Listener ports from `ARCH-COMP-*.interfaces`. Health check paths from interface definitions.
5. **NAT gateway**: required if private-subnet services need outbound internet access (pulling container images, calling external APIs identified in `ARCH-DIAG-*.c4-context`).

## Cost estimation

Provide a rough monthly cost estimate for the production environment:

1. Identify the primary cost drivers (compute instances, database instances, data transfer).
2. Use the target cloud's pricing calculator or known reference prices.
3. Express as a range (`min` / `max`) in USD to account for variable load.
4. Record in `infrastructure_code.cost_estimate` per the schema in [../schemas/section-schemas.md](../schemas/section-schemas.md).

Cost estimation is **optional** but strongly recommended. If the RE constraints include a budget ceiling, the estimate must demonstrate compliance.

## Output sequence

All metadata operations use `${SKILL_DIR}/scripts/artifact.py`. Never edit `.meta.yaml` files directly.

1. Initialize the IaC section:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py init --section iac
   ```
   This returns the new artifact id (e.g. `DEVOPS-IAC-001`).

2. Fill the paired `.md` file via Edit with:
   - Module inventory (name, path, responsibility, inputs, outputs per module)
   - Environment overrides table
   - State management configuration
   - Networking topology description
   - Cost estimate (if applicable)
   - Optionally write actual `.tf` and Helm files under the project tree

3. Link upstream and set progress:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py set-progress <id> --completed 1 --total 1
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream ARCH-COMP-001
   python ${SKILL_DIR}/scripts/artifact.py link <id> --upstream ARCH-TECH-001
   ```
   Link to every `ARCH-COMP-*` and `ARCH-TECH-*` that contributed to the IaC modules. If RE constraints were a factor, also link `--upstream RE-CON-*`.

4. Transition to review:
   ```bash
   python ${SKILL_DIR}/scripts/artifact.py set-phase <id> in_review
   ```

## Escalation conditions

Escalate to the user **only** when:

- An Arch-chosen technology has **no managed service on the target cloud** (e.g. Arch specifies CockroachDB but the target is AWS with a "managed services only" constraint). Propose alternatives: self-hosted on compute, switch to a compatible managed alternative, or change the cloud provider.
- A **hard constraint** (`constraint_ref` with enforcement level `hard`) specifies a cloud provider or region that conflicts with another hard constraint (e.g. "AWS only" + "data must reside in a region where AWS has no presence").
- The `ARCH-COMP-*.dependencies` graph contains **circular dependencies** that prevent determining a valid deploy order and network topology.
- The cost estimate **exceeds a budget ceiling** specified in the RE constraints and no right-sizing can bring it within range.

Do **not** escalate for:

- Choosing between instance types or sizing tiers (use the smallest production-viable option and note the choice).
- Selecting specific subnet CIDR ranges (use conventional ranges).
- Picking between Terraform module patterns (use the standard structure above).
