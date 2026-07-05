"""AI edge-guard — slice 3 of #312 (#413).

When the opponent recovers off-stage, a bot contests it from ON-STAGE: a projectile
at range (specials levels) or a melee poke in reach, never going off (the PM CPU
weakness, #251 Q4). The projectile drops the on-stage poke's `dy<60` cap (the foe is
below the lip). Edge-guard takes precedence over the #404 edge-hog grab. On at level
>= 5; off by default → level-less/low never runs (golden-safe).
"""
import random
import types

import pygame as pg

from pycats.entities.ledge import Ledge
from pycats.sim.controllers import AttackerController

pg.init()

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}
_LEFT = Ledge("left", ax=60, ay=300)     # off-stage is x < 60


def _stub(cx, cy, alive=True, on_ground=True):
    s = types.SimpleNamespace()
    s.rect = pg.Rect(0, 0, 40, 60)
    s.rect.center = (cx, cy)
    s.fighter = types.SimpleNamespace(is_alive=alive, on_ground=on_ground,
                                      hurt_timer=0, stun_timer=0, grabbed_ledge=None)
    s.controls = _CTRL
    s.current_move = None
    s.move_frame = 0
    s.state = "idle"
    return s


def _guard(specials=False, **kw):
    moves = frozenset({"jab", "specials"}) if specials else frozenset({"jab"})
    return AttackerController(attacker_num=1, edge_guard=True, follow_through_p=1.0,
                             attack_period=1, enabled_moves=moves, rng=random.Random(0), **kw)


# ---- projectile at an off-stage foe (drops the dy<60 cap) --------------------

def test_projectile_fires_at_off_stage_foe_below_the_lip():
    c = _guard(specials=True)
    a = _stub(100, 300)                          # on-stage
    foe = _stub(30, 390, on_ground=False)        # off-stage left, BELOW the lip (dy=90 > 60)
    assert c.decide(a, foe, 0, None, [_LEFT]) == {_CTRL["special"]}


# ---- melee poke in reach of the edge ----------------------------------------

def test_melee_poke_when_foe_in_reach():
    c = _guard(specials=False)
    a = _stub(90, 300)
    # off-stage left (x<60), in melee reach, and BELOW the lip (dy=75 > 60) — the
    # on-stage poke's dy<60 gate would NOT fire here, only edge-guard does.
    foe = _stub(52, 375, on_ground=False)
    assert c.decide(a, foe, 0, None, [_LEFT]) == {_CTRL["attack"]}


def test_no_guard_when_foe_is_on_stage():
    c = _guard(specials=True)
    a = _stub(100, 300)
    on = _stub(30, 390, on_ground=True)          # grounded → not recovering → no target
    got = c.decide(a, on, 0, None, [_LEFT])
    assert got != {_CTRL["special"]} and got != {_CTRL["attack"]}


# ---- precedence over edge-hog (#404) ----------------------------------------

def test_edge_guard_takes_precedence_over_edge_hog():
    # A level-9 bot has BOTH edge_hog and edge_guard. Near the ledge with the foe in
    # projectile range, the on-stage guard (special) fires FIRST — not the edge-hog
    # grab movement (left/right toward the ledge).
    c = AttackerController(attacker_num=1, level=9, rng=random.Random(0))
    a = _stub(100, 300)                           # within EDGE_HOG_RANGE of ax=60
    foe = _stub(30, 380, on_ground=False)         # off-stage, projectile range, below lip
    got = c.decide(a, foe, 0, None, [_LEFT])
    assert got == {_CTRL["special"]}
    assert got != {_CTRL["left"]} and got != {_CTRL["right"]}   # not the edge-hog grab


# ---- golden-safety ----------------------------------------------------------

def _default():
    return AttackerController(attacker_num=1, rng=random.Random(0))   # level=None


def test_level_less_default_unaffected_by_ledges():
    a = _stub(100, 300)
    foe = _stub(30, 390, on_ground=False)
    assert _default().decide(a, foe, 0, None, [_LEFT]) == _default().decide(a, foe, 0, None, None)


# ---- real loop (the #248 gotcha) --------------------------------------------

def _guards_in_real_battle(edge_guard_on):
    """Pin the opponent recovering off-stage past the left ledge and an on-stage bot
    near it; run a REAL loop and return whether the bot emitted an attack/projectile
    toward the off-stage foe IN the loop. Discriminates the feature (#248/#370)."""
    import pygame

    from pycats.entities.ledge import ledges_from_platforms
    from pycats.sim import runner

    plats = runner.build_stage()
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    ledges = ledges_from_platforms(plats)
    left = min(ledges, key=lambda L: L.ax)
    p1.rect.center = (left.ax + 40, left.ay - 30)     # bot on-stage near the edge
    c1 = AttackerController(attacker_num=1, level=9, rng=random.Random(0))
    if not edge_guard_on:
        c1.edge_guard = False                         # discriminating control
    attacks = pygame.sprite.Group()
    attacked = False
    for f in range(40):
        p2.rect.center = (left.ax - 40, left.ay + 50)  # pin foe off-stage + below lip
        p2.fighter.on_ground = False
        foe_off = p2.rect.centerx < left.ax
        fi = c1(p1, p2, f, attacks, ledges)
        if foe_off and ({p1.controls["attack"], p1.controls["special"]} & fi.held):
            attacked = True
        p1.update(fi, plats, attacks)
        attacks.update(plats)
    return attacked


def test_edge_guard_attacks_the_recovering_foe_in_a_real_battle():
    assert _guards_in_real_battle(edge_guard_on=True), \
        "edge-guard bot should poke/projectile the off-stage foe (in the real loop)"
    assert not _guards_in_real_battle(edge_guard_on=False), \
        "feature-off bot must not edge-guard (proves the test discriminates)"
