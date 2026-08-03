"""Stage geometry — platforms, the v1 Starting Point (Final Destination), blast
zones, stocks, and the respawn freeze. World-space constants that derive from the
screen dimensions and are consumed by both the sim and the render path."""

from .screen import FPS, SCREEN_HEIGHT, SCREEN_WIDTH

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

# ---------------- Starting Point (v1 Final Destination) ----------------
# pycats' single player-facing stage (#660): a flat Final Destination whose thematic
# name inverts "Final Destination" -> "Starting Point". One solid main platform, NO side
# platforms. Sized from the PM FD measurements in
# docs/research/2026-07-06-pm-final-destination-measurements.md (#659): the Melee FD
# ground half-width (85.5657 units, libmelee EDGE_GROUND_POSITION) x 2 x PX_PER_UNIT.
# ⚠ best-guess (Melee-proportioned; PM 3.6 floats live in-.pac, unsourceable). Kept a bare
# literal per ADR-0003 C1 (like DODGE_AIR_SPEED = round(3.1 x PX_PER_UNIT)); the derivation
# is re-evaluated by tests/test_starting_point_stage.py.
#   width = round(2 x 85.5656967163 x 5.4) = 924 px  (fits 960 with ~18px margins).
# Height + surface-y reuse the thick-platform convention so live-game spawns land at today's
# floor height. Blast zones stay on the existing BLAST_PADDING model — the FD blast-zone vs
# fixed-camera reconciliation is a deferred decision: per #659, NOT built here.
FD_EDGE_GROUND_UNITS = 85.5656967163  # Melee FD teeter/ground edge x (libmelee), #659
STARTING_POINT_WIDTH = 924  # round(2 * FD_EDGE_GROUND_UNITS * PX_PER_UNIT)
STARTING_POINT_HEIGHT = THICK_PLAT_HEIGHT  # reuse the thick-platform thickness (80)
STARTING_POINT_DICT = {
    "x": SCREEN_WIDTH // 2 - STARTING_POINT_WIDTH // 2,
    "y": SCREEN_HEIGHT - THICK_PLAT_Y_OFF - GLOBAL_Y_OFF,  # same surface y as today's main plat
    "w": STARTING_POINT_WIDTH,
    "h": STARTING_POINT_HEIGHT,
}

# ---------------- stocks / blast zone --------
INITIAL_LIVES = 3
BLAST_PADDING = 50  # px beyond screen = KO (vertical, bottom; also L/R fallback baseline)
# Owner design decision (Avi, 2026-07-20): the TOP KO line sits 100px higher than the
# bottom — a fighter launched upward is KO'd at 150px above the screen top instead of 50,
# giving more vertical room above the stage. Mirrors the BLAST_PADDING_X axis-split (#733,
# #823). The bottom KO boundary stays on BLAST_PADDING (50). Registered TUNED (owner
# decision) in combat/provenance.py.
BLAST_PADDING_TOP = BLAST_PADDING + 100  # = 150 px above the screen top = KO (#823)
# TEMPORARY game-feel experiment (#733, owner-requested 2026-07-20): a *horizontal*
# KO boundary widened so a fighter may travel ~100px off the left/right screen edge
# before being KO'd — more sideways recovery room. This is NOT a Project M-faithful /
# ratified value; it is an experimental playtest knob, deliberately unregistered in the
# tuning-provenance registry (it is not a settled TUNED design value). If a PM-canon
# horizontal blast-zone width later surfaces, it supersedes this — see the FD blast-zone
# note above ("Blast zones stay on the existing BLAST_PADDING model"). The vertical
# (top/bottom) KO boundary stays on BLAST_PADDING (50).
BLAST_PADDING_X = 100  # px beyond L/R screen edge = KO (temporary; see note above)
RESPAWN_DELAY_FRAMES = int(2 * FPS)  # 2 s freeze before respawn
