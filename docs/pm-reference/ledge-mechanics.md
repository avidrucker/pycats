# Ledge mechanics — PM mechanics reference

> The **edge game**: grabbing a stage ledge to survive off-stage, the options for
> getting back on, and the edgeguarding that tries to stop you. This doc owns the
> ledge *interaction model*; the **ledge-hang state** is named in
> [fighter-states](./fighter-states.md), recovery (up-B) **move data** in
> [moveset-and-frame-data](./moveset-and-frame-data.md), and *which* edges are
> grabbable is stage geometry in [stages-and-environment](./00-overview.md) —
> linked, not restated. Part of the [PM mechanics reference](./00-overview.md)
> ([epic #147](https://github.com/avidrucker/pycats/issues/147)); PM 3.6.
>
> **Note on values:** ledge *mechanics* are described qualitatively; PM-specific
> *numbers* (intangibility frames, getup frame data) are per-character/version and
> should be taken from a PM source (rukaidata / SmashWiki PM pages) at authoring
> time, not memorised.

**Audience:** a contributor — human or agent — about to implement or modify
ledge/edge mechanics. Reference depth, not a tutorial; assumes the
[00-overview](./00-overview.md) conventions (60 Hz integer frames).

Off-stage is where stocks are won and lost. A launched fighter recovers toward the
stage; the **ledge** is a survival checkpoint, and denying it is **edgeguarding** —
together the most decisive phase of a match.

## Grabbing the ledge

- A fighter falling/​moving near a grabbable edge **snaps to the ledge** when its
  catch region overlaps the ledge's **sweetspot**. Recovery moves (up-B) are often
  designed to sweetspot the ledge.
- **Facing** matters: you generally grab a ledge while facing **toward** the stage;
  recoveries that arrive facing away may need to turn or may miss.
- There's typically a **rising-grab limitation** (you grab on the way down / level,
  not while shooting upward past it) and you can't grab again immediately after
  letting go without leaving the ledge's regrab window.
- *Which* platforms have grabbable edges is **stage geometry** →
  [stages-and-environment](./00-overview.md) (and the pycats thin-vs-thick open
  question in the footer).

## Ledge-hang & intangibility

Holding the ledge puts the fighter in **ledge-hang** (a hang state — see
[fighter-states](./fighter-states.md)) with **ledge intangibility**:

- A fresh grab grants a **burst of intangibility** (the tangibility flag from
  [combat-hitboxes-priority](./combat-hitboxes-priority.md)) — in Melee, **~7f
  CliffCatch + ~30f = ~37f** total (per-character; ⚠ pull PM numbers at authoring).
  This is a burst **that expires**, *not* a cap on how long you may hang.
- That intangibility **scales DOWN with repeated grabs** — each regrab in quick
  succession gives less, to curb stalling/​infinite ledge-camping. This *decay*, not
  a hang clock, is the lineage's anti-planking tool.
- **How long can you hang? ⚠ undocumented for Melee/PM.** No hard single-hang
  auto-release timer is documented in Melee/PM — you sit in **CliffWait** until you
  choose an option, and only the *intangibility burst* above expires. (A Brawl
  ~360/300f figure appears in [#297](../research/2026-06-30-ledge-recovery-mechanics.md),
  but it is itself unsourced/contested — needs a PM/Melee source or a debug-mode
  capture; do **not** treat a hard hang timer as PM-faithful without one.) Per research
  [#458](https://github.com/avidrucker/pycats/issues/458).

## Getup options

From the hang, four ways back on — a mixup, each with a different speed/coverage/
vulnerability tradeoff:

- **Neutral getup** — climb on; fast at low %, **slow and punishable at high %**.
- **Ledge roll** — roll onto the stage past the edge; covers distance, vulnerable
  on the roll.
- **Ledge attack** — climb with a hitbox to clear the space; beats a too-close
  edgeguard, punishable on whiff.
- **Ledge jump** — jump from the hang (into an aerial / further recovery).

The defender picks based on what the edgeguarder is covering; the edgeguarder reads
the option. (Intangibility from the grab can carry into the getup's early frames.)

**Frame data** (all options have a **fast (<100%)** and a **slow (≥100%)** variant —
SmashWiki). PM ledge-attack reference (Smashboards PM 3.6; **Mario → Nalio archetype**):
~**55f** total <100% (intang 1–20, hitbox ~f24) / ~**69f** ≥100% (intang 1–36, hitbox
~f40). Per-character neutral/roll/jump frame counts: pull from the Smashboards
"Ledge Option Frame Data" thread at implementation. Full table + intangibility/decay:
[2026-06-30-ledge-recovery-mechanics.md](../research/2026-06-30-ledge-recovery-mechanics.md) (#297).

## Dropping off & re-recovering

You can **drop from the ledge** (down/back) into a fall, then **double-jump** or
aerial back — used to reposition, refresh options, or bait an edgeguard.

**What makes you let go:** in Melee/PM you release by deflecting the control stick
**down or away past an analog magnitude threshold** — a slight tilt does *not* drop
you, and the direction you hold while recovering (usually *toward* the stage) keeps you
on. Leaving is that same stick input past threshold, not a separate button. ⚠ **Keyboard
implication (pycats):** a digital keyboard has **no magnitude axis**, and pycats reads
the drop from **held** state, so a direction carried over from the recovery drops you on
the very **grab frame** — measurably more eager than Melee/PM. See research
[#458](https://github.com/avidrucker/pycats/issues/458) for the accidental-fall-off
analysis and the keyboard-appropriate fixes (fresh-press-to-drop + a short post-grab
grace window).

## Edgeguarding, edge-hog & trump

- **Edgeguarding** — attacking a recovering opponent off-stage (aerials, a move
  that covers the ledge, or simply taking the space).
- **Edge-hog (PM's occupied-edge rule)** — occupy the ledge so the opponent **can't
  grab it** (one fighter per ledge); a grab on an occupied ledge is **denied**. PM
  specifics (#297): **ledge invincibility scales with the occupant's percent**
  (higher % → longer), so a hog's success is gated by the **occupant's invincibility
  timer** — hog **timing is percent-dependent** (too early and the recoverer takes the
  ledge). A fighter can **act out of the grab sooner** than Brawl, and during **any**
  getup the ledge is re-grabbable by others **only after ~half the animation**; tether
  recoveries **ignore** hoggers.
- **Ledge-trump** — grabbing a ledge an opponent holds **auto-removes** them. ⚠ **This
  is a Smash-4/Ultimate mechanic and is NOT in Project M** (confirmed #297). PM uses
  **edge-hogging** (above), the *opposite* system. Earlier text wrongly called trump
  "first-class in the Brawl/PM family." **Do not implement trump for PM** — pycats'
  one-occupant lockout is already the correct (hog) model.
- **The "2-frame"** — a recovering opponent is briefly vulnerable (~**2 frames**) as
  they grab the ledge, before intangibility activates; a well-timed hit catches that
  window.

## Teching

Hitting a wall/​ceiling/​ground with the right-timed press **techs** — cancelling
the bounce and recovering quickly (wall tech, wall jump tech). At the ledge,
teching off the stage wall is a recovery/edgeguard-survival tool. (General teching
also appears in [fighter-states](./fighter-states.md) under knockdown/getup.)

## Brawl / Melee / PM deltas

PM deliberately **reworked Brawl's ledge mechanics** — this is a defining change:

- **No infinite invincible hog:** ledge intangibility **decays with repeated
  grabs** (vs Melee's exploitable invincibility and Brawl's planking), curbing
  ledge-stalling.
- **Occupied-edge rule:** Brawl/PM use **edge-hogging** (the grab is *denied*);
  **auto-ledge-trump is Smash-4+** (corrected per #297). Melee also hogs (with
  stronger invincibility). PM's contribution is *reduced* ledge intangibility, not
  trump.
- **Recovery feel** follows PM's Melee-leaning movement (fast-fall, wavedash,
  Melee-style up-Bs) — see [movement-and-tech](./movement-and-tech.md).
- Getup-option frame data is PM-specific — use PM sources for numbers.

## Sources

- SmashWiki — [Ledge](https://www.ssbwiki.com/Ledge), [Edge-hogging](https://www.ssbwiki.com/Edge-hogging), [Ledge trump](https://www.ssbwiki.com/Ledge_trump), [Edge sweet spot](https://www.ssbwiki.com/Sweet_spot_(edge)), [Tech](https://www.ssbwiki.com/Tech).
- PM-specific getup/intangibility data: [rukaidata PM 3.6](https://rukaidata.com/PM3.6/) / SmashWiki PM pages.
- Hang **stay/leave** rules (#458): SmashWiki — [Ledgestall](https://www.ssbwiki.com/Ledgestall) (CliffCatch 7f + ~30f intangibility; letting go keeps intangibility), [Planking](https://www.ssbwiki.com/Planking), [Edge recovery](https://www.ssbwiki.com/Edge_recovery) (release = stick down/away); [SuperCombo SSBM Advanced Controls](https://wiki.supercombo.gg/w/SSBM/Advanced_Controls) (down/away analog zones). A hard single continuous-hang auto-release is ⚠ **undocumented** for Melee/PM.
- State: [fighter-states](./fighter-states.md); recovery moves: [moveset-and-frame-data](./moveset-and-frame-data.md); intangibility: [combat-hitboxes-priority](./combat-hitboxes-priority.md); stage edges: [stages-and-environment](./00-overview.md). Conventions: [00-overview](./00-overview.md).

## pycats status

**v1 implemented** ([#14](https://github.com/avidrucker/pycats/issues/14)): automatic
grab at a **solid** stage edge (thin platforms are NOT grabbable — owner ruling),
**ledge-hang** with full-window intangibility (reusing the `invulnerable` flag), and
three exits — **neutral getup** (up, climb on), **drop** (down or away → fall with a
regrab lockout), and a **timeout** (120f auto-release → off-stage drop; unfaithful,
**slated for removal in [#475](https://github.com/avidrucker/pycats/issues/475)** per #458).
Occupancy is a **one-occupant lockout**
per edge (no trump yet). The state lives in the fighter chart
([fighter-states](./fighter-states.md)) as `ledge_hang`; design +
plan in `docs/superpowers/specs/2026-06-30-ledge-hang-design.md` /
`docs/superpowers/plans/2026-06-30-ledge-hang.md`.

**Deferred** (epic [#267](https://github.com/avidrucker/pycats/issues/267)): the other
getup options (**ledge roll / attack / jump**), **intangibility decay** on repeated
grabs, the **"2-frame"**, **teching**, **up-B sweetspot** recovery, and
hold-away-to-decline + a frame-accurate getup window. Per-character/longer hang tuning
is ⚠ playtest (`LEDGE_HANG_FRAMES` et al.).

**Researched values to apply** (#297, [findings](../research/2026-06-30-ledge-recovery-mechanics.md)):
- Grab **intangibility** should be a **short burst (~23f, Brawl)** — pycats currently
  grants the *whole* `LEDGE_HANG_FRAMES` (120f), which is over-generous.
- **Hang auto-release:** ⚠ **contested** (#458). The ≈360/300f Brawl figure is
  unsourced, and #458 found **no documented** hard single-hang timer for Melee/PM.
  pycats' 120f timeout that **drops you off-stage** is an invention (no lineage game
  force-KOs a hanger) — **slated for removal in [#475](https://github.com/avidrucker/pycats/issues/475)**;
  do not "tune" it toward a PM value until one is actually sourced.
- Neutral getup is currently **instant**; needs a real frame window + the fast/slow
  (<100% / ≥100%) variant. Ledge attack ≈ 55f/69f (Mario ref).
- **Occupied-edge: pycats' one-occupant lockout already models PM edge-hogging
  correctly** — keep the deny-lockout. **Ledge-trump is NOT a PM mechanic** (Smash-4+);
  #267's trump slice was **removed** (#297). The PM fidelity gap to chase later is
  **percent-scaled ledge invincibility** + hog timing, not trump.

Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
