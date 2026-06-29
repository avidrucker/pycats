# tests/test_parity.py
"""Backend equivalence, anchored on the recorded golden (ADR-0002 step 1, #176).

Previously this asserted the **legacy** and **statechart** backends were
byte-identical to each *other* — two live engines cross-checked per frame. ADR-0002
(#174) deletes the legacy backend, so that live cross-check is going away. To keep
the equivalence from lapsing we anchor it on the **committed golden** instead:

  * `tests/test_golden.py` already asserts **statechart == golden** for the same two
    scenarios (`default`, `combat`).
  * this file asserts **legacy == the SAME golden**.

Together they still prove legacy == statechart (both == golden) for as long as legacy
exists — but via the frozen record, not a live second engine. So when the next slice
deletes the legacy backend (and this file with it), the statechart-vs-golden coverage
in `test_golden.py` carries on with nothing lost. This also verifies the golden
*faithfully froze legacy's behaviour* before legacy is removed (it was recorded from
statechart; this proves it equals legacy too).

Reuses the `default` / `combat` golden files maintained by `test_golden.py` (single
source of truth; `PYCATS_UPDATE_GOLDENS=1` regen is byte-identical from either backend
while parity holds).
"""
from pycats.sim.runner import run_battle, KEYMAPS
from pycats.sim.input_script import compile_timeline, COMBAT_SCRIPT
from tests.golden_util import check_or_update

DEFAULT_FRAMES = 200
COMBAT_TAIL = 240


def test_legacy_matches_default_golden():
    """The legacy backend still reproduces the committed `default` golden."""
    snaps = run_battle(backend="legacy", frames=DEFAULT_FRAMES)
    assert len(snaps) == DEFAULT_FRAMES
    check_or_update("default", snaps)


def test_legacy_matches_combat_golden_and_reaches_hurt_and_ko():
    """Legacy reproduces the `combat` golden, and the run still exercises hurt+ko."""
    frame_inputs = compile_timeline(COMBAT_SCRIPT, KEYMAPS)
    frames = len(frame_inputs) + COMBAT_TAIL
    snaps = run_battle(backend="legacy", frames=frames, frame_inputs=frame_inputs)
    assert len(snaps) == frames

    all_states = {p[1] for snap in snaps for p in snap[0]}
    assert "hurt" in all_states, (
        f"'hurt' state never reached in combat scenario; visited: {sorted(all_states)}"
    )
    assert "ko" in all_states, (
        f"'ko' state never reached in combat scenario; visited: {sorted(all_states)}"
    )

    check_or_update("combat", snaps)
