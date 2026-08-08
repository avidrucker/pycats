# Narz up-B = Marth Dolphin Slash (PM 3.6) — value sourcing

> **Role:** RESEARCH · `area:combat` · closes #1063 · **feeds implementation #1059** (author Narz's
> up-B) — do NOT implement here; this doc supplies the values + option space #1059 consumes.
> **Date:** 2026-08-01 · **Agent:** GRAPE
> **Method:** primary datamine of the PM 3.6 Marth `SpecialAirHi` subaction via brawllib_rs
> `high_level_frame_data` (the #956/#969 toolchain, repeatable) — hitbox scalars, per-frame root-motion
> velocity, and hitbox geometry read from the processed `HighLevelFrame`s. **Independently
> cross-confirmed** against `meleelight`'s Marth `UPSPECIAL` (Melee — a labelled PROXY), whose hitbox
> table and per-frame velocity shape match the PM 3.6 datamine. Every hitbox scalar is **FOUND**; the
> recovery burst is **FOUND-derived** from the animation's net rise. Modeling choices (frame counts,
> body-fit `dx` placement) are labelled and are the human-gated eyeball step, exactly as the Nalio SJP
> (#956/#954) and Birky Final Cutter (#969) up-Bs were authored.

## TL;DR

1. **Hitbox scalars + frame timeline are FOUND (brawllib_rs PM 3.6 primary), and confirmed by a second
   independent primary (meleelight/Melee).** Air Dolphin Slash (`SpecialAirHi`) is a **2-window**
   move: an **initial hit** (frames 4–5) and a **rising multi-hit** (frames 6–10). Each window has
   **3 hitboxes, all `set_id 0`** → by pycats first-box-wins (#130) exactly **one** connects per
   target. The PM 3.6 datamine numbers are **identical** to meleelight's Melee `upb1`/`upb2` tables
   (damage/angle/BKB/KBG/size all match) — i.e. **PM 3.6 kept Melee's Dolphin Slash hitboxes**, so
   these are FOUND for PM 3.6 directly, not a proxy.
2. **Tipper structure confirmed** — the strong box is `id0` (the most-forward box: 13% initial / 7%
   rising, `bkb 80`/`20`), the two weaker base boxes are `id1`/`id2` (10% / 6–7%). Author `id0`
   **first** (tuple order = priority; first overlapping box wins — the Narz #299/#313 tip-first
   pattern).
3. **Recovery burst is FOUND-derived** — `SpecialAirHi`'s per-frame root velocity (`y_vel_temp`),
   integrated, peaks at **47.27 units = 255.3 px** net rise (≈ **1.60× Narz's full-jump height**,
   160 px). Matched to a single SET burst under Narz's pinned `gravity 0.45` (`v = √(2·g·h)`):
   > **`recovery_vy ≈ −15.2`** (`√(2·0.45·255.3) = 15.16`). Datamine-derived, not game-feel.
   The meleelight/Melee velocity table has the **same rise shape** (strong 14–15-unit burst on
   frames 1–2, rapid decay) — a second-source shape confirmation.
4. **Horizontal component — small, near-vertical.** Root x drifts forward ≈ **38 px at apex** (≈ 54 px
   over the whole move). Recommend **`recovery_vx ≈ 0` to ~3** (a small facing-forward push), an
   eyeball/design call in #1059, not load-bearing. Dolphin Slash is player-**angleable** in the source
   (meleelight `upbAngleMultiplier`, ±π/16); pycats' single-burst recovery model does not capture the
   live-angle input, so V1 uses a fixed near-vertical burst — a **documented divergence**, same class
   as the per-frame-curve divergence Nalio/Birky already carry.
5. **No new combat capability required.** pycats already resolves the `angle 361` **Sakurai sentinel**
   (`combat/knockback.py:sakurai_angle`), and Narz already ships `angle=361` moves (`narz_cat.py`).
   The recovery hook (#578) + first-box-wins + Sakurai angle cover the whole move. **No `decision`
   child needed** — every load-bearing value is FOUND or FOUND-derived.

---

## Datamine (reproducible)

```bash
cd ~/Documents/Study/Rust/brawllib_rs && ~/.cargo/bin/cargo run --release \
  --example high_level_frame_data -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd -f Marth -l subaction -a SpecialAirHi
```

`SpecialAirHi` is **40 frames**, `iasa: None`. It carries the **whole air move** — both hitbox windows
(frames 4–10) **and** the complete rise-then-fall root motion (rise peaks frame 20, then descends).
Unlike Kirby's Final Cutter (#969, split across 4 subactions), Marth's Dolphin Slash is a **single
subaction, single upward burst then helpless fall** — a clean, data-only fit for the recovery hook
(#578). (Second source: `meleelight/src/characters/marth/moves/UPSPECIAL.js` +
`marthAttributes.js` — Melee, labelled PROXY.)

---

## 1. Hitbox + frame data (FOUND — brawllib_rs PM 3.6, meleelight-confirmed)

Combat scalars are entered **RAW** (no ×5.4) per `combat/units.py`. `damage`→Dmg, `angle`→trajectory,
`bkb`→BKB, `kbg`→KBG (`combat/collapse.py`). **All boxes `set_id 0`** and **`wdsk 0`** (standard
BKB/KBG knockback, *not* weight-dependent set knockback — unlike Nalio SJP / Birky FC).

### 1a. Window 1 — initial hit (active frames 4–5)

| id | Dmg | angle | BKB | KBG | size | role |
|---|---|---|---|---|---|---|
| **0** | **13.0** | **361** (Sakurai) | 80 | 70 | 3.906 | **tip** (strong) |
| 1 | 10.0 | 74 | 60 | 70 | 3.906 | base |
| 2 | 10.0 | 74 | 60 | 70 | 3.906 | base |

### 1b. Window 2 — rising multi-hit (active frames 6–10)

| id | Dmg | angle | BKB | KBG | size | role |
|---|---|---|---|---|---|---|
| **0** | **7.0** | **361** (Sakurai) | 20 | 90 | 3.906 | **tip** (strong) |
| 1 | 7.0 | 74 | 20 | 90 | 3.906 | base |
| 2 | 6.0 | 74 | 20 | 90 | 3.125 | base |

**Cross-confirmation (meleelight/Melee, `marthAttributes.js`):** `upb1` = `(3.906, 13, 361, 70, 80)` /
`(3.906, 10, 74, 70, 60)` ×2; `upb2` = `(3.906, 7, 361, 90, 20)` / `(3.906, 7, 74, 90, 20)` /
`(3.125, 6, 74, 90, 20)` — **identical** to the PM 3.6 datamine above (size, dmg, angle, KBG, BKB all
match). Independent second primary.

### 1c. Tipper structure (Narz archetype identity)

All three boxes in each window share `set_id 0`, so **exactly one hits per target** (pycats #130
first-box-wins), and the winner is decided by **which box overlaps** + tuple order. `id0` is both the
**highest-damage** box (13/7 vs 10/6–7) and the **most-forward** box (see geometry §1e) → it is the
**tip**. **Author `id0` first** so it wins on overlap at the blade's end — the same tip-first ordering
Narz's tilts/smashes already use (`narz_cat.py`, `angle=361` tippers). Report only; the DEV authors.

### 1d. Frame timeline (FOUND raw → pycats convention)

| Property | Value (datamine) | pycats mapping |
|---|---|---|
| Total animation frames | 40 | — |
| Hitboxes active | **4–10** (window 1: 4–5, window 2: 6–10) | — |
| IASA | None | recovery runs past the hit window |
| **startup** (`first_active − 1`) | 4 → **3** | `startup=3` |
| **active** (`last_active − first_active + 1`) | 10 − 4 + 1 → **7** | `active=7` |

The 3-tuple split is the same faithful mechanical mapping the Nalio/Birky docs document (raw frames
FOUND; the split is convention, not a new source claim). The **move's frame count and the recovery
arc are decoupled** — see §3.

### 1e. Hitbox geometry (FOUND — coordinate map per #956 §0a)

Mapping: pycats `dx ← brawl z` (forward), `dy ← brawl y` (up), `r ← size`, each `× PX_PER_UNIT (5.4)`;
brawl `x` (lateral depth) dropped in the 2-D side view. Radius `u(3.906) = 21 px`, `u(3.125) = 17 px`.

| Window | id | brawl (y_up, z_fwd) | pycats (dx, dy, r) |
|---|---|---|---|
| 1 (f4) | 0 | (3.82, 7.37) | (**40**, 21, 21) |
| 1 (f4) | 1 | (6.37, 4.23) | (23, 34, 21) |
| 1 (f4) | 2 | (6.00, −0.53) | (−3, 32, 21) |
| 2 (f6) | 0 | (14.91, 13.15) | (**71**, 81, 21) |
| 2 (f6) | 1 | (15.35, 9.13) | (49, 83, 21) |
| 2 (f6) | 2 | (11.48, 0.02) | (0, 62, 17) |

**Radii + `dy` map cleanly; `dx` is a body-fit placement** (the Nalio/Birky precedent): the window-2
tip's raw `dx = 71` is a long human-Marth reach that should be **eyeball-adjusted to Narz's cat body**
in the #1059 tuning pass (a player-visible step gated by the eyeball-OK on close). meleelight's Melee
`upb2` offsets show the same upward-sweeping blade (`id0` sweeps `(13.85, 13.53) → (4.78, 27.94)` over
5 frames), corroborating the geometry.

---

## 2. Recovery rise velocity — FOUND-derived

`SpecialAirHi` has no single set-velocity event (`y_vel_modify: None`); the rise is the animation
root's per-frame velocity (`y_vel_temp`). Launch begins frame 5; integrated (∫ velocity), the
**cumulative rise peaks at 47.27 units at frame 20**, then the root descends (helpless fall):

> apex rise = **47.27 × PX_PER_UNIT (5.4) = 255.3 px ≈ 1.60× Narz's full-jump height**
> (160 px, from `jump_vel 12` / `gravity 0.45`: `12²/(2·0.45)`).

pycats models the rise as a **single SET burst + gravity** (a documented divergence from the authored
per-frame curve — identical to Nalio #956 §0b / Birky #969 §2; pycats gives a parabolic arc, not the
source rise curve). Matching the datamined **net rise** under Narz's `gravity 0.45`
(`apex = v²/2g ⇒ v = √(2·g·h)`):

> **`recovery_vy ≈ −15.2`**  (`√(2 · 0.45 · 255.3) = 15.16`). Datamine-derived, not game-feel.

**Second-source shape check (meleelight/Melee, labelled PROXY):** the `setVelocities` y-column is a
strong initial burst that decays fast — frames 1–2 = `14.42, 15.51`, then `8.66, 2.42, 2.12, …` → near
0 by frame 17. The **brawllib PM 3.6** per-frame `y_vel_temp` has the **same profile** — frames 5–8 =
`13.11, 14.10, 7.87, 2.20`. Two independent engines agree on the rise shape (a hard front-loaded burst,
not a sustained climb), which is exactly what the single-SET-burst model approximates. (Melee-unit
magnitudes are **not** convertible to pycats px — only the PM 3.6 brawl-unit integral × 5.4 is; the
Melee table is a shape/lineage cross-check only.)

**Horizontal (`recovery_vx`):** root x drifts forward monotonically — **6.998 units = 37.8 px at apex**
(frame 20), 10.07 units = 54.4 px over the full 40 frames. A minor near-vertical arc. Recommend
**`recovery_vx ≈ 0` to ~3** (a small facing push), an eyeball/design call in #1059. Note the source move
is **player-angleable** (meleelight `upbAngleMultiplier`, ±π/16 ≈ ±11.25° from stick-X in the first
6 frames); pycats' single-burst recovery has no live-angle input, so V1 ships a fixed near-vertical
burst — a divergence to note in #1059, same class as the per-frame-curve divergence.

---

## 3. Frame model (modeling choice — labelled)

Following the Nalio/Birky precedent, the pycats move is authored **rise-only**, launch → apex:

- **startup 3, active 7, recovery = ascent tail** (hit window frames 4–10 per §1d). The move ends
  airborne → routes to `helpless` (#184) via the recovery hook.
- The burst model reaches apex in `v/g ≈ 15.2/0.45 ≈ 34 f` vs the source's 20 f — the **hitbox/lock
  window** (frames) and the **recovery arc** (physics) are decoupled, as they are for Nalio/Birky.
  Narz coasts up on momentum for the upper rise. A feel call for the eyeball pass.

---

## 4. Routing recommendation for #1059 — nothing blocks it

| Value class | Status | Ready to author in #1059? |
|---|---|---|
| Damage / angle / BKB / KBG (both windows, §1a/1b) | **FOUND** (brawllib PM 3.6, meleelight-confirmed) | **Yes** — RAW into hitbox JSON. |
| Tipper structure / box order (`id0` = tip, first) (§1c) | **FOUND** | **Yes** — author `id0` first; `set_id 0` = one hit. |
| Sakurai angle 361 support | **FOUND capability** (`knockback.sakurai_angle`; Narz already ships 361) | **Yes** — no new engine work. |
| Frame timeline: total 40, active 4–10, IASA none (§1d) | **FOUND** | **Yes** — `startup=3 / active=7` (derived). |
| Hitbox size / position (§1e) | **FOUND** | **Yes** — radii + `dy` verbatim; eyeball-adjust `dx` to Narz's body. |
| Recovery `recovery_vy` (§2) | **FOUND-derived** (`≈ −15.2`) | **Yes** — no `decision` child. |
| `recovery_vx` (§2) | ≈ 0–3 (small forward arc; eyeball) | **Yes** — design call, not load-bearing. |
| Recovery model divergences (single burst vs per-frame curve; no live-angle) | Design notes | Document in #1059 (§2/§3). |

**Bottom line:** every value #1059 needs is **FOUND** (hitbox scalars/geometry/frames — two agreeing
primaries) or **FOUND-derived** (`recovery_vy ≈ −15.2`, from the net-rise integral against Narz's
`jump_vel 12 / gravity 0.45`). **No `decision` child is required.** The only remaining human step is the
routine **`dx` placement eyeball-adjust** to Narz's cat body (window-2 tip reach especially) — a
player-visible tuning pass gated by the eyeball-OK on close, same as every other Narz move.
Evidence-sufficiency is Avi's call: the load-bearing gap classes are all closed, but the `dx` body-fit
and the two labelled divergences (per-frame curve; live-angle) are model choices, not sourced numbers.

---

## Refs

- **brawllib_rs datamine — PM 3.6 Marth `SpecialAirHi`:** command above; `HighLevelSubaction` with
  per-hitbox `HitBoxValues` (damage/trajectory/bkb/kbg/wdsk/set_id/size) + per-frame `y_vel_temp` /
  `x_vel_temp` (root motion) + `next_pos`/`prev_pos` (geometry). PM 3.6 overlay `pm-data/pm36-sd`.
- **meleelight (local, #616):** `~/Documents/Study/JavaScript/meleelight/src/characters/marth/moves/UPSPECIAL.js`
  (`setVelocities` per-frame table + `upbAngleMultiplier` angle input) and `.../marth/marthAttributes.js`
  (`upb1`/`upb2` hitbox tables) — **Melee**, labelled PROXY; matches the PM 3.6 datamine exactly on the
  hitbox scalars and on the rise shape.
- **Precedent sourcing docs:** `docs/research/2026-07-31-nalio-super-jump-punch-sourcing.md` (#956, the
  §0a/§0b datamine + net-rise method) · `docs/research/2026-07-31-birky-final-cutter-sourcing.md` (#969).
- **brawllib_rs datamine recipe:** `docs/tooling-brawllib-rs-datamine-recipe.md` (`size × 5.4 → r`;
  `dx ← z`, `dy ← y`; the root-motion path for the rise).
- **pycats seams:** `pycats/combat/units.py` (`PX_PER_UNIT ≈ 5.4`; scalars RAW),
  `pycats/combat/data.py` (`MoveData.grants_recovery/recovery_vy/recovery_vx`, #578/#566),
  `pycats/combat/knockback.py` (`sakurai_angle` = angle-361 sentinel), `pycats/combat/collapse.py`
  (hitbox JSON keys), `pycats/characters/narz_cat.py` (Narz's PM-Marth data + `angle=361` tipper
  precedents; physics pin `weight 87 / gravity 0.45 / jump_vel 12`), data seam
  `pycats/characters/data/narz.json` (`moves`; no `up_b` yet — #1059 adds it).
- **Engine-hardcoded limit / air-dodge precedent:** the recipe's "engine globals NOT in subaction
  scripts" scope boundary — why the rise velocity is derived from root motion, not a lone attribute.
```
