"""#1314: guard the packaged datamine ground-truth tables + their editor-facing seam.

The canonical datamine hitbox-table dumps (schema ``pycats.datamine.hitboxes/v1``) were
relocated from ``tests/fixtures/datamine/`` to the shipped package
``pycats/combat/datamine_data/`` in #1314, so the pycats-editor datamine-truth review
layer (tracker #1299) reads them through the editable-install import seam
(``pycats.combat.datamine_data``) rather than reaching into pycats' ``tests/`` tree.

This is the cross-repo guard the #1309 ARC ruling required — the ADR-0022 / #1281 pattern
applied to the data-file surface: if a table is moved, renamed, removed, or added without
updating ``pycats.combat.datamine_data.TABLES``, an assertion below reddens and names the
editor as the consumer to update, so the change can never break the editor with no signal.

Able-to-fail: delete or rename any ``mario_*_hitboxes.json`` under ``datamine_data/``, or
add one without registering it in ``TABLES``, and the parametrised / contents assertions
go red.
"""

from __future__ import annotations

import pytest

from pycats.combat import datamine_data
from pycats.combat.datamine_hitboxes import SCHEMA, load_hitbox_table

_CONSUMER = (
    "The pycats-editor datamine-truth review layer (src/pycats_editor/datamine.py, "
    "tracker #1299) reads these tables via `pycats.combat.datamine_data`. If you moved, "
    "renamed, added, or removed a datamine table, update "
    "`pycats.combat.datamine_data.TABLES` (and the editor consumer) to match."
)


def test_data_dir_resolves_to_a_directory() -> None:
    d = datamine_data.data_dir()
    assert d.is_dir(), f"packaged datamine data dir missing: {d}\n{_CONSUMER}"


@pytest.mark.parametrize("name", datamine_data.TABLES)
def test_each_registered_table_is_present(name: str) -> None:
    path = datamine_data.table_path(name)
    assert path.is_file(), f"registered datamine table missing: {path}\n{_CONSUMER}"


@pytest.mark.parametrize("name", datamine_data.TABLES)
def test_each_registered_table_loads_with_canonical_schema(name: str) -> None:
    table = load_hitbox_table(datamine_data.table_path(name))
    assert table.schema == SCHEMA, f"{name}: unexpected schema {table.schema!r}, expected {SCHEMA!r}\n{_CONSUMER}"


def test_registered_tables_match_dir_contents() -> None:
    """TABLES is the single source both the guard and the editor trust: no unregistered
    .json in the package dir, and no registered name absent from disk."""
    on_disk = {p.name for p in datamine_data.data_dir().glob("*.json")}
    registered = set(datamine_data.TABLES)
    assert on_disk == registered, (
        f"datamine_data TABLES drift: on-disk={sorted(on_disk)} registered={sorted(registered)}\n{_CONSUMER}"
    )
