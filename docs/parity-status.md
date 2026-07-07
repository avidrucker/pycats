# PM parity status — Axis C parity light

> **Generated file — do not hand-edit.** Regenerate with `python parity_report.py`
> (drift-check: `python parity_report.py --check`). Circles are computed from the
> `pycats/combat/provenance.py` registry (#233): 🟢 FOUND · 🟡 TUNED/GUESS · 🔴 DIVERGENCE.
> Legend: [docs/parity-labeling-legend.md](parity-labeling-legend.md) (#452). Design: #448 (Pass C of #451).

**Summary:** 22 🟢 / 32 🟡 / 4 🔴  (58 constants)

## 🟢 Sourced — FOUND (PM-valid, checked)

| Constant | Value | Status | ○ | Source |
|---|---|---|---|---|
| `CLANK_PRIORITY_RANGE` | 9 | FOUND | 🟢 | SmashWiki:Priority — 9% across the Melee/Brawl/PM family |
| `CROUCH_CANCEL_FACTOR` | 0.67 | FOUND | 🟢 | Melee/PM crouch-cancel knockback scale (0.67x); value cited, still a tuning starting point |
| `DASH_SPEED` | 8 | FOUND | 🟢 | PM Mario dash ~1.5 u/f (config #388 comment; docs/research-120) -> round(1.5 * PX_PER_UNIT) = round(8.1) |
| `DODGE_AIR_SPEED` | 17 | FOUND | 🟢 | doldecomp/melee escapeair_force=3.1u/f; meleelight ESCAPEAIR.js; SmashWiki:Air_dodge |
| `GRAVITY` | 0.5 | FOUND | 🟢 | PM Mario gravity 0.095 u/f^2 (SmashWiki:Mario_(PM); #120) |
| `HITLAG_BASE` | 5 | FOUND | 🟢 | SmashWiki:Hitlag (Brawl onward) — base term |
| `HITLAG_CAP` | 30 | FOUND | 🟢 | SmashWiki:Hitlag — Brawl-onward cap (Melee was 20) |
| `HITLAG_DAMAGE_FACTOR` | 0.3846154 | FOUND | 🟢 | SmashWiki:Hitlag (Brawl onward) — d-term coefficient 1/2.6 |
| `HITSTUN_MULTIPLIER` | 0.4 | FOUND | 🟢 | SmashWiki:Hitstun — 0.4 frames per unit of knockback (Melee; Brawl same; PM = Melee model) |
| `JUMP_VEL` | -13 | FOUND | 🟢 | calibrated to PM Mario full-hop 30.19 u (SmashWiki:Mario_(PM); #120) via height = JUMP_VEL^2/(2*GRAVITY) = 169 px ~= 31 u @ PX_PER_UNIT |
| `LEDGE_INVULN_BASE_FRAMES` | 21 | FOUND | 🟢 | PM 3.6 CliffCatch intangibility 1-21, flat across characters (rukaidata; #671) |
| `MAX_JUMPS` | 2 | FOUND | 🟢 | Mario/PM jump count: 1 ground + 1 midair = 2 (standard 2-jump character; SmashWiki:Mario_(PM)) |
| `MOVE_SPEED` | 6 | FOUND | 🟢 | PM Mario walk 1.1 u/f (SmashWiki:Mario_(PM); #120) |
| `PX_PER_UNIT` | 5.4 | FOUND | 🟢 | data-authoring units->px calibration ~=5.4 (docs/research-120-smash-units-and-sources.md; #120/#195); the base every spatial derivation in this registry references |
| `SAKURAI_ANGLE_CODE` | 361 | FOUND | 🟢 | SmashWiki:Sakurai_angle — the 361 sentinel (not a literal degree) |
| `SHIELDSTUN_FACTOR` | 0.345 | FOUND | 🟢 | SmashWiki:Shieldstun — Brawl/PM factor 0.345 |
| `SHIELD_BREAK_STUN_MAX` | 490 | FOUND | 🟢 | Melee/PM shield-break stun = (400 - percent) + 90; max at 0% |
| `SHIELD_BREAK_STUN_MIN` | 90 | FOUND | 🟢 | Melee/PM shield-break stun = (400 - percent) + 90; min at >=400% |
| `SMASH_CHARGE_FRAMES` | 59 | FOUND | 🟢 | PM smash charge ramp = 59 frames. ⚠ primary-unconfirmed: single secondary (SmashWiki:Project_M "59 frames as opposed to 60"), contradicted by SmashWiki:Smash_attack (60, all games); cap is engine-hardcoded so brawllib_rs has none — a PM DOL/RAM dump is the only primary (see #626). Supersedes the base-game 60 #581 registered. |
| `SMASH_CHARGE_SCALE` | 1.3671 | FOUND | 🟢 | PM full-charge damage multiplier = 1.3671, Melee value restored in PM. [primary] meleelight (Melee reimpl, clone #616) hardcodes 1 + chargeFrames*(0.3671/60) → 1.3671 at cap; [secondary] SmashWiki:Project_M "deals x1.3671". Supersedes #581 Brawl-era 1.4. |
| `WAVEDASH_ANGLE_DEG` | 17.1 | FOUND | 🟢 | SmashWiki:Wavedash — optimal angle 17.1 deg below horizontal (Melee/PM) |
| `WAVEDASH_LANDING_LAG` | 10 | FOUND | 🟢 | SmashWiki:Wavedash — Melee/PM landing lag ~10 frames (60 FPS maps 1:1) |

## 🟡 Inferred — TUNED / GUESS (good-enough / unsourced)

| Constant | Value | Status | ○ | Source |
|---|---|---|---|---|
| `AIR_FRICTION` | 0.85 | TUNED | 🟡 | pycats air friction; deliberate design knob, no PM equivalent |
| `BLAST_PADDING` | 50 | TUNED | 🟡 | pycats KO boundary = px beyond the screen edge; pycats stage rule, no canon |
| `DASH_DURATION` | 12 | GUESS | 🟡 | pycats initial-dash burst window; GUESS tuning start (config ⚠, #388), no canon single value |
| `DODGE_FRAMES` | 15 | GUESS | 🟡 | roll intangibility window; playtest starting point (tracked #65) |
| `DODGE_SPEED` | 14 | TUNED | 🟡 | pycats ground-roll horizontal boost; Melee rolls are animation-driven per-character, no single canon speed to derive |
| `DODGE_TIME` | 14 | GUESS | 🟡 | roll duration; playtest starting point (tracked #65) |
| `FSMASH_ANGLE_DOWN` | 330 | GUESS | 🟡 | pycats angled-fsmash down-forward launch angle (-30deg); GUESS (config ⚠ playtest, #327) |
| `FSMASH_ANGLE_UP` | 50 | GUESS | 🟡 | pycats angled-fsmash up-forward launch angle; GUESS (config ⚠ playtest, #327), no canon value |
| `GETUP_ROLL_SPEED` | 12.0 | TUNED | 🟡 | pycats getup-roll horizontal speed (decays under friction); no canon single value (animation-driven) |
| `GROUND_FRICTION` | 0.5 | TUNED | 🟡 | pycats ground friction (1.0=ice, 0.0=instant stop); deliberate design knob, no PM equivalent |
| `HITSTUN_FLOOR` | 1 | TUNED | 🟡 | pycats floor: >=1 frame for any clean hit; SmashWiki:Hitstun documents no canon minimum |
| `HURT_TIME` | 12 | TUNED | 🟡 | pycats hurt/flinch timer; deliberate design value, no PM canon equivalent |
| `INITIAL_LIVES` | 3 | TUNED | 🟡 | pycats default stock count; a match ruleset setting, not a PM physics value |
| `JOSTLE_MIN_VOVERLAP_FRAC` | 0.8 | TUNED | 🟡 | deliberate vertical-overlap gate for the PM X-only push heuristic |
| `KNOCKDOWN_PRONE_FRAMES` | 30 | TUNED | 🟡 | pycats fixed getup window (~0.5s @60 FPS); Melee knockdown/getup is variable + per-character, no single canon value (SmashWiki:Floor_getup) |
| `KNOCKDOWN_VY_THRESHOLD` | 8.0 | TUNED | 🟡 | pycats auto-knockdown impact-speed gate (#145); pycats-specific mechanic, no canon equivalent |
| `LEDGE_CATCH_H` | 64 | TUNED | 🟡 | pycats ledge-grab catch-region height below the lip; pycats geometry, no canon |
| `LEDGE_CATCH_W` | 24 | TUNED | 🟡 | pycats ledge-grab catch-region width off the edge corner; pycats geometry, no canon |
| `LEDGE_GETUP_FRAMES` | 16 | TUNED | 🟡 | pycats neutral ledge-getup climb window (edge frees at half); PM getup frames are per-character |
| `LEDGE_REGRAB_LOCKOUT_FRAMES` | 30 | TUNED | 🟡 | pycats post-release regrab-suppression window; pycats ledge rule (#14), no canon single value |
| `PLAYER_ATTACK_DURATION` | 12 | TUNED | 🟡 | pycats default attack duration; deliberate design value, no PM canon |
| `PLAYER_SIZE` | (40, 60) | TUNED | 🟡 | pycats default fighter collision box (Fighter.__init__ reads stand_size or PLAYER_SIZE); reclassified render->collision per #584, no PM-mapped dimension |
| `PROJECTILE_GRAVITY` | 0.5 | GUESS | 🟡 | pycats projectile fall accel; GUESS tuning start (config ⚠, #266/#425), no PM source |
| `PROJECTILE_MAX_BOUNCES` | 3 | GUESS | 🟡 | pycats projectile bounces before despawn; GUESS (config ⚠, #266/#425) |
| `PROJECTILE_RESTITUTION` | 0.6 | GUESS | 🟡 | pycats projectile bounce energy kept (<1); GUESS tuning start (config ⚠, #266/#425) |
| `RESPAWN_DELAY_FRAMES` | 120 | TUNED | 🟡 | pycats respawn freeze ~2s (config computes int(2*FPS)); ruleset value, no canon |
| `SAKURAI_AIRBORNE_DEG` | 40.0 | TUNED | 🟡 | pycats airborne launch angle; keyed to pycats knockback() magnitude, not Smash units — no canon value |
| `SAKURAI_GROUNDED_HIGH_KB` | 88.0 | TUNED | 🟡 | pycats threshold — grounded angle reaches max at this pycats KB magnitude; no canon value |
| `SAKURAI_GROUNDED_LOW_KB` | 60.0 | TUNED | 🟡 | pycats threshold — grounded angle stays flat below this pycats KB magnitude; no canon value |
| `SAKURAI_GROUNDED_MAX_DEG` | 40.0 | TUNED | 🟡 | pycats grounded max angle at HIGH_KB; keyed to pycats knockback() magnitude, not Smash units — no canon value |
| `SHIELD_DRAIN_PER_FRAME` | 0.2 | TUNED | 🟡 | pycats shield-HP model; deliberate drain/regain rate, no canon equivalent |
| `SHIELD_MAX_HP` | 50 | TUNED | 🟡 | pycats shield-HP model; no verified 1:1 canon value (Melee uses a different shield-health/decay model) |

## 🔴 Divergence — intentional departure from canon

| Constant | Value | Status | ○ | Source |
|---|---|---|---|---|
| `GETUP_ROLL_FRAMES` | 16 | DIVERGENCE | 🔴 | pycats getup-roll duration = its intangibility window; DIVERGENCE from Melee (getup roll 35f, intangible frames 1-14..1-24 per Smashboards frame data) — pycats runs a shorter roll on its own scale |
| `KNOCKBACK_DECAY` | 0.145 | DIVERGENCE | 🔴 | DIVERGENCE from Smash decay 0.051/frame (#43): deliberately scaled to the 960px stage, preserving the 1.7 decay/launch ratio |
| `KNOCKBACK_LAUNCH_FACTOR` | 0.085 | DIVERGENCE | 🔴 | DIVERGENCE from Smash launch_speed = KB*0.03 (docs/research/knockback-launch-physics-findings.md, #43): deliberately scaled to the 960px stage |
| `MAX_FALL_SPEED` | 13 | DIVERGENCE | 🔴 | DIVERGENCE: pycats uses a single global fall speed ~= PM Mario fast-fall 2.3 u/f; the Melee/PM base 1.7 / fast-fall 2.3 split is not modelled (SmashWiki:Mario_(PM); #120) |
