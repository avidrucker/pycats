"""#960 — revert CPU edge-hog to canon (no edgehog at Lv7/Lv9).

#942 D4 / ADR-0010: V1 reverts pycats' edge-hog (#404) to documented canon — a
leveled CPU never leaves the stage to contest/grab a ledge (SmashWiki flaws table,
#928 Axis 6). The revert is *behavioral only*: `edge_hog` is dropped from every
`LEVEL_PARAMS` anchor so no level enables it, but the machinery (`edge_hog` flag,
`_edge_hog_target`, the `decide` branch) is left dormant for epic #952 to rebuild
intentional edgehogging on. `edge_guard` (the on-stage poke, #413) is untouched.
"""

import random
import types

import pygame as pg

from pycats.entities.ledge import Ledge
from pycats.sim.controllers import EDGE_HOG_RANGE, AttackerController, level_params

pg.init()

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}
_LEFT = Ledge("left", ax=60, ay=300)  # off-stage is x < 60


def _stub(cx, cy, on_ground=True, grabbed_ledge=None):
    s = types.SimpleNamespace()
    s.rect = pg.Rect(0, 0, 40, 60)
    s.rect.center = (cx, cy)
    s.fighter = types.SimpleNamespace(
        is_alive=True, on_ground=on_ground, hurt_timer=0, stun_timer=0, grabbed_ledge=grabbed_ledge
    )
    s.controls = _CTRL
    s.current_move = None
    s.move_frame = 0
    s.state = "idle"
    return s


def _bot(level):
    return AttackerController(attacker_num=1, level=level, rng=random.Random(0))


# ---- no level enables edge-hog (the revert) ---------------------------------


def test_no_level_enables_edge_hog_after_the_v1_revert():
    # Able-to-fail: before #960, Lv7/Lv8/Lv9 had edge_hog=True (8 interpolates the two
    # odd anchors). The revert drops the flag from every anchor → uniformly False.
    for lvl in range(1, 10):
        assert level_params(lvl).edge_hog is False, f"Lv{lvl} still edge-hogs after the revert"
    assert AttackerController(level=7).edge_hog is False
    assert AttackerController(level=9).edge_hog is False


# A bot on-stage within EDGE_HOG_RANGE of the left ledge; the foe recovering
# off-stage-left just past the lip (x=58 < ax=60) and well below it (dy large), so
# neither edge_guard's poke nor Lv9's fireball fires — the edge-hog grab is the only
# branch that keys off `ledges`. So plumbing ledges vs. None isolates edge-hog.
_A = (100, 300)
_FOE_OFF = (58, 420)


def test_lv7_no_longer_walks_to_the_ledge_to_contest_a_recovering_foe():
    # Able-to-fail: with edge_hog=True the decision was {left} (the ledge-grab walk)
    # WITH ledges and {down} without — they differed. Reverted, the edge-hog branch is
    # dead, so plumbing ledges must not change the decision.
    a, off = _stub(*_A), _stub(*_FOE_OFF, on_ground=False)
    assert _bot(7).decide(a, off, 0, None, [_LEFT]) == _bot(7).decide(a, off, 0, None, None)


def test_lv9_no_longer_walks_to_the_ledge_to_contest_a_recovering_foe():
    a, off = _stub(*_A), _stub(*_FOE_OFF, on_ground=False)
    assert _bot(9).decide(a, off, 0, None, [_LEFT]) == _bot(9).decide(a, off, 0, None, None)


# ---- the machinery stays dormant, not deleted (#952 groundwork) -------------


def test_edge_hog_machinery_survives_and_fires_when_the_flag_is_forced_on():
    # #960 leaves the flag/target-finder/branch in place for epic #952. Forcing the
    # dormant flag on (as a future level will) must still produce the ledge-grab walk —
    # proof the machinery wasn't deleted, only unreferenced by any level.
    c = _bot(7)
    c.edge_hog = True
    a = _stub(100, 300)  # within EDGE_HOG_RANGE of ax=60
    off = _stub(30, 320, on_ground=False)  # foe recovering off-stage left
    assert abs(a.rect.centerx - _LEFT.ax) <= EDGE_HOG_RANGE  # geometry sanity
    assert c.decide(a, off, 0, None, [_LEFT]) == {_CTRL["left"]}


# ---- edge_guard is untouched by the revert ----------------------------------


def test_edge_guard_still_enabled_at_lv5_7_9():
    # The kept canonical behavior (#413 on-stage poke) must be unaffected by the
    # edge-hog revert.
    for lvl in (5, 7, 9):
        assert level_params(lvl).edge_guard is True, f"Lv{lvl} lost edge_guard"
