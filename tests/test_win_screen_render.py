"""#728 — the win screen renders both fighters as portraits.

Invariants (the design ruling on #738, research #736):
  * seat-fixed horizontal slots — P1 always left, P2 always right, keyed off
    ``identity.number``, NOT winner/loser;
  * the winner is drawn visually higher (smaller ``y``) than the loser;
  * the tails are live-animated (they move frame-to-frame).

Able-to-fail: before #728 ``WinScreenManager.render`` drew only text/stats and
exposed no ``cat_portraits`` seam, so every assertion below is red (no cats, no
tail motion). The manager stores each cat's on-screen body rect in
``self.cat_portraits`` keyed by seat number, which is the testable seam.
"""

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats.config import P1_COLOR, P2_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE  # noqa: E402
from pycats.entities.player import Player  # noqa: E402
from pycats.win_screen import WinScreenManager  # noqa: E402

pytestmark = pytest.mark.usefixtures("render_isolation")

_CONTROLS = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "up": pygame.K_w,
    "down": pygame.K_s,
    "shield": pygame.K_q,
    "attack": pygame.K_e,
    "special": pygame.K_r,
}


def _player(char_name, facing_right):
    color = P1_COLOR if char_name == "P1" else P2_COLOR
    return Player(
        x=200,
        y=200,
        controls=_CONTROLS,
        color=color,
        eye_color=WHITE,
        char_name=char_name,
        facing_right=facing_right,
    )


def _render(winner, loser):
    ws = WinScreenManager(_CONTROLS, _CONTROLS)
    ws.set_match_data(winner, loser)
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    ws.render(surface)
    return ws, surface


def test_p1_left_p2_right_regardless_of_who_won():
    # P1 wins
    ws, _ = _render(winner=_player("P1", True), loser=_player("P2", False))
    assert ws.cat_portraits[1]["rect"].centerx < SCREEN_WIDTH / 2, "P1 must be in the left half"
    assert ws.cat_portraits[2]["rect"].centerx > SCREEN_WIDTH / 2, "P2 must be in the right half"

    # P2 wins — the seat slots must NOT swap with the outcome
    ws2, _ = _render(winner=_player("P2", False), loser=_player("P1", True))
    assert ws2.cat_portraits[1]["rect"].centerx < SCREEN_WIDTH / 2, "P1 stays left even when P2 wins"
    assert ws2.cat_portraits[2]["rect"].centerx > SCREEN_WIDTH / 2, "P2 stays right even when it wins"


def test_winner_drawn_higher_than_loser_both_ways():
    # P1 wins → seat 1 is the winner and sits higher
    ws, _ = _render(winner=_player("P1", True), loser=_player("P2", False))
    assert ws.cat_portraits[1]["is_winner"] is True
    assert ws.cat_portraits[2]["is_winner"] is False
    assert ws.cat_portraits[1]["rect"].top < ws.cat_portraits[2]["rect"].top

    # P2 wins → seat 2 is the winner and sits higher
    ws2, _ = _render(winner=_player("P2", False), loser=_player("P1", True))
    assert ws2.cat_portraits[2]["is_winner"] is True
    assert ws2.cat_portraits[2]["rect"].top < ws2.cat_portraits[1]["rect"].top


def test_tails_animate_across_frames():
    winner, loser = _player("P1", True), _player("P2", False)
    ws = WinScreenManager(_CONTROLS, _CONTROLS)
    ws.set_match_data(winner, loser)
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    ws.render(surface)
    before = [(s.x, s.y) for s in winner.tail.segments]
    for _ in range(3):
        ws.render(surface)
    after = [(s.x, s.y) for s in winner.tail.segments]
    assert before != after, "the tail must animate live across frames"


def test_render_is_calm_no_crash_with_live_hurt_tint():
    # A just-KO'd loser can carry a live hurt/stun tint; the portrait must render
    # calm (tint forced off) and must not crash. We assert it renders + records
    # both portraits regardless of the incoming timer state.
    winner, loser = _player("P1", True), _player("P2", False)
    loser.fighter.hurt_timer = 30  # live hurt flash at match end
    winner.fighter.stun_timer = 20
    ws, _ = _render(winner=winner, loser=loser)
    assert set(ws.cat_portraits.keys()) == {1, 2}
    # timers restored (render must not leave the live fighters mutated)
    assert loser.fighter.hurt_timer == 30
    assert winner.fighter.stun_timer == 20
