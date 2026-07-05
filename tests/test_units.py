"""PX_PER_UNIT named constant + u() authoring helper (#195).

Pins the px↔unit authoring scale so it is single-sourced (not a magic 5.4 in
comments) and so the ADR-0003 derivation-guard (#233) has an importable constant to
re-evaluate against. Able-to-fail: change PX_PER_UNIT and these go red.
"""
from pycats.combat.units import u
from pycats.config import PX_PER_UNIT


def test_px_per_unit_is_the_calibrated_scale():
    # The #120-calibrated authoring scale. Red if the constant drifts.
    assert PX_PER_UNIT == 5.4


def test_u_converts_units_to_integer_pixels():
    # round(units * PX_PER_UNIT); the sim is integer-pixel (#80), so u() returns int.
    assert u(10) == 54          # round(54.0)
    assert u(1) == 5            # round(5.4)
    assert isinstance(u(1), int)


def test_u_matches_the_documented_derivations():
    # The exact values baked into the character data (byte-identity anchor):
    assert u(3.1) == 17         # DODGE_AIR_SPEED derivation (escapeair_force 3.1u)
    assert u(3.5) == 19         # Nalio fireball radius (3.5u -> r19)
    assert u(2.34) == 13        # Nalio d-tilt id0 radius
    assert u(3.13) == 17        # Nalio d-tilt id1 radius
    assert u(3.91) == 21        # Nalio d-tilt id2 radius


def test_u_is_single_source_of_the_scale():
    # u() must derive from the named constant, not a re-hardcoded literal — so a
    # change to PX_PER_UNIT propagates. (Guards against u() silently pinning its own 5.4.)
    assert u(100) == round(100 * PX_PER_UNIT)
