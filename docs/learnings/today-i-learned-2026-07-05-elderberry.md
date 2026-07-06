# TIL 2026-07-05 — ELDERBERRY

**Context:** A render + character-data session on the fighter outline and Birky's posture. Shipped #573 (raise the name label above the ears), #585 (kill the body↔tail outline seam), #565→#589 (Birky Kirby-low crouch: research → owner decision → DEV slice), and #592→#603 (Project M crouch-movement research → post-v1 crawl mechanic). Also filed follow-ups #564/#572 lineage tickets and reviewed my own tickets before taking them.

---

## 1. An internal seam is a z-order bug — draw all halos behind, then all bodies

**What happened:** The fighter's slot-coloured outline (#546/#564/#572) showed a ring-coloured line *between* the body and the tail (#585). Cause: each part outlined itself and was drawn as an independent halo+body stack — the tail (halo→body) onto the surface, then the body composite (its own ring baked behind its own pixels) on top. Where the tail base overlapped the body, the body composite's ring landed *over* the already-drawn tail body.

**What I learned:** The fix isn't a smarter mask — it's ordering. I split the body composite into two depth layers (`_cat_body_layers` → `(ring_layer, body_layer)`) and drew **ring → tail → body**: every outline behind every body pixel. The tail body then covers the body-ring at the overlap, so no ring segment survives on the join. Critically, I kept `_cat_body_surface` (the merged composite) byte-identical by rebuilding it via the original sequence, so the render-cache parity oracle and the #564/#572 silhouette tests needed **zero** changes.

**The rule:** When an outline seams at an internal junction of composited parts, it's a draw-order defect — draw all the halos first and all the bodies second; don't try to patch it per-part.

---

## 2. No primary source → surface a game-designer decision, don't guess

**What happened:** #565 asked whether Birky's crouch (inherited `(40,40)` under a 44 stand — a 4px drop) was too tall. It was, measurably (9% drop vs the default proportion's 33%). But crouch *height* is engine/model-side in PM — not in rukaidata's scripted move data — and Birky's own sizes are pycats approximations, so there was **nothing to cite**.

**What I learned:** The right move under RULES ("changing a value needs a basis") is not to pick a game-feel number and not to stall — it's to compute proposals (ratio-matched vs Kirby-low) and put the call to the owner via `AskUserQuestion`. The answer ("Kirby-low", `(40,24)`/`(40,14)`) *is* the basis (recorded TUNED), and then the change lands as a **separate DEV slice** (#589), keeping implementation out of the research ticket. #589 was also not a one-liner: combat tests the crouch *hurtbox circles*, so the inherited circles had to be re-authored to fit the shorter box.

**The rule:** A value with no citable source is a decision, not a guess — propose concrete options, get the owner's ratification, then implement in a DEV slice separate from the research.

---

## 3. Cite primary, not inference — including in your own ticket framing

**What happened:** I filed #592 (can all PM characters move while crouching?) asserting crawl is a mechanic "only some characters have it in **Melee**/PM." When I took the ticket and actually pulled the source, crawling **didn't exist in Melee** — it was introduced in **Brawl** and PM inherits it. I'd stated a parity fact from memory.

**What I learned:** The cite-primary discipline (RULES; the #520→#537 correction) applies to the *setup* of a research ticket too, not just its findings. The ticket's own research caught and corrected it, and I logged it (error id=75). Good outcome, but the assumption should never have shipped in the ticket text.

**The rule:** Any PM mechanic claim — even one line of context in a ticket you're filing — needs a primary source before it's asserted; label everything else as inference.

---

## 4. A generated doc's source of truth is its inputs — don't hand-edit the artifact

**What happened:** "File crawl to the roadmap" — but `docs/roadmap.md` says at the top it's **generated from the `v1`/`post-v1` labels**, and it hadn't been regenerated since it was created (#560), so its counts were already stale. Hand-adding a crawl line would desync it and get dropped on the next regen.

**What I learned:** The durable action was to file the crawl issue (#603) with the `post-v1` label — the label *is* the roadmap entry; the doc is just a view. I surfaced that the .md is a stale generated snapshot and offered a separate regen ticket, rather than silently editing a generated file.

**The rule:** Before editing a file, check whether it's generated — if so, change the source (here: the label) and regenerate; don't hand-edit the artifact.

---

## 5. A colour assertion must exclude same-coloured siblings; prove it able-to-fail

**What happened:** #585's regression test needed to prove "no body-ring paints over the tail." A naïve scan for ring-coloured pixels would also catch the name label (same slot colour). I built a precise detector instead: pixels the *tail body* occupies that the *full render* shows in the ring colour. Revert-check: **41** such pixels with the old order, **0** with the fix.

**What I learned:** This is the same pitfall that bit the #572 ring test (which counted the name label and passed even when the ring was reverted). The detector has to isolate the element under test from every other element drawn in that colour, and the revert-check is what proves it isolated correctly.

**The rule:** When asserting a rendered colour, exclude other elements drawn in that same colour, and confirm the test goes red on the reverted code — a colour test that can't fail is a Liar.

---

## What landed

| Artifact | Change |
|---|---|
| `render_battle.py` `NAME_LABEL_OFFSET_Y` | 25→35 so the name label clears the ears (#573) |
| `render_battle.py` `_cat_body_layers` / `render_battle` | split ring/body layers, draw ring→tail→body — no junction seam (#585) |
| `characters/birky_cat.py` | own Kirby-low crouch `(40,24)`/prone `(40,14)` + re-authored posture hurtboxes (#589) |
| #603 (filed) | post-v1 crawl mechanic + crawler roster, from #592 research |

## Open threads

- `docs/roadmap.md` is a stale label-generated snapshot — offered a regen ticket; not yet filed.
- Minor CLI slip logged: `pmtools release` is positional-only (`release <N>`, no `--as`) — error id=71.

## Related artifacts

- Issues #573, #585, #565, #589, #592, #603
- Errors id=71 (release syntax), id=75 (Melee-vs-Brawl crawl)
