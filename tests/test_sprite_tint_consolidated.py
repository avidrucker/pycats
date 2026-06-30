"""#109 — the hurt/stun/dodge flash must cover the WHOLE cat (body, stripes,
ears, whiskers, tail), at ~50% strength, from a single source of truth.

Bug being guarded:
  - ears (`draw_cat_features`) and tail (`tail.draw`) used raw `char_color`, so
    only the torso flashed — the cat looked half-tinted.
  - the body fill fully replaced the colour (solid RED/YELLOW/WHITE), too strong.

The fix introduces `render_battle.tinted(base, p)` (a 50% blend toward the active
flash colour, or the base unchanged when no hurt/stun/dodge timer is live) and
routes every part through it. `body_tint` (#75) is unchanged — it still returns
the overlay colour RED/YELLOW/WHITE / char_color — these tests are about the new
blended per-part consumption.

Revert-the-fix checks:
  - drop the blend (return the solid overlay) → the 50% value assertions go red.
  - draw ears/tail with raw `char_color` again → the "no untinted char_color part
    survives a hurt flash" pixel-count assertions go red (the ear/tail pixels
    stay exactly char_color).
"""
import pytest
import pygame as pg

from pycats import cat_faces
from pycats import render_battle as rb
from pycats.entities.player import Player
from pycats.config import WHITE, RED, YELLOW

pytestmark = pytest.mark.usefixtures("render_isolation")

# A char_color that is none of RED/YELLOW/WHITE and survives a 50% blend as a
# clearly different colour, so an exact-match pixel count cleanly separates
# "untinted" from "tinted" regions.
C = (10, 200, 30)

CONTROLS = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
            "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _mk(hurt=0, stun=0, dodge=0):
    p = Player(x=100, y=100, controls=CONTROLS, color=C, eye_color=(0, 0, 200),
               char_name="P1", facing_right=True)
    p.fighter.hurt_timer = hurt
    p.fighter.stun_timer = stun
    p.fighter.dodge_timer = dodge
    return p


def _blend50(base, overlay):
    return tuple(round(b + (o - b) * 0.5) for b, o in zip(base, overlay))


def _count_exact(surf, rgb):
    """Number of fully-opaque pixels exactly equal to `rgb` in `surf`."""
    data = pg.image.tobytes(surf, "RGBA")
    target = bytes((*rgb, 255))
    return sum(1 for i in range(0, len(data), 4) if data[i:i + 4] == target)


# --- the pure tint helper -----------------------------------------------------

def test_tinted_is_identity_when_no_timer_is_live():
    p = _mk()
    assert tuple(rb.tinted(C, p)) == C


def test_tinted_blends_50pct_toward_red_when_hurt():
    p = _mk(hurt=1)
    assert tuple(rb.tinted(C, p)) == _blend50(C, RED)


def test_tinted_blends_50pct_toward_yellow_when_stunned():
    p = _mk(stun=1)
    assert tuple(rb.tinted(C, p)) == _blend50(C, YELLOW)


def test_tinted_blends_50pct_toward_white_when_dodging():
    p = _mk(dodge=1)
    assert tuple(rb.tinted(C, p)) == _blend50(C, WHITE)


def test_tinted_is_a_softened_blend_not_a_solid_replace():
    # The whole point of "soften to ~50%": a hurt body must NOT read solid RED.
    p = _mk(hurt=1)
    assert tuple(rb.tinted(C, p)) != tuple(RED)


def test_body_tint_75_contract_is_unchanged():
    # #75: body_tint stays the overlay selector (solid RED / char_color), the
    # blend lives in `tinted`. Guards against accidentally moving the blend here.
    assert rb.body_tint(_mk(hurt=1)) == RED
    assert tuple(rb.body_tint(_mk())) == C


# --- whole-sprite composite: body + ears + stripes all flash ------------------

def test_hurt_flash_leaves_no_untinted_char_color_in_the_body_composite():
    normal = rb._cat_body_surface(_mk(), cat_faces.PRIMITIVES)
    assert _count_exact(normal, C) > 0, "setup: body/ears/stripes paint char_color when calm"

    hurt = rb._cat_body_surface(_mk(hurt=1), cat_faces.PRIMITIVES)
    # Every char_color part (body fill + ears + stripes) blends away — if the
    # ears still drew raw char_color (the bug), this count would be > 0.
    assert _count_exact(hurt, C) == 0, "a part kept raw char_color through the hurt flash"


def test_stun_and_dodge_also_clear_raw_char_color_from_the_composite():
    for kw in (dict(stun=1), dict(dodge=1)):
        surf = rb._cat_body_surface(_mk(**kw), cat_faces.PRIMITIVES)
        assert _count_exact(surf, C) == 0, f"{kw} flash left an untinted char_color part"


# --- the tail flashes too -----------------------------------------------------

def _draw_tail(p):
    surf = pg.Surface((300, 300), pg.SRCALPHA)
    # #265: the caller resolves the tint (was computed inside Tail.draw); this
    # mirrors render_battle's call site so the test still exercises the flash.
    p.tail.draw(surf, rb.tinted(p.char_color, p))
    return surf


def test_tail_flashes_with_the_body_when_hurt():
    calm = _draw_tail(_mk())
    assert _count_exact(calm, C) > 0, "setup: the calm tail is drawn in char_color"

    hurt = _draw_tail(_mk(hurt=1))
    assert _count_exact(hurt, C) == 0, "the tail kept raw char_color through the hurt flash"
