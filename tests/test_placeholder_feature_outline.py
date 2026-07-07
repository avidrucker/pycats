"""The flat-gray placeholder's features read via black outlines (#694, DP1 of #672).

Under DP1 the placeholder / `testcat` cat is flat uniform gray (128,128,128) — body,
stripe and eye are the same colour, so the primitive eyes + stripes vanish by colour.
Legibility is carried by **black outlines** on those features (the #546 outline basis),
drawn in render_battle only when a fighter's features share the body colour.

`testcat` can't be picked in char-select, so it only reaches the render path through
`create_from_selection` with an unknown/testcat key — this harness exercises exactly that.

Able-to-fail: revert the draw_eye/draw_stripes black-outline strokes and the placeholder
body composite has zero pure-black opaque pixels → the placeholder assertion goes red.
Scope guard: a named cat (tabby/calico) has contrasting features, so the same path emits
no black-outline pixels — this stays 0, proving named cats are untouched (byte-identity).
"""

import pygame

from pycats.battle_screen import BattleScreen
from pycats.render_battle import _cat_body_surface

_P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)
_P2 = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_PERIOD,
    special=pygame.K_SLASH,
    shield=pygame.K_RSHIFT,
)


def _black_outline_px(player):
    """Count pure-black opaque pixels in a fighter's composited body surface — the
    feature-outline strokes (nothing else in the composite is opaque (0,0,0))."""
    raw = pygame.image.tobytes(_cat_body_surface(player), "RGBA")
    return sum(
        1 for i in range(0, len(raw), 4) if raw[i] == 0 and raw[i + 1] == 0 and raw[i + 2] == 0 and raw[i + 3] == 255
    )


def _body(p1_char, p2_char):
    pygame.init()
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection(p1_char, p2_char)
    return bs.player1


def test_placeholder_features_have_black_outlines():
    p = _body("testcat", "testcat")
    assert p.char_color == p.eye_color == p.stripe_color == (128, 128, 128), (
        f"harness precondition: placeholder should be flat gray, got {p.char_color}/{p.eye_color}/{p.stripe_color}"
    )
    assert _black_outline_px(p) > 0, "placeholder eyes/stripes must be black-outlined so they read"


def test_named_cat_has_no_placeholder_outline():
    # Named cats have contrasting features → the outline never fires → composite has no
    # pure-black opaque pixels. Guards that #694 does not restyle the named roster.
    assert _black_outline_px(_body("tabby", "calico")) == 0
