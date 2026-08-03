# Birky up-B = Kirby Final Cutter (PM 3.6) — value sourcing (rise-only)

> **Role:** RESEARCH · `area:combat` · **feeds implementation #969** (author Birky's up-B,
> **rise-only** per Avi's 2026-07-31 scope ruling). Mirrors the Nalio SJP sourcing
> (`2026-07-31-nalio-super-jump-punch-sourcing.md`, #956).
> **Date:** 2026-07-31 · **Agent:** CHERRY
> **Method:** primary datamine of the PM 3.6 Kirby `SpecialAirHi2` subaction via brawllib_rs
> `high_level_frame_data` (the #956 toolchain, repeatable) — hitbox scalars, per-frame root-motion
> velocity, and hitbox geometry read from the processed `HighLevelFrame`s. Every hitbox scalar is
> **FOUND**; the recovery burst is **FOUND-derived** from the animation's net rise. Modeling choices
> (frame counts, body-fit placement) are labelled and are the human-gated eyeball step, exactly as
> Birky's whole moveset is authored (`⚠ playtest starting point`, ADR-0003).

## Scope (Avi ruling, 2026-07-31)

Final Cutter has **three phases**: (1) rising slash, (2) fast descending plunge + spike, (3) ground
shockwave beam on landing. Phases 2 & 3 each need **new engine code** — neither is data-only:

- Phase 2 → scripted mid-move downward velocity flip (the recovery hook only does one upward burst
  then natural gravity). Split to **#973**.
- Phase 3 → landing-triggered projectile spawn (projectiles spawn only on an active hitbox frame
  mid-move; no touchdown hook). Split to **#974**.

**#969 = the rising slash + its hitbox + `recovery_vy` only.** This doc sources exactly that.

## Datamine (reproducible)

```bash
cd ~/Documents/Study/Rust/brawllib_rs && cargo run --release --example high_level_frame_data -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd -f Kirby -l subaction -a SpecialAirHi2
```

Kirby's air Final Cutter is split across subactions: `SpecialAirHi` (23 f, ~zero root motion —
pre-jump startup; brawllib renders the full authored animation even where the script transitions
early), then **`SpecialAirHi2`** (36 f) carries the **rise + rising slash + descent**, then
`SpecialAirHi3` (6 f, stationary hitbox = the phase-3 shockwave) and `SpecialAirHi4` (35 f, landing
lag). All rise + the rising slash live in `SpecialAirHi2`.

### Frame timeline (`SpecialAirHi2`, from the per-frame parse)

| Phase | frames | root motion | hitboxes |
|---|---|---|---|
| **Rising slash** (phase 1) | **1–2** | rising | **4 boxes** (ids 0–3) |
| Ascent to apex | 3–18 | rising (∫ peaks f18) | none |
| Descent + plunge hit (phase 2 — **out of #969**) | 19–36 | falling | 2 boxes (ids 0–1) |

## 1. Rising slash — hitbox scalars (FOUND)

The phase-1 slash is **4 boxes, all active frames 1–2, all `set_id 0`** → by pycats first-box-wins
(#130) exactly **one** connects per target (a single hit), lowest overlapping id winning. Verbatim from
the datamine `HitBoxValues`:

| id | brawl pos (x, y_up, z_fwd) | size | damage | angle | wdsk | kbg | bkb | effect |
|---|---|---|---|---|---|---|---|---|
| 0 | (0.0, 3.5, 7.0) | 3.5 | 8.0 | 80 | 117 | 100 | 0 | Slash |
| 1 | (0.0, 3.5, 18.0) | 3.5 | 8.0 | 91 | 117 | 100 | 0 | Slash |
| 2 | (0.0, 13.5, 7.0) | 3.5 | 8.0 | 90 | 102 | 100 | 0 | Slash |
| 3 | (0.0, 13.5, 18.0) | 3.5 | 8.0 | 91 | 102 | 100 | 0 | Slash |

- **Damage 8%**, one hit (all same `set_id`). **WDSK** knockback (`bkb 0`, `wdsk 117/102`, `kbg 100`) —
  the same weight-dependent set-knockback model pycats already ships (`set_knockback` key; Birky's
  utilt/dsmash use it). No new combat capability required.
- **Radius** `u(3.5) = 19 px` (the `u()` unit→px seam; datamine `size` maps cleanly, as validated for
  Nalio in #956 §0a). **Geometry (dx/dy) is a body-fit placement**, not a hard number: the datamine
  boxes span an up-and-forward blade (2 heights × 2 forward reaches). On Birky's small featherweight
  body (40×44) the raw forward reach (`u(18) = 97 px`) is far too long, so dx is drawn in to Birky's
  short-reach convention and dy is zone-anchored (`zone_dy`, #309), matching how every Birky move is
  authored. These are `⚠ playtest starting point`s tuned in the #969 eyeball pass.

## 2. Recovery rise velocity — FOUND-derived

`SpecialAirHi2` has no single set-velocity event; the rise is the animation root's per-frame velocity
(`y_vel_temp`). Integrated (∫ velocity), the **cumulative rise peaks at 54.12 units at frame 18**:

> **apex rise = 54.12 × PX_PER_UNIT = 292.3 px ≈ 2.03× Birky's full-jump height** (144 px, from
> `jump_vel 11` / `gravity 0.42`: `11²/(2·0.42)`).

pycats models the rise as a **single SET burst + gravity** (a documented divergence from the authored
per-frame curve — same as Nalio #956 §0b; pycats gives a parabolic arc, not the source rise curve).
Matching the datamined **net rise** under Birky's `gravity = 0.42` (`apex = v²/2g` ⇒ `v = √(2·g·h)`):

> **`recovery_vy ≈ −15.7`**  (`√(2 · 0.42 · 292.3) = 15.67`). Datamine-derived, not game-feel.

**Horizontal: `recovery_vx = 0`.** Root-motion x is **0.0 on every one of the 36 frames** — Final
Cutter is purely vertical (canon: Kirby's up-B has no horizontal recovery). Sourced as exactly 0, not a
guess (a stronger source than Nalio's small forward drift).

## 3. Frame model (modeling choice — labelled)

The pycats move is authored **rise-only**, spanning launch → apex:

- **startup 2, active 2, recovery 16** (total 20). The slash is active f3–4 (the datamine's 2-frame
  phase-1 window, placed early per the source). Recovery covers the ascent; the move ends near apex →
  airborne exit routes to `helpless` (#184).
- The 23-frame `SpecialAirHi` is treated as animation-only startup (see Datamine note), not fixed
  recovery lag; the plunge/land frames (`SpecialAirHi2` 19–36, `SpecialAirHi3/4`) belong to #973/#974.
- The burst model reaches apex in `v/g ≈ 37` f vs the source's 18 f — the move's frame count (the
  hitbox/lock window) and the recovery arc (the physics) are decoupled, as they are for Nalio. Birky is
  `helpless` for the upper part of the rise, coasting up on momentum. A feel call for the eyeball pass.

## 4. Routing — nothing blocks #969

| Value class | Status |
|---|---|
| Rising-slash scalars (dmg / angle / WDSK / KBG / one-hit) | **FOUND** (datamine, §1) |
| Rising-slash radius | **FOUND** (`u(3.5)=19`, §1) |
| Rising-slash dx/dy placement | body-fit `⚠ playtest starting point` (Birky convention; §1) — eyeball |
| `recovery_vy` | **FOUND-derived** (`≈ −15.7`, §2) |
| `recovery_vx` | **FOUND** (`0`, purely vertical, §2) |
| Frame counts | modeling choice (§3) — eyeball |

No `decision` child required (all load-bearing values FOUND / FOUND-derived). The remaining human step
is the **eyeball-OK** on the rendered move (blade placement + recovery arc) at #969 close — the normal
player-visible tuning gate every Birky move passes.
