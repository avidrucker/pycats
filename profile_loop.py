#!/usr/bin/env python3
"""cProfile hot-function harness for the game loop (#1247, sibling to bench.py).

Where ``bench.py`` profiles only the state engine (``Player.update`` + physics +
combat, no window), THIS harness profiles the full ``App.step()`` per-frame loop
— poll → update → render → present — so the render/font/settings hotspots the
#1236 investigation named actually show up. It runs a bounded, headless
(SDL dummy) run under ``cProfile`` and prints:

  * a ranked hot-function table (top-N by cumulative and by total time), and
  * a #1236 hypothesis check — for each named suspect (settings.load, the
    font-construction burst, runtime_settings.get's defaults() copy, the
    uncached render_text_simple, per-frame surface allocation) it prints the
    measured call count + cumulative/total time, so each hypothesis is
    confirmed or refuted with a number.

Two ways to aim it (both requested on #1247):
  * ``--state session`` (default): one representative run that visits
    main_menu → char_select → playing → pause, so a single aggregated table
    covers every hypothesis at once (cProfile sums a function across the whole
    run regardless of state).
  * ``--state {main_menu,char_select,playing,pause,options}``: profile one FSM
    state in isolation for per-state numbers.

Repeatability note: the loop's 60-FPS ``clock.tick`` sleep is swapped out for a
no-sleep clock, so cumulative time measures compute, not the frame cap. The
run is headless by default (``SDL_VIDEODRIVER=dummy``); pass ``--headed`` for a
real window. Caveat: the #1236 B1 fontconfig/``SysFont`` hard-hang only fully
manifests on a real display — use ``--headed`` to reproduce that one; the
headless ranking still shows the call counts.

Usage (headless, from the repo root, with the venv python):
    SDL_VIDEODRIVER=dummy PYTHONPATH=. .venv/bin/python profile_loop.py
    ... profile_loop.py --state playing --frames 900 --top 40
    ... profile_loop.py --state options --out profile_options.txt
    make profile ARGS="--state playing"
"""

from __future__ import annotations

import argparse
import cProfile
import io
import os
import pstats
import sys

# The #1236 named hotspots. Each matcher is (funcname_substring, file_substring|None);
# a hypothesis is "present" when ANY matcher finds a profiled function. Kept as the
# single source of truth so the report and the tests agree on the target set.
HYPOTHESES = [
    {
        "id": "A1",
        "label": "uncached settings.load() per frame (ESC-hold disk read)",
        "matchers": [("load", "settings.py")],
    },
    {
        "id": "B1",
        "label": "font-construction burst: SysFont / match_font on a cache miss",
        "matchers": [
            ("_get_font", "text_utils.py"),
            ("sys_font", "text_utils.py"),
            ("SysFont", None),
            ("match_font", None),
        ],
    },
    {
        "id": "B2",
        "label": "per-frame surface allocation (attack/breath/shield) → GC pressure",
        "matchers": [("_attack_surface", "battle.py"), ("render_battle", "battle.py")],
    },
    {
        "id": "B3",
        "label": "runtime_settings.get()'s unconditional settings.defaults() copy",
        "matchers": [("get", "runtime_settings.py"), ("defaults", "settings.py")],
    },
    {
        "id": "B4",
        "label": "uncached render_text_simple() re-rasterizes HUD text every frame",
        "matchers": [("render_text_simple", "text_utils.py")],
    },
    {
        "id": "B5",
        "label": "_compose_mixed() wholesale cache clear at cap (periodic hitch)",
        "matchers": [("_compose_mixed", "text_utils.py")],
    },
]


# --------------------------------------------------------------------- reporting
def find_functions(stats, funcname, file_substr=None):
    """Return ``[(key, row), ...]`` for every profiled function whose name contains
    ``funcname`` (and, if given, whose file path contains ``file_substr``).

    ``stats`` is a ``pstats.Stats``; ``key`` is its ``(filename, lineno, funcname)``
    tuple and ``row`` is the raw stats tuple ``(primitive_calls, total_calls,
    tottime, cumtime, callers)``. Pure — this is the harness's testable core."""
    out = []
    for key, row in stats.stats.items():
        filename, _lineno, name = key
        if funcname in name and (file_substr is None or file_substr in filename):
            out.append((key, row))
    return out


def hypothesis_hits(stats):
    """For each #1236 hypothesis, aggregate the calls/tottime/cumtime of every
    profiled function any of its matchers finds. Returns one dict per hypothesis
    with ``calls`` (0 ⇒ refuted for this run), ``tottime``, ``cumtime``, and the
    matched function keys. Pure over ``stats``."""
    results = []
    for h in HYPOTHESES:
        seen = {}
        for funcname, file_substr in h["matchers"]:
            for key, row in find_functions(stats, funcname, file_substr):
                seen[key] = row  # de-dupe: a fn matched by two matchers counts once
        calls = sum(row[1] for row in seen.values())
        tottime = sum(row[2] for row in seen.values())
        cumtime = sum(row[3] for row in seen.values())
        # Per-function detail so a headline count that mixes a cheap cache-hit path
        # (e.g. _get_font) with a costly construction path (SysFont) stays readable.
        functions = sorted(
            f"{k[0].split('/')[-1]}:{k[1]}({k[2]}) calls={row[1]} cum={row[3] * 1e3:.1f}ms" for k, row in seen.items()
        )
        results.append(
            {
                "id": h["id"],
                "label": h["label"],
                "calls": calls,
                "tottime": tottime,
                "cumtime": cumtime,
                "functions": functions,
            }
        )
    return results


def format_top(stats, top, sort):
    """Top-``top`` rows of ``stats`` sorted by ``sort`` ('cumulative' | 'tottime'),
    as pstats' own text table."""
    buf = io.StringIO()
    stats.stream = buf  # print_stats writes here; re-sorting never touches .stats
    stats.sort_stats(sort).print_stats(top)
    return buf.getvalue()


def format_hypotheses(hits, frames):
    lines = [f"#1236 hypothesis check  (over {frames} frames)", "=" * 72]
    for h in hits:
        verdict = "PRESENT" if h["calls"] > 0 else "not called (refuted this run)"
        per_frame = h["calls"] / frames if frames else 0
        lines.append(
            f"[{h['id']}] {h['label']}\n"
            f"      calls={h['calls']} ({per_frame:.1f}/frame)  "
            f"cum={h['cumtime'] * 1e3:.1f}ms  tot={h['tottime'] * 1e3:.1f}ms  — {verdict}"
        )
        for fn in h["functions"]:
            lines.append("        " + fn)
    return "\n".join(lines)


# ----------------------------------------------------------------- app driving
class _NoSleepClock:
    """Replaces pygame's Clock so ``App.step``'s 60-FPS cap doesn't sleep — the
    profile then measures compute, not the frame-rate wait. Mirrors the Clock API
    App uses (``tick`` no-op, ``get_fps`` a constant for the render call)."""

    def tick(self, *_a):
        return 0

    def get_fps(self):
        return 60.0


# The representative session: which FSM states to visit, in order. The frame
# budget is split evenly across them.
SESSION_PLAN = ["main_menu", "char_select", "playing", "pause"]


def _build_app(headed=False, prefs=None):
    if not headed:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame  # deferred so --help works without a display

    from pycats.shell.app import App
    from pycats.storage import runtime_settings, settings

    pygame.init()
    pygame.display.set_caption("PyCats - LOOP PROFILER (#1247)")
    prefs = prefs if prefs is not None else settings.load()
    runtime_settings.seed(prefs)
    app = App(prefs=prefs)
    app.clock = _NoSleepClock()
    return app


def _seed_state(app, state):
    """Force the FSM into ``state`` (running its on_enter). For the in-match states
    (``playing``/``pause``) the char selector's picks are pre-set so the lazy battle
    creation in ``_update_playing`` succeeds; ``pause`` additionally steps one
    playing frame first to build the battle, then forces the overlay."""
    sm = app.screen_manager
    if state in ("playing", "pause"):
        cs = sm.char_selector
        roster = cs.characters
        cs.p1_selected = roster[0]
        cs.p2_selected = roster[1 % len(roster)]
        sm.engine.force("playing")
        app.step()  # first playing frame lazily creates the battle
        if state == "pause":
            sm.engine.force("pause")
    else:
        sm.engine.force(state)


def _drive(app, state, frames):
    if state == "session":
        per = max(1, frames // len(SESSION_PLAN))
        for seg in SESSION_PLAN:
            _seed_state(app, seg)
            for _ in range(per):
                app.step()
    else:
        _seed_state(app, state)
        for _ in range(frames):
            app.step()


def profile_state(state, frames=600, headed=False, prefs=None):
    """Drive ``frames`` of ``App.step()`` in ``state`` (or the representative
    'session') under cProfile and return the ``pstats.Stats``. Headless by default."""
    app = _build_app(headed=headed, prefs=prefs)
    prof = cProfile.Profile()
    prof.enable()
    _drive(app, state, frames)
    prof.disable()
    return pstats.Stats(prof)


# ------------------------------------------------------------------------- CLI
_STATES = ["session", "main_menu", "char_select", "playing", "pause", "options"]


def parse_args(argv):
    ap = argparse.ArgumentParser(
        prog="profile_loop", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--state",
        choices=_STATES,
        default="session",
        help="what to profile: a single FSM state, or the representative "
        "'session' (default) that visits " + " → ".join(SESSION_PLAN),
    )
    ap.add_argument("--frames", type=int, default=600, help="frames to profile (default: 600)")
    ap.add_argument("--top", type=int, default=30, help="rows in the hot-function table (default: 30)")
    ap.add_argument("--headed", action="store_true", help="use a real window (else SDL dummy)")
    ap.add_argument("--out", default=None, help="also write the full report to this text file")
    return ap.parse_args(argv)


def build_report(stats, frames, top):
    parts = [
        f"Loop profile — {frames} frames" + "\n" + "=" * 72,
        "TOP BY CUMULATIVE TIME",
        format_top(stats, top, "cumulative"),
        "TOP BY TOTAL (self) TIME",
        format_top(stats, top, "tottime"),
        format_hypotheses(hypothesis_hits(stats), frames),
    ]
    return "\n".join(parts)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    stats = profile_state(args.state, frames=args.frames, headed=args.headed)
    report = build_report(stats, args.frames, args.top)
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
