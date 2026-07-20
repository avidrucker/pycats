"""AI edge-hog must reach safety, never hog forever (#424, updated for #475).

Two facets of the #404 edge-hog were flagged by the #417 persona review:

1. **Hold-to-deny forever.** The deny branch returned `set()` (hold, suppress getup)
   unconditionally. Pre-#475 the engine's 120f hang timeout eventually force-dropped
   the bot (a self-KO with no jump). #475 removed that timeout — so the bot would now
   hang *forever*. Fix: the controller counts its OWN hang frames and, after
   `LEDGE_HOG_MAX_FRAMES`, stops denying and climbs (neutral getup) to the stage.
   The bot always reaches safety; it never self-KOs and never hogs indefinitely.

2. **Go-to-ledge walk-off miss.** Investigated and found already safe: the
   `{left/right}` walk toward the ledge is arrested at the platform edge (plus the
   `EDGE_HOG_RANGE` commit bound), so the bot never walks off into a self-destruct.
   The real-loop guard below documents that invariant (it stays green today; it
   goes red if a future change lets the walk step off the stage).
"""
import random
import types

import pygame as pg

from pycats import config
from pycats.entities.ledge import Ledge, ledges_from_platforms
from pycats.sim.controllers import EDGE_HOG_RANGE, LEDGE_HOG_MAX_FRAMES, AttackerController

pg.init()

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}
_LEFT = Ledge("left", ax=60, ay=300)   # off-stage is x < 60


def _stub(cx, cy, alive=True, on_ground=True, grabbed_ledge=None):
    s = types.SimpleNamespace()
    s.rect = pg.Rect(0, 0, 40, 60)
    s.rect.center = (cx, cy)
    s.fighter = types.SimpleNamespace(is_alive=alive, on_ground=on_ground, hurt_timer=0,
                                      stun_timer=0, grabbed_ledge=grabbed_ledge)
    s.controls = _CTRL
    s.current_move = None
    s.move_frame = 0
    s.state = "idle"
    return s


def _hogger():
    return AttackerController(attacker_num=1, level=9, rng=random.Random(0))


# ---- facet 1: decide-level contract ----------------------------------------
def test_holds_the_deny_while_within_the_hog_budget():
    # A fresh hogger (0 hog frames spent) HOLDS to deny — the #404 behaviour, bounded.
    c = _hogger()
    a = _stub(48, 300, grabbed_ledge=_LEFT)
    off = _stub(30, 320, on_ground=False)
    assert c.decide(a, off, 0, None, [_LEFT]) == set()


def test_climbs_instead_of_holding_once_the_hog_budget_is_spent():
    # #424/#475: after LEDGE_HOG_MAX_FRAMES of denying, the bot must GET UP (climb to
    # safety) rather than hog forever — even though the opponent is still off-stage.
    c = _hogger()
    c._hog_frames = LEDGE_HOG_MAX_FRAMES          # budget already spent
    a = _stub(48, 300, grabbed_ledge=_LEFT)
    off = _stub(30, 320, on_ground=False)
    assert c.decide(a, off, 0, None, [_LEFT]) == {_CTRL["up"]}


# ---- facet 1: real loop (the #248 gotcha — must survive, not just decide) ----
def _run_a_full_hold_to_deny(*, jumps):
    """Seed a level-9 edge-hog bot HANGING on the left ledge (as player.update does
    on grab) with `jumps` air-jumps left, pin the opponent off-stage to keep the deny
    live, and run well past the hog budget. Return (is_alive, lives, climbed) — the bot
    must climb to the stage (grabbed_ledge cleared) rather than hog forever."""
    from pycats.sim import runner
    plats = runner.build_stage()
    p1, p2, _ = runner.build_players(p1_char="nalio", p2_char="nalio")
    ledges = ledges_from_platforms(plats)
    left = min(ledges, key=lambda L: L.ax)
    p1.rect.topleft = left.hang_topleft(p1.rect.size)
    p1.fighter.grabbed_ledge = left
    left.occupied_by = p1
    p1.fighter.on_ground = False
    p1.fighter.vel.x = 0
    p1.fighter.vel.y = 0
    p1.fighter.ledge_intangible_timer = 0
    p1.fighter.jumps_remaining = jumps
    c1 = AttackerController(attacker_num=1, level=9, rng=random.Random(0))  # edge_hog on @ lv9
    attacks = pg.sprite.Group()
    for f in range(LEDGE_HOG_MAX_FRAMES + config.LEDGE_GETUP_FRAMES + 90):
        p2.rect.center = (left.ax - 60, left.ay + 40)   # keep the opponent off-stage left
        p2.fighter.on_ground = False
        p1.update(c1(p1, p2, f, attacks, ledges), plats, attacks)
        if not p1.fighter.is_alive:
            break
    climbed = p1.fighter.grabbed_ledge is None and p1.fighter.on_ground
    return p1.fighter.is_alive, p1.fighter.lives, climbed


def test_edge_hog_climbs_to_safety_instead_of_hogging_forever():
    # Able-to-fail: an UNBOUNDED deny (return set() every frame) would leave the bot
    # hanging forever — grabbed_ledge never clears, `climbed` is False. The bounded
    # counter climbs it onto the stage after the budget, with no jump needed and no KO.
    alive, lives, climbed = _run_a_full_hold_to_deny(jumps=0)
    assert climbed, "edge-hog bot never climbed to safety — it hogged the ledge forever"
    assert alive, "edge-hog bot self-KO'd off the ledge"
    assert lives == 3, f"edge-hog bot lost a life to a self-destruct (lives={lives})"


# ---- facet 2: real-loop guard (already safe; catches a future regression) ----
def test_go_to_ledge_walk_never_walks_off_into_a_self_ko():
    from pycats.sim import runner
    plats = runner.build_stage()
    p1, p2, _ = runner.build_players(p1_char="nalio", p2_char="nalio")
    ledges = ledges_from_platforms(plats)
    left = min(ledges, key=lambda L: L.ax)
    for startx in (left.ax + 5, left.ax + 10, left.ax + 30, left.ax + EDGE_HOG_RANGE - 5):
        p1.rect.center = (startx, left.ay - 30)
        p1.fighter.on_ground = True
        p1.fighter.vel.x = 0
        p1.fighter.vel.y = 0
        p1.fighter.grabbed_ledge = None
        p1.fighter.jumps_remaining = 0          # no recovery net -> a walk-off would be fatal
        p1.fighter.is_alive = True
        p1.fighter.lives = 3
        left.occupied_by = None
        c1 = AttackerController(attacker_num=1, level=9, rng=random.Random(0))
        c1.recover = False                      # isolate the go-to-ledge walk branch
        attacks = pg.sprite.Group()
        for f in range(180):
            p2.rect.center = (left.ax - 60, left.ay + 40)
            p2.fighter.on_ground = False
            p1.update(c1(p1, p2, f, attacks, ledges), plats, attacks)
            if not p1.fighter.is_alive:
                break
        assert p1.fighter.is_alive, f"edge-hog walk self-KO'd from startx={startx}"
