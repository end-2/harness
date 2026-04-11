# Adaptive Depth

Impl runs in one of two modes — **light** or **heavy** — and the mode drives how much of the four-stage workflow actually executes. The goal is correct sizing: a CRUD scaffold should not carry nine IDRs and a multi-module structure, and a genuinely distributed system should not get a single-file drop.

## How the mode is decided

Impl's mode is **inherited from Arch's mode**. Arch already made the sizing call using RE's density; Impl follows it directly, so the pipeline stays coherent.

| Arch mode (from `./artifacts/arch/`) | Impl mode | Rationale |
|-------------------------------------|-----------|-----------|
| Arch ran in light mode: C4 Context only, ≤ 2 ADRs, style + directory recommendation instead of formal components | **light** | A system small enough for light Arch is also small enough for light Impl |
| Arch ran in heavy mode: full component decomposition with interfaces, ADRs per significant decision, Container + sequence diagrams | **heavy** | Every heavy Arch signal (boundaries, ADRs, diagrams) needs a corresponding Impl artifact |

**Detection**: read the Arch metadata. Specifically:

1. If `ARCH-DIAG-*` has a Container diagram → heavy.
2. Or if `ARCH-DEC-*.architecture_decisions` has more than 2 entries → heavy.
3. Or if `ARCH-COMP-*.components` has more than 3 entries → heavy.
4. Otherwise → light.

Tell the user which mode you chose and which signal you used. The user may override by saying "run Impl in heavy mode" or "run Impl in light mode" — record the override in the Implementation Guide.

## What light mode means

Light mode is **not lazy**. It is "correct for a small system".

| Stage | Light mode action |
|-------|------------------|
| generate | Single-project scaffold (one `src/`, one `tests/`). Inline implementation notes in the module docstrings instead of full Impl sections. Still create all four section artifacts, but keep them short. |
| pattern | Apply only Arch-mandated patterns. Skip discretionary patterns unless a smell is obvious. IDR count typically 0–2. |
| review | Run the Arch-compliance axis and a lightweight clean-code pass (naming, obvious bugs, baseline security). Skip deep SOLID analysis. |
| refactor | Run only if `review` finds auto-fixable issues. Skip otherwise. |

Four sections are still produced, but with the following trimmed depth:

- **Implementation Map**: one or two `IM-xxx` entries (usually one per top-level directory).
- **Code Structure**: directory layout + a short external dependency list. No Mermaid dependency graph required.
- **Implementation Decisions**: 0–2 IDRs.
- **Implementation Guide**: prerequisites + setup + build + run. Conventions section may be brief.

## What heavy mode means

| Stage | Heavy mode action |
|-------|------------------|
| generate | Multi-module project structure. One module per `ARCH-COMP-*` or a tight grouping. Full interface-contract code. All four Impl sections in full form. |
| pattern | Apply Arch-mandated patterns *and* run the discretionary-pattern pass. Record every applied pattern as an IDR. |
| review | Both axes in full: Arch compliance and full clean-code review including SOLID, complexity metrics, and baseline security. Run as a subagent. |
| refactor | Run for every auto-fixable issue. Record non-trivial refactors as IDRs. Loop until review is clean. |

Four sections in full form:

- **Implementation Map**: one entry per Arch component, with full `internal_structure` and `interfaces_implemented` lists.
- **Code Structure**: directory layout + Mermaid dependency graph + full external dependency list with tech-stack refs on every row.
- **Implementation Decisions**: one IDR per significant code-level decision (expect several).
- **Implementation Guide**: full prerequisites, setup, build, run, conventions, and extension points.

## Mode is not about quality

Both modes produce production-shaped code. Mode controls **how much structure travels alongside the code**, not how carefully the code is written. A light-mode Impl still respects Arch, still follows detected conventions, still runs the review pass. It just does not generate seven IDRs when two would cover the decisions actually made.
