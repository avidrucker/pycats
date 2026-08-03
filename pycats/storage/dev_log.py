"""Dev breadcrumb log for not-yet-implemented action attempts (#587).

When a fighter attempts an action the game does not yet implement (e.g. an
undefined special that `resolve_move_key` maps to `None`), the input silently
no-ops in play. This module leaves a breadcrumb instead — one line per attempt in
a **gitignored** ``logs/LOGS.txt``:

    <fighter> attempted to use <move> with <combo> but it's not yet implemented,
    see relevant files for implementation area(s) [<file1>, <file2>, ...]

OFF by default. It writes only when ``PYCATS_DEV_LOG`` is set (truthy), so the
sim / golden / test path does **zero file I/O** and stays byte-identical — a hard
requirement (#587). De-dupes per ``(fighter, move)`` for the process so a held
input does not spam the file every frame. The log path defaults to
``logs/LOGS.txt`` (relative to cwd) and is overridable via ``PYCATS_DEV_LOG_PATH``
(used by tests to point at a tmp dir).
"""

import os
import time

_LINE = (
    "{fighter} attempted to use {move} with {combo} but it's not yet implemented, "
    "see relevant files for implementation area(s) [{files}]"
)

# Per-process de-dupe memory: a (fighter, move) that already logged is skipped.
_seen: set[tuple[str, str]] = set()


def enabled() -> bool:
    """True only when PYCATS_DEV_LOG is set (truthy). Default OFF."""
    return bool(os.environ.get("PYCATS_DEV_LOG"))


def _log_path() -> str:
    return os.environ.get("PYCATS_DEV_LOG_PATH") or os.path.join("logs", "LOGS.txt")


def reset() -> None:
    """Clear the per-process de-dupe memory. For tests; harmless in play."""
    _seen.clear()


def log_unimplemented(fighter: str, move: str, combo: str, files) -> bool:
    """Append a breadcrumb for an attempted-but-unimplemented action.

    Returns True iff a line was written this call. No-ops (returns False) when the
    logger is disabled or when this (fighter, move) already logged this process.
    """
    if not enabled():
        return False
    key = (fighter, move)
    if key in _seen:
        return False
    _seen.add(key)
    path = _log_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    line = _LINE.format(fighter=fighter, move=move, combo=combo, files=", ".join(files))
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")
    return True
