"""Tests for the representative-frame comparison tool's pure geometry (#1217).

`scripts/compare_representative_frames.py` renders a two-panel comparison a human
eyeballs to pick `propose()`'s default representative-frame strategy. The rendering
(pygame/imageio) is not unit-tested, but the tool's claim — that the RIGHT panel plots
EXACTLY what `propose()` would produce — rests on three pure functions, tested here:

- collect_geometry — the plotted strategy circles must equal `propose()`'s circles, and
  the plotted arc must be exactly the box's active frames (so the picture cannot drift
  from what the editor receives).
- geometry_bounds — must enclose every circle's full extent AND the body origin.
- make_transform — must be isotropic (circles stay circular) and keep everything on canvas.

The script imports pygame/imageio only inside its render functions, so importing the
module for these pure-function tests pulls in no rendering dependency.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from pycats.combat import datamine_data
from pycats.combat.datamine_hitboxes import load_hitbox_table
from pycats.combat.datamine_proposer import RepresentativeFrame, _active_boxes, propose

_REPO = Path(__file__).resolve().parent.parent
_FIXTURES = datamine_data.data_dir()


def _load_tool():
    spec = importlib.util.spec_from_file_location(
        "compare_representative_frames",
        _REPO / "scripts" / "compare_representative_frames.py",
    )
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so the module's @dataclass can resolve its own module.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


TOOL = _load_tool()

# Every committed datamine fixture the tool compares against.
FIXTURES = [
    "mario_attack11_hitboxes.json",  # jab — static baseline
    "mario_attackhi4_hitboxes.json",  # u-smash — up-and-over sweep
    "mario_attackairf_hitboxes.json",  # fair — down-sweep
    "mario_attacklw4_hitboxes.json",  # d-smash — bidirectional (the AVERAGE-failure case)
]


@pytest.mark.parametrize("fixture", FIXTURES)
def test_plotted_strategy_circles_equal_propose(fixture):
    """The three plotted dots per id equal propose()'s circle for that strategy exactly."""
    table = load_hitbox_table(_FIXTURES / fixture)
    geometry = TOOL.collect_geometry(table)
    for strategy in RepresentativeFrame:
        by_id = {c.hitbox_id: c.circle for c in propose(table, strategy)}
        for hid, g in geometry.items():
            dot = g["strat"][strategy]
            circle = by_id[hid]
            assert (dot.dx, dot.dy, dot.r) == (circle.dx, circle.dy, circle.r)


@pytest.mark.parametrize("fixture", FIXTURES)
def test_plotted_arc_is_exactly_the_active_frames(fixture):
    """The arc plotted per id has one dot per active frame, keyed by frame index."""
    table = load_hitbox_table(_FIXTURES / fixture)
    geometry = TOOL.collect_geometry(table)
    for hid, g in geometry.items():
        expected_indices = [idx for idx, _ in _active_boxes(table, hid)]
        assert sorted(g["arc"].keys()) == sorted(expected_indices)
        assert len(g["arc"]) == len(expected_indices)


def test_geometry_bounds_encloses_origin_and_every_radius():
    """Bounds include the body origin (0,0) and every dot's full extent (no clip)."""
    Dot = TOOL._Dot
    geometry = {
        7: {
            "arc": {2: Dot(dx=50.0, dy=-10.0, r=8.0)},
            "strat": {s: Dot(dx=50.0, dy=-10.0, r=8.0) for s in RepresentativeFrame},
        }
    }
    min_x, min_y, max_x, max_y = TOOL.geometry_bounds(geometry)
    # Origin is always inside.
    assert min_x <= 0.0 <= max_x
    assert min_y <= 0.0 <= max_y
    # The dot's full extent (centre +/- radius) is inside.
    assert max_x >= 50.0 + 8.0
    assert min_y <= -10.0 - 8.0


def test_make_transform_is_isotropic_and_on_canvas():
    """One scale for both axes (circles stay circular); all mapped points on canvas."""
    bounds = (0.0, 0.0, 10.0, 5.0)
    tx, scale = TOOL.make_transform(bounds, width=100, height=100, margin=10)
    o = tx(0.0, 0.0)
    step_x = tx(1.0, 0.0)
    step_y = tx(0.0, 1.0)
    # Equal world step -> equal pixel step on each axis (isotropic).
    assert (step_x[0] - o[0]) == (step_y[1] - o[1])
    # Corners of the bounds land within the canvas.
    for wx, wy in [(0.0, 0.0), (10.0, 0.0), (0.0, 5.0), (10.0, 5.0)]:
        px, py = tx(wx, wy)
        assert 0 <= px <= 100
        assert 0 <= py <= 100
