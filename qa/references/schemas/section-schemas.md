# Section Schemas

The four QA sections each carry their own structured block inside the metadata file. The block mirrors the tables in the paired markdown document — the markdown is the human-readable source of truth for prose, and the YAML block is what downstream skills and scripts parse. Write these blocks through `artifact.py set-block`, except for `rtm_rows` (`rtm-upsert`) and gate verdict fields (`gate-evaluate`).

Common metadata fields (`artifact_id`, `phase`, `approval`, …) are covered in [meta-schema.md](meta-schema.md).

## 1. `test-strategy`

Block key: `test_strategy` (singular — this section is not a list)

```yaml
test_strategy:
  mode: heavy                  # light | heavy
  scope:
    in:
      - re_id: FR-001
        title: User can log in with email and password
        priority: must
        reason: core domain
    out:
      - re_id: FR-099
        priority: wont
        reason: explicitly deferred per RE
  pyramid:
    - layer: unit
      ratio: 0.60
      rationale: per ARCH-COMP boundary count and IMPL-MAP module fan-out
    - layer: integration
      ratio: 0.25
      rationale: ARCH-COMP-001 ↔ ARCH-COMP-002 contract surface
    - layer: e2e
      ratio: 0.10
      rationale: ARCH-DIAG sequence flow count
  nfr_test_plan:
    - metric_ref: RE-QA-001
      attribute: latency
      target: "p95 < 200 ms"
      scenario: "100 RPS for 5 min on /search"
      tooling: k6
  environment_matrix:
    - environment: ci
      purpose: full suite
      notes: ARCH-TECH-003 pins postgres 16
      constraint_refs: [RE-CON-002]
  test_double_strategy:
    - seam: src/auth → identity provider
      strategy: fake at HTTP layer
      notes: per IDR-002
  quality_gate_criteria:
    code_coverage_min: 0.80
    requirements_coverage_must_min: 1.00
    max_failed_tests: 0
    nfr_metric_refs: [RE-QA-001, RE-QA-002]
```

| Field | Required | Description |
|-------|----------|-------------|
| `mode` | yes | `light` or `heavy`. Picked at the start of the strategy stage. |
| `scope.in` | yes | List of `{re_id, title, priority, reason}`. Every Must/Should RE row in the project. |
| `scope.out` | yes | List of `{re_id, priority, reason}`. Every Won't (and Could that the project decided not to test). |
| `pyramid` | yes | List of `{layer, ratio, rationale}`. Layer ∈ `unit` / `integration` / `e2e` / `contract` / `nfr`. Ratios should sum to ~1.0. |
| `nfr_test_plan` | yes | List of `{metric_ref, attribute, target, scenario, tooling}`. One row per `RE-QA-*` with a `metric`. |
| `environment_matrix` | yes | List of `{environment, purpose, notes, constraint_refs}`. |
| `test_double_strategy` | yes | List of `{seam, strategy, notes}`. One row per `IMPL-CODE-*.external_dependencies`. |
| `quality_gate_criteria` | yes | Object copied verbatim into the Quality Report's `quality_gate.criteria` block. |

## 2. `test-suite`

Block key: `test_suite` (a list — there may be multiple `QA-SUITE-*` artifacts in heavy mode, each with its own list of suites; in practice each artifact has one suite per file but the schema allows grouping)

```yaml
test_suite:
  - id: TS-001
    type: unit                  # unit | integration | e2e | contract | nfr
    title: Auth service unit tests
    target_module: src/auth/
    framework: pytest
    test_files:
      - tests/auth/test_service.py
      - tests/auth/test_repository.py
    re_refs: [FR-002, NFR-003]
    arch_refs: [ARCH-COMP-001, ARCH-DEC-002]
    impl_refs: [IMPL-MAP-001, IMPL-IDR-001]
    test_cases:
      - case_id: TS-001-C01
        description: login with valid credentials returns a session
        technique: example_based
        acceptance_criteria_ref: FR-002.AC-1
        given: a user exists with hashed password
        when: POST /login with correct credentials
        then: 200 with a non-empty session token
        test_node: tests/auth/test_service.py::test_login_with_valid_credentials
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | `TS-NNN`, unique within this artifact |
| `type` | yes | `unit` / `integration` / `e2e` / `contract` / `nfr` |
| `title` | yes | Short human-readable title |
| `target_module` | yes | Repo-relative directory or file the suite targets (mirrors an `IMPL-MAP-*.module_path`) |
| `framework` | yes | The testing framework name + version, taken from `IMPL-CODE-*` or `ARCH-TECH-*` |
| `test_files` | yes | List of repo-relative test source files |
| `re_refs` | yes (at least one) | RE ids the suite covers |
| `arch_refs` | yes (at least one) | Arch ids the suite is anchored to |
| `impl_refs` | yes (at least one) | Impl ids the suite targets |
| `test_cases` | yes (at least one) | List of case objects |

Test case sub-fields:

| Field | Required | Description |
|-------|----------|-------------|
| `case_id` | yes | `TS-NNN-CMM`, unique within the suite |
| `description` | yes | One-line description |
| `technique` | yes | `boundary_value` / `equivalence_partition` / `decision_table` / `state_transition` / `property_based` / `example_based` |
| `acceptance_criteria_ref` | yes | The exact RE criterion this case verifies (e.g. `FR-002.AC-1`) |
| `given` / `when` / `then` | yes | The Given-When-Then triple. `then` must be a concrete observable assertion |
| `test_node` | optional | The test runner's node id (e.g. `tests/x.py::test_y`); enables direct re-run |

## 3. `rtm`

Block key: `rtm_rows` (a list — the only structured field on the RTM artifact)

```yaml
rtm_rows:
  - re_id: FR-001
    re_title: User can log in with email and password
    re_priority: must            # must | should | could | wont
    arch_refs: [ARCH-COMP-001]
    impl_refs: [IMPL-MAP-001]
    test_refs:
      - QA-SUITE-001:TS-001-C01
      - QA-SUITE-001:TS-001-C02
    coverage_status: covered     # covered | partial | uncovered
    gap_description: null
```

| Field | Required | Description |
|-------|----------|-------------|
| `re_id` | yes | RE requirement id (`FR-*` / `NFR-*`) |
| `re_title` | optional | Title for the human-readable rendering |
| `re_priority` | optional | MoSCoW priority (`must` / `should` / `could` / `wont`) — drives `rtm-gap-report` binning |
| `arch_refs` | optional | Arch ids in the chain |
| `impl_refs` | optional | Impl ids in the chain |
| `test_refs` | yes when `coverage_status != uncovered` | Test refs in the form `<suite-id>:<case-id>` |
| `coverage_status` | yes | `covered` / `partial` / `uncovered` |
| `gap_description` | yes when status ∈ `partial` / `uncovered` | One-line explanation of the gap |

**Rule**: rows may only be edited via `artifact.py rtm-upsert`. Direct `Edit`/`Write` against the RTM `*.meta.yaml` is forbidden.

## 4. `quality-report`

Block keys: `quality_report` (presentation), `quality_gate` (criteria + actuals + verdict)

```yaml
quality_report:
  code_coverage:
    by_module:
      - module: src/auth/
        lines: 0.92
        branches: 0.87
        notes: IMPL-MAP-001
    total:
      lines: 0.84
      branches: 0.78
  requirements_coverage:
    by_priority:
      - priority: must
        total: 12
        covered: 12
        partial: 0
        uncovered: 0
      - priority: should
        total: 8
        covered: 6
        partial: 2
        uncovered: 0
  nfr_results:
    - metric_id: RE-QA-001
      target: "p95 < 200 ms"
      actual: "148 ms"
      pass: true
      notes: k6 run id 42
  residual_risks:
    - re_id: FR-014
      priority: should
      status: partial
      reason: IdP stub not in CI; deferred
  recommendations:
    - "Wire the IdP stub into CI before the next release."

quality_gate:
  criteria:
    code_coverage_min: 0.80
    requirements_coverage_must_min: 1.00
    max_failed_tests: 0
  actuals:
    code_coverage: 0.84
    requirements_coverage_must: 1.00
    failed_tests: 0
    nfr_results:
      - metric_id: RE-QA-001
        target: "p95 < 200 ms"
        actual: "148 ms"
        pass: true
  verdict: pass               # pass | fail | escalated; set by gate-evaluate
  reasons:
    - all gate criteria satisfied
  evaluated_at: 2026-04-11T14:00:00Z
```

| Field | Required | Description |
|-------|----------|-------------|
| `quality_report.code_coverage` | yes | Per-module + total line/branch coverage |
| `quality_report.requirements_coverage` | yes | Roll-up of `rtm_rows` by MoSCoW priority |
| `quality_report.nfr_results` | yes when NFR plan is non-empty | Target vs actual for every NFR scenario |
| `quality_report.residual_risks` | yes | Every accepted Should/Could/Won't gap, plus resolved Must escalations |
| `quality_report.recommendations` | optional | Free-form, prioritised |
| `quality_gate.criteria` | yes | Set during the strategy/handoff path via `artifact.py set-block` |
| `quality_gate.actuals` | yes | Set during the report stage by the main agent applying `write-quality-report-actuals` via `artifact.py set-block` |
| `quality_gate.verdict` / `reasons` / `evaluated_at` | yes | Set **only** by `artifact.py gate-evaluate` |
