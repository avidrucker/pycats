"""
tests/test_magic_number_extraction_1135.py

Tier-1 combat/physics magic-number extraction (#1135, child of the #1134 tracker;
audit doc docs/research/2026-08-02-magic-number-audit-findings.md).

These assertions are ABLE-TO-FAIL against pre-#1135 main: the knockback coefficients
were bare inline literals with no registry rows; DOUBLE_TAP_WINDOW /
LEDGE_REGRAB_INTANGIBLE_CUTOFF were config registry-orphans; VEL_DEADZONE /
min_overlap lived in core/physics.py (invisible to the config-scoped drift-guard);
and GETUP_ATTACK / the default-cat jab carried no #1133 value-status. Reverting any
part of #1135 reds the relevant assertion here.

The registry↔config lock-step itself is guarded by test_tuning_provenance.py; this
module pins the *intent* of #1135 — which values got registered, with which status,
and that the knockback formula still computes bit-for-bit after the extraction.
"""

from pycats.combat.data import (
    GETUP_ATTACK,
    FieldStatus,
    Status,
    load_fighter_data,
)
from pycats.combat.knockback import knockback
from pycats.combat.provenance import TUNING_PROVENANCE
from pycats.core.physics import (
    DODGE_MIN_PLATFORM_OVERLAP_PX,
    PLATFORM_STAND_TOLERANCE_PX,
    VEL_DEADZONE,
)

_KB_COEFFS = (
    "KB_PERCENT_DIVISOR",
    "KB_PERCENT_DAMAGE_DIVISOR",
    "KB_WEIGHT_NUMERATOR",
    "KB_WEIGHT_OFFSET",
    "KB_GROWTH_SCALE",
    "KB_GROWTH_BASE",
    "KB_KBG_DIVISOR",
)


# --- Extraction is behaviour-preserving: the KB formula still computes exactly ---


def test_knockback_formula_unchanged_after_coefficient_extraction():
    # Hand-computed from KB = (((((p/10)+(p*d/20))*(200/(w+100))*1.4)+18)*(KBG/100))+BKB.
    # A swapped/typo'd extracted coefficient moves one of these.
    assert knockback(50.0, 10.0, 100, 30.0, 100.0) == 90.0  # (5+25)*1*1.4+18 = 60; *1+30
    assert knockback(0.0, 10.0, 100, 30.0, 100.0) == 48.0  # growth 0 → 18; *1+30
    assert knockback(50.0, 10.0, 100, 0.0, 100.0) == 60.0  # isolates growth (BKB=0)
    assert knockback(50.0, 10.0, 300, 0.0, 100.0) == 39.0  # weight term: (30*0.5)*1.4+18


# --- The extracted knockback coefficients are all registered FOUND ---------------


def test_knockback_coefficients_registered_found():
    for name in _KB_COEFFS:
        assert name in TUNING_PROVENANCE, f"{name} missing a provenance row"
        assert TUNING_PROVENANCE[name].status == "FOUND", name


# --- The three former registry-orphans are now registered with the right status --


def test_former_orphans_now_registered():
    assert TUNING_PROVENANCE["DOUBLE_TAP_WINDOW"].status == "GUESS"
    # LEDGE_REGRAB_INTANGIBLE_CUTOFF's basis is a PMDT 3.5 primary quote → FOUND.
    assert TUNING_PROVENANCE["LEDGE_REGRAB_INTANGIBLE_CUTOFF"].status == "FOUND"
    # VEL_DEADZONE + the dodge margin relocated from core/physics.py → config; TUNED.
    assert TUNING_PROVENANCE["VEL_DEADZONE"].status == "TUNED"
    assert TUNING_PROVENANCE["DODGE_MIN_PLATFORM_OVERLAP_PX"].status == "TUNED"


# --- The relocated core values keep their numbers; the slop stays a carve-out -----


def test_core_physics_values_relocated_and_carve_out_named():
    assert VEL_DEADZONE == 0.05
    assert DODGE_MIN_PLATFORM_OVERLAP_PX == 25
    # bottom_tolerance → a named constant, but deliberately NOT registered (it is
    # float-comparison slop, not a tuning value — #1135 carve-out).
    assert PLATFORM_STAND_TOLERANCE_PX == 2
    assert "PLATFORM_STAND_TOLERANCE_PX" not in TUNING_PROVENANCE


# --- GETUP_ATTACK gained a GUESS home via the #1133 per-value status seam ---------


def test_getup_attack_values_tagged_guess():
    guess = FieldStatus(Status.GUESS)
    assert GETUP_ATTACK.status["startup"] == guess
    assert GETUP_ATTACK.status["active"] == guess
    assert GETUP_ATTACK.status["recovery"] == guess
    box = GETUP_ATTACK.hitboxes[0]
    assert box.status["base_knockback"] == guess
    assert box.status["knockback_growth"] == guess
    assert box.status["damage"] == guess
    assert box.status["angle"] == guess
    assert box.circle.status["r"] == guess


# --- The default-cat jab's BKB/KBG are tagged GUESS, carried into the shipped JSON -


def test_default_cat_jab_knockback_tagged_guess_through_json():
    # load_fighter_data("default") hydrates default.json (the JSON branch), so this
    # proves the status survived the regenerated file, not just the Python oracle.
    jab = load_fighter_data("default").moves["attack"].hitboxes[0]
    assert jab.status["base_knockback"] == FieldStatus(Status.GUESS)
    assert jab.status["knockback_growth"] == FieldStatus(Status.GUESS)
    # damage/angle are documented-continuity values → left unannotated (per-value).
    assert "damage" not in jab.status
