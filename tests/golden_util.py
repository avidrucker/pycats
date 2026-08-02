# tests/golden_util.py
"""Helper for golden-snapshot regression tests.

New here? See ``docs/golden-tests.md`` for the plain-English onboarding + glossary
(golden / oracle / digest-sidecar / re-baseline / check-vs-record).

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

# Appended to every golden failure so a first-time reader knows what a golden is
# and how to read the failure. Onboarding home: docs/golden-tests.md (B2/#1016).
DOC_HINT = "New to goldens? See docs/golden-tests.md (what goldens are + how to read this)."


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
    where each part is ``(name, character, state, x, y, vx, vy, on_ground, percent,
    shield_hp, lives, is_alive, ...)`` — read here by NAME via ``PlayerSnap(*row)``,
    so field order can grow (e.g. #672 Phase 2a inserted ``character`` after ``name``)
    without touching this code.
    """
    snaps = _to_list(snaps)  # normalise tuples → lists for uniform indexing
    n = len(snaps)
    if n == 0:
        return {"frames": 0, "final_phase": None, "winner": None, "attack_active_frames": 0, "players": {}}

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
            "character": rows[0].character,  # #672 Phase 2a (DP2): which fighter this slot played
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


def _flatten(obj: Any, prefix: str = "") -> dict:
    """Flatten a nested dict to ``{dotted.path: value}``; lists are leaves.

    Used by :func:`_summary_diff_lines` so a summary change reports only the
    fields that moved (e.g. ``players.birky.lives_end``) instead of two blobs.
    """
    if isinstance(obj, dict):
        out: dict = {}
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(_flatten(v, key))
        return out
    return {prefix: obj}


def _summary_diff_lines(expected: dict, actual: dict, cap: int = 30) -> list:
    """Return compact ``path: expected → actual`` lines for changed leaves only.

    Only fields whose value differs appear; a missing side shows ``<missing>``.
    Bounded at *cap* lines so an all-fields drift can't dump the whole summary.
    """
    fe, fa = _flatten(expected), _flatten(actual)
    lines = []
    for k in sorted(set(fe) | set(fa)):
        if fe.get(k) != fa.get(k):
            e = json.dumps(fe[k]) if k in fe else "<missing>"
            a = json.dumps(fa[k]) if k in fa else "<missing>"
            lines.append(f"  {k}: {e} → {a}")
    if len(lines) > cap:
        lines = lines[:cap] + [f"  … and {len(lines) - cap} more changed field(s)"]
    return lines


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
            f"Golden summary missing: {path}\nRun tests with PYCATS_UPDATE_GOLDENS=1 to record it.\n{DOC_HINT}"
        )

    expected = json.loads(path.read_text(encoding="utf-8"))
    if summary != expected:
        diff = "\n".join(_summary_diff_lines(expected, summary))
        raise AssertionError(
            f"Golden '{name}': semantic summary changed. Changed fields (expected → actual):\n"
            f"{diff}\n"
            f"If intended, review per tests/golden/REGEN_PROTOCOL.md and regen.\n{DOC_HINT}"
        )


# ---------------------------------------------------------------------------
# Oracle
# ---------------------------------------------------------------------------

# A serialized frame is ``[parts, attacks, phase, winner]`` (see sim/runner.snapshot).
_FRAME_COMPONENTS = ("parts", "attacks", "phase", "winner")


def _describe_frame_divergence(actual_frame: Any, expected_frame: Any) -> str:
    """Name the first component/fighter/field that differs between two frames.

    ``parts`` is a list of per-player rows read by name via ``PlayerSnap`` — so a
    row-level difference is reported as ``<fighter>.<field>: <expected> → <actual>``
    (e.g. ``birky.percent: 88.0 → 85.0``) rather than a raw positional index. The
    other components (attacks/phase/winner) report as ``<component>: expected → actual``.
    """
    for ci, comp in enumerate(_FRAME_COMPONENTS):
        av = actual_frame[ci] if ci < len(actual_frame) else None
        ev = expected_frame[ci] if ci < len(expected_frame) else None
        if av == ev:
            continue
        if comp != "parts":
            return f"{comp}: {json.dumps(ev)} → {json.dumps(av)}"
        # parts: find the first player row that differs, then the first field.
        for pi in range(max(len(av or []), len(ev or []))):
            arow = av[pi] if av and pi < len(av) else None
            erow = ev[pi] if ev and pi < len(ev) else None
            if arow == erow:
                continue
            if arow is None or erow is None:
                return f"player slot {pi} present on one side only"
            pa, pe = PlayerSnap(*arow), PlayerSnap(*erow)
            for f in PlayerSnap._fields:
                va, ve = getattr(pa, f), getattr(pe, f)
                if va != ve:
                    return f"{pe.name}.{f}: {json.dumps(ve)} → {json.dumps(va)}"
            return f"player {pe.name}: rows differ"
        return "parts differ"
    return "frames differ"


def _lead_in_frames(actual_frames: list, expected_frames: list, i: int, back: int = 2, width: int = 200) -> str:
    """Compact context: up to *back* matching frames before divergence, then frame *i*.

    Each frame is truncated to *width* chars so a large drift never dumps the whole
    blob. Frames before *i* are identical on both sides (that's why they matched), so
    each is shown once; frame *i* shows expected vs actual.
    """

    def _clip(s: str) -> str:
        return s if len(s) <= width else s[:width] + "…"

    lines = [f"    frame {f} (matches): {_clip(json.dumps(actual_frames[f]))}" for f in range(max(0, i - back), i)]
    lines.append(f"  → frame {i} expected: {_clip(json.dumps(expected_frames[i]))}")
    lines.append(f"  → frame {i} actual  : {_clip(json.dumps(actual_frames[i]))}")
    return "\n".join(lines) + "\n"


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
            f"Golden file missing: {golden_path}\nRun tests with PYCATS_UPDATE_GOLDENS=1 to record it.\n{DOC_HINT}"
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
            f"Golden '{name}': frame count mismatch — got {len(actual_frames)}, "
            f"expected {len(expected_frames)}.\n{DOC_HINT}"
        )

    for i, (a, e) in enumerate(zip(actual_frames, expected_frames)):
        if a != e:
            what = _describe_frame_divergence(a, e)
            lead = _lead_in_frames(actual_frames, expected_frames, i)
            raise AssertionError(
                f"Golden '{name}': first divergence at frame {i}.\n"
                f"  first change (expected → actual): {what}\n"
                f"{lead}{DOC_HINT}"
            )

    # Lengths match and all frames match — the raw strings differ only in
    # encoding (shouldn't happen, but just in case).
    raise AssertionError(
        f"Golden '{name}': JSON content matches but raw strings differ "
        f"(encoding mismatch). Rerun with PYCATS_UPDATE_GOLDENS=1.\n{DOC_HINT}"
    )
