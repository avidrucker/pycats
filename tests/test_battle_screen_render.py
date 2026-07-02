"""BattleScreen render — slice 2b of #100 (#205).

Parity oracle for the render extraction: BattleScreen.render / render_paused must
produce a surface byte-identical to the inline composition game.py's loop used.
Render is NOT golden-covered (goldens run sim/runner.py, no render path), so this
parity test is the real divergence guard — the render analogue of slice 2's
test_battle_screen_step_matches_runner_sim_path.

draw_hud / draw_controls are imported from pycats.render_battle (their slice-2b
home, beside their sibling drawers render_battle / render_attacks).
"""
import pygame

from pycats.battle_screen import BattleScreen
from pycats.config import (
    BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, HUD_PADDING, HUD_SPACING, WHITE,
)
from pycats import runtime_settings, settings, text_utils
from pycats.render_battle import (
    render_battle, render_attacks, render_hitbox_overlay, draw_hud, draw_controls,
    draw_input_history,
)

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)

_SENTINEL = (1, 2, 3)  # != BG_COLOR and != any fighter color; render() must paint over it


def _raw(surface):
    return pygame.image.tobytes(surface, "RGBA")


def _battle():
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("tabby", "calico")
    return bs


def _draw_pause_hint(surface):
    """The static 'P: Pause Game' battle-HUD hint (#279 moved it into render())."""
    text_utils.render_text(
        surface, "P: Pause Game",
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 3), 24, WHITE,
        right_align=True,
    )


def test_render_matches_inline_playing_composition():
    """render() == fill(BG) -> render_battle -> render_attacks ->
    render_hitbox_overlay -> draw_hud x2 -> draw_controls x2 ->
    draw_input_history x2 -> pause hint (the playing branch's inline block),
    byte-for-byte. The input-history strip (#21) is default-ON, so it's part of
    the composite; the 'P: Pause Game' hint is part of render() (battle HUD,
    #279) — the FPS/fullscreen/debug shell overlays moved to draw_shell_chrome
    (see test_shell_chrome)."""
    runtime_settings.seed(settings.defaults())  # input-history strip default ON (#21)
    bs = _battle()
    platforms = []

    expected = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    expected.fill(BG_COLOR)
    render_battle(expected, bs.players, platforms)
    render_attacks(expected, bs.attacks)
    render_hitbox_overlay(expected, bs.players, bs.attacks)  # #219 debug overlay
    draw_hud(expected, bs.player1, "P1")
    draw_hud(expected, bs.player2, "P2", topright=True)
    draw_controls(expected, bs.player1, "P1")
    draw_controls(expected, bs.player2, "P2", topright=True)
    draw_input_history(expected, bs.p1_history, "P1")  # #21 default-ON strip
    draw_input_history(expected, bs.p2_history, "P2", topright=True)
    _draw_pause_hint(expected)

    actual = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    actual.fill(_SENTINEL)  # proves render() fills BG over whatever was there
    bs.render(actual, platforms)

    assert _raw(actual) == _raw(expected)


def test_render_paused_excludes_pause_hint():
    """render_paused()'s frozen-battle background must NOT carry the 'P: Pause Game'
    hint — you can't pause while already paused. Guards the #279 move: the hint went
    into render() (playing only), not into the shared _draw_battle path."""
    bs = _battle()
    platforms = []

    # background WITHOUT the pause hint (what render_paused should composite)
    bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg.fill(BG_COLOR)
    render_battle(bg, bs.players, platforms)
    render_attacks(bg, bs.attacks)
    render_hitbox_overlay(bg, bs.players, bs.attacks)
    draw_hud(bg, bs.player1, "P1")
    draw_hud(bg, bs.player2, "P2", topright=True)

    captured = {}

    class _FakePauseMenu:
        def render(self, surface, background):
            captured["background"] = background

    display = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bs.render_paused(display, platforms, _FakePauseMenu())
    assert _raw(captured["background"]) == _raw(bg)


def test_render_paused_freezes_battle_onto_intermediate_background():
    """render_paused() composites the frozen battle + HUD (no controls) onto an
    INTERMEDIATE background surface, then delegates to pause_menu.render(surface,
    background) — matching game.py's pause branch."""
    bs = _battle()
    platforms = []

    expected_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    expected_bg.fill(BG_COLOR)
    render_battle(expected_bg, bs.players, platforms)
    render_attacks(expected_bg, bs.attacks)
    render_hitbox_overlay(expected_bg, bs.players, bs.attacks)  # #219 debug overlay
    draw_hud(expected_bg, bs.player1, "P1")
    draw_hud(expected_bg, bs.player2, "P2", topright=True)

    captured = {}

    class _FakePauseMenu:
        def render(self, surface, background):
            captured["surface"] = surface
            captured["background"] = background

    display = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    display.fill(_SENTINEL)
    bs.render_paused(display, platforms, _FakePauseMenu())

    # the display surface is handed straight through (not drawn onto by render_paused)
    assert captured["surface"] is display
    # the frozen battle was composited onto a SEPARATE intermediate surface
    assert captured["background"] is not display
    assert _raw(captured["background"]) == _raw(expected_bg)
