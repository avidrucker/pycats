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
in `docs/research/pm-air-dodge-values-sourcing.md` (#192/#216). The engine-level model + the
magnitude were pinned from the **Melee decompilation** ([doldecomp/melee `ftCo_EscapeAir.c`](https://github.com/doldecomp/melee/blob/master/src/melee/ft/chara/ftCommon/ftCo_EscapeAir.c))
and the **meleelight** reimplementation ([`ESCAPEAIR.js`](https://github.com/schmooblidon/meleelight/blob/master/src/characters/shared/moves/ESCAPEAIR.js)),
cross-checked against PlCo.dat common-data values (Magus *SSBM Data Sheet*) — see #215.

## Air dodge core (#184 this slice)

| Constant / behaviour | Value used | Status | Basis / what to research |
|---|---|---|---|
| Neutral air dodge → momentum | **set to `(0, 0)`** (halt/hover) | **FOUND (primary)** | Melee decomp `ftCo_EscapeAir.c` (#215): stick within `escapeair_deadzone` → `self_vel.x = self_vel.y = 0`. pycats matches exactly. |
| Directional air dodge → momentum | **set** (replace), not add/preserve | **FOUND (primary)** | Melee decomp `ftCo_EscapeAir.c` (#215): `self_vel = escapeair_force × (cosθ, sinθ)` in the stick direction — a SET, not Brawl-preserve/add. pycats matches. |
| `DODGE_AIR_SPEED` (directional burst magnitude, px/frame) | **17** | **FOUND (#215)** | Melee `escapeair_force` = **3.1 units/frame** (single global in PlCo.dat common data), corroborated 3 ways: meleelight `ESCAPEAIR.js` literal `3.1 * cos(ang)`; the doldecomp/melee model `escapeair_force × (cosθ,sinθ)`; a ~2.79 max-angle wavedash back-solve. PM restored Melee's air dodge (#23/#184). Derivation: `round(3.1 × PX_PER_UNIT≈5.4) = 17`. Pinned in #222 (was the feel-tuned 14). |
| Helpless / special-fall duration | **until landing** (no timer; `on_ground → idle`) | **FOUND** | SmashWiki: "characters enter a helpless state and fall to the ground" — ends on land. Internal Melee name `landfallspecial`. No fixed-frame guess needed. |
| Air-dodge intangibility window | **full `DODGE_TIME` (14f), `intangible=True`** (pycats existing) | **DIVERGENCE (canon confirmed)** | Melee/PM canon **confirmed**: intangible **frames 4–29 of a 49-frame** air dodge — rukaidata PM3.6 Mario `EscapeAir` (`IntangibleFlashing` at frame 3 → `Normal` at 29) + SmashWiki Air dodge + FightCore all agree. pycats keeps its 14-frame full-window intangibility as a **conscious divergence** (its own scale); porting the 4–29 sub-window is an open feel decision, not a missing fact. |
| `DODGE_TIME` (air-dodge active duration, frames) | **14** (pycats existing) | **GUESS / divergence** | pycats' own value; Melee's air dodge is ~48–49f. Not changed here. Research: whether the helpless package warrants a longer dodge. |
| In-dodge per-frame velocity decay (`escapeair_decay`) | **not modelled** (pycats holds vel, then zeroes at dodge end) | **DIVERGENCE (canon confirmed)** | Melee decomp `ftCo_EscapeAir.c` (#215) multiplies `self_vel` by `escapeair_decay` **every frame** during the dodge: **×0.95** (PlCo.dat 0xA170) / ×0.9 (meleelight rounds). pycats does not decay mid-dodge — a documented divergence; whether to model it is a feel decision (**#218**). |

## Wavedash (landed in #202)

| Constant / behaviour | Value used | Status | Basis / what to research |
|---|---|---|---|
| Wavedash air-dodge angle (`WAVEDASH_ANGLE_DEG`) | **17.1° below horizontal** (optimal) | **FOUND** | SmashWiki Wavedash: "maximum length … with an angle of 17.1[°]". Landed in #202: a diagonal-down air dodge sets the `DODGE_AIR_SPEED` burst at this angle. Now that the magnitude is pinned (17), the burst is fully PM-faithful. |
| Wavedash landing lag (`WAVEDASH_LANDING_LAG`) | **10 frames** | **FOUND (primary)** | Confirmed in PlCo.dat: "Airdodge(wavedash) landing lag" = **10** (offset 0xA324, via the Magus SSBM Data Sheet; #215), corroborated by SmashWiki/dragdown. Melee & pycats both run 60 FPS → 1:1; landed in #202. No longer a guess. |
| Slide distance / traction | governed by **`GROUND_FRICTION = 0.5`** (pycats existing) | **GUESS** | SmashWiki: "low traction → long wavedash", per-character, **no numeric values published**. #202 reuses pycats' single `GROUND_FRICTION` for the waveland slide; per-character traction is a later tuning pass (#192 out-of-scope). |

## How to retire this doc
For each row, replace the GUESS with a researched/playtested value, flip its Status to
a cited FOUND (or "TUNED — playtested <date>"), and tick it on the umbrella ticket.
When every row is resolved, delete this file and close the umbrella.
