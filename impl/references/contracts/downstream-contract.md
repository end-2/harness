# Downstream Consumption Contract

What downstream skills (`qa`, `security`, `deployment`, `operation`, `management`) expect to find in the four Impl sections. Read this before transitioning any Impl artifact to `approved`, so you can verify the hand-off is consumable.

## qa — test strategy and coverage

**Reads**: `IMPL-MAP-*`, `IMPL-CODE-*`, `IMPL-IDR-*`.

- `IMPL-MAP-*.module_path` / `entry_point` → list of modules to cover; one test-module per Impl-map entry is a reasonable default.
- `IMPL-MAP-*.interfaces_implemented` → the contract each test should check.
- `IMPL-CODE-*.module_dependencies` → the graph that tells qa whether a test is a unit, integration, or end-to-end test.
- `IMPL-IDR-*.pattern_applied` → each pattern has its own testability rules (e.g. Repository → fakes at the seam, Strategy → one test per strategy, Decorator → verify the wrapped behaviour is preserved).

qa will fail its run if: a component has no matching Implementation Map entry, or a pattern IDR does not name the testing seam, or `IMPL-CODE-*.external_dependencies` includes a runtime dependency without a test double recommendation.

## security — threat modelling and code-level review

**Reads**: `IMPL-MAP-*`, `IMPL-CODE-*`, `IMPL-IDR-*`.

- `IMPL-MAP-*` → attack surface: every component that is listed as external-facing (type = service or edge) is a trust boundary.
- `IMPL-CODE-*.external_dependencies` → dependency vulnerability scan targets.
- `IMPL-IDR-*` → code-level security-relevant choices (token storage, serialisation format, input-validation pattern). security will grade the coverage.

security will fail its run if: any trust boundary is unclear in Implementation Map, or any dependency lacks version pinning in `IMPL-CODE-*.external_dependencies`.

## deployment — build and release

**Reads**: `IMPL-CODE-*`, `IMPL-GUIDE-*`.

- `IMPL-CODE-*.build_config` → the set of build artefacts to produce (container images, JARs, executables, wheels).
- `IMPL-CODE-*.environment_config` → the set of environment variables / secrets each artefact requires.
- `IMPL-GUIDE-*.prerequisites` → runtime versions the deployment target must satisfy.
- `IMPL-GUIDE-*.build_commands` / `run_commands` → the canonical commands deployment automation invokes.

deployment will fail its run if: `build_config` is missing a build file for a runtime that `IMPL-GUIDE-*.prerequisites` names, or `run_commands` references a variable that is not in `environment_config`.

## operation — runbooks and monitoring

**Reads**: `IMPL-MAP-*`, `IMPL-GUIDE-*`, `IMPL-IDR-*`.

- `IMPL-MAP-*.module_path` → the operational unit; one runbook per operationally-distinct module.
- `IMPL-GUIDE-*.extension_points` → where operators should not touch without going through the correct seam.
- `IMPL-IDR-*.pattern_applied` → each pattern has its own operational shape (e.g. Circuit Breaker → dashboard, Outbox → DLQ handling).
- `IMPL-GUIDE-*.run_commands` → the commands the runbook's "restart" / "rollback" steps wrap.

## management — technical debt and onboarding

**Reads**: `IMPL-IDR-*`, `IMPL-GUIDE-*`.

- `IMPL-IDR-*` → every recorded trade-off and deliberate shortcut is a candidate for the debt register.
- `IMPL-GUIDE-*.conventions` → used as the first-day onboarding reference for new contributors.
- `IMPL-GUIDE-*.extension_points` → the "where do I add this?" answer.

## Downstream linking

Before approving, for each downstream skill the Impl artifacts will feed, add a downstream ref:

```
python ${SKILL_DIR}/scripts/artifact.py link <impl-map-id> --downstream QA-STRATEGY-001
```

If the downstream artifact does not exist yet, leave the downstream_ref list empty — the downstream skill will back-fill when it runs. What matters at Impl approval time is that the upstream refs (back to Arch and RE) are complete.
