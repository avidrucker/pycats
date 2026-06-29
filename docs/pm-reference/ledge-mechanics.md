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

- A fresh grab grants a burst of **intangibility** (the tangibility flag from
  [combat-hitboxes-priority](./combat-hitboxes-priority.md)).
- That intangibility **scales DOWN with repeated grabs** — each regrab in quick
  succession gives less, to prevent stalling/​infinite ledge-camping.
- A fighter that hangs too long without acting eventually **falls** (or auto-getups
  in some rulesets); you can't hang forever.

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

## Dropping off & re-recovering

You can **drop from the ledge** (down/back) into a fall, then **double-jump** or
aerial back — used to reposition, refresh options, or bait an edgeguard. Drop-down
is also how you go for an offensive **ledge-trump** (below).

## Edgeguarding, edge-hog & trump

- **Edgeguarding** — attacking a recovering opponent off-stage (aerials, a move
  that covers the ledge, or simply taking the space).
- **Edge-hog** — occupying the ledge yourself so the opponent **can't grab it**
  (only one fighter holds a ledge). In Brawl/PM, ledge intangibility makes the
  classic Melee-style invincible hog weaker, shifting toward...
- **Ledge-trump** — grabbing a ledge an opponent is already holding **knocks them
  off** (trumps them) into a vulnerable state, a strong offensive option PM
  emphasises.
- **The "2-frame"** — a recovering opponent is briefly vulnerable as they grab the
  ledge; a well-timed hit catches that window.

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
- **Ledge-trump** is a first-class offensive option in the Brawl/PM family (absent
  in Melee).
- **Recovery feel** follows PM's Melee-leaning movement (fast-fall, wavedash,
  Melee-style up-Bs) — see [movement-and-tech](./movement-and-tech.md).
- Getup-option frame data is PM-specific — use PM sources for numbers.

## Sources

- SmashWiki — [Ledge](https://www.ssbwiki.com/Ledge), [Edge-hogging](https://www.ssbwiki.com/Edge-hogging), [Ledge trump](https://www.ssbwiki.com/Ledge_trump), [Edge sweet spot](https://www.ssbwiki.com/Sweet_spot_(edge)), [Tech](https://www.ssbwiki.com/Tech).
- PM-specific getup/intangibility data: [rukaidata PM 3.6](https://rukaidata.com/PM3.6/) / SmashWiki PM pages.
- State: [fighter-states](./fighter-states.md); recovery moves: [moveset-and-frame-data](./moveset-and-frame-data.md); intangibility: [combat-hitboxes-priority](./combat-hitboxes-priority.md); stage edges: [stages-and-environment](./00-overview.md). Conventions: [00-overview](./00-overview.md).

## pycats status

**Not implemented — deferred** ([Phase 5 roadmap](../research/pm-mechanics-implementation-analysis.md); tracked by [#14](https://github.com/avidrucker/pycats/issues/14) "Add ledge-hang state"). There is no ledge grab, ledge-hang, getup, edge-hog, trump, or tech today.

Intent is captured as a source TODO in `pycats/entities/player.py`:
> implement ledge grabbing — grab the ledge when falling off a platform, press up
> to get back on / down to drop, limited-time invulnerability while hanging,
> eventually fall off if you don't act. **(Open Q: can thin platforms be
> ledge-grabbed, or only thick ones?)**

When built, the ledge-hang **state** belongs in the fighter chart
([fighter-states](./fighter-states.md)), the intangibility reuses the existing
`invulnerable` flag, recoveries are up-B specials
([moveset-and-frame-data](./moveset-and-frame-data.md)), and the thin-vs-thick
grabbable-edge question is a [stages-and-environment](./00-overview.md) +
[#14](https://github.com/avidrucker/pycats/issues/14) decision.

Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
