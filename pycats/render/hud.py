# pycats/render/hud.py
"""The battle HUD + shell chrome: the per-player stat rows (secondary + emphasized
bottom-corner numbers), the controls block, the input-history strip, the pause
hint, and the shell overlays (FPS / fullscreen / debug input).

Extracted verbatim from render_battle (#900, child 3 of #833). Byte-identical to
the pre-#900 draws — the render-parity oracle guards it.
"""

import pygame

from .. import runtime_settings
from ..config import (
    HUD_EMPHASIS_SIZE,
    HUD_PADDING,
    HUD_SPACING,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from ..entities import Player
from ..input_history import _GLYPHS, INPUT_HISTORY_FRAMES, PRESSED
from ..ui import text_utils

# HUD / text-overlay layout (#415: named from inline literals). The overlay font
# size was repeated at ~10 call sites; the line counts + block gap couple the
# controls / input-history blocks' start-y to the HUD's row count.
HUD_FONT_SIZE = 24  # shared size for HUD / controls / input-history / chrome text
# draw_hud rows split by audience (#545) AND by emphasis (#550). The top-anchored
# "secondary" group holds the player-facing label/jumps/Shield HP rows (always on)
# plus the two implementation-jargon rows (FSM state, Shield Attempting bool) that
# render only when the dev-info flag is on. The two numbers players read constantly
# — Damage % and Lives — are split OUT of this group and drawn larger in the bottom
# corners (see hud_emphasis_rows / draw_hud). HUD_LINE_COUNT is the all-secondary-rows
# total kept for back-compat; layout below anchors on the live hud_line_count().
HUD_PLAYER_LINE_COUNT = 3  # label + jumps + Shield HP (always on; #550 moved Lives/Damage out)
HUD_DEV_LINE_COUNT = 2  # FSM: + Shield Attempting: (dev-info-gated)
HUD_MOVEMENT_LINE_COUNT = 1  # Movement: (movement-status-gated, under Shield HP, #977)
HUD_MINIMAL_LINE_COUNT = 1  # just the player-name label when minimal-HUD is on (#977)
HUD_LINE_COUNT = HUD_PLAYER_LINE_COUNT + HUD_DEV_LINE_COUNT  # 5, all secondary rows (dev-info on)
CONTROLS_LINE_COUNT = 7  # rows drawn by draw_controls (header + 6 controls)
HUD_BLOCK_GAP = 20  # vertical gap between stacked text blocks
HUD_EMPHASIS_SPACING = 34  # row pitch for the larger emphasized rows (cf. HUD_SPACING for the size 24 rows)

# Input-history GRID layout (#875). Replaces #21's one-line strip: one row per
# control (in _GLYPHS order), one column per recent frame (newest on the right),
# so a same-frame combo, a sequential press, and a held-while-pressed one read
# apart. Compact font/pitch keeps the 7-row block from crowding the 540px screen.
INPUT_GRID_FONT_SIZE = 16
INPUT_GRID_ROW_H = 18  # vertical pitch between grid rows (header + 7 control rows)
INPUT_GRID_CELL_W = 13  # horizontal pitch between frame columns
INPUT_GRID_LABEL_W = 22  # width reserved for the leading row-glyph column
# Cells are drawn as pygame primitives, not text glyphs — the HUD font lacks ●/│,
# and primitives keep columns pixel-aligned regardless of glyph metrics. A filled
# dot = a rising edge that frame; a dim vertical bar = down-but-not-freshly-pressed.
INPUT_GRID_DOT_R = 4  # pressed-edge dot radius
INPUT_GRID_BAR_H = 12  # held bar height
INPUT_GRID_PRESSED_COLOR = WHITE
INPUT_GRID_HELD_COLOR = (130, 130, 140)  # dimmer than a fresh press


def hud_line_count():
    """Rows draw_hud actually draws given the live HUD flags. The input-history
    block anchors below the HUD, so it must follow the real row count, not a fixed
    maximum, or a gap opens. Minimal-HUD (#977) collapses to the single label row;
    otherwise it's the player rows plus the movement (#977) and dev-info (#545)
    rows when those flags are on. Mirrors hud_rows exactly."""
    if runtime_settings.minimal_hud():
        return HUD_MINIMAL_LINE_COUNT
    return (
        HUD_PLAYER_LINE_COUNT
        + (HUD_MOVEMENT_LINE_COUNT if runtime_settings.show_movement_status() else 0)
        + (HUD_DEV_LINE_COUNT if runtime_settings.show_dev_info() else 0)
    )


def hud_rows(label, p: Player):
    """The ordered *secondary* HUD row strings for player `p` — the top-anchored,
    standard-size group. Minimal-HUD (#977) collapses this to just the player-name
    label (the essential Lives / Damage % stay — they are the emphasized bottom-corner
    rows, see hud_emphasis_rows, #550). Otherwise it honours the live flags: the
    Movement row (#977) renders under Shield HP when show_movement_status() is on, and
    the FSM / Shield Attempting jargon rows when show_dev_info() is on (#545); the
    label / jumps / Shield HP rows always render. Row order matches the pre-gate layout
    so the flags-off secondary render is unchanged."""
    if runtime_settings.minimal_hud():
        return [label]
    dev = runtime_settings.show_dev_info()
    rows = [label]
    if dev:
        rows.append(f"FSM: {p.state.capitalize()}")
    rows.append(f"{p.fighter.jumps_remaining} jump{'s' if p.fighter.jumps_remaining != 1 else ''} left")
    rows.append(f"Shield HP: {p.fighter.shield_hp}")
    if runtime_settings.show_movement_status():
        rows.append(f"Movement: {p.state.capitalize()}")
    if dev:
        rows.append(f"Shield Attempting: {'Yes' if p.fighter.shield_attempting else 'No'}")
    return rows


def hud_emphasis_rows(p: Player):
    """The two numbers players read constantly — Lives then Damage % — split out of
    the secondary group (#550) to render larger in the bottom corners. Ordered
    top->bottom, so Damage (the most-glanced value) sits closest to the corner."""
    return [f"Lives: {p.fighter.lives}", f"Damage: {int(p.fighter.percent)}%"]


def emphasis_row_y(i, n):
    """Top-y of emphasized row `i` of `n`, bottom-anchored (#550). The block is
    lifted to sit just above the 'P: Pause Game' hint line (draw_pause_hint, at
    SCREEN_HEIGHT - HUD_SPACING*3) so the P2 (bottom-right) rows never overlap it,
    and grows UPWARD as the font scale enlarges the rows. Pure geometry — the
    testable seam for the emphasized-row placement."""
    baseline = SCREEN_HEIGHT - HUD_SPACING * 3 - HUD_BLOCK_GAP
    return baseline - (n - i) * HUD_EMPHASIS_SPACING


def draw_hud_emphasis(surface, p: Player, topright=False):
    """Draws the emphasized Damage %/Lives rows larger in the bottom corner (#550).
    Split from the secondary rows so the two concerns — glanceable stats vs. the
    top-grouped detail — render independently. The size routes through
    text_utils.render_text -> scaled_font_size, so it honours the live font_scale."""
    emphasis = hud_emphasis_rows(p)
    for i, txt in enumerate(emphasis):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = emphasis_row_y(i, len(emphasis))

        text_utils.render_text(surface, txt, (x_pos, y_pos), HUD_EMPHASIS_SIZE, WHITE, right_align=topright)


def draw_hud(surface, p: Player, label, topright=False):
    """Draws the HUD for a player in two groups (#550): the secondary rows (label,
    jumps, Shield HP, plus the dev-info rows FSM/Shield Attempting when the flag is
    on, #545) top-anchored at the standard size, and the emphasized Damage %/Lives
    rows larger in the bottom corner."""
    for i, txt in enumerate(hud_rows(label, p)):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = HUD_PADDING + i * HUD_SPACING

        text_utils.render_text(surface, txt, (x_pos, y_pos), HUD_FONT_SIZE, WHITE, right_align=topright)

    draw_hud_emphasis(surface, p, topright=topright)


def draw_controls(surface, p: Player, label, topright=False):
    """Draws the control scheme for a player below the HUD."""
    # Convert pygame key constants to readable strings with Unicode arrows where appropriate
    key_names = {
        pygame.K_a: "A",
        pygame.K_d: "D",
        pygame.K_w: "W",
        pygame.K_s: "S",
        pygame.K_v: "V",
        pygame.K_c: "C",
        pygame.K_x: "X",
        pygame.K_LEFT: "←",
        pygame.K_RIGHT: "→",
        pygame.K_UP: "↑",
        pygame.K_DOWN: "↓",
        pygame.K_SLASH: "/",
        pygame.K_PERIOD: ".",
        pygame.K_COMMA: ",",
        pygame.K_b: "B",  # #462 P1 default smash (now just a prettifier — pygame names it 'b' too)
        pygame.K_QUOTE: "'",  # #462 P2 default smash — pygame names K_QUOTE 'quote', so the glyph still helps
    }

    def keyname(code):
        # #469: render ANY bound key by name so a rebind (#439) to a key outside the
        # glyph dict shows its actual name instead of '?'. The dict above is now an
        # optional prettifier (arrows/punctuation), not a correctness requirement.
        # None (an unbound action, e.g. missing 'smash') has no name -> stays '?'.
        if code is None:
            return "?"
        return key_names.get(code) or pygame.key.name(code).upper() or "?"

    controls = [
        f"{label} Controls:",
        f"Move: {keyname(p.controls['left'])}/{keyname(p.controls['right'])}",
        f"Jump: {keyname(p.controls['up'])}",
        f"Down: {keyname(p.controls['down'])}",
        f"Attack: {keyname(p.controls['attack'])}",
        f"Shield: {keyname(p.controls['shield'])}",
        f"Special: {keyname(p.controls['special'])}",
        f"Smash: {keyname(p.controls.get('smash'))}",  # #462
    ]

    # Start drawing below the HUD (its live row count + some spacing) — the count
    # shrinks when the dev-info rows are gated off (#545), so read it live.
    start_y = HUD_PADDING + hud_line_count() * HUD_SPACING + HUD_BLOCK_GAP

    for i, txt in enumerate(controls):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = start_y + i * HUD_SPACING

        # Use mixed text rendering for Unicode arrow support
        if topright:
            # For right-aligned text, we need to calculate positioning differently
            text_width = text_utils.text_renderer._get_font(None, HUD_FONT_SIZE).size(txt)[0]
            adjusted_x = x_pos - text_width
            text_utils.text_renderer.render_text_mixed(txt, HUD_FONT_SIZE, WHITE, surface, (adjusted_x, y_pos))
        else:
            text_utils.text_renderer.render_text_mixed(txt, HUD_FONT_SIZE, WHITE, surface, (x_pos, y_pos))


def draw_input_history(surface, history, label, topright=False):
    """Draw a fighter's recent-input GRID (#875) below the controls block.

    ``history`` is an :class:`~pycats.input_history.InputHistory`. Rows are the
    seven controls (``_GLYPHS`` order: absolute-direction arrows then A/B/S);
    columns are the last ``INPUT_HISTORY_FRAMES`` frames, newest at the right.
    A cell shows ``●`` where that control had its rising edge that frame and
    ``│`` where it was held-but-not-freshly-pressed — so a same-frame combo, a
    sequential press, and a held-while-pressed one look different (the #21 strip
    could not tell them apart). Glyphs go through ``render_text_mixed`` (the same
    Unicode path draw_controls uses). The block anchors directly under the HUD (its
    live row count, #545/#977) — controls are pause-only (#977); for P2 it hugs the
    right edge."""
    frames = history.frames()
    n = INPUT_HISTORY_FRAMES
    block_w = INPUT_GRID_LABEL_W + n * INPUT_GRID_CELL_W
    # Controls are now pause-only (#977), so in battle the input-history grid anchors
    # directly below the HUD's live row count (was below HUD + the controls block).
    top_y = HUD_PADDING + hud_line_count() * HUD_SPACING + HUD_BLOCK_GAP
    block_x = (SCREEN_WIDTH - HUD_PADDING - block_w) if topright else HUD_PADDING
    cells_x0 = block_x + INPUT_GRID_LABEL_W
    # Recorded frames right-align inside the N-column window (newest fixed at the
    # rightmost column, filling in from the right as the buffer warms up).
    offset = n - len(frames)

    draw = text_utils.text_renderer.render_text_mixed
    draw(f"{label} Inputs", INPUT_GRID_FONT_SIZE, WHITE, surface, (block_x, top_y))
    mid = INPUT_GRID_FONT_SIZE // 2  # vertical centre of a row-glyph, for cell markers
    for r, (name, glyph) in enumerate(_GLYPHS):
        row_y = top_y + (r + 1) * INPUT_GRID_ROW_H
        draw(glyph, INPUT_GRID_FONT_SIZE, WHITE, surface, (block_x, row_y))
        cy = row_y + mid
        for i, marks in enumerate(frames):
            mark = marks.get(name)
            if mark is None:
                continue
            cx = cells_x0 + (offset + i) * INPUT_GRID_CELL_W + INPUT_GRID_CELL_W // 2
            if mark == PRESSED:
                pygame.draw.circle(surface, INPUT_GRID_PRESSED_COLOR, (cx, cy), INPUT_GRID_DOT_R)
            else:
                pygame.draw.line(
                    surface,
                    INPUT_GRID_HELD_COLOR,
                    (cx, cy - INPUT_GRID_BAR_H // 2),
                    (cx, cy + INPUT_GRID_BAR_H // 2),
                    2,
                )


def draw_pause_hint(surface):
    """The static 'P: Pause Game' battle-HUD hint, drawn during the playing state.

    It reads no shell state (a constant string), so it is battle HUD, not shell
    chrome — BattleScreen.render owns it (#279), beside draw_hud/draw_controls."""
    text_utils.render_text(
        surface,
        "P: Pause Game",
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 3),
        HUD_FONT_SIZE,
        WHITE,
        right_align=True,
    )


def draw_shell_chrome(surface, fps, is_fullscreen, frame_input):
    """Draw the playing-state SHELL overlays — debug input, FPS, fullscreen hints.

    These read shell/loop state (fps, is_fullscreen, frame_input), NOT battle state,
    so game.py's loop calls this helper with the state it owns instead of inlining the
    draws (#279). Kept out of BattleScreen so the battle object stays free of shell
    state (cf. #100 Risks, #246). Byte-identical to the old inline block."""
    if frame_input:
        text_utils.render_text(
            surface,
            frame_input.__str__(),
            (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
            HUD_FONT_SIZE,
            WHITE,
        )
    text_utils.render_text(
        surface,
        f"FPS: {fps:.2f}",
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
        HUD_FONT_SIZE,
        WHITE,
        right_align=True,
    )
    fs_text = "F11: Toggle Fullscreen | " + ("F10: Fullscreen Zoom" if is_fullscreen else "F10: Window Size")
    text_utils.render_text(
        surface,
        fs_text,
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 2),
        HUD_FONT_SIZE,
        WHITE,
        right_align=True,
    )
    # In-battle ESC-hold leave-match hint (#681, from the #549 audit) — gated by the
    # BATTLE show_controls toggle, and only while the ESC-hold affordance is enabled.
    # Worded "hold" + "leave match" to name the ESC-hold action plainly (#868 removed the
    # old ESC-tap "Exit Fullscreen" hint, since ESC no longer exits fullscreen).
    if runtime_settings.show_controls() and runtime_settings.esc_hold_to_navigate():
        text_utils.render_text(
            surface,
            "Hold ESC to leave match",
            (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 2),
            HUD_FONT_SIZE,
            WHITE,
        )
