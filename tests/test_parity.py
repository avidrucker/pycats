# tests/test_parity.py
from pycats.sim.runner import run_battle, KEYMAPS
from pycats.sim.input_script import compile_timeline, COMBAT_SCRIPT

FRAMES = 200


def test_backends_are_byte_identical():
    legacy = run_battle(backend="legacy", frames=FRAMES)
    statechart = run_battle(backend="statechart", frames=FRAMES)
    assert len(legacy) == len(statechart) == FRAMES
    for f, (a, b) in enumerate(zip(legacy, statechart)):
        assert a == b, f"divergence at frame {f}:\n legacy={a}\n  state={b}"


def test_combat_scenario_byte_identical_and_reaches_hurt_and_ko():
    """Parity test for hurt->fall/idle and ko->respawn->idle arcs.

    COMBAT_SCRIPT drives P1 to land several grounded hits on P2, building up
    enough knockback for P2 to be sent off the right blast zone (ko).  Both
    backends must produce byte-identical per-frame snapshots, AND the run must
    contain at least one frame where a player is in 'hurt' and at least one
    where a player is in 'ko'.
    """
    frame_inputs = compile_timeline(COMBAT_SCRIPT, KEYMAPS)
    frames = len(frame_inputs) + 240  # run long enough for ko + respawn
    legacy = run_battle(backend="legacy", frames=frames, frame_inputs=frame_inputs)
    statechart = run_battle(backend="statechart", frames=frames,
                            frame_inputs=frame_inputs)

    assert len(legacy) == len(statechart) == frames, (
        f"snapshot count mismatch: legacy={len(legacy)}, statechart={len(statechart)}"
    )

    for f, (a, b) in enumerate(zip(legacy, statechart)):
        assert a == b, f"divergence at frame {f}:\n legacy={a}\n  state={b}"

    # Verify that hurt and ko states are actually reached
    all_states = set()
    for snap in legacy:
        players, _atk, _phase, _winner = snap
        for p in players:
            all_states.add(p[1])  # state label is index 1 in each player tuple

    assert "hurt" in all_states, (
        f"'hurt' state never reached in combat scenario; visited states: {sorted(all_states)}"
    )
    assert "ko" in all_states, (
        f"'ko' state never reached in combat scenario; visited states: {sorted(all_states)}"
    )
