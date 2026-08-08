"""Canonical datamine hitbox-table dumps (schema ``pycats.datamine.hitboxes/v1``).

These JSON tables are the datamined ground truth (Project M / Brawl, produced by the
#1207 brawllib-rs hitbox-table dumper) — **not** test scaffolding. They were relocated
here from ``tests/fixtures/datamine/`` in #1314 so they ship as package data
(``include = ["pycats*"]`` + ``package-data``) and the pycats-editor datamine-truth
review layer (tracker #1299) can read them through the editable-install import seam,
exactly as it already imports ``load_fighter_data`` / ``resolve_circle``.

Read a table via :func:`table_path` (or :func:`data_dir`) and hand it to
``pycats.combat.datamine_hitboxes.load_hitbox_table``.

If these files move or are renamed again, the consumer to update is the pycats-editor
datamine layer (``src/pycats_editor/datamine.py``). The guard test
``tests/test_1314_datamine_data_packaged.py`` fails loud on such a move and names that
consumer — the ADR-0022 / #1281 cross-repo-surface pattern applied to the data-file
surface.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

#: Canonical datamine table file names shipped in this package (the moves dumped so far).
TABLES: tuple[str, ...] = (
    "mario_attack11_hitboxes.json",
    "mario_attackairf_hitboxes.json",
    "mario_attackhi4_hitboxes.json",
    "mario_attacklw4_hitboxes.json",
)


def data_dir() -> Path:
    """Filesystem directory holding the packaged datamine tables.

    Resolves through :mod:`importlib.resources`, so it works under both a source
    checkout and pycats' editable install (``pip install -e ../pycats``).
    """
    return Path(str(resources.files(__name__)))


def table_path(name: str) -> Path:
    """Path to one packaged datamine table by file name.

    ``name`` is a file name such as ``"mario_attack11_hitboxes.json"`` (an entry of
    :data:`TABLES`).
    """
    return data_dir() / name
