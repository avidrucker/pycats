# Stages & environment — PM mechanics reference

> The arena: the **stage geometry** fighters move on and die past. This doc owns
> stage *geometry* (platforms, walls, **which edges are grabbable**, blast zones,
> camera); the ledge *interaction* (grab/hang/getup) is
> [ledge-mechanics](./ledge-mechanics.md), the KO *math* is
> [combat-knockback-hitstun](./combat-knockback-hitstun.md), and stage-**select**
> UI is [menus-and-game-flow](./00-overview.md) — linked, not restated. Part of the
> [PM mechanics reference](./00-overview.md) ([epic #147](https://github.com/avidrucker/pycats/issues/147)); PM 3.6.
>
> **Note on values:** stage *geometry* is described qualitatively; PM-specific
> dimensions are per-stage and not memorised here — take them from a PM source if
> needed.

**Audience:** a contributor — human or agent — about to implement or modify
stages / platforms / blast zones / camera. Reference depth, not a tutorial;
assumes the [00-overview](./00-overview.md) conventions.

## Stage anatomy

A PM stage is a layout of collision surfaces plus the kill boundaries around them:

- **Main platform / floor** — the solid ground fighters stand and fight on; its
  left/right ends are the **grabbable ledges**.
- **Soft (pass-through) platforms** — raised platforms you can jump up through and
  **drop through**; they extend the vertical game.
- **Walls / ceilings** — solid surfaces on some stages (enable wall-tech, wall-jump).
- **Ledges** — the grabbable edges of the **main stage** (and walls on some
  stages). **Pass-through platforms are NOT ledge-grabbable** — only the solid
  main-stage edges are. The interaction (snap, hang, getup) is
  [ledge-mechanics](./ledge-mechanics.md); this doc just says *where* a grabbable
  edge exists.

## Platform types

- **Solid** — collide from all sides; the main floor (and walls/​ceilings).
- **Pass-through / drop-through** — collide only from above; jump up through them,
  and press **down** (while grounded on one) to drop through. The competitive
  layout staple (Battlefield's three soft platforms).

## Blast zones

Four off-screen **blast lines** (top / bottom / left / right) bound the stage. A
fighter is **KO'd when they cross a blast line** — that's what a KO *is*: launch
the opponent (knockback) far enough/fast enough to pass a boundary. The side/top
lines reward horizontal/vertical kills; the bottom line is the off-stage abyss the
ledge game is fought over. The launch that gets them there is
[combat-knockback-hitstun](./combat-knockback-hitstun.md); the boundary is here.

## Camera

PM uses a **dynamic camera** — it zooms and pans to keep all live fighters framed,
tightening for a 1v1 in the center and pulling back as they spread or go off-stage.
Consequently there is **no fixed unit→pixel mapping** (the camera scale changes
constantly), which is exactly why spatial values are abstract units (× a chosen
`PX_PER_UNIT` for a fixed-camera port — see [00-overview](./00-overview.md) / #120).

## Stage conventions & hazards

- **Legal layouts:** competitive PM favours **Battlefield-style** (main platform +
  three soft platforms) and **Final-Destination-style** (one flat platform, no soft
  platforms) layouts; **starting positions** are symmetric.
- **Hazards & moving platforms:** many stages have hazards, moving/transforming
  platforms, or walk-off edges; tournament play **toggles these off** (hazardless /
  legal versions). A PM-faithful baseline starts from a static, hazardless layout.

## Brawl / Melee / PM deltas

- **Stage roster** differs (PM has its own stage list + Melee/Brawl ports), but the
  *anatomy* (main platform, soft platforms, ledges, blast lines) is consistent
  across the family.
- **Camera/​engine** is Brawl's (PM inherits it); blast-line KO and pass-through
  platforms are family-standard.
- **Legal/hazardless conventions** are a competitive-ruleset layer, not an engine
  difference.

## Sources

- SmashWiki — [Stage](https://www.ssbwiki.com/Stage), [Platform](https://www.ssbwiki.com/Platform), [Blast line](https://www.ssbwiki.com/Blast_line), [Camera](https://www.ssbwiki.com/Camera).
- [`docs/research/screen-camera-sizing-findings.md`](../research/screen-camera-sizing-findings.md) — pycats screen/resolution + a PM-style bounding-box camera.
- Ledge interaction: [ledge-mechanics](./ledge-mechanics.md); KO/launch: [combat-knockback-hitstun](./combat-knockback-hitstun.md); scale: [00-overview](./00-overview.md). Conventions: [00-overview](./00-overview.md).

## pycats status

Implemented:
- **Platforms** — `pycats/entities/platform.py`: `thin=False` = **solid** (collide all sides), `thin=True` = **pass-through** (collide from above; drop through with **down** while grounded). The default layout is **one thick main platform + two thin platforms** (config), a Battlefield-ish arrangement on a **960×540** stage (`SCREEN_WIDTH/HEIGHT`).
- **Blast-zone KO** — `Fighter._outside_blast_zone()` KOs a fighter past the screen + `BLAST_PADDING` margin on any side (the blast-line model).
- **Camera/screen** — resolution-independent rendering; a PM-style dynamic camera is scoped in [`screen-camera-sizing-findings.md`](../research/screen-camera-sizing-findings.md) (#45).

**Decisions / deferred:**
- ✅ **Grabbable edges = main-stage (thick) ledges only; thin/pass-through platforms are NOT ledge-grabbable** — sticking with **Project M parity** (resolves the open question from [ledge-mechanics](./ledge-mechanics.md) / [#167](https://github.com/avidrucker/pycats/issues/167); applies to the ledge-hang implementation [#14](https://github.com/avidrucker/pycats/issues/14)). Ledge *grabbing itself* is still unimplemented (deferred with the ledge mechanics).
- ⬜ **Multiple stages + stage select** (single static stage today; stage-select UI → [menus-and-game-flow](./00-overview.md)).
- ⬜ **Walls/ceilings as tech surfaces, moving platforms, hazards, dynamic camera** — deferred (the static hazardless baseline is the starting point).
- Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24). Camera/screen: #45 / #15 / #18.
