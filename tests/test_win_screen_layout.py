"""Layout regression test for the win screen (issue #11).

Adding the KOs and Falls rows made the stats table two rows taller. The screen
is a fixed 960x540, so the table plus the confirmation instructions underneath
it must still fit — otherwise the "Press A to confirm" line and the P1/P2 status
indicator render off the bottom edge and the player can't tell what to press.

This renders the real win screen onto a screen-sized surface and asserts every
piece of drawn text stays within ``SCREEN_HEIGHT``. It is red with the extra
rows but the original (too-large) section spacing, green once the spacing is
tightened.
"""



import pygame  # noqa: E402  (must follow the dummy-driver env setup)
import pytest  # noqa: E402

from pycats import text_utils  # noqa: E402
from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.domain import PlayerIdentity, PlayerName, PlayerNumberSlot, PlayerTeamColor  # noqa: E402
from pycats.win_screen import WinScreenManager  # noqa: E402

# Reuse the suite's font-cache isolation so this passes regardless of order (#63).
pytestmark = pytest.mark.usefixtures("render_isolation")


class _FakePlayer:
    def __init__(self, char_name, lives, suicides):
        self.char_name = char_name
        _n = 1 if char_name == "P1" else 2
        self.identity = PlayerIdentity(
            PlayerNumberSlot(_n), PlayerTeamColor.RED if _n == 1 else PlayerTeamColor.BLUE, PlayerName(char_name)
        )
        self.lives = lives
        self.suicides = suicides
        self.hits_landed = 7
        self.attacks_made = 20
        # Wide three-digit values exercise the worst-case row width/height.
        self.damage_given = 312.0
        self.damage_taken = 188.0
        self.fighter = self


def _record_text_ys(render_call):
    """Render via ``render_call`` while spying on every text draw.

    Returns a list of ``(center_y, font_size)`` for each piece of text drawn,
    covering both the plain ``render_text`` path and the mixed Unicode renderer
    used for the P1/P2 status line.
    """
    drawn = []
    orig = text_utils.render_text
    orig_mixed = text_utils.text_renderer.render_text_mixed

    def spy(surface, text, position, size, color, center=False, right_align=False):
        drawn.append((position[1], size))
        return orig(surface, text, position, size, color,
                    center=center, right_align=right_align)

    def spy_mixed(text, size, color, surface, position, center=False):
        drawn.append((position[1], size))
        return orig_mixed(text, size, color, surface, position, center=center)

    text_utils.render_text = spy
    text_utils.text_renderer.render_text_mixed = spy_mixed
    try:
        render_call()
    finally:
        text_utils.render_text = orig
        text_utils.text_renderer.render_text_mixed = orig_mixed
    return drawn


def test_all_win_screen_text_fits_on_screen():
    ws = WinScreenManager({"attack": 1, "special": 2}, {"attack": 3, "special": 4})
    # A match with a suicide so the full six-row table (incl. KOs/Falls) renders.
    ws.set_match_data(_FakePlayer("P1", 2, 0), _FakePlayer("P2", 0, 1))
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    drawn = _record_text_ys(lambda: ws.render(surface))

    # Text is center-anchored, so its lowest pixel is ~ center_y + size/2.
    overflowing = [(y, s) for (y, s) in drawn if y + s / 2 > SCREEN_HEIGHT]
    assert not overflowing, (
        f"win-screen text runs past the {SCREEN_HEIGHT}px bottom edge: "
        f"{overflowing}"
    )
