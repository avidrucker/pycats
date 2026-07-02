"""Narz jab — fast disjoint neutral-A poke (slice 3 of #294, #301).

Marth's jab is a quick sword stab (one box, not a tipper — that's the f-tilt's job),
but it still reaches BEYOND the hurtbox (disjoint). Golden-free: sim loads the default cat.
"""
from pycats.combat.data import load_fighter_data


def test_narz_has_its_own_single_box_jab():
    narz = load_fighter_data("narz")
    default = load_fighter_data("default")
    assert "jab" in narz.moves                      # neutral-A fires "jab" (move_select)
    assert "jab" not in default.moves               # default uses the "attack" alias
    jab = narz.moves["jab"]
    assert jab.name == "jab"
    assert len(jab.hitboxes) == 1                   # a single quick poke (not a tipper)


def test_narz_jab_is_disjoint():
    narz = load_fighter_data("narz")
    box = narz.moves["jab"].hitboxes[0].circle
    hurtbox_outer = max(c.dx + c.r for c in narz.hurtbox.circles)
    # the jab's near edge is past the hurtbox far edge → disjoint reach
    assert box.dx - box.r > hurtbox_outer


def test_narz_jab_is_fast_and_weak_vs_the_ftilt():
    # the jab is the quick poke; the f-tilt is the committal spacing/KO hit
    narz = load_fighter_data("narz")
    jab = narz.moves["jab"]
    ftilt_tip = narz.moves["ftilt"].hitboxes[0]
    assert jab.startup < narz.moves["ftilt"].startup          # faster
    assert jab.hitboxes[0].damage < ftilt_tip.damage          # weaker
