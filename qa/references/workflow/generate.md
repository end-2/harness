# Workflow — Stage 2: generate

## Role

Turn the approved Test Strategy into (a) actual test source files under the project tree and (b) the Test Suite section artifacts that record every case with full traceability. Also create the project-wide RTM artifact and seed it with one row per requirement that gains coverage. This is the only stage in QA that *creates* test source files.

## Inputs

- The approved `QA-STRATEGY-*` artifact (scope, pyramid, NFR plan, environment matrix, doubles, gate criteria).
- All `RE-SPEC-*` rows in scope, with their `acceptance_criteria`.
- All `RE-QA-*` rows with a `metric`.
- The Arch and Impl artifacts already cited by the strategy.
- The existing project tree as the destination for the test files.

## Acceptance criteria → test cases

For every in-scope `RE-SPEC-*` row, walk its `acceptance_criteria` list and convert each criterion into one or more Given-When-Then cases. Pick a `technique` deliberately, never by reflex:

| Technique | When to use |
|-----------|------------|
| `boundary_value` | the criterion talks about ranges, limits, off-by-one, or "at most / at least N" |
| `equivalence_partition` | the criterion has discrete categories of input that should behave the same |
| `decision_table` | the criterion has multiple flag combinations that produce different outcomes |
| `state_transition` | the criterion is about a state machine — entry conditions and legal next states |
| `property_based` | the criterion is invariant-shaped ("for all inputs X, Y holds") and has a generator |
| `example_based` | everything else — the default for prose criteria with no obvious shape |

Every case must:

- Cite an `acceptance_criteria_ref` back to the exact RE criterion.
- Be expressible as one observable assertion (no "the system should be reliable").
- Live in the test framework recorded in `IMPL-CODE-*.external_dependencies` (or `ARCH-TECH-*` if Impl is silent).
- Be placed where `IMPL-GUIDE-*.conventions.tests` says tests live; fall back to the stack idiom only when the convention is silent.

## Mapping to test type

| Test type | Trigger |
|-----------|---------|
| `unit` | covers a single Impl module / function in isolation; uses test doubles for collaborators |
| `integration` | crosses an `ARCH-COMP-*.interfaces` boundary; runs against a real or in-memory implementation of the next layer |
| `e2e` | follows an `ARCH-DIAG-*` sequence diagram from input to output; touches the real system entry points |
| `contract` | verifies a wire-level contract with an external (or sibling) component, usually in microservice topologies |
| `nfr` | verifies a `RE-QA-*.metric` with a measurable scenario (latency, throughput, availability, …) |

A single `acceptance_criteria` row may produce cases of multiple types — that is fine.

## Output — the Test Suite + RTM sections

Create the suite artifacts in order, then the project-wide RTM:

1. `artifact.py init --section test-suite` — once per Arch component group, or once total in light mode.
2. `artifact.py init --section rtm` — once for the whole project. The script refuses a second RTM init.

For each suite:

1. Edit the `.md` file via Edit (never `.meta.yaml`).
2. Write the actual test files with Write/Edit. They are not tracked by `artifact.py`.
3. Write the structured `test_suite[]` payload via `artifact.py set-block` (the next iteration of `init` and `set-progress` will not touch this list, so generation owns the full replacement payload):
   ```
   python ${SKILL_DIR}/scripts/artifact.py set-block <suite-id> --field test_suite --from /tmp/test-suite.yaml
   ```
4. Refresh the RTM as soon as a requirement gains coverage:
   ```
   python ${SKILL_DIR}/scripts/artifact.py rtm-upsert \
       --re-id FR-001 \
       --re-title "User can log in with email and password" \
       --re-priority must \
       --arch-refs ARCH-COMP-001 \
       --impl-refs IMPL-MAP-001 \
       --test-refs QA-SUITE-001:TS-001-C01,QA-SUITE-001:TS-001-C02 \
       --status covered
   ```
5. Add traceability:
   ```
   python ${SKILL_DIR}/scripts/artifact.py link <suite-id> --upstream RE-SPEC-001
   python ${SKILL_DIR}/scripts/artifact.py link <suite-id> --upstream IMPL-MAP-001
   python ${SKILL_DIR}/scripts/artifact.py link <suite-id> --upstream ARCH-COMP-001
   ```
6. Update progress and transition to `in_review`:
   ```
   python ${SKILL_DIR}/scripts/artifact.py set-progress <suite-id> --completed N --total M
   python ${SKILL_DIR}/scripts/artifact.py set-phase <suite-id> in_review
   ```

For requirements that the strategy ruled in but the project genuinely cannot test yet, call `rtm-upsert` with `--status partial` (or `uncovered`) and a one-line `--gap` description. Stage 3 will pick those up and either route them back here or escalate.

## Conventions

- **AAA pattern** (Arrange-Act-Assert) for unit tests; Given-When-Then phrasing in the markdown view, code-level AAA in the actual test file.
- **One assertion per case** unless the technique demands a small set (decision tables, parameterised tests).
- **No hidden state**: no shared module-level fixtures that cross test boundaries. If a test depends on another test's side effect, that is a flaky pattern — split or fix.
- **Naming**: follow `IMPL-GUIDE-*.conventions.tests` exactly. Do not invent a parallel naming scheme.
- **Fixtures**: prefer the framework's idiomatic fixture mechanism (pytest fixtures, vitest setup, JUnit @BeforeEach, …) over module-level globals.

## Escalation

Escalate when:

- A required test type implies infrastructure that does not exist and cannot be substituted (e.g. an NFR metric that needs k8s load gen on a local-only project).
- An `acceptance_criteria` row is so vague that no observable assertion can be derived. Ask the user (or send back to RE) rather than fabricate.
- A test framework is implied by Arch but is incompatible with the existing project (e.g. JUnit on a Node project).

Do **not** escalate for:

- Choice of fixture style, test file naming, or assertion library — detect or fall back to the stack idiom.
- "Should I write more tests for this case?" — apply the technique honestly and stop when the criterion is covered.
