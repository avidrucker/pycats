"""#967 (slice 3 of #388): the sustained ``run`` state — dash → run on hold-past-window.

Slice 2 (#403) made the dash burst reachable (double-tap → ``_start_dash``), but the
burst decayed straight to ``walk``/``idle`` when its window closed. This slice adds the
sustained ``run`` leaf: keeping the dash direction held past the burst enters ``run`` at
``run_speed`` (fighter_input reads the state label); releasing the direction decays back
to ``walk``/``idle``.

Driven through the public ``Player.update(...)`` API like test_double_tap_dash.py. The two
able-to-fail regressions the ticket calls for:
  1. a PLAIN-held direction (no double-tap) never enters ``run`` — stays ``walk`` (red if
     run ever leaks into the plain-hold / golden path);
  2. a double-tap-THEN-hold enters ``run`` at ``run_speed`` after the burst (red without
     the dash → run transition).

Per ADR-0011 §Decision 4: dash != run is a STATE distinction (sustained vs. decay), not a
pixel one. For the default cat (and nalio) run == dash == round(mod_factor(1.5)) == 8; the
equal pixel is correct and intended. run_speed (8) still differs from the walk move_speed
(6), so the vel.x assertions below distinguish run from walk.
"""

import pygame as pg

from pycats.combat.data import load_fighter_data
from pycats.config import DASH_DURATION, DOUBLE_TAP_WINDOW, P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

CONTROLS = {
    "left": pg.K_a,
    "right": pg.K_d,
    "up": pg.K_w,
    "down": pg.K_s,
    "shield": pg.K_q,
    "attack": pg.K_e,
}
LEFT, RIGHT = pg.K_a, pg.K_d


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _grounded_player():
    """A player settled on a thick floor (one empty frame to land)."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, 400, 800, 40), thin=False))
    p = Player(x=400, y=400, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE, char_name="DashCat", facing_right=True)
    p.update(_frame(set(), set()), plats, pg.sprite.Group())  # settle on ground
    return p, plats


def _step(p, plats, held=(), pressed=()):
    p.update(_frame(held, pressed), plats, pg.sprite.Group())


def _hold(p, plats, key, frames):
    """Hold `key` (no fresh press) for `frames` frames."""
    for _ in range(frames):
        _step(p, plats, held={key}, pressed=set())


def _enter_dash_right(p, plats):
    """Double-tap right → the dash burst (press + release + fresh press)."""
    _step(p, plats, held={RIGHT}, pressed={RIGHT})
    _step(p, plats, held=set(), pressed=set())
    _step(p, plats, held={RIGHT}, pressed={RIGHT})


# ---- regression 1: plain-held never enters run (golden-safe) ----


def test_plain_held_never_enters_run():
    # A single held press (no double-tap) walks; it must never dash and never run —
    # so the sim/controller plain-hold path (which never double-taps) stays byte-stable.
    p, plats = _grounded_player()
    _step(p, plats, held={RIGHT}, pressed={RIGHT})  # the one fresh press
    for i in range(DASH_DURATION + DOUBLE_TAP_WINDOW + 5):
        _step(p, plats, held={RIGHT}, pressed=set())  # keep holding, never re-press
        assert p.state != "dash", f"plain-held dashed on frame {i}"
        assert p.state != "run", f"plain-held entered run on frame {i}"
    assert p.state == "walk"


# ---- regression 2: double-tap then hold enters run at run_speed ----


def test_double_tap_then_hold_enters_run_at_run_speed():
    p, plats = _grounded_player()
    _enter_dash_right(p, plats)
    assert p.state == "dash"
    # keep holding right past the burst window -> sustained run
    _hold(p, plats, RIGHT, DASH_DURATION + 2)
    assert p.state == "run", f"expected run after the burst, got {p.state!r}"
    assert p.fighter.vel.x == p.fighter.run_speed  # running at run_speed, not walk speed


def test_double_tap_left_then_hold_enters_run():
    p, plats = _grounded_player()
    _step(p, plats, held={LEFT}, pressed={LEFT})
    _step(p, plats, held=set(), pressed=set())
    _step(p, plats, held={LEFT}, pressed={LEFT})
    assert p.state == "dash"
    _hold(p, plats, LEFT, DASH_DURATION + 2)
    assert p.state == "run"
    assert p.fighter.vel.x == -p.fighter.run_speed
    assert p.fighter.facing_right is False


# ---- releasing the direction decays run -> walk -> idle ----


def test_releasing_direction_exits_run():
    p, plats = _grounded_player()
    _enter_dash_right(p, plats)
    _hold(p, plats, RIGHT, DASH_DURATION + 2)
    assert p.state == "run"
    # release: run_input_held goes False -> the still-sliding body decays to walk, then
    # idle once friction zeroes vel.x.
    for _ in range(30):
        _step(p, plats, held=set(), pressed=set())
    assert p.state == "idle"
    assert p.fighter.vel.x == 0


# ---- nalio wiring: run == dash == 8 (ADR-0011 §Decision 4) ----


def test_nalio_run_speed_matches_dash():
    """nalio's run and dash are the same raw unit (PM 3.6 Mario 1.5 u), so both derive
    round(mod_factor(1.5)) == 8. Equal pixel is intended, not a bug (#967 / ADR-0011)."""
    fd = load_fighter_data("nalio")
    assert fd.run_speed == 8
    assert fd.run_speed == fd.dash_speed
