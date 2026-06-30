# Narz cat — Project M Marth → pycats spec (#290)

> Third archetype of the 5-cat epic (#117), after **Nalio/Mario** ✅ and **Birky/Kirby** ◐.
> Maps **Project M 3.6 Marth** (disjointed swordfighter) onto pycats so the DEV children can
> author `FighterData` with confidence. Read-only research → this spec. Mirrors the Nalio
> spec (#119, `research-spec-119-mario-cat-pm.md`) and Birky's scope (#229).
>
> **Name:** `Narz` (canonical, per `docs/current-parity-progress-report.md`). "Marth" =
> the *archetype emulated*; internal ids use `narz`. Unit convention (#120): combat numbers
> transfer raw; spatial values scale by `PX_PER_UNIT ≈ 5.4`, anchored on Mario/Nalio.
> Primary source: [rukaidata PM3.6 Marth](https://rukaidata.com/PM3.6/Marth/) +
> [SmashWiki Marth (PM)](https://www.ssbwiki.com/Marth_(PM)). Date: 2026-06-30. Agent: DRAGONFRUIT.

## TL;DR

1. **Narz's *mobility* is near-Mario — the archetype identity is NOT in the stats.** Marth's
   weight/gravity/speeds sit close to Mario's (lighter, slightly floatier), so the stats slice
   is a small set of deltas off the Nalio/Mario baseline. The distinctive feel is entirely in
   **move geometry**.
2. **Both signature mechanics are confirmed pure data — zero new engine work** (the crux this
   spike resolves):
   - **Disjointed reach** = a `Circle(dx, dy, r)` hitbox offset *beyond* the `Hurtbox` (Nalio
     already does this).
   - **Tipper sweetspot** = a **multi-hitbox** move (#130) with the **tip box authored FIRST**
     (priority = tuple order, `attack.py:36`; "first box that overlaps wins", `combat.py:141`)
     carrying higher `damage`/`base_knockback`/`knockback_growth` than a near-body base box.
   No charge, no projectile, no new mechanic for the core kit.
3. **The real work is move data, sliced one move at a time** (à la Nalio #142 / Birky #228):
   stats scaffolding first, then a tippered forward-tilt as the identity proof, then the rest
   of the ground/air kit. F-smash (charge), Dancing Blade / Dolphin Slash / Counter (specials),
   and grabs/throws are **deferred** (missing mechanics — see §4).
4. **Recommend a `Narz` sub-epic** (mirror Birky's #228) to track the ~6–8 slices.

---

## 1. Attribute mapping (PM3.6 Marth → pycats), as deltas from the Mario/Nalio baseline

`px = unit × 5.4`. Baseline = pycats globals (= PM Mario): `weight 100`, `GRAVITY 0.5`,
`JUMP_VEL 13`, `MAX_JUMPS 2`, `MOVE_SPEED 6`, `MAX_FALL_SPEED 13`. "Δ" = differs from Mario.
Exact PM3.6 values to be **rukaidata-confirmed at DEV time** (as #119 did for per-hitbox data);
values below are canonical Melee/PM Marth starting points.

| Quantity | PM3.6 Marth | vs Mario | → pycats `FighterData` (Δ from baseline) | Status |
|---|---|---|---|---|
| **Weight** | ~87 | lighter (100) | `weight = 87` | ✅ raw; Δ (launched ~15% further) |
| **Gravity** | ~0.085 /f² | floatier (0.095) | `gravity ≈ 0.45` | ≈ Δ — ⚠ confirm + watch jump-arc feel |
| **Jump y velocity** | ~2.1 /f | a touch lower (2.395) | `jump_vel ≈ -12` | ≈ Δ — tall jump comes from low gravity |
| **Jump count** | 2 | same | `max_jumps = 2` | ✅ faithful |
| **Walk / dash** | walk ~1.6 / dash ~1.6 | ~Mario | `move_speed ≈ 6` (single-speed model) | ≈ same — pycats has no walk/run split (#119 open) |
| **Max fall speed** | ~1.8 /f base | ~Mario (1.7) | `max_fall_speed ≈ 13` | ≈ same (fast-fall deferred, #261) |
| **Air speed** | ~0.9 /f | ~Mario (0.86) | drift via `AIR_FRICTION` | ≈ approx (no air-x cap) |
| **Body size** | tall/lanky (~1.05) | taller than Mario | keep `PLAYER_SIZE 40×60` for v1; consider 40×64 | ⚠ minor — flag, keep simple |

**Takeaway:** only **weight (87)** and **gravity (~0.45, floatier)** are meaningful deltas; the
rest ≈ Mario. The stats slice is therefore small and low-risk. *The archetype is the sword,
not the legs.*

---

## 2. Signature mechanics — the crux (confirmed PURE DATA)

### Disjointed reach
A Marth hitbox lives on the blade, **past** the body. In pycats that's a `Circle` whose `(dx,
dy)` puts it beyond the `Hurtbox` circles — exactly what Nalio's jab already does (`dx=54`,
hurtbox at `dy=15/45`). No mechanic needed; it's authored geometry. Narz simply pushes its
attack circles **further out** (larger `dx`, modest `r`) than Nalio.

### Tipper sweetspot
**Engine-verified pure data.** A tippered move is one `MoveData` with **two hitboxes** in the
same active window:

| Box | Tuple position | `Circle` | `damage` | BKB / KBG | Role |
|---|---|---|---|---|---|
| **Tip** | **FIRST** (highest priority) | far out (large `dx`) | higher (e.g. 13%) | high | the spacing/KO hit |
| **Base** | second | near body (small `dx`) | lower (e.g. 8%) | low | the weak close hit |

Because **priority = tuple order** (`attack.py:36`) and the **first overlapping box wins**
(`combat.py:141`), spacing the tip onto the opponent applies the strong hit; getting hit up
close applies the weak base. That *is* the tipper — no sweetspot/sourspot flag required. (WDSK
`set_knockback` #211 is available if a set-knockback tipper is ever wanted, but Marth's tippers
are percent-scaling, so plain `BKB`/`KBG` per box is correct.)

**One thing to verify in the first DEV slice (not a blocker):** confirm via a test that when
both boxes overlap a defender, the **tip** (box 0) resolves — i.e. author order really does
decide, per `combat.py:141`. A one-assert able-to-fail test pins it.

### No projectile, no charge (core kit)
Marth has no projectile (skip the Fox-blaster gate). His tipper *smashes* need a **charge**
mechanic pycats lacks — so the first identity move is a **tippered tilt/aerial**, not the
f-smash (deferred, §4).

---

## 3. Moveset mapping (PM3.6 Marth → pycats scope)

Damage from SmashWiki; per-hitbox BKB/KBG/angle/positions sourced from rukaidata at DEV time
(as #119 did). #38 combat core is **landed** (multi-hitbox/hitlag/ground-air/shieldstun), so
multi-box tippers are buildable now.

| Move | PM role | pycats scope |
|---|---|---|
| **Forward-tilt** | disjoint poke | ✅ **identity proof, buildable now** — 2-box tipper (§2); recommend as the first move |
| Jab / Dancing-Blade-1 | quick poke | ✅ single/▲ multi-input — jab buildable; full Dancing Blade is a special (deferred) |
| Down-tilt / Up-tilt | pokes/anti-air | ✅ buildable (tip+base where applicable) |
| Dash attack | lunging slash | ⚠ needs dash-state; single-box near-term |
| **Forward-air** | iconic spacing aerial | ✅ buildable — disjoint + tipper aerial (ground/air split is in #38) |
| N-air / B-air / U-air / D-air | sword aerials | ✅ buildable (some multi-hit) |
| **F-smash** (tipper KO) | the signature | 🔻 **deferred — no charge mechanic** (charge is the gate, not the tipper) |
| **Dancing Blade** (side-B) | multi-hit string | 🔻 deferred — sequenced-input special, no engine support |
| **Dolphin Slash** (up-B) | recovery | 🔻 deferred — recovery-special semantics |
| **Counter** (down-B) | reactive counter | 🔻 deferred — needs a counter mechanic |
| Grab / throws | — | 🔻 deferred — **no grab system** |

---

## 4. Hurtbox
Keep the existing 2-circle vertical stack (mirror `default_cat.py`/Nalio) as Marth's body
approximation — adequate for v1, keeps goldens simple. A taller/narrower stack (Marth is
lanky) is a later refinement, not a v1 need.

## 5. Scope ledger
- 🟢 **Early wins:** the `narz` `load_fighter_data` branch + a distinct `FighterData` (weight
  87, floatier gravity, 2-circle hurtbox); the **forward-tilt tipper** as the first authentic
  disjoint+tipper move (no new mechanic).
- 🎯 **Primary:** Narz stats scaffolding → tippered ground normals → sword aerials, one slice
  each. The tipper *pattern* (tip-box-first) is reusable across every Narz move.
- 🔍 **Further scoping:** none blocking — the disjoint/tipper crux is resolved here. (Shared
  open items walk/run split + fast-fall + air-cap are #119/#261 concerns, not Narz-specific.)
- ⚖️ **Decisions:** confirm exact PM3.6 Marth attribute values from rukaidata at DEV time;
  pick the v1 body size (keep 40×60 vs 40×64); whether to create the Narz sub-epic (rec: yes).
- 🔻 **Deferred (missing mechanics):** f-smash (charge), Dancing Blade/Dolphin Slash/Counter
  (specials), grabs/throws (no grab system), fast-fall (#261).
- 🚫 **Won't-do:** frame-perfect parity (integer-pixel approx #80); PAL.

## 6. Ordered slice plan (file children one at a time)
1. **Narz stats + body + seam** — `"narz"` branch in `load_fighter_data`,
   `characters/narz_cat.py` (`NARZ_FIGHTER_DATA`: weight 87, gravity ~0.45, jump ~-12,
   2-circle hurtbox), `tests/test_narz_cat.py`, add `narz` to the `watch.py`/char-select roster
   (selectability proper is gated on #117/#127/#268). Behaviour-preserving for other cats
   (goldens green).
2. **Narz forward-tilt — the tipper identity move** — 2-box `MoveData` (tip first, high
   dmg/BKB/KBG; base second, low), plus the **tip-wins-on-overlap** able-to-fail test.
3. **Remaining ground normals** — jab, down-tilt, up-tilt (tippered where canon).
4. **Sword aerials** — n-air, **f-air** (the spacing aerial), b-air, u-air, d-air.
5. *(Deferred children, filed only if/when their mechanic lands)* — f-smash (charge), the
   specials, grabs.

**Sub-epic recommendation:** **create a `Narz` sub-epic** (mirror Birky's #228) to track
slices 2–4+; slice 1 can land under it. ~6–8 slices warrants the tracker.

## Sources
- [rukaidata PM3.6 Marth](https://rukaidata.com/PM3.6/Marth/) (attributes + subactions; primary, datamined).
- [SmashWiki Marth (PM)](https://www.ssbwiki.com/Marth_(PM)) (moveset damage; attribute cross-check).
- pycats: `combat/data.py` (`Circle`/`Hitbox`/`MoveData`, `load_fighter_data`),
  `entities/attack.py:36` + `systems/combat.py:141` (tuple-order priority = tipper),
  `combat/knockback.py` (per-fighter weight), `characters/nalio_cat.py` (authoring template).
- Epic #117; templates #119 (Nalio spec) / #228–#229 (Birky); units #120 (`PX_PER_UNIT`);
  multi-hitbox #130; WDSK #211; canonical PM3.6 (rukaidata).
