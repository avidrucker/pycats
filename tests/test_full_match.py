# tests/test_full_match.py
"""A real chase battle that exercises the hurt/KO arc to a full defeat.

The deterministic ChaseController generates inputs once; we FREEZE that input list
and replay it, driving at least one KO (hurt + ko states + a stock loss) through
to a full 3-stock defeat. (Byte-stability of the replay is guarded by the recorded
golden in test_golden.py; ADR-0002 left a single engine, so the former
legacy-vs-statechart parity check is gone.)

NOTE (#44 → #64): #44's knockback decay briefly left the chase bot unable to
finish off a target parked at a ledge (full-defeat was deferred to #46). The #64
jab-reach fix lets the bot connect a body-blocked/fleeing target again, so it now
**fully 3-stocks** P2 — the assertion below is restored to a full defeat.
"""
from pycats.sim.runner import run_battle
from pycats.sim.controllers import ChaseController


def _captured_match_inputs():
    ctrl = ChaseController(attacker_num=1)
    run_battle(frames=6000, controller=ctrl, stop_on_match_over=True)
    return ctrl.emitted


def test_match_exercises_ko_arc_to_full_defeat():
    inputs = _captured_match_inputs()
    n = len(inputs)
    snaps = run_battle(frames=n, frame_inputs=inputs)
    assert len(snaps) == n

    # the hurt -> ko arc is exercised, and P2 is fully 3-stocked (#64 reach fix)
    states = {p[1] for snap in snaps for p in snap[0]}
    assert "hurt" in states and "ko" in states, sorted(states)
    p2_lives = [next(p for p in s[0] if p[0] == "P2")[9] for s in snaps]
    assert min(p2_lives) == 0, (
        f"expected a full defeat (P2 to 0 lives); P2 lives bottomed at {min(p2_lives)}"
    )
