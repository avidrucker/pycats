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
plus the prior research `docs/research/air-dodge-vertical-momentum-findings.md` (#23).

## Air dodge core (#184 this slice)

| Constant / behaviour | Value used | Status | Basis / what to research |
|---|---|---|---|
| Neutral air dodge → momentum | **set to `(0, 0)`** (halt/hover) | **FOUND (qualitative)** | SmashWiki: Melee air dodge "halts the character's momentum … hovering in place". The *behaviour* (halt) is canon; whether PM leaves a tiny residual vs exact 0 is **GUESS** (we use 0). |
| Directional air dodge → momentum | **set** (replace), not add/preserve | **FOUND (qualitative)** | SmashWiki: "small boost in the chosen direction"; #23 confirms PM = set, not Brawl-preserve. |
| `DODGE_AIR_SPEED` (directional burst magnitude, px/frame) | **14** | **GUESS** | No PM/Melee value exists in px/frame. Reusing pycats' ground `DODGE_SPEED = 14` as a consistent starting point. Research: tune by feel vs PM video; likely wants to relate to `JUMP_VEL`(13)/`move_speed`. |
| Helpless / special-fall duration | **until landing** (no timer; `on_ground → idle`) | **FOUND** | SmashWiki: "characters enter a helpless state and fall to the ground" — ends on land. Internal Melee name `landfallspecial`. No fixed-frame guess needed. |
| Air-dodge intangibility window | **full `DODGE_TIME` (14f), `invulnerable=True`** (pycats existing) | **GUESS / divergence** | Melee canon is intangible **frames 4–29 of a ~48–49f** animation (Mario 48; Mewtwo 39). pycats already uses a 14-frame full-window invuln (its own choice); we keep that rather than port Melee's start-up/late frames. Research: decide whether to model the 4–29 sub-window. |
| `DODGE_TIME` (air-dodge active duration, frames) | **14** (pycats existing) | **GUESS / divergence** | pycats' own value; Melee's air dodge is ~48–49f. Not changed here. Research: whether the helpless package warrants a longer dodge. |

## Wavedash (deferred to follow-up #184b — listed here so it's tracked)

| Constant / behaviour | Value used | Status | Basis / what to research |
|---|---|---|---|
| Wavedash air-dodge angle | **~17.1° below horizontal** (optimal) | **FOUND** | SmashWiki Wavedash: "maximum length … with an angle of 17.1[°]". Needs `dir_y` (down) input plumbing — not in this slice. |
| Wavedash landing lag | **10 frames** | **FOUND** | SmashWiki Wavedash: "for 10 frames afterwards they are unable to attack". Maps ~directly to pycats frames; **GUESS** that 10 is right for pycats' feel. |
| Slide distance / traction | governed by **`GROUND_FRICTION = 0.5`** (pycats existing) | **GUESS** | SmashWiki: "low traction → long wavedash", per-character, **no numeric values published**. Reuse pycats' single `GROUND_FRICTION`; per-character traction is a later tuning pass (#184 out-of-scope). |

## How to retire this doc
For each row, replace the GUESS with a researched/playtested value, flip its Status to
a cited FOUND (or "TUNED — playtested <date>"), and tick it on the umbrella ticket.
When every row is resolved, delete this file and close the umbrella.
