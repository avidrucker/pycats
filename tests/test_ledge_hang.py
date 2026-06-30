"""Ledge-hang state (#14, v1 slice).

Automatic grab at a solid stage edge -> ledge_hang (timed intangible hang) ->
neutral getup (up) / drop (down or away) / timeout. One-occupant lockout per edge
(no trump). Spec: docs/superpowers/specs/2026-06-30-ledge-hang-design.md.
"""
import pygame

from pycats.entities import Player
from pycats.entities.ledge import Ledge, LEFT, RIGHT, ledges_from_platforms
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats import config


def _thick(x, y, w, h):
    return Platform(pygame.Rect(x, y, w, h), thin=False)


def _thin(x, y, w, h):
    return Platform(pygame.Rect(x, y, w, h), thin=True)


# --- shared scaffolding (verified against tests/test_prone.py) ---------------

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


def _player():
    return Player(200, 200, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True)


def _frame(*keys):
    ks = {_CONTROLS[k] for k in keys}
    return InputFrame(held=set(ks), pressed=set(ks), released=set())


def _empty_frame():
    return _frame()


def _frame_up(p):    return _frame("up")
def _frame_down(p):  return _frame("down")
def _frame_left(p):  return _frame("left")


def p_attack_group():
    return pygame.sprite.Group()


def _stage():
    return [_thick(80, 410, 800, 80)]


# --- Task 1: Ledge value + geometry ------------------------------------------

def test_ledges_from_platforms_only_thick_yields_two_edges():
    plats = [_thick(80, 410, 800, 80), _thin(0, 300, 150, 20)]
    ledges = ledges_from_platforms(plats)
    sides = sorted(l.side for l in ledges)
    assert sides == [LEFT, RIGHT]                 # exactly the thick platform's 2 edges
    left = next(l for l in ledges if l.side == LEFT)
    right = next(l for l in ledges if l.side == RIGHT)
    assert (left.ax, left.ay) == (80, 410)        # top-left corner
    assert (right.ax, right.ay) == (880, 410)     # top-right corner


def test_catch_rect_sits_off_stage_side_and_below_lip():
    left = Ledge(LEFT, 80, 410)
    r = left.catch_rect()
    assert r.right == 80 and r.left == 80 - config.LEDGE_CATCH_W   # left of corner
    assert r.top == 410 and r.height == config.LEDGE_CATCH_H        # lip and below
    right = Ledge(RIGHT, 880, 410)
    rr = right.catch_rect()
    assert rr.left == 880 and rr.width == config.LEDGE_CATCH_W      # right of corner


def test_hang_and_getup_positions_and_facing():
    size = (40, 60)
    left = Ledge(LEFT, 80, 410)
    assert left.facing_right() is True                       # face the stage (right)
    assert left.hang_topleft(size) == (80 - 40, 410)         # body off the left lip
    assert left.getup_topleft(size) == (80, 410 - 60)        # standing on the lip
    right = Ledge(RIGHT, 880, 410)
    assert right.facing_right() is False
    assert right.hang_topleft(size) == (880, 410)
    assert right.getup_topleft(size) == (880 - 40, 410 - 60)


def test_away_held_is_off_stage_direction():
    assert Ledge(LEFT, 80, 410).away_held(left_held=True, right_held=False) is True
    assert Ledge(LEFT, 80, 410).away_held(left_held=False, right_held=True) is False
    assert Ledge(RIGHT, 880, 410).away_held(left_held=False, right_held=True) is True


# --- Task 2: fighter fields + ledge_hang statechart leaf ---------------------

def test_force_ledge_grab_enters_hang_and_exits():
    p = _player()
    p.fighter.grabbed_ledge = object()      # stand-in: "is hanging"
    p.fighter.on_ground = False
    p.engine.force("ledge_grab")
    assert p.state == "ledge_hang"
    p.fighter.grabbed_ledge = None          # release while airborne -> fall
    p.engine.tick(None)
    assert p.state == "fall"


def test_ledge_hang_release_on_ground_goes_idle():
    p = _player()
    p.fighter.grabbed_ledge = object()
    p.fighter.on_ground = False
    p.engine.force("ledge_grab")
    assert p.state == "ledge_hang"
    p.fighter.grabbed_ledge = None
    p.fighter.on_ground = True
    p.engine.tick(None)
    assert p.state == "idle"


def test_fighter_ledge_fields_default():
    p = _player()
    assert p.fighter.grabbed_ledge is None
    assert p.fighter.ledge_hang_timer == 0
    assert p.fighter.ledge_regrab_lockout_timer == 0


# --- Task 3: automatic grab detection ----------------------------------------

def test_descending_into_left_catch_region_grabs():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    p.rect.topleft = (80 - 40, 420)          # body just left of the left lip
    p.fighter.vel.x, p.fighter.vel.y = 0, 5  # descending
    p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p.state == "ledge_hang"
    assert p.fighter.invulnerable is True
    assert p.fighter.ledge_hang_timer == config.LEDGE_HANG_FRAMES
    assert (p.rect.left, p.rect.top) == (40, 410)     # snapped to hang_topleft
    assert any(l.occupied_by is p for l in ledges)


def test_rising_does_not_grab():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    p.rect.topleft = (80 - 40, 420)
    p.fighter.vel.y = -5                     # rising
    p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p.state != "ledge_hang"
    assert p.fighter.grabbed_ledge is None


# --- Task 4: hang getup / drop / timeout + lockout ---------------------------

def _grab_left(p, plats, ledges):
    p.rect.topleft = (80 - 40, 420)
    p.fighter.vel.x, p.fighter.vel.y = 0, 5
    p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p.state == "ledge_hang"


def test_getup_climbs_onto_stage_and_idles():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    _grab_left(p, plats, ledges)
    p.update(_frame_up(p), plats, p_attack_group(), ledges)   # press up -> getup
    assert p.fighter.grabbed_ledge is None
    assert all(l.occupied_by is None for l in ledges)
    assert p.fighter.invulnerable is False
    assert p.state == "idle"


def test_drop_releases_into_fall_with_lockout():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    _grab_left(p, plats, ledges)
    p.update(_frame_down(p), plats, p_attack_group(), ledges)  # press down -> drop
    assert p.fighter.grabbed_ledge is None
    # lockout armed (set to LEDGE_REGRAB_LOCKOUT_FRAMES, then ticked once this same
    # frame); the blocking contract itself is pinned by the regrab test below.
    assert p.fighter.ledge_regrab_lockout_timer > 0
    assert p.state == "fall"


def test_away_also_drops():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    _grab_left(p, plats, ledges)              # LEFT edge -> "away" is left
    p.update(_frame_left(p), plats, p_attack_group(), ledges)
    assert p.fighter.grabbed_ledge is None
    assert p.state == "fall"


def test_timeout_auto_releases():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    _grab_left(p, plats, ledges)
    p.fighter.ledge_hang_timer = 1                              # imminent timeout
    p.update(_empty_frame(), plats, p_attack_group(), ledges)  # tick to 0 -> release
    assert p.fighter.grabbed_ledge is None
    assert p.state == "fall"


def test_regrab_lockout_blocks_immediate_regrab():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    _grab_left(p, plats, ledges)
    p.update(_frame_down(p), plats, p_attack_group(), ledges)   # drop -> lockout armed
    p.rect.topleft = (80 - 40, 420)
    p.fighter.vel.y = 5; p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)   # in region again
    assert p.fighter.grabbed_ledge is None                      # blocked by lockout
