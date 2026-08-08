# Smash unit systems + best data sources — can pycats consume raw values? (#120)

> Foundational research for the PM-archetype epic (#117). Decides the unit
> convention every archetype's numbers get entered in, and so logically
> **precedes #119** (Mario spec), which currently assumes "scale spatial values."
>
> Method: targeted web research, each key claim cross-checked against ≥2 sources
> (SmashWiki + the relevant datamining tool/repo) and against the pycats code at
> `config.py` / `combat/knockback.py` / `combat/data.py`. Not run through the
> 100-agent deep-research harness; the core facts (KB formula, 60 FPS, unit =
> decimetre, source coverage) are long-established community knowledge and are
> directly corroborated by primary datamining repos. Date: 2026-06-26.
> Companion to [off-pixel-coordinates-findings.md](./research/off-pixel-coordinates-findings.md)
> (#80), [knockback-launch-physics-findings.md](./research/knockback-launch-physics-findings.md)
> (#43) and [pm-framerate-fidelity.md](./research/pm-framerate-fidelity.md).

## TL;DR

1. **The combat layer drops in raw — zero per-value conversion.** Frames, damage
   %, weight, BKB, KBG, and launch angle all mean the same thing in pycats as in
   PM. pycats' `knockback()` **is the Melee/Brawl/PM formula verbatim** (verified
   term-by-term against SmashWiki), so raw BKB/KBG/weight/damage/percent feed it
   unchanged. This is the bulk of per-archetype data entry.
2. **The spatial layer needs exactly ONE scale constant — and pycats already
   has it.** Smash positions/sizes/speeds/gravity are in abstract "units"
   (1 unit ≈ 1 decimetre); there is **no canonical unit→pixel mapping** in the
   games (the camera zooms; size is "based on feel"). pycats must pick a scale.
   Reverse-deriving from PM Mario, pycats' **existing** gravity, walk speed, and
   jump height all independently land on **≈ 5.4 px per Smash unit** — so pycats'
   movement is *already* de-facto calibrated to PM Mario. Adopt
   **`PX_PER_UNIT ≈ 5.4`** as the documented spatial constant; every other
   archetype's spatial values then fall out with a single multiply.
3. **Best machine-readable sources:** PM → **rukaidata.com (PM 3.6 / Project+)**,
   datamined from the actual game files (full BKB/KBG/angle/damage/hitbox
   coverage) + **SmashWiki PM character pages** for attributes. Melee has the
   single cleanest *pure-JSON* pipeline (`meleeDat2Json`/`meleeFrameDataExtractor`).
   Brawl fallback = **rukaidata/Brawl** (Kurogane Hammer's JSON API is Smash 4 /
   Ultimate only — it does **not** cover Brawl).

---

## Q1 — What are the units? (per game, per quantity)

| Quantity | Melee | Brawl | Project M | Notes |
|---|---|---|---|---|
| **Time** | frame @ 60 Hz | frame @ 60 Hz | frame @ 60 Hz | Universal. All NTSC 60 FPS fixed-timestep; PM inherits Brawl's NTSC clock. PAL builds = 50 Hz (out of scope). Already 1:1 with pycats (`FPS=60`). |
| **Distance / position** | "units" (1 unit ≈ **0.1 m**, a decimetre) | same unit | same (PM = Brawl engine) | Consistent Melee→Brawl→PM. **No fixed unit→pixel** mapping: the camera zooms, and SmashWiki notes size is "based on feel," not real scale. |
| **Hitbox size (radius)** | **256× smaller unit** (radius 2000 ≈ 7.8 standard units) | standard unit | standard unit | ⚠ **Melee-only quirk.** Divide Melee hitbox radii by 256 before comparing to Brawl/PM (or before applying `PX_PER_UNIT`). |
| **Velocity / speed** | units **/frame** | units/frame | units/frame | e.g. PM Mario walk 1.1, dash 1.5/1.55, air 0.86 units/frame. |
| **Gravity / acceleration** | units **/frame²** | units/frame² | units/frame² | e.g. PM Mario gravity 0.095 units/frame². |
| **Fall speed** | units/frame | units/frame | units/frame | PM Mario 1.7 base / 2.3 fast-fall. |
| **Knockback (KB)** | KB magnitude (formula output) | same | same | Dimensionless magnitude → **launch speed = KB × 0.03 units/frame**, decaying **0.051 units/frame** each frame. (Brawl exposes velocity = KB/0.03 = "units per 1000 frames".) |
| **Weight** | scale where **Mario = 100** | same | same | "default" 100; Mario coded 98 (PAL/later) / 95 in Project+. Average ≈ 90–95. Higher = less KB via `200/(w+100)`. |
| **Percent / damage** | % (0–999) | % | % | Damage dealt and accumulated % both feed the KB formula directly. |
| **Angles** | degrees (0° = forward, 90° = up) | degrees | degrees | ⚠ **Special "sentinel" angles** (e.g. **361** = Sakurai angle, 365/366 autolink) are *codes*, not literal degrees — need explicit handling when porting moves. |
| **Shield** | HP 50, special Melee light-shield density | HP 50, drain 0.28/f, regen 0.07/f | Brawl-faithful (+ powershield/parry) | Already researched in [brawl-projectm-fighter-states.md](./research/brawl-projectm-fighter-states.md); pycats models the shield-break stun `(400−p)+90`. |

### The knockback formula is identical Melee→Brawl→PM

SmashWiki gives a single formula from **Melee onward** (Brawl and PM are the same
engine family):

```
KB = ( ( ( ( ( p/10 + p·d/20 ) · 200/(w+100) · 1.4 ) + 18 ) · (KBG/100) ) + BKB ) · r
```

`p` = post-hit %, `d` = move damage, `w` = weight, `r` = situational modifier
(rage/handicap/launch-rate; **1** in normal play). pycats'
`combat/knockback.py`:

```python
growth = ((percent/10.0) + (percent*damage/20.0)) * (200.0/(weight+100.0))
growth = (growth * 1.4) + 18.0
return (growth * (knockback_growth/100.0)) + base_knockback
```

is **term-for-term the same** (with `r = 1`). ✅ Brawl added a vertical-KB gravity
term `(g − 0.075) × 5` that boosts launch for high-gravity characters — pycats has
a single global gravity and does **not** model this yet (flag for a later slice).

---

## Q2 — Can pycats use raw values as-is? (the key question)

**Yes for combat; one scale constant for spatial — and that constant already
exists inside pycats.** Conversion is *not* per-value; it is localised to a
handful of constants.

### (a) Transfers RAW — zero conversion

| Quantity | Why it's raw |
|---|---|
| **Frames** (startup/active/recovery/hitstun/shieldstun) | Both run a fixed 60 Hz tick; `pm-framerate-fidelity.md` already established 1:1. |
| **Weight** | Feeds `knockback()` unchanged. pycats default `weight=100` already **is** the Smash "Mario = 100" convention. |
| **Damage %, accumulated %** | Same %-based system; both feed the formula directly. |
| **BKB / KBG** | The formula *is* the PM formula → BKB/KBG mean the same thing. |
| **Launch angle** | Degrees, same convention (0° = forward, 90° = up) as `Hitbox.angle`. (Except sentinel angles 361/365/366 — handle explicitly.) |

This is the headline: **every per-move combat number a researcher copies from a
PM source goes into `MoveData`/`Hitbox` unchanged.**

### (b) Needs the single spatial scale `PX_PER_UNIT`

Lengths, positions, hitbox radii, body size, walk/run/air speed, gravity, fall
speed, jump velocity/height are in Smash units; pycats works in pixels. Since the
games have **no canonical px/unit** (camera zoom), pycats picks one. The striking
finding: pycats' **existing** constants already encode a consistent scale when
anchored on PM Mario:

| Quantity | PM Mario (units) | pycats default (px) | ⇒ implied px/unit |
|---|---|---|---|
| Gravity | 0.095 /f² | `GRAVITY = 0.5` /f² | **5.26** |
| Walk speed | 1.1 /f | `MOVE_SPEED = 6` /f | **5.45** |
| Full-hop height | 30.19 u | ≈ 169 px (`JUMP_VEL²/2·GRAVITY` = 13²/1.0) | **5.60** |
| Fall speed (base) | 1.7 /f | `MAX_FALL_SPEED = 13` /f | 7.6 → pycats' single global ≈ Mario *fast-fall* (2.3) |
| *(Knockback launch)* | × 0.03 /f per KB | `KNOCKBACK_LAUNCH_FACTOR = 0.085` | **2.83** ⚠ outlier |

Three independent movement quantities (gravity, walk, jump height) cluster at
**≈ 5.4 px/unit** — too tight to be coincidence. pycats' movement was, in effect,
tuned to PM Mario at this scale. The 960 px stage ≈ **177 units** wide at 5.4,
and the 40×60 body ≈ **7.4 × 11 units** — both plausible PM values, so the scale
is self-consistent across size, speed, and stage.

**Recommendation — adopt the convention "PM-native data + one anchored scale":**

1. **Store every per-archetype number in raw PM units** in the data files —
   combat numbers literally raw (they feed the formula), spatial numbers in raw
   PM units too.
2. **Define `PX_PER_UNIT ≈ 5.4`** (a single documented constant) and apply it
   only to lengths/positions/velocities/gravity at the point of use. Because it
   is back-derived from pycats' current gravity/walk/jump, **today's feel ≈ PM
   Mario stays unchanged**, and every *other* archetype (Fox faster, Bowser
   bigger/heavier, Kirby floatier) falls out **proportionally** with one multiply
   — raw reuse with one anchor.
3. This respects #80's verdict (**keep the integer-pixel sim; do not move to
   world units**): `PX_PER_UNIT` is a *data-entry/authoring* conversion, not a
   runtime coordinate change — goldens are untouched.

### (c) Where conversion is genuinely unavoidable / flags

- **`PX_PER_UNIT` itself** — the one unavoidable spatial constant (a one-time
  choice, ≈ 5.4). Everything spatial scales by it.
- **Knockback launch is under-scaled (~2.83 vs the 5.4 movement scale).** At the
  movement scale a faithful launch would be `LAUNCH_FACTOR ≈ 0.03×5.4 ≈ 0.162`,
  `DECAY ≈ 0.051×5.4 ≈ 0.275`; pycats uses 0.085 / 0.145, tuned "by feel" in #43
  so a 10% jab travels ~80 px. **Consequence:** hits currently travel ~half the
  PM distance relative to character mobility. This is a **tuning decision for the
  combat owner**, not a bug — flagged, not resolved here.
- **Melee hitbox radii are 256× smaller** — divide by 256 before applying
  `PX_PER_UNIT` if sourcing hitbox sizes from Melee. PM/Brawl are standard units.
- **Per-character gravity → vertical KB** (`(g−0.075)×5`, Brawl/PM) — not modelled
  (single global gravity). Later slice.
- **Sentinel angles** (361 Sakurai, etc.) — codes, not degrees; need a small
  resolver when porting moves.

---

## Q3 — Best data sources (ranked PM → Melee → Brawl)

Rated on **coverage** (all chars + moves), **accuracy** (datamined vs
hand-transcribed), **format** (machine-readable beats prose).

### Project M — priority 1 (the target game)

| Source | Coverage | Accuracy | Format | Verdict |
|---|---|---|---|---|
| **[rukaidata.com](https://rukaidata.com/) — PM 3.6, PM 3.02, Project+** | All chars, every subaction, every hitbox (damage, BKB, KBG, angle, hitbox id/size) | **Highest** — datamined from raw `.pac` files via open-source [`brawllib_rs`](https://github.com/rukai/rukaidata) | Per-subaction **HTML** + **bincode** + WASM; Discord bot. No clean JSON API, but the generator is open-source → run `brawllib_rs` locally to **dump structured data**. | ⭐ **Primary** for moves/hitboxes. |
| **[SmashWiki PM pages](https://www.ssbwiki.com/Mario_(PM))** (Mario (PM), Pit (PM), …) | Per-character: full attributes (weight, walk/dash/air, gravity, fall, jump heights) **and** per-move BKB/KBG/angle/damage | Community-datamined, cross-corroborated; good | Prose / HTML tables — hand-entry, but complete & human-readable per character | ⭐ **Primary** for attributes + move cross-check. |
| [pmunofficial.com](https://pmunofficial.com/en/) docs; Smashboards PM 3.5/3.6 stat threads | Partial / WIP | Community | Prose / spreadsheets | Secondary cross-check only. |

### Melee — priority 2 (best *pure-JSON* tooling)

| Source | Coverage | Accuracy | Format | Verdict |
|---|---|---|---|---|
| **[meleeFrameDataExtractor](https://github.com/pfirsich/meleeFrameDataExtractor)** + **[meleeDat2Json](https://github.com/pfirsich/meleeDat2Json)** | All chars/moves | High — generated straight from `.dat` files | ⭐ **JSON**, open-source Python (powers [meleeframedata.com](https://meleeframedata.com/)) | Cleanest machine-readable pipeline of any game. |
| **[libmelee](https://github.com/altf4/libmelee)** `framedata` | Broad | Good but **sanitised for bots** ("not binary-compatible with in-game values") | Python API | Convenient; cross-check values. |
| SmashWiki Melee attributes / Magus data dump / ikneedata | Broad | Community tables | Prose/HTML | Reference. |

⚠ Melee KB formula = Brawl/PM (BKB/KBG feed pycats unchanged), but PM **rebalanced**
many values, so Melee numbers differ per character — use Melee only where PM data
is missing or PM is Melee-faithful. Remember the **256× hitbox-unit** quirk.

### Brawl — priority 3 (fallback)

| Source | Coverage | Accuracy | Format | Verdict |
|---|---|---|---|---|
| **[rukaidata.com/Brawl](https://rukaidata.com/Brawl/)** | All chars/moves | Datamined (same pipeline as PM) | HTML + bincode | ⭐ Best Brawl source for our needs. |
| **Kurogane Hammer** + [FrannHammer REST API](https://github.com/Frannsoft/FrannHammer) | **Smash 4 & Ultimate only** | High | JSON / Swagger | ❌ Does **not** cover Brawl — useful only as Smash4/Ult reference. |
| [OpenSA / dantarion](http://opensa.dantarion.com/wiki/Actions_(Brawl)), SmashWiki Brawl | Action IDs, prose | Primary/community | Prose | Engine/state reference (see fighter-states doc). |

**Machine-readability verdict:** Melee wins on *ready-made JSON*
(`meleeDat2Json`). But since the target is **PM**, the practical best is
**rukaidata PM 3.6** (datamined accuracy, full coverage) for moves +
**SmashWiki PM pages** for attributes. For a fully-automated dump, run
`brawllib_rs` against PM 3.6 `.pac` files to emit JSON.

---

## What this hands to #119 (Mario) and the rest of #117

- **Enter PM Mario's combat numbers raw** (frames, %, weight 95, BKB/KBG/angle/
  damage) — no conversion. Source moves from **rukaidata PM 3.6**, attributes
  from **SmashWiki Mario (PM)** (weight 95, walk 1.1, dash 1.5/1.55, air 0.86,
  gravity 0.095, fall 1.7/2.3, jumpsquat 4 f, full hop 30.19 u, short hop 11.763 u).
- **Convert spatial values with `PX_PER_UNIT ≈ 5.4`.** Since this anchor *is*
  today's Mario-ish defaults, #119's "scale spatial values" note is correct —
  but the scale is a **single known constant**, not a per-value guess, and the
  current 40×60 body / `GRAVITY 0.5` / `MOVE_SPEED 6` already sit at it.
- **Flag at hand-off:** knockback launch is under-scaled (~2.83) vs movement
  (~5.4) — decide whether to keep the #43 "feel" tuning or rescale to faithful
  (`LAUNCH_FACTOR ≈ 0.162`, `DECAY ≈ 0.275`).

## Sources

- SmashWiki — [Distance unit](https://www.ssbwiki.com/Distance_unit),
  [Knockback](https://www.ssbwiki.com/Knockback),
  [Weight](https://www.ssbwiki.com/Weight),
  [Mario (PM)](https://www.ssbwiki.com/Mario_(PM)).
- [rukaidata.com](https://rukaidata.com/) + [rukai/rukaidata](https://github.com/rukai/rukaidata)
  ([writeup](https://github.com/rukai/rukaidata/blob/main/docs/writeup.md)).
- Melee: [pfirsich/meleeFrameDataExtractor](https://github.com/pfirsich/meleeFrameDataExtractor),
  [pfirsich/meleeDat2Json](https://github.com/pfirsich/meleeDat2Json),
  [meleeframedata.com](https://meleeframedata.com/),
  [altf4/libmelee](https://github.com/altf4/libmelee).
- Brawl/Smash4/Ult API: [Frannsoft/FrannHammer](https://github.com/Frannsoft/FrannHammer)
  (Kurogane Hammer REST API — Smash 4 / Ultimate).
- pycats code: `pycats/config.py`, `pycats/combat/knockback.py`,
  `pycats/combat/data.py`, `pycats/characters/default_cat.py`.
- Prior pycats research: #80 (off-pixel), #43 (knockback launch), #38 framerate.

## Local reference clones (offline)

Read-only source clones kept under `~/Documents/Study/<Stack>/` — **grep for literals, not run.**

- **meleelight** (`schmooblidon/meleelight`, JS) → `~/Documents/Study/JavaScript/meleelight` (#616).
  A faithful Melee reimplementation that hardcodes engine-hardcoded **literals** rukaidata/brawllib_rs
  cannot give (engine globals, not subaction scripts — see the `rukaidata-engine-hardcoded-limit`
  finding, #215/#222). Confirmed finds:
  - **Smash-charge damage scaling** — `src/physics/hitDetection.js`: `damage *= 1 + (chargeFrames * (0.3671 / 60))`.
    At full charge (`chargeFrames === 60`) this is **×1.3671** — the Melee full-charge multiplier
    (feeds #599 `SMASH_CHARGE_SCALE`). Note the ramp is **60 frames** in Melee (the `/60`, and the
    smash fires at `chargeFrames === 60` in each `characters/*/moves/*SMASH.js`) — meleelight is Melee,
    so it does **not** confirm PM's claimed 59-frame ramp; that stays PM-specific (SmashWiki `Project_M`).
  - **Air-dodge** — `src/characters/shared/moves/ESCAPEAIR.js`: `escapeair_force = 3.1` (the #222 source for `DODGE_AIR_SPEED`).
