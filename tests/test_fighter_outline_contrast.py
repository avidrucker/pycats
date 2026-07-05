"""#546: fighters carry a thin light outline so a body whose luminance sits near
the dark stage bg (P2 gray ~1.6:1; the tabby / void skins ~2.8 / ~1.7:1) stays
separable from the stage. The outline is the separator, so its contrast vs
``BG_COLOR`` is what must clear the WCAG large-object target (>= 3:1) — and it is
actually painted on the rendered body edge.

The outline approach (not a P2 recolor) is the ticket's preferred path: it needs
no P2-identity game-designer decision, and it is skin-independent — it helps every
low-luminance skin, not just the legacy P2_COLOR.
"""
import pygame

from pycats.battle_screen import BattleScreen
from pycats.config import BG_COLOR, FIGHTER_OUTLINE_COLOR, FIGHTER_OUTLINE_WIDTH
from pycats.render_battle import _BODY_PAD_TOP, _BODY_PAD_X, _cat_body_surface

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(color):
    r, g, b = color[:3]
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def _wcag_ratio(a, b):
    """WCAG 2.x relative-luminance contrast ratio between two RGB colours."""
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _dark_body():
    """A rendered body surface for the gray 'tabby' skin (2.76:1 vs bg — one of
    the low-contrast skins the outline is meant to rescue)."""
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("tabby", "void")
    return bs.player1, _cat_body_surface(bs.player1)


def test_outline_clears_large_object_target_vs_bg():
    """The separator (outline) must clear WCAG's >= 3:1 large-object target vs the
    stage bg — the measurable acceptance for #546."""
    ratio = _wcag_ratio(FIGHTER_OUTLINE_COLOR, BG_COLOR)
    assert ratio >= 3.0, f"outline vs BG_COLOR is only {ratio:.2f}:1 (< 3:1)"


def test_low_contrast_skins_are_the_ones_that_needed_it():
    """Guard the premise: the gray/black skin bodies really do sit below 3:1 vs the
    bg (so the outline is load-bearing, not decorative). If a future palette change
    lifts them clear, this flags that the outline's justification shifted."""
    for skin in ((128, 128, 128), (20, 20, 20)):  # tabby, void bodies
        assert _wcag_ratio(skin, BG_COLOR) < 3.0


def test_outline_is_painted_just_outside_the_body_silhouette():
    """The outline is actually drawn — now *outside* the silhouette, behind the
    sprite (#564 moved it off the body edge). The body edge itself is the sprite's
    own fill; the ring sits one px beyond it. Able-to-fail: drop the outline and
    the just-outside pixel reverts to transparent. (Where the outline lives is
    covered in depth by test_fighter_silhouette_outline.py.)"""
    player, surf = _dark_body()
    w, h = player.fighter.stand_size
    edge = surf.get_at((_BODY_PAD_X, _BODY_PAD_TOP + h // 2))
    just_outside = surf.get_at((_BODY_PAD_X - 1, _BODY_PAD_TOP + h // 2))
    assert tuple(edge)[:3] != FIGHTER_OUTLINE_COLOR  # body edge is the sprite, not the ring
    assert tuple(just_outside)[:3] == FIGHTER_OUTLINE_COLOR  # ring hugs the silhouette


def test_outline_width_is_thin():
    """A 'thin' outline per the ticket — a couple of px, not a heavy frame."""
    assert 1 <= FIGHTER_OUTLINE_WIDTH <= 3
