"""Watch/demo input display (#434, regridded #875) — reuse InputHistory in presenters.

Feed each frame's pressed + held (`InputFrame.pressed` / `.held`) into a per-player
`InputHistory` via that player's own keymap (`player.controls`), rendered by
`render_battle.draw_input_history` (now the #875 per-frame grid).

Two able-to-fail layers:
- the pure per-player record helper (data path), keymap-disjoint;
- a headless `ScreenshotPresenter(show_inputs=True)` smoke test proving the grid
  renders inside `run_battle` and that default-off leaves the render untouched.
"""

import types

from pycats.core.input import InputFrame
from pycats.input_history import PRESSED, InputHistory
from pycats.sim.presenters import record_player_histories
from pycats.sim.runner import P1_KEYS, P2_KEYS


def _players():
    # Stand-ins carrying only what the recorder reads: a `.controls` keymap.
    return (
        types.SimpleNamespace(controls=P1_KEYS),
        types.SimpleNamespace(controls=P2_KEYS),
    )


def _pf(*codes):
    """One frame's (pressed, held) with `codes` freshly pressed (held == pressed)."""
    fi = InputFrame(held=set(codes), pressed=set(codes), released=set())
    return fi.pressed, fi.held


def test_records_frame_marks_into_each_players_history_via_controls():
    p1, p2 = _players()
    h1, h2 = InputHistory(), InputHistory()
    # P1 presses left + attack this frame.
    pressed, held = _pf(P1_KEYS["left"], P1_KEYS["attack"])
    record_player_histories([h1, h2], [p1, p2], pressed, held)
    assert h1.frames() == [{"left": PRESSED, "attack": PRESSED}]
    assert h2.frames() == [{}]  # disjoint keymap: P2 sees an idle column


def test_recording_is_keymap_specific_disjoint_players():
    p1, p2 = _players()
    h1, h2 = InputHistory(), InputHistory()
    # A key that is P2's "up" — only P2's history should mark it.
    pressed, held = _pf(P2_KEYS["up"])
    record_player_histories([h1, h2], [p1, p2], pressed, held)
    assert h1.frames() == [{}]
    assert h2.frames() == [{"up": PRESSED}]


def test_empty_frame_records_idle_columns():
    p1, p2 = _players()
    h1, h2 = InputHistory(), InputHistory()
    pressed, held = _pf()
    record_player_histories([h1, h2], [p1, p2], pressed, held)
    assert h1.frames() == [{}] and h2.frames() == [{}]


def test_screenshot_presenter_runs_input_grid_path_in_run_battle(tmp_path):
    """End-to-end: run_battle threads `inputs=fi` to the presenter, which builds the
    per-player histories and renders the grid on saved frames — headless, no error.
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
