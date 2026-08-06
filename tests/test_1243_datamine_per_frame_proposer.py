"""Datamine hitbox per-frame proposer (#1243, prereq of editor #1220).

`pycats.combat.datamine_proposer.propose_per_frame` turns a datamined HitboxTable
(#1207's loader output) into MOTION-PRESERVING candidates: one Circle per active
frame, so the editor can author a box that MOVES across its window (frame-major
working model, #913) rather than collapsing to one representative-frame circle the
way `propose` does. These tests pin, off the committed fixture (no gated env):

  - one candidate per distinct datamine id, in id order, window preserved;
  - a Circle on EVERY active datamine frame index, keyed by that index;
  - motion is PRESERVED — an id whose world position moves across its window gets
    DIFFERENT circles per frame (able-to-fail: a collapse-to-one would make them
    equal);
  - each frame's Circle matches `propose`'s own world->px seam for that frame;
  - FOUND/datamine status + damage/angle carry;
  - `propose` output is untouched (regression guard alongside test_1210_*).
"""

from __future__ import annotations

from pathlib import Path

from pycats.combat.data import Circle, FieldStatus, Status
from pycats.combat.datamine_hitboxes import load_hitbox_table
from pycats.combat.datamine_proposer import (
    PerFrameCandidate,
    RepresentativeFrame,
    propose,
    propose_per_frame,
)
from pycats.combat.units import u

FIXTURE = Path(__file__).parent / "fixtures" / "datamine" / "mario_attack11_hitboxes.json"


def _table():
    return load_hitbox_table(FIXTURE)


def _box(table, hid, frame_index):
    """The raw DatamineHitBox for `hid` on `frame_index` (fixture lookup helper)."""
    for frame in table.frames:
        if frame.index == frame_index:
            for box in frame.boxes:
                if box.hitbox_id == hid:
                    return box
    raise AssertionError(f"no box id={hid} on frame {frame_index}")


def test_one_candidate_per_distinct_id_in_order():
    cands = propose_per_frame(_table())
    assert [c.hitbox_id for c in cands] == [0, 1, 2]
    assert all(isinstance(c, PerFrameCandidate) for c in cands)


def test_windows_preserved_in_datamine_frame_space():
    cands = propose_per_frame(_table())
    # fixture: every id live on frames 1-2 (0-based datamine index)
    assert all(c.window == (1, 2) for c in cands)


def test_frames_map_holds_a_circle_on_every_active_index():
    cands = {c.hitbox_id: c for c in propose_per_frame(_table())}
    for hid in (0, 1, 2):
        frames = cands[hid].frames
        assert sorted(frames) == [1, 2]  # a Circle on each active datamine frame
        assert all(isinstance(circ, Circle) for circ in frames.values())


def test_motion_is_preserved_not_collapsed():
    """Able-to-fail guard: id0 moves z=12.14 -> 11.87 across [1,2], so its two
    per-frame circles must DIFFER. A collapse-to-one proposer would make them
    equal — this is the whole point of #1243."""
    cands = {c.hitbox_id: c for c in propose_per_frame(_table())}
    f1, f2 = cands[0].frames[1], cands[0].frames[2]
    assert f1 != f2
    assert f1.dx != f2.dx  # the horizontal position actually moved (66 vs 64)


def test_each_frame_circle_matches_the_world_seam():
    table = _table()
    cands = {c.hitbox_id: c for c in propose_per_frame(table)}
    for hid in (0, 1, 2):
        for idx in (1, 2):
            b = _box(table, hid, idx)
            assert cands[hid].frames[idx] == Circle(
                dx=u(b.pos[2]),
                dy=-u(b.pos[1]),
                r=u(b.size),
                status=cands[hid].frames[idx].status,
            )
    # Concrete lock on id0's actual pixels (frame1 z=12.14; frame2 z=11.87).
    assert (cands[0].frames[1].dx, cands[0].frames[1].dy, cands[0].frames[1].r) == (66, -32, 19)
    assert cands[0].frames[2].dx == 64


def test_source_and_status_are_found_datamine():
    cands = propose_per_frame(_table())
    for c in cands:
        assert c.source == "datamine"
        for circ in c.frames.values():
            for fieldname in ("dx", "dy", "r"):
                assert circ.status[fieldname] == FieldStatus(Status.FOUND, "datamine")


def test_damage_and_angle_carried_from_first_active_frame():
    cands = {c.hitbox_id: c for c in propose_per_frame(_table())}
    assert cands[0].damage == 3 and cands[0].angle == 83
    assert cands[2].angle == 85  # id2 differs — proves per-id carry, not a constant


def test_propose_is_untouched_by_per_frame_addition():
    """Regression: propose_per_frame is a sibling, not a change to propose. The
    representative-frame collapse still yields exactly one circle per id."""
    table = _table()
    reps = propose(table, RepresentativeFrame.FIRST_ACTIVE)
    assert [c.hitbox_id for c in reps] == [0, 1, 2]
    # The FIRST_ACTIVE representative equals per_frame's first-frame circle.
    pf = {c.hitbox_id: c for c in propose_per_frame(table)}
    for c in reps:
        assert c.circle == pf[c.hitbox_id].frames[c.window[0]]
