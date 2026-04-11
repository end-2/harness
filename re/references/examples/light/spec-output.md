# Example — Light Mode Spec Output

Excerpt of the three markdown artifacts produced at the end of `spec` for the bookmark-feature example (continuing from [elicit-conversation.md](elicit-conversation.md)).

---

## `RE-REQ-001.md` (Requirements Specification)

```markdown
# Requirements Specification

## 1. Overview

Add a per-note favourites feature to the existing note-taking app. Users can
toggle a binary "favourite" flag on any note, filter the sidebar to show only
favourites, and the state syncs across devices via the existing note sync.

## 2. Functional Requirements

| ID | Title | Description | Priority | Acceptance Criteria | Source | Dependencies |
|----|-------|-------------|----------|--------------------|--------|--------------|
| FR-001 | Toggle favourite on a note | A user can mark any note as favourite or un-favourite it. Binary flag. | Must | - Toggle is accessible from the note view<br>- State persists on page reload<br>- Toggle reflects current state correctly | user-prompt | — |
| FR-002 | Favourites sidebar filter | A sidebar filter lists only notes currently marked favourite. | Must | - Filter entry in sidebar<br>- Selecting it hides non-favourited notes<br>- Deselecting restores the full list | user-prompt (turn 1) | FR-001 |
| FR-003 | Cross-device sync of favourite state | Favourite state syncs across a user's devices via the existing sync pipeline. | Must | - Toggle on device A is visible on device B after sync | user-prompt (turn 1) | FR-001, CON-001 |
| FR-004 | Auto-cleanup on note delete | Deleting a favourited note removes it from favourites silently. | Should | - Deleted note does not appear in the favourites filter<br>- No orphan entry remains in storage | user-prompt (turn 1) | FR-001, FR-002 |

## 3. Non-Functional Requirements

| ID | Category | Title | Description | Priority | Acceptance Criteria | Source |
|----|----------|-------|-------------|----------|--------------------|--------|
| NFR-001 | performance | Instant toggle | Toggling favourite feels instant from the user's perspective. | Must | - Client-side toggle round trip < 100ms at 95th percentile | user-prompt (turn 2) |

## 4. Open Questions

(none at approval time)
```

---

## `RE-CON-001.md` (Constraints)

```markdown
# Constraints

## 1. Technical Constraints

| ID | Title | Description | Rationale | Impact | Flexibility |
|----|-------|-------------|-----------|--------|-------------|
| CON-001 | Reuse existing note sync | Favourite state must travel through the existing note sync transport, not a new channel. | Team does not want a second sync system to operate. | Violating adds operational burden and a new class of sync bugs. | hard |

## 2. Business Constraints
_(none for this feature)_

## 3. Regulatory Constraints
_(none for this feature)_

## 4. Environmental Constraints
_(none for this feature)_
```

---

## `RE-QA-001.md` (Quality Attribute Priorities)

```markdown
# Quality Attribute Priorities

## 1. Priority Ranking

| Rank | Attribute | Description | Metric | Trade-off Notes |
|------|-----------|-------------|--------|----------------|
| 1 | usability | The toggle must feel instant and effortless; users will use it dozens of times per session. | Click-to-visible-state-change < 100ms p95 (client-side) | Accepted at the cost of stronger consistency guarantees — brief divergence across devices during sync is acceptable. |
| 2 | consistency | Favourite state must eventually match across a user's devices. | Sync convergence < 5 seconds under normal connectivity | Accepted at the cost of strict read-your-writes across devices during offline periods. |
| 3 | performance | Filter operation must handle typical note counts (< 500) without jank. | Filter render < 16ms for 500 notes | — |

## 2. Rationale

Usability wins the top slot because the entire value of the feature is "a fast
way to mark and find favourites" — any latency kills the point. Consistency
ranks second because cross-device correctness matters, but only eventually:
users will not notice a 1–2 second delay. Performance ranks third because the
upper bound on notes is small; this is essentially free.
```

---

## Corresponding metadata state (light)

At approval time:

```
RE-REQ-001  section=requirements         phase=approved  approval=approved
RE-CON-001  section=constraints          phase=approved  approval=approved
RE-QA-001   section=quality-attributes   phase=approved  approval=approved
```

Progress on each is `5/5`, `1/1`, `3/3` respectively. `upstream_refs` on all three point at `user-prompt:bookmark-feature`. `downstream_refs` are empty until `arch:design` or `qa:strategy` picks them up.
