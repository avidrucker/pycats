"""Datamine hitbox proposer (#1210, slice I.1b of #1206).

`pycats.combat.datamine_proposer.propose` turns a datamined HitboxTable (#1207's
loader output) into pycats-px HitboxCandidates the editor draws as ghosts a human
accepts/tweaks. These tests pin, off the committed fixture (no gated env):

  - one candidate per distinct datamine id, in id order, window preserved;
  - the world -> px transform goes through the named units.py::u() seam
    (ADR-0011) for radius AND offset — a wrong scale / inline multiply reddens;
  - the axis mapping (dx <- z, dy <- -y screen-down) and FOUND/datamine status;
  - each RepresentativeFrame strategy selects a DIFFERENT representative position
    (able-to-fail: a propose() that ignored `strategy` would collapse them).
"""

from __future__ import annotations

from pathlib import Path

from pycats.combat.data import Circle, FieldStatus, Status
from pycats.combat.datamine_hitboxes import load_hitbox_table
from pycats.combat.datamine_proposer import (
    HitboxCandidate,
    RepresentativeFrame,
    propose,
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
    cands = propose(_table())
    assert [c.hitbox_id for c in cands] == [0, 1, 2]
    assert all(isinstance(c, HitboxCandidate) for c in cands)


def test_windows_preserved_in_datamine_frame_space():
    cands = propose(_table())
    # fixture: every id live on frames 1-2 (0-based datamine index)
    assert all(c.window == (1, 2) for c in cands)


def test_source_and_status_are_found_datamine():
    cands = propose(_table())
    for c in cands:
        assert c.source == "datamine"
        for fieldname in ("dx", "dy", "r"):
            assert c.circle.status[fieldname] == FieldStatus(Status.FOUND, "datamine")


def test_damage_and_angle_carried_from_datamine():
    cands = {c.hitbox_id: c for c in propose(_table())}
    assert cands[0].damage == 3 and cands[0].angle == 83
    assert cands[2].angle == 85  # id2 differs — proves per-id carry, not a constant


def test_first_active_uses_first_frame_position_via_u_seam():
    table = _table()
    cands = {c.hitbox_id: c for c in propose(table, RepresentativeFrame.FIRST_ACTIVE)}
    b = _box(table, 0, 1)  # id0's first active frame
    # Derived through u() from the fixture's raw world coords — pins the named seam
    # (a wrong scale or inline multiply makes these three reads disagree).
    assert cands[0].circle == Circle(
        dx=u(b.pos[2]),
        dy=-u(b.pos[1]),
        r=u(b.size),
        status=cands[0].circle.status,
    )
    # Concrete lock on the actual pixels (id0 frame1: z=12.14, y=5.84, size=3.52).
    assert (cands[0].circle.dx, cands[0].circle.dy, cands[0].circle.r) == (66, -32, 19)


def test_radius_is_u_of_size_not_inline_multiply():
    table = _table()
    cands = {c.hitbox_id: c for c in propose(table)}
    for hid in (0, 1, 2):
        size = _box(table, hid, 1).size
        assert cands[hid].circle.r == u(size)


def test_dy_sign_is_screen_down():
    # World y is up-positive; a box above the origin must map to a NEGATIVE dy
    # (pycats screen-y grows down). All Mario-jab boxes sit above origin.
    cands = propose(_table())
    assert all(c.circle.dy < 0 for c in cands)


def test_mid_window_picks_the_middle_active_frame():
    table = _table()
    cands = {c.hitbox_id: c for c in propose(table, RepresentativeFrame.MID_WINDOW)}
    b = _box(table, 0, 2)  # [1,2] -> len//2 == 1 -> the later frame (index 2)
    assert cands[0].circle.dx == u(b.pos[2])
    assert cands[0].circle.dx == 64


def test_window_average_is_the_centroid():
    table = _table()
    cands = {c.hitbox_id: c for c in propose(table, RepresentativeFrame.WINDOW_AVERAGE)}
    f1, f2 = _box(table, 0, 1), _box(table, 0, 2)
    exp_dx = u((f1.pos[2] + f2.pos[2]) / 2)
    exp_dy = -u((f1.pos[1] + f2.pos[1]) / 2)
    assert (cands[0].circle.dx, cands[0].circle.dy) == (exp_dx, exp_dy)
    assert (cands[0].circle.dx, cands[0].circle.dy) == (65, -29)


def test_strategies_select_distinct_positions():
    """Able-to-fail guard: the three rules must disagree on a moving box, else
    `strategy` is being ignored. id0 moves z=12.14 -> 11.87 across [1,2]."""
    table = _table()
    dx = {
        s: propose(table, s)[0].circle.dx
        for s in (
            RepresentativeFrame.FIRST_ACTIVE,
            RepresentativeFrame.MID_WINDOW,
            RepresentativeFrame.WINDOW_AVERAGE,
        )
    }
    assert len(set(dx.values())) == 3, dx  # 66, 64, 65 all distinct


def test_default_strategy_is_first_active():
    table = _table()
    assert propose(table) == propose(table, RepresentativeFrame.FIRST_ACTIVE)
