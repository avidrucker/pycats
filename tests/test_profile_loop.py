"""Tests for the cProfile hot-function harness (#1247).

The reporting core (``find_functions`` / the #1236 hypothesis lookup) is pure
over a ``pstats.Stats``, so it is proven by profiling a KNOWN synthetic
workload and asserting the harness locates the function with the exact call
count it was called. A second, lighter test drives the real ``App`` headless
for a few frames in the ``playing`` state and asserts the profile captured
``App.step`` and the render dispatch — proving the harness exercises the
render/App path (the whole point vs ``bench.py``, which profiles only the
state engine).
"""

import cProfile
import pstats

from profile_loop import HYPOTHESES, find_functions, hypothesis_hits, profile_state


def _marker_helper():
    return sum(range(50))


def _synthetic_stats():
    def work():
        for _ in range(7):
            _marker_helper()

    prof = cProfile.Profile()
    prof.enable()
    work()
    prof.disable()
    return pstats.Stats(prof)


# ---- pure reporting core (able-to-fail against a known workload) --------------
def test_find_functions_locates_a_called_function_with_its_call_count():
    stats = _synthetic_stats()
    hits = find_functions(stats, "_marker_helper")
    assert hits, "the profiled helper must be found by name"
    _key, row = hits[0]
    # pstats row = (primitive_calls, total_calls, tottime, cumtime, callers)
    assert row[1] == 7


def test_find_functions_returns_empty_for_an_uncalled_name():
    stats = _synthetic_stats()
    assert find_functions(stats, "this_name_was_never_profiled") == []


def test_find_functions_can_narrow_by_file():
    stats = _synthetic_stats()
    # The helper lives in this test module, not in "settings.py".
    assert find_functions(stats, "_marker_helper", file_substr="settings.py") == []
    assert find_functions(stats, "_marker_helper", file_substr="test_profile_loop")


def test_hypotheses_carry_the_1236_targets():
    ids = {h["id"] for h in HYPOTHESES}
    # A1 (settings.load), B1 (font burst), B3 (runtime_settings/defaults copy),
    # B4 (uncached render_text_simple) are the named #1236 hotspots.
    assert {"A1", "B1", "B3", "B4"} <= ids
    for h in HYPOTHESES:
        assert h["matchers"], f"hypothesis {h['id']} needs at least one matcher"


def test_hypothesis_hits_reports_a_measured_row_per_hypothesis():
    stats = _synthetic_stats()
    hits = hypothesis_hits(stats)
    assert {h["id"] for h in hits} == {h["id"] for h in HYPOTHESES}
    for row in hits:
        # Every hypothesis is answered with a number (0 calls = refuted, >0 = present).
        assert isinstance(row["calls"], int)
        assert row["calls"] >= 0


# ---- integration: the harness drives the real render/App path ----------------
def test_playing_run_profiles_the_app_and_render_path():
    stats = profile_state("playing", frames=5)
    # App.step in the profile proves we drove the real per-frame loop.
    assert find_functions(stats, "step", file_substr="app.py"), "App.step must be profiled"
    # render_active_screen proves the RENDER path ran (bench.py never touches it).
    assert find_functions(stats, "render_active_screen"), "render path must be exercised"


def test_playing_run_exercises_a_1236_hypothesis_function():
    stats = profile_state("playing", frames=5)
    # settings.load() runs every frame via _tick_esc_hold — the A1 hotspot — so a
    # 5-frame run must show it. This ties the harness output to a #1236 target.
    assert find_functions(stats, "load", file_substr="settings.py"), "A1 (settings.load) must appear"
