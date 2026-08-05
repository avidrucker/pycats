"""Narz down-B Counter (#1199, ruled #1194) — a detect-and-riposte special.

Narz's down-B arms a DETECT stance (the `counter` fighter state). While the stance's
active sub-window is open, an incoming MELEE hit is intercepted in
`hit_resolution.process_hits`: the incoming hitbox is negated (the defender takes 0
damage/knockback) and a fixed-7% riposte (the `down_b_riposte` move) is spawned on the
next `Player.update`, which can hit the attacker. Ruled scope (#1194 D2): melee only —
projectiles pass through in V1 (#1201 is the post-V1 follow-up). Grounded + air (D4).

Able-to-fail (revert-check):
  * remove the `is_counter` arm in fighter_input → `test_down_b_press_enters_counter`
    reds (down-B no longer enters the `counter` state);
  * remove the process_hits counter branch → `test_melee_in_window_is_negated_and_ripostes`
    reds (the defender takes damage and no riposte spawns);
  * flip the detect gate to always-on → `test_hit_outside_window_connects_normally` reds
    (a pre-window hit would be countered);
  * drop the `is_projectile` guard → `test_projectile_in_window_passes_through` reds.
"""

from __future__ import annotations

import types

import pygame as pg
from helpers import P1, P2, ground, mk_player

from pycats.combat.data import Circle, Hitbox, Status, load_fighter_data
from pycats.core.input import InputFrame
from pycats.entities.attack import Attack, Projectile
from pycats.systems.hit_resolution import process_hits

_NARZ = load_fighter_data("narz")
_DOWN_B = _NARZ.moves["down_b"]
# Detect window in the 1-indexed post-increment convention (startup < frame <= startup+active).
_DETECT_START = _DOWN_B.startup + 1  # 5
_DETECT_END = _DOWN_B.startup + _DOWN_B.active  # 30


def _frame(held=(), pressed=()):
    return InputFrame(held={P1[k] for k in held}, pressed={P1[k] for k in pressed}, released=set())


def _narz_defender():
    """A grounded Narz player, settled on the floor, facing right."""
    pg.init()
    p = mk_player(100, 100, char_name="P1", fighter_data=_NARZ)
    plats = ground()
    grp = pg.sprite.Group()
    for _ in range(3):  # settle onto the ground
        p.update(_frame(), plats, grp)
    return p, plats, grp


def _stub_owner(rect):
    """A minimal attacker whose fighter carries the few attrs process_hits/receive_hit
    read on the owner (facing, hitlag, the damage-given/hit-landed recorders)."""
    fighter = types.SimpleNamespace(
        facing_right=True,
        hitlag_timer=0,
        record_damage_given=lambda amount: None,
        record_hit_landed=lambda: None,
    )
    owner = types.SimpleNamespace(rect=rect, fighter=fighter, record_hit_landed=lambda: None)
    return owner


def _melee_over(defender, damage=12.0, projectile=False):
    """An attack whose hitbox circle overlaps the defender's hurtbox (owner rect == the
    defender's rect + a big central circle). `projectile=True` builds a Projectile
    (is_projectile True) to exercise the melee-only counter scope."""
    owner = _stub_owner(defender.rect)
    cls = Projectile if projectile else Attack
    hb = Hitbox(circle=Circle(20, 30, 30), damage=damage, angle=20, base_knockback=30.0, knockback_growth=60.0)
    return cls(owner, hitboxes=(hb,), lifetime=10, disappear_on_hit=False)


def _arm_counter(p, plats, grp):
    """Press down+special so Narz enters the counter stance; return after the arm frame."""
    p.update(_frame(held=("down",), pressed=("down", "special")), plats, grp)
    return p


def _advance_to_elapsed(p, plats, grp, elapsed):
    """Advance until the counter stance has run `elapsed` frames (counter_timer counts
    down from the stance total)."""
    target = p.fighter.counter_total - elapsed
    guard = 0
    while p.fighter.counter_timer > target and guard < 200:
        p.update(_frame(), plats, grp)
        guard += 1
    return p


# --------------------------------------------------------------------- dispatch


def test_down_b_press_enters_counter():
    """A grounded down-B press enters the `counter` state (not an attack), commits the
    fighter, and starts no move clock — the stance runs off counter_timer."""
    p, plats, grp = _narz_defender()
    _arm_counter(p, plats, grp)
    assert p.state == "counter"
    assert p.fighter.counter_timer > 0
    assert p.current_move is None  # no hitbox move started; the stance is not clocked
    assert p.fighter.counter_riposte_key == "down_b_riposte"


def test_down_b_air_enters_counter():
    """Air down-B enters the counter stance from the air (D4 — grounded + air)."""
    p, plats, grp = _narz_defender()
    p.update(_frame(pressed=("up",)), plats, grp)  # jump
    p.update(_frame(), plats, grp)
    assert not p.fighter.on_ground
    p.update(_frame(held=("down",), pressed=("down", "special")), plats, grp)
    assert p.state == "counter"
    assert p.fighter.counter_timer > 0


# ------------------------------------------------------------- detect + riposte


def test_counter_active_only_inside_the_window():
    """counter_active is closed before the detect window opens, open inside it, and
    closed again after it — so only in-window hits are intercepted."""
    p, plats, grp = _narz_defender()
    _arm_counter(p, plats, grp)
    _advance_to_elapsed(p, plats, grp, _DETECT_START - 2)  # just before the window
    assert not p.fighter.counter_active
    _advance_to_elapsed(p, plats, grp, _DETECT_START + 1)  # inside
    assert p.fighter.counter_active
    _advance_to_elapsed(p, plats, grp, _DETECT_END + 1)  # past the window
    assert not p.fighter.counter_active


def test_melee_in_window_is_negated_and_ripostes():
    """A melee hit during the detect window: the defender takes 0 damage, the incoming
    hitbox is consumed, and the fixed-7% riposte spawns and routes counter -> attacking."""
    p, plats, grp = _narz_defender()
    _arm_counter(p, plats, grp)
    _advance_to_elapsed(p, plats, grp, _DETECT_START + 2)  # inside the window
    assert p.fighter.counter_active
    grp2 = pg.sprite.Group()
    atk = _melee_over(p)
    grp2.add(atk)
    process_hits([p], grp2)
    assert p.fighter.percent == 0  # incoming hit negated
    assert not atk.active  # the attacker's hitbox is consumed
    assert p.fighter.pending_counter_riposte  # riposte armed for next update

    # Next update spawns the riposte on the clock and routes counter -> attacking.
    p.update(_frame(), plats, grp)
    assert p.current_move is _NARZ.moves["down_b_riposte"]
    assert p.state == "attack"  # the attacking region collapses to the flat label "attack"
    assert not p.fighter.pending_counter_riposte


def test_riposte_deals_fixed_7_percent_to_attacker():
    """Drive a full counter and let the riposte hitbox connect with a real attacker in
    front of Narz: the attacker takes exactly the fixed 7% (no scaling)."""
    p, plats, grp = _narz_defender()
    # A real attacker grounded just in front of Narz's facing (feet at x≈130, same floor),
    # so the riposte hitbox (authored at the front, dx≈40) overlaps its hurtbox.
    attacker = mk_player(130, 100, controls=P2, char_name="P2", fighter_data=_NARZ)
    for _ in range(5):  # settle onto the ground
        attacker.update(InputFrame(held=set(), pressed=set(), released=set()), plats, grp)
    _arm_counter(p, plats, grp)
    _advance_to_elapsed(p, plats, grp, _DETECT_START + 2)
    grp2 = pg.sprite.Group()
    grp2.add(_melee_over(p))
    process_hits([p], grp2)  # counter connects, arms riposte
    before = attacker.fighter.percent
    # Advance until the riposte hitbox (spawned into `grp` by p.update) is live and
    # connects with the attacker, resolving hits each frame.
    for _ in range(12):
        p.update(_frame(), plats, grp)
        process_hits([p, attacker], grp)
        if attacker.fighter.percent > before:
            break
    assert attacker.fighter.percent == before + 7.0  # fixed 7%, no scaling


def test_hit_outside_window_connects_normally():
    """A melee hit landing BEFORE the detect window opens connects normally (percent
    rises, the counter is cancelled, the fighter goes to hurt) — not countered."""
    p, plats, grp = _narz_defender()
    _arm_counter(p, plats, grp)
    _advance_to_elapsed(p, plats, grp, 1)  # frame 1: before the window (opens at 5)
    assert not p.fighter.counter_active
    grp2 = pg.sprite.Group()
    grp2.add(_melee_over(p, damage=12.0))
    process_hits([p], grp2)
    assert p.fighter.percent == 12.0  # normal hit landed
    assert not p.fighter.pending_counter_riposte
    assert p.fighter.counter_timer == 0  # counter cancelled by the hit


def test_projectile_in_window_passes_through():
    """A PROJECTILE during the detect window is NOT countered in V1 (ruled #1194 D2):
    it lands normally and arms no riposte."""
    p, plats, grp = _narz_defender()
    _arm_counter(p, plats, grp)
    _advance_to_elapsed(p, plats, grp, _DETECT_START + 2)
    assert p.fighter.counter_active
    grp2 = pg.sprite.Group()
    grp2.add(_melee_over(p, damage=8.0, projectile=True))
    process_hits([p], grp2)
    assert p.fighter.percent == 8.0  # projectile landed (not intercepted)
    assert not p.fighter.pending_counter_riposte


# --------------------------------------------------------------------- data


def test_riposte_damage_is_found_seven_percent():
    """The 7% riposte value is registered FOUND with a citation (criterion 5 / D1)."""
    box = _NARZ.moves["down_b_riposte"].hitboxes[0]
    assert box.damage == 7.0
    fs = box.status["damage"]
    assert fs.status is Status.FOUND
    assert fs.source and "SmashWiki" in fs.source
