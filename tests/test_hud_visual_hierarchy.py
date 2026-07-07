"""#550: HUD visual hierarchy — the two numbers players read constantly (Damage %
and Lives) are emphasized (larger, anchored in the bottom corners), while the rest
of the stats stay grouped at the top at the standard size.

Guards the acceptance criteria:
- the emphasized rows render LARGER than the secondary rows and DISTINCT in position;
- the emphasized size flows through the live ``font_scale`` (it is not a fixed literal),
  so the ``large`` preset grows the rows — able-to-fail.

The emphasized block is drawn by ``draw_hud_emphasis`` (split from ``draw_hud``'s
secondary loop, #550), so a rendered pixel bbox isolates it cleanly.
"""
import pygame
import pytest

from pycats import runtime_settings, settings, text_utils
from pycats.battle_screen import BattleScreen
from pycats.config import (
    HUD_EMPHASIS_SIZE,
    HUD_PADDING,
    HUD_SPACING,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from pycats.render_battle import (
    HUD_FONT_SIZE,
    HUD_PLAYER_LINE_COUNT,
    draw_hud,
    draw_hud_emphasis,
    emphasis_row_y,
    hud_emphasis_rows,
)

# Re-init font + clear stale render/font caches before each test (#63) so a scale
# change in one test can't leave a cached glyph behind for the next.
pytestmark = pytest.mark.usefixtures("render_isolation")

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)

_BLACK = (0, 0, 0)


def _player():
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("tabby", "calico")
    return bs.player1


def _text_bbox(draw):
    """Bounding rect over the white HUD text `draw` paints on a black surface.
    A black colorkey makes get_bounding_rect ignore the background."""
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surf.fill(_BLACK)
    draw(surf)
    surf.set_colorkey(_BLACK)
    return surf.get_bounding_rect()


def test_emphasized_rows_render_larger_than_secondary():
    """Damage %/Lives use a bigger font than the secondary rows — both as the
    source-of-truth constant and as taller rendered glyphs at the standard scale."""
    runtime_settings.seed(settings.defaults())  # standard scale (identity)
    assert HUD_EMPHASIS_SIZE > HUD_FONT_SIZE

    big = text_utils.text_renderer._get_font(None, HUD_EMPHASIS_SIZE).get_height()
    small = text_utils.text_renderer._get_font(None, HUD_FONT_SIZE).get_height()
    assert big > small, "emphasized rows must render taller glyphs than the secondary rows"


def test_emphasized_rows_anchored_bottom_distinct_from_secondary():
    """The emphasized block sits in the bottom region, below where the top-anchored
    secondary group ends — the two groups are distinct in position (#550)."""
    runtime_settings.seed(settings.defaults())
    p = _player()

    emph = _text_bbox(lambda s: draw_hud_emphasis(s, p))
    full = _text_bbox(lambda s: draw_hud(s, p, "P1"))

    # the top-anchored secondary group ends here (label + jumps + Shield HP)
    secondary_bottom = HUD_PADDING + HUD_PLAYER_LINE_COUNT * HUD_SPACING

    assert full.top <= HUD_PADDING + 2, "secondary group must be anchored at the top"
    assert emph.top > secondary_bottom, "emphasized block must be below the secondary group"
    assert emph.top > SCREEN_HEIGHT // 2, "emphasized block must be in the bottom half"


def test_emphasized_block_clears_pause_hint():
    """The P2 (bottom-right) emphasized rows share the bottom-right corner with the
    'P: Pause Game' hint (draw_pause_hint, at SCREEN_HEIGHT - HUD_SPACING*3). The
    block is lifted so the lowest emphasized row's bottom stays above that line —
    no overlap. Able-to-fail: drop the lift and the rows collide with the hint."""
    n = len(hud_emphasis_rows(_player()))
    lowest_row_bottom = emphasis_row_y(n - 1, n) + HUD_EMPHASIS_SIZE
    pause_hint_top = SCREEN_HEIGHT - HUD_SPACING * 3
    assert lowest_row_bottom <= pause_hint_top


def test_emphasized_size_scales_with_font_scale():
    """The emphasized rows grow with the live font_scale — the size routes through
    scaled_font_size, not a fixed literal. Able-to-fail: render the emphasized rows
    at a hardcoded size and the 'large' preset would not enlarge them."""
    p = _player()

    runtime_settings.seed(settings.defaults())  # standard 1.0
    std = _text_bbox(lambda s: draw_hud_emphasis(s, p))

    runtime_settings.set("font_scale", "large")  # 2.0
    large = _text_bbox(lambda s: draw_hud_emphasis(s, p))

    assert large.height > std.height, (
        "emphasized rows must grow with font_scale (size must flow through "
        "scaled_font_size, not be a fixed literal)"
    )
