"""Narz up-B = Dolphin Slash (#1059, B4 of #566 / Narz specials umbrella #1058) —
the recovery move wired onto the generalized #578 hook as DATA only (no new engine
code), the third archetype after Nalio SJP (#954) and Birky Final Cutter (#969).

Values sourced in docs/research/2026-08-01-narz-dolphin-slash-sourcing.md
(closes #1063): a primary datamine of PM 3.6 Marth `SpecialAirHi` (brawllib_rs),
independently cross-confirmed against meleelight's Melee `UPSPECIAL` (the two
primaries agree exactly on the hitbox scalars). A 2-window multi-hit — an initial
tipper (frames 4-5: tip 13% / base 10%x2) and a rising tipper (frames 6-10: tip
7% / base 7% / 6%) — all boxes `set_id 0` (one hit per target). `recovery_vy = -15.2`
is derived from the animation-root net rise (255 px ≈ 1.60x Narz's full jump) under
Narz's pinned gravity 0.45.

Two layers of test:
  - LIVE: drive the REAL shipped Narz data (`load_fighter_data("narz")`) through
    `Player.update`, proving the JSON move flows through the recovery hook (#578)
    and the move clock (burst -> helpless; both windows spawn live).
  - DATA: pin the sourced scalars / geometry / windows / tipper order so a wrong
    value reds here.
"""

from __future__ import annotations

import types

import pygame as pg

from pycats.combat.data import Circle, FighterData, Hurtbox, load_fighter_data
from pycats.combat.move_select import resolve_move_key
from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.attack import Attack
from pycats.entities.platform import Platform
from pycats.entities.player import Player
from pycats.systems.hit_resolution import process_hits

_NARZ = load_fighter_data("narz")

CONTROLS = {
    "left": pg.K_a,
    "right": pg.K_d,
    "up": pg.K_w,
    "down": pg.K_s,
    "shield": pg.K_q,
    "attack": pg.K_e,
    "special": pg.K_c,
}
UP, SPECIAL = pg.K_w, pg.K_c


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _airborne(floor_y=2000, facing_right=True):
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, floor_y, 960, 40), thin=False))
    p = Player(
        x=300,
        y=100,
        controls=CONTROLS,
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="narz",
        facing_right=facing_right,
        fighter_data=load_fighter_data("narz"),
    )
    empty = pg.sprite.Group()
    for _ in range(3):
        p.update(_frame(set(), set()), plats, empty)
    assert not p.fighter.on_ground, "fixture precondition: airborne"
    return p, plats


def _up_b(p, plats, attacks=None):
    attacks = pg.sprite.Group() if attacks is None else attacks
    p.update(_frame({UP, SPECIAL}, {UP, SPECIAL}), plats, attacks)
    return attacks


# ---------------------------------------------------------------------------
# LIVE — the recovery hook, driven by real shipped Narz data
# ---------------------------------------------------------------------------


def test_up_b_sets_sourced_upward_burst():
    """Airborne up-B SETS Narz's vel.y to the sourced recovery_vy (-15.2), a
    stronger-than-jump upward burst that replaces downward momentum (SET, not add)."""
    up_b = _NARZ.moves["up_b"]
    p, plats = _airborne()
    p.fighter.vel.y = 8.0  # falling
    _up_b(p, plats)
    assert p.fighter.vel.y < 0, f"up-B should set an upward burst, got vy={p.fighter.vel.y}"
    # SET to recovery_vy (robust to one tick of gravity), NOT added onto +8.
    assert p.fighter.vel.y <= up_b.recovery_vy + 2, (
        f"burst should be ~{up_b.recovery_vy} (SET, not added to +8), got {p.fighter.vel.y}"
    )
    # The sourced burst is stronger than Narz's plain jump (a real recovery).
    assert up_b.recovery_vy < _NARZ.jump_vel, f"recovery_vy {up_b.recovery_vy} should exceed Narz jump {_NARZ.jump_vel}"


def test_up_b_ends_in_helpless():
    p, plats = _airborne()
    _up_b(p, plats)
    # move total = 3 + 7 + 30 = 40; step well past it, still airborne (high floor)
    for _ in range(60):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.state == "helpless", f"recovery move should end in helpless, got {p.state!r}"


def test_up_b_reachable_through_special_seam():
    assert resolve_move_key(set(_NARZ.moves), "up", on_ground=False, is_special=True) == "up_b"
    assert resolve_move_key(set(_NARZ.moves), "up", on_ground=True, is_special=True) == "up_b"


def test_up_b_spawns_both_windows_live():
    """Driven live, the move spawns one hit per window carrying that window's tip
    damage — the 13% initial tip and the 7% rising tip — proving both windows of
    the JSON data flow through the move clock into live attacks."""
    p, plats = _airborne()
    atks = _up_b(p, plats)
    seen = set()
    for _ in range(40):
        for a in atks:
            if getattr(a, "active", False):
                seen.add(round(a.damage, 1))
        p.update(_frame(set(), set()), plats, atks)
    assert {13.0, 7.0} <= seen, f"expected the window-1 (13%) and window-2 (7%) tips live, saw {sorted(seen)}"


# ---------------------------------------------------------------------------
# DATA — the sourced values (a wrong number reds here)
# ---------------------------------------------------------------------------


def test_up_b_is_a_recovery_special():
    m = _NARZ.moves["up_b"]
    assert m.grants_recovery is True
    assert m.recovery_vy == -15.2  # §2 net-rise integral (255 px ≈ 1.60x jump)
    assert m.in_air is True  # aerial special (does not clank, #133)


def test_up_b_frame_timing():
    # §1d: datamine total 40 f, active 4-10 -> startup 3 / active 7 / recovery 30.
    m = _NARZ.moves["up_b"]
    assert (m.startup, m.active, m.recovery) == (3, 7, 30)
    assert m.startup + m.active + m.recovery == 40


def test_up_b_two_windows_present():
    # §1a/§1b: two sequential windows, initial [4,5] and rising [6,10].
    m = _NARZ.moves["up_b"]
    windows = sorted({(h.active_start, h.active_end) for h in m.hitboxes})
    assert windows == [(4, 5), (6, 10)]


def test_up_b_window1_initial_tipper():
    # §1a: window 1 [4,5] — tip 13% (BKB 80) + base 10%x2 (BKB 60), tip angle 361.
    m = _NARZ.moves["up_b"]
    w1 = [h for h in m.hitboxes if h.active_start == 4]
    assert sorted(h.damage for h in w1) == [10.0, 10.0, 13.0]
    tip = w1[0]  # authored first
    assert (tip.damage, tip.angle, tip.base_knockback) == (13.0, 361, 80.0)


def test_up_b_window2_rising_tipper():
    # §1b: window 2 [6,10] — tip 7% + base 7% / 6%, all BKB 20 / KBG 90, tip angle 361.
    m = _NARZ.moves["up_b"]
    w2 = [h for h in m.hitboxes if h.active_start == 6]
    assert sorted(h.damage for h in w2) == [6.0, 7.0, 7.0]
    assert {h.knockback_growth for h in w2} == {90.0}
    assert {h.base_knockback for h in w2} == {20.0}
    tip = w2[0]  # authored first
    assert (tip.damage, tip.angle) == (7.0, 361)


def test_up_b_tip_authored_first_in_each_window():
    """The Narz tipper identity: within each window the tip (the strongest,
    angle-361 box) is authored FIRST so it wins on overlap (tuple order = priority)."""
    m = _NARZ.moves["up_b"]
    for start in (4, 6):
        window = [h for h in m.hitboxes if h.active_start == start]
        tip = window[0]
        assert tip.angle == 361, "the tip carries the Sakurai (361) angle"
        assert tip.damage == max(h.damage for h in window), "the tip is the strongest box"


def test_up_b_tip_beats_base_when_both_overlap():
    """A defender overlapping BOTH window-1 boxes takes the TIP's 13% (priority =
    tuple order; first overlapping box wins). Able-to-fail: reorder the window or
    equalize the boxes and this reds."""
    pg.init()
    up_b = _NARZ.moves["up_b"]
    w1 = tuple(h for h in up_b.hitboxes if h.active_start == 4)
    attacker = _player(pg.Rect(0, 0, 40, 60), hurtbox_circles=[Circle(20, 15, 14), Circle(20, 45, 14)])
    # defender hurtbox at absolute (32,27): overlaps tip(40,21,r21) AND base(23,34,r21).
    defender = _player(pg.Rect(12, 0, 40, 60), hurtbox_circles=[Circle(20, 27, 14)])
    atk = Attack(attacker, hitboxes=w1, lifetime=2)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1, "overlapping boxes of one window = one hit (set_id 0)"
    assert defender.last_damage == w1[0].damage == 13.0, "the TIP (box 0) must win on dual overlap"


def test_up_b_datamined_radii():
    # §1e radii (size × PX_PER_UNIT): five u(3.906)=21 boxes + one u(3.125)=17 box.
    m = _NARZ.moves["up_b"]
    radii = sorted(h.circle.r for h in m.hitboxes)
    assert radii == [17, 21, 21, 21, 21, 21]


def _player(rect, *, hurtbox_circles, facing_right=True):
    p = types.SimpleNamespace(
        rect=rect,
        facing_right=facing_right,
        intangible=False,
        is_alive=True,
        fighter_data=FighterData(
            walk=1.1, dash=1.5, run=1.5, hurtbox=Hurtbox(circles=tuple(hurtbox_circles)), moves={}
        ),
        hits_received=0,
        hits_landed=0,
        last_damage=None,
        last_angle=None,
    )

    def receive_hit(atk, is_crouching=False):
        p.hits_received += 1
        p.last_damage = atk.damage
        p.last_angle = atk.angle

    p.receive_hit = receive_hit
    p.record_hit_landed = lambda: None
    p.fighter = p
    return p
