"""Grounded per-character walk/dash/run speeds (#1209, ADR-0011 item 2).

The re-pin: each `<cat>.json` carries its raw PM unit for walk / dash / run
verbatim from the #814 datamine; the load seam derives the integer shipped
pixel via `combat.units.u()` (`round(PX_PER_UNIT * unit)`). The
`MOVE_SPEED`/`DASH_SPEED` config globals are gone — a cat's speeds come only
from its own data (matching the #887 no-fallback stance).

These pin:
  - each cat's shipped px == the ADR-0011 table (nalio 6/8/8 … narz 9/8/10);
  - the px is DERIVED from the raw unit (a changed unit derives a different px —
    able-to-fail, the revert-check), not a stored literal;
  - each speed carries a FOUND provenance tag (source = datamine), via the
    #1216 FighterData-level status seam.

The dedicated `json unit == u()` drift conformance guard is #957, sequenced
after this lands.
"""

from __future__ import annotations

from dataclasses import replace

from pycats.combat.data import Status, load_fighter_data
from pycats.combat.units import u

# ADR-0011 §Decision 3 table (raw unit -> derived px). default mirrors nalio
# (Mario), preserving the old MOVE_SPEED=6 / DASH_SPEED=8 grounding.
_EXPECTED_PX = {
    "nalio": (6, 8, 8),
    "birky": (5, 8, 8),
    "narz": (9, 8, 10),
    "gnok": (6, 10, 10),
    "default": (6, 8, 8),
}
_EXPECTED_UNITS = {
    "nalio": (1.1, 1.5, 1.5),
    "birky": (0.85, 1.5, 1.5),
    "narz": (1.6, 1.5, 1.8),
    "gnok": (1.2, 1.8, 1.8),
    "default": (1.1, 1.5, 1.5),
}


def test_shipped_px_matches_adr_table():
    """Every cat's shipped walk/dash/run px equals the ADR-0011 table."""
    for name, (w, d, r) in _EXPECTED_PX.items():
        fd = load_fighter_data(name)
        assert (fd.move_speed, fd.dash_speed, fd.run_speed) == (w, d, r), name


def test_json_units_match_datamine():
    """Each cat stores the raw PM unit verbatim (walk/dash/run fields)."""
    for name, (w, d, r) in _EXPECTED_UNITS.items():
        fd = load_fighter_data(name)
        assert (fd.walk, fd.dash, fd.run) == (w, d, r), name


def test_px_is_derived_from_unit_not_a_literal():
    """The shipped px is `u(unit)`, derived — a changed unit derives a different
    px. Able-to-fail: a hard-coded pixel would ignore the unit change."""
    fd = load_fighter_data("narz")
    assert fd.move_speed == u(fd.walk) == 9
    assert fd.run_speed == u(fd.run) == 10
    bumped = replace(fd, walk=2.0)
    assert bumped.move_speed == u(2.0) == 11  # derivation follows the unit


def test_speed_units_carry_found_provenance():
    """Each cat tags walk/dash/run FOUND (source = datamine) via the #1216
    FighterData-level status seam — the machine-readable grounding #957 reads."""
    for name in _EXPECTED_UNITS:
        fd = load_fighter_data(name)
        for speed in ("walk", "dash", "run"):
            fs = fd.status[speed]
            assert fs.status is Status.FOUND, (name, speed)
            assert fs.source == "datamine", (name, speed)
