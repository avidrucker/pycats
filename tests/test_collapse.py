"""
tests/test_collapse.py

R6 (#862, child of #792): the collapse contract (design §1.3). `collapse` folds a
move's per-frame provenance into canonical windowed `Hitbox`es. The runtime never
runs it; the editor Save (E5) and the drift-guard (R7) do, so it must be exact.

The primary oracle is the real Nalio jab (`nalio_cat.py` _JAB): its worked
provenance (design §1.1 — frames 2 & 3 identical, all three boxes) must collapse
back to `_JAB.hitboxes` byte-for-byte, windows canonicalized to None. Able-to-fail:
the fixtures below assert exact structures; a wrong fold, a dropped
canonicalization, or a non-deterministic order breaks a specific assertion.
"""

from pycats.characters.nalio_cat import _JAB
from pycats.combat.collapse import collapse
from pycats.combat.data import Circle, Hitbox

# The design §1.1 worked example: Nalio jab (startup=1, active=2 → default window
# [2,3]), three boxes all present + identical on frames 2 and 3.
_JAB_FRAMES = [
    {
        "frame": 2,
        "boxes": [
            {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20},
        ],
    },
    {
        "frame": 3,
        "boxes": [
            {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20},
        ],
    },
]


def test_nalio_jab_collapses_to_the_python_oracle():
    # The headline golden-safety guarantee: the per-frame trace folds back to the
    # exact hand-written _JAB.hitboxes, windows canonicalized to None.
    result = collapse(_JAB_FRAMES, startup=1, active=2)
    assert result == _JAB.hitboxes


def test_nalio_jab_windows_canonicalize_to_none():
    # Step 3: every box spans the default window [2,3], so active_start/end drop
    # to None (not left as an explicit [2,3]) — that None is what keeps the
    # serialized bytes identical to today's Python.
    result = collapse(_JAB_FRAMES, startup=1, active=2)
    assert all(hb.active_start is None and hb.active_end is None for hb in result)


def test_shuffled_frame_and_box_order_is_deterministic():
    # Step 4: author edit order must not leak into the output tuple.
    shuffled = [
        {
            "frame": 3,
            "boxes": [
                {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20},
                {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
                {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            ],
        },
        {
            "frame": 2,
            "boxes": [
                {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
                {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20},
                {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20},
            ],
        },
    ]
    assert collapse(shuffled, startup=1, active=2) == _JAB.hitboxes


def test_moving_box_yields_a_one_frame_window_staircase():
    # Step 2: a box whose circle changes every frame breaks the run each frame →
    # one 1-frame-window Hitbox per frame (the ratified static staircase). Windows
    # are NOT canonicalized (they are not all the default window), so they persist.
    frames = [
        {"frame": 4, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40}]},
        {"frame": 5, "boxes": [{"id": 0, "circle": [14, 0, 8], "damage": 5.0, "angle": 40}]},
        {"frame": 6, "boxes": [{"id": 0, "circle": [18, 0, 8], "damage": 5.0, "angle": 40}]},
    ]
    result = collapse(frames, startup=3, active=3)  # default window would be [4,6]
    assert result == (
        Hitbox(circle=Circle(10, 0, 8), damage=5.0, angle=40, active_start=4, active_end=4),
        Hitbox(circle=Circle(14, 0, 8), damage=5.0, angle=40, active_start=5, active_end=5),
        Hitbox(circle=Circle(18, 0, 8), damage=5.0, angle=40, active_start=6, active_end=6),
    )


def test_blinking_box_yields_two_windows_under_one_id():
    # Step 2: a gap in an id's frames closes the run and opens a new one → two
    # Hitboxes sharing the box's geometry/scalars/id, distinct windows.
    frames = [
        {"frame": 4, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40}]},
        {"frame": 5, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40}]},
        # frame 6: box absent (blink off)
        {"frame": 7, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40}]},
    ]
    result = collapse(frames, startup=3, active=4)  # default [4,7]; neither run matches
    assert result == (
        Hitbox(circle=Circle(10, 0, 8), damage=5.0, angle=40, active_start=4, active_end=5),
        Hitbox(circle=Circle(10, 0, 8), damage=5.0, angle=40, active_start=7, active_end=7),
    )
