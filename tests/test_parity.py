# tests/test_parity.py
from pycats.sim.runner import run_battle

FRAMES = 200


def test_backends_are_byte_identical():
    legacy = run_battle(backend="legacy", frames=FRAMES)
    statechart = run_battle(backend="statechart", frames=FRAMES)
    assert len(legacy) == len(statechart) == FRAMES
    for f, (a, b) in enumerate(zip(legacy, statechart)):
        assert a == b, f"divergence at frame {f}:\n legacy={a}\n  state={b}"
