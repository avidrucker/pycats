# Gnok cat — Project M 3.6 Donkey Kong source-data findings (#781)

> **Child 1 of epic #779** (Gnok — DK-archetype heavyweight bruiser), first of the
> two-step scope: this RESEARCH doc *gathers the raw PM 3.6 DK data* and *records what
> pycats' engine can/can't model*. The follow-up **DESIGN/ARCH ticket** turns this into
> final pycats-scaled `gnok_cat.py` targets + an ordered slice plan. Read-only research.
>
> **Name:** `Gnok` (the DK archetype slot; "Donkey Kong" = the archetype emulated,
> internal id `gnok`). Mirrors the Nalio/Birky/Narz spec pattern (#119 / #229 / #290).
> **Unit convention (#120):** combat numbers transfer raw; spatial/velocity values scale
> by `PX_PER_UNIT = 5.4` (`config.py`), anchored on Mario/Nalio = pycats globals.
> **Primary sources:** [rukaidata PM3.6 Donkey Kong](https://rukaidata.com/PM3.6/Donkey%20Kong/attributes.html)
> + [rukaidata PM3.6 Mario](https://rukaidata.com/PM3.6/Mario/attributes.html) (baseline anchor)
> + [SmashWiki Donkey Kong (PM)](https://www.ssbwiki.com/Donkey_Kong_(PM)) (corroboration; note it
> now reports **Project+** values, flagged below). **Date:** 2026-07-20. **Agent:** DRAGONFRUIT.

## TL;DR

1. **PM DK is a *fast* super-heavyweight, not a slow one.** rukaidata PM3.6 has DK's
   walk (1.2), dash (1.8), air speed (1.1), and jump height (2.8) all **above Mario's**
   (1.1 / 1.5 / 0.86 / 2.395), and he falls faster (term 2.4 vs 1.7). His weaknesses are
   **big body** (combo/juggle food), **low air acceleration** (0.02 vs Mario 0.04 → floaty
   drift, hard to change direction), **slow jumpsquat** (5f vs 4f), and slow-startup
   powerful attacks — **not** ground speed. **This contradicts epic #779's design-target
   line "slow ground/air speed"** — that line was written from the generic
   heavyweight-is-slow trope; the DESIGN ticket should correct it (see §5).
2. **Heaviest weight is the headline trait, and it's pure data.** `weight = 114` (vs Mario
   100) feeds the existing KB formula's only defender term (`200 / (weight+100)`) → DK
   takes ~6.5% less knockback per hit → dies late. No engine work.
3. **Two engine-capability gaps confirmed (§2):** pycats has **no per-character horizontal
   acceleration** (movement is instant-set) and **no per-character / per-platform friction**
   (a single global multiplier). PM DK's *distinctive* fast-heavy momentum + high traction
   are therefore **not expressible as data today** — a fidelity gap tied to **#243**.
4. **No new mechanic needed for V1** (working hypothesis confirmed). DK's V1 identity —
   weight, body size, heavy normals — is pure data on the existing seam. His genuinely-unique
   mechanics (cargo grab/throws, Giant Punch charge, move armor/intangibility) are all
   **deferred** per #779 and each needs an engine that pycats lacks (§4).

---

## 1. Attribute mapping (PM3.6 DK → pycats), deltas from the Mario/Nalio baseline

All PM3.6 values are **verbatim from rukaidata attributes pages**. `px = unit × 5.4`.
pycats baseline (`config.py`, = PM Mario): `weight 100`, `GRAVITY 0.5`, `JUMP_VEL -13`,
`MAX_JUMPS 2`, `MOVE_SPEED 6`, `DASH_SPEED 8`, `MAX_FALL_SPEED 13`, `PLAYER_SIZE 40×60`.
The **"pycats ref (×5.4)"** column is arithmetic for the DESIGN ticket to finalize — **not**
a ratified target.

| Attribute (rukaidata) | PM3.6 DK | PM3.6 Mario | vs Mario | pycats field | pycats ref (×5.4) | Notes |
|---|---|---|---|---|---|---|
| weight | **114** | 100 | **heavier** | `weight` | `114` (raw) | dies late: `200/214=0.935` vs Mario `1.0` |
| size (model scale) | 0.915 | 0.99 | — | — | ⚠ not a body dim | see §1a — model-scale multiplier, NOT px |
| walk max vel | **1.2** | 1.1 | **faster** | `move_speed` | ~6.5 (vs 6) | DK walks *faster* than Mario |
| dash init / run term vel | **1.8** | 1.5 | **faster** | `dash_speed` | ~9.7 (vs 8) | DK dashes *faster* than Mario |
| walk init vel | 0.1 | 0.1 | same | (no accel model) | — | see §2 Q1 |
| ground friction (traction) | **0.08** | 0.06 | higher | (no per-char model) | — | see §2 Q2; #243 |
| air x term vel | **1.1** | 0.86 | **faster** | drift via `AIR_FRICTION` | ~5.9 | pycats has no air-x cap |
| air mobility a | **0.02** | 0.04 | **lower** | (no accel model) | — | DK harder to steer midair |
| air mobility b | 0.02 | 0.02 | same | (no accel model) | — | — |
| air friction x / y | 0.02 / 0.015 | 0.016 / 0.01 | higher | global `AIR_FRICTION 0.85` | — | not per-char in pycats |
| gravity | **0.1** | 0.095 | heavier | `gravity` | ~0.54 (vs 0.5) | small Δ, heavier fall |
| term vel | **2.4** | 1.7 | **faster fall** | `max_fall_speed` | ~13.0 | ≈ pycats default 13 |
| fastfall velocity | 2.96 | 2.3 | faster | (fast-fall deferred #261) | ~16.0 | fast-fall not in engine yet |
| num jumps | 2 | 2 | same | `max_jumps` | `2` | faithful |
| jump y init vel | **2.8** | 2.395 | **higher** | `jump_vel` | ~-15 (vs -13) | DK jumps *higher* than Mario |
| jump y init vel short | 1.7 | 1.495 | higher | (SH not modeled) | ~9.2 | — |
| jump squat frames | 5 | 4 | slower | (jumpsquat not modeled) | — | 1f slower to leave ground |

**Takeaway:** the only pycats-expressible deltas that matter for V1 are **weight (114)**,
**a taller/bigger body** (§1a), **slightly heavier gravity (~0.54)**, and **higher jump
(~-15)** — plus the *choice* of whether to give DK his faster-than-Mario walk/dash/air
(the data says yes; the "slow heavyweight" fantasy says no — a DESIGN call, §5).

### 1a. Body size — the `size` attribute is NOT a body dimension
rukaidata's `size: 0.915` is Brawl's **model-scale multiplier**, not a height/width. DK's
in-game bulk comes from his large **base model + ECB**, which this scalar shrinks slightly.
So it can't be scaled ×5.4 into a `stand_size`. pycats sets body geometry via
`FighterData.stand_size` (#275; Birky = `(40, 44)` off the `(40, 60)` default) and a
matching multi-`Circle` `hurtbox`. **For Gnok, the "big hurtbox" archetype trait is a
DESIGN decision** — pick a `stand_size` taller/wider than default (e.g. `(48, 68)`, TBD)
and a matching hurtbox; the DK note in `combat/data.py` ("DK barely lowers") also implies a
shallow `crouch_size`. The exact box is the DESIGN ticket's call, not sourced from `size`.

---

## 2. Engine-capability findings (the two questions #781 was filed to answer)

### Q1 — per-character horizontal acceleration? **No.**
`systems/movement.py` `step_horizontal` sets `vel.x = ±move_speed` the frame a direction is
pressed (full speed in one frame); `core/physics.py` has no acceleration term, global or
per-fighter. PM, by contrast, gives DK `walk init vel 0.1`, `dash init vel 1.8`, and
`air mobility a/b 0.02` — i.e. **real acceleration/momentum curves**. **Fidelity gap:** DK's
"heavy to get moving, momentum-y once rolling" feel is **not representable as `FighterData`
today**. Gnok's ground speed will be a flat instant-set number like every other cat. This
is the same modelling gap that traction ticket **#243** circles.

### Q2 — per-platform (or per-character) friction? **No.**
pycats friction is a single **global multiplicative** model: `GROUND_FRICTION = 0.5`,
`AIR_FRICTION = 0.85` (`config.py`), applied uniformly by `apply_horizontal_friction`
(`core/physics.py`) — not per-stage, not per-fighter. PM uses a **per-character subtractive**
traction (DK `0.08`, Mario `0.06`). So DK's higher stopping traction is **not expressible**,
and the two models aren't directly convertible (multiplicative-decay vs subtractive-decel).
Picking a per-character traction model is exactly open ticket **#243** (under #117).

**Consequence for V1:** accept both gaps. Gnok differentiates on weight / size / fall /
jump / heavy normals — all data — and leaves accel + traction to the engine-level #243
thread. Neither gap blocks a playable, recognisable heavyweight.

---

## 3. Moveset inventory + per-move frame-data method

rukaidata enumerates DK's PM3.6 subactions (move names below). **Per-move frame data is
gathered at DEV time, one move per slice** (as Nalio #142 / Birky #228 / Narz #294 did) —
not bulk-pulled here — from two sources:
- **rukaidata subaction pages** → per-hitbox `damage`, `angle`, `base_knockback` (BKB),
  `knockback_growth` (KBG), bone/offset, radius → pycats `Hitbox` fields.
- **brawllib_rs datamine** (#614, env live — re-run `-f "Donkey Kong"`) → active/startup/
  endlag **frame lengths** (`subaction.frames.len()`), which rukaidata's HTML hides. See the
  datamine re-run recipe (memory: `brawllib-datamine-env-live`).

**V1 kit (normals only — the DESIGN ticket orders the slices):**
- **Jab:** `Attack11`, `Attack12`
- **Tilts:** `AttackHi3` (u-tilt), `AttackLw3` (d-tilt), `AttackS3S`/`AttackS3Hi`/`AttackS3Lw` (f-tilt + angles)
- **Dash attack:** `AttackDash` (SmashWiki notes **light armor** — armor deferred, author as a plain hit)
- **Aerials:** `AttackAirN`, `AttackAirF`, `AttackAirB`, `AttackAirHi`, `AttackAirLw`

**Deferred (NOT V1 — see §4):** Smashes `AttackHi4*` / `AttackLw4*` / `AttackS4*` (charge);
Grabs/throws `Catch*` / `Throw*` (cargo hold — a whole grab engine); Specials `SpecialN*`
(Giant Punch charge + invuln), `SpecialS`, `SpecialHi` (Spinning Kong recovery), `SpecialLw*`
(Hand Slap).

---

## 4. Mechanic classification — pure-data vs needs-new-engine

| DK trait | pycats today | Verdict |
|---|---|---|
| Heaviest weight → dies late | `weight` feeds KB formula | **pure data ✅** |
| Big body / big hurtbox | `stand_size` + `hurtbox` circles (#275) | **pure data ✅** (DESIGN picks the box) |
| Heavy normals (high dmg + BKB/KBG, slow frames) | `MoveData.hitboxes` + frame windows | **pure data ✅** |
| Higher jump / heavier gravity / faster fall | `jump_vel` / `gravity` / `max_fall_speed` | **pure data ✅** |
| Faster-than-Mario walk/dash/air | `move_speed` / `dash_speed` (flat) | **pure data ✅** (DESIGN decides if kept) |
| Slow-to-accelerate momentum feel | no accel model | **needs engine** (deferred; #243) |
| Higher ground traction | global friction only | **needs engine** (deferred; #243) |
| Fast-fall (2.96) | no fast-fall | **needs engine** (deferred; #261) |
| Cargo grab + throws | no grab/throw engine | **needs engine** (deferred; no ticket yet) |
| Giant Punch charge (+ invuln, 30% max) | no charge mechanic | **needs engine** (deferred; charge #328) |
| Move armor / limb intangibility | no hit-absorption / intangible-hurtbox mechanic | **needs engine** (deferred) |

## 5. Recommendation

- **No new engine mechanic for V1.** Gnok ships as pure `FighterData`: `weight = 114`, a
  larger `stand_size` + hurtbox, `gravity ≈ 0.54`, `jump_vel ≈ -15`, `max_fall_speed ≈ 13`,
  and heavy normals — mirroring the Birky/Narz "swap the data" path at the heavy end.
- **DESIGN ticket must resolve one identity fork:** PM data says DK is a **fast** heavyweight
  (walk/dash/air/jump all above Mario). Epic #779's "slow ground/air speed" line reflects the
  generic trope, not PM3.6. Options for the DESIGN ticket: **(a) faithful** — give Gnok
  above-Mario `move_speed`/`dash_speed` per rukaidata; **(b) fantasy** — keep him slow for the
  classic bruiser feel. This is a game-designer call (per RULES "Changing values"), not a
  data question — surface it to the human. Recommendation: **(a) faithful**, since the whole
  epic thesis is PM-archetype fidelity, and note the slow feel is partly an *accel* gap (§2)
  that flat speed can't fix anyway.
- **Two engine gaps to leave as-is for V1:** per-character acceleration + traction (#243) and
  fast-fall (#261). Neither blocks a recognisable Gnok.
- **Next ticket:** DESIGN/ARCH — set final `gnok_cat.py` scalars + `stand_size`/hurtbox box +
  the ordered move-slice plan, resolving the fast-vs-slow fork above. File one at a time.

## Sources
- rukaidata PM3.6 Donkey Kong attributes — `https://rukaidata.com/PM3.6/Donkey%20Kong/attributes.html` (2026-07-20)
- rukaidata PM3.6 Mario attributes (baseline anchor) — `https://rukaidata.com/PM3.6/Mario/attributes.html` (2026-07-20)
- rukaidata PM3.6 Donkey Kong subactions (moveset inventory) — `https://rukaidata.com/PM3.6/Donkey%20Kong/subactions/`
- SmashWiki Donkey Kong (PM) — `https://www.ssbwiki.com/Donkey_Kong_(PM)` (reports **Project+** values: weight 109, traction 0.08, jumpsquat 5 — corroborating trend, not PM3.6-exact)
- pycats seam: `combat/data.py` (`FighterData`, `load_fighter_data`), `combat/knockback.py`,
  `systems/movement.py`, `core/physics.py`, `config.py`, `characters/roster.py`,
  `characters/body_zones.py`. Engine gaps: traction #243, fast-fall #261, charge #328.
- Sibling specs (format/scaling template): `docs/research-spec-119-mario-cat-pm.md`,
  `docs/research-spec-290-narz-marth-pm.md`; Nalio movement pin #557.
