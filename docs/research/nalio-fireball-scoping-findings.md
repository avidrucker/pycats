# Nalio neutral-B Fireball — scoping findings (#155)

Research/scoping for Nalio's (PM3.6 Mario) **neutral-B Fireball**. Parent #125; epic
#142 (moveset) / #117 (archetypes). **No code here** — this defines the minimal
implementation slice + acceptance, and proposes one ready-to-claim DEV ticket.

Sources: [Smashboards "Mario: Hitboxes and Frame Data [3.6]"](https://smashboards.com/threads/mario-hitboxes-and-frame-data-3-6.350701/),
[SmashWiki Mario (PM)](https://www.ssbwiki.com/Mario_(PM)), [SmashWiki Fireball](https://www.ssbwiki.com/Fireball);
unit/scale conventions from #119/#120 (`PX_PER_UNIT ≈ 5.4`, #195).

## Current combat model (grounded in code)

- **`entities/attack.py` `Attack` is a STATIC hitbox.** It resolves its hitbox
  circles at spawn from the owner's position and **does not move** — `update()` only
  decrements `frames_left` and `kill()`s at 0 (`attack.py`). It already has
  `lifetime`, `disappear_on_hit`, `rehit_rate`, multi-hitbox, and circle-based
  collision via `systems/combat.process_hits`.
- **Spawn seam** (`entities/player.py:329`): during a move's active window the clock
  emits `tick.spawn` and a static `Attack(hitboxes=…, lifetime=…)` is added to
  `attack_group`. Tied to the owner's position at spawn.
- **Routing is ready** (`combat/move_select.py`): `neutral` + special → `neutral_b`;
  undefined special is a no-op. Nalio (`characters/nalio_cat.py`) defines all
  normals (jab/tilts/aerials) but **no specials** — fireball is the first.
- **Sakurai angle (361) is supported** (#203/#206): `SAKURAI_ANGLE_CODE = 361`
  resolved in `Fighter.receive_hit` via `knockback.sakurai_angle`. The fireball's
  361 angle drops in unchanged.

## Q1 — Smallest pycats representation of a projectile special

A fireball is a **detached, moving, lifetime-limited hitbox** — which is an `Attack`
**plus per-frame motion**. The current `Attack` already provides everything *except*
movement (detached-at-spawn, lifetime, circle collision, disappear-on-hit). So the
minimal representation is: **give a spawned hitbox a velocity and advance its
position each frame** — either an optional `velocity=` on `Attack` (its `update()`
adds `pos += vel` before the lifetime decrement) or a thin `Projectile(Attack)`
subclass. **Recommend extending the spawn path** (least new surface; reuses
`process_hits` + lifetime + `disappear_on_hit`). No general projectile *system* is
needed for one flat-travelling fireball.

## Q2 — Data fields + sources to capture (FOUND vs GUESS)

| Field | PM3.6 Mario value | Status |
|---|---|---|
| Throw startup | **14 frames** | FOUND (Smashboards 3.6) |
| Throw total / IASA | **48 total, IASA 41** | FOUND |
| Projectile spawn frame | **~frame 14–17** (after startup) | FOUND-ish |
| Damage | **7%** on hit (4.9 on shield) | FOUND |
| Angle | **361** (Sakurai sentinel — supported) | FOUND |
| BKB / WDSK / KBG | **22 / 0 / 20** (WDSK 0 → plain BKB/KBG; #211 not needed) | FOUND |
| Projectile size | **3.5 units → ≈19 px** radius (× `PX_PER_UNIT` 5.4) | FOUND (units); px via #195 |
| Lifetime / range | **article duration 1–73 frames** | FOUND (lifetime ≈73f) |
| Travel speed (px/frame) | not published in the summary | **GUESS** — rukaidata article field or playtest; derive units/frame × 5.4 |
| Gravity / bounce arc | PM fireballs bounce, "no longer degrade as they bounce" | **GUESS / defer** — flat travel first |
| Absorbable / reflectable | yes | FOUND — but **out of scope** (no Cape/absorb system) |

Guessed rows are tracked the way #192 tracks the air-dodge guesses (mark + derive via
rukaidata × 5.4 / playtest; don't bury silent constants).

## Q3 — First DEV slice vs projectile-system prerequisite

**A first DEV slice is feasible — no general projectile system required.** Build the
minimal moving projectile (Attack + horizontal velocity + lifetime), reusing the
existing circle collision, Sakurai angle, and disappear-on-hit. **Not** a placeholder
FX (a real moving hitbox is barely more code and is actually testable), and **not** a
full system. Deferred to follow-ups: the **bounce arc** (gravity/restitution — ship
flat horizontal travel first), and **reflect/absorb** (Cape — needs a separate
mechanic). Both are explicit non-goals of #155.

## Q4 — Tests the DEV slice should pin

- **Routing**: with Nalio defining `neutral_b`, a grounded neutral-B press selects
  `neutral_b` (and stays a no-op for characters without it).
- **Spawn**: a projectile entity is created at the spawn frame, detached from the
  owner (its position advances independently).
- **Motion**: the projectile's position advances by its velocity each frame (the new
  behaviour vs static `Attack`).
- **Collision/damage**: `process_hits` applies the fireball hitbox — 7%, angle 361
  (Sakurai-resolved), BKB 22 / KBG 20.
- **Lifetime/despawn**: killed at ~73 frames, on hit (`disappear_on_hit`), and off
  the blast zone.
- **Golden-safety**: Nalio isn't in the golden scenarios (default/combat/full_match
  use the default cat), so the new move + moving projectile won't perturb goldens —
  verify byte-identical.

## Proposed DEV ticket (ready to claim)

**"DEV: Nalio neutral-B Fireball — minimal moving projectile (flat travel)"** —
- Define `neutral_b` `MoveData` on Nalio (startup 14, lifetime ≈73, one hitbox:
  7% / angle 361 / BKB 22 / KBG 20 / r≈19px) with the FOUND values above.
- Extend the spawn path to launch a **moving** projectile (velocity + per-frame
  position update; despawn on lifetime / hit / off-stage). Travel speed is a flagged
  GUESS (derive via rukaidata × 5.4 / playtest).
- Route B → neutral_b; the tests in Q4; golden byte-identical.
- **Out of scope**: bounce arc/gravity, reflect/absorb (Cape), other specials.

Filed as the follow-up DEV ticket (see #155 close comment).
