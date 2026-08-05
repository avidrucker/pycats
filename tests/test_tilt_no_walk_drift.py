"""A grounded normal begun while a direction is held stays planted (#898).

The bug: `Player.update` runs `handle_actions` (which starts the attack) and then
`handle_move`, which applied walk speed for any held left/right — so a forward-tilt
(Right + A) slid the fighter ~10px instead of rooting it. Up/down tilts never drifted
because `handle_move` only reacts to left/right, so `forward` was the asymmetric case.

The fix roots the fighter for the whole grounded attack: while a move is on the clock
and the fighter is on the ground, `handle_move` is `locked` (friction still bleeds any
prior momentum, but held left/right no longer applies walk speed). Airborne attacks
keep their air drift (the lock is `on_ground`-gated).

Red on `main` (forward-tilt drifts ~10px); green with the lock.
"""

import pygame as pg
from helpers import P1

from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player


def _frame(*keys):
    ks = {P1[k] for k in keys}
    return InputFrame(held=ks, pressed=ks, released=set())


def _neutral():
    return InputFrame(held=set(), pressed=set(), released=set())


def _grounded_nalio():
    """Nalio settled at rest on solid ground (vel.x == 0)."""
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="nalio", facing_right=True)
    plats = [Platform(pg.Rect(0, 300, 600, 20), thin=False)]
    grp = pg.sprite.Group()
    for _ in range(240):
        p.update(_neutral(), plats, grp)
        if p.fighter.on_ground:
            break
    assert p.fighter.on_ground and p.fighter.vel.x == 0, "setup: expected a fighter at rest on the ground"
    return p, plats, grp


def _play_out_grounded(p, plats, grp, trigger):
    """Fire `trigger` on one frame from standstill, then let the move play to
    completion. Returns (x0, drift, trigger_vel_x, move_name)."""
    x0 = p.rect.x
    p.update(trigger, plats, grp)
    move = p.current_move
    trigger_vel_x = p.fighter.vel.x
    move_name = move.name if move else None
    for _ in range(p.attack_timer + 5):
        p.update(_neutral(), plats, grp)
    return x0, p.rect.x - x0, trigger_vel_x, move_name


def test_forward_tilt_from_standing_does_not_drift():
    """Right + A from a standstill fires the forward-tilt and stays planted."""
    p, plats, grp = _grounded_nalio()
    x0, drift, trigger_vel_x, move_name = _play_out_grounded(p, plats, grp, _frame("right", "attack"))
    assert move_name == "forward tilt", f"expected the forward-tilt to fire, got {move_name!r}"
    # Mechanism: the trigger frame must not apply walk speed (the cause of the drift).
    assert trigger_vel_x == 0, f"walk speed leaked onto the attack frame: vel.x={trigger_vel_x}"
    # Result: no horizontal translation across the whole move.
    assert drift == 0, f"forward-tilt drifted {drift}px; expected 0"


def test_up_and_down_tilt_and_jab_still_do_not_drift():
    """Regression guard: up-tilt / down-tilt / neutral jab already stayed put
    (their direction isn't a left/right walk input) — keep it that way."""
    for keys, expected in (
        (("up", "attack"), "up tilt"),
        (("down", "attack"), "down tilt"),
        (("attack",), None),  # neutral jab: name not asserted, only the no-drift property
    ):
        p, plats, grp = _grounded_nalio()
        x0, drift, _trigger_vel_x, move_name = _play_out_grounded(p, plats, grp, _frame(*keys))
        assert p.current_move is None or drift == 0, f"{keys} drifted {drift}px"
        if expected is not None:
            assert move_name == expected, f"{keys} fired {move_name!r}, expected {expected!r}"
        assert drift == 0, f"{keys} drifted {drift}px; expected 0"
