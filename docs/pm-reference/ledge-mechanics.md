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
- That intangibility is **cut off after repeated grabs**, to curb stalling/​infinite
  ledge-camping — the lineage's anti-planking tool. In **PM** this is a **hard
  5-regrab count cutoff** (grabs 1–5 give the full burst; grab 6+ give only a few
  snap frames), **not** the gradual per-grab decay of Smash-4/Ultimate. Full spec +
  the HUD that shows it: [ledge-regrab-intangible-and-display.md](./ledge-regrab-intangible-and-display.md)
  (mechanic ratified [#670](https://github.com/avidrucker/pycats/issues/670), shipped #656).
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
  (higher % → longer) — **⚠ but the *magnitude* scaling is a DIVERGENCE, not PM-sourced;
  see "Validation (#538)" below** — so (in pycats) a hog's success is gated by the
  **occupant's invincibility timer** — hog **timing is percent-dependent** (too early and
  the recoverer takes the ledge). A fighter can **act out of the grab sooner** than Brawl, and during **any**
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
**ledge-hang** with a short percent-scaled intangibility **burst** (`ledge_intangible_frames`,
#311), and exits — **neutral getup** (up, climb on) and **drop** (down or away → fall
with a regrab lockout). There is **no hang timeout** (removed in
[#475](https://github.com/avidrucker/pycats/issues/475) per #458 — no lineage game
force-drops a hanger); a fighter hangs until it acts. A **connecting hit past the
intangibility burst knocks a hanger off the ledge** (#475), so a hang is ended under
attack (edge-guard) rather than by a timer. Occupancy is a **one-occupant lockout**
per edge (no trump yet). The state lives in the fighter chart
([fighter-states](./fighter-states.md)) as `ledge_hang`; design +
plan in `docs/superpowers/specs/2026-06-30-ledge-hang-design.md` /
`docs/superpowers/plans/2026-06-30-ledge-hang.md`.

**Deferred** (epic [#267](https://github.com/avidrucker/pycats/issues/267)): the other
getup options (**ledge roll / attack / jump**), **intangibility decay** on repeated
grabs, the **"2-frame"**, **teching**, **up-B sweetspot** recovery, and
hold-away-to-decline + a frame-accurate getup window. (Per-character/longer *hang*
tuning is moot — #475 removed the hang timer entirely.)

**Researched values to apply** (#297, [findings](../research/2026-06-30-ledge-recovery-mechanics.md)):
- Grab **intangibility** should be a **short burst (~23f, Brawl)** — pycats currently
  grants the *whole* `LEDGE_HANG_FRAMES` (120f), which is over-generous.
- **Hang auto-release:** ⚠ **contested** (#458), and now **removed** (#475). The
  ≈360/300f Brawl figure is unsourced, and #458 found **no documented** hard single-hang
  timer for Melee/PM. pycats' 120f timeout that **dropped you off-stage** was an invention
  (no lineage game force-KOs a hanger); [#475](https://github.com/avidrucker/pycats/issues/475)
  deleted it (`LEDGE_HANG_FRAMES` gone). The faithful anti-stall answer is
  intangibility-decay-on-regrab (#267), not a timer — do not reintroduce a hang timeout
  unless one is actually sourced.
- Neutral getup is currently **instant**; needs a real frame window + the fast/slow
  (<100% / ≥100%) variant. Ledge attack ≈ 55f/69f (Mario ref).
- **Occupied-edge: pycats' one-occupant lockout already models PM edge-hogging
  correctly** — keep the deny-lockout. **Ledge-trump is NOT a PM mechanic** (Smash-4+);
  #267's trump slice was **removed** (#297). The PM fidelity gap to chase later is
  **percent-scaled ledge invincibility** + hog timing, not trump.

## Validation (#538) — is ledge intangibility percent-scaled? Likely **NO** (DIVERGENCE)

Spike #538 validated the "ledge invincibility scales with the occupant's percent" claim above
(introduced by #311) against PM/Brawl sources, to put #531's timer-bar on a sourced footing.

- **The intangibility *magnitude* is a FIXED burst, not a continuous function of percent.**
  Confidence: **inferred-strong**. The documented percent-dependence in Brawl/PM ledge play is
  (a) getup/climb **speed** slowing at the **≥100% threshold** (SmashWiki *Edge recovery*: "when
  the character has 100% damage or more, the action of climbing back to the stage is
  significantly slower") and (b) hang **duration** (~6 s <100% / ~5 s ≥100%). **No source** scales
  the intangibility *duration* continuously with percent. PM's actual contribution was to
  **reduce** ledge intangibility (~1 f under Melee) and **decay it with repeated grabs**
  (anti-plank) — neither is percent-based, and both make high-% recovery *harder*, the opposite
  of "higher % → longer intangibility".
- **`LEDGE_INTANGIBLE_BASE_FRAMES` → FOUND.** Was 23 (Brawl baseline); **updated to 21 in #683** — PM
  3.6 `CliffCatch` is fully intangible frames 1–21, flat across every character checked (rukaidata,
  #671). #297 (`docs/research/2026-06-30-ledge-recovery-mechanics.md`) + SmashWiki *Ledge*.
- **`LEDGE_INVULN_PER_PERCENT = 0.3` + `LEDGE_INVULN_MAX_FRAMES = 60` → DIVERGENCE, now REMOVED
  (#683).** The continuous "higher % → longer" scaling (#311) had no PM source and inverted PM's real
  high-% effect. Reclassified DIVERGENCE (#536); both constants **deleted in #683** for the flat 21f burst.

**Consequences**
- **#531 bar model:** the true window is a **fixed-per-grab burst that drains to 0**, so divide the
  bar fill by the **value granted at that grab** — store `ledge_intangible_granted` at grab and use
  `ratio = ledge_intangible_timer / ledge_intangible_granted` (a truthful 100%→0 drain). Robust whether
  pycats keeps its divergent scaling *or* later aligns to a fixed burst; a cap-denominator would
  misrender a short low-% burst.
- **Decision — RATIFIED (#543, 2026-07-05): align to PM's fixed burst.** Drop the continuous
  percent-scaling (`+0.3/%` + cap 60); the grab intangibility becomes a fixed per-grab window.
  #543 is the game-designer basis (RULES "Changing values") the implementing DEV cites to change
  `23 / 0.3 / 60`. Scoping of the code change + the exact PM 3.6 value is a follow-up ARCH spike →
  DEV (see #543). A rukaidata PM 3.6 dump would lift the "fixed" finding from inferred-strong to explicit.
- **Decision — RATIFIED (#670, 2026-07-06): adopt PM's 5-regrab count cutoff (anti-plank).** After a
  fighter regrabs the ledge **5 times without touching the ground**, further grabs grant no
  ledge-intangibility until the fighter **lands on the stage or gets hit**. Primary basis: PMDT
  dev-blog #6 (audit #536, `docs/research/2026-07-05-pm-ledge-intangibility-basis.md`). This is a
  **new sim mechanic** pycats lacks today — #670 is the basis the implementing DEV (**#656**) cites.
  The **exact post-cutoff residual** — grab 6+ gives zero intangibility, or PMDT's "few frames during the
  initial ledge snap" — is deferred to research **#671** (the mechanic's only open sub-question).

Sources: [SmashWiki — Edge recovery](https://www.ssbwiki.com/Edge_recovery),
[SmashWiki — Ledgestall](https://www.ssbwiki.com/Ledgestall) (CliffCatch 7 f + ~30 f intangibility,
Melee), [Smashboards — Invincibility & armor list](https://smashboards.com/threads/invincibility-and-armor-list.371822/);
in-repo #297. PM canon = **Project M 3.6**.

Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
