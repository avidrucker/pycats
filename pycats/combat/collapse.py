"""
pycats/combat/collapse.py

R6 (#862, child of #792 editor): the per-frame → window fold, the collapse
contract defined in docs/pycats-editor-data-schema-design.md §1.3.

The **runtime never runs this** — a shipped fighter's `hitboxes` are already the
collapsed windows (loaded by `_fighter_from_json`, #838/#844). Collapse exists so
two other places agree on how per-frame authoring becomes canonical windows:

  - the editor's Save (E5) runs it over the author's per-frame provenance;
  - the drift-guard pytest (R7, #-pending) re-runs it over a shipped file's
    `provenance` and asserts it reproduces the committed `hitboxes`.

Per Risk-2 of docs/pycats-editor-scope.md the module lives in **pycats** (the
editor imports pycats anyway; the drift-guard test cannot import from the editor
repo). Pure, deterministic, no I/O, no RNG.

Input shape — a single move's `provenance[<move>]["frames"]`, frame-major:

    [
      {"frame": 2, "boxes": [
          {"id": 0, "circle": [54, 27, 19], "damage": 3.0, "angle": 83,
           "kbg": 100.0, "wdsk": 20},
          ...
      ]},
      {"frame": 3, "boxes": [ ... ]},
    ]

Box scalar keys are the editor's convention and map to `Hitbox` fields here:
`kbg` → knockback_growth, `wdsk` → set_knockback, `bkb` → base_knockback,
`damage`/`angle` direct. Missing `bkb`/`kbg` default to 0.0, missing `wdsk` to
None — the same defaults as `Hitbox`.
"""

from __future__ import annotations

from dataclasses import replace

from pycats.combat.data import Circle, Hitbox

# The box scalars that must stay unchanged for a run to extend (design §1.3 step
# 2c). `circle` is compared separately (step 2b). `id` is identity, not a scalar.
_SCALAR_KEYS = ("damage", "angle", "bkb", "kbg", "wdsk")


def _scalar_signature(box: dict) -> tuple:
    """The (circle, scalars) tuple that a run-length run holds constant."""
    return (tuple(box["circle"]), tuple(box.get(k) for k in _SCALAR_KEYS))


def _make_hitbox(box: dict, *, active_start: int | None, active_end: int | None) -> Hitbox:
    """Build a `Hitbox` from a provenance box, mapping the editor key names."""
    dx, dy, r = box["circle"]
    return Hitbox(
        circle=Circle(dx=dx, dy=dy, r=r),
        damage=box["damage"],
        angle=box["angle"],
        base_knockback=box.get("bkb", 0.0),
        knockback_growth=box.get("kbg", 0.0),
        active_start=active_start,
        active_end=active_end,
        set_knockback=box.get("wdsk"),
    )


def collapse(frames, *, startup: int, active: int) -> tuple[Hitbox, ...]:
    """Fold a move's per-frame provenance into canonical windowed `Hitbox`es (§1.3).

    Args:
        frames: the move's `provenance[...]["frames"]` list (frame-major).
        startup, active: the move's timing — needed for step 3's default-window
            canonicalization (the fold alone cannot know the move's default
            window `[startup+1, startup+active]`).

    Returns:
        A deterministically ordered tuple of `Hitbox`. A single-window move whose
        every box spans exactly the default window is canonicalized to
        `active_start=active_end=None`, reproducing today's hand-written Python
        byte-for-byte (golden-safe).
    """
    # 1. Index by identity — regroup frame-major boxes into box-major streams
    #    keyed by author id. Same box iff same id (geometry is NOT identity).
    streams: dict = {}
    for frame_record in frames:
        frame = frame_record["frame"]
        for box in frame_record["boxes"]:
            streams.setdefault(box["id"], []).append((frame, box))

    # 2. Run-length fold — one Hitbox per maximal run where frame is contiguous
    #    and (circle, scalars) are unchanged. Track (window_start, id, Hitbox).
    emitted: list[tuple[int, object, Hitbox]] = []
    for box_id, entries in streams.items():
        entries.sort(key=lambda e: e[0])  # by frame; author edit order is irrelevant
        run_first = run_last = None
        run_box = None
        for frame, box in entries:
            if run_box is None:
                run_first = run_last = frame
                run_box = box
            elif frame == run_last + 1 and _scalar_signature(box) == _scalar_signature(run_box):
                run_last = frame
            else:
                emitted.append((run_first, box_id, _make_hitbox(run_box, active_start=run_first, active_end=run_last)))
                run_first = run_last = frame
                run_box = box
        if run_box is not None:
            emitted.append((run_first, box_id, _make_hitbox(run_box, active_start=run_first, active_end=run_last)))

    # 3. Default-window canonicalization (golden-safe) — if EVERY emitted box
    #    spans exactly [startup+1, startup+active], drop the windows to None so
    #    single-window moves are byte-identical to today's None-window Python.
    default_start, default_end = startup + 1, startup + active
    if emitted and all(hb.active_start == default_start and hb.active_end == default_end for _, _, hb in emitted):
        emitted = [
            (default_start, box_id, replace(hb, active_start=None, active_end=None)) for _, box_id, hb in emitted
        ]

    # 4. Deterministic order — sort by (window_start, id). The design's
    #    (window_start, priority, id) reduces to this: `priority` has no field in
    #    the current Hitbox model, so id is the sole tiebreak. Stable regardless
    #    of author edit order, which keeps overlap resolution and golden bytes fixed.
    emitted.sort(key=lambda t: (t[0], t[1]))
    return tuple(hb for _, _, hb in emitted)
