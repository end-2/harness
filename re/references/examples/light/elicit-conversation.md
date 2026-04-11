# Example — Light Mode Elicit Conversation

A short example of how an `elicit` dialogue looks in light mode. The user starts with a terse prompt and RE walks them through targeted questions in batches.

---

**User**: "Add a bookmark button to my note-taking app so users can favourite notes."

**RE (elicit, turn 1)**:

> I have a good high-level read; let me ask a focused batch before I draft anything. Three small groups:
>
> **Scope**
> 1. Is "favourite" a binary flag per note, or a list the user can reorder?
> 2. Does a user have one favourites list, or multiple (folders/collections)?
>
> **Visibility & sync**
> 3. Does the favourites state need to sync across devices, or is local-only fine?
> 4. Is there a "favourites" filter in the note list, or is favourite state only visible on the note itself?
>
> **Edge cases**
> 5. What happens if a favourited note is deleted — does the favourite silently disappear, or do we show a tombstone?

**User**: "Binary flag. One list. Needs to sync across devices like the rest of the notes. Yes, a filter in the sidebar. Deleted note should just silently vanish from favourites."

**RE (elicit, turn 2)**:

> Got it. One more batch, then I'll summarise:
>
> **Performance expectations**
> 6. How many notes does a typical user have? (just to know if "filter by favourite" is an in-memory scan or needs a DB index)
> 7. Is toggling favourite expected to feel instant, or is a short spinner acceptable?
>
> **Observability**
> 8. Do you want analytics on how often favourite is used, or is that out of scope for v1?

**User**: "Most users have under 500 notes. Toggling should feel instant. No analytics for v1."

**RE (elicit, summary)**:

> Here is what I have so far.
>
> **Candidate FRs**
> - FR-001 Toggle favourite on a note (binary, Must)
> - FR-002 Sidebar filter: show only favourited notes (Must)
> - FR-003 Favourites state syncs across devices via the existing note sync (Must)
> - FR-004 Deleted note auto-removes from favourites (Should)
>
> **Candidate NFRs**
> - NFR-001 Favourite toggle latency < 100ms on the client (Must) — "feels instant"
>
> **Candidate constraints**
> - CON-001 Sync must reuse the existing note sync transport (technical, hard) — rationale: no new sync channel
>
> **Candidate quality attributes (tentative)**
> 1. usability (instant toggle is a UX quality)
> 2. consistency (sync correctness across devices)
> 3. performance (filter with up to 500 notes is trivial but record the metric)
>
> **Open questions**: none that I need to block on.
>
> **Mode**: Light — 4 FRs, 1 NFR, 3 quality attributes, no regulatory context. I'll skip the full trade-off matrix.
>
> Happy to proceed to `analyze`? Any of the above you want to change first?

**User**: "Looks right. Keep going."

---

## What this example illustrates

- **Batched questions**, not one-per-turn
- **Categorisation** (scope / visibility / performance / observability) so the user understands why each question exists
- **Confirmation summary** before leaving `elicit`
- **Explicit mode declaration** at the end
- Light mode: a single short dialogue is enough; no multi-paragraph exploration.
