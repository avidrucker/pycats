"""Birky up-B = Final Cutter, rise-only (#969, B3 of #566) — the recovery move
wired onto the generalized #578 hook as DATA only (no new engine code).

Values sourced in docs/research/2026-07-31-birky-final-cutter-sourcing.md: a
primary datamine of PM 3.6 Kirby `SpecialAirHi2`. Avi's 2026-07-31 scope ruling
keeps this to the RISING SLASH + recovery — an 8% single hit (4 boxes sharing one
window -> first-box-wins picks one), WDSK 117/102, KBG 100, angle ~80-91 — with
`recovery_vy ≈ -15.7` derived from the animation-root net rise (apex 292.3 px ≈
2.03× Birky's full-jump height, back-solved under Birky's gravity 0.42). Final
Cutter's phase-2 plunge (#973) and phase-3 landing shockwave (#974) need new engine
code and are out of scope here.

Two layers of test:
  - LIVE: drive the REAL shipped Birky data (`load_fighter_data("birky")`) through
    `Player.update`, proving the JSON move flows through the recovery hook (#578)
    and the move clock (burst -> helpless; the slash spawns live).
  - DATA: pin the sourced scalars / geometry / window so a wrong value reds here.
"""

import pygame as pg

from pycats.combat.data import load_fighter_data
from pycats.combat.move_select import resolve_move_key
from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

_BIRKY = load_fighter_data("birky")

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
        char_name="birky",
        facing_right=facing_right,
        fighter_data=load_fighter_data("birky"),
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
# LIVE — the recovery hook, driven by real shipped Birky data
# ---------------------------------------------------------------------------


def test_up_b_sets_sourced_upward_burst():
    """Airborne up-B SETS Birky's vel.y to the sourced recovery_vy (-15.7), a
    stronger-than-jump upward burst that replaces downward momentum (SET, not add)."""
    up_b = _BIRKY.moves["up_b"]
    p, plats = _airborne()
    p.fighter.vel.y = 8.0  # falling
    _up_b(p, plats)
    assert p.fighter.vel.y < 0, f"up-B should set an upward burst, got vy={p.fighter.vel.y}"
    # SET to recovery_vy (robust to one tick of gravity), NOT added onto +8.
    assert p.fighter.vel.y <= up_b.recovery_vy + 2, (
        f"burst should be ~{up_b.recovery_vy} (SET, not added to +8), got {p.fighter.vel.y}"
    )
    # The sourced burst is stronger than Birky's own jump (a real recovery).
    assert up_b.recovery_vy < _BIRKY.jump_vel, (
        f"recovery_vy {up_b.recovery_vy} should exceed Birky's jump {_BIRKY.jump_vel}"
    )


def test_up_b_is_purely_vertical():
    """Final Cutter has zero horizontal drift (datamine root-motion x = 0 every
    frame) — the burst must not shove Birky sideways."""
    up_b = _BIRKY.moves["up_b"]
    assert up_b.recovery_vx == 0.0
    for facing in (True, False):
        p, plats = _airborne(facing_right=facing)
        vx0 = p.fighter.vel.x
        _up_b(p, plats)
        assert p.fighter.vel.x == vx0 == 0.0, f"up-B should add no horizontal velocity (facing={facing})"


def test_up_b_ends_in_helpless():
    p, plats = _airborne()
    _up_b(p, plats)
    # move total = 2 + 2 + 16 = 20; the airborne exit routes to helpless (#184). Check
    # as soon as the move ends — the strong burst then glides Birky off the top blast
    # zone on momentum (a KO), so don't step arbitrarily far past the move.
    saw_helpless = False
    for _ in range(24):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
        if p.state == "helpless":
            saw_helpless = True
            break
    assert saw_helpless, f"recovery move should end in helpless, ended {p.state!r}"


def test_up_b_reachable_through_special_seam():
    assert resolve_move_key(set(_BIRKY.moves), "up", on_ground=False, is_special=True) == "up_b"
    assert resolve_move_key(set(_BIRKY.moves), "up", on_ground=True, is_special=True) == "up_b"


def test_up_b_slash_spawns_live():
    """Driven live, the move spawns the sourced 8% rising slash — proving the JSON
    data flows through the move clock into a live attack."""
    p, plats = _airborne()
    atks = _up_b(p, plats)
    seen = set()
    for _ in range(24):
        for a in atks:
            if getattr(a, "active", False):
                seen.add(round(a.damage, 1))
        p.update(_frame(set(), set()), plats, atks)
    assert 8.0 in seen, f"expected the 8% rising slash to spawn live, saw {sorted(seen)}"


# ---------------------------------------------------------------------------
# DATA — the sourced values (a wrong number reds here)
# ---------------------------------------------------------------------------


def test_up_b_is_a_recovery_special():
    m = _BIRKY.moves["up_b"]
    assert m.grants_recovery is True
    assert m.recovery_vy == -15.7  # §2 apex 292.3px back-solved at g=0.42
    assert m.recovery_vx == 0.0  # §2 purely vertical
    assert m.in_air is True  # aerial special (does not clank, #133)


def test_up_b_frame_timing():
    # §3: total 20 f, active 3-4 -> startup 2 / active 2 / recovery 16.
    m = _BIRKY.moves["up_b"]
    assert (m.startup, m.active, m.recovery) == (2, 2, 16)
    assert m.startup + m.active + m.recovery == 20


def test_up_b_is_a_single_window():
    # §1: one rising-slash window, active f3-4 (rise-only; no plunge/shockwave here).
    m = _BIRKY.moves["up_b"]
    windows = sorted({(h.active_start, h.active_end) for h in m.hitboxes})
    assert windows == [(3, 4)]


def test_up_b_rising_slash_scalars():
    # §1: 8% slash, WDSK (set_knockback) 117/102, KBG 100, angles 80/90/91, BKB 0.
    m = _BIRKY.moves["up_b"]
    hbs = m.hitboxes
    assert {h.damage for h in hbs} == {8.0}
    assert all(h.set_knockback is not None for h in hbs), "rising slash is WDSK (set knockback)"
    assert sorted({h.set_knockback for h in hbs}) == [102, 117]
    assert {h.knockback_growth for h in hbs} == {100.0}
    assert {h.base_knockback for h in hbs} == {0.0}
    assert sorted({h.angle for h in hbs}) == [80, 90, 91]


def test_up_b_datamined_radii():
    # §1: radius u(3.5) = 19 px (datamine size × PX_PER_UNIT, verbatim) on all 4 boxes.
    m = _BIRKY.moves["up_b"]
    assert sorted(h.circle.r for h in m.hitboxes) == [19, 19, 19, 19]
