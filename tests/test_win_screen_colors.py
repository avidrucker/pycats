"""Win-screen player-color test (#726).

Each player's stats column is painted in that player's slot accent color
(P1_UI_COLOR / P2_UI_COLOR — the same colors the confirmation boxes already use),
and the "<name> Wins!" banner is painted in the *winning* player's slot color.

Able-to-fail: before #726 every line rendered in the flat WIN_SCREEN_TEXT_COLOR,
so the banner and both columns were white — the color assertions below are red.
"""

import pygame  # noqa: E402  (must follow the dummy-driver env setup)
import pytest  # noqa: E402

from pycats import text_utils  # noqa: E402
from pycats.config import P1_UI_COLOR, P2_UI_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.domain import PlayerIdentity, PlayerName, PlayerNumberSlot, PlayerTeamColor  # noqa: E402
from pycats.win_screen import WinScreenManager  # noqa: E402

pytestmark = pytest.mark.usefixtures("render_isolation")


class _FakePlayer:
    def __init__(self, char_name, lives=1, suicides=0):
        self.char_name = char_name
        _n = 1 if char_name == "P1" else 2
        self.identity = PlayerIdentity(
            PlayerNumberSlot(_n), PlayerTeamColor.RED if _n == 1 else PlayerTeamColor.BLUE, PlayerName(char_name)
        )
        self.lives = lives
        self.suicides = suicides
        self.hits_landed = 7
        self.attacks_made = 20
        self.damage_given = 100.0
        self.damage_taken = 50.0
        self.fighter = self


def _record_draws(render_call):
    """Spy every text draw, returning ``(text, color_tuple, x)`` per draw."""
    drawn = []
    orig = text_utils.render_text
    orig_mixed = text_utils.text_renderer.render_text_mixed

    def spy(surface, text, position, size, color, center=False, right_align=False):
        drawn.append((text, tuple(color), position[0]))
        return orig(surface, text, position, size, color, center=center, right_align=right_align)

    def spy_mixed(text, size, color, surface, position, center=False):
        drawn.append((text, tuple(color), position[0]))
        return orig_mixed(text, size, color, surface, position, center=center)

    text_utils.render_text = spy
    text_utils.text_renderer.render_text_mixed = spy_mixed
    try:
        render_call()
    finally:
        text_utils.render_text = orig
        text_utils.text_renderer.render_text_mixed = orig_mixed
    return drawn


def _render(winner, loser):
    ws = WinScreenManager({"attack": 1, "special": 2}, {"attack": 3, "special": 4})
    ws.set_match_data(winner, loser)
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    return _record_draws(lambda: ws.render(surface))


def test_winner_banner_painted_in_winner_slot_color():
    p1_wins = [c for (t, c, _x) in _render(_FakePlayer("P1"), _FakePlayer("P2")) if t.endswith("Wins!")]
    assert p1_wins, "no winner banner drawn"
    assert p1_wins[0] == P1_UI_COLOR, f"P1 win banner should be P1 color, got {p1_wins[0]}"

    p2_wins = [c for (t, c, _x) in _render(_FakePlayer("P2"), _FakePlayer("P1")) if t.endswith("Wins!")]
    assert p2_wins[0] == P2_UI_COLOR, f"P2 win banner should be P2 color, got {p2_wins[0]}"


def test_stats_columns_painted_in_player_colors():
    draws = _render(_FakePlayer("P1"), _FakePlayer("P2"))

    p1_hdr = [(c, x) for (t, c, x) in draws if t == "P1"]
    p2_hdr = [(c, x) for (t, c, x) in draws if t == "P2"]
    assert p1_hdr and p2_hdr, "P1/P2 column headers not found"
    p1_color, p1_x = p1_hdr[0]
    p2_color, p2_x = p2_hdr[0]
    assert p1_color == P1_UI_COLOR, f"P1 header should be P1 color, got {p1_color}"
    assert p2_color == P2_UI_COLOR, f"P2 header should be P2 color, got {p2_color}"

    # Every value cell in a column shares that column's x → must be that player's color.
    p1_col = [c for (_t, c, x) in draws if x == p1_x]
    p2_col = [c for (_t, c, x) in draws if x == p2_x]
    assert all(c == P1_UI_COLOR for c in p1_col), f"P1 column not all P1 color: {p1_col}"
    assert all(c == P2_UI_COLOR for c in p2_col), f"P2 column not all P2 color: {p2_col}"
