# Nalio up-B = Mario Super Jump Punch (PM 3.6) — value sourcing

> **Role:** RESEARCH · `area:combat` · closes #956 · **feeds implementation #954** (author
> Nalio's up-B) — do NOT implement here; this doc supplies the values + option space #954 consumes.
> **Date:** 2026-07-31 · **Agent:** CHERRY
> **Method:** primary datamine of rukaidata's PM 3.6 Mario `SpecialAirHi` subaction (hitbox scalars +
> frame timeline read verbatim from the page's own tables) + the PM 3.6 Mario attributes page; the
> Melee lineage from SmashWiki is used as labelled *context/PROXY*, never as the PM number. Every
> hitbox scalar below is FOUND from rukaidata PM 3.6. The two value classes first flagged as **gaps**
> (hitbox **size/position** and the **recovery rise velocity**) were **both closed by running the
> brawllib_rs datamine — see §0** (added 2026-07-31); §1–§3 below are the original rukaidata-only pass,
> kept for provenance. Inference/recommendation is labelled throughout.

## TL;DR

1. **Hitbox scalars + frame timeline are FOUND (rukaidata PM 3.6 primary).** SpecialAirHi is a
   **4-window multi-hit**: an initial 5% grab-up (frames 3–6, WDSK 130), two 1% linking/hold windows
   (frames 7–9 and 10–13, WDSK-based, 0 hitlag / 0 SDI so opponents can't escape), and a **3% launcher**
   (frames 14–15, **BKB 40 / KBG 140**, angle 50). Total animation **38 frames**, **intangible 3–9**,
   **IASA none**. All damage/angle/BKB/KBG/WDSK values below are verbatim from the page's tables.
2. **Hitbox size + body-relative position are a GAP** — rukaidata renders them only in a client-side
   WebGL model (no numbers in the page text). They live in the same brawllib binary the repo already
   datamines. **Obtainable** via `brawllib_rs high_level_frame_data -f Mario -a SpecialAirHi -l subaction`
   (`hit_boxes[].size / x_pos / y_pos`). The PM pac files + PM 3.6 overlay are already on disk at
   `/home/avi/Documents/Study/Rust/pm-data`; the only blocker is the **gated Rust-toolchain install**
   (cargo is absent — a human-approved dep per the datamine recipe). Until that runs, size/offset are
   **not sourced** and should not be invented.
3. **The recovery rise velocity has NO published primary number.** It is **not** in the PM 3.6 Mario
   attributes page (checked — no `SpecialsHi`/`SpecialAirHi` velocity attribute), matching the repo's
   established "engine-hardcoded, not in subaction attributes" limit (the air-dodge / `DODGE_AIR_SPEED`
   precedent). In Melee it lives as a **character-hardcoded per-frame velocity table** (the same idiom
   `meleelight` encodes as `setVelocities` for the 5 characters it ships — **Mario is not one of them**).
   In PM (Brawl engine) the rise is the SpecialAirHi animation's **root-motion translation**, which the
   brawllib datamine *can* measure per-frame — so a faithful number is **obtainable via the same gated
   datamine**, but is **not** a single clean attribute. **No faithful Smash-unit value is in hand today.**
4. **pycats already has the up-B model** — `MoveData.grants_recovery` / `recovery_vy` / `recovery_vx`
   (#578/#566). `recovery_vy` is a **single SET burst on move start**, then gravity takes over. That is a
   **documented divergence** from Melee's per-frame velocity table: pycats gives a parabolic arc, not the
   authored rise curve. #954 authors the move; **it needs a human `decision` on the burst magnitude**
   unless the datamine (item 3) is run first. §2 lays out the option space (with g = 0.5, apex height
   h ⇒ burst = √h — a clean back-solve).
5. **WDSK multi-hit is fully representable in pycats today** — `combat/knockback.py:set_knockback()` +
   the `wdsk` hitbox JSON key (`combat/collapse.py`) implement weight-dependent set knockback, and Nalio
   already ships WDSK/same-set multi-hit moves (u-tilt, d-smash). No new combat capability is required for
   the hitboxes; the launcher and all linking hits map directly.

---

## 0. Datamine resolution (2026-07-31) — BOTH gaps closed (brawllib_rs, PM 3.6 primary)

> Update supersedes the two GAPs flagged in the TL;DR. The gated brawllib_rs datamine was **run**
> (toolchain present after all — `cargo 1.92` via rustup; the "cargo absent" note was a PATH gap in the
> prior subshell). Command (reproducible):
> ```bash
> cd ~/Documents/Study/Rust/brawllib_rs && cargo run --release --example high_level_frame_data -- \
>   -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
>   -m ~/Documents/Study/Rust/pm-data/pm36-sd -f Mario -l subaction -a SpecialAirHi
> ```
> (`-m` is the PARENT of the `projectm` mod dir — brawllib scans `*/pf/fighter`; `-d` is the dir holding
> `fighter/`.) The processed `HighLevelHitBox` carries `next_pos` (Point3, units) + `next_size` (units),
> and each frame carries `y_vel_temp` = the animation root's per-frame vertical velocity (units/frame).
> **The datamine's hitbox scalars match §1b's rukaidata read exactly** (independent cross-confirmation).

### 0a. Hitbox geometry — FOUND (was §1d gap)

Per-window `next_pos`/`next_size` (representative active frame; positions drift ≤2px across a window).
Coordinate mapping (validated below): pycats `dx ← brawl z` (forward), `dy ← brawl y` (up), `r ← size`,
each `× PX_PER_UNIT (5.4)`; brawl `x` (lateral depth) is dropped in the 2-D side view.

| Window (rukaidata f) | ID | brawl (y_up, z_fwd, size) | pycats (dx, dy, r) | Dmg | Angle |
|---|---|---|---|---|---|
| A: 3–6 | 0 | (4.9, 6.0, 7.42) | (33, 27, **40**) | 5 | 70 |
| A: 3–6 | 1 | (2.9, 4.5, 5.08) | (24, 16, **27**) | 5 | 90 |
| B: 7–9 | 0 | (5.5, 6.0, 6.25) | (32, 30, **34**) | 1 | 74 |
| B: 7–9 | 1 | (2.1, 5.2, 5.08) | (28, 13, **27**) | 1 | 78 |
| C: 10–13 | 0 | (5.7, 4.9, 6.25) | (26, 31, **34**) | 1 | 72 |
| C: 10–13 | 1 | (3.0, 5.0, 5.08) | (27, 16, **27**) | 1 | 78 |
| **D: 14–15** | 0 | (6.7, 1.5, 8.79) | (8, 36, **47**) | 3 | 50 |
| **D: 14–15** | 1 | (2.6, 0.1, 3.91) | (1, 14, **21**) | 3 | 50 |

**Radius mapping validated against shipped data:** datamining Mario's jab (`Attack11`) yields radii
`19 / 13 / 15` px — **identical** to committed `nalio.json` jab `[54,27,**19**] / [44,28,**13**] /
[34,29,**15**]`, confirming `size × 5.4 → r` and that Nalio's existing hitboxes were authored from this
same datamine. **Positions are a faithful STARTING point, not a hard number:** the jab check shows the
author kept datamined radii verbatim but **hand-stylised the horizontal `dx`** (raw z→66/33/24 became an
even 54/44/34) to sit on Nalio's cat body, which differs from Mario's. So #954 should seed from the table
above and **eyeball-adjust `dx` to Nalio's body** (a player-visible tuning step, per the existing-move
precedent) — radii + `dy` map cleanly; `dx` is placement.

### 0b. Recovery rise velocity — FOUND-derived (was §2 gap)

`SpecialAirHi` applies the rise as the animation root's per-frame velocity (`y_vel_temp`; `y_vel_modify`
is `None` — no single "set-velocity" event, so there is no one attribute to copy). The curve, integrated:

- Peak per-frame velocity ≈ **9.4 units/f** (frame 7) — but it decays and reverses over the move, so the
  peak is **not** the recovery height.
- **Cumulative rise (∫ velocity) peaks at 44.4 units = 239.7 px ≈ 1.42× Nalio's full-jump height** (169 px).

pycats models the rise as a **single SET burst + gravity** (a documented divergence from the per-frame
curve — §2b). Matching the datamined **net rise** (239.7 px) under Nalio's `gravity = 0.5` (apex = v²/2g,
so v = √(2·g·h) = √h):

> **`recovery_vy ≈ −15.5`**  (√239.7 = 15.48). Lands inside the −13…−16 band §2c predicted from
> SmashWiki's "poor recovery / reduced range." This is now **datamine-derived**, not a bare game-feel pick.

Horizontal: net forward drift ≈ **111 px** over 38 f (avg 0.54 u/f) — a minor near-vertical arc. Recommend
**`recovery_vx ≈ 0` to ~3** (a small facing-forward push), an eyeball/design call in #954, not load-bearing.

### 0c. Updated routing — nothing blocks #954

| Value class | Was | Now |
|---|---|---|
| Hitbox scalars + frame timing | FOUND (rukaidata) | FOUND (datamine-cross-confirmed) |
| Hitbox size / position | GAP (WebGL-only) | **FOUND** (§0a) — radii verbatim; `dx` eyeball-adjust to Nalio's body |
| Recovery `recovery_vy` | GAP / needs decision | **FOUND-derived** (§0b) — `≈ −15.5` from the net-rise integral |
| `recovery_vx` | — | ≈ 0–3 (small arc; eyeball) |

#954 can author the whole move now (no `decision` child required). The only remaining human step is the
**`dx` placement eyeball-adjust** to fit Nalio's cat body — a normal player-visible tuning pass, gated by
the human eyeball-OK on close, exactly like every other Nalio move.

---

## 1. Hitbox + frame data (FOUND — rukaidata PM 3.6 primary)

**Source:** `https://rukaidata.com/PM3.6/Mario/subactions/SpecialAirHi.html` (the house-canonical
per-move source, #614/#120). Column set read verbatim from the page's own hitbox tables:
`Set | ID | Dmg | WDSK | BKB | KBG | Angle | Effect | Sound | (Hitlag Mult | SDI Mult) | Shieldstun | Hitlag`.
`WDSK` = **weight-dependent set knockback**; when present it drives the hit's launch and BKB is 0.

### 1a. Frame timeline (page's own labels, verbatim)

| Property | Value (verbatim) | pycats mapping |
|---|---|---|
| Total animation frames | **38** (`Frames:38`) | — |
| Fully intangible | **3–9** (`Intangible:3-9`) | (informational; pycats has no per-move intangibility field yet) |
| Hitboxes active | **3–15** (window labels 3-6 / 7-9 / 10-13 / 14-15) | — |
| IASA | **None** (`IASA:None`) | recovery runs to the last frame |
| **startup** (derived, pycats convention `first_active − 1`) | first active = 3 → **2** | `startup=2` |
| **active** (derived, `last_active − first_active + 1`) | 15 − 3 + 1 → **13** | `active=13` |
| **recovery** (derived, `total − startup − active`, no IASA) | 38 − 2 − 13 → **23** | `recovery=23` |

Startup/active/recovery are **derived** from the FOUND raw frames using the same rule the existing Nalio
moves document (`nalio_cat.py`, e.g. AttackHi3 "active 5-11 → startup 4 / active 7"). The raw frame
numbers are FOUND; the 3-tuple split is a faithful mechanical mapping, not a new source claim.

### 1b. Hitbox scalars — all 4 windows (RAW = rukaidata verbatim)

Combat scalars are entered **RAW** (no ×5.4) per `combat/units.py`. `wdsk`/`bkb`/`kbg`/`angle`/`damage`
below are the exact page numbers. Each window has two hitboxes (ID 0, ID 1).

| Window (frames) | ID | Dmg | WDSK | BKB | KBG | Angle | Effect | Shieldstun | Hitlag | Role |
|---|---|---|---|---|---|---|---|---|---|---|
| **A: 3–6** | 0 | 5 | 130 | 0 | 100 | 70 | Coin | 4 | 4 | initial grab-up |
| **A: 3–6** | 1 | 5 | 130 | 0 | 100 | 90 | Coin | 4 | 4 | initial grab-up (straight up) |
| **B: 7–9** | 0 | 1 | 110 | 0 | 100 | 74 | Coin | 2 | 0 | link/hold (0 hitlag, 0 SDI) |
| **B: 7–9** | 1 | 1 | 150 | 0 | 100 | 78 | Coin | 2 | 0 | link/hold |
| **C: 10–13** | 0 | 1 | 90 | 0 | 100 | 72 | Coin | 2 | 0 | link/hold |
| **C: 10–13** | 1 | 1 | 120 | 0 | 100 | 78 | Coin | 2 | 0 | link/hold |
| **D: 14–15** | 0 | 3 | — | **40** | **140** | 50 | Coin | 3 | 3 | **final launcher** |
| **D: 14–15** | 1 | 3 | — | **40** | **140** | 50 | Coin | 3 | 3 | **final launcher** |

Notes on the FOUND numbers:
- **Windows B & C carry `Hitlag Mult 0` and `SDI Mult 0`** (verbatim extra columns on those tables) — the
  classic auto-link "hold" hitboxes that keep the opponent captured through the rise.
- **The launcher (D) has no WDSK column** — it uses standard BKB 40 / KBG 140, i.e. real growing knockback.
- **`Effect: Coin` / `Sound: Coin`** on every hitbox — the coin visual/SFX flavor, not a knockback modifier.
- pycats hitbox JSON keys map 1:1: `damage`→Dmg, `angle`→Angle, `bkb`→BKB, `kbg`→KBG, `wdsk`→WDSK
  (`combat/collapse.py`). Shieldstun/Hitlag have no per-hitbox pycats field today (informational).

### 1c. Multi-hit structure — cross-check with the Melee lineage (labelled PROXY/context)

SmashWiki *Super Jump Punch* (Melee section, verbatim): *"the starting hit deals 5%, the seven rising
hits deal 1% each, and the final hit deals 3%"* — the 5 / 1×n / 3 shape matches PM's 5% grab-up → 1% link
windows → 3% launcher exactly. This is **corroborating context only**: Melee's SJP is 12 hitboxes over
frames 3–24 (per FightCore / community frame data), whereas PM 3.6 condensed it to the 4 windows / 38
frames read above. **Use the rukaidata PM numbers; the SmashWiki/Melee framing is lineage, not the PM
value.** SmashWiki also characterizes the move (verbatim): *"From Super Smash Bros. Melee onward, this
range was reduced, causing it to become an overall rather poor recovery move"* — relevant to §2 (the rise
is deliberately modest, not a blowout recovery).

### 1d. GAP — hitbox size (radius) + body-relative position

**Not sourced.** rukaidata's PM 3.6 subaction page exposes size/x_pos/y_pos **only** through its
client-side WebGL model (the page carries a base64 `subaction_data` blob = the brawllib binary; the text
tables contain no Size/Bone/offset columns). So there is **no primary number to quote** for radius or
offset here.

**Where it lives + how to get it (precise):** the same brawllib data the repo already datamines
(`docs/tooling-brawllib-rs-datamine-recipe.md`). The processed `HighLevelFighter` tree exposes per hitbox
`size`, `x_pos`, `y_pos` (and `hitbox_id`). Command:

```bash
cd ~/Documents/Study/Rust/brawllib_rs
cargo run --release --example high_level_frame_data -- \
  -d /home/avi/Documents/Study/Rust/pm-data/brawl-dump \
  -m /home/avi/Documents/Study/Rust/pm-data/pm36-sd \
  -f Mario -a SpecialAirHi -l subaction
```

The pac files **and** the PM 3.6 overlay are already present (verified on disk). **The only blocker is the
gated Rust-toolchain install** — `cargo` is absent (`which cargo` → nothing), and installing rustup/1.92
is a human-approved dependency per the recipe's "gated prerequisites." Once run, `size`/`x_pos`/`y_pos`
map to pycats via `u(units) = round(units × 5.4)` (integer px). **Until then, size/offset are a documented
gap — do not fabricate them.** (Interim option for #954: reuse Nalio's existing up-tilt/jab hitbox
geometry as a visibly-labelled placeholder, but that is a design choice, not a source.)

---

## 2. Recovery launch burst (the rise) — GAP + option space

### 2a. What was checked, and why there is no primary number

| Source | Result |
|---|---|
| rukaidata **PM 3.6 Mario attributes** page | **No** `SpecialsHi` / `SpecialAirHi` / up-special velocity attribute. It publishes jump/gravity attrs only: `jump y init vel 2.395`, `air jump y mult 0.9`, `gravity 0.095`, `term vel 1.7`, `num jumps 2`. None govern the SJP rise. |
| rukaidata SpecialAirHi **subaction** text | Hitbox tables + GFX/SFX/Goto script tabs only; the rise is not a quotable velocity command in the page text (it is inside the WebGL `subaction_data` blob). |
| **meleelight** (local Melee sim, #616) | Implements up-specials as a **per-frame `setVelocities` table** (e.g. Falcon), confirming the Melee idiom — but ships only falco/falcon/fox/marth/puff. **Mario is not implemented**, so no value here. |
| SmashWiki / FightCore | Publish startup/hitboxes/duration, **not** the initial vertical velocity or per-frame rise table. |

**Conclusion (plain):** no primary source publishes Mario's SJP rise as a Smash-unit number. It is a
**character-hardcoded rise** — in Melee a per-frame velocity table in the character special code (engine /
DOL, like air-dodge, the repo's `DODGE_AIR_SPEED` precedent); in PM the SpecialAirHi animation's
**root-motion translation**. The PM rise **is** measurable via the gated brawllib datamine (per-frame
subaction positions of the `TransN` root, the same mechanism `idle_body_extent`/`gif_generator` use for
amplitude), but that requires the same toolchain install as §1d and yields a per-frame curve, not one
clean attribute. **No faithful value is in hand today.**

### 2b. How pycats models the rise (and the divergence to document)

`MoveData` already has the up-B model (`combat/data.py`, #578/#566): `grants_recovery=True` applies
`recovery_vy` as a **SET** vertical burst **once, on move start** (negative = up, like `jump_vel`), plus an
optional facing-relative `recovery_vx`; the fighter routes into `helpless` if it ends airborne. So pycats
gives a **single-burst parabola** (rise decelerating under `gravity=0.5`), **not** Melee's authored
per-frame velocity table. This is an **acceptable, already-established simplification** — #954 does not
need a new engine; it needs one `recovery_vy` (and maybe a small `recovery_vx`) number. **Document this as
a deliberate divergence** in #954: "pycats models SJP rise as one SET vertical burst + gravity; Melee/PM
apply a per-frame rise curve."

### 2c. Option space for the burst magnitude (for a downstream human `decision`)

Nalio's pinned anchors (FOUND, `pycats/config`): `jump_vel = −13`, `gravity = 0.5`, `max_jumps = 2`,
full-jump apex `h = v²/(2g) = 13²/1 = 169 px`. Because **g = 0.5**, the rise-height back-solve collapses to
a clean identity: for a target apex `h` px, the required burst magnitude is `v = √(2·g·h) = √h`. And if a
faithful Smash-unit rise `V` is ever datamined, the mapping is `recovery_vy = −vel(V) = −round(V × 5.4, 2)`.

| Design target (apex above launch) | Burst `recovery_vy` (via `v = √h`, g = 0.5) | Relation to Nalio's full jump |
|---|---|---|
| 169 px | **−13.0** | == one full jump |
| 220 px | −14.83 | ~1.3× jump height |
| 250 px | −15.81 | ~1.5× jump height |
| 300 px | −17.32 | ~1.8× jump height |
| 338 px | −18.38 | 2× jump height |
| 400 px | −20.0 | ~2.4× jump height |

Three routes for #954's owner to pick from:
1. **Datamine-faithful (best):** run the gated brawllib datamine (§1d command), measure the SpecialAirHi
   root-motion peak rise in Smash units `V`, set `recovery_vy = −vel(V)`. Turns this GAP into FOUND.
2. **Ratio to the pinned jump anchor:** choose a multiple of Nalio's `jump_vel` (−13). A design number, not
   sourced.
3. **Chosen apex height → back-solve:** pick a target px apex, read `v = √h` from the table. A design
   number, not sourced.

**Recommendation (NOT a decision — evidence + a lean):** SmashWiki characterizes Melee-onward SJP as a
*"rather poor recovery move"* whose vertical range was *reduced* — i.e. it rises **modestly**, roughly on
the order of a full jump, not a blowout. Absent the datamine, a placeholder in the **−13 to −16** band
(apex ≈ 169–256 px, ~1–1.5× Nalio's jump) reads as faithful-feeling and is easy to re-pin once §1d/route-1
is run. Keep `recovery_vx` ≈ 0 (SJP is near-vertical) or a small facing value for arc — also a design call.
**The final number is ratified in #954 or a `decision` child, not here.**

---

## 3. Routing recommendation for #954

| Value class | Status | Ready to author in #954? |
|---|---|---|
| Damage / angle / BKB / KBG / **WDSK** (all 4 windows, §1b) | **FOUND** (rukaidata PM 3.6, verbatim) | **Yes** — RAW, straight into hitbox JSON (`damage/angle/bkb/kbg/wdsk`). |
| Frame timeline: total 38, active 3–15, intangible 3–9, IASA none (§1a) | **FOUND** | **Yes** — `startup=2 / active=13 / recovery=23` (derived per pycats convention). |
| Multi-hit / WDSK combat support (§ TL;DR 5) | **FOUND capability** (`knockback.set_knockback`, `wdsk` key) | **Yes** — no new engine work; mirror Nalio's existing WDSK/same-set moves. |
| Hitbox **size / position** (§1d → §0a) | ~~GAP~~ → **FOUND** (datamine, §0a) | **Yes** — radii verbatim (`size×5.4`, jab-validated); seed positions from §0a and eyeball-adjust `dx` to Nalio's body. |
| Recovery **rise velocity** `recovery_vy` (§2 → §0b) | ~~GAP~~ → **FOUND-derived** (datamine, §0b) | **Yes** — `≈ −15.5` (net-rise integral, 239.7 px ≈ 1.42× jump). No `decision` child needed. |
| Recovery model divergence (single burst + gravity vs per-frame curve) | Design note | Document it in #954 (§2b). |

**Bottom line (post-datamine, §0):** the datamine was run, so **every value #954 needs is now FOUND** —
hitbox scalars + frame timing (rukaidata, datamine-cross-confirmed), hitbox size/position (§0a), and the
rise velocity `recovery_vy ≈ −15.5` (§0b, net-rise integral). **No `decision` child is required.** #954's
only human step is the routine `dx` placement eyeball-adjust to Nalio's cat body (a player-visible tuning
pass gated by the eyeball-OK on close, same as every other Nalio move). §1–§2 are retained as the
rukaidata-only provenance trail behind §0.

---

## Refs

- **rukaidata PM 3.6 Mario — SpecialAirHi (Super Jump Punch):**
  `https://rukaidata.com/PM3.6/Mario/subactions/SpecialAirHi.html` (hitbox tables + frame labels,
  read verbatim; size/position rendered only in its WebGL model).
- **rukaidata PM 3.6 Mario — attributes:** `https://rukaidata.com/PM3.6/Mario/attributes.html`
  (no up-special velocity attribute; jump/gravity attrs quoted in §2a).
- **SmashWiki — Super Jump Punch:** `https://www.ssbwiki.com/Super_Jump_Punch` (Melee damage shape
  "5% / seven 1% / final 3%"; "rather poor recovery move" — labelled lineage/context, not the PM number).
- **brawllib_rs datamine recipe:** `docs/tooling-brawllib-rs-datamine-recipe.md` (`HighLevelFighter`
  `hit_boxes[].size/x_pos/y_pos`; gated toolchain; the size/position + root-motion path).
- **Engine-hardcoded limit / air-dodge precedent:** the recipe's "engine globals NOT in subaction scripts"
  scope boundary (`DODGE_AIR_SPEED`, #215/#222) — why the rise velocity isn't a rukaidata attribute.
- **meleelight (local, #616):** `~/Documents/Study/JavaScript/meleelight` — up-specials as per-frame
  `setVelocities` tables (Falcon idiom); Mario not implemented → no value.
- **pycats seams:** `pycats/combat/units.py` (`PX_PER_UNIT ≈ 5.4`; `u()` px, `vel()` px/frame, scalars RAW),
  `pycats/combat/data.py` (`MoveData.grants_recovery/recovery_vy/recovery_vx`, #578/#566),
  `pycats/combat/knockback.py` (`set_knockback` = WDSK), `pycats/combat/collapse.py` (hitbox JSON keys),
  `pycats/config` (`jump_vel −13`, `gravity 0.5`, `max_jumps 2`, `max_fall_speed 13`),
  `pycats/characters/nalio_cat.py` (existing PM-Mario-calibrated Nalio data + WDSK move precedents).
</content>
