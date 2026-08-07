"""Combat / physics tuning scalars — gravity, movement, dodges, ledges, shield,
knockback / hitstun / hitlag, and the px<->unit authoring scale. Self-contained
(no sibling-submodule imports).

#### TODO: implement unique attacks for each player
#### TODO: implement attack cooldowns
#### TODO: implement attack dodging
#### TODO: implement character selection that offers heavy, medium, & light-weight
# choices where heavy characters do more damage but are slower, and lighter
# characters are faster but deal less damage
#### TODO: implement attack combos that can be chained together for more damage
"""

# ── Combat/physics tuning provenance ─────────────────────────────────────────
# Structured, machine-enforced provenance (value / unit / source / status / issue
# / derivation) for the combat-physics tuning SCALARS below lives in
# `pycats/combat/provenance.py` (ADR-0003 / #233) — that registry is the source of
# truth the drift-guard checks. Changing a value here must update its Provenance
# row in the same diff or `tests/test_tuning_provenance.py` reds. The inline
# comments below stay as human-readable narrative; deep sourcing write-ups live in
# docs/research/*. (Render/UI/tail/platform/menu constants are out of scope.)

# NOTE (#785): these velocity/physics defaults are GAME-TUNED px, not faithful
# rukaidata × PX_PER_UNIT — e.g. MAX_FALL_SPEED 13 is well above Mario's real term
# vel (1.7 × 5.4 ≈ 9.2). New per-fighter *faithful* velocity data is authored raw-first
# through `combat.units.vel(units)` (e.g. `move_speed=vel(1.2)`); these globals stay as
# the tuned baseline. Sourcing true raw for the shipped cats + any re-tune is a separate
# design pass. (config can't call vel() itself — units.py imports PX_PER_UNIT from here.)
GRAVITY = 0.5
MAX_FALL_SPEED = 13
# Projectile physics defaults (#266, #425). ⚠ GUESS tuning starting points — no
# measured PM values (see docs/research/2026-06-30-nalio-fireball-*.md). Per-move
# overridable via projectile_gravity/_restitution/_max_bounces; these are the
# shared fallbacks used by Projectile.__init__ and the Player spawn path.
PROJECTILE_GRAVITY = 0.5  # px/frame² downward accel
PROJECTILE_RESTITUTION = 0.6  # vertical energy kept per bounce (<1)
PROJECTILE_MAX_BOUNCES = 3  # bounces before despawn
# Walk / dash / run are per-character raw PM units in <cat>.json (#1209, ADR-0011);
# the MOVE_SPEED / DASH_SPEED globals were removed — a cat's speeds live on
# FighterData.walk/dash/run, with the shipped px derived at read via
# combat.units.u(). DASH_DURATION stays global: the initial-dash burst WINDOW in
# frames (⚠ tuning start; the sustained run state after the burst is #967) — a
# frame count, not a speed.
DASH_DURATION = 12
# Double-tap dash window (#388 slice 2b, #403): frames after a fresh directional
# press during which a second same-direction press counts as a double-tap and
# fires the dash burst. A HELD key is `pressed` only on its down-frame, so holding
# never double-taps → walk stays golden-safe. (⚠ tuning start, ~8–10 frames.)
DOUBLE_TAP_WINDOW = 8
JUMP_VEL = -13
DODGE_FRAMES = 15
MAX_JUMPS = 2  # single + double

# ---------------- physics constants --------------
GROUND_FRICTION = 0.5  # 1.0 = ice; 0.0 = instant stop
AIR_FRICTION = 0.85
# Horizontal-velocity dead-zone (#446/#1135): after friction multiplies vel.x, a
# magnitude below this snaps to 0 so a fighter fully stops instead of creeping at a
# sub-pixel speed forever. Third member of the friction model with GROUND/AIR_FRICTION
# (all three read by core.physics.apply_horizontal_friction); relocated here from
# core/physics.py so the provenance drift-guard (ADR-0003) covers it too — #1135.
# TUNED: a pycats implementation threshold, no PM canon.
VEL_DEADZONE = 0.05
# Dodge-off-ledge safety margin (#1135): a ground roll/dodge is cancelled if it would
# leave fewer than this many px of the fighter's body overlapping its platform, so a
# dodge can't walk a fighter clean off the edge. Relocated from a would_dodge_off_platform
# function local in core/physics.py for the same drift-guard coverage. TUNED: pycats
# edge-safety rule, no PM canon.
DODGE_MIN_PLATFORM_OVERLAP_PX = 25

# Fighter-vs-fighter "jostle" (Project M ground push, #1/#1020, ADR-0012). A literal
# port of meleelight's grounded jostle (schmooblidon/meleelight @ 27af171,
# src/physics/physics.js). Authored raw-first in Smash *units*; the pixel trigger /
# push derive at the seam via combat.units.u() in core/physics.py (ADR-0011 — no bare
# × PX_PER_UNIT here). Both are FOUND from meleelight, a SECONDARY reimplementation
# proxy; the exact retail Melee/Brawl/PM 3.6 magnitude is ⚠ UNDOCUMENTED (the push is
# an engine global, not per-move script data). See pycats/combat/provenance.py.
JOSTLE_TRIGGER_UNITS = 6.5  # centre-distance below which the push fires (meleelight `diff < 6.5`)
JOSTLE_PUSH_UNITS = 0.3  # per-fighter position nudge each overlap frame (meleelight `pos.x += ±0.3`)

# Timers (frames)
HURT_TIME = 12
# Shield-break "dizzy" stun (#12). Melee/PM: duration = (400 - p) + 90 frames,
# i.e. SHIELD_BREAK_STUN_MAX - percent, clamped to [MIN, MAX]. Higher damage =>
# SHORTER stun (inverse of every other stun). See combat.shield and
# docs/research/brawl-projectm-fighter-states.md.
SHIELD_BREAK_STUN_MAX = 490  # frames at 0% damage
SHIELD_BREAK_STUN_MIN = 90  # frames at >= 400% damage
# Shieldstun (#140): a blocked hit locks the defender in shield for
# floor(damage * SHIELDSTUN_FACTOR) frames. SmashWiki Shieldstun / the project
# roadmap (pm-mechanics-implementation-analysis.md): Brawl/PM factor 0.345.
# Attacks under ~2.9% give 0 frames (the floor yields that naturally).
SHIELDSTUN_FACTOR = 0.345
DODGE_TIME = 14
DODGE_SPEED = 14  # horizontal boost for a roll
# Smash charge (#327 slice 3a): frames of holding the smash input to reach full
# charge (fraction 0 -> 1). PM: 59 frames (SmashWiki:Project_M — "chargable for 59
# frames as opposed to 60"; supersedes the base-game 60 #581 registered, #599/#595).
SMASH_CHARGE_FRAMES = 59
# Smash charge (#327 slice 3b): full-charge output multiplier. A charged hit's
# damage scales by 1 + c*(SMASH_CHARGE_SCALE - 1) for charge fraction c (c=0 ->
# authored, c=1 -> base x SCALE); knockback rises through the formula, BKB/KBG are
# NOT scaled (#437/#423/#426). PM restored Melee's 1.3671 (not Brawl's 1.4;
# SmashWiki:Project_M; supersedes #581's Brawl value, #599/#595).
SMASH_CHARGE_SCALE = 1.3671
# Angleable f-smash (#327 slice 4): a forward smash held with up/down aims the swing.
# The angled variant REPLACES the fsmash hitboxes' launch angle with these literals
# (facing-right-relative degrees: 0=forward, 90=up, 270=down). ⚠ playtest.
FSMASH_ANGLE_UP = 50  # up-forward (anti-air / juggle)
FSMASH_ANGLE_DOWN = 330  # down-forward = -30° (edgeguard poke)
# Data-authoring scale (#195, operationalizes #120): pycats authors combat data in
# raw Smash *units* and scales SPATIAL values (hitbox radii/offsets) to pixels by this
# factor. Named here so the px↔unit boundary is single-sourced + greppable, and so the
# ADR-0003 derivation-guard (#233) can re-evaluate `round(units * PX_PER_UNIT)` against
# config. The SIM stays integer-pixel (a determinism asset, #80) — this only names the
# authoring-time scale already in de-facto use. Author new spatial data via
# `pycats.combat.units.u(units)`. Calibration ≈5.4 is documented in
# docs/research-120-smash-units-and-sources.md.
PX_PER_UNIT = 5.4
# PM-faithful (Melee-style) air dodge directional burst (#184). The air dodge
# *sets* (replaces) velocity to this magnitude in the stick direction, unlike the
# ground roll which the sim reads separately. FOUND (#215): Melee's hardcoded
# air-dodge speed `escapeair_force` = 3.1 units/frame — corroborated by the
# meleelight reimplementation (ESCAPEAIR.js: `3.1 * cos(ang)`) and the doldecomp
# /melee model (`escapeair_force × (cosθ,sinθ)`); PM restored Melee's air dodge.
# px/frame = round(3.1 × PX_PER_UNIT) = 17 (kept a bare literal per ADR-0003 C1).
DODGE_AIR_SPEED = 17
# Wavedash (#202, follow-up to #184): a *diagonal-down* air dodge sets the
# DODGE_AIR_SPEED burst at an angle below horizontal so it drives into the ground
# and cancels into a grounded slide (the waveland). FOUND — SmashWiki gives the
# optimal wavedash angle as 17.1° below horizontal (Melee/PM).
WAVEDASH_ANGLE_DEG = 17.1
# Landing lag after a waveland — frames locked out of action once the air dodge
# touches the ground (the slide still decays under GROUND_FRICTION during it).
# FOUND — Melee/PM wavedash landing lag is ~10 frames; pycats runs at 60 FPS like
# Melee so the frame count maps 1:1, but it stays a tuning starting point (#192).
WAVEDASH_LANDING_LAG = 10

# Ledge-hang (#14). ⚠ playtest starting points (no published PM px values; pycats
# scale). The catch region is a box hanging off a solid-stage corner.
LEDGE_CATCH_W = 24  # px outward from the edge corner the catch box spans
LEDGE_CATCH_H = 64  # px downward from the lip the catch box spans
# No ledge-hang timeout (#475): PM/Melee impose none — you hang until you act, only
# the intangibility burst (ledge_intangible_frames) expires over time. The old 120f
# auto-release was an unfaithful pycats invention that dropped a hanger off-stage.
LEDGE_REGRAB_LOCKOUT_FRAMES = 30  # post-release frames grab is suppressed
# True PM edge-hog (#311, grounded by #297): the ledge-grab intangibility is a
# fixed per-grab burst — #543 dropped the old percent-scaling (a #311 divergence,
# #536) for PM's flat window. A hog succeeds once the occupant's burst lapses. The
# 21f value is PM 3.6's CliffCatch intangibility (fully intangible frames 1-21, flat
# across every character checked; rukaidata, #671). Registered with #233.
LEDGE_INTANGIBLE_BASE_FRAMES = 21  # ledge-grab intangibility burst (PM 3.6 CliffCatch 1-21; #683)
# PM's 5-regrab ledge-intangibility count cutoff (#656, ratified #670). PMDT 3.5:
# "After a character regrabs the ledge five times without touching the ground, that
# character no longer receives intangibility for grabbing the ledge again (except
# for a few frames during the initial ledge snap) until he or she either lands on the
# stage or gets hit." The count (5) is primary-sourced; the post-cutoff residual is NOT.
LEDGE_REGRAB_INTANGIBLE_CUTOFF = 5  # grabs 1..5 grant the full burst; grab 6+ grant only the residual
LEDGE_POST_CUTOFF_RESIDUAL_FRAMES = 5  # PLACEHOLDER_VALUE_PLS_RESEARCH_ACTUAL
# ^ No grounded basis: PM primary says only "a few frames" (qualitative, no number).
# Needs a datamined engine/DOL dump of the ledge-snap intangibility window — NOT an
# inference from the dev blog, and NOT #671's estimated 3-7f range. Deliberately carries
# NO Provenance entry (it is an acknowledged gap, not a FOUND/TUNED value) — #656.
# Neutral ledge-getup climb window (#311): getup is no longer instant — the fighter
# climbs for this many frames; the edge frees to others at ~half (half-animation
# regrab), and the climber snaps onto the stage when it closes. ⚠ playtest.
LEDGE_GETUP_FRAMES = 16

# ---------------- combat / attacks ----------------
# this can be different than the lifetime of an attack, for example, a fireball could
# take 6 frames to fire, and then the lifetime of the fireball could be as long as 120 frames
PLAYER_ATTACK_DURATION = 12
ATTACK_SIZE = (30, 18)  # width, height — render-only: sizes the drawn hit-box rect.
# NOTE (#584/#598): not render-ONLY — its width doubles as the projectile despawn
# bound (the off-stage check in Attack.update). Excluded from the provenance registry
# (a render constant), but the gameplay coupling is real; kept as a comment, not a row.
# Per-move damage/lifetime/knockback now live in the move data (MoveData/Hitbox,
# see characters/default_cat.py); the old global ATTACK_LIFETIME / HIT_DAMAGE
# fallbacks were retired in #70.

# ---------------- shield / bubble ---------------
SHIELD_MAX_HP = 50  # fresh shield bubble hit points
# HP lost per frame while the shield is held (and regained per frame when not).
# Keep in sync with the literal in player.py's shield tick. Used to estimate the
# shield count-down seconds for the status timer bar (#111).
SHIELD_DRAIN_PER_FRAME = 0.2
MAX_SHIELD_RADIUS = 40
MIN_SHIELD_RADIUS = 10

# ---------------- status-effect timer bars (#111) ----------------
# A count-down bar above a fighter showing how long a status effect (shield, stun)
# has left — a deliberate divergence from Project M. The ON/OFF toggle moved from a
# constant here into persisted prefs (#121): default lives in settings.py
# (`show_status_timer_bars`), the live value the render path reads is in
# runtime_settings, and the main-menu Options sub-menu flips it.

# ---------------- knockback / hitstun ----------------
# Authentic Brawl/PM knockback feeds these. The formula lives in
# pycats/combat/knockback.py; per-hitbox BKB/KBG and fighter weight are the
# per-move/character inputs.
# Knockback-formula coefficients (#39 §2 / #1135). The Brawl/PM knockback equation
# (SmashWiki:Knockback), with p = post-hit percent, d = damage, w = weight:
#   KB = (((((p/10) + (p*d/20)) * (200/(w+100)) * 1.4) + 18) * (KBG/100)) + BKB
# Every literal below is a FIXED term of that canonical formula (FOUND) — named so
# knockback.py reads as the equation and the ADR-0003 drift-guard covers each. These
# are NOT tuning knobs: changing one departs from Smash canon. (BKB/KBG/weight are the
# per-move/character inputs, not coefficients.) KB_WEIGHT_OFFSET and KB_KBG_DIVISOR are
# both 100 but mean different things (the w+100 weight offset vs the KBG% → factor
# divisor), so they are named apart.
KB_PERCENT_DIVISOR = 10.0  # p/10 term
KB_PERCENT_DAMAGE_DIVISOR = 20.0  # p*d/20 term
KB_WEIGHT_NUMERATOR = 200.0  # 200/(w+100) weight-ratio numerator
KB_WEIGHT_OFFSET = 100.0  # w+100 weight offset
KB_GROWTH_SCALE = 1.4  # ×1.4 growth scale
KB_GROWTH_BASE = 18.0  # +18 base term
KB_KBG_DIVISOR = 100.0  # KBG/100 (knockback-growth percent → factor)
HITSTUN_MULTIPLIER = 0.4  # hitstun_frames = floor(KB * this). ⚠🔬 verify (Brawl/PM ~0.4).
HITSTUN_FLOOR = 1  # minimum hitstun frames for any clean hit. ⚠🔬 tuning, not sourced.
# Hitlag / freeze frames (#138). SmashWiki Hitlag (Brawl onward):
# floor((d * HITLAG_DAMAGE_FACTOR + HITLAG_BASE) * h * e) * c, capped at HITLAG_CAP.
# This slice uses h = e = c = 1 (per-move/electric/crouch-cancel multipliers are
# deferred). Both attacker and defender freeze for this many frames on a clean
# hit, then the knockback slide proceeds.
HITLAG_DAMAGE_FACTOR = 0.3846154
HITLAG_BASE = 5
HITLAG_CAP = 30  # Brawl-onward cap (Melee was 20).
# Victim-only hitlag cap when crouch-cancelling (#1230, C-slice of #1228). SmashWiki
# Hitlag: "30 frames (20 for the victim if crouch cancelling) from Brawl onward". The
# attacker keeps HITLAG_CAP (30); only the crouch-cancelling victim's freeze is capped
# here. See docs/research/2026-08-04-full-hitlag-model-findings.md (the cap table).
HITLAG_VICTIM_CROUCH_CAP = 20
# Knockback decay model (#44, from #43 research). A hit sets an initial launch
# velocity of KB * KNOCKBACK_LAUNCH_FACTOR (px/frame), which then bleeds off by
# KNOCKBACK_DECAY (px/frame) every frame during hitstun — mirroring Smash's
# launch_speed = KB*0.03 / decay 0.051/frame, scaled to pycats' 960px stage while
# preserving the 1.7 decay/launch ratio. ⚠ tuning — playtest and adjust.
KNOCKBACK_LAUNCH_FACTOR = 0.085
KNOCKBACK_DECAY = 0.145
# Sakurai angle (#203, a #142 gate). The angle id 361 is a SENTINEL, not a literal
# degree (SmashWiki "Sakurai angle"). Resolved in Fighter.receive_hit via
# knockback.sakurai_angle(kb, on_ground):
#   - airborne victim  -> SAKURAI_AIRBORNE_DEG (fixed), regardless of KB;
#   - grounded victim   -> 0° below LOW_KB, scaling LINEARLY up to
#     SAKURAI_GROUNDED_MAX_DEG at HIGH_KB (weak grounded hits stay flat so they
#     don't pop a grounded opponent straight up).
# Angles/thresholds are Brawl/PM-derived ⚠ playtest starting points (KB here is
# the pycats knockback() magnitude, not raw Smash units), tunable like the
# crouch/prone numbers.
SAKURAI_ANGLE_CODE = 361
SAKURAI_AIRBORNE_DEG = 40.0
SAKURAI_GROUNDED_MAX_DEG = 40.0
SAKURAI_GROUNDED_LOW_KB = 60.0
SAKURAI_GROUNDED_HIGH_KB = 88.0
# Crouch-cancel (#135). A hit taken while in the `crouch` state (#124) has its
# knockback magnitude scaled by this factor before launch + hitstun are derived
# — Melee/PM's signature defensive use of crouch. 0.67x is the Melee/PM value;
# ⚠ tuning starting point. This same 0.67 factor is the hitlag "c" multiplier: as
# of #1230 it also scales the crouch-cancelling VICTIM's hitlag (attacker unchanged),
# floored + capped at HITLAG_VICTIM_CROUCH_CAP in knockback.hitlag_frames. A single
# global factor for v1; per-character/game tweaks can move it into FighterData later.
CROUCH_CANCEL_FACTOR = 0.67
# Auto landing-velocity knockdown (#145). A fighter that lands while still in
# hitstun (tumble) and hits the ground at/above KNOCKDOWN_VY_THRESHOLD downward
# px/frame is knocked down — forced into `prone` (#13) for KNOCKDOWN_PRONE_FRAMES
# getup frames. The hitstun gate is the real discriminator (normal jumps land at
# the same MAX_FALL_SPEED but with hurt_timer == 0); the velocity threshold filters
# out gentle pops. Teching (a tech input window that cancels the knockdown) is out
# of scope — #146 sibling. ⚠🔬 tuning starting points, not sourced — playtest.
KNOCKDOWN_VY_THRESHOLD = 8.0  # downward impact speed (px/frame); MAX_FALL_SPEED is 13
KNOCKDOWN_PRONE_FRAMES = 30  # getup window the auto-knockdown sets (~0.5s @ 60 FPS)
# Getup-roll (#146): a directional getup out of `prone` — holding left/right as the
# getup window ends rolls that way with intangibility, instead of a neutral stand.
# The roll lasts GETUP_ROLL_FRAMES (= its intangibility window) and sets an initial
# horizontal GETUP_ROLL_SPEED that decays under friction. ⚠ playtest starting
# points (per PM feel; like the dodge/crouch/prone numbers).
GETUP_ROLL_FRAMES = 16
GETUP_ROLL_SPEED = 12.0

# Clank / priority (#38 4c). When two opposing GROUND hitboxes overlap, the Smash
# "priority range" decides the outcome: if their damage differs by <= this many
# percent, both attacks end (clank); otherwise the stronger continues and the
# weaker ends. SmashWiki "Priority": 9% across the Melee/Brawl/PM family.
CLANK_PRIORITY_RANGE = 9
