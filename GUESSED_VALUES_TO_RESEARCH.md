# Guessed values to research — PM-faithful air dodge (#184)

Tracking doc for tuning constants that the PM-faithful (Melee-style) air dodge (#184)
needs but which **could not be sourced authoritatively in pycats' units**. Each row
is either **FOUND** (canon, cited) or **GUESS** (a marked starting value — replace
with a researched/playtested number). Umbrella ticket: **#192**.

**Why so many guesses:** SmashWiki/Smashboards give Melee/PM mechanics *qualitatively*
and some Melee **frame** data, but (a) no Project-M-specific air-dodge numbers (the wiki
covers Melee/Brawl/4/Ultimate; PM "= Melee model"), and (b) all magnitudes are in
Melee's internal engine units, which **do not map** to pycats' 960×540 / `GRAVITY=0.5`
/ `JUMP_VEL=-13` / `DODGE_TIME=14` scale. So pycats-unit magnitudes are derived from
pycats' own existing constants for internal consistency, not from canon.

Sources consulted: SmashWiki [Air dodge](https://www.ssbwiki.com/Air_dodge),
[Wavedash](https://www.ssbwiki.com/Wavedash), [Helpless](https://www.ssbwiki.com/Helpless);
rukaidata [PM3.6 Mario `EscapeAir`](https://rukaidata.com/PM3.6/Mario/subactions/EscapeAir.html)
(datamined subaction) + [FightCore](https://www.fightcore.gg/) Melee frame data; plus the prior
research `docs/research/air-dodge-vertical-momentum-findings.md` (#23) and the full sourcing pass
in `docs/research/pm-air-dodge-values-sourcing.md` (#192/#216).

## Air dodge core (#184 this slice)

| Constant / behaviour | Value used | Status | Basis / what to research |
|---|---|---|---|
| Neutral air dodge → momentum | **set to `(0, 0)`** (halt/hover) | **FOUND (qualitative)** | SmashWiki: Melee air dodge "halts the character's momentum … hovering in place". The *behaviour* (halt) is canon; whether PM leaves a tiny residual vs exact 0 is **GUESS** (we use 0). |
| Directional air dodge → momentum | **set** (replace), not add/preserve | **FOUND (qualitative)** | SmashWiki: "small boost in the chosen direction"; #23 confirms PM = set, not Brawl-preserve. |
| `DODGE_AIR_SPEED` (directional burst magnitude, px/frame) | **14** | **GUESS — blocked on a binary datamine (#215)** | ⚠ The rukaidata × 5.4 path **does not reach this value**: the air-dodge boost magnitude is **engine-hardcoded**, not in the datamined `.pac` subaction script. rukaidata PM3.6 Mario `EscapeAir` (subaction 0x46) lists the animation + intangibility flags + SFX but **no Self-Velocity command** (checked 2026-06-29). SmashWiki/FightCore describe the boost only qualitatively. Candidate from the Melee community-standard air-dodge speed ≈ **3.1 u/f → ×5.4 ≈ 17 px/f**, but **uncorroborated** — do not pin without #215 (a `brawllib_rs`/engine dump or an empirical wavedash-length back-solve). Placeholder stays at ground `DODGE_SPEED = 14`. |
| Helpless / special-fall duration | **until landing** (no timer; `on_ground → idle`) | **FOUND** | SmashWiki: "characters enter a helpless state and fall to the ground" — ends on land. Internal Melee name `landfallspecial`. No fixed-frame guess needed. |
| Air-dodge intangibility window | **full `DODGE_TIME` (14f), `invulnerable=True`** (pycats existing) | **DIVERGENCE (canon confirmed)** | Melee/PM canon **confirmed**: intangible **frames 4–29 of a 49-frame** air dodge — rukaidata PM3.6 Mario `EscapeAir` (`IntangibleFlashing` at frame 3 → `Normal` at 29) + SmashWiki Air dodge + FightCore all agree. pycats keeps its 14-frame full-window invuln as a **conscious divergence** (its own scale); porting the 4–29 sub-window is an open feel decision, not a missing fact. |
| `DODGE_TIME` (air-dodge active duration, frames) | **14** (pycats existing) | **GUESS / divergence** | pycats' own value; Melee's air dodge is ~48–49f. Not changed here. Research: whether the helpless package warrants a longer dodge. |

## Wavedash (landed in #202)

| Constant / behaviour | Value used | Status | Basis / what to research |
|---|---|---|---|
| Wavedash air-dodge angle (`WAVEDASH_ANGLE_DEG`) | **17.1° below horizontal** (optimal) | **FOUND** | SmashWiki Wavedash: "maximum length … with an angle of 17.1[°]". Landed in #202: a diagonal-down air dodge sets the `DODGE_AIR_SPEED` burst at this angle. The *angle* is canon; the *magnitude* still rides on `DODGE_AIR_SPEED` (GUESS row above). |
| Wavedash landing lag (`WAVEDASH_LANDING_LAG`) | **10 frames** | **FOUND (frame value GUESS)** | SmashWiki Wavedash: "for 10 frames afterwards they are unable to attack". Landed in #202. Melee & pycats both run 60 FPS so 10 maps 1:1, but whether 10 is right for pycats' feel is a tuning **GUESS** (#192). |
| Slide distance / traction | governed by **`GROUND_FRICTION = 0.5`** (pycats existing) | **GUESS** | SmashWiki: "low traction → long wavedash", per-character, **no numeric values published**. #202 reuses pycats' single `GROUND_FRICTION` for the waveland slide; per-character traction is a later tuning pass (#192 out-of-scope). |

## How to retire this doc
For each row, replace the GUESS with a researched/playtested value, flip its Status to
a cited FOUND (or "TUNED — playtested <date>"), and tick it on the umbrella ticket.
When every row is resolved, delete this file and close the umbrella.
