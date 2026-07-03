"""The curated Nalio-vs-Birky showcase demonstrates each feature (#325, epic #308).

Two gates:

1. `test_showcase_exercises_each_feature` — the original "feature-touched-SOMEWHERE"
   gate: each event/state occurs anywhere in the run. Kept as a weak safety net.
2. The window-bound per-beat gate (#397, from the #395 audit) — each showcased feature
   must occur inside ITS caption's frame window. #398 re-choreographed the demo so all
   seven beats pass. See the section comment below.

`stun` (shield-break) is deliberately NOT required — a fixed input script can't reliably
break a held shield (jabs whiff on the shield bubble, so it only drains passively, which
doesn't trigger the hit-driven break). `KO` is likewise NOT required (#398): the default
cats are jab-only (no smash/launcher — see combat/charge.py), so jab knockback can't KO
at reasonable percent; the *only* KO these fighters can produce is a walk-off
self-destruct, which is the very anti-pattern #395 flagged. The demo therefore ends
cleanly with P1 hanging on the ledge and does not stage a KO. `battle_log.NOTABLE_STATES`
also doesn't emit STATE events for `ledge_hang`, so those states are read from the raw
snapshot state (part index 1), not the event-log.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from pycats.config import SHIELD_DRAIN_PER_FRAME
from pycats.sim.captions import is_active
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
    # Event-log: jumps and landed hits occur. (KO is not required — the jab-only cats can
    # only KO via a walk-off self-destruct; see the module docstring. ATTACK is not
    # required either: an ATTACK event only fires while a hitbox stays *active*, but the
    # re-choreographed jabs all CONNECT, so `process_hits` consumes each hitbox before the
    # snapshot — the connect surfaces as the stronger HIT event instead of ATTACK.)
    evtypes = {e.type for e in events_from_snaps(snaps)}
    assert {"JUMP", "HIT"} <= evtypes, sorted(evtypes)
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
# The #395 audit found 4 of 7 beats (3/4/6/7) did not demonstrate their feature
# in-window; #398 re-choreographed the demo so all seven now pass (the `xfail` markers
# were removed as each beat was fixed). Seg 2's original defect was presentation-only
# (the #352 dwell freezes the wrong frame) and isn't visible in the sim snapshots, so
# beat 2 asserts only that the airborne double-jump occurs in-window; the dwell-emphasis
# fix is tracked separately.
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


def test_beat3_jab_connects_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    fr = _frames(caps, snaps, 2)
    p2_start = _snap(snaps, fr.start, 1)[_PERCENT]
    landed = any(_snap(snaps, f, 1)[_PERCENT] > p2_start + 1e-6 for f in fr)
    assert landed, "the jab beat should land a hit (P2 takes damage) inside its window"


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


def test_beat6_fireball_projectile_in_flight_in_window(showcase_run):
    # #432: the fireball beat fires Nalio's neutral-B and the projectile travels in-window.
    _d, snaps, caps = showcase_run
    fire = [i for i, c in enumerate(caps) if "fireball" in c.text.lower()]
    assert fire, "there should be a fireball beat (caption mentioning 'fireball')"
    idx = fire[0]
    p1_name = snaps[0][0][0][0]  # P1 (Nalio)'s char_name — ties the projectile to its owner
    # snaps[f] = (players, atk, phase, winner); atk entry = (x,y,frames_left,owner,active,cx,cy,r)
    active = any(
        any(a[3] == p1_name and a[4] for a in snaps[f][1])
        for f in _frames(caps, snaps, idx)
    )
    assert active, "Nalio's fireball projectile should be active in the fireball beat's window"


def test_beat7_dodge_passes_the_opponent_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    dodge_frames = [f for f in _frames(caps, snaps, 6) if _snap(snaps, f, 0)[_STATE] == "dodge"]
    assert dodge_frames, "P1 should roll-dodge inside the beat's window"
    swept = [_snap(snaps, f, 0)[_RECT_X] for f in dodge_frames]
    lo, hi = min(swept), max(swept)
    passed = any(lo <= _snap(snaps, f, 1)[_RECT_X] <= hi for f in dodge_frames)
    assert passed, "the roll should pass through/past the opponent (P2 x within P1's dodge sweep)"


def test_beat8_ledge_hang_is_held_in_window(showcase_run):
    _d, snaps, caps = showcase_run
    held = sum(1 for f in _frames(caps, snaps, 7) if _snap(snaps, f, 0)[_STATE] == "ledge_hang")
    assert held >= _LEDGE_HANG_MIN_FRAMES, (
        f"the edge-grab beat should hold the ledge >= {_LEDGE_HANG_MIN_FRAMES} frames (got {held})")


def test_late_payoff_beats_freeze_on_their_action_frame(showcase_run):
    # #412: beats 2/3/7 pay off late in their window, so they set `dwell_at` to freeze on
    # the action (not a pre-action pose). Assert P1 is in the beat's action state at each
    # chosen dwell_at frame — the machine-verifiable half of "the dwelled frame shows the
    # action" (the visual half is re-checkable via `watch.py --demo showcase --shots`).
    _d, snaps, caps = showcase_run
    checks = {
        1: ("double-jump airborne", lambda p: not p[_ON_GROUND]),
        2: ("jab attacking", lambda p: p[_STATE] == "attack"),
        7: ("ledge hang", lambda p: p[_STATE] == "ledge_hang"),
    }
    for idx, (what, pred) in checks.items():
        at = caps[idx].dwell_at
        assert at is not None, f"beat {idx + 1} ({what}) should set dwell_at"
        p1 = _snap(snaps, at, 0)
        assert pred(p1), f"beat {idx + 1} dwell_at=f{at} should show {what}; P1 state={p1[_STATE]}"


def test_showcase_shows_at_most_one_caption_per_frame(showcase_run):
    # #419: the showcase beats are SEQUENTIAL, so at most one caption may be active on any
    # frame — two would render stacked (bottom-center) and, on a dwell freeze, hold ~2.5s.
    # Windows are inclusive-inclusive, so an `end` equal to the next `start` double-renders.
    # (Overlap is allowed in the demo model generally — nested spans — but not this
    # sequential showcase, hence a showcase-specific invariant.)
    _d, snaps, caps = showcase_run
    for f in range(len(snaps)):
        active = [c.text.split(" — ")[0] for c in caps if is_active(c, f)]
        assert len(active) <= 1, f"frame {f} has >1 caption active: {active}"
