"""Nalio up-B = Super Jump Punch (#954, B2 of #566) — the recovery move wired onto
the generalized #578 hook as DATA only (no new engine code).

Values sourced in docs/research/2026-07-31-nalio-super-jump-punch-sourcing.md
(closes #956): a primary datamine of PM 3.6 Mario `SpecialAirHi`. It is a
4-window multi-hit — an initial 5% grab-up, two 1% auto-link windows, and a 3%
launcher — with `recovery_vy ≈ -15.5` derived from the animation-root net rise
(239.7 px ≈ 1.42× Nalio's full-jump height, back-solved under gravity = 0.5).

Two layers of test:
  - LIVE: drive the REAL shipped Nalio data (`load_fighter_data("nalio")`) through
    `Player.update`, proving the JSON move flows through the recovery hook (#578)
    and the move clock (burst -> helpless; all four windows spawn live).
  - DATA: pin the sourced scalars / geometry / windows so a wrong value reds here.
"""

import pygame as pg

from pycats.combat.data import load_fighter_data
from pycats.combat.move_select import resolve_move_key
from pycats.config import JUMP_VEL, P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

_NALIO = load_fighter_data("nalio")

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
        char_name="nalio",
        facing_right=facing_right,
        fighter_data=load_fighter_data("nalio"),
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
# LIVE — the recovery hook, driven by real shipped Nalio data
# ---------------------------------------------------------------------------


def test_up_b_sets_sourced_upward_burst():
    """Airborne up-B SETS Nalio's vel.y to the sourced recovery_vy (-15.5), a
    stronger-than-jump upward burst that replaces downward momentum (SET, not add)."""
    up_b = _NALIO.moves["up_b"]
    p, plats = _airborne()
    p.fighter.vel.y = 8.0  # falling
    _up_b(p, plats)
    assert p.fighter.vel.y < 0, f"up-B should set an upward burst, got vy={p.fighter.vel.y}"
    # SET to recovery_vy (robust to one tick of gravity), NOT added onto +8.
    assert p.fighter.vel.y <= up_b.recovery_vy + 2, (
        f"burst should be ~{up_b.recovery_vy} (SET, not added to +8), got {p.fighter.vel.y}"
    )
    # The sourced burst is stronger than a plain jump (a real recovery).
    assert up_b.recovery_vy < JUMP_VEL, f"recovery_vy {up_b.recovery_vy} should exceed jump {JUMP_VEL}"


def test_up_b_ends_in_helpless():
    p, plats = _airborne()
    _up_b(p, plats)
    # move total = 2 + 13 + 23 = 38; step well past it, still airborne (high floor)
    for _ in range(50):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    assert p.state == "helpless", f"recovery move should end in helpless, got {p.state!r}"


def test_up_b_reachable_through_special_seam():
    assert resolve_move_key(set(_NALIO.moves), "up", on_ground=False, is_special=True) == "up_b"
    assert resolve_move_key(set(_NALIO.moves), "up", on_ground=True, is_special=True) == "up_b"


def test_up_b_spawns_all_four_windows_live():
    """Driven live, the move spawns hitboxes carrying every sourced window damage:
    5% grab-up, 1% auto-links, 3% launcher — proving the JSON data flows through
    the move clock into live attacks."""
    p, plats = _airborne()
    atks = _up_b(p, plats)
    seen = set()
    for _ in range(40):
        for a in atks:
            if getattr(a, "active", False):
                seen.add(round(a.damage, 1))
        p.update(_frame(set(), set()), plats, atks)
    assert {5.0, 1.0, 3.0} <= seen, f"expected the 5/1/3% windows to spawn live, saw {sorted(seen)}"


# ---------------------------------------------------------------------------
# DATA — the sourced values (a wrong number reds here)
# ---------------------------------------------------------------------------


def test_up_b_is_a_recovery_special():
    m = _NALIO.moves["up_b"]
    assert m.grants_recovery is True
    assert m.recovery_vy == -15.5  # §0b net-rise integral (239.7 px ≈ 1.42× jump)
    assert m.in_air is True  # aerial special (does not clank, #133)


def test_up_b_frame_timing():
    # §1a: total 38 f, active 3-15 -> startup 2 / active 13 / recovery 23.
    m = _NALIO.moves["up_b"]
    assert (m.startup, m.active, m.recovery) == (2, 13, 23)
    assert m.startup + m.active + m.recovery == 38


def test_up_b_four_windows_present():
    # §0a/§1b: four sequential windows A[3,6] B[7,9] C[10,13] D[14,15].
    m = _NALIO.moves["up_b"]
    windows = sorted({(h.active_start, h.active_end) for h in m.hitboxes})
    assert windows == [(3, 6), (7, 9), (10, 13), (14, 15)]


def test_up_b_grab_up_window():
    # A[3,6]: 5% grab-up, WDSK 130, KBG 100, angles 70/90.
    m = _NALIO.moves["up_b"]
    a = [h for h in m.hitboxes if h.active_start == 3]
    assert {h.damage for h in a} == {5.0}
    assert {h.set_knockback for h in a} == {130}
    assert {h.knockback_growth for h in a} == {100.0}
    assert sorted(h.angle for h in a) == [70, 90]


def test_up_b_auto_link_windows_are_set_knockback():
    # B[7,9] + C[10,13]: 1% auto-links, all WDSK-based (set_knockback), KBG 100.
    m = _NALIO.moves["up_b"]
    links = [h for h in m.hitboxes if h.active_start in (7, 10)]
    assert {h.damage for h in links} == {1.0}
    assert all(h.set_knockback is not None for h in links)
    assert sorted(h.set_knockback for h in links) == [90, 110, 120, 150]


def test_up_b_launcher_is_growing_knockback():
    # D[14,15]: 3% launcher — real BKB 40 / KBG 140, angle 50, NO WDSK.
    m = _NALIO.moves["up_b"]
    launch = [h for h in m.hitboxes if h.active_start == 14]
    assert launch, "the launcher window [14,15] must exist"
    assert {h.damage for h in launch} == {3.0}
    assert {h.base_knockback for h in launch} == {40.0}
    assert {h.knockback_growth for h in launch} == {140.0}
    assert {h.angle for h in launch} == {50}
    assert all(h.set_knockback is None for h in launch), "the launcher uses growing KB, not WDSK"


def test_up_b_datamined_radii():
    # §0a radii (size × PX_PER_UNIT, verbatim) keyed by (window, sorted radius).
    m = _NALIO.moves["up_b"]
    radii = sorted(h.circle.r for h in m.hitboxes)
    assert radii == [21, 27, 27, 27, 34, 34, 40, 47]
