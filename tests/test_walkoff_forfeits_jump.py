"""Walk-off forfeits the grounded jump — the takeoff clamp (#473, ruling #466).

PM-faithful rule: leaving the ground **without jumping** forfeits the grounded jump,
so only the midair jump(s) remain. pycats resets `jumps_remaining = max_jumps` on
landing (`_handle_landing`); this pins the symmetric ground→air clamp
(`_handle_takeoff`): on any takeoff the count drops to at most `max_jumps - 1`.

Every takeoff cause collapses to the same clamp, without knowing which:
- **jumped off** — already decremented to `max_jumps-1` by the jump press → clamp is a no-op;
- **walked / fell / dropped off** — `max_jumps` → clamped to `max_jumps-1` (midair only);
- **launched (hitstun)** — input gated, still `max_jumps` → clamped to `max_jumps-1`.

`ledges` is deliberately NOT passed to `update()` (defaults to `()`), so a walk-off is a
clean ground→air transition with no ledge-grab intercepting it.
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame
from pycats.config import P1_COLOR, WHITE

CONTROLS = {
    "left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
    "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e,
}
RIGHT, UP, DOWN = pg.K_d, pg.K_w, pg.K_s


def _frame(held=(), pressed=()):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _grounded(plat_rect, spawn_x, thin=False):
    """A player standing on `plat_rect`. Spawns airborne (pycats default), idle-falls
    onto the platform. Returns (player, platforms) with full jumps confirmed."""
    plats = pg.sprite.Group()
    plats.add(Platform(plat_rect, thin=thin))
    p = Player(x=spawn_x, y=plat_rect.top - 80, controls=CONTROLS,
               color=P1_COLOR, eye_color=WHITE, char_name="JumpCat", facing_right=True)
    for _ in range(90):
        p.update(_frame(), plats, pg.sprite.Group())
        if p.fighter.on_ground:
            break
    assert p.fighter.on_ground, "fixture precondition: grounded"
    assert p.fighter.jumps_remaining == p.fighter.max_jumps, "fixture: full jumps on ground"
    return p, plats


def _step_until_airborne(p, plats, held=(), max_frames=180):
    for _ in range(max_frames):
        p.update(_frame(held=held), plats, pg.sprite.Group())
        if not p.fighter.on_ground:
            return
    raise AssertionError("fighter never left the ground within the window")


def test_walk_off_forfeits_grounded_jump():
    """Walk off the edge (no jump press) → only the midair jump remains."""
    plat = pg.Rect(200, 400, 180, 40)            # spans x=200..380
    p, plats = _grounded(plat, spawn_x=360)      # near the right lip
    _step_until_airborne(p, plats, held={RIGHT})
    assert p.fighter.jumps_remaining == p.fighter.max_jumps - 1, (
        "walking off the ground forfeits the grounded jump (midair jump only)"
    )


def test_jump_off_does_not_double_decrement():
    """Jumping off must leave exactly max_jumps-1 — the jump press already spent one,
    so the takeoff clamp must be a no-op, not a second decrement."""
    plat = pg.Rect(100, 400, 500, 40)
    p, plats = _grounded(plat, spawn_x=350)
    # press jump; step until airborne
    p.update(_frame(held={UP}, pressed={UP}), plats, pg.sprite.Group())
    _step_until_airborne(p, plats)
    assert p.fighter.jumps_remaining == p.fighter.max_jumps - 1, (
        "jump-off must not double-decrement (jump press + clamp)"
    )


def test_launched_off_keeps_midair_jump():
    """A launch off the ground (upward velocity, no jump press) → max_jumps-1."""
    plat = pg.Rect(100, 400, 500, 40)
    p, plats = _grounded(plat, spawn_x=350)
    p.fighter.hurt_timer = 20          # in hitstun: input is gated, jumps stay max
    p.fighter.vel.y = -22              # launched upward
    _step_until_airborne(p, plats)
    assert p.fighter.jumps_remaining == p.fighter.max_jumps - 1, (
        "a launched fighter forfeits the grounded jump but keeps its midair jump"
    )


def test_drop_through_thin_platform_forfeits_grounded_jump():
    """Drop-through a thin platform (down-press, no jump) → max_jumps-1 (PM-faithful, #480)."""
    plat = pg.Rect(100, 400, 500, 40)
    p, plats = _grounded(plat, spawn_x=350, thin=True)
    _step_until_airborne(p, plats, held={DOWN})
    assert p.fighter.jumps_remaining == p.fighter.max_jumps - 1, (
        "dropping through a thin platform is a no-jump takeoff: forfeits the grounded jump"
    )


def test_fresh_airborne_spawn_keeps_full_jumps():
    """A freshly spawned fighter (airborne per today's model) is not clamped below
    max_jumps — there is no ground→air transition, so the clamp must not fire (#480)."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, 600, 960, 40), thin=False))
    p = Player(x=300, y=100, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE,
               char_name="SpawnCat", facing_right=True)
    assert not p.fighter.on_ground, "today's model: spawns airborne"
    assert p.fighter.jumps_remaining == p.fighter.max_jumps, "fresh spawn keeps full jumps"
    # a couple of airborne frames must not erode the count (was_airborne stays True)
    for _ in range(3):
        p.update(_frame(), plats, pg.sprite.Group())
    assert p.fighter.jumps_remaining == p.fighter.max_jumps, (
        "airborne spawn must retain full jumps until it actually lands"
    )
