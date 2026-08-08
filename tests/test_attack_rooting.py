"""Grounded-attack rooting — held input can't extend travel during a move (#935).

Companion to `test_tilt_no_walk_drift.py` (#898), which covers the *from-rest*
ground case (a tilt begun from a standstill stays planted). This file covers the
cases that file does not, all grounded in the #922 audit
(`docs/research/move-during-attack-findings.md`):

- **Prior momentum bleeds, held input adds nothing** — a fighter that enters an
  attack at walk speed keeps sliding under friction only; the held direction can't
  sustain or re-apply walk speed (the literal "can't move *further*").
- **Reverse input is inert** — holding the opposite direction can't turn the fighter.
- **Every phase** — the lock holds in startup, active, AND recovery (not just the
  active window), because `attack_timer` spans the whole move.
- **Air drift is preserved** — an aerial still drifts; the lock is `on_ground`-gated,
  so this guard reddens if a fix ever over-locks the air.

Mechanism under test: `FighterInput.handle_move` passes `locked=True` to
`step_horizontal` when `attack_timer > 0 and on_ground`; friction (step 1 of
`step_horizontal`) always runs, so pre-existing momentum decays but held left/right
is ignored. Remove the `on_ground` guard and the air test fails; drop the
`attack_timer` term (or unlock any single phase) and the ground tests fail.
"""

import pygame as pg
from helpers import P1

from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player


def _mk_frame(held=(), pressed=()):
    return InputFrame(
        held={P1[k] for k in held},
        pressed={P1[k] for k in pressed},
        released=set(),
    )


def _grounded_nalio():
    """Nalio settled at rest on solid ground (vel.x == 0)."""
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="nalio", facing_right=True)
    plats = [Platform(pg.Rect(0, 300, 600, 20), thin=False)]
    grp = pg.sprite.Group()
    for _ in range(240):
        p.update(_mk_frame(), plats, grp)
        if p.fighter.on_ground:
            break
    assert p.fighter.on_ground and p.fighter.vel.x == 0, "setup: expected a fighter at rest on the ground"
    return p, plats, grp


def _airborne_nalio():
    """Nalio a couple frames into a fall — airborne with vel.x == 0."""
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="nalio", facing_right=True)
    plats = [Platform(pg.Rect(0, 300, 600, 20), thin=False)]
    grp = pg.sprite.Group()
    for _ in range(2):
        p.update(_mk_frame(), plats, grp)
    assert not p.fighter.on_ground, "setup: expected an airborne fighter"
    assert p.fighter.vel.x == 0, f"setup: expected no horizontal velocity, got {p.fighter.vel.x}"
    return p, plats, grp


def _walk_to_speed(p, plats, grp, direction):
    """Walk `direction` until at full walk speed. First frame presses (arms the
    dash window but does not dash); later frames hold with an empty `pressed` so
    the double-tap detector never fires — steady walk, not a dash burst."""
    p.update(_mk_frame(held=(direction,), pressed=(direction,)), plats, grp)
    for _ in range(6):
        p.update(_mk_frame(held=(direction,)), plats, grp)
    speed = p.fighter.move_speed
    assert abs(p.fighter.vel.x) == speed, f"setup: expected walk speed {speed}, got {p.fighter.vel.x}"
    assert p.fighter.dash_timer == 0, "setup: fighter dashed; wanted a plain walk"
    return p.fighter.vel.x


def _play_move(p, plats, grp, hold=()):
    """Play the current move to completion while holding `hold`. Every recorded
    frame is a locked (in-move) frame: the loop reads `attack_timer` BEFORE each
    update, so the frame that ticks the clock to 0 is still recorded as in-move,
    and no post-move frame (which would re-enable walking) is ever held.
    Returns a list of (move_frame, vel_x, on_ground)."""
    rows = []
    frame = _mk_frame(held=hold)
    while p.attack_timer > 0:
        p.update(frame, plats, grp)
        rows.append((p.move_frame, p.fighter.vel.x, p.fighter.on_ground))
    return rows


# --------------------------------------------------------------------------- #
# 1. Prior momentum bleeds off; held input can't add walk speed.
# --------------------------------------------------------------------------- #
def test_prior_momentum_bleeds_but_held_input_adds_no_walk():
    """Walk into a forward-tilt at full speed, keep holding forward: the fighter
    slides only as friction decays the entry velocity, never re-climbing to walk
    speed, and comes to rest before the move ends."""
    p, plats, grp = _grounded_nalio()
    speed = p.fighter.move_speed
    entry = _walk_to_speed(p, plats, grp, "right")
    assert entry == speed

    # Trigger the forward-tilt while still holding right (fresh press = attack only,
    # so the held right can't re-arm a dash).
    p.update(_mk_frame(held=("right", "attack"), pressed=("attack",)), plats, grp)
    assert p.current_move is not None and p.current_move.name == "forward tilt", (
        f"expected forward tilt, got {p.current_move and p.current_move.name!r}"
    )
    trigger_vx = p.fighter.vel.x
    # The trigger frame applied friction (halved), not walk speed.
    assert 0 < trigger_vx < speed, f"expected friction-only decay on the trigger frame, got {trigger_vx}"

    rows = _play_move(p, plats, grp, hold=("right",))
    vxs = [trigger_vx] + [vx for _, vx, _ in rows]
    # Monotonically non-increasing magnitude — never re-accelerates under held input.
    for prev, cur in zip(vxs, vxs[1:]):
        assert abs(cur) <= abs(prev) + 1e-9, f"velocity re-climbed under held input: {prev} -> {cur}"
    # Never reaches walk speed again after the trigger.
    assert max(abs(vx) for vx in vxs[1:]) < speed, "held input re-applied walk speed mid-move"
    # Comes fully to rest before the move ends (ftilt is 30f; a decay from 3 hits 0 in ~7).
    assert vxs[-1] == 0, f"expected the slide to bleed to 0 within the move, ended at {vxs[-1]}"


# --------------------------------------------------------------------------- #
# 2. Reverse input can't turn the fighter mid-move.
# --------------------------------------------------------------------------- #
def test_held_reverse_input_cannot_turn_the_fighter_during_a_move():
    """Walk right into a forward-tilt, then hold LEFT for the rest of the move:
    velocity only decays toward 0, never crossing sign — input can't reverse it."""
    p, plats, grp = _grounded_nalio()
    _walk_to_speed(p, plats, grp, "right")

    p.update(_mk_frame(held=("right", "attack"), pressed=("attack",)), plats, grp)
    assert p.current_move is not None and p.current_move.name == "forward tilt"
    trigger_vx = p.fighter.vel.x
    assert trigger_vx > 0

    rows = _play_move(p, plats, grp, hold=("left",))
    vxs = [vx for _, vx, _ in rows]
    # If the lock broke, held-left would drive vel.x to -move_speed.
    assert min(vxs) >= 0, f"held-left reversed the fighter mid-move: min vel.x={min(vxs)}"
    assert max(vxs) <= trigger_vx + 1e-9, "velocity grew under held-left"
    assert vxs[-1] == 0, f"expected the fighter to stop, ended at {vxs[-1]}"


# --------------------------------------------------------------------------- #
# 3. The lock holds in every phase (startup / active / recovery), from rest.
# --------------------------------------------------------------------------- #
def test_ground_rooting_holds_in_every_phase_from_rest():
    """From a standstill, hold right through a forward-tilt: vel.x stays 0 in
    startup, active, AND recovery — a regression that unlocks any single phase
    would let the held right apply walk speed in that phase."""
    p, plats, grp = _grounded_nalio()

    p.update(_mk_frame(held=("right", "attack"), pressed=("attack",)), plats, grp)
    move = p.current_move
    assert move is not None and move.name == "forward tilt"
    startup, active = move.startup, move.active  # active window: startup < frame <= startup+active

    seen = {"startup": 0, "active": 0, "recovery": 0}
    for mf, vx, on_ground in _play_move(p, plats, grp, hold=("right",)):
        if mf <= startup:
            phase = "startup"
        elif mf <= startup + active:
            phase = "active"
        else:
            phase = "recovery"
        seen[phase] += 1
        assert on_ground, f"fighter left the ground during {phase} (frame {mf})"
        assert vx == 0, f"held right applied walk speed in {phase} (frame {mf}): vel.x={vx}"

    # Coverage guard: we actually sampled all three phases.
    for phase, n in seen.items():
        assert n > 0, f"no frame sampled in {phase} phase (seen={seen})"


# --------------------------------------------------------------------------- #
# 4. Air drift is preserved — the lock is on_ground-gated (guards against over-lock).
# --------------------------------------------------------------------------- #
def test_aerial_attack_keeps_air_drift():
    """An airborne attack must NOT be rooted (#922): holding right through an
    aerial drives vel.x to full drift speed. This reddens if the on_ground guard
    is ever dropped and the air gets locked like the ground."""
    p, plats, grp = _airborne_nalio()
    speed = p.fighter.move_speed

    p.update(_mk_frame(held=("right", "attack"), pressed=("attack",)), plats, grp)
    assert p.current_move is not None, "expected an aerial to fire"
    assert not p.fighter.on_ground, "setup: fighter landed on the trigger frame"

    drift = [p.fighter.vel.x]  # trigger frame already drifts if unlocked
    while p.attack_timer > 0 and not p.fighter.on_ground:
        p.update(_mk_frame(held=("right",)), plats, grp)
        if not p.fighter.on_ground:
            drift.append(p.fighter.vel.x)

    assert max(drift) == speed, f"aerial drift was locked; max vel.x={max(drift)}, expected {speed}"
