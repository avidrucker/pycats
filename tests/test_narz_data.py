"""Narz (Marth-archetype) stats + seam — slice 1 of #294 (scoped by #290).

Pure-data foundation: a distinct FighterData differing from the default cat in its
movement scalars (weight/gravity/jump_vel and, since the #1209 re-pin, the grounded
walk/run units), the load_fighter_data branch, and the selectable-roster entry.
Golden-free: the sim/golden path loads the default cat via "P1"/"P2".
"""

from pycats.characters import roster
from pycats.combat.data import load_fighter_data


def test_narz_loads_distinct_movement_scalars():
    narz = load_fighter_data("narz")
    # the meaningful deltas from the Mario/default baseline (#290 stat table)
    assert narz.weight == 87
    assert narz.gravity == 0.45
    assert narz.jump_vel == -12


def test_narz_differs_from_default_on_the_deltas():
    narz = load_fighter_data("narz")
    default = load_fighter_data("default")
    # revert-check: a wrong scalar (or no branch) fails here
    assert (narz.weight, narz.gravity, narz.jump_vel) != (default.weight, default.gravity, default.jump_vel)
    assert narz.weight != default.weight
    assert narz.gravity != default.gravity


def test_narz_non_delta_fields_match_baseline():
    # Marth shares jump-count, fall speed, and DASH speed (1.5u → 8) with the Mario
    # baseline; its WALK and RUN are faster grounded values — see the test below.
    narz = load_fighter_data("narz")
    default = load_fighter_data("default")
    assert narz.max_jumps == 2 == default.max_jumps
    assert narz.max_fall_speed == default.max_fall_speed
    assert narz.dash_speed == 8 == default.dash_speed  # both dash 1.5u → 8


def test_narz_walk_and_run_are_faster_grounded_values():
    # #1209 (ADR-0011): Marth's grounded speeds are per-character raw units — walk 1.6u
    # → 9 (faster than Mario's 6), run 1.8u → 10 (faster than the 8 baseline); the dash
    # stays 1.5u → 8. Marth is the fast-walking swordfighter, now grounded, not a copy.
    narz = load_fighter_data("narz")
    default = load_fighter_data("default")
    assert (narz.walk, narz.dash, narz.run) == (1.6, 1.5, 1.8)
    assert narz.move_speed == 9 and default.move_speed == 6
    assert narz.run_speed == 10 and default.run_speed == 8


def test_narz_keeps_default_placeholders_except_its_own_moves():
    # hurtbox is still the default placeholder (#290 v1 body); the "attack" neutral-A
    # alias is kept as a placeholder, but slice 2 (#299) adds Narz's own "ftilt".
    narz = load_fighter_data("narz")
    default = load_fighter_data("default")
    assert narz.hurtbox == default.hurtbox
    assert narz.moves["attack"] == default.moves["attack"]  # placeholder kept
    assert "ftilt" in narz.moves and "ftilt" not in default.moves  # Narz's own move


def test_narz_is_in_the_selectable_roster():
    # watch.py / char-select read ARCHETYPE_ROSTER + ARCHETYPE_NAME (indexed directly)
    assert "narz" in roster.ARCHETYPE_ROSTER
    assert roster.ARCHETYPE_NAME["narz"] == "Narz"
    assert roster.palette_for("narz") is not None  # never raises; real palette set
