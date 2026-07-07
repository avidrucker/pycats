# PM post-ledge-cutoff intangibility — the "few frames during the initial ledge snap" (#671)

> **Home-of-record** for one question left open by decision **#670** (adopt PM's 5-regrab
> cutoff): after a fighter is cut off (grab 6+ without touching the ground), does it get
> **any** grab-invulnerability, or **zero**? Feeds #656's post-cutoff branch. Sits under the
> ledge-intangibility audit `2026-07-05-pm-ledge-intangibility-basis.md` (#536).

## Answer — NOT zero. A small residual (the ledge-snap intangibility) remains.

PMDT dev-blog #6, verbatim (primary; re-verified 2026-07-06 via an independent search):

> "After a character regrabs the ledge five times without touching the ground, that
> character no longer receives invulnerability for grabbing the ledge again **(except for a
> few frames during the initial ledge snap)** until he or she either lands on the stage or
> gets hit."

The parenthetical is explicit: grab 6+ still grants **a few frames**. So the post-cutoff
value is **non-zero** — a small residual, not a full suppression.

## What the residual is — the CliffCatch (catch-animation) intangibility

Two layers make up a normal ledge grab, and the cutoff removes only the larger one:

- **The CliffCatch catch animation is intangible for its whole duration.** rukaidata's
  **PM 3.6** data (which runs brawllib_rs over the PM 3.6 build) — for **both Mario and
  Kirby** — shows `CliffCatch`: **Fully Intangible frames 1–21**, subaction length **21f**.
  This is the datamined per-grab intangibility of a *normal* (grabs 1–5) catch.
- **The 5-regrab anti-stall removes the "invulnerability for grabbing the ledge"** — the
  larger grant — and leaves only "a few frames during the initial ledge snap": a small
  residual of that catch window.

So: normal grab ≈ 21 intangible frames (PM 3.6); post-cutoff grab ≈ **a few** frames.

## What is NOT recoverable here, and why

**The exact post-cutoff "few frames" count is engine-hardcoded and was not pinned.** The
5-regrab reduction is *dynamic engine anti-stall logic* layered on the catch, **not** part of
the `CliffCatch` subaction script — so rukaidata / brawllib_rs (which expose scripted
subaction data, not engine globals) show only the *normal* 1–21 window, never the reduced
post-cutoff one. This is the same limit as `DODGE_AIR_SPEED` (#215 / #222): an engine-global
question routed to brawllib_rs comes back empty. Pinning the literal "few frames" needs a **PM
DOL / codeset dump** (the #638 dump-capability epic) or a **frame-stepped playtest** — out of
reach for this spike.

"A few frames" therefore stays **qualitative** from the primary. Melee's comparable CliffCatch
is **7 f** (below) — a plausible order-of-magnitude anchor, but **Melee, not PM** (do not
silently attribute).

## Game attribution — keep these separate

| Game | Ledge-grab (CliffCatch) intangibility | Tier / source |
|---|---|---|
| Melee | 7 f CliffCatch (3 f Link) + 30 f after = 37 f | secondary — [SmashWiki *Ledgestall*](https://www.ssbwiki.com/Ledgestall) |
| Brawl | ~23 f | secondary — [SmashWiki *Ledge*](https://www.ssbwiki.com/Ledge) (via #297) |
| **PM 3.6, normal grab** | **CliffCatch fully intangible 1–21 (21 f)** — Mario + Kirby | **datamined primary** — [rukaidata PM3.6 Mario](https://rukaidata.com/PM3.6/Mario/subactions/CliffCatch.html) / [Kirby](https://rukaidata.com/PM3.6/Kirby/subactions/CliffCatch.html) |
| **PM 3.6, post-5-regrab** | **"a few frames during the initial ledge snap"** — exact count engine-hardcoded, **unrecovered** | **primary (qualitative)** — PMDT dev-blog #6 |

## Recommendation for #656 (post-cutoff branch)

- **Grant a small non-zero residual, not zero** — the primary is explicit. Modelling grab 6+
  as zero would be a (small) divergence, not PM-faithful.
- pycats models grab intangibility as a single `ledge_invuln_timer` burst (no separate
  catch-animation window), so the residual is a **single small fixed frame count**. Recommend a
  **⚠ TUNED** value of **~3–7 f** (matches "a few frames"; Melee's 7 f CliffCatch is the upper
  anchor). Tag it **TUNED**, not FOUND — there is no primary *number*, only "a few" (RULES
  "Changing values").
- If the owner prefers **zero for a v1 simplification**, that is acceptable as a **documented
  minor divergence** (the residual is small enough to be near-imperceptible) — but it is a
  divergence, and the faithful default is the small residual above.

**Also feeds #552:** the datamined **PM 3.6 CliffCatch = 21 f** (Mario + Kirby) is the exact
per-grab intangibility value #552 is trying to pin for the fixed-burst change — ~21 f, close to
pycats' current `LEDGE_INVULN_BASE_FRAMES = 23`. #552 should confirm across more characters.

## Sources

| Source | Tier | Used for |
|---|---|---|
| [rukaidata PM3.6 — Mario / Kirby `CliffCatch`](https://rukaidata.com/PM3.6/Mario/subactions/CliffCatch.html) | **datamined primary (PM 3.6)** | normal CliffCatch intangible 1–21 (21 f) |
| PMDT — "3.5 Blogpost #6: Ledge Invincibility" ([projectmgame.com](https://projectmgame.com/en/news/dev-blogpost-6-ledge-invincibility), dead; reproduced) | **primary (PMDT)** | the residual "few frames," non-zero, is qualitative |
| [SmashWiki — Ledgestall](https://www.ssbwiki.com/Ledgestall) | secondary | Melee 7 f + 30 f (comparison anchor — not PM) |
| [SmashWiki — Ledge](https://www.ssbwiki.com/Ledge) | secondary | Brawl ~23 f (via #297) |

## Cross-refs

Research **#671**; decision **#670** (adopt the cutoff); audit **#536**; fixed-burst value spike
**#552** (PM 3.6 CliffCatch = 21 f feeds it); implementation **#656** under epic **#267**;
dump-capability epic **#638** (would pin the exact post-cutoff count); engine-global limit
**#215 / #222**. PM canon = **Project M 3.6**.
