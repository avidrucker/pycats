# Mario cat — Project M Mario → pycats spec (#119)

> First child of the 5-archetype epic (#117). Maps **Project M 3.6 Mario** onto
> pycats' systems so the follow-up DEV ticket can author `FighterData` with
> confidence. Read-only research → this spec. Siblings (Marth/Kirby/DK/Fox) come
> later, one at a time, per RULES.
>
> Builds directly on **#120** (units + sources). Unit convention from there:
> **combat numbers transfer raw; spatial values scale by `PX_PER_UNIT ≈ 5.4`
> px/unit**, anchored on Mario. Primary data source:
> [rukaidata PM3.6 Mario](https://rukaidata.com/PM3.6/Mario/) (datamined from the
> `.pac` files) + [SmashWiki Mario (PM)](https://www.ssbwiki.com/Mario_(PM)).
> Method: cross-checked rukaidata attributes against SmashWiki; one move
> (down-tilt) pulled at full hitbox detail as a worked example. Date: 2026-06-26.

## TL;DR

- **Mario's movement is essentially already shipped.** PM3.6 Mario's weight,
  gravity, jump velocity, walk speed, and jump count map — at 5.4 px/unit —
  almost exactly onto pycats' current global defaults. So the *balanced
  all-rounder feel* is the baseline pycats already has; Mario is the cheapest
  archetype to land.
- **Combat data drops in raw** (frames, %, damage, BKB, KBG, angle). Verified on
  Mario's down-tilt: PM3.6 values (9%, BKB 30, KBG 80, 80°) need no conversion.
- **The real work is structural, not Mario-specific:** moving movement constants
  from global `config.py` into per-character `FighterData` (so the *other* four
  cats can differ), and the #38 combat-core mechanics (multi-hitbox, ground/air,
  shieldstun) that Mario's full kit needs. Most of Mario's *moveset* is gated on
  #38; his *stats + one single-hit move* are buildable now.
- See the **Scope ledger** (§4) for early wins / primary / decisions / further
  scoping / later / deferred / won't-do.

---

## 1. Attribute mapping (PM3.6 Mario → pycats)

`px = unit × 5.4`. Velocities are units/frame → px/frame; gravity units/frame² →
px/frame². "✅ faithful" = pycats' value already matches; "≈ approx" = mapped but
pycats' model differs; "⚠ scope/decision" = needs a call (see §4).

| Quantity | PM3.6 Mario | × 5.4 → px | pycats today | Verdict |
|---|---|---|---|---|
| **Weight** | 100 | (raw, no scale) | `weight=100` default | ✅ **faithful** (Project+ uses 95 — see §4 decision) |
| **Gravity** | 0.095 /f² | 0.51 | `GRAVITY = 0.5` | ✅ **faithful** |
| **Jump y velocity** | 2.395 /f | 12.9 | `JUMP_VEL = 13` | ✅ **faithful** |
| **Jump count** | 2 | — | `MAX_JUMPS = 2` | ✅ **faithful** |
| **Walk max speed** | 1.1 /f | 5.9 | `MOVE_SPEED = 6` | ✅ **faithful** (as *walk*) |
| **Body size** | size mult 0.99 | — | `PLAYER_SIZE 40×60` (≈7.4×11 u) | ✅ reference body (Mario = medium) |
| **Dash/run speed** | 1.5 /f | 8.1 | `MOVE_SPEED = 6` (single) | ⚠ pycats has **no walk/run split** — scope |
| **Air speed (max x)** | 0.86 /f | 4.6 | `AIR_FRICTION 0.85` (no cap) | ≈ approx — pycats models drift via friction, not a terminal velocity |
| **Max fall speed** | 1.7 /f (base) | 9.2 | `MAX_FALL_SPEED = 13` (≈2.4 u) | ⚠ pycats' 13 ≈ Mario **fast-fall** (2.3→12.4); decision |
| **Fast-fall speed** | 2.3 /f | 12.4 | — (no fast-fall) | 🔻 deferred (#38-era mechanic) |
| **Short hop y** | 1.495 /f | 8.1 | — (no short hop) | 🔻 deferred |
| **Jumpsquat** | 4 f | — | instant jump | ⚠ decision (affects feel + goldens) |
| **Ground friction** | 0.06 /f² (decel) | 0.32 | `GROUND_FRICTION 0.5` (×multiplier) | ≈ approx — **different model** (decel vs multiplier), can't map raw |
| **Air accel / friction** | a 0.04 / f 0.016 | — | not modelled separately | 🔻 later |
| **Shield size / strength** | 7.7 / 2.695 | — | `SHIELD_MAX_HP 50`, radius 10–40 | ≈ approx — pycats shield already specced (#12) |

**Key takeaway:** the five core feel constants (weight, gravity, jump, jumps,
walk) are *already* Mario-faithful. pycats was, in effect, tuned to PM Mario.

---

## 2. Moveset mapping

pycats today exposes **one** ground move (`default_cat.py`: a single-hitbox jab,
10%, BKB 30, KBG 100, angle 0, r=12). Mario's real kit is mostly multi-hit /
aerial / special → **gated on #38**. Damage from SmashWiki; per-hitbox BKB/KBG/
angle to be sourced from rukaidata at DEV time.

### Worked example — Down-tilt (`AttackLw3`, the one buildable now)

Pulled at full detail from rukaidata as proof the combat data drops in raw:

| Field | PM3.6 value | → pycats |
|---|---|---|
| Damage | 9 / 9 / 8 (3 hitboxes) | `9.0` (single-hit approx; 3-box needs #38) |
| BKB | 30 | `base_knockback = 30` (raw) |
| KBG | 80 | `knockback_growth = 80` (raw) |
| Angle | 80° | `angle = 80` (raw; low launch) |
| Hitbox size | 2.34–3.91 u | r ≈ 13–21 px (× 5.4); single ≈ **17 px** |
| Active | frames 5–8 | `startup=5, active=4` (raw) |
| Total | 30 f (interruptible @28) | `recovery ≈ 21` (raw) |

→ This is a clean, PM-faithful replacement for the current placeholder attack,
**with zero #38 dependency** — a strong first "real Mario move."

### Full kit — damage + scope

| Move | PM dmg | pycats scope |
|---|---|---|
| Jab (neutral) | 2 / 3 / 5 (multi-hit) | 🔻 multi-hit → #38; single-hit approx (5%) buildable now |
| Dash attack | 9 / 8 | ⚠ needs dash-state; single-hit, near-term |
| F/U/D-tilt | 7–9 | ✅ **single-hit, buildable now** (d-tilt worked above) |
| F-smash | 20 / 15 / 11 (angleable) | 🔻 charge + angle → #38/later |
| U-smash / D-smash | 15–16 / 16–12 | 🔻 → #38 |
| Aerials (N/F/B/U/D) | 9–17; D-air multi-hit | 🔻 ground/air split + multi-hit → #38 |
| **Fireball** (neutral-B) | 7 | 🔻 **no projectile system** — deferred (shared gate w/ Fox blaster) |
| **Cape** (side-B) | 10 / 9 | 🔻 needs reflect/turn mechanic — deferred |
| **Super Jump Punch** (up-B) | 5/1/3 multi-hit | 🔻 multi-hit + recovery semantics — deferred |
| **Tornado** (down-B) | 2/1/5 multi-hit | 🔻 multi-hit + rise — deferred |
| Grab / throws | — | 🔻 **no grab system** — deferred |

---

## 3. Hurtbox

Keep the existing 2-circle vertical stack (`default_cat.py`, r=14 at dy=15/45) as
an **approximation** of Mario's body. Mario's actual datamined hurtboxes
(rukaidata, multiple bone-attached capsules) are a *later refinement* — the
2-circle model is adequate for a medium all-rounder and keeps goldens simple.

---

## 4. Scope ledger

Tagging every piece per your ask — early wins, primary, scoping, decisions,
later, deferred, won't-do.

### 🟢 Early wins (cheap, high value, no #38)
- **Branch `load_fighter_data` to a distinct Mario `FighterData`** — the seam
  already exists (`data.py:18` returns the default for all keys). Weight 100
  already matches → free.
- **Document that Mario's movement feel is already shipped** (the five faithful
  constants above) — no retuning, no golden churn.
- **Replace the placeholder attack with Mario's down-tilt** (real PM3.6 values,
  §2) — first authentic single-hitbox move, no #38 needed.

### 🎯 Primary goals
- **Per-character stat scaffolding:** lift `weight` (path exists:
  `Player(weight)→Fighter.weight→knockback()`) and then movement constants
  (gravity/fall/speed/jumps) out of global `config.py` into `FighterData`, so the
  *other four* cats can differ. For Mario the values equal today's defaults, so
  this lands behaviour-preserving (goldens green) — the ideal first DEV slice.
- **Mario's single-hitbox ground moves** (tilts, dash attack, jab final hit) as
  the schema/state support each.
- **Placeholder FX** for Fireball / Up-B punch / explosions — a flat coloured
  circle or sprite is a *primary goal* (your call), wired to the move's active
  frames. Quality particles are later.

### 🔍 Further scoping needed (open design questions)
- **Walk vs run split** — pycats has one `MOVE_SPEED`; PM has walk 1.1 + dash
  1.5. Needed for Fox (fastest run) too — scope a two-speed ground model.
- **Air-speed model** — pycats uses air friction; PM uses an air-x terminal
  velocity (0.86). Decide whether to add an explicit drift cap.
- **Base-fall vs fast-fall** — pycats has one `MAX_FALL_SPEED`; PM splits 1.7 /
  2.3. Tied to the fast-fall mechanic (#38-era).
- **Ground traction model** — PM friction is a deceleration (0.06 u/f²);
  pycats' `GROUND_FRICTION 0.5` is a velocity multiplier. Different math → can't
  port raw; decide whether to keep the multiplier model.
- **Hurtbox fidelity** — 2-circle approx vs Mario's datamined capsules.

### ⚖️ Decisions to make
- **Canonical version: PM3.6 vs Project+.** Differ on e.g. weight (100 vs 95).
  *Recommend PM3.6* — it's the source you gave and weight 100 = pycats default
  (zero change). Note the choice so all five cats use one version.
- **Confirm `PX_PER_UNIT`.** #120 derived ≈5.4; pick the exact value (5.4, or a
  round 5.0/5.5). Affects every spatial port.
- **`MAX_FALL_SPEED`:** keep 13 (current; ≈ Mario fast-fall) or drop to ~9
  (faithful base fall)? Keeping 13 avoids golden churn but conflates base/fast.
- **Jumpsquat (4f):** add a pre-jump lag for fidelity, or keep instant jumps?
  Affects feel and invalidates jump goldens.
- **When to flip movement to per-character** vs leave global until a non-Mario
  cat needs it.

### 🔧 Later refinement
- Multi-hit moves (jab, d-air, tornado, up-B) — after #38 multi-hitbox.
- Charged smashes, aerial ground/air split, shieldstun interactions — after #38.
- Quality FX / particle systems (placeholders ship first).
- DI/SDI, hitstun-cancel-removal (Phase 3); Sakurai-angle (361) realism;
  per-character gravity → vertical-KB term `(g−0.075)×5`.
- Datamined hurtbox capsules.

### 🔻 Deferred (for now)
- **Fireball projectile** — no projectile system yet (shared gate with Fox's
  blaster). Mario's signature, but the *mechanic* waits; placeholder FX can come
  with it.
- **Cape** (reflect/turn), **Super Jump Punch** (recovery + coin), **Tornado**
  (down-B rise) — special-move mechanics beyond #38's scope.
- **Grabs / throws** — no grab system.
- Short hop, fast-fall, wavedash, L-cancel (some #24-deferred PM tech), walljump,
  footstool, ledge mechanics.

### 🚫 Won't-do
- **3D anything** (your call).
- Frame-perfect parity with PM — pycats is an integer-pixel *approximation*
  (#80); the goal is faithful *feel*, not bit-exact reproduction.
- PAL / 50 Hz.
- Reproducing PM's physics engine (per-attribute air accel/friction curves,
  momentum micro-model) verbatim.

---

## 5. What this hands the DEV ticket

The recommended **first DEV slice** (file when starting, per RULES) is the
**Mario stat scaffolding + down-tilt**, because it's entirely buildable now and
behaviour-preserving:

1. `load_fighter_data("<mario-cat-key>")` returns a distinct `FighterData`
   (weight 100, the 2-circle hurtbox, and the down-tilt move with the §2 values).
2. Thread `weight` from `FighterData` into the `Player`/`Fighter` constructor
   (path already exists).
3. (Optionally, same or next slice) move gravity/fall/speed/jumps into
   `FighterData` as Mario-valued defaults so the other cats have somewhere to
   diverge — golden-safe since Mario's numbers equal today's globals.

Mario's **full moveset** is a later slice, gated on #38 (multi-hitbox, ground/air,
hitlag, shieldstun) and, for specials, on projectile/grab/reflect systems that
are not in #38's scope (deferred above).

## Sources

- [rukaidata PM3.6 Mario](https://rukaidata.com/PM3.6/Mario/) —
  [attributes](https://rukaidata.com/PM3.6/Mario/attributes.html),
  [down-tilt subaction](https://rukaidata.com/PM3.6/Mario/subactions/AttackLw3.html)
  (datamined; primary).
- [SmashWiki Mario (PM)](https://www.ssbwiki.com/Mario_(PM)) — moveset damage,
  Project+ attribute cross-check.
- #120 findings (`docs/research-120-smash-units-and-sources.md`) — unit
  convention, `PX_PER_UNIT ≈ 5.4`, raw-combat rule.
- pycats: `config.py`, `combat/data.py`, `combat/knockback.py`,
  `characters/default_cat.py`, `entities/fighter.py`.
- Epic #117; combat-core gate #38; PM research umbrella #24.
