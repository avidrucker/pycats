# tests/test_dual_controller.py
"""Dual-controller seam (#49, child A of #47).

Drive BOTH players from per-player controllers, merging their emitted frames by
set-union. Safe because P1/P2 keymaps are disjoint and Player._pressed filters by
self.controls, so the union is unambiguous.
"""
import pytest

from pycats.core.input import InputFrame, merge_frames
from pycats.sim.runner import run_battle, P1_KEYS
from pycats.sim.controllers import ChaseController


def test_merge_frames_unions_held_pressed_released():
    a = InputFrame(held={1, 2}, pressed={2}, released={9})
    b = InputFrame(held={3}, pressed={3}, released=set())
    m = merge_frames([a, b])
    assert m.held == {1, 2, 3}
    assert m.pressed == {2, 3}
    assert m.released == {9}


def test_merge_frames_empty_is_identity():
    a = InputFrame(held={7}, pressed={7}, released=set())
    empty = InputFrame(held=set(), pressed=set(), released=set())
    m = merge_frames([a, empty])
    assert m.held == {7} and m.pressed == {7} and m.released == set()
    # merging does not mutate the inputs
    assert a.held == {7}


def _p1_x(snap):
    return snap[0][0][2]  # parts[P1].rect.x


def _p2_x(snap):
    return snap[0][1][2]  # parts[P2].rect.x


def test_controllers_drives_both_players_in_pre_contact_window():
    """A controller per player moves BOTH players. Asserted on the first 20 frames
    — before the first hit (frame ~33) — so the motion is input-driven, not the
    knockback a single attacker would impart on an idle target (which would let a
    broken `controllers` merge pass anyway). Both moving early ⇒ the union of the
    two emitted frames is actually applied, not just the first controller's."""
    c1 = ChaseController(attacker_num=1)
    c2 = ChaseController(attacker_num=2)
    snaps = run_battle("legacy", frames=40, controllers=(c1, c2))
    window = 20
    p1_early = [_p1_x(s) for s in snaps[:window]]
    p2_early = [_p2_x(s) for s in snaps[:window]]
    assert len(set(p1_early)) > 1, "P1 did not move pre-contact — slot-0 controller ignored"
    assert len(set(p2_early)) > 1, "P2 did not move pre-contact — slot-1 controller ignored"


def test_single_controller_equals_controllers_tuple_with_none():
    """`controller=c` must be byte-identical to `controllers=(c, None)`."""
    old = run_battle("legacy", frames=200, controller=ChaseController(1))
    new = run_battle("legacy", frames=200, controllers=(ChaseController(1), None))
    assert old == new


def test_p2_controller_emits_no_p1_keycodes():
    """Load-bearing invariant: a P2-bound controller only emits P2 keycodes."""
    c2 = ChaseController(attacker_num=2)
    run_battle("legacy", frames=300, controllers=(None, c2))
    emitted = set().union(
        *(f.held | f.pressed | f.released for f in c2.emitted)
    ) if c2.emitted else set()
    assert emitted, "P2 controller never emitted anything to check"
    assert emitted.isdisjoint(set(P1_KEYS.values())), (
        f"P2 controller leaked P1 keycodes: {emitted & set(P1_KEYS.values())}"
    )


def test_capture_and_replay_byte_identical_across_backends():
    """Freeze the merged 2-NPC stream, replay it through both backends identically,
    and confirm the replay reproduces the original live capture run."""
    c1 = ChaseController(attacker_num=1)
    c2 = ChaseController(attacker_num=2)
    live = run_battle("legacy", frames=300, controllers=(c1, c2))
    inputs = [merge_frames([a, b]) for a, b in zip(c1.emitted, c2.emitted)]
    assert len(inputs) == len(live) == 300

    replay_legacy = run_battle("legacy", frames=len(inputs), frame_inputs=inputs)
    replay_state = run_battle("statechart", frames=len(inputs), frame_inputs=inputs)

    assert live == replay_legacy, "captured stream does not reproduce the live run"
    assert replay_legacy == replay_state, "backends diverge on the frozen 2-NPC stream"


def test_controller_and_controllers_together_is_an_error():
    c = ChaseController(1)
    with pytest.raises(ValueError):
        run_battle("legacy", frames=10, controller=c, controllers=(c, None))
