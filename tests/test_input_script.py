# tests/test_input_script.py
from helpers import P1, P2

from pycats.core.input import InputFrame
from pycats.sim.input_script import InputSpan, compile_timeline


def test_compile_length_covers_last_frame():
    frames = compile_timeline([InputSpan(0, 3, 1, "right")], [P1, P2])
    assert len(frames) == 3
    assert all(isinstance(f, InputFrame) for f in frames)


def test_held_pressed_released_edges():
    frames = compile_timeline([InputSpan(1, 3, 1, "right")], [P1, P2])
    # frame 0: nothing
    assert P1["right"] not in frames[0].held
    # frame 1: freshly pressed + held
    assert P1["right"] in frames[1].pressed
    assert P1["right"] in frames[1].held
    # frame 2: still held, not freshly pressed
    assert P1["right"] in frames[2].held
    assert P1["right"] not in frames[2].pressed


def test_release_edge_after_span_end():
    # span active frames 0..1; ensure a release edge is recorded the frame it ends
    frames = compile_timeline([InputSpan(0, 1, 1, "right")], [P1, P2])
    assert P1["right"] in frames[0].held
    # only one frame long -> no extra frame to observe release; extend:
    frames = compile_timeline([InputSpan(0, 1, 1, "right"), InputSpan(2, 3, 1, "left")], [P1, P2])
    assert P1["right"] in frames[1].released
    assert P1["right"] not in frames[1].held
