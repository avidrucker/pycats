"""
Dense hit-box label migration (#1041) — the baseline half of the letter-identity
round-trip (#1029 preserve / #1030 adopt).

Authored fighter data carries a full, hole-free `A, B, C…` letter run per move in
box order. `with_dense_hit_labels` stamps that onto every `Hitbox.label`, the
oracles apply it, and the shipped `<stem>.json` therefore ships real labels the
editor adopts (#1030) instead of none — no editor-side auto-assign.

These guard both halves: the transform assigns dense letters, and every shipped
JSON round-trips to dense-labeled hit boxes. Able-to-fail: unwrap an oracle (or
drop the label from the JSON) and the shipped-data test goes red for that stem.
"""

import pytest

from pycats.combat.data import (
    Circle,
    FighterData,
    Hitbox,
    Hurtbox,
    MoveData,
    fighter_json_paths,
    load_fighter_data,
    with_dense_hit_labels,
)

_HURTBOX = Hurtbox(circles=(Circle(20, 30, 14),))


def _dense(n: int) -> list[str]:
    return [chr(ord("A") + i) for i in range(n)]


def _move(*hitboxes: Hitbox) -> MoveData:
    return MoveData(name="m", in_air=False, startup=1, active=1, recovery=1, hitboxes=hitboxes)


def _fighter(*hitboxes: Hitbox) -> FighterData:
    return FighterData(hurtbox=_HURTBOX, moves={"jab": _move(*hitboxes)})


def _hb(dx: int, label: str | None = None) -> Hitbox:
    return Hitbox(circle=Circle(dx, 0, 5), damage=1.0, angle=0, label=label)


def test_with_dense_hit_labels_assigns_letters_in_box_order():
    # Three unlabeled boxes → A, B, C in tuple order. Able-to-fail: a no-op
    # transform leaves label=None.
    fd = _fighter(_hb(10), _hb(20), _hb(30))
    labeled = with_dense_hit_labels(fd)
    assert [hb.label for hb in labeled.moves["jab"].hitboxes] == ["A", "B", "C"]


def test_with_dense_hit_labels_is_idempotent():
    # Dense in → dense out (the migration can run twice with no drift).
    fd = _fighter(_hb(10), _hb(20), _hb(30))
    once = with_dense_hit_labels(fd)
    twice = with_dense_hit_labels(once)
    assert twice == once


def test_with_dense_hit_labels_leaves_geometry_and_timing_untouched():
    # Only labels change — geometry/scalars/timing are preserved.
    fd = _fighter(_hb(10), _hb(20))
    labeled = with_dense_hit_labels(fd)
    src = fd.moves["jab"]
    out = labeled.moves["jab"]
    assert (out.startup, out.active, out.recovery) == (src.startup, src.active, src.recovery)
    assert [hb.circle for hb in out.hitboxes] == [hb.circle for hb in src.hitboxes]


_STEMS = [p.stem for p in fighter_json_paths()]


@pytest.mark.parametrize("stem", _STEMS)
def test_shipped_json_hit_boxes_carry_dense_labels(stem):
    # End-to-end: every shipped move hydrates to hit boxes labeled densely in box
    # order. Able-to-fail: pre-#1041 data (no `label` keys) loads label=None and
    # this reds for every stem.
    fighter = load_fighter_data(stem)
    for move_key, move in fighter.moves.items():
        got = [hb.label for hb in move.hitboxes]
        assert got == _dense(len(move.hitboxes)), (
            f"{stem}.{move_key}: labels {got} are not dense A,B,C… — fix the "
            f"labels in characters/data/{stem}.json (the sole source since #1141)"
        )
