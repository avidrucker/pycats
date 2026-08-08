"""PX_PER_UNIT named constant + u()/vel() authoring helpers (#195, #785).

Pins the px↔unit authoring scale so it is single-sourced (not a magic 5.4 in
comments) and so the ADR-0003 derivation-guard (#233) has an importable constant to
re-evaluate against. Able-to-fail: change PX_PER_UNIT and these go red.
"""

from pycats.combat.units import u, vel
from pycats.config import PX_PER_UNIT


def test_px_per_unit_is_the_calibrated_scale():
    # The #120-calibrated authoring scale. Red if the constant drifts.
    assert PX_PER_UNIT == 5.4


def test_u_converts_units_to_integer_pixels():
    # round(units * PX_PER_UNIT); the sim is integer-pixel (#80), so u() returns int.
    assert u(10) == 54  # round(54.0)
    assert u(1) == 5  # round(5.4)
    assert isinstance(u(1), int)


def test_u_matches_the_documented_derivations():
    # The exact values baked into the character data (byte-identity anchor):
    assert u(3.1) == 17  # DODGE_AIR_SPEED derivation (escapeair_force 3.1u)
    assert u(3.5) == 19  # Nalio fireball radius (3.5u -> r19)
    assert u(2.34) == 13  # Nalio d-tilt id0 radius
    assert u(3.13) == 17  # Nalio d-tilt id1 radius
    assert u(3.91) == 21  # Nalio d-tilt id2 radius


def test_u_is_single_source_of_the_scale():
    # u() must derive from the named constant, not a re-hardcoded literal — so a
    # change to PX_PER_UNIT propagates. (Guards against u() silently pinning its own 5.4.)
    assert u(100) == round(100 * PX_PER_UNIT)


# --- vel(): velocity/accel unit -> px-per-frame (float), #785 ---------------------


def test_vel_keeps_a_two_decimal_float_not_int():
    # Unlike u(), velocities are float px/frame — vel() must NOT round to int.
    assert vel(1.2) == 6.48  # round(1.2 * 5.4, 2); NOT u()'s round-to-6
    assert isinstance(vel(1.2), float)
    assert vel(0.1) == 0.54  # small gravity-scale value keeps precision


def test_vel_reproduces_the_faithful_gnok_targets():
    # Gnok (#779/#794) is authored raw-first through vel(); these are the exact px
    # the rukaidata PM3.6 DK source values produce (the spec's ~6.5/~9.7/~-15 were
    # hand-rounded — vel() gives the real value). Able-to-fail: change PX_PER_UNIT.
    assert vel(1.2) == 6.48  # walk max vel 1.2
    assert vel(1.8) == 9.72  # dash/run term vel 1.8
    assert vel(0.1) == 0.54  # gravity 0.1
    assert vel(2.4) == 12.96  # term (fall) vel 2.4
    assert -vel(2.8) == -15.12  # jump y init vel 2.8 (negated: pycats jumps are -y)


def test_vel_is_single_source_of_the_scale():
    # vel() must derive from the named constant, not a re-hardcoded 5.4.
    assert vel(3.3) == round(3.3 * PX_PER_UNIT, 2)
