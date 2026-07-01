"""NPC platform-reunification — no vertical-standoff stall (#369, epic #365).

Pinned by #367: the jump-up input was HELD every frame its gate held, so the lower bot
got one press edge, jumped once, then sat idle holding `up` — a stable limit cycle that
ran the seed-3 `nalio` L5 vs `birky` L9 match the full 30s (1800f) with no engagement.
The fix PULSES the jump-up so a fresh press re-fires the jump and the bot climbs. This
asserts the sustained x-aligned / different-platform standstill is gone.
"""
import random

from pycats.sim.runner import run_battle
from pycats.sim.controllers import AttackerController


def _longest_standoff(p1_char, p2_char, l1, l2, seed=3, frames=1800):
    """Longest run of consecutive frames where the two bots are x-aligned but on
    different platforms (a not-engaging vertical standstill)."""
    rng = random.Random(seed)
    cs = (AttackerController(1, level=l1, rng=rng), AttackerController(2, level=l2, rng=rng))
    snaps = run_battle(frames=frames, controllers=cs, p1_char=p1_char, p2_char=p2_char,
                       stop_on_match_over=True)
    best = cur = 0
    for sn in snaps:
        a, b = sn[0][0], sn[0][1]          # P1, P2 parts: (name, state, x, y, ...)
        dx = abs((a[2] + 20) - (b[2] + 20))
        dy = abs(a[3] - b[3])
        if dx < 60 and dy > 80:            # x-aligned but on different platforms
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def test_no_sustained_vertical_standoff_seed3():
    """#369: the seed-3 nalio-L5 vs birky-L9 match must not lock into a prolonged
    x-aligned / different-platform standstill. Able-to-fail: the pre-fix build sits in
    that state for 625 consecutive frames (the held-not-pulsed jump-up limit cycle)."""
    streak = _longest_standoff("nalio", "birky", 5, 9)
    assert streak < 150, f"NPCs stuck in a vertical standoff for {streak} frames (#369)"
