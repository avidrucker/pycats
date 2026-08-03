# Knockback, hitstun, hitlag & launch — PM mechanics reference

> How Project M turns a hit into a launch: the knockback magnitude, the hitlag
> freeze that precedes it, the hitstun the victim suffers, and the decaying
> velocity that carries them. Part of the [PM mechanics reference](./00-overview.md)
> ([epic #147](https://github.com/avidrucker/pycats/issues/147)); PM 3.6 values,
> Brawl/Melee deltas noted. Conventions (60 Hz integer frames, raw combat numbers,
> spatial × `PX_PER_UNIT ≈ 5.4`): see [00-overview](./00-overview.md).

The hit-to-launch pipeline, in frame order: **contact → hitlag (both fighters
freeze) → percent applied → knockback computed → launch velocity set → hitstun +
decaying slide.** Each stage below.

## Knockback magnitude

A hit's knockback is a dimensionless magnitude from the **Melee-onward formula**
(Brawl and PM share it verbatim):

```
KB = ( ( ( ( (p/10) + (p·d/20) ) · (200/(w+100)) · 1.4 ) + 18 ) · (KBG/100) ) + BKB ) · r
```

| Term | Meaning |
|---|---|
| `p` | target's percent **after** the hit |
| `d` | the hitbox's damage |
| `w` | target **weight** (heavier → less KB, via `200/(w+100)`) |
| `BKB` | base knockback — the hitbox's KB floor at 0% |
| `KBG` | knockback growth — how fast KB scales with percent |
| `r` | situational modifier (rage/handicap/launch-rate); **1** in normal play |

Weight is the only *defender* attribute in the formula, which is why weight
classes matter: at the same percent, a heavier fighter is launched less and dies
later. `BKB`/`KBG`/`d`/angle are **per-hitbox** (a move's hitboxes can each launch
differently); see [moveset-and-frame-data](./00-overview.md).

## Hitlag (freeze frames)

Before anyone moves, **both the attacker and the defender freeze in place** for
hitlag frames — the "impact pause" that gives hits weight and the defender a beat
to react (DI/SDI are buffered here). SmashWiki *Hitlag* (Brawl onward):

```
hitlag = floor( (d · 0.3846154 + 5) · h · e ) · c       (capped at 30)
```

| Term | Meaning |
|---|---|
| `d` | damage dealt (after stale/fresh) |
| `h` | per-move hitlag multiplier (default 1) |
| `e` | electric multiplier (1.5× if electric, else 1) |
| `c` | crouch-cancel multiplier (0.67×, **victim only**) |

Cap: **30 frames** (Brawl onward; Melee was 20, with formula `floor(d/3 + 3)`).
Hitlag affects both fighters equally (except the victim-only crouch-cancel factor);
**knockback is applied after hitlag ends**, so the launch begins when the freeze
releases.

## Hitstun

When the freeze ends the victim enters **hitstun** — unable to act for a
KB-scaled number of frames:

```
hitstun = floor( KB · 0.4 )
```

The 0.4 multiplier is the Melee/Brawl value; **PM is Brawl-based and removed
*hitstun cancelling*** (you can't airdodge/aerial out of hitstun early), but the
multiplier itself is unchanged. Higher KB → longer hitstun → longer combos and,
eventually, an inescapable launch toward the blast zone.

## Launch velocity & per-frame decay

Knockback is **not** a velocity — it drives a small kinematic model (shared Melee/
Brawl/PM internal units):

| Quantity | Formula | Constant |
|---|---|---|
| initial launch **speed** | `KB · 0.03` units/frame | 0.03 |
| per-frame **decay** | `speed −= 0.051` each frame until 0 | 0.051 |

So the launched fighter **decelerates every frame from the moment of the hit**,
during hitstun and beyond, until momentum is gone. Travel distance is the
arithmetic-series sum ≈ `launch_speed² / (2 · decay)` — i.e. **distance ∝ KB²**.

A consequence worth noting: the slide can outlast hitstun. At KB 56.4 (a 10% jab)
hitstun is ~22 f but the slide lasts ~33 f, so the victim is **still drifting yet
actionable** (can tech/DI/jump) for the final ~11 f. The launch **angle** sets the
initial velocity's direction (below).

## DI & SDI

- **DI (Directional Influence):** holding a direction during hitlag/hitstun
  rotates the launch trajectory (perpendicular component), letting the victim
  survive longer or set up a tech. It changes *direction*, not *magnitude*.
- **SDI (Smash DI):** rapid stick inputs during **hitlag** nudge the victim's
  position a few units per input — used to escape multi-hits.

Both are *defensive inputs read during the freeze/stun*; documented here for
completeness (pycats has not implemented them — see footer).

## Launch angles & sentinels

Angles are degrees (0° = forward, 90° = straight up), **except special sentinel
codes** that are interpreted, not taken literally:

- **361 — the Sakurai angle:** the most common code. An *airborne* victim is
  launched at a fixed angle (~40° Brawl/PM, ~44° Melee). A *grounded* victim
  scales from ~horizontal (0°) for weak/low-KB hits up to that same angle as KB
  rises — so weak hits don't pop grounded opponents straight up. Not a literal
  361°. Implemented in pycats by `knockback.sakurai_angle` (#203).
- **365 / 366 — autolink angles:** scale with the attacker's own motion to keep
  multi-hit moves connecting.

Porting a move faithfully means **handling these codes**, not storing them as raw
degrees.

## Brawl / Melee deltas

- **Hitstun cancelling:** present in Brawl, **removed by PM** (and absent in
  Melee). PM combos therefore behave Melee-like despite the Brawl base.
- **Vertical-KB gravity term:** Brawl adds `(g − 0.075) × 5` to vertical knockback
  for high-gravity characters; carried in PM.
- **Hitlag cap:** 30 (Brawl/PM) vs 20 (Melee); Melee's formula is `floor(d/3+3)`.
- **Hitbox-radius unit:** Melee radii are 256× a smaller unit (divide before
  comparing); Brawl/PM use the standard unit.

## Sources

- SmashWiki — [Knockback](https://www.ssbwiki.com/Knockback), [Hitstun](https://www.ssbwiki.com/Hitstun), [Hitlag](https://www.ssbwiki.com/Hitlag), [Directional influence](https://www.ssbwiki.com/Directional_influence), [Sakurai angle](https://www.ssbwiki.com/Sakurai_angle).
- [`docs/research/knockback-launch-physics-findings.md`](../research/knockback-launch-physics-findings.md) — the launch/decay model, measured (#43).
- Conventions: [`00-overview.md`](./00-overview.md), [`docs/research-120-smash-units-and-sources.md`](../research-120-smash-units-and-sources.md).

## pycats status

Implemented in Phase 1 ([#38](https://github.com/avidrucker/pycats/issues/38)):
- **Knockback formula** — `pycats/combat/knockback.py::knockback` (term-for-term, `r = 1`). Weight threaded per-fighter ([#117](https://github.com/avidrucker/pycats/issues/117)/[#123](https://github.com/avidrucker/pycats/issues/123)).
- **Hitstun** — `knockback.py::hitstun_frames` = `max(HITSTUN_FLOOR, floor(KB · HITSTUN_MULTIPLIER))`; constants `HITSTUN_MULTIPLIER = 0.4`, `HITSTUN_FLOOR = 1` (config). ([#40](https://github.com/avidrucker/pycats/issues/40))
- **Hitlag** — `knockback.py::hitlag_frames` = `min(HITLAG_CAP, floor(d · HITLAG_DAMAGE_FACTOR + HITLAG_BASE))`; both fighters freeze via `Player.update`'s early-return; constants `HITLAG_DAMAGE_FACTOR = 0.3846154`, `HITLAG_BASE = 5`, `HITLAG_CAP = 30`. ([#138](https://github.com/avidrucker/pycats/issues/138))
- **Launch + decay** — set in `Fighter.receive_hit`, bled off by `knockback.py::decay_velocity` each hitstun frame; constants `KNOCKBACK_LAUNCH_FACTOR = 0.085`, `KNOCKBACK_DECAY = 0.145` (scaled to pycats' 960 px stage while keeping the ~1.7 decay/launch ratio). ([#43](https://github.com/avidrucker/pycats/issues/43)/[#44](https://github.com/avidrucker/pycats/issues/44))

**Deferred / divergent in pycats:**
- **DI / SDI** — not implemented (Phase 3).
- **Hitlag `h`/`e`/`c` multipliers** (per-move / electric / crouch-cancel) — fixed at 1; crouch-cancel KB reduction is a separate follow-up ([#135](https://github.com/avidrucker/pycats/issues/135)).
- **Sakurai angle (361)** — resolved by `knockback.sakurai_angle` (#203): airborne-fixed, grounded scales flat→max with KB. The angle/KB-threshold constants (`SAKURAI_*` in config) are unsourced ⚠ playtest starting points, not exact PM values.
- **Brawl vertical-KB gravity term** — pycats has one global gravity; not modelled.
- Launch/decay constants are **tuned to the pixel stage**, not the raw 0.03/0.051 — a deliberate scale divergence (see [#99](https://github.com/avidrucker/pycats/issues/99) when logged).
- Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
