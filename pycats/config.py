"""
Purpose: Central configuration module.

Contents:
- Screen dimensions (SCREEN_WIDTH, SCREEN_HEIGHT), framerate (FPS)
- Physics constants (gravity, fall speed, movement speed)
- Player action constants (jump velocity, dodge frames, max jumps)
- UI constants (attack hit-box size and lifetime, eye offset, shield color)

Use: Shared constants across modules for tuning gameplay and UI.
"""

#### TODO: implement unique attacks for each player
#### TODO: implement attack cooldowns
#### TODO: implement attack dodging
#### TODO: implement character selection that offers heavy, medium, & light-weight choices where heavy characters do more damage but are slower, and lighter characters are faster but deal less damage
#### TODO: implement attack combos that can be chained together for more damage

SCREEN_WIDTH, SCREEN_HEIGHT = 960, 540
FPS = 60

# ── Combat/physics tuning provenance ─────────────────────────────────────────
# Structured, machine-enforced provenance (value / unit / source / status / issue
# / derivation) for the combat-physics tuning SCALARS below lives in
# `pycats/combat/provenance.py` (ADR-0003 / #233) — that registry is the source of
# truth the drift-guard checks. Changing a value here must update its Provenance
# row in the same diff or `tests/test_tuning_provenance.py` reds. The inline
# comments below stay as human-readable narrative; deep sourcing write-ups live in
# docs/research/*. (Render/UI/tail/platform/menu constants are out of scope.)

GRAVITY = 0.5
MAX_FALL_SPEED = 13
MOVE_SPEED = 6
JUMP_VEL = -13
DODGE_FRAMES = 15
MAX_JUMPS = 2  # single + double

# ---------------- physics constants --------------
GROUND_FRICTION = 0.5  # 1.0 = ice; 0.0 = instant stop
AIR_FRICTION = 0.85

# Fighter-vs-fighter "jostle" (Project M X-only push, issue #1) only applies when
# the two bodies are at substantially the same level — i.e. a grounded-contact
# interaction. Require their vertical overlap to be at least this fraction of the
# shorter body's height; below it, one fighter is clearly above the other
# (jumping over / standing on a head) and must NOT shove the one below (issue #68).
JOSTLE_MIN_VOVERLAP_FRAC = 0.8

# Timers (frames)
HURT_TIME = 12
# Shield-break "dizzy" stun (#12). Melee/PM: duration = (400 - p) + 90 frames,
# i.e. SHIELD_BREAK_STUN_MAX - percent, clamped to [MIN, MAX]. Higher damage =>
# SHORTER stun (inverse of every other stun). See combat.shield and
# docs/research/brawl-projectm-fighter-states.md.
SHIELD_BREAK_STUN_MAX = 490  # frames at 0% damage
SHIELD_BREAK_STUN_MIN = 90   # frames at >= 400% damage
# Shieldstun (#140): a blocked hit locks the defender in shield for
# floor(damage * SHIELDSTUN_FACTOR) frames. SmashWiki Shieldstun / the project
# roadmap (pm-mechanics-implementation-analysis.md): Brawl/PM factor 0.345.
# Attacks under ~2.9% give 0 frames (the floor yields that naturally).
SHIELDSTUN_FACTOR = 0.345
DODGE_TIME = 14
DODGE_SPEED = 14  # horizontal boost for a roll
# Smash charge (#327 slice 3a): frames of holding the smash input to reach full
# charge (fraction 0 -> 1). ⚠ playtest (~1s @60fps; PM smashes charge over ~1s).
SMASH_CHARGE_FRAMES = 60
# Smash charge (#327 slice 3b): full-charge output multiplier. A charged hit's
# damage/BKB/KBG scale by 1 + c*(SMASH_CHARGE_SCALE - 1) for charge fraction c
# (c=0 -> authored, c=1 -> base x SCALE). ⚠ playtest (PM ≈ 1.4).
SMASH_CHARGE_SCALE = 1.4
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
# scale). LEDGE_HANG_FRAMES doubles as the intangibility window for v1 (decay-on-
# regrab is deferred). The catch region is a box hanging off a solid-stage corner.
LEDGE_CATCH_W = 24    # px outward from the edge corner the catch box spans
LEDGE_CATCH_H = 64    # px downward from the lip the catch box spans
LEDGE_HANG_FRAMES = 120          # ~2s @60fps before auto-release (timeout)
LEDGE_REGRAB_LOCKOUT_FRAMES = 30  # post-release frames grab is suppressed

# ---------------- combat / attacks ----------------
PLAYER_ATTACK_DURATION = 12  # this can be different than the lifetime of an attack, for example, a fireball could take 6 frames to fire, and then the lifetime of the fireball could be as long as 120 frames
ATTACK_SIZE = (30, 18)  # width, height — render-only: sizes the drawn hit-box rect
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
HITSTUN_MULTIPLIER = 0.4   # hitstun_frames = floor(KB * this). ⚠ verify (Brawl/PM ~0.4).
HITSTUN_FLOOR = 1          # minimum hitstun frames for any clean hit. ⚠ tuning, not sourced.
# Hitlag / freeze frames (#138). SmashWiki Hitlag (Brawl onward):
# floor((d * HITLAG_DAMAGE_FACTOR + HITLAG_BASE) * h * e) * c, capped at HITLAG_CAP.
# This slice uses h = e = c = 1 (per-move/electric/crouch-cancel multipliers are
# deferred). Both attacker and defender freeze for this many frames on a clean
# hit, then the knockback slide proceeds.
HITLAG_DAMAGE_FACTOR = 0.3846154
HITLAG_BASE = 5
HITLAG_CAP = 30            # Brawl-onward cap (Melee was 20).
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
# ⚠ tuning starting point. Hitlag scaling (the "c" multiplier in knockback.py)
# stays deferred this slice — knockback only. A single global factor for v1;
# per-character/game tweaks can move it into FighterData later.
CROUCH_CANCEL_FACTOR = 0.67
# Auto landing-velocity knockdown (#145). A fighter that lands while still in
# hitstun (tumble) and hits the ground at/above KNOCKDOWN_VY_THRESHOLD downward
# px/frame is knocked down — forced into `prone` (#13) for KNOCKDOWN_PRONE_FRAMES
# getup frames. The hitstun gate is the real discriminator (normal jumps land at
# the same MAX_FALL_SPEED but with hurt_timer == 0); the velocity threshold filters
# out gentle pops. Teching (a tech input window that cancels the knockdown) is out
# of scope — #146 sibling. ⚠ tuning starting points, not sourced — playtest.
KNOCKDOWN_VY_THRESHOLD = 8.0   # downward impact speed (px/frame); MAX_FALL_SPEED is 13
KNOCKDOWN_PRONE_FRAMES = 30    # getup window the auto-knockdown sets (~0.5s @ 60 FPS)
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

# ---------------- platform constants ------------
# note: 300 is good for a 540 width map
THICK_PLAT_WIDTH = 800
# note: 40 is good for a 540 height map
THICK_PLAT_HEIGHT = 80
THICK_PLAT_Y_OFF = THICK_PLAT_HEIGHT
THIN_PLAT_WIDTH = 150
THIN_PLAT_HEIGHT = 20
THIN_PLAT_LEFT_X_OFF = -200
THIN_PLAT_RIGHT_X_OFF = 200
THIN_PLAT_Y_OFF = 200
GLOBAL_Y_OFF = 50

THICK_PLAT_DICT = {
    "x": SCREEN_WIDTH // 2 - THICK_PLAT_WIDTH // 2,
    "y": SCREEN_HEIGHT - THICK_PLAT_Y_OFF - GLOBAL_Y_OFF,
    "w": THICK_PLAT_WIDTH,
    "h": THICK_PLAT_HEIGHT,
}

THIN_PLAT_DICT_L = {
    "x": SCREEN_WIDTH // 2 - THIN_PLAT_WIDTH // 2 + THIN_PLAT_LEFT_X_OFF,
    "y": SCREEN_HEIGHT - THIN_PLAT_Y_OFF - GLOBAL_Y_OFF,
    "w": THIN_PLAT_WIDTH,
    "h": THIN_PLAT_HEIGHT,
}

THIN_PLAT_DICT_R = {
    "x": SCREEN_WIDTH // 2 - THIN_PLAT_WIDTH // 2 + THIN_PLAT_RIGHT_X_OFF,
    "y": SCREEN_HEIGHT - THIN_PLAT_Y_OFF - GLOBAL_Y_OFF,
    "w": THIN_PLAT_WIDTH,
    "h": THIN_PLAT_HEIGHT,
}

# ---------------- player size, position, color ---------------
PLAYER_SIZE = (40, 60)  # width, height
PLAYER1_START_X = SCREEN_WIDTH // 2 + THIN_PLAT_LEFT_X_OFF
PLAYER2_START_X = SCREEN_WIDTH // 2 + THIN_PLAT_RIGHT_X_OFF
PLAYER1_START_Y = SCREEN_HEIGHT - PLAYER_SIZE[1] - GLOBAL_Y_OFF - THIN_PLAT_Y_OFF
PLAYER2_START_Y = SCREEN_HEIGHT - PLAYER_SIZE[1] - GLOBAL_Y_OFF - THIN_PLAT_Y_OFF

EYE_OFFSET_X = 10
EYE_OFFSET_Y = 12
EYE_RADIUS = 8
GLINT_OFFSET_X = 12
GLINT_OFFSET_Y = 14
GLINT_RADIUS = 4

# ---------------- Other UI / visuals --------------------
HUD_PADDING = 10
HUD_SPACING = 22

# ---------------- colors -------------------
BG_COLOR = (60, 60, 70)
P1_COLOR = (255, 160, 64)  # orange
P2_COLOR = (90, 90, 90)  # gray
BLACK = (0, 0, 0)  # black
BLUE = (0, 0, 255)  # blue
WHITE = (255, 255, 255)  # white
RED = (255, 0, 0)  # red
YELLOW = (255, 255, 0)  # yellow

# ---------------- cat features -----------------
EAR_WIDTH = 15
EAR_HEIGHT = 20
EAR_SPACING = -2
EAR_PADDING = 5
WHISKER_OFFSET_Y = 20
WHISKER_OFFSET_X = 10
WHISKER_LENGTH = 20
WHISKER_THICKNESS = 2
WHISKER_SPACING = 4
WHISKER_COUNT = 3
WHISKER_ANGLE = 25  # Angle in degrees between whiskers

# Stripe pattern constants
STRIPE_COUNT = 3
STRIPE_WIDTH = 20
STRIPE_HEIGHT = 8
STRIPE_SPACING = 12  # Vertical spacing between stripes

# ---------------- tail features -----------------
TAIL_SEGMENTS = 15  # Number of segments in the tail
TAIL_SEGMENT_LENGTH = 8  # Length of each segment
TAIL_SEGMENT_WIDTH = 14  # Width of each segment (tapers towards the tip)
TAIL_BASE_OFFSET_X = 15  # Horizontal offset from player center to tail base
TAIL_BASE_OFFSET_Y = 5  # Vertical offset from player bottom to tail base
TAIL_ANCHOR_FLIP_STEP = 3  # px/frame the tail-base anchor eases across a facing
# flip (#3): caps the per-frame anchor move so a turn slides the base to the
# other hip over ~2*offset/step frames instead of teleporting in one frame.
TAPER_MODIFER = 0.2  # Tapering effect for tail segments

# (#37) Verlet tail physics — secondary motion (trail / drag / whip / settle).
# The tail is a Verlet point chain pinned at the hip; inertia is implicit in
# (pos - prev_pos), so these few knobs are the whole feel:
TAIL_GRAVITY = 0.30  # downward accel per frame — weight / how hard it hangs.
TAIL_AIR_DRAG = 0.85  # velocity retained per frame (<1). LOWER = more damped /
# less springy (settles faster); HIGHER = floppier, more trailing/whip. Main knob.
TAIL_CONSTRAINT_ITERS = 30  # relaxation passes/frame — higher = stiffer/less stretch.

# (#42) Cat-tail curl/expression layered on top of the passive chain: each frame
# the free points are nudged toward a gently up-curling rest arc in the cat's
# frame, so the tail holds a cat-like curl while gravity/inertia still dominate
# (trailing on the move, settling at rest).
TAIL_CURL = 0.02  # rad of upward curl per segment in the rest pose (0 = straight).
TAIL_CURL_STRENGTH = 0.02  # how strongly the tail seeks that curl each frame
# (0 = off / pure passive physics; higher = holds the curl more, flops less).

# (#42) Continuous undulation — a traveling sine wave on the rest target makes
# the tail constantly snake/flow even when idle (the cat is never "stiff").
TAIL_UNDULATE_AMP = 9.0  # px lateral wave amplitude at the tip (0 = off; tapers
# to ~0 at the base so the base stays attached and only the length snakes).
TAIL_UNDULATE_SPEED = 0.08  # temporal phase advance per frame (wiggle speed).
TAIL_UNDULATE_WAVELENGTH = 0.20  # spatial phase per segment (waves along length).

#### TODO: implement player color (yellow, blue, red, green) which will affect the shield color
#### TODO: implement parameterized shield color
SHIELD_COLOR = (80, 180, 255)

# ---------------- stocks / blast zone --------
INITIAL_LIVES = 3
BLAST_PADDING = 50  # px beyond screen = KO
RESPAWN_DELAY_FRAMES = int(2 * FPS)  # 2 s freeze before respawn

# ---------------- win screen ----------------
WIN_SCREEN_BG_COLOR = (40, 40, 50)
WIN_SCREEN_TEXT_COLOR = WHITE
WIN_SCREEN_TITLE_SIZE = 48
# 26, not 32: the stats table grew to 8 rows (KOs/Falls #11, Damage Given/Taken
# #98). At 32px the table + confirm instructions overflowed the 540px screen;
# 26px keeps every row on-screen and is still comfortably legible.
WIN_SCREEN_STATS_SIZE = 26
WIN_SCREEN_INSTRUCTION_SIZE = 24
WIN_SCREEN_PADDING = 20
WIN_SCREEN_LINE_SPACING = 40

# ---------------- character selection screen ---------------
CHAR_SELECT_BG_COLOR = (30, 30, 40)
CHAR_SELECT_TITLE_COLOR = WHITE
CHAR_SELECT_TITLE_SIZE = 36
CHAR_SELECT_INSTRUCTION_SIZE = 20
CHAR_SELECT_PADDING = 20
CHAR_SELECT_GRID_COLS = 3
CHAR_SELECT_GRID_ROWS = 2
CHAR_SELECT_TILE_SIZE = 120
CHAR_SELECT_TILE_SPACING = 20
CHAR_SELECT_CURSOR_COLOR = WHITE
CHAR_SELECT_CURSOR_WIDTH = 3
CHAR_SELECT_TOKEN_SIZE = 15
CHAR_SELECT_TOKEN_BORDER_WIDTH = 2

# ---------------- main menu ----------------
MAIN_MENU_BG_COLOR = (20, 20, 30)
MAIN_MENU_TITLE_COLOR = WHITE
MAIN_MENU_TITLE_SIZE = 72
MAIN_MENU_OPTION_SIZE = 36
MAIN_MENU_OPTION_COLOR = WHITE
MAIN_MENU_SELECTED_COLOR = YELLOW
MAIN_MENU_PADDING = 60
MAIN_MENU_OPTION_SPACING = 50

# Cat character definitions.
# Archived to pycats/characters/og_skins.py (#131, Part 1 of epic #127): these six
# entries are colour-skins of one cat, not characters. CAT_CHARACTERS re-exports the
# archive so existing consumers (char_select, game, sim/runner) read the one source.
from .characters.og_skins import OG_SKINS as CAT_CHARACTERS  # noqa: E402
