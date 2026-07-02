"""AI deliberate recovery — slice 2 of #312 (#409).

When the bot itself is airborne off-stage, it aims for the near ledge (moves inward
+ jumps) instead of chasing the opponent further out into the blast zone; the
hang->getup (#291) returns it once #14's auto-grab catches. On at level >= 5;
off by default → level-less/low never runs (golden-safe). Deliberately imperfect
(the PM CPU weakness, #251 Q4).
"""
import random
import types

import pygame as pg

from pycats.sim.controllers import AttackerController
from pycats.entities.ledge import Ledge

pg.init()

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}


def _stub(cx, cy, alive=True, on_ground=True, grabbed_ledge=None):
    s = types.SimpleNamespace()
    s.rect = pg.Rect(0, 0, 40, 60)
    s.rect.center = (cx, cy)
    s.fighter = types.SimpleNamespace(is_alive=alive, on_ground=on_ground,
                                      hurt_timer=0, stun_timer=0,
                                      grabbed_ledge=grabbed_ledge)
    s.controls = _CTRL
    s.current_move = None
    s.move_frame = 0
    s.state = "fall"
    return s


def _recoverer():
    # level 5 => recover=True, edge_hog=False (recovery isolated from edge-hog).
    return AttackerController(attacker_num=1, level=5, rng=random.Random(0))


def _default():
    return AttackerController(attacker_num=1, rng=random.Random(0))   # level=None


_LEFT = Ledge("left", ax=60, ay=300)     # off-stage is x < 60


# ---- detection (pure) -------------------------------------------------------

def test_self_recover_target_detects_own_off_stage():
    c = _recoverer()
    off = _stub(30, 330, on_ground=False)          # airborne, past ax=60 to the left
    assert c._self_recover_target(off, [_LEFT]) is _LEFT
    assert c._self_recover_target(_stub(30, 330, on_ground=True), [_LEFT]) is None   # grounded
    assert c._self_recover_target(_stub(200, 330, on_ground=False), [_LEFT]) is None  # inbounds
    assert c._self_recover_target(off, None) is None                # no ledges (golden-safe)


# ---- decision ---------------------------------------------------------------

def test_off_stage_bot_moves_inward_and_jumps():
    c = _recoverer()
    a = _stub(30, 330, on_ground=False)            # bot off-stage left, airborne
    t = _stub(300, 300, on_ground=True)            # opponent safely on stage
    # inward toward ax=60 (to the RIGHT of x=30) + jump for height.
    assert c.decide(a, t, 0, None, [_LEFT]) == {_CTRL["right"], _CTRL["up"]}


def test_on_stage_bot_does_not_trigger_recovery():
    c = _recoverer()
    a = _stub(120, 300, on_ground=True)            # grounded → no recovery override
    t = _stub(300, 300, on_ground=True)
    assert c.decide(a, t, 0, None, [_LEFT]) != {_CTRL["right"], _CTRL["up"]}


# ---- golden-safety ----------------------------------------------------------

def test_level_less_default_unaffected_by_ledges():
    a = _stub(30, 330, on_ground=False)
    t = _stub(300, 300, on_ground=True)
    assert _default().decide(a, t, 0, None, [_LEFT]) == _default().decide(a, t, 0, None, None)


# ---- real loop (the #248 gotcha — recoverable scenario) ---------------------

def _recovery_signals(recover_on):
    """Launch the bot off-stage just below the ledge lip (a recoverable spot, per the
    #409 tightening) with the opponent safe inboard, and run a REAL battle loop.
    Return (jumped_while_off_stage, reached_safety): whether the controller's
    emitted input included the recovery jump `up` while the bot was airborne
    off-stage (the decision surviving the full loop — the #248/#370 guard), and
    whether the bot ever grabbed the ledge / regained the ground."""
    import pygame
    from pycats.sim import runner
    from pycats.entities.ledge import ledges_from_platforms

    plats = runner.build_stage()
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    ledges = ledges_from_platforms(plats)
    left = min(ledges, key=lambda L: L.ax)
    p1.rect.center = (left.ax - 30, left.ay + 20)     # just off + just below the lip
    p1.fighter.on_ground = False
    p1.fighter.vel.update(0, 2)                       # a gentle downward launch
    p2.rect.center = (left.ax + 200, left.ay - 30)    # opponent safe, inboard
    c1 = _recoverer() if recover_on else _default()
    attacks = pygame.sprite.Group()
    jumped_off_stage = reached_safety = False
    for f in range(45):
        off_stage_before = (not p1.fighter.on_ground) and p1.rect.centerx < left.ax
        fi = c1(p1, p2, f, attacks, ledges)
        if off_stage_before and p1.controls["up"] in fi.held:
            jumped_off_stage = True             # recovery decision fired IN the loop
        p1.update(fi, plats, attacks)
        if p1.fighter.grabbed_ledge is not None or p1.fighter.on_ground:
            reached_safety = True
            break
    return jumped_off_stage, reached_safety


def test_recovery_decision_fires_in_a_real_battle():
    # #248/#370 gotcha guard: the recovery must survive the FULL loop (emit the jump
    # while airborne off-stage), and the test must FAIL with the feature off — a
    # level-less bot never jumps to recover while off-stage.
    on_jumped, on_safe = _recovery_signals(recover_on=True)
    off_jumped, off_safe = _recovery_signals(recover_on=False)
    assert on_jumped, "recover bot should jump for the ledge while off-stage (in the real loop)"
    assert not off_jumped, "level-less bot must NOT jump-recover (proves the test discriminates)"
