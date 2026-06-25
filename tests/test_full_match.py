# tests/test_full_match.py
"""Backend parity across a real chase battle that exercises the hurt/KO arc.

The deterministic ChaseController generates inputs once on a legacy run; we FREEZE
that input list and replay it through both backends, so this is a clean
byte-identical parity test on identical fixed inputs — its primary value — while
also driving at least one KO (hurt + ko states + a stock loss).

NOTE (#44 → #64): #44's knockback decay briefly left the chase bot unable to
finish off a target parked at a ledge (full-defeat was deferred to #46). The #64
jab-reach fix lets the bot connect a body-blocked/fleeing target again, so it now
**fully 3-stocks** P2 — the assertion below is restored to a full defeat.
"""
from pycats.sim.runner import run_battle
from pycats.sim.controllers import ChaseController


def _captured_match_inputs():
    ctrl = ChaseController(attacker_num=1)
    run_battle("legacy", frames=6000, controller=ctrl, stop_on_match_over=True)
    return ctrl.emitted


def test_match_byte_identical_and_exercises_ko_arc():
    inputs = _captured_match_inputs()
    n = len(inputs)
    legacy = run_battle("legacy", frames=n, frame_inputs=inputs)
    statechart = run_battle("statechart", frames=n, frame_inputs=inputs)

    # byte-identical parity across the whole replay (the primary regression value)
    assert len(legacy) == len(statechart) == n
    for f, (a, b) in enumerate(zip(legacy, statechart)):
        assert a == b, f"divergence at frame {f}:\n legacy={a}\n  state={b}"

    # the hurt -> ko arc is exercised, and P2 is fully 3-stocked (#64 reach fix)
    states = {p[1] for snap in legacy for p in snap[0]}
    assert "hurt" in states and "ko" in states, sorted(states)
    p2_lives = [next(p for p in s[0] if p[0] == "P2")[9] for s in legacy]
    assert min(p2_lives) == 0, (
        f"expected a full defeat (P2 to 0 lives); P2 lives bottomed at {min(p2_lives)}"
    )
