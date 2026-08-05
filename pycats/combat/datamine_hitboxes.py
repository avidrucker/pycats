"""
pycats/combat/datamine_hitboxes.py

Purpose: Load the datamined per-frame HIT-box table emitted by the brawllib_rs
dumper (scripts/brawllib/hitbox_dump.rs, run via scripts/datamine_hitboxes.sh) into
a typed structure — the sourced input the datamine-grounded hitbox proposer reads
(#1207, slice I.1a of #1206).

Contents:
- DatamineHitBox   — one hitbox on one frame: id, radius, world pos, damage, angle
- DatamineFrame    — one animation frame: its frame index + the hitboxes live on it
- HitboxTable      — a whole subaction dump: metadata + frames + summary helpers
- load_hitbox_table(path) -> HitboxTable

Design notes:
- This slice EXTRACTS only. `pos` is the resolved WORLD position [x, y, z] straight
  from the datamine (x=depth, y=vertical up+, z=horizontal), unscaled. The world->
  pycats-px transform + Circle synthesis are I.1b's job — deliberately NOT here.
- `damage`/`angle` are None for a non-Hit (grab) box; the geometry (id/size/pos) is
  what I.1b consumes, so damage/angle ride along as later-useful metadata.
- The dumper writes a `summary` block (distinct-id count + per-id active-frame
  windows). `HitboxTable` re-derives both from `frames` so a consumer never has to
  trust the block, and so the two can be cross-checked (see tests/test_1207_*).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

SCHEMA = "pycats.datamine.hitboxes/v1"


@dataclass(frozen=True)
class DatamineHitBox:
    """One hitbox as it exists on a single animation frame.

    - `hitbox_id`: a move's distinct hitboxes each carry a stable id across the
      frames they are live on.
    - `size`: radius in world units.
    - `pos`: resolved WORLD position (x=depth, y=vertical up+, z=horizontal),
      unscaled — the same space gif_generator_fixed renders from.
    - `damage`/`angle`: from the datamine's Hit values; None for a grab box.
    """

    hitbox_id: int
    size: float
    pos: tuple[float, float, float]
    damage: float | None
    angle: int | None


@dataclass(frozen=True)
class DatamineFrame:
    """One animation frame: its 0-based index and the hitboxes active on it.

    `boxes` is empty on frames where the move has no active hitbox.
    """

    index: int
    boxes: tuple[DatamineHitBox, ...]


@dataclass(frozen=True)
class HitboxTable:
    """A whole subaction's datamined hitbox table."""

    schema: str
    fighter: str
    subaction: str
    frame_count: int
    frames: tuple[DatamineFrame, ...]
    # The dumper's own summary block, parsed as-emitted (id string -> list of
    # inclusive [start, end] frame ranges). `derived_windows()` recomputes the
    # same thing from `frames` for cross-checking.
    summary_count: int
    summary_windows: dict[int, tuple[tuple[int, int], ...]]

    def distinct_ids(self) -> tuple[int, ...]:
        """Distinct hitbox ids across the whole move, ascending — derived from frames."""
        ids: set[int] = set()
        for frame in self.frames:
            for box in frame.boxes:
                ids.add(box.hitbox_id)
        return tuple(sorted(ids))

    def derived_windows(self) -> dict[int, tuple[tuple[int, int], ...]]:
        """Per-id active-frame windows as inclusive [start, end] ranges, from frames.

        Recomputed independently of the dumper's `summary` block so a consumer or
        test can verify the block against the per-frame truth.
        """
        active: dict[int, list[int]] = {}
        for frame in self.frames:
            for box in frame.boxes:
                active.setdefault(box.hitbox_id, []).append(frame.index)
        windows: dict[int, tuple[tuple[int, int], ...]] = {}
        for hid, idxs in active.items():
            idxs = sorted(set(idxs))
            ranges: list[tuple[int, int]] = []
            start = prev = idxs[0]
            for v in idxs[1:]:
                if v == prev + 1:
                    prev = v
                else:
                    ranges.append((start, prev))
                    start = prev = v
            ranges.append((start, prev))
            windows[hid] = tuple(ranges)
        return windows


def _hitbox_from(obj: dict) -> DatamineHitBox:
    pos = obj["pos"]
    return DatamineHitBox(
        hitbox_id=int(obj["hitbox_id"]),
        size=float(obj["size"]),
        pos=(float(pos[0]), float(pos[1]), float(pos[2])),
        damage=None if obj["damage"] is None else float(obj["damage"]),
        angle=None if obj["angle"] is None else int(obj["angle"]),
    )


def load_hitbox_table(path: str | Path) -> HitboxTable:
    """Parse a dumper JSON file into a `HitboxTable`.

    Raises `KeyError`/`ValueError` on a malformed or wrong-schema file — the caller
    (and the fixture test) rely on that to catch a corrupted dump.
    """
    data = json.loads(Path(path).read_text())
    schema = data["schema"]
    if schema != SCHEMA:
        raise ValueError(f"unexpected datamine schema {schema!r}, expected {SCHEMA!r}")

    frames = tuple(
        DatamineFrame(
            index=int(fr["index"]),
            boxes=tuple(_hitbox_from(b) for b in fr["boxes"]),
        )
        for fr in data["frames"]
    )

    summary = data["summary"]
    summary_windows = {
        int(hid): tuple((int(a), int(b)) for a, b in ranges) for hid, ranges in summary["windows"].items()
    }

    return HitboxTable(
        schema=schema,
        fighter=data["fighter"],
        subaction=data["subaction"],
        frame_count=int(data["frame_count"]),
        frames=frames,
        summary_count=int(summary["count"]),
        summary_windows=summary_windows,
    )
