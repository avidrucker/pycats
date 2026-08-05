"""Per-fighter rolling input-history buffer (#21, regridded #875).

Pure, pygame-free logic. Records the last up-to-``INPUT_HISTORY_FRAMES`` raw
frames a player produced. Each frame stores, per control, whether it was
*pressed* this frame (the rising edge) or merely *held* (down but not fresh) —
so the HUD grid can tell a same-frame combo from a sequential press and from a
held-while-pressed one (#875). Directions are ABSOLUTE (right always = physical
right, independent of facing). The HUD grid render + Options toggle are exercised
elsewhere (test_input_history_render / test_input_history_toggle).
"""

from pycats.shell.input_history import (
    HELD,
    INPUT_HISTORY_FRAMES,
    PRESSED,
    InputHistory,
    frame_marks,
)

# A minimal controls dict shaped like game.P1_KEYS (name -> pygame keycode).
CONTROLS = {
    "left": 1,
    "right": 2,
    "up": 3,
    "down": 4,
    "attack": 5,
    "special": 6,
    "shield": 7,
}


# --------------------------------------------------------------------------- #
# frame_marks — (pressed, held) keycode sets + controls -> per-control mark
# --------------------------------------------------------------------------- #
def test_pressed_key_marks_pressed():
    # up freshly pressed this frame (in both pressed and held, edge model).
    assert frame_marks({3}, {3}, CONTROLS) == {"up": PRESSED}


def test_held_but_not_pressed_marks_held():
    # up still down but not a fresh edge -> held, not pressed.
    assert frame_marks(set(), {3}, CONTROLS) == {"up": HELD}


def test_pressed_wins_over_held_same_frame():
    # A fresh key is in .held too; the edge (PRESSED) must win.
    assert frame_marks({5}, {3, 5}, CONTROLS) == {"attack": PRESSED, "up": HELD}


def test_multiple_controls_one_frame():
    assert frame_marks({3, 5}, {3, 5}, CONTROLS) == {"up": PRESSED, "attack": PRESSED}


def test_unmapped_keycodes_ignored():
    assert frame_marks({99}, {99}, CONTROLS) == {}
    assert frame_marks({99, 5}, {99, 5}, CONTROLS) == {"attack": PRESSED}


def test_empty_frame_marks_nothing():
    assert frame_marks(set(), set(), CONTROLS) == {}


# --------------------------------------------------------------------------- #
# InputHistory — rolling window of the last N frames' marks
# --------------------------------------------------------------------------- #
def test_records_frames_oldest_to_newest():
    h = InputHistory()
    h.record({3}, {3}, CONTROLS)  # up pressed
    h.record(set(), {3}, CONTROLS)  # up held
    h.record({5}, {3, 5}, CONTROLS)  # attack pressed, up still held
    assert h.frames() == [
        {"up": PRESSED},
        {"up": HELD},
        {"attack": PRESSED, "up": HELD},
    ]


def test_idle_frames_are_recorded_as_empty_columns():
    # A gap between presses must survive as empty frames so the grid shows the gap.
    h = InputHistory()
    h.record({5}, {5}, CONTROLS)
    h.record(set(), set(), CONTROLS)
    h.record({5}, {5}, CONTROLS)
    assert h.frames() == [{"attack": PRESSED}, {}, {"attack": PRESSED}]


def test_window_caps_at_frame_count_oldest_out():
    h = InputHistory(frames=3)
    for code in (1, 2, 3, 4, 5):  # 5 distinct single-key frames (left,right,up,down,attack)
        h.record({code}, {code}, CONTROLS)
    # only the last 3 survive: up (3), down (4), attack (5)
    assert h.frames() == [
        {"up": PRESSED},
        {"down": PRESSED},
        {"attack": PRESSED},
    ]


def test_held_while_pressed_is_distinct_from_sequential_tap():
    """The #875 core: hold-A-then-press-Up must differ from tap-A-then-tap-Up."""
    held_then = InputHistory()
    held_then.record({5}, {5}, CONTROLS)  # press A
    held_then.record({3}, {3, 5}, CONTROLS)  # press Up while A still held

    seq_taps = InputHistory()
    seq_taps.record({5}, {5}, CONTROLS)  # tap A
    seq_taps.record({3}, {3}, CONTROLS)  # tap Up, A already released

    assert held_then.frames() != seq_taps.frames()
    assert held_then.frames()[1] == {"up": PRESSED, "attack": HELD}
    assert seq_taps.frames()[1] == {"up": PRESSED}


def test_default_window_is_the_named_constant():
    h = InputHistory()
    for _ in range(INPUT_HISTORY_FRAMES + 5):
        h.record({5}, {5}, CONTROLS)
    assert len(h.frames()) == INPUT_HISTORY_FRAMES
