"""The curated Nalio-vs-Birky showcase demonstrates each feature (#325, epic #308).

Two gates:

1. `test_showcase_exercises_each_feature` — the original "feature-touched-SOMEWHERE"
   gate: each event/state occurs anywhere in the run. Kept as a weak safety net.
2. The window-bound per-beat gate (#397, from the #395 audit) — each showcased feature
   must occur inside ITS caption's frame window. 4 of 7 beats don't yet (they are
   `xfail(strict=True)` until #398 re-choreographs them). See the section comment below.

`stun` (shield-break) is deliberately NOT required — a fixed input script can't reliably
break a held shield (jabs whiff on the shield bubble, so it only drains passively, which
doesn't trigger the hit-driven break). `battle_log.NOTABLE_STATES` also doesn't emit
STATE events for `ledge_hang`, so those states are read from the raw snapshot state (part
index 1), not the event-log.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from pycats.config import SHIELD_DRAIN_PER_FRAME
from pycats.sim.demo import DEMOS, demo_timeline, demo_frames, demo_captions
from pycats.sim.runner import run_battle, KEYMAPS
from pycats.sim.battle_log import events_from_snaps


def _run_showcase():
    d = DEMOS["showcase"]
    snaps = run_battle(frame_inputs=demo_timeline(d, KEYMAPS), frames=demo_frames(d),
                       p1_char=d.p1_char, p2_char=d.p2_char)
    return d, snaps


def test_showcase_registered_with_captioned_segments():
    d = DEMOS["showcase"]
    assert d.p1_char == "nalio" and d.p2_char == "birky"
    caps = demo_captions(d)
    assert len(caps) == len(d.segments) >= 5
    assert all(c.text for c in caps), "every segment has a caption"


def test_showcase_exercises_each_feature():
    _d, snaps = _run_showcase()
    # Event-log: attacks, jumps, a landed hit, and a KO all occur.
    evtypes = {e.type for e in events_from_snaps(snaps)}
    assert {"ATTACK", "JUMP", "HIT", "KO"} <= evtypes, sorted(evtypes)
    # Visited fighter states (snapshot part index 1): shield, dodge, ledge-grab.
    states = {part[1] for snap in snaps for part in snap[0]}
    assert {"shield", "dodge", "ledge_hang"} <= states, sorted(states)


# --------------------------------------------------------------------------- #
# Window-bound per-beat gate (#397, from the #395 audit).
#
# `test_showcase_exercises_each_feature` above is a "feature-touched-SOMEWHERE"
# gate: it asserts each event/state occurs anywhere in the 480-frame run, decoupled
# from the caption that narrates it — so a lone airborne jump satisfies "double-jump",
# a 1-frame ledge_hang from a walk-off satisfies "edge-grab", and a HIT (on P2) plus a
# shield state (on P1) independently satisfy "hit while shielding" though no attack
# ever contacts the shield. The tests below instead bind each showcased feature to ITS
# caption's frame window, so a beat that drifts out of its window FAILS.
#
# Per the #395 audit, 4 of 7 beats do not yet demonstrate their feature in-window —
# those are `xfail(strict=True)`, so #398's re-choreography turns them green and a
# leftover marker on a fixed beat fails (forcing its removal). Seg 2's real defect is
# presentation-only (the #352 dwell freezes the wrong frame) and isn't visible in the
# sim snapshots, so beat 2 asserts only that the airborne double-jump occurs in-window
# (which it does today); the dwell-emphasis fix is tracked in #398.
#
# PlayerSnap field indices (mirror `runner.PlayerSnap` field order).
_STATE, _RECT_X, _ON_GROUND, _PERCENT, _SHIELD_HP, _JUMPS = 1, 2, 6, 7, 8, 11

# A demonstrated ledge grab holds the ledge, not a 1-frame incidental touch.
_LEDGE_HANG_MIN_FRAMES = 10


@pytest.fixture(scope="module")
def showcase_run():
    d, snaps = _run_showcase()
    return d, snaps, demo_captions(d)


def _snap(snaps, frame, player):
    """The PlayerSnap tuple for `player` (0=P1/Nalio, 1=P2/Birky) at `frame`."""
    return snaps[frame][0][player]


def _frames(caps, snaps, seg_index, lo=0):
    """Inclusive frame range of the seg_index-th (0-based) caption's window, clamped to
    the frames that actually ran. A caption's `end` can sit one past the last snapshot
    (seg 7's window ends at 480 while the run yields frames 0..479), so clamp to
    `len(snaps) - 1`. `lo` raises the start (pass lo=1 for tests that read frame f-1)."""
    s, e = caps[seg_index].frames
    return range(max(lo, s), min(e, len(snaps) - 1) + 1)


def test_beat1_approach_closes_the_distance(showcase_run):
    _d, snaps, caps = showcase_run
    fr = _frames(caps, snaps, 0)
    s, e = fr.start, fr.stop - 1
    gap_start = abs(_snap(snaps, s, 0)[_RECT_X] - _snap(snaps, s, 1)[_RECT_X])
    gap_end = abs(_snap(snaps, e, 0)[_RECT_X] - _snap(snaps, e, 1)[_RECT_X])
    assert gap_end < gap_start, f"fighters should approach in beat 1: gap {gap_start}->{gap_end}"


def test_beat2_double_jump_is_airborne_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    airborne_jump = any(
        _snap(snaps, f, 0)[_JUMPS] < _snap(snaps, f - 1, 0)[_JUMPS]
        and not _snap(snaps, f - 1, 0)[_ON_GROUND]
        for f in _frames(caps, snaps, 1, lo=1))
    assert airborne_jump, "an airborne (second) jump should occur inside the double-jump beat's window"


@pytest.mark.xfail(strict=True, reason="#398: seg-3 'jab' is an airborne aerial that whiffs — "
                                       "P2 is first damaged at f142 (seg 5), outside this window")
def test_beat3_jab_connects_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    fr = _frames(caps, snaps, 2)
    p2_start = _snap(snaps, fr.start, 1)[_PERCENT]
    landed = any(_snap(snaps, f, 1)[_PERCENT] > p2_start + 1e-6 for f in fr)
    assert landed, "the jab beat should land a hit (P2 takes damage) inside its window"


@pytest.mark.xfail(strict=True, reason="#398: P1 can't shield airborne & Birky never attacks — "
                                       "shield only drains passively, no hit contacts it")
def test_beat4_shield_blocks_a_hit_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    # A blocked hit subtracts the full atk.damage (~3% for a jab) from shield_hp in one
    # frame (fighter.py); passive drain is only SHIELD_DRAIN_PER_FRAME (0.2). A single-
    # frame drop beyond passive, while shielding, is therefore a block.
    blocked = any(
        _snap(snaps, f - 1, 0)[_STATE] == "shield"
        and (_snap(snaps, f - 1, 0)[_SHIELD_HP] - _snap(snaps, f, 0)[_SHIELD_HP])
        > SHIELD_DRAIN_PER_FRAME + 0.1
        for f in _frames(caps, snaps, 3, lo=1))
    assert blocked, "the shield beat should show P1 blocking a hit (shield_hp drops beyond passive) in its window"


def test_beat5_jab_combo_racks_damage_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    fr = _frames(caps, snaps, 4)
    p2_start = _snap(snaps, fr.start, 1)[_PERCENT]
    racked = any(_snap(snaps, f, 1)[_PERCENT] > p2_start + 1e-6 for f in fr)
    assert racked, "the jab-combo beat should rack damage on P2 inside its window"


@pytest.mark.xfail(strict=True, reason="#398: the roll fires in open space — Birky is far right, "
                                       "P1 rolls left away, so it never passes the opponent")
def test_beat6_dodge_passes_the_opponent_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    dodge_frames = [f for f in _frames(caps, snaps, 5) if _snap(snaps, f, 0)[_STATE] == "dodge"]
    assert dodge_frames, "P1 should roll-dodge inside the beat's window"
    swept = [_snap(snaps, f, 0)[_RECT_X] for f in dodge_frames]
    lo, hi = min(swept), max(swept)
    passed = any(lo <= _snap(snaps, f, 1)[_RECT_X] <= hi for f in dodge_frames)
    assert passed, "the roll should pass through/past the opponent (P2 x within P1's dodge sweep)"


@pytest.mark.xfail(strict=True, reason="#398: only a 1-frame ledge_hang (f409) then a held-left "
                                       "walk-off self-destruct — the ledge is never held")
def test_beat7_ledge_hang_is_held_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    held = sum(1 for f in _frames(caps, snaps, 6) if _snap(snaps, f, 0)[_STATE] == "ledge_hang")
    assert held >= _LEDGE_HANG_MIN_FRAMES, (
        f"the edge-grab beat should hold the ledge >= {_LEDGE_HANG_MIN_FRAMES} frames (got {held})")
