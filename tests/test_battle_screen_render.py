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
from pycats.config import BG_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT
from pycats.render_battle import (
    render_battle, render_attacks, draw_hud, draw_controls,
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


def test_render_matches_inline_playing_composition():
    """render() == fill(BG) -> render_battle -> render_attacks -> draw_hud x2 ->
    draw_controls x2 (the playing branch's inline block), byte-for-byte."""
    bs = _battle()
    platforms = []

    expected = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    expected.fill(BG_COLOR)
    render_battle(expected, bs.players, platforms)
    render_attacks(expected, bs.attacks)
    draw_hud(expected, bs.player1, "P1")
    draw_hud(expected, bs.player2, "P2", topright=True)
    draw_controls(expected, bs.player1, "P1")
    draw_controls(expected, bs.player2, "P2", topright=True)

    actual = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    actual.fill(_SENTINEL)  # proves render() fills BG over whatever was there
    bs.render(actual, platforms)

    assert _raw(actual) == _raw(expected)


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
