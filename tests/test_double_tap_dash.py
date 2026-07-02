"""#403 (slice 2b of #388): double-tap detection wires `_start_dash`.

Slice 2a (#396) built the dash machinery (`_start_dash`, `dash_timer`, the `dash`
leaf, `dash_speed`) but nothing called it. This slice adds the input edge-timing
so a fast double-tap of a direction fires `_start_dash(direction)` — turning the
dash machinery into a reachable behaviour.

Driven through the public `Player.update(...)` API (like test_dodge_mechanics.py):
a genuine double-tap is press → release → press, so the second press is a FRESH
`pressed` key (a held key is only in `pressed` the frame it goes down). Held or
single presses stay `walk` (golden-safe); a tap outside the window re-arms rather
than dashing; and a hit-stunned fighter never dashes off a stale window (#370).
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import P1_COLOR, WHITE, DOUBLE_TAP_WINDOW, DASH_SPEED

CONTROLS = {
    "left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
    "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e,
}
LEFT, RIGHT = pg.K_a, pg.K_d


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _grounded_player():
    """A player settled on a thick floor (one empty frame to land)."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, 400, 800, 40), thin=False))
    p = Player(x=400, y=400, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE,
               char_name="DashCat", facing_right=True)
    p.update(_frame(set(), set()), plats, pg.sprite.Group())  # settle on ground
    return p, plats


def _step(p, plats, held=(), pressed=()):
    p.update(_frame(held, pressed), plats, pg.sprite.Group())


def _tap(p, plats, key):
    """One frame with the key freshly pressed, then one frame released — a tap."""
    _step(p, plats, held={key}, pressed={key})
    _step(p, plats, held=set(), pressed=set())


# ---- the double-tap fires _start_dash ----

def test_double_tap_within_window_starts_dash():
    p, plats = _grounded_player()
    # first tap (press + release), then a second press well within the window
    _step(p, plats, held={RIGHT}, pressed={RIGHT})
    _step(p, plats, held=set(), pressed=set())  # release, 1 frame < window
    _step(p, plats, held={RIGHT}, pressed={RIGHT})  # second tap -> dash
    assert p.state == "dash"
    assert p.fighter.dash_timer > 0
    assert p.fighter.vel.x == DASH_SPEED  # dashing right


def test_double_tap_left_dashes_left():
    p, plats = _grounded_player()
    _step(p, plats, held={LEFT}, pressed={LEFT})
    _step(p, plats, held=set(), pressed=set())
    _step(p, plats, held={LEFT}, pressed={LEFT})
    assert p.state == "dash"
    assert p.fighter.vel.x == -DASH_SPEED
    assert p.fighter.facing_right is False


# ---- non-double-taps never dash (golden-safe) ----

def test_single_press_walks_never_dashes():
    p, plats = _grounded_player()
    _step(p, plats, held={RIGHT}, pressed={RIGHT})
    assert p.state == "walk"
    assert p.fighter.dash_timer == 0


def test_held_direction_never_dashes():
    # a HELD key is fresh (`pressed`) only the first frame; holding never re-fires.
    p, plats = _grounded_player()
    for i in range(DOUBLE_TAP_WINDOW + 5):
        pressed = {RIGHT} if i == 0 else set()
        _step(p, plats, held={RIGHT}, pressed=pressed)
        assert p.state != "dash", f"held direction dashed on frame {i}"


def test_two_presses_outside_window_do_not_dash():
    p, plats = _grounded_player()
    _step(p, plats, held={RIGHT}, pressed={RIGHT})  # first tap opens the window
    for _ in range(DOUBLE_TAP_WINDOW + 2):          # let it expire
        _step(p, plats, held=set(), pressed=set())
    _step(p, plats, held={RIGHT}, pressed={RIGHT})  # too late -> re-arm, not dash
    assert p.state != "dash"


def test_opposite_direction_second_tap_does_not_dash():
    p, plats = _grounded_player()
    _step(p, plats, held={RIGHT}, pressed={RIGHT})  # arm right
    _step(p, plats, held=set(), pressed=set())
    _step(p, plats, held={LEFT}, pressed={LEFT})    # different direction -> no dash
    assert p.state != "dash"


# ---- the #370 timer-gate: no dash out of hitstun on a stale window ----

def test_no_dash_during_hitstun_via_player_update():
    # Player.update skips handle_actions entirely during hitstun, so an armed
    # window can't produce a dash while hurt_timer is live.
    p, plats = _grounded_player()
    _step(p, plats, held={RIGHT}, pressed={RIGHT})  # arm the window
    p.fighter.hurt_timer = 10                        # a hit lands (label lags a frame)
    _step(p, plats, held={RIGHT}, pressed={RIGHT})  # second tap during hitstun
    assert p.state != "dash"
    assert p.fighter.dash_timer == 0


def test_no_dash_when_hurt_timer_live_even_if_label_lags():
    # The #370 guard proper: drive the detector DIRECTLY with an armed window and
    # a live hurt_timer while the label still reads a movement state (the one-frame
    # FSM lag). Gating on the timer — not the label — must block the dash.
    p, plats = _grounded_player()
    _step(p, plats, held={RIGHT}, pressed={RIGHT})   # arm the window
    assert p.fighter.dash_input_window > 0
    assert p.state in ("idle", "walk")               # label still a movement state
    p.fighter.hurt_timer = 10                         # hit lands; label hasn't flipped
    p.handle_actions(_frame({RIGHT}, {RIGHT}), pg.sprite.Group())
    assert p.fighter.dash_timer == 0                 # timer gate blocked the dash
