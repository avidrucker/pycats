# Gnok cat — Project M 3.6 Donkey Kong → pycats DESIGN spec (#794)

> **Child 2 of epic #779** (Gnok — the DK-archetype heavyweight bruiser). Consumes the
> #781 findings (`docs/research/gnok-dk-pm-data-findings.md`) and turns the raw PM3.6 DK
> data into **final pycats `FighterData` targets + body geometry + an ordered move-slice
> plan**. No production code here — this is the ratified spec the DEV children build to
> (mirrors #119 / #229 / #290).
>
> **Name:** `Gnok` (internal id `gnok`) — the DK archetype slot. The archetype is
> mechanical; the skin stays feline.
>
> **Ratified:** 2026-07-20 by the owner (agent DRAGONFRUIT), via a grilling walkthrough.
> Every geometry value below is **measured from PM3.6 data or derived from a measurement**
> — none are eyeballed. Combat/frame values remain `⚠🔬 playtest / rukaidata-confirm-later`
> per [ADR-0003](./adr/0003-hitbox-values-are-playtest-starting-points.md), as for every cat.

## TL;DR

Gnok is a **fast super-heavyweight**: heaviest cat *and* fastest walk/dash/jump (faithful
PM3.6 DK — the "slow heavyweight" trope was rejected, #781). The counterweight is his
**body**: a measured near-square giant (**76×80**, ~2× the default width) that makes him
huge combo-food. V1 ships weight + mobility + the big body + a full striking kit
(normals, aerials, smashes). Grabs/throws, specials, and armor are deferred (no engine).
Authoring is **raw-first through #785** — Gnok is that converter's first consumer.

## 1. Attribute mapping (PM3.6 DK → pycats), deltas from the Mario/Nalio baseline

Faithful to rukaidata PM3.6 DK. Per #120, **combat scalars transfer RAW** (weight, jumps);
**velocity/accel scalars scale ×`PX_PER_UNIT` = 5.4** (they are px-per-frame spatial rates).
Values are authored **raw-first via #785**'s converter (see §5) — the px column is what the
engine sees.

| `FighterData` field | Raw PM3.6 | pycats (×5.4 where spatial) | Default/Nalio | Note |
|---|---|---|---|---|
| `weight` | 114 | **114** (raw) | 100 | heaviest cat — dies latest (only defender term in the KB formula) |
| `move_speed` (walk) | 1.2 | **6.5** | 6 | **fastest-walking cat** |
| `dash_speed` | 1.8 | **9.7** | 8 | **fastest-dashing cat** |
| `jump_vel` | 2.8 | **−15** | −13 | jumps highest |
| `gravity` | 0.1 | **0.54** | 0.5 | falls a touch harder |
| `max_fall_speed` | 2.4 | **13** | 13 | ≈ default |
| `max_jumps` | 2 | **2** (raw) | 2 | default |

**Why faithful even though it fights intuition:** PM DK is genuinely heavy *and* mobile;
he is balanced by a giant hurtbox (§2), not by being slow. Making Gnok slow would be the
generic trope, not PM3.6. The big body below is the intended counterbalance — the two are
a matched pair.

## 2. Body geometry — the "big hurtbox" archetype trait (measured)

The headline trait. #781 §1a established that rukaidata's `size 0.915` attribute is a
**model-scale multiplier, not a body dimension**, so it can't be read off directly. Instead
the body was **measured from PM3.6 idle animation hurtbox extents in world units** (the
`size` multiplier is baked into the bone transforms, so cross-fighter comparison is valid).
Method + reproduction in §6.

### 2a. Stand box — `stand_size = (76, 80)`

PM3.6 idle (`Wait1`) mean hurtbox extent, world units:

| Fighter | Width | Height | w/h |
|---|---|---|---|
| Mario | 9.33 | 13.64 | 0.68 |
| Donkey Kong | 17.88 | 18.06 | 0.99 |
| **DK ÷ Mario** | **×1.92** | **×1.32** | — |

- **Validation:** Mario's real idle ratio (0.68) ≈ the pycats default box ratio (40/60 =
  0.667). The default cat *is* a faithful Mario box, so applying the DK/Mario ratio to it
  is legitimate.
- **DK is far broader than tall** (×1.92 W but only ×1.32 H) — the hunched, long-armed ape
  silhouette (nearly square, 0.99).
- **Applied to the 40×60 default:** 40×1.92 ≈ 77, 60×1.32 ≈ 79 → **`stand_size = (76, 80)`**.

### 2b. Stand hurtbox — 4 circles (measured capsules, symmetrized)

DK's 14 idle hurtbox capsules were dumped in world units and converted to pycats coords
(×4.33 world→px; `dx` from body top-left, `dy` grows down). The raw dump is *one asymmetric
idle pose* (right arm raised); a pycats hurtbox is **static and mirror-flips with facing**,
so the measured reach/radii are **symmetrized**. The owner chose the 4-circle fill:

```python
Circle(dx=24, dy=28, r=22),   # upper-left  (head/chest + L arm)
Circle(dx=52, dy=28, r=22),   # upper-right (head/chest + R arm)
Circle(dx=24, dy=60, r=16),   # lower-left  (L leg)
Circle(dx=52, dy=60, r=16),   # lower-right (R leg)
```

Covers ~dx 2..74, dy 6..76 — fills the broad box; only extreme corners/foot-tips open. (A
denser 6-circle fit — separate head, two wide arms, gut, two legs — is recorded in the #794
grilling if the flanks read too open in playtest.)

### 2c. Crouch box — `crouch_size = (80, 58)` (measured squash)

PM3.6 held-duck (`SquatWait`) mean hurtbox extent vs standing:

| Fighter | Stand H | Crouch H | Crouch÷Stand | Height drop | Width change |
|---|---|---|---|---|---|
| Mario | 13.64 | 7.90 | 0.58 | −42% | ≈0% |
| Donkey Kong | 18.06 | 13.19 | 0.73 | **−27%** | **+5%** |

"DK barely lowers" is true only *relative to Mario* (Mario nearly halves; DK drops a
quarter). Faithful application: height 80×0.73 = **58**; width 76×1.05 = **80** (DK spreads
when ducking). → **`crouch_size = (80, 58)`**. Note: crouch is *wider* than stand here — the
first cat to do so (all others hold stand width); the engine takes any `(w, h)`. Nice
property: at 58 tall, Gnok *crouching* ≈ the default cat *standing* (60) — still huge.

Crouch hurtbox (the measured squash applied to the 4 stand circles, ×80/76 W, ×58/80 H,
r×0.889):

```python
Circle(dx=25, dy=20, r=20),   Circle(dx=55, dy=20, r=20),   # upper
Circle(dx=25, dy=44, r=14),   Circle(dx=55, dy=44, r=14),   # lower (legs)
```

### 2d. Prone

Not an archetype lever — start as a scaled default (`prone_size` ~ (80, 20) with a fitted
hurtbox) or defer to the DEV slice's judgement. ⚠ playtest starting point.

## 3. Archetype identity (what makes Gnok *Gnok*)

- **Fast super-heavyweight.** Heaviest + fastest ground/air mobility (§1). Lives late,
  moves well, hits hard.
- **Giant target.** The 76×80 body (§2) is the balancing weakness — easy to combo, easy to
  hit. This is the whole reason the fast+heavy stats are fair.
- **Heavy normals** (the "attack power" of epic #779): high-damage, high-knockback strikes
  and chargeable smashes (§4). No projectile, no reflector.
- **Deferred identity** (NOT V1, need engine): the grab-based cargo game, Giant Punch
  charge/armor, Spinning Kong recovery. Called out so a future epic can pick them up.

## 4. Moveset mapping (PM3.6 DK → pycats V1 scope)

Per-move frame/hitbox data is pulled **at DEV time** from rukaidata subactions + the
brawllib datamine (`-f "Donkey Kong"`, #614) — *not* bulk-sourced here (as #781 specified).
Subaction names for the `-a` filter:

| pycats move | PM3.6 subaction | V1? | Note |
|---|---|---|---|
| jab | `Attack11` / `Attack12` | ✅ | DK's 1-2 |
| f-tilt | `AttackS3` (`*S3S/Hi/Lw`) | ✅ | |
| u-tilt | `AttackHi3` | ✅ | |
| d-tilt | `AttackLw3` | ✅ | |
| dash attack | `AttackDash` | ✅ | its light armor → author as a plain hit; armor deferred |
| n/f/b/u/d-air | `AttackAirN/F/B/Hi/Lw` | ✅ | d-air = the spike |
| f/u/d-smash | `AttackS4` / `AttackHi4` / `AttackLw4` | ✅ | `chargeable=True` — charge mechanic is live (#371/#377, proven by Narz) |
| grabs / throws | `Catch*` / `Throw*` | ❌ | no grab engine (epic #779's explicit V1 exclusion) |
| specials | Giant Punch / Spinning Kong / Hand Slap | ❌ | bespoke engine each |
| armor / intangibility | — | ❌ | no armor system |

## 5. Scope ledger

**In V1:** weight · mobility scalars · the 76×80 body + crouch · full striking kit (jab,
3 tilts, dash attack, 5 aerials, 3 smashes) · `"gnok"` `load_fighter_data` branch +
`characters/roster.py` registration.

**Out (deferred, engine-gated):**

- **Grabs/throws** — no grab engine. Epic #779's stated V1 exclusion.
- **Specials** — Giant Punch (charge + super-armor), Spinning Kong (multi-hit recovery),
  Hand Slap (ground-shockwave). Each needs bespoke work.
- **Armor / intangibility** — dash-attack light armor and Giant Punch armor both drop.
- **Air-mobility fidelity** — DK's real `air_x 1.1` / `air_accel 0.02` need #787 (which
  needs #785 first). V1 uses the current global air-drift; because `move_speed` is fast,
  drift is already fast (roughly faithful). No inert `air_x_speed`/`air_accel` fields until
  the engine consumes them. Gnok opts in when #787 lands.
- **Per-character traction** — global `GROUND_FRICTION` only; tracked by #243.

**Authoring order (decision 3):** **raw-first through #785**. #785 (store raw + convert via
one `PX_PER_UNIT` function) **lands first**; Gnok is its first consumer, so no pre-scaled
literals are written and then deleted. #785 is a pure refactor of the existing cats
(goldens stay byte-identical — the px results are unchanged).

## 6. Ordered slice plan (DEV children under #779, filed one at a time)

Blocked-by **#785** (raw-first authoring). File each child only when its work begins;
finish it before the next.

1. **Stats + seam + body** — `characters/gnok_cat.py` with the §1 scalars (raw, via #785) +
   the §2 `stand_size` / `hurtbox` / `crouch_size` / `crouch_hurtbox` + the `"gnok"` branch
   in `combat/data.py` `load_fighter_data` + `characters/roster.py` registration. Able-to-
   fail tests: weight → dies-later than default; body-box size = (76, 80).
2. **jab** (`Attack11`/`Attack12`).
3. **tilts** — f/u/d-tilt (`AttackS3` / `AttackHi3` / `AttackLw3`). One move per slice.
4. **dash attack** (`AttackDash`; armor → plain hit).
5. **aerials A** — nair/fair/bair. One per slice.
6. **aerials B** — uair/dair. One per slice.
7. **smashes** — f/u/d-smash (`chargeable=True`). One per slice.

Deferred (NOT V1): grabs/throws, specials, armor/intangibility (§5).

## 7. Reproducing the measurements

All body numbers come from the brawllib_rs datamine (env live, #614; clone at
`~/Documents/Study/Rust/brawllib_rs`, PM3.6 `.pac` under `~/Documents/Study/Rust/pm-data/`).
Two throwaway examples were added to the clone (not vendored into pycats):

```bash
. ~/.cargo/env
# idle bounding box (mean hurtbox extent, world units) — the ×1.92/×1.32 stand ratio + crouch:
cargo run --release --example idle_body_extent -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd -f "Donkey" -a Wait1      # and -a SquatWait, and -f Mario
# per-capsule dump (world center + radius) for the 4/6-circle hurtbox fit:
cargo run --release --example hurtbox_dump -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd -f "Donkey" -a Wait1
```

Both use the crate's own `HighLevelFrame::hurt_box_extent()` (world units, model-scale
baked in) — the same data behind rukaidata's renderer. A body-geometry preview PNG lives in
the gitignored `repros/gnok-body/` (per the repros policy).

## Sources

- **rukaidata.com/PM3.6/Donkey Kong/** — primary DK attribute + subaction data (#781).
- **brawllib_rs datamine** (#614) — idle/crouch hurtbox extents + capsule geometry (§2, §6).
- **#781** `docs/research/gnok-dk-pm-data-findings.md` — the raw-data findings this spec ratifies.
- Cross-refs: raw-units #785 · air-mobility #787 · traction #243 · scaling/spec templates
  #119 / #229 / #290 / #557 · charge mechanic #371 / #377. Seam: `combat/data.py`
  `FighterData` · `characters/roster.py` · `combat/units.py` · `characters/body_zones.py`.
