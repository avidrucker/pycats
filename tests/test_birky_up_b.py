"""Birky up-B = Final Cutter — the full 3-phase recovery special, wired onto the
engine hooks as DATA (#1110, task 2 of the #1095 tracker).

Phase 1 (rising slash + burst) sourced in
docs/research/2026-07-31-birky-final-cutter-sourcing.md: a primary datamine of PM 3.6
Kirby `SpecialAirHi2` — an 8% single hit (4 boxes sharing one window -> first-box-wins
picks one), WDSK 117/102, KBG 100, angle ~80-91 — with `recovery_vy ≈ -15.7` derived
from the animation-root net rise (apex 292.3 px ≈ 2.03× Birky's full-jump height,
back-solved under Birky's gravity 0.42). #969 shipped phase 1 alone (rise-only); this
ticket adds the per-cat data for phases 2 & 3 onto the shipped engine hooks:
  - phase 2 = descending plunge + spike (`velocity_phases`, engine #973): a plunge
    velocity SET at the apex (~f38) + a downward (angle 270) spike window;
  - phase 3 = landing shockwave (`landing_spawn`, engine #974): a feet-level ground
    beam on the touchdown event, routed through `landing_lag`.
All phase-2/3 numbers (plunge frame, plunge vy, spike scalars, beam speed/lifetime,
landing_lag) are ⚠ playtest starting points (ADR-0003 class), tuned in task 3 of #1095.

Two layers of test:
  - LIVE: drive the REAL shipped Birky data (`load_fighter_data("birky")`) through
    `Player.update`, proving the JSON move flows through the recovery hook (#578),
    the mid-move velocity phase (#973 plunge) and the touchdown spawn (#974 beam).
  - DATA: pin the sourced/authored scalars / geometry / windows so a wrong value reds.
"""

import pygame as pg

from pycats.combat.data import load_fighter_data
from pycats.combat.move_select import resolve_move_key
from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.attack import Projectile
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


def _airborne(floor_y=2000, facing_right=True, y=420):
    # Spawn LOW enough (y=420) that Birky's full ~292px Final Cutter rise stays on-stage:
    # from y=100 the -15.7 burst carries the whole arc off the top blast zone (a KO at
    # ~f27), so the plunge (f38) would never fire. y=420 keeps the apex (~y=88) on-stage.
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, floor_y, 960, 40), thin=False))
    p = Player(
        x=300,
        y=y,
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
    # move total = 2 + 2 + 40 = 44; the airborne exit routes to helpless (#184). The
    # plunge (f38) reverses the rise mid-descent, so Birky no longer glides off the top
    # blast zone — step through the full move (floor at y=2000 → still airborne at end).
    saw_helpless = False
    for _ in range(48):
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


def _rise_boxes(m):
    # The phase-1 rising-slash boxes: the f3-4 window (the plunge spike is a separate
    # f38-44 window). Scoped so the sourced #969 scalar/radius pins survive the phase-2
    # box addition (#1110) instead of fighting it (de-census, not delete).
    return [h for h in m.hitboxes if (h.active_start, h.active_end) == (3, 4)]


def test_up_b_frame_timing():
    # total 44 f: rise slash active f3-4 (startup 2 / active 2), recovery 40 extended so
    # the clock stays alive to the apex plunge (f38) + spike window (#1110). Was 20f in
    # the #969 rise-only slice; the move now spans all three phases (one MoveData, #1066).
    m = _BIRKY.moves["up_b"]
    assert (m.startup, m.active, m.recovery) == (2, 2, 40)
    assert m.startup + m.active + m.recovery == 44


def test_up_b_windows_rise_then_spike():
    # Two hitbox windows now: the phase-1 rising slash (f3-4) and the phase-2 descending
    # spike (f38-44). #969 pinned a single window; #1110 adds the plunge spike.
    m = _BIRKY.moves["up_b"]
    windows = sorted({(h.active_start, h.active_end) for h in m.hitboxes})
    assert windows == [(3, 4), (38, 44)]


def test_up_b_rising_slash_scalars():
    # §1 (sourced): 8% slash, WDSK (set_knockback) 117/102, KBG 100, angles 80/90/91,
    # BKB 0 — asserted on the RISE boxes only (the plunge spike has its own scalars).
    hbs = _rise_boxes(_BIRKY.moves["up_b"])
    assert len(hbs) == 4
    assert {h.damage for h in hbs} == {8.0}
    assert all(h.set_knockback is not None for h in hbs), "rising slash is WDSK (set knockback)"
    assert sorted({h.set_knockback for h in hbs}) == [102, 117]
    assert {h.knockback_growth for h in hbs} == {100.0}
    assert {h.base_knockback for h in hbs} == {0.0}
    assert sorted({h.angle for h in hbs}) == [80, 90, 91]


def test_up_b_datamined_radii():
    # §1 (sourced): radius u(3.5) = 19 px on all 4 RISE boxes (datamine size ×
    # PX_PER_UNIT, verbatim). The plunge spike's radius is a separate playtest value.
    assert sorted(h.circle.r for h in _rise_boxes(_BIRKY.moves["up_b"])) == [19, 19, 19, 19]


# ---------------------------------------------------------------------------
# DATA — phase 2 (plunge + spike, #973) and phase 3 (landing shockwave, #974)
# ---------------------------------------------------------------------------


def test_up_b_has_apex_plunge_phase():
    # Phase 2 (#973): exactly one VelocityPhase — a downward SET at the apex (~f38).
    # vy = +12 (= Birky max_fall_speed, the fastest a data-only plunge descends); the
    # SET must be within the move (frame <= total 44). Playtest starting points (#1095).
    m = _BIRKY.moves["up_b"]
    assert len(m.velocity_phases) == 1
    plunge = m.velocity_phases[0]
    assert plunge.frame == 38, "plunge fires at the burst apex (recovery_vy/g ≈ 37.4)"
    assert plunge.vy > 0, "the plunge is a DOWNWARD velocity SET (screen-space, +y = down)"
    assert plunge.vx == 0.0, "Final Cutter is purely vertical"
    assert plunge.frame <= m.startup + m.active + m.recovery


def test_up_b_has_descending_spike():
    # Phase 2 (#973): a downward (angle 270) meteor box active across the plunge window.
    m = _BIRKY.moves["up_b"]
    spikes = [h for h in m.hitboxes if h.angle == 270]
    assert len(spikes) == 1, "one descending spike box"
    spike = spikes[0]
    assert (spike.active_start, spike.active_end) == (38, 44)
    assert spike.damage > 0


def test_up_b_has_landing_shockwave():
    # Phase 3 (#974): a LandingSpawn beam — mirrored both ways, landing_lag 35
    # (PM SpecialAirHi4), a live spawn (>=1 hitbox, speed/lifetime > 0).
    ls = _BIRKY.moves["up_b"].landing_spawn
    assert ls is not None, "Final Cutter must carry the phase-3 landing shockwave"
    assert ls.landing_lag == 35
    assert ls.both_directions is True
    assert ls.speed > 0 and ls.lifetime > 0
    assert len(ls.hitboxes) >= 1


# ---------------------------------------------------------------------------
# LIVE — the real shipped data drives the plunge + the touchdown shockwave
# ---------------------------------------------------------------------------


def test_up_b_plunges_downward_at_apex():
    """Driven live, the real up-B's vy shows a single-frame DOWNWARD jump far larger
    than gravity — the #973 plunge SET. Able-to-fail: without `velocity_phases` vy only
    ever changes by gravity (0.42/frame), so the max downward step stays tiny."""
    p, plats = _airborne()  # floor at y=2000 → never lands during the move
    _up_b(p, plats)
    prev = p.fighter.vel.y
    max_down_step = 0.0
    for _ in range(44):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
        max_down_step = max(max_down_step, p.fighter.vel.y - prev)
        prev = p.fighter.vel.y
    assert max_down_step > 5.0, (
        f"the plunge SET should jump vy downward in one frame (got max step {max_down_step:.2f}; gravity alone is 0.42)"
    )


def test_up_b_shockwave_spawns_on_touchdown_and_routes_landing_lag():
    """Driven live over a reachable floor, the plunge carries Birky down; on touchdown
    the #974 shockwave spawns a Projectile and the fighter routes into landing_lag.
    Able-to-fail: without `landing_spawn` no Projectile spawns."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, 500, 960, 40), thin=False))
    p = Player(
        x=300,
        y=420,  # low enough that the rise stays on-stage (see _airborne); plunge lands on the floor
        controls=CONTROLS,
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="birky",
        facing_right=True,
        fighter_data=load_fighter_data("birky"),
    )
    for _ in range(3):
        p.update(_frame(set(), set()), plats, pg.sprite.Group())
    atks = pg.sprite.Group()
    _up_b(p, plats, atks)
    saw_landing_lag = False
    for _ in range(160):
        p.update(_frame(set(), set()), plats, atks)
        if p.fighter.on_ground and p.state == "landing_lag":
            saw_landing_lag = True
            break
    beams = [a for a in atks if isinstance(a, Projectile)]
    assert beams, "touchdown should spawn the shockwave Projectile"
    assert len(beams) == 2, "both_directions → a mirrored pair"
    assert saw_landing_lag, f"touchdown should route through landing_lag, ended {p.state!r}"
