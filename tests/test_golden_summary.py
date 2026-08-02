"""Golden semantic summaries (#74 / S4).

`summarize(snaps)` distills a per-frame snapshot list into a tiny, reviewable
digest (frame count, phase/winner, attack activity, per-player states / lives /
percent / KO frames). The digest is the artifact a reviewer reads before
accepting a `PYCATS_UPDATE_GOLDENS=1` regen — see tests/golden/REGEN_PROTOCOL.md.
"""

import pytest

from tests import golden_util
from tests.golden_util import check_or_update, summarize


def _player(name, state, percent=0, lives=3, character="testcat"):
    # Real per-player snapshot tuples are wide; summarize reads indices 0 (name),
    # 1 (state), 7 (percent), 9 (lives) + the trailing `character` (#672 Phase 2a,
    # appended last). Pad the middle.
    return tuple([name, state, 0, 0, 0.0, 0.0, True, percent, 50, lives, True] + [0] * 10 + [character])


def _snap(players, atk=(), phase="in_play", winner=0):
    return (tuple(players), tuple(atk), phase, winner)


def test_summarize_counts_frames_and_states_and_max_percent():
    snaps = [
        _snap([_player("P1", "idle"), _player("P2", "idle")]),
        _snap([_player("P1", "walk"), _player("P2", "hurt", percent=10)]),
    ]
    s = summarize(snaps)
    assert s["frames"] == 2
    assert s["players"]["P2"]["states"] == ["hurt", "idle"]  # sorted, de-duped
    assert s["players"]["P1"]["states"] == ["idle", "walk"]
    assert s["players"]["P2"]["percent_max"] == 10


def test_summarize_detects_ko_frames_and_lives_arc():
    snaps = [
        _snap([_player("P1", "idle", lives=3), _player("P2", "idle", lives=3)]),
        _snap([_player("P1", "idle", lives=3), _player("P2", "ko", lives=2)]),
        _snap([_player("P1", "idle", lives=3), _player("P2", "ko", lives=1)]),
    ]
    s = summarize(snaps)
    assert s["players"]["P2"]["ko_frames"] == [1, 2]  # stock lost at frames 1 and 2
    assert s["players"]["P2"]["lives_start"] == 3
    assert s["players"]["P2"]["lives_end"] == 1
    assert s["players"]["P2"]["lives_min"] == 1
    assert s["players"]["P1"]["ko_frames"] == []


def test_summarize_counts_attack_frames_and_final_phase_winner():
    snaps = [
        _snap([_player("P1", "attack"), _player("P2", "idle")], atk=[(0, 0, 3, "P1", True, 0, 0, 12)]),
        _snap([_player("P1", "idle"), _player("P2", "ko")], atk=(), phase="match_over", winner=1),
    ]
    s = summarize(snaps)
    assert s["attack_active_frames"] == 1  # only the first frame has an attack
    assert s["final_phase"] == "match_over"
    assert s["winner"] == 1


def test_summarize_empty():
    s = summarize([])
    assert s["frames"] == 0 and s["players"] == {}


def test_golden_failure_message_names_onboarding_doc(tmp_path, monkeypatch):
    """B2/#1016: a failing golden points a first-time reader at docs/golden-tests.md.

    Record a baseline in an isolated golden dir, then feed a behaviour-changed run so
    the summary assertion fires — the message must name the onboarding doc. Able-to-fail:
    without the DOC_HINT append, ``docs/golden-tests.md`` is absent from the message.
    """
    monkeypatch.setattr(golden_util, "GOLDEN_DIR", tmp_path)

    recorded = [_snap([_player("P1", "idle"), _player("P2", "idle")])]
    monkeypatch.setenv("PYCATS_UPDATE_GOLDENS", "1")
    check_or_update("hintcase", recorded)  # write baseline
    monkeypatch.delenv("PYCATS_UPDATE_GOLDENS", raising=False)

    changed = [_snap([_player("P1", "walk"), _player("P2", "hurt", percent=10)])]
    with pytest.raises(AssertionError) as exc:
        check_or_update("hintcase", changed)
    msg = str(exc.value)
    assert "semantic summary changed" in msg
    assert "docs/golden-tests.md" in msg


def test_golden_summary_change_reports_field_level_diff(tmp_path, monkeypatch):
    """A1/#1017: a changed summary field produces a compact per-field
    ``path: expected → actual`` diff, not two whole-summary blobs.

    Able-to-fail: the old message dumped the full expected/actual summary JSON and
    never emitted a dotted field path like ``players.P2.percent_max``.
    """
    monkeypatch.setattr(golden_util, "GOLDEN_DIR", tmp_path)

    base = [_snap([_player("P1", "idle"), _player("P2", "idle", percent=0)])]
    monkeypatch.setenv("PYCATS_UPDATE_GOLDENS", "1")
    check_or_update("diffcase", base)  # write baseline
    monkeypatch.delenv("PYCATS_UPDATE_GOLDENS", raising=False)

    changed = [_snap([_player("P1", "idle"), _player("P2", "hurt", percent=42)])]
    with pytest.raises(AssertionError) as exc:
        check_or_update("diffcase", changed)
    msg = str(exc.value)
    assert "Changed fields (expected → actual)" in msg
    assert "players.P2.percent_max: 0 → 42" in msg  # field-level line, only the moved key
    assert "players.P2.states" in msg  # state set also changed
    assert "expected (sidecar) =" not in msg  # old whole-summary blob dump is gone
    assert "docs/golden-tests.md" in msg


def test_golden_raw_divergence_names_fighter_field_and_lead_in(tmp_path, monkeypatch):
    """A2/#1017: when the summary matches but raw bytes differ, the message names the
    diverging ``fighter.field`` and shows lead-in frames — not just a frame index.

    Change a field the semantic summary does NOT read (``rect_x``) so the summary
    check passes and execution reaches the raw byte compare. Able-to-fail: the old
    message printed only ``first divergence at frame N`` + truncated blobs, naming
    no field and showing no lead-in.
    """
    monkeypatch.setattr(golden_util, "GOLDEN_DIR", tmp_path)

    base = [
        _snap([_player("P1", "idle"), _player("P2", "idle")]),
        _snap([_player("P1", "idle"), _player("P2", "idle")]),
    ]
    monkeypatch.setenv("PYCATS_UPDATE_GOLDENS", "1")
    check_or_update("rawcase", base)  # write baseline
    monkeypatch.delenv("PYCATS_UPDATE_GOLDENS", raising=False)

    # Move P2's rect_x (index 2) at frame 1 only — the summary ignores position, so
    # the sidecar still matches and the raw byte compare is the one that fails.
    p2 = list(_player("P2", "idle"))
    p2[2] = 999  # rect_x
    changed = [
        _snap([_player("P1", "idle"), _player("P2", "idle")]),
        _snap([_player("P1", "idle"), tuple(p2)]),
    ]
    with pytest.raises(AssertionError) as exc:
        check_or_update("rawcase", changed)
    msg = str(exc.value)
    assert "first divergence at frame 1" in msg
    assert "P2.rect_x" in msg  # names the diverging fighter.field, not a positional index
    assert "frame 0 (matches)" in msg  # lead-in context frame
    assert "docs/golden-tests.md" in msg
