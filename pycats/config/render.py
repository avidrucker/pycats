"""Fighter render constants — body size/start positions, eyes, colors, cat
features, stripes, the Verlet tail, shield colour, and HUD padding. Derives fighter
spawn positions from the screen dimensions and the thin-platform offsets."""

from .screen import SCREEN_HEIGHT, SCREEN_WIDTH
from .stage import GLOBAL_Y_OFF, THIN_PLAT_LEFT_X_OFF, THIN_PLAT_RIGHT_X_OFF, THIN_PLAT_Y_OFF

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
P1_COLOR = (255, 160, 64)  # orange — P1's body
P2_COLOR = (90, 90, 90)  # gray — P2's body
# Fighter body outline (#546): a thin light border ringing each fighter's body
# rect so a low-luminance skin stays separable from the dark stage bg. The gray
# tabby (2.76:1), black void (1.69:1), and legacy P2 gray (1.58:1) bodies all sit
# below WCAG's 3:1 large-object target vs BG_COLOR; the outline is the separator
# and measures 8.7:1 vs BG_COLOR. Light-on-dark by design: it rescues dark bodies
# and is harmlessly redundant on already-visible light skins (ghost/bengal). This
# is a functional accessibility separator validated by the #346 audit's contrast
# measurement — not a P2 identity recolor (which would need a design decision).
FIGHTER_OUTLINE_COLOR = (230, 230, 230)
FIGHTER_OUTLINE_WIDTH = 2
P1_STRIPE_COLOR = (204, 102, 0)  # dark orange — P1's secondary fur (P2's is BLACK)
# Player identity ACCENT colours (#450): the red/blue used for name labels
# (render_battle), cursors/confirmations (char_select), and confirmation borders
# (win_screen). Distinct from the body colours above.
P1_UI_COLOR = (255, 100, 100)  # red — P1 accent
P2_UI_COLOR = (100, 100, 255)  # blue — P2 accent
# Standard ~50% dim over a screen (char_select start overlay, pause menu) (#450).
OVERLAY_DIM_ALPHA = 128
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
