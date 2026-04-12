# Impl → Verify Input Contract

This document defines how Verify consumes Impl artifacts to provision the local integration environment.

## IMPL-MAP-* → Service Mapping

| Impl field | Verify usage |
|-----------|-------------|
| `implementation_map[].component_ref` | Maps to `ARCH-COMP-*.type` to determine service type (application container vs infrastructure) |
| `implementation_map[].module_path` | Docker build context path |
| `implementation_map[].entry_point` | Service entry point for container CMD |
| `implementation_map[].interfaces_implemented` | Derive health check endpoints and exposed ports |
| `implementation_map[].arch_refs` | Trace to Arch component for dependency graph |

## IMPL-CODE-* → Build and Dependencies

| Impl field | Verify usage |
|-----------|-------------|
| `code_structure.build_config[]` | Dockerfile generation, build arguments, multi-stage build configuration |
| `code_structure.external_dependencies[]` | Infrastructure service containers (DB, cache, queue images and versions) |
| `code_structure.environment_config[]` | Docker environment variables, connection strings (rewritten for Docker DNS) |
| `code_structure.module_dependencies[]` | Dependency install commands in Dockerfile |

## IMPL-IDR-* → Scenario Derivation

| Impl field | Verify usage |
|-----------|-------------|
| `implementation_decisions[].pattern_applied` | Derive failure scenario expectations (Circuit Breaker → graceful degradation, Retry → eventual success) |
| `implementation_decisions[].arch_refs` | Trace back to Arch decisions for traceability |

## IMPL-GUIDE-* → Build and Run Commands

| Impl field | Verify usage |
|-----------|-------------|
| `implementation_guide.prerequisites[]` | Validate build environment dependencies |
| `implementation_guide.build_commands[]` | Docker image build procedure |
| `implementation_guide.run_commands[]` | Container CMD / entrypoint |
| `implementation_guide.conventions` | Detect logging format, error handling patterns |

## Validation rules

Before provisioning, Verify checks:

1. Every `IMPL-MAP-*` entry has a `component_ref` that resolves to an `ARCH-COMP-*`.
2. Every `external_dependencies[]` entry has enough information to select a Docker image.
3. `build_commands` produce a valid Dockerfile or the source tree already contains one.
4. `environment_config[]` entries cover all connection strings needed for service-to-service communication.

If validation fails, Verify stops and tells the user which Impl artifact needs attention.
