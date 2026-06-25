"""Golden semantic summaries (#74 / S4).

`summarize(snaps)` distills a per-frame snapshot list into a tiny, reviewable
digest (frame count, phase/winner, attack activity, per-player states / lives /
percent / KO frames). The digest is the artifact a reviewer reads before
accepting a `PYCATS_UPDATE_GOLDENS=1` regen — see tests/golden/REGEN_PROTOCOL.md.
"""
from tests.golden_util import summarize


def _player(name, state, percent=0, lives=3):
    # Real per-player snapshot tuples are wide; summarize only reads indices
    # 0 (name), 1 (state), 7 (percent), 9 (lives). Pad the rest.
    return tuple([name, state, 0, 0, 0.0, 0.0, True, percent, 50, lives, True] + [0] * 10)


def _snap(players, atk=(), phase="in_play", winner=0):
    return (tuple(players), tuple(atk), phase, winner)


def test_summarize_counts_frames_and_states_and_max_percent():
    snaps = [
        _snap([_player("P1", "idle"), _player("P2", "idle")]),
        _snap([_player("P1", "run"), _player("P2", "hurt", percent=10)]),
    ]
    s = summarize(snaps)
    assert s["frames"] == 2
    assert s["players"]["P2"]["states"] == ["hurt", "idle"]  # sorted, de-duped
    assert s["players"]["P1"]["states"] == ["idle", "run"]
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
        _snap([_player("P1", "attack"), _player("P2", "idle")],
              atk=[(0, 0, 3, "P1", True, 0, 0, 12)]),
        _snap([_player("P1", "idle"), _player("P2", "ko")],
              atk=(), phase="match_over", winner=1),
    ]
    s = summarize(snaps)
    assert s["attack_active_frames"] == 1  # only the first frame has an attack
    assert s["final_phase"] == "match_over"
    assert s["winner"] == 1


def test_summarize_empty():
    s = summarize([])
    assert s["frames"] == 0 and s["players"] == {}
