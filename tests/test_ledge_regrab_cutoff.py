"""PM's 5-regrab ledge-intangibility count cutoff (#656, ratified #670).

Anti-plank: grabs 1..5 (consecutive, without touching the ground) grant the full
fixed intangibility burst; grab 6+ grants only a small non-zero PLACEHOLDER residual
(config.LEDGE_POST_CUTOFF_RESIDUAL_FRAMES — an unsourced gap). The consecutive-regrab
count resets on landing on the stage OR on getting hit.

Harness mirrors tests/test_ledge_hang.py.
"""

import pygame

from pycats import config
from pycats.core.input import InputFrame
from pycats.entities import Player
from pycats.entities.ledge import (
    ledge_invuln_frames,
    ledge_regrab_invuln_frames,
    ledges_from_platforms,
)
from pycats.entities.platform import Platform

_CONTROLS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)


def _thick(x, y, w, h):
    return Platform(pygame.Rect(x, y, w, h), thin=False)


def _player():
    return Player(200, 200, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1", facing_right=True)


def _empty_frame():
    return InputFrame(held=set(), pressed=set(), released=set())


def _attacks():
    return pygame.sprite.Group()


def _stage():
    return [_thick(80, 410, 800, 80)]


def _regrab(p, plats, ledges):
    """Force one fresh consecutive ledge grab WITHOUT touching the ground: free any
    current hang + the edges, clear the post-drop lockout, drop the airborne body into
    the left catch region. Leaves on_ground False throughout (no landing between grabs)."""
    p.fighter.grabbed_ledge = None
    for lg in ledges:
        lg.occupied_by = None
    p.fighter.ledge_regrab_lockout_timer = 0
    p.rect.topleft = (80 - 40, 420)  # body just left of the left lip
    p.fighter.vel.x, p.fighter.vel.y = 0, 5  # descending
    p.fighter.on_ground = False
    p.update(_empty_frame(), plats, _attacks(), ledges)
    assert p.state == "ledge_hang"


# --- pure value function: the count -> burst mapping -------------------------


def test_grabs_1_through_5_grant_the_full_burst():
    full = ledge_invuln_frames()
    for n in range(1, config.LEDGE_REGRAB_INVULN_CUTOFF + 1):  # 1..5
        assert ledge_regrab_invuln_frames(n) == full


def test_grab_6_and_beyond_grant_only_the_residual():
    residual = config.LEDGE_POST_CUTOFF_RESIDUAL_FRAMES
    assert ledge_regrab_invuln_frames(6) == residual
    assert ledge_regrab_invuln_frames(9) == residual
    # able-to-fail guard: the residual is a real cut, not accidentally equal to the burst
    assert residual < ledge_invuln_frames()
    assert residual > 0  # non-zero: PM's "a few frames" snap residual, not zero


# --- behavioural: grab site increments + cutoff applies at grant -------------


def test_first_five_regrabs_grant_full_burst_sixth_is_residual():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    full = config.LEDGE_INVULN_BASE_FRAMES
    for n in range(1, 6):  # grabs 1..5
        _regrab(p, plats, ledges)
        assert p.fighter.ledge_regrab_count == n
        assert p.fighter.ledge_invuln_granted == full  # full burst
    _regrab(p, plats, ledges)  # 6th consecutive grab
    assert p.fighter.ledge_regrab_count == 6
    assert p.fighter.ledge_invuln_granted == config.LEDGE_POST_CUTOFF_RESIDUAL_FRAMES  # cut
    assert p.fighter.ledge_invuln_granted < full


# --- reset: landing on the stage ---------------------------------------------


def test_landing_on_the_stage_resets_the_regrab_count():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    for _ in range(3):
        _regrab(p, plats, ledges)
    assert p.fighter.ledge_regrab_count == 3
    # neutral getup climbs onto the stage; when the climb completes the fighter is
    # grounded -> _handle_landing fires -> count resets. Then a fresh grab is grab #1.
    p.update(InputFrame(held={_CONTROLS["up"]}, pressed={_CONTROLS["up"]}, released=set()), plats, _attacks(), ledges)
    for _ in range(config.LEDGE_GETUP_FRAMES + 3):
        p.update(_empty_frame(), plats, _attacks(), ledges)
        if p.state == "idle":
            break
    assert p.state == "idle"  # landed on the stage
    assert p.fighter.on_ground is True
    assert p.fighter.ledge_regrab_count == 0  # touching the stage reset the count
    _regrab(p, plats, ledges)
    assert p.fighter.ledge_regrab_count == 1  # counting starts over
    assert p.fighter.ledge_invuln_granted == config.LEDGE_INVULN_BASE_FRAMES  # full again


# --- reset: getting hit ------------------------------------------------------


def test_getting_hit_resets_the_regrab_count():
    from pycats.combat.data import Circle, Hitbox
    from pycats.entities.attack import Attack

    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    for _ in range(4):
        _regrab(p, plats, ledges)
    assert p.fighter.ledge_regrab_count == 4
    # let the burst lapse so the hit connects (combat skips intangible defenders),
    # then a connecting hit knocks the hanger off AND resets the count.
    for _ in range(config.LEDGE_INVULN_BASE_FRAMES + 1):
        p.update(_empty_frame(), plats, _attacks(), ledges)
    attacker = _player()
    hb = Hitbox(circle=Circle(dx=27, dy=30, r=12), damage=10, angle=0, base_knockback=30.0, knockback_growth=100.0)
    p.fighter.receive_hit(Attack(owner=attacker, hitbox=hb, lifetime=1))
    assert p.fighter.ledge_regrab_count == 0  # getting hit reset the count


def test_regrab_count_defaults_zero():
    assert _player().fighter.ledge_regrab_count == 0
