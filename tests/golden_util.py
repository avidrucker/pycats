# tests/golden_util.py
"""Helper for golden-snapshot regression tests.

Usage::

    from tests.golden_util import check_or_update
    check_or_update("my_scenario", snaps)

Set the environment variable ``PYCATS_UPDATE_GOLDENS=1`` to (re)write the
golden file; otherwise the test asserts byte-identity against the committed
snapshot and fails with the first differing frame index.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pycats.sim.runner import PlayerSnap  # #322/B-b: read player rows by name

# Goldens live alongside this file, one sub-directory down.
GOLDEN_DIR = Path(__file__).parent / "golden"


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _to_list(obj: Any) -> Any:
    """Recursively convert tuples to lists so json.dumps can handle them."""
    if isinstance(obj, (list, tuple)):
        return [_to_list(item) for item in obj]
    # All other snapshot values are str/int/float/bool/None — JSON-native.
    return obj


def serialize(snaps: list) -> str:
    """Return a deterministic JSON string for a list of per-frame snapshots.

    Tuples are converted to JSON arrays (round-trip stable because every
    snapshot is reproduced from the same engine code, not from JSON).
    """
    return json.dumps(_to_list(snaps), separators=(",", ":"))


# ---------------------------------------------------------------------------
# Semantic summary (S4 — the reviewable digest of an opaque golden)
# ---------------------------------------------------------------------------

def summarize(snaps: list) -> dict:
    """Distil a snapshot list into a tiny, human-reviewable semantic digest.

    The raw golden is good at *detecting* divergence but its diff is unreadable;
    this digest is what a reviewer reads before accepting a regen (see
    tests/golden/REGEN_PROTOCOL.md). It captures the behaviour that matters —
    not every pixel.

    Snapshot shape (see sim/runner.snapshot): ``(parts, attacks, phase, winner)``
    where each part is ``(name, state, x, y, vx, vy, on_ground, percent,
    shield_hp, lives, is_alive, ...)`` — we read name(0)/state(1)/percent(7)/
    lives(9).
    """
    snaps = _to_list(snaps)  # normalise tuples → lists for uniform indexing
    n = len(snaps)
    if n == 0:
        return {"frames": 0, "final_phase": None, "winner": None,
                "attack_active_frames": 0, "players": {}}

    # #322/B-b: wrap each per-player row in PlayerSnap so fields are read by name
    # (the parts are lists here after _to_list; PlayerSnap(*row) re-attaches names).
    names = [PlayerSnap(*p).name for p in snaps[0][0]]
    players: dict = {}
    for idx, name in enumerate(names):
        rows = [PlayerSnap(*snaps[f][0][idx]) for f in range(n)]
        states = sorted({r.state for r in rows})
        lives = [r.lives for r in rows]
        percents = [r.percent for r in rows]
        ko_frames = [f for f in range(1, n) if lives[f] < lives[f - 1]]
        players[name] = {
            "states": states,
            "lives_start": lives[0],
            "lives_end": lives[-1],
            "lives_min": min(lives),
            "percent_max": max(percents),
            "ko_frames": ko_frames,
        }

    attack_active_frames = sum(1 for f in range(n) if snaps[f][1])
    return {
        "frames": n,
        "final_phase": snaps[-1][2],
        "winner": snaps[-1][3],
        "attack_active_frames": attack_active_frames,
        "players": players,
    }


def _summary_path(name: str) -> Path:
    return GOLDEN_DIR / f"{name}.summary.json"


def _summary_text(summary: dict) -> str:
    """Pretty, stable JSON so the sidecar git-diffs cleanly."""
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


def _check_or_update_summary(name: str, snaps: list) -> None:
    """Write (update mode) or assert (check mode) the reviewable summary sidecar.

    In check mode the sidecar must equal ``summarize(snaps)`` for the current
    run — so a stale/hand-edited sidecar, or a behaviour change that slipped past
    review, surfaces as a small readable diff rather than an opaque blob."""
    path = _summary_path(name)
    summary = summarize(snaps)

    if os.environ.get("PYCATS_UPDATE_GOLDENS") == "1":
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(_summary_text(summary), encoding="utf-8")
        return

    if not path.exists():
        raise AssertionError(
            f"Golden summary missing: {path}\n"
            "Run tests with PYCATS_UPDATE_GOLDENS=1 to record it."
        )

    expected = json.loads(path.read_text(encoding="utf-8"))
    if summary != expected:
        raise AssertionError(
            f"Golden '{name}': semantic summary changed.\n"
            f"  expected (sidecar) = {json.dumps(expected, sort_keys=True)}\n"
            f"  actual   (this run)= {json.dumps(summary, sort_keys=True)}\n"
            "If intended, review per tests/golden/REGEN_PROTOCOL.md and regen."
        )


# ---------------------------------------------------------------------------
# Oracle
# ---------------------------------------------------------------------------

def check_or_update(name: str, snaps: list) -> None:
    """Compare *snaps* against the committed golden file ``tests/golden/<name>.json``.

    * If ``PYCATS_UPDATE_GOLDENS=1`` is set in the environment, (re)write the
      golden file and return (always passes).
    * If the golden file does not exist and update mode is off, raise
      ``AssertionError`` with a clear message explaining how to record it.
    * If the golden file exists, assert the serialized snapshots match exactly;
      on mismatch fail with the index of the first differing frame.
    """
    golden_path = GOLDEN_DIR / f"{name}.json"
    actual = serialize(snaps)

    if os.environ.get("PYCATS_UPDATE_GOLDENS") == "1":
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(actual, encoding="utf-8")
        _check_or_update_summary(name, snaps)  # rewrite the reviewable sidecar too
        return  # always passes in update mode

    if not golden_path.exists():
        raise AssertionError(
            f"Golden file missing: {golden_path}\n"
            "Run tests with PYCATS_UPDATE_GOLDENS=1 to record it."
        )

    # Semantic summary first: a behaviour change fails with a small readable diff
    # (the reviewable layer) before the opaque raw byte comparison below.
    _check_or_update_summary(name, snaps)

    expected = golden_path.read_text(encoding="utf-8")
    if actual == expected:
        return

    # Provide a useful first-differing-frame message for debugging.
    actual_frames = json.loads(actual)
    expected_frames = json.loads(expected)

    if len(actual_frames) != len(expected_frames):
        raise AssertionError(
            f"Golden '{name}': frame count mismatch — "
            f"got {len(actual_frames)}, expected {len(expected_frames)}."
        )

    for i, (a, e) in enumerate(zip(actual_frames, expected_frames)):
        if a != e:
            raise AssertionError(
                f"Golden '{name}': first divergence at frame {i}.\n"
                f"  actual  = {json.dumps(a)[:300]}\n"
                f"  expected= {json.dumps(e)[:300]}"
            )

    # Lengths match and all frames match — the raw strings differ only in
    # encoding (shouldn't happen, but just in case).
    raise AssertionError(
        f"Golden '{name}': JSON content matches but raw strings differ "
        "(encoding mismatch). Rerun with PYCATS_UPDATE_GOLDENS=1."
    )
