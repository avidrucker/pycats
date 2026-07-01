"""The curated Nalio-vs-Birky showcase demonstrates each feature (#325, epic #308).

Coverage gate: run the `showcase` demo headless and assert it exercises the target
features — via the derived event-log (ATTACK/JUMP/HIT/KO) and the visited fighter-state
set (shield/dodge/ledge_hang). `stun` (shield-break) is deliberately NOT required — see
the ticket finding: a fixed input script can't reliably break a held shield (jabs whiff
on the shield bubble, so it only drains passively, which doesn't trigger the hit-driven
break). `battle_log.NOTABLE_STATES` also doesn't emit STATE events for `ledge_hang`, so
those two states are read from the raw snapshot state (part index 1), not the event-log.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

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
