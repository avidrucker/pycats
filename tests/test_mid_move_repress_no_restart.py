"""Mid-move attack re-press must not restart the running move (#1087).

Root cause (#961 / #1079): `entities/fighter_input.py :: handle_actions` gated the
Attack/Special/ground-smash branch only on `p.state not in ("shield","dodge",
"helpless")`. During an active move `p.state == "attack"` (or a not-yet-ticked
"idle") passes that gate, and `MoveClock.start()` unconditionally resets `_frame=0`
— so ANY re-press (CPU or human) restarted the running move to frame 1 instead of
being ignored. The Lv9 bot re-pressing B every 10f into a 48f fireball is rooted
~75% of frames because 77% of its presses restart the move before it spawns (#961).

Fix (V1, ruling #1079 Q2 = **hard-drop**): while a move is active
(`p.current_move is not None`), that branch ignores the press — no `start()`, no
restart, **no early-out window**. PM 3.6 is faithful to hard-drop: it has no input
buffer by default, so a mid-move re-press is dropped, not buffered to IASA
(research #1093, `docs/research/pm-input-buffer-findings.md`). IASA-aware interrupt
is post-V1 (#1089).

Both tests are able to fail: on `main` before the guard the re-press restarts the
move (move_frame drops back toward 0); with the guard it keeps advancing.
"""

import pygame as pg
from helpers import P1

from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player


def _frame(held=(), pressed=()):
    return InputFrame(
        held={P1[k] for k in held},
        pressed={P1[k] for k in pressed},
        released=set(),
    )


def _nalio():
    """A bare grounded nalio (no settling loop) — enough to drive handle_actions."""
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="nalio", facing_right=True)
    p.fighter.on_ground = True
    return p


def _grounded_nalio():
    """Nalio settled at rest on solid ground, for the full-loop `update()` repro."""
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="nalio", facing_right=True)
    plats = [Platform(pg.Rect(0, 300, 600, 20), thin=False)]
    grp = pg.sprite.Group()
    for _ in range(240):
        p.update(_frame(), plats, grp)
        if p.fighter.on_ground:
            break
    assert p.fighter.on_ground and p.fighter.vel.x == 0, "setup: expected a fighter at rest on the ground"
    return p, plats, grp


# ---- mechanism level: handle_actions must not re-start an active clock ------


def test_repress_via_handle_actions_does_not_reset_move_frame():
    """Tightest form: start the jab through the input seam, hand-advance the clock a
    few frames, then re-press attack through the SAME seam. The re-press must be
    ignored — `move_frame` stays where the ticks left it. On `main` (no guard) the
    re-press calls `MoveClock.start()` and `move_frame` snaps back to 0."""
    p = _nalio()
    grp = pg.sprite.Group()
    p.handle_actions(_frame(held=("attack",), pressed=("attack",)), grp)
    assert p.current_move is not None, "setup: a move should be running after the first press"
    p._clock.tick()
    p._clock.tick()
    p._clock.tick()
    frame_before = p.move_frame
    assert frame_before == 3, "setup: three ticks should put the move at frame 3"
    p.handle_actions(_frame(held=("attack",), pressed=("attack",)), grp)
    assert p.move_frame == frame_before, "the mid-move re-press must not reset the move clock"
    assert p.current_move is not None, "the move is still running, not cleared"


# ---- full-loop repro: the ticket's exact scenario, driven through update() --


def test_mid_move_repress_keeps_move_advancing_in_the_live_loop():
    """The ticket's repro at the loop level: start a move, let it run a few frames
    with no input, then mash attack again. In `update()` the clock ticks BEFORE
    handle_actions, so with the guard `move_frame` advances one more; on `main` the
    re-press restarts the move and `move_frame` collapses back toward 0."""
    p, plats, grp = _grounded_nalio()
    p.update(_frame(held=("attack",), pressed=("attack",)), plats, grp)
    assert p.current_move is not None, "setup: a move should be running"
    for _ in range(3):
        p.update(_frame(), plats, grp)
    frame_before = p.move_frame
    assert frame_before > 0, "setup: the move should have advanced past frame 0"
    p.update(_frame(held=("attack",), pressed=("attack",)), plats, grp)
    assert p.current_move is not None, "the move is still running after the re-press"
    assert p.move_frame > frame_before, "the re-press must not restart the move; it keeps advancing"
