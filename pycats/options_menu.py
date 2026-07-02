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
    MAIN_MENU_SELECTED_COLOR,
    FONT_SCALE_ORDER,
    FONT_SCALE_NAMES,
    MENU_NAV_COOLDOWN,
    MENU_SELECT_COOLDOWN,
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

# Focused-option captions (#390): one-line description of what each row does, shown
# at bottom-centre in a reserved band above the hint lines (never overlaps a button).
CAPTION_SIZE = 18
CAPTION_COLOR = MAIN_MENU_SELECTED_COLOR  # ties the caption to the focused row
INSTRUCTION_FONT_SIZE = 20   # bottom nav-hint lines (also drives the instr-band height)
MORE_CUE_FONT_SIZE = 18      # the "↑ more" / "↓ more" scroll affordances
ROW_DESCRIPTIONS = {
    "status_bars": "Show the HUD stun / shield timer bars above each fighter.",
    "hitbox_overlay": "Draw debug hit / hurtbox outlines during battle.",
    "input_history": "Show your recent inputs in Project M notation, in-battle.",
    "controls": "Show the on-screen control hints during battle.",
    "font_scale": "Resize all menu / HUD text: Small / Standard / Large.",
    "window_scale": "Cycle the windowed zoom (also F10).",
    "fullscreen": "Toggle fullscreen (also F11).",
    "esc_quit": "Hold ESC for 2 seconds to quit / return to menu.",
    "back": "Return to the main menu.",
}


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
            self.input_cooldown = MENU_SELECT_COOLDOWN
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
            self.input_cooldown = MENU_NAV_COOLDOWN

        if self._pressed("attack", pressed_keys):
            self._activate(self.rows[self.selected_option])
            self.input_cooldown = MENU_SELECT_COOLDOWN

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

    # ---- captions (#390) ----
    def _focused_caption(self):
        """The description line for the currently-focused row (empty if none)."""
        return ROW_DESCRIPTIONS.get(self.rows[self.selected_option], "")

    def _fit_caption(self, text, size, max_w):
        """`text` ellipsized so it renders within `max_w` pixels at `size`."""
        font = text_renderer._get_font(None, size)
        if font.size(text)[0] <= max_w:
            return text
        while text and font.size(text + "…")[0] > max_w:
            text = text[:-1]
        return (text.rstrip() + "…") if text else "…"

    def _caption_layout(self, meta):
        """(text, rect) for the focused caption, ellipsized to fit and centred in the
        reserved caption band. Shared by render and the no-overlap test (#390)."""
        scale = runtime_settings.font_scale()
        text = self._fit_caption(self._focused_caption(), CAPTION_SIZE,
                                 SCREEN_WIDTH - round(40 * scale))
        w, h = text_renderer._get_font(None, CAPTION_SIZE).size(text)
        rect = pygame.Rect(0, 0, w, h)
        rect.center = meta["caption_center"]
        return text, rect

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
        instr_h = text_renderer._get_font(None, INSTRUCTION_FONT_SIZE).get_height()
        cap_h = text_renderer._get_font(None, CAPTION_SIZE).get_height()
        title_center_y = round(10 * scale) + title_h // 2
        grid_top = round(10 * scale) + title_h + round(10 * scale)
        instr_line = instr_h + round(4 * scale)
        instr_top = SCREEN_HEIGHT - (2 * instr_line + round(8 * scale))

        # Reserved caption band (#390): one line just above the hints. The grid
        # viewport ends above it (and above a bottom strip for the "↓ more" cue), so a
        # caption can never overlap a button or the scroll affordance.
        caption_center_y = instr_top - round(8 * scale) - cap_h // 2
        caption_top = caption_center_y - cap_h // 2 - round(6 * scale)
        more_strip = instr_h + round(6 * scale)

        row_spacing = bh + round(6 * scale)
        viewport_h = max(row_spacing, caption_top - grid_top - more_strip)
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

        more_below_y = grid_top + visible_rows * row_spacing + more_strip // 2
        meta = dict(ncols=ncols, nrows=nrows, visible_rows=visible_rows,
                    title_center=(SCREEN_WIDTH // 2, title_center_y),
                    grid_top=grid_top, instr_top=instr_top, instr_line=instr_line,
                    caption_center=(SCREEN_WIDTH // 2, caption_center_y),
                    more_above=self.scroll_top > 0, more_below=last < nrows,
                    more_below_y=more_below_y, button_width=bw)
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
        # (↑↓ are in the font-capability whitelist, unlike ▲▼). ↓ sits in the reserved
        # bottom strip, above the caption band (#390).
        if meta["more_above"]:
            text_renderer.render_mixed_centered(
                "↑ more", MORE_CUE_FONT_SIZE, WHITE, surface,
                (SCREEN_WIDTH // 2, meta["grid_top"] - round(12 * scale)))
        if meta["more_below"]:
            text_renderer.render_mixed_centered(
                "↓ more", MORE_CUE_FONT_SIZE, WHITE, surface,
                (SCREEN_WIDTH // 2, meta["more_below_y"]))

        # Focused-option caption (#390): describes what the highlighted row does, in a
        # reserved band above the hints so it never overlaps a button.
        caption_text, _caption_rect = self._caption_layout(meta)
        if caption_text:
            text_renderer.render_text_mixed(
                caption_text, CAPTION_SIZE, CAPTION_COLOR, surface,
                meta["caption_center"], center=True)

        instructions = ["Use WASD or arrows to navigate", "A to toggle, B to go back"]
        for i, instruction in enumerate(instructions):
            cy = meta["instr_top"] + i * meta["instr_line"] + meta["instr_line"] // 2
            text_renderer.render_text_mixed(
                instruction, INSTRUCTION_FONT_SIZE, WHITE, surface,
                (SCREEN_WIDTH // 2, cy), center=True,
            )
