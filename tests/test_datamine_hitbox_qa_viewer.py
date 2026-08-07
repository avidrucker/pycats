"""#1301: behaviour guard for scripts/datamine_hitbox_qa_viewer.py (#1278).

The QA viewer (shipped in #1278, `0d7ef6b`) carries three pieces of logic that were
verified only by manual/headless smoke this session — nothing guarded them against
drift:

  - the frame mapping ``MoveClock = datamine idx + 1``,
  - the feet-centre anchor ``feet_centre_anchor(fd) == (w/2, h)``,
  - the layer builders ``datamine_layer`` / ``authored_boxes``.

``tests/test_scripts_import.py`` already guards that the script *imports*; it asserts
nothing about this behaviour. A refactor of ``_circle_from_world``, ``PLAYER_SIZE``,
``MoveClock``, or the move-window resolution could change what the viewer draws with
every test still green. This pins the tool's own logic off the four committed nalio
fixtures (jab/usmash/fair/dsmash) plus a synthetic move for the window-resolution branch.

Able-to-fail: reverting the ``idx + 1`` mapping to ``idx + 0`` (directly, or via the
``authored_boxes`` default-window resolution) reddens the frame-mapping assertions;
flipping the feet-centre anchor to ``(0, 0)`` / rect-top-left reddens the anchor
assertion. See the explicit negative assertions in each test.

NOT tested here (out of scope per #1278/#1301): whether the authored circles actually
*cover* the datamine boxes — that stays eyeball-gated and needs a tolerance ruling.
This guards the tool's logic, not the data's correctness.

Import mechanism mirrors ``tests/test_scripts_import.py::_import_by_path`` — the target
is a ``scripts/`` module imported by path and registered in ``sys.modules`` so its
frozen ``@dataclass`` (``Dot``) resolves its annotations at class-creation (#1259).
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

from pycats.combat import datamine_data

REPO = Path(__file__).resolve().parents[1]
VIEWER = REPO / "scripts" / "datamine_hitbox_qa_viewer.py"
NALIO = REPO / "pycats" / "characters" / "data" / "nalio.json"
FIXTURES = datamine_data.data_dir()

# datamine fixture <-> nalio move key — the four moves #1278 verified the mapping across.
CASES = {
    "jab": "attack11",
    "usmash": "attackhi4",
    "fair": "attackairf",
    "dsmash": "attacklw4",
}


def _import_viewer():
    """Import the viewer by path, registered in ``sys.modules`` (its frozen ``Dot``
    dataclass resolves its annotations via ``sys.modules`` at class-creation, #1259)."""
    spec = importlib.util.spec_from_file_location(VIEWER.stem, VIEWER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[VIEWER.stem] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def viewer():
    # The viewer imports pygame lazily inside run(), so module import opens no window;
    # set the dummy drivers defensively to match tests/test_scripts_import.py.
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    return _import_viewer()


@pytest.fixture(scope="module")
def nalio(viewer):
    from pycats.combat.data import _fighter_from_json

    return _fighter_from_json(json.loads(NALIO.read_text()))


def _table(fixture):
    from pycats.combat.datamine_hitboxes import load_hitbox_table

    return load_hitbox_table(FIXTURES / f"mario_{fixture}_hitboxes.json")


def _dm_live(dm):
    """The set of datamine frame indices carrying at least one live box."""
    return {i for i, dots in dm.items() if dots}


def _auth_live(auth, frame_count, offset):
    """The set of datamine indices ``i`` for which some authored box is live at
    ``MoveClock i + offset`` — ``offset=1`` is the viewer's mapping, ``offset=0`` the
    no-shift null hypothesis the negative assertions rule out."""
    return {i for i in range(frame_count) if any(b.start <= i + offset <= b.end for b in auth)}


@pytest.mark.parametrize("move_key,fixture", list(CASES.items()))
def test_frame_mapping_is_idx_plus_one(viewer, nalio, move_key, fixture):
    """The datamine-live frame indices coincide with the authored-live indices under the
    ``MoveClock = datamine idx + 1`` mapping — the two layers step together (#1278)."""
    table = _table(fixture)
    move = nalio.moves[move_key]
    dm = viewer.datamine_layer(table)
    auth = viewer.authored_boxes(move)
    dm_live = _dm_live(dm)
    # +1 mapping: e.g. usmash datamine-live {2,3,4,5} == authored-live-under-+1 {2,3,4,5}.
    assert dm_live == _auth_live(auth, table.frame_count, 1)
    # Able-to-fail: reverting the shift to idx + 0 (here, or via authored_boxes window
    # resolution) breaks the coincidence — the two layers no longer step together.
    assert dm_live != _auth_live(auth, table.frame_count, 0)


def test_feet_centre_anchor_is_rect_midbottom(viewer, nalio):
    """The datamine layer anchors at the fighter's feet-centre — the rect midbottom
    ``(w/2, h)`` in Circle (rect-top-left) coords — not the rect top-left origin (#1278)."""
    from pycats import config

    w, h = nalio.stand_size or config.PLAYER_SIZE
    assert viewer.feet_centre_anchor(nalio) == (w / 2.0, float(h))
    # nalio has no stand_size, so it falls back to PLAYER_SIZE (40, 60) -> (20.0, 60.0).
    assert viewer.feet_centre_anchor(nalio) == (20.0, 60.0)
    # Able-to-fail: the anchor is NOT the rect-top-left origin — reverting to raw
    # propose()-space (dx=dy=0) reddens here (a down-smash would render above the head).
    assert viewer.feet_centre_anchor(nalio) != (0.0, 0.0)


def test_authored_window_resolution(viewer):
    """``authored_boxes`` uses an explicit ``[active_start, active_end]`` verbatim and
    resolves an unset window to the move default ``[startup+1, startup+active]`` (#1278)."""
    from pycats.combat.data import Circle, Hitbox, MoveData

    circle = Circle(0, 0, 5)
    explicit = Hitbox(circle=circle, damage=1.0, angle=0, active_start=4, active_end=7)
    implicit = Hitbox(circle=circle, damage=1.0, angle=0)  # unset window
    move = MoveData(
        name="synthetic",
        in_air=False,
        startup=3,
        active=2,
        recovery=5,
        hitboxes=(explicit, implicit),
    )
    boxes = viewer.authored_boxes(move)
    # Explicit window (#204) used verbatim.
    assert (boxes[0].start, boxes[0].end) == (4, 7)
    # Unset window resolves to the move default [startup+1, startup+active] == [4, 5].
    assert (boxes[1].start, boxes[1].end) == (move.startup + 1, move.startup + move.active)
    assert (boxes[1].start, boxes[1].end) == (4, 5)


def test_datamine_layer_key_span_and_ids(viewer):
    """``datamine_layer`` keys span every animation frame ``0..frame_count-1``; a live
    frame carries the expected box ids and an inactive frame maps to ``[]`` (#1278)."""
    table = _table("attackhi4")  # usmash
    dm = viewer.datamine_layer(table)
    assert set(dm.keys()) == set(range(table.frame_count))
    # usmash frame 2 is the first live frame; it carries datamine boxes id0, id1.
    assert [d.label for d in dm[2]] == ["id0", "id1"]
    # An inactive frame maps to an empty list, not a missing key.
    assert dm[0] == []
