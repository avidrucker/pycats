# tests/test_move_clock_c001.py
"""Fresh from-scratch red-green non-vacuous tests pinning PYC-C-001-GRAPE.

Claim PYC-C-001-GRAPE: In pycats every move runs on a three-phase frame clock
(`MoveClock`, `combat/move_clock.py`) with phases *startup → active → recovery*.
A move's hitbox is live only during the active phase — with POST-increment frame
counting the hit window is ``startup < frame <= startup + active`` (so the box
spawns on the first active frame ``startup + 1``) — and the move goes inactive
once the counter reaches ``startup + active + recovery``.

These are authored solely to pin that claim (its OPEN and CLOSE boundaries),
distinct from the pre-existing MoveClock unit tests in ``test_move_clock.py``
(introduced by the #71 extraction, not written to pin C-001). Each is proven
able-to-fail by the revert-checks recorded in #993:

  * OPEN  — mutate the window start off ``startup + 1`` in
    ``MoveClock._compute_windows`` (``move.startup + 1`` → ``+ 2``): the spawn
    frame shifts and ``test_c001_open_boundary_*`` go red.
  * CLOSE — loosen the completion comparison in ``MoveClock.tick``
    (``>=`` → ``>``): the move stays active one frame too long and
    ``test_c001_close_boundary_*`` go red.
"""

import pytest

from pycats.combat.data import Circle, Hitbox, MoveData
from pycats.combat.move_clock import MoveClock, MoveTick


def _move(startup=3, active=3, recovery=6):
    """A plain no-per-box-timing move, so the DEFAULT window is under test."""
    hb = Hitbox(circle=Circle(dx=10, dy=10, r=5), damage=1.0, angle=0)
    return MoveData(
        name="t",
        in_air=False,
        startup=startup,
        active=active,
        recovery=recovery,
        hitboxes=(hb,),
    )


def _spawn_frames(move):
    """Run a move to completion; return the frames on which a hitbox spawned."""
    c = MoveClock()
    c.start(move)
    total = move.startup + move.active + move.recovery
    frames = []
    for _ in range(total):
        t = c.tick()
        if t.spawn is not None:
            frames.append(c.frame)
    return frames


# -- OPEN boundary: spawns on the first active frame, and on no earlier frame --


@pytest.mark.parametrize(
    "startup, active, recovery",
    [(3, 3, 6), (5, 2, 4), (0, 1, 3), (7, 4, 1)],
)
def test_c001_open_boundary_spawns_once_on_first_active_frame(startup, active, recovery):
    """PYC-C-001-GRAPE (OPEN): the hitbox spawns exactly once, on the first
    active frame ``startup + 1``, for a default-window move. Able-to-fail:
    shifting the window start off ``startup + 1`` moves the spawn frame."""
    move = _move(startup, active, recovery)
    frames = _spawn_frames(move)
    assert frames == [startup + 1]


def test_c001_open_boundary_no_spawn_during_startup():
    """PYC-C-001-GRAPE (OPEN): no hitbox is live before the active phase — every
    startup frame (1..startup) yields ``spawn is None``. Able-to-fail: a window
    start earlier than ``startup + 1`` would spawn during startup."""
    c = MoveClock()
    c.start(_move(startup=3, active=3, recovery=6))
    for _ in range(3):  # frames 1, 2, 3 — the startup phase
        t = c.tick()
        assert t.spawn is None
    # frame 4 is the first active frame — the spawn lands here
    assert c.tick().spawn is not None


def test_c001_open_boundary_spawn_lifetime_equals_active():
    """PYC-C-001-GRAPE (OPEN): the spawning window's lifetime is the move's
    ``active`` length for a default-window move."""
    c = MoveClock()
    c.start(_move(startup=3, active=3, recovery=6))
    spawn_ticks = [t for _ in range(12) if (t := c.tick()).spawn is not None]
    assert len(spawn_ticks) == 1
    assert spawn_ticks[0].lifetime == 3


# -- CLOSE boundary: inactive exactly at startup + active + recovery -----------


@pytest.mark.parametrize(
    "startup, active, recovery",
    [(3, 3, 6), (5, 2, 4), (0, 1, 3), (7, 4, 1)],
)
def test_c001_close_boundary_inactive_exactly_at_total(startup, active, recovery):
    """PYC-C-001-GRAPE (CLOSE): the move is still active at ``total - 1`` and
    goes inactive exactly when ``frame == startup + active + recovery``.
    Able-to-fail: loosening the completion compare (``>=`` → ``>``) keeps it
    active one frame past ``total``."""
    total = startup + active + recovery
    c = MoveClock()
    c.start(_move(startup, active, recovery))
    for _ in range(total - 1):
        c.tick()
    assert c.frame == total - 1
    assert c.is_active  # not yet complete
    c.tick()
    assert c.frame == total
    assert not c.is_active  # completes exactly on reaching total
    assert c.remaining == 0


def test_c001_close_boundary_further_ticks_are_noops():
    """PYC-C-001-GRAPE (CLOSE): once complete, further ticks are no-ops — the
    frame does not advance and ``tick()`` returns ``MoveTick(None, 0)``."""
    c = MoveClock()
    c.start(_move())  # total = 12
    for _ in range(12):
        c.tick()
    assert not c.is_active
    frame_at_completion = c.frame
    assert c.tick() == MoveTick(None, 0)
    assert c.frame == frame_at_completion
    assert c.remaining == 0
