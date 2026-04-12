# Arch → Verify Input Contract (Indirect)

Verify does not consume Arch artifacts directly. It reaches Arch through Impl's `component_ref` / `arch_refs` and DevOps's `arch_refs` / `re_refs` chains. This document maps how Arch artifacts influence Verify behaviour.

## ARCH-COMP-* → Service Topology and Scenarios

| Arch field (via Impl) | Verify usage |
|-----------------------|-------------|
| `type` (service, store, queue, gateway) | Determine Docker service category (application, infrastructure). |
| `dependencies[]` | Derive startup order and failure scenarios (what happens when a dependency is unavailable). |
| `interfaces[]` | Derive health check endpoints, exposed ports, API contracts for integration scenarios. |
| `responsibilities` | Understand what each service should do — informs expected results in scenarios. |

## ARCH-DIAG-* → Scenario Derivation

| Arch field (via Impl/DevOps refs) | Verify usage |
|-----------------------------------|-------------|
| Sequence diagrams | Each sequence becomes one or more integration scenarios. Participants map to Docker services; messages map to HTTP/gRPC/message calls. |
| Data-flow diagrams | Verify data moves through services in the expected direction. Inform trace propagation validation. |
| C4 Container diagrams | High-level service topology, used to validate Docker Compose matches the intended architecture. |

## ARCH-DEC-* → Expected Behaviour

| Arch field (via Impl IDRs) | Verify usage |
|----------------------------|-------------|
| Decisions with pattern implications | If Arch mandated Circuit Breaker, Verify expects graceful degradation in failure scenarios. If Arch mandated CQRS, Verify tests read and write paths independently. |
| Deployment-related decisions | Inform whether deployment scenarios are relevant. |

## ARCH-TECH-* → Instrumentation Selection

| Arch field (via Impl) | Verify usage |
|-----------------------|-------------|
| `choice` (language, framework) | Select appropriate instrumentation libraries during the `instrument` stage. |

## RE → Verify (via Arch → DevOps)

| RE field (indirect) | Verify usage |
|--------------------|-------------|
| Quality attribute metrics (e.g., "response time < 200ms") | Validate that SLO metrics are actually collectible and within range. |
| Acceptance criteria | Integration scenario expected results may reference RE criteria. |
| Constraints (e.g., PII masking) | Log masking verification scenarios. |

## Traceability chain

Verify closes the chain:
```
RE quality attribute → Arch decision (re_refs) → Impl code (arch_refs) → DevOps SLO (impl_refs) → Verify evidence
```

For each scenario, the report should cite the full chain where possible.
