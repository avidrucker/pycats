"""#335 (DEV-A of #285) — the AttackerController derives its melee range from the
reach of the move it actually commits, instead of the flat `attack_range=45`.

Reach numbers are the #285 catalogue (center-relative = max(dx+r) − body_width/2),
computed from live FighterData. Gated behind `reach_aware`; the level-less default
keeps 45 (golden-safe).
"""
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pycats.combat.geometry import move_reach
from pycats.combat.data import load_fighter_data
from pycats.sim.controllers import AttackerController
from pycats.sim.runner import build_players, run_battle


# ---- move_reach: pure reach from FighterData (the #285 catalogue) --------------

def test_move_reach_matches_catalogue_ftilt():
    # forward-tilt center-relative reach, body width 40 (half 20)
    assert move_reach(load_fighter_data("nalio"), "ftilt", 40) == 58
    assert move_reach(load_fighter_data("birky"), "ftilt", 40) == 52
    assert move_reach(load_fighter_data("narz"), "ftilt", 40) == 64


def test_move_reach_matches_catalogue_jab():
    assert move_reach(load_fighter_data("nalio"), "jab", 40) == 53
    assert move_reach(load_fighter_data("birky"), "jab", 40) == 35


def test_move_reach_none_for_absent_move():
    # the default cat has no ftilt — derivation must fall back, not crash
    assert move_reach(load_fighter_data("default"), "ftilt", 40) is None


# ---- controller effective melee range -----------------------------------------

def test_default_controller_not_reach_aware_keeps_45():
    c = AttackerController()
    assert c.reach_aware is False
    p1, _p2, _ = build_players("nalio", "birky")
    assert c._melee_range(p1) == 45


def test_level5_controller_is_reach_aware_and_uses_ftilt_reach():
    # level 5 commits the forward-tilt (#292), so its melee range is the ftilt reach
    c = AttackerController(attacker_num=1, level=5, rng=random.Random(0))
    assert c.reach_aware is True
    p1_nalio, _p2, _ = build_players("nalio", "birky")
    assert c._melee_range(p1_nalio) == 58
    p1_narz, _p2b, _b = build_players("narz", "birky")
    assert c._melee_range(p1_narz) == 64


def test_reach_aware_falls_back_to_attack_range_when_move_absent():
    # a reach_aware bot on a character without the committed move keeps the constant
    c = AttackerController(attacker_num=1, reach_aware=True)  # level=None → commits jab
    p1_default, _p2, _ = build_players(None, "birky")  # default cat has only "attack"
    # default cat has no "jab" either → fall back to the literal attack_range
    assert c._melee_range(p1_default) == 45


# ---- discriminating: the gate opens at a gap the flat bot rejects --------------

def _place(p, cx, cy):
    p.rect.centerx = cx
    p.rect.centery = cy


def test_reach_aware_bot_attacks_at_a_gap_the_flat_bot_rejects():
    # nalio's committed move (jab at level=None) reaches 53 center-to-center; the flat
    # bot only attacks within 45. At a 50 px gap the reach-aware bot commits, the flat
    # bot holds. follow_through=1.0 + reaction_delay=0 (level-less defaults) → clean.
    aware = AttackerController(attacker_num=1, reach_aware=True, standoff=35)
    flat = AttackerController(attacker_num=1, reach_aware=False, standoff=35)
    keys = None
    for ctrl, expect_attack in ((aware, True), (flat, False)):
        p1, p2, _ = build_players("nalio", "birky")
        _place(p1, 100, 300)
        _place(p2, 150, 300)  # center gap 50 (between 45 and nalio jab 53)
        keys = p1.controls
        held = ctrl.decide(p1, p2, 0)
        assert (keys["attack"] in held) is expect_attack, (
            f"reach_aware={ctrl.reach_aware}: attack-in-held should be {expect_attack} "
            f"at gap 50 (held={held})"
        )


def test_reach_aware_changes_leveled_sim_trajectory():
    # end-to-end: flipping reach_aware on the leveled bots changes a real deterministic
    # battle — proof the knob reaches sim behaviour, not just a getter. reach_aware
    # never consumes self.rng (move_reach is pure), so the two runs share the same rng
    # draws until a reach decision genuinely diverges — any difference here IS the
    # reach logic biting. seed 1 / 2000f is a scenario where it binds (a mirror match
    # where the bot closes to standoff rarely exercises the wider ceiling — see #335).
    def run(reach_aware):
        rng = random.Random(1)
        c1 = AttackerController(attacker_num=1, level=5, rng=rng)
        c2 = AttackerController(attacker_num=2, level=5, rng=rng)
        c1.reach_aware = c2.reach_aware = reach_aware
        return run_battle(frames=2000, controllers=(c1, c2),
                          p1_char="nalio", p2_char="birky", stop_on_match_over=True)
    assert run(True) != run(False), "reach_aware must change the sim trajectory"
