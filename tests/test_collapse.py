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

#1029: collapse now PRESERVES each box's assigned letter (the editor stamps a
`"label"` on every provenance box) onto `Hitbox.label`, instead of recomputing a
rank among the ids. The letter is a stable identity — deleting a *middle* box does
not re-letter the survivors. A provenance box with no `"label"` key collapses to
`Hitbox.label = None` (assignment/validation live editor-side, not in the pure
fold).
"""

from dataclasses import replace

from pycats.characters.nalio_cat import _JAB
from pycats.combat.collapse import collapse
from pycats.combat.data import Circle, Hitbox

# The jab's three boxes carry labels A/B/C in the editor's provenance. The
# committed _JAB.hitboxes is unlabeled (migrated data), so the oracle is _JAB with
# the preserved A/B/C labels grafted on.
_LABELED_JAB = tuple(replace(hb, label=letter) for hb, letter in zip(_JAB.hitboxes, "ABC"))

# The design §1.1 worked example: Nalio jab (startup=1, active=2 → default window
# [2,3]), three boxes all present + identical on frames 2 and 3, each carrying its
# stable letter (the editor stamps them onto every provenance box).
_JAB_FRAMES = [
    {
        "frame": 2,
        "boxes": [
            {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20, "label": "A"},
            {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20, "label": "B"},
            {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20, "label": "C"},
        ],
    },
    {
        "frame": 3,
        "boxes": [
            {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20, "label": "A"},
            {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20, "label": "B"},
            {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20, "label": "C"},
        ],
    },
]


def test_nalio_jab_collapses_to_the_python_oracle():
    # The headline golden-safety guarantee: the per-frame trace folds back to the
    # exact hand-written _JAB.hitboxes, windows canonicalized to None, labels
    # preserved as A/B/C.
    result = collapse(_JAB_FRAMES, startup=1, active=2)
    assert result == _LABELED_JAB


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
                {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20, "label": "C"},
                {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20, "label": "A"},
                {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20, "label": "B"},
            ],
        },
        {
            "frame": 2,
            "boxes": [
                {"id": 1, "circle": [44, 28, 13], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20, "label": "B"},
                {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "kbg": 100.0, "wdsk": 20, "label": "C"},
                {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "kbg": 100.0, "wdsk": 20, "label": "A"},
            ],
        },
    ]
    assert collapse(shuffled, startup=1, active=2) == _LABELED_JAB


def test_moving_box_yields_a_one_frame_window_staircase():
    # Step 2: a box whose circle changes every frame breaks the run each frame →
    # one 1-frame-window Hitbox per frame (the ratified static staircase). Windows
    # are NOT canonicalized (they are not all the default window), so they persist.
    # All three windows carry the box's one preserved letter.
    frames = [
        {"frame": 4, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
        {"frame": 5, "boxes": [{"id": 0, "circle": [14, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
        {"frame": 6, "boxes": [{"id": 0, "circle": [18, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
    ]
    result = collapse(frames, startup=3, active=3)  # default window would be [4,6]
    assert result == (
        Hitbox(circle=Circle(10, 0, 8), damage=5.0, angle=40, active_start=4, active_end=4, label="A"),
        Hitbox(circle=Circle(14, 0, 8), damage=5.0, angle=40, active_start=5, active_end=5, label="A"),
        Hitbox(circle=Circle(18, 0, 8), damage=5.0, angle=40, active_start=6, active_end=6, label="A"),
    )


def test_deleting_a_middle_box_does_not_reletter_survivors():
    # #1029 core (the ruling's able-to-fail regression): a move authored with boxes
    # A, B, C (ids 0, 1, 2); the author deletes B (id 1). The surviving id=2 was
    # assigned "C" at creation and KEEPS "C" — collapse preserves the supplied
    # label rather than re-ranking the surviving ids [0, 2] → A, B.
    # Able-to-fail: the old id-rank labeling returns "B" for the survivor.
    frames = [
        {
            "frame": 2,
            "boxes": [
                {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83, "label": "A"},
                {"id": 2, "circle": [34, 29, 15], "damage": 3.0, "angle": 85, "label": "C"},
            ],
        },
    ]
    result = collapse(frames, startup=1, active=1)  # default window [2,2] → canonicalized
    # output sorted by (window_start, id): id 0 then id 2
    assert [hb.label for hb in result] == ["A", "C"]


def test_collapse_leaves_label_none_when_a_box_has_no_label():
    # #1029: collapse is preservation, not assignment — a provenance box carrying
    # no "label" key collapses to Hitbox.label = None (assignment/validation live
    # editor-side, in #1030, not in the pure fold).
    # Able-to-fail: the old id-rank labeling stamps "A" here.
    frames = [
        {"frame": 4, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40}]},
    ]
    result = collapse(frames, startup=3, active=1)  # default window [4,4]
    assert result[0].label is None


def test_collapse_label_is_stable_across_a_boxs_windows():
    # A single box that blinks yields two windows under one id — both carry the
    # SAME preserved letter (the label tracks identity, not the window).
    # Able-to-fail: a per-window (not per-id) label would give the two windows
    # different letters.
    frames = [
        {"frame": 4, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
        {"frame": 5, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
        {"frame": 7, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
    ]
    result = collapse(frames, startup=3, active=4)  # default [4,7]; two windows [4,5] + [7,7]
    assert [hb.label for hb in result] == ["A", "A"]


def test_blinking_box_yields_two_windows_under_one_id():
    # Step 2: a gap in an id's frames closes the run and opens a new one → two
    # Hitboxes sharing the box's geometry/scalars/id/label, distinct windows.
    frames = [
        {"frame": 4, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
        {"frame": 5, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
        # frame 6: box absent (blink off)
        {"frame": 7, "boxes": [{"id": 0, "circle": [10, 0, 8], "damage": 5.0, "angle": 40, "label": "A"}]},
    ]
    result = collapse(frames, startup=3, active=4)  # default [4,7]; neither run matches
    assert result == (
        Hitbox(circle=Circle(10, 0, 8), damage=5.0, angle=40, active_start=4, active_end=5, label="A"),
        Hitbox(circle=Circle(10, 0, 8), damage=5.0, angle=40, active_start=7, active_end=7, label="A"),
    )
