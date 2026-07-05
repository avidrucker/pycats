"""Watch/demo input display (#434) — reuse #21's InputHistory in the presenters.

The correct approach (vs the reverted #405 held-only overlay): feed each frame's
press-edge (`InputFrame.pressed`) into a per-player `InputHistory` via that player's
own keymap (`player.controls`), rendered by the existing `render_battle.draw_input_history`.

Two able-to-fail layers:
- the pure per-player record helper (data path), keymap-disjoint;
- a headless `ScreenshotPresenter(show_inputs=True)` smoke test proving the strip
  renders inside `run_battle` and that default-off leaves the render untouched.
"""
import types

from pycats.core.input import InputFrame
from pycats.input_history import InputHistory
from pycats.sim.presenters import record_player_histories
from pycats.sim.runner import P1_KEYS, P2_KEYS


def _players():
    # Stand-ins carrying only what the recorder reads: a `.controls` keymap.
    return (
        types.SimpleNamespace(controls=P1_KEYS),
        types.SimpleNamespace(controls=P2_KEYS),
    )


def _pressed(*codes):
    return InputFrame(held=set(), pressed=set(codes), released=set()).pressed


def test_records_press_edge_into_each_players_history_via_controls():
    p1, p2 = _players()
    h1, h2 = InputHistory(), InputHistory()
    # P1 presses left + attack this frame.
    record_player_histories([h1, h2], [p1, p2], _pressed(P1_KEYS["left"], P1_KEYS["attack"]))
    assert h1.entries() == ["←A"]          # _GLYPHS order: directions then buttons
    assert h2.entries() == []              # disjoint keymap: P2 sees nothing


def test_recording_is_keymap_specific_disjoint_players():
    p1, p2 = _players()
    h1, h2 = InputHistory(), InputHistory()
    # A key that is P2's "up" — only P2's history should log it.
    record_player_histories([h1, h2], [p1, p2], _pressed(P2_KEYS["up"]))
    assert h1.entries() == []
    assert h2.entries() == ["↑"]


def test_empty_frame_records_nothing():
    p1, p2 = _players()
    h1, h2 = InputHistory(), InputHistory()
    record_player_histories([h1, h2], [p1, p2], _pressed())
    assert h1.entries() == [] and h2.entries() == []


def test_screenshot_presenter_runs_input_strip_path_in_run_battle(tmp_path):
    """End-to-end: run_battle threads `inputs=fi` to the presenter, which builds the
    per-player histories and renders the strip on saved frames — headless, no error.
    Able-to-fail on the runner seam: drop `inputs=fi` and histories stay None."""
    import os

    from pycats.sim.presenters import ScreenshotPresenter
    from pycats.sim.runner import run_battle

    sp = ScreenshotPresenter(str(tmp_path), frames={0: "s0", 1: "s1"}, show_inputs=True)
    run_battle(frames=3, presenter=sp)
    assert sp._input_histories is not None, "runner did not thread inputs=fi to the presenter"
    assert len(sp._input_histories) == 2  # one InputHistory per player
    assert sp.saved and all(os.path.exists(p) for _, p in sp.saved)


def test_screenshot_presenter_default_off_records_nothing(tmp_path):
    """Default off ⇒ no histories built, render path untouched (golden-safe)."""
    from pycats.sim.presenters import ScreenshotPresenter
    from pycats.sim.runner import run_battle

    sp = ScreenshotPresenter(str(tmp_path), frames={0: "s0"}, show_inputs=False)
    run_battle(frames=2, presenter=sp)
    assert sp._input_histories is None
