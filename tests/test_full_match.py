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
from pycats.sim.controllers import ChaseController
from pycats.sim.runner import run_battle


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


# Stage geometry: the main thick platform stands across x∈[80, 880] (SCREEN_WIDTH
# 960, body-margin per pycats/sim/runner.build_stage). A target launched well past
# that extent is "off-platform / at a ledge" — the scenario #46 is about.
_PLATFORM_X_LO, _PLATFORM_X_HI = 120, 840  # loose inner bound (margin off [80,880])


def _p2_lives_series(snaps):
    return [next(p for p in s[0] if p[0] == "P2")[9] for s in snaps]


def test_chase_bot_3stocks_a_ledge_parked_target_without_stalling():
    """#46 regression: under realistic knockback (#44), the chase bot used to STALL
    — it scored the first KO then froze, unable to follow a target parked at a ledge
    / off the platform (repro: P1 x=82, P2 x=41, only 1 of 3 stocks taken, both
    players frozen). #64's jab-reach fix lets it pursue off-platform targets and
    re-engage after each respawn, so the match now runs to a *bounded, full* 3-stock
    defeat. This pins the anti-stall contract that the bare full-defeat assertion
    above leaves implicit.

    Driven live (stop_on_match_over) so the match's natural length is the evidence:
    a stall would run the whole budget without ever reaching `match_over`.
    """
    budget = 6000
    ctrl = ChaseController(attacker_num=1)
    snaps = run_battle(frames=budget, controller=ctrl, stop_on_match_over=True)
    n = len(snaps)

    # 1) the match TERMINATES — no freeze/stall — well within the frame budget.
    assert n < budget, f"match never ended (stalled?): ran the full {budget}-frame budget"
    assert snaps[-1][2] == "match_over", f"match never reached match_over; phase={snaps[-1][2]!r}"
    assert snaps[-1][3] == 1, f"P1 (the chaser) should win; winner={snaps[-1][3]!r}"

    # 2) P2 loses ALL three stocks, across three DISTINCT KOs — i.e. the bot
    #    re-engages after each respawn rather than stalling once.
    p2_lives = _p2_lives_series(snaps)
    assert p2_lives[0] == 3 and p2_lives[-1] == 0, (
        f"expected a 3->0 defeat; P2 lives went {p2_lives[0]} -> {p2_lives[-1]}"
    )
    ko_steps = [f for f in range(1, n) if p2_lives[f] < p2_lives[f - 1]]
    assert len(ko_steps) == 3, f"expected 3 KOs (one per stock), got {len(ko_steps)}: {ko_steps}"

    # 3) at least one KO finished an OFF-PLATFORM target (the ledge scenario): the
    #    bot pursued past the platform extent instead of only KOing from mid-stage.
    def p2_x_before_ko(f):
        return next(p for p in snaps[f - 1][0] if p[0] == "P2")[2]

    pre_ko_x = [p2_x_before_ko(f) for f in ko_steps]
    off_platform = [x for x in pre_ko_x if not (_PLATFORM_X_LO <= x <= _PLATFORM_X_HI)]
    assert off_platform, (
        "every KO happened mid-platform; expected the bot to pursue and finish at "
        f"least one off-platform/ledge target. pre-KO P2 x = {[round(x) for x in pre_ko_x]}"
    )
