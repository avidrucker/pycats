"""
#1207 (I.1a of #1206) — the datamine hitbox-table dumper's pycats consumer.

Loads the committed Mario/Attack11 (nalio's source jab) fixture produced by
scripts/datamine_hitboxes.sh and asserts the table's structure, so downstream
slices (I.1b transform + proposer) and their tests can run without the gated
brawllib datamine env.

Able-to-fail: corrupt/rename a field in the fixture, or break the loader's
window derivation, and these assertions go red (see test_corrupt_fixture_is_rejected
and the summary/derived cross-check).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from pycats.combat.datamine_hitboxes import (
    SCHEMA,
    HitboxTable,
    load_hitbox_table,
)

FIXTURE = Path(__file__).parent / "fixtures" / "datamine" / "mario_attack11_hitboxes.json"


@pytest.fixture
def table() -> HitboxTable:
    return load_hitbox_table(FIXTURE)


def test_fixture_exists_and_loads(table: HitboxTable) -> None:
    assert table.schema == SCHEMA
    assert table.fighter == "Mario"
    assert table.subaction == "Attack11"
    assert table.frame_count == len(table.frames)
    assert table.frame_count > 0


def test_frames_are_indexed_in_order(table: HitboxTable) -> None:
    assert [f.index for f in table.frames] == list(range(table.frame_count))


def test_every_hitbox_has_finite_geometry(table: HitboxTable) -> None:
    seen_any = False
    for frame in table.frames:
        for box in frame.boxes:
            seen_any = True
            assert box.size > 0 and math.isfinite(box.size)
            assert len(box.pos) == 3
            assert all(math.isfinite(c) for c in box.pos)
            # Mario jab is a hit (not a grab) box, so damage/angle are present.
            assert box.damage is not None and math.isfinite(box.damage)
            assert box.angle is not None
    assert seen_any, "fixture has no active hitboxes on any frame"


def test_distinct_ids_grouped(table: HitboxTable) -> None:
    # Mario's Attack11 (jab1) has three hitboxes, ids 0/1/2.
    assert table.distinct_ids() == (0, 1, 2)


def test_summary_matches_frame_derived_truth(table: HitboxTable) -> None:
    # The dumper's summary block must agree with what the per-frame data implies.
    assert table.summary_count == len(table.distinct_ids())
    assert table.summary_windows == table.derived_windows()


def test_active_windows_are_within_the_move(table: HitboxTable) -> None:
    last = table.frame_count - 1
    for hid, ranges in table.derived_windows().items():
        assert ranges, f"hitbox {hid} has no active window"
        for start, end in ranges:
            assert 0 <= start <= end <= last


def test_corrupt_fixture_is_rejected(tmp_path: Path) -> None:
    # Wrong schema string => ValueError. Proves the loader guards the fixture
    # rather than accepting anything shaped vaguely like a dump.
    bad = json.loads(FIXTURE.read_text())
    bad["schema"] = "pycats.datamine.hitboxes/v999"
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        load_hitbox_table(p)
