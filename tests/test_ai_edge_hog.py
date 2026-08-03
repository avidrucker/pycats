"""AI edge-hog — slice 1 of #312 (#404).

A high-level bot contests the ledge against a recovering opponent: when the
opponent is airborne off-stage past a near ledge, the bot goes to that ledge, and
if it is already hanging there it HOLDS (deny via the one-occupant lockout, #14/
#311) instead of getting up. Off by default → level-less/low never edge-hog
(golden-safe). Deliberately imperfect (the PM CPU weakness, #251 Q4).
"""

import random
import types

import pygame as pg

from pycats.core.geometry import FrozenRect
from pycats.entities.ledge import Ledge
from pycats.sim.controllers import EDGE_HOG_RANGE, AttackerController

pg.init()

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}


def _stub(cx, cy, alive=True, on_ground=True, grabbed_ledge=None, current_move=None, move_frame=0, state="idle"):
    # #475: the deny is now bounded by the controller's own _hog_frames counter (no
    # engine hang timer). A fresh controller starts at 0, so its first hang frames HOLD.
    s = types.SimpleNamespace()
    s.rect = FrozenRect(0, 0, 40, 60)
    s.rect = s.rect.with_center((cx, cy))
    s.fighter = types.SimpleNamespace(
        is_alive=alive, on_ground=on_ground, hurt_timer=0, stun_timer=0, grabbed_ledge=grabbed_ledge
    )
    s.controls = _CTRL
    s.current_move = current_move
    s.move_frame = move_frame
    s.state = state
    return s


def _hogger(**kw):
    # level 7 => level>=5 (the getup/hold branch is live). #960/#942 D4 reverted
    # edge_hog off at every level, so force the dormant flag on to exercise the
    # still-present machinery (epic #952 rebuilds intentional edgehogging on it).
    c = AttackerController(attacker_num=1, level=7, rng=random.Random(0), **kw)
    c.edge_hog = True
    return c


_LEFT = Ledge("left", ax=60, ay=300)  # off-stage is x < 60
_RIGHT = Ledge("right", ax=560, ay=300)  # off-stage is x > 560


# ---- detection (pure) -------------------------------------------------------


def test_edge_hog_target_detects_a_recovering_opponent():
    c = _hogger()
    a = _stub(100, 300)
    # opponent airborne + off-stage past the LEFT ledge (x=30 < ax=60)
    off = _stub(30, 320, on_ground=False)
    assert c._edge_hog_target(a, off, [_LEFT]) is _LEFT
    # on the stage (on_ground) => not recovering => no target
    on = _stub(30, 320, on_ground=True)
    assert c._edge_hog_target(a, on, [_LEFT]) is None
    # airborne but still inbounds (x=200 > ax=60) => not off-stage on the left
    inbounds = _stub(200, 320, on_ground=False)
    assert c._edge_hog_target(a, inbounds, [_LEFT]) is None
    # no ledges => None (golden-safe)
    assert c._edge_hog_target(a, off, None) is None


def test_target_skips_a_ledge_the_bot_already_holds():
    c = _hogger()
    a = _stub(60, 300)
    held = Ledge("left", ax=60, ay=300)
    held.occupied_by = a
    off = _stub(30, 320, on_ground=False)
    assert c._edge_hog_target(a, off, [held]) is None


# ---- go to the ledge --------------------------------------------------------


def test_goes_toward_the_ledge_when_near_the_edge():
    c = _hogger()
    a = _stub(100, 300)  # on-stage, within EDGE_HOG_RANGE of ax=60
    off = _stub(30, 320, on_ground=False)  # opponent recovering off-stage left
    assert c.decide(a, off, 0, None, [_LEFT]) == {_CTRL["left"]}  # toward ax<cx


def test_does_not_commit_off_stage_from_mid_stage():
    # Too far from the edge: the edge-hog branch is inert, so passing ledges gives
    # the same decision as no ledges (two fresh, identically-seeded controllers).
    a = _stub(60 + EDGE_HOG_RANGE + 50, 300)
    off = _stub(30, 320, on_ground=False)
    assert _hogger().decide(a, off, 0, None, [_LEFT]) == _hogger().decide(a, off, 0, None, None)


# ---- hold the hang to deny --------------------------------------------------


def test_holds_the_hang_to_deny_a_recovering_opponent():
    c = _hogger()
    a = _stub(48, 300, grabbed_ledge=_LEFT)  # bot hanging on the left ledge
    off = _stub(30, 320, on_ground=False)  # opponent still recovering off-stage left
    assert c.decide(a, off, 0, None, [_LEFT]) == set()  # HOLD, no getup


def test_gets_up_normally_when_no_one_is_being_denied():
    c = _hogger()
    a = _stub(48, 300, grabbed_ledge=_LEFT)
    safe = _stub(200, 300, on_ground=True)  # opponent back on stage => no deny
    assert c.decide(a, safe, 0, None, [_LEFT]) == {_CTRL["up"]}  # getup (#291)


# ---- golden-safety ----------------------------------------------------------


def _low():
    return AttackerController(attacker_num=1, level=3, rng=random.Random(0))


def test_non_edge_hog_level_ignores_ledges():
    # A low level (edge_hog=False) never evaluates the edge-hog branch: passing
    # ledges must not change its decision vs no ledges (two fresh identical bots).
    a = _stub(100, 300)
    off = _stub(30, 320, on_ground=False)
    assert _low().decide(a, off, 0, None, [_LEFT]) == _low().decide(a, off, 0, None, None)


def _default():
    return AttackerController(attacker_num=1, rng=random.Random(0))  # level=None


def test_level_less_default_controller_unaffected_by_ledges():
    # The sim/golden path uses a level-less controller (edge_hog=False). Passing
    # ledges must never change its output — the golden-safety guarantee.
    a = _stub(100, 300)
    off = _stub(30, 320, on_ground=False)
    assert _default().decide(a, off, 0, None, [_LEFT]) == _default().decide(a, off, 0, None, None)
