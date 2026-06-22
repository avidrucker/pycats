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
        return  # always passes in update mode

    if not golden_path.exists():
        raise AssertionError(
            f"Golden file missing: {golden_path}\n"
            "Run tests with PYCATS_UPDATE_GOLDENS=1 to record it."
        )

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
