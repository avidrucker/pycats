"""Main-menu Options sub-menu (#121).

A consolidated settings screen reachable from the main menu — pycats's deliberate,
ratified divergence from Project M's distributed settings model (#122; global/HUD
prefs here, per-player config stays on char-select). Each change persists through
`settings.py` and updates the live value so it takes effect immediately:

- **Status Bars** (HUD overlay #111): flips `runtime_settings` live + persists.
- **Hitbox Overlay** (debug box visualiser #219): flips `runtime_settings` live
  + persists; the battle render path draws hit/hurtbox outlines when ON.
- **Window Size / Fullscreen** (display): routed back to game.py via injected
  `display_hooks` (None in headless/tests → those rows are inert). The hooks reuse
  game.py's existing F10/F11 machinery, which already persists display prefs.
- **Hold-ESC Quit**: flips the persisted hold-ESC-to-quit setting (#113).

Nav convention (research #115 §10.4): up/down move, A (attack) confirms/toggles,
B (special) backs out.
"""
import pygame  # type: ignore
from .config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    MAIN_MENU_BG_COLOR,
    MAIN_MENU_TITLE_COLOR,
    MAIN_MENU_TITLE_SIZE,
    MAIN_MENU_OPTION_SIZE,
    FONT_SCALE_ORDER,
    FONT_SCALE_NAMES,
)
from . import runtime_settings
from . import settings
from .menu_widgets import draw_menu_button, menu_button_size, BUTTON_MIN_WIDTH
from .menu_layout import effective_columns, grid_dims, scroll_to_visible
from .text_utils import text_renderer

# The rows lay out as a row-major grid (#389). NCOLS is the MAX columns; the actual
# column count is chosen per-frame from the scaled button width (#402) — 2 where the
# buttons fit, 1 at a large font_scale — via _effective_cols(). Navigation is 2D:
# up/down move a full row within a column, left/right move between columns.
NCOLS = 2


class OptionsMenu:
    """Consolidated Options screen: navigation, toggles, and rendering."""

    def __init__(self, p1_controls, p2_controls, display_hooks=None):
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls
        # Optional callables wiring display settings to game.py (None in
        # headless/tests → display rows render but do nothing on activate).
        self.display_hooks = display_hooks or {}

        # Row keys in display order. "back" is the explicit exit row.
        self.rows = ["status_bars", "hitbox_overlay", "input_history", "controls",
                     "font_scale", "window_scale", "fullscreen", "esc_quit", "back"]
        self.selected_option = 0
        # Top visible grid-row when the grid is taller than the viewport (large
        # font_scale); kept in range by render via scroll_to_visible (#402).
        self.scroll_top = 0

        self.input_cooldown = 0
        self.action_requested = None  # "back" or None

    def reset(self):
        self.selected_option = 0
        self.scroll_top = 0
        self.input_cooldown = 0
        self.action_requested = None

    # ---- input ----
    def _pressed(self, action, pressed_keys):
        """True if either player's ``action`` key is down this frame. Uses .get so a
        partial control dict (e.g. no left/right bound) is inert, not a KeyError."""
        a = self.p1_controls.get(action)
        b = self.p2_controls.get(action)
        return (a is not None and a in pressed_keys) or (
            b is not None and b in pressed_keys
        )

    def update(self, pressed_keys):
        if self.input_cooldown > 0:
            self.input_cooldown -= 1
            return

        # B / special backs out from any row.
        if self._pressed("special", pressed_keys):
            self.action_requested = "back"
            self.input_cooldown = 20
            return

        # 2D grid navigation (#389): up/down move a full row within a column,
        # left/right move between columns. Both wrap. The column count is the live
        # scale-aware value (#402) — 1 at large scale, so left/right become no-ops.
        n = len(self.rows)
        ncols, nrows = grid_dims(n, self._effective_cols())
        row, col = divmod(self.selected_option, ncols)
        moved = False
        if self._pressed("up", pressed_keys):
            row = (row - 1) % nrows
            moved = True
        if self._pressed("down", pressed_keys):
            row = (row + 1) % nrows
            moved = True
        if self._pressed("left", pressed_keys):
            col = (col - 1) % ncols
            moved = True
        if self._pressed("right", pressed_keys):
            col = (col + 1) % ncols
            moved = True
        if moved:
            new = row * ncols + col
            if new >= n:  # partial last row (odd count) — snap to the last cell
                new = n - 1
            self.selected_option = new
            self.input_cooldown = 10

        if self._pressed("attack", pressed_keys):
            self._activate(self.rows[self.selected_option])
            self.input_cooldown = 20

    def _activate(self, row):
        if row == "status_bars":
            new = not runtime_settings.show_status_timer_bars()
            runtime_settings.set("show_status_timer_bars", new)
            settings.save({"show_status_timer_bars": new})
        elif row == "hitbox_overlay":
            new = not runtime_settings.show_hitbox_overlay()
            runtime_settings.set("show_hitbox_overlay", new)
            settings.save({"show_hitbox_overlay": new})
        elif row == "input_history":
            new = not runtime_settings.show_input_history()
            runtime_settings.set("show_input_history", new)
            settings.save({"show_input_history": new})
        elif row == "controls":
            new = not runtime_settings.show_controls()
            runtime_settings.set("show_controls", new)
            settings.save({"show_controls": new})
        elif row == "font_scale":
            # Cycle Small -> Standard -> Large (#345); live + persisted.
            cur = runtime_settings.get("font_scale")
            order = FONT_SCALE_ORDER
            idx = order.index(cur) if cur in order else order.index("standard")
            new = order[(idx + 1) % len(order)]
            runtime_settings.set("font_scale", new)
            settings.save({"font_scale": new})
        elif row == "window_scale":
            hook = self.display_hooks.get("cycle_windowed_scale")
            if hook:
                hook()
        elif row == "fullscreen":
            hook = self.display_hooks.get("toggle_fullscreen")
            if hook:
                hook()
        elif row == "esc_quit":
            prefs = settings.load()
            settings.save(
                {"esc_hold_to_quit": not prefs.get("esc_hold_to_quit", True)}
            )
        elif row == "back":
            self.action_requested = "back"

    # ---- labels ----
    def _row_label(self, row):
        if row == "status_bars":
            return "Status Bars: " + ("ON" if runtime_settings.show_status_timer_bars() else "OFF")
        if row == "hitbox_overlay":
            return "Hitbox Overlay: " + ("ON" if runtime_settings.show_hitbox_overlay() else "OFF")
        if row == "input_history":
            return "Input History: " + ("ON" if runtime_settings.show_input_history() else "OFF")
        if row == "controls":
            return "Controls: " + ("ON" if runtime_settings.show_controls() else "OFF")
        if row == "font_scale":
            return "Font Size: " + FONT_SCALE_NAMES.get(
                runtime_settings.get("font_scale"), "Standard")
        if row == "window_scale":
            getter = self.display_hooks.get("get_windowed_scale")
            return "Window Size: " + (f"{getter():g}x" if getter else "F10")
        if row == "fullscreen":
            getter = self.display_hooks.get("is_fullscreen")
            return "Fullscreen: " + (("ON" if getter() else "OFF") if getter else "F11")
        if row == "esc_quit":
            return "Hold-ESC Quit: " + (
                "ON" if settings.load().get("esc_hold_to_quit", True) else "OFF"
            )
        if row == "back":
            return "Back"
        return row

    # ---- layout (scale-aware, scrollable grid #402) ----
    def _button_size(self):
        """Uniform (w, h) for every option button at the live font scale — the widest
        label sets the width so the grid columns line up."""
        w, h = BUTTON_MIN_WIDTH, 0
        for row in self.rows:
            bw, bh = menu_button_size(self._row_label(row), MAIN_MENU_OPTION_SIZE,
                                      focused=True)
            w, h = max(w, bw), max(h, bh)
        return w, h

    def _effective_cols(self):
        """Columns that fit at the live scale — 2 where the buttons fit, 1 at large."""
        bw, _ = self._button_size()
        return effective_columns(SCREEN_WIDTH, bw, NCOLS)

    def _layout(self):
        """Placement for this frame, updating scroll_top so the selected row stays on
        screen. Returns (placements, meta) — placements is [(row_index, (cx, cy))] for
        the rows to draw; meta carries the title/instruction bands + scroll flags.

        Vertical bands scale with the font: a title at top, two instruction lines at
        the bottom, and the grid scrolls within whatever is left (the grid is taller
        than the viewport at large scale, so scroll_to_visible keeps focus on screen)."""
        scale = runtime_settings.font_scale()
        n = len(self.rows)
        bw, bh = self._button_size()
        ncols, nrows = grid_dims(n, effective_columns(SCREEN_WIDTH, bw, NCOLS))

        title_h = text_renderer._get_font(None, MAIN_MENU_TITLE_SIZE).get_height()
        instr_h = text_renderer._get_font(None, 20).get_height()
        title_center_y = round(10 * scale) + title_h // 2
        grid_top = round(10 * scale) + title_h + round(10 * scale)
        instr_line = instr_h + round(4 * scale)
        instr_top = SCREEN_HEIGHT - (2 * instr_line + round(8 * scale))
        row_spacing = bh + round(6 * scale)
        viewport_h = max(row_spacing, instr_top - grid_top)
        visible_rows = max(1, viewport_h // row_spacing)

        sel_row = self.selected_option // ncols
        self.scroll_top = scroll_to_visible(self.scroll_top, sel_row, visible_rows, nrows)

        col_x = (SCREEN_WIDTH // 2,) if ncols == 1 else (SCREEN_WIDTH // 4,
                                                         SCREEN_WIDTH * 3 // 4)
        last = min(nrows, self.scroll_top + visible_rows)
        placements = []
        for gr in range(self.scroll_top, last):
            cy = grid_top + (gr - self.scroll_top) * row_spacing + bh // 2
            for c in range(ncols):
                i = gr * ncols + c
                if i < n:
                    placements.append((i, (col_x[c], cy)))

        meta = dict(ncols=ncols, nrows=nrows, visible_rows=visible_rows,
                    title_center=(SCREEN_WIDTH // 2, title_center_y),
                    grid_top=grid_top, instr_top=instr_top, instr_line=instr_line,
                    more_above=self.scroll_top > 0, more_below=last < nrows,
                    button_width=bw)
        return placements, meta

    # ---- render ----
    def render(self, surface):
        surface.fill(MAIN_MENU_BG_COLOR)
        scale = runtime_settings.font_scale()
        placements, meta = self._layout()

        text_renderer.render_text_simple(
            "Options", MAIN_MENU_TITLE_SIZE, MAIN_MENU_TITLE_COLOR, surface,
            meta["title_center"], center=True,
        )

        for i, center in placements:
            # Each row is a menu-button widget (#359): a coloured rect that glows when
            # focused, with a redundant ► marker (focus not colour-only, #346). A
            # uniform width keeps the columns aligned (#402).
            draw_menu_button(
                surface, self._row_label(self.rows[i]), center, MAIN_MENU_OPTION_SIZE,
                focused=(i == self.selected_option), min_width=meta["button_width"],
            )

        # Scroll affordances (#402): ↑/↓ "more" when the grid overflows the viewport
        # (↑↓ are in the font-capability whitelist, unlike ▲▼).
        if meta["more_above"]:
            text_renderer.render_mixed_centered(
                "↑ more", 18, WHITE, surface,
                (SCREEN_WIDTH // 2, meta["grid_top"] - round(12 * scale)))
        if meta["more_below"]:
            text_renderer.render_mixed_centered(
                "↓ more", 18, WHITE, surface,
                (SCREEN_WIDTH // 2, meta["instr_top"] - round(4 * scale)))

        instructions = ["Use WASD or arrows to navigate", "A to toggle, B to go back"]
        for i, instruction in enumerate(instructions):
            cy = meta["instr_top"] + i * meta["instr_line"] + meta["instr_line"] // 2
            text_renderer.render_text_mixed(
                instruction, 20, WHITE, surface, (SCREEN_WIDTH // 2, cy), center=True,
            )
