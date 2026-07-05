"""#61 — a `watch.py --vs` battle runs up to 30s OR until a 3-stock KO-out,
whichever happens first.

Before #61, `--vs` used the fixed `--frames` default (300 ≈ 5s) with no early
stop (`stop_on_match_over` was only set for `--match`), so a 2-NPC demo always
cut off at ~5s and never ended on a KO. `resolve_battle_plan` now maps the CLI
mode flags to (frames, stop_on_match_over):

  - `--vs <archetype>` -> (30 * FPS, True)   # up to 30s, stop early on KO-out
  - `--match`          -> (6000, True)        # full battle to defeat (unchanged)
  - scripted replay    -> (300, False)        # ~5s, runs to completion

with `--frames` overriding the cap for `--vs` and the scripted replay.

Revert-the-fix check: point `--vs` back at the scripted default / drop the stop
flag (return (frames or 300, False)) and the 30s + early-stop assertions go red.
"""

import watch
from pycats.config import FPS


def test_vs_runs_30s_and_stops_on_match_over():
    frames, stop = watch.resolve_battle_plan(vs="chase", match=False, frames=None)
    assert frames == 30 * FPS == 1800
    assert stop is True


def test_vs_frames_flag_overrides_the_cap_but_keeps_early_stop():
    frames, stop = watch.resolve_battle_plan(vs="chase", match=False, frames=500)
    assert frames == 500
    assert stop is True


def test_all_vs_archetypes_get_the_30s_early_stop_plan():
    for vs in ("chase", "idler", "follower"):
        frames, stop = watch.resolve_battle_plan(vs=vs, match=False, frames=None)
        assert (frames, stop) == (30 * FPS, True), vs


def test_match_is_unchanged_6000_and_stops():
    frames, stop = watch.resolve_battle_plan(vs="idle", match=True, frames=None)
    assert frames == 6000
    assert stop is True


def test_scripted_replay_default_300_no_early_stop():
    frames, stop = watch.resolve_battle_plan(vs="idle", match=False, frames=None)
    assert frames == 300
    assert stop is False


def test_scripted_replay_respects_frames_override():
    frames, stop = watch.resolve_battle_plan(vs="idle", match=False, frames=120)
    assert frames == 120
    assert stop is False


def test_vs_battle_runs_headless_and_is_bounded():
    """Headless smoke: the --vs controllers pair + stop flag drive run_battle to
    a bounded snapshot list (the early KO-out path is exercised; at this tiny cap
    no match resolves, so it runs the full cap)."""
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    from pycats.sim.controllers import AttackerController
    from pycats.sim.runner import run_battle

    cap = 40
    snaps = run_battle(
        frames=cap,
        controllers=(AttackerController(attacker_num=1),
                     AttackerController(attacker_num=2)),
        stop_on_match_over=True,
    )
    assert 0 < len(snaps) <= cap
