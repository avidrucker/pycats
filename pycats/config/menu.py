"""Menu / screen-chrome constants — win screen, character-select, main menu, the
shared menu-input debounce windows, and the single-source font sizes / scales.
Aliases the shared colours from `render`."""

from .render import WHITE, YELLOW

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
# 5 cols holds the full 5-archetype roster on ONE row (#779/#821): 5×120 + 4×20 spacing =
# 680 px, centred in the 960-wide screen (grid_start_x recomputes from COLS). Was 3 (the
# 4th tile, Gnok, wrapped to a second row).
CHAR_SELECT_GRID_COLS = 5
CHAR_SELECT_GRID_ROWS = 1
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
# Menu input-debounce windows (frames), shared by main / options / pause menus
# (#433): navigation repeats faster than a committing select/back.
MENU_NAV_COOLDOWN = 10
MENU_SELECT_COOLDOWN = 20

# ---------------- font sizes (single source, #344) ----------------
# The one place every UI/HUD text size lives, so a size change — and the planned
# font-scale scalar (#345) — has a single chokepoint. The per-screen title / option
# / stat sizes above are part of this same family (WIN_SCREEN_*_SIZE,
# CHAR_SELECT_*_SIZE, MAIN_MENU_*_SIZE); the HUD + text-probe sizes that used to be
# scattered as literals across the render/game/text-util modules are gathered here.
# NOTE: cat_faces._MONO_SIZE is deliberately NOT centralised — it is a monospace
# FACE-render size (tuned to the ASCII face art), not a UI text size.
STATUS_BAR_SECONDS_SIZE = 16  # above-head timer-bar seconds / percent readout (#111/#334)
STATUS_BAR_LABEL_SIZE = 12  # above-head timer-bar word label (#334)
GAME_HUD_FONT_SIZE = 24  # the shared in-game HUD font (game.py)
HUD_EMPHASIS_SIZE = 36  # the emphasized Damage %/Lives rows in the bottom corners (#550)
TEXT_PROBE_SIZE = 16  # glyph-support probe / measurement fonts (text_utils)

# Font-scale scalar (#345): a global multiplier over every font size above, chosen
# from the Options menu. Applied at the text_utils font chokepoint (runtime_settings
# .scaled_font_size); "standard" (1.0) is an exact identity, so the default render is
# byte-identical. MIN_FONT_PX clamps a scaled-down size so it never rounds to 0.
FONT_SCALES = {"small": 0.5, "standard": 1.0, "large": 2.0}
FONT_SCALE_ORDER = ("small", "standard", "large")  # Options-menu cycle order
FONT_SCALE_NAMES = {"small": "Small", "standard": "Standard", "large": "Large"}
MIN_FONT_PX = 6
