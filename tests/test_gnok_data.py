"""Gnok (Donkey-Kong-archetype) stats + seam + measured body — slice 1 of #779 (spec #794).

Pure-data foundation: a distinct FighterData differing from the default cat in its
faithful PM3.6 velocity scalars (authored raw-first via the #785 `vel()` seam), its
*measured* big body geometry (spec §2), the load_fighter_data branch, and the selectable-
roster entry. No moves authored yet (Gnok's heavy normals are slices 2-7). Golden-free:
the sim/golden path loads the default cat via "P1"/"P2".
"""

from pycats.characters import roster
from pycats.combat.data import load_fighter_data
from pycats.combat.knockback import knockback
from pycats.combat.units import vel


def test_gnok_scalars_come_from_the_vel_seam_not_hand_typed_px():
    # The #785 raw-first authoring path: the faithful PM3.6 unit rates go through vel(),
    # so the source value stays visible and the ×PX_PER_UNIT factor lives in one place.
    # A hand-typed px literal that drifts from the converter fails here.
    gnok = load_fighter_data("gnok")
    assert gnok.move_speed == vel(1.2)  # 6.48 — fastest-walking cat
    assert gnok.dash_speed == vel(1.8)  # 9.72 — fastest-dashing cat
    assert gnok.jump_vel == -vel(2.8)  # -15.12 — jumps highest
    assert gnok.gravity == vel(0.1)  # 0.54
    assert gnok.max_fall_speed == vel(2.4)  # 12.96


def test_gnok_is_the_fastest_and_highest_jumping_cat():
    # The archetype is heavy AND mobile (spec §1/§3) — not the generic slow-heavy trope.
    gnok = load_fighter_data("gnok")
    default = load_fighter_data("default")
    assert gnok.move_speed > default.move_speed
    assert gnok.dash_speed > default.dash_speed
    assert gnok.jump_vel < default.jump_vel  # more negative = higher jump


def test_gnok_weight_is_heaviest_and_takes_less_knockback():
    # weight 114 → dies latest. Wire it through the REAL knockback formula (weight is the
    # only defender term): under an identical hit, Gnok travels less than the weight-100
    # default. Able-to-fail: a wrong/unwired weight flips or collapses this inequality.
    gnok = load_fighter_data("gnok")
    default = load_fighter_data("default")
    assert gnok.weight == 114
    assert gnok.weight > default.weight == 100
    hit = dict(percent=50.0, damage=12.0, base_knockback=30.0, knockback_growth=100.0)
    kb_gnok = knockback(weight=gnok.weight, **hit)
    kb_default = knockback(weight=default.weight, **hit)
    assert kb_gnok < kb_default  # heavier → launched less → dies later


def test_gnok_body_is_the_measured_big_box():
    # spec §2: measured from PM3.6 idle/duck hurtbox extents, not eyeballed.
    gnok = load_fighter_data("gnok")
    assert gnok.stand_size == (76, 80)  # DK ÷ Mario ×1.92 W ×1.32 H on the 40×60 default
    assert gnok.crouch_size == (80, 58)  # −27% H, +5% W squash — first cat wider crouching
    # 4-circle stand hurtbox fill (owner's choice, spec §2b)
    assert len(gnok.hurtbox.circles) == 4


def test_gnok_crouch_is_wider_than_its_stand():
    # The notable measured property (spec §2c): DK spreads when ducking — every other cat
    # holds stand width. The engine takes any (w, h).
    gnok = load_fighter_data("gnok")
    assert gnok.crouch_size[0] > gnok.stand_size[0]


def test_gnok_differs_from_default_on_scalars_and_body():
    # revert-check: a missing branch or a copy-of-default body/scalars fails here.
    gnok = load_fighter_data("gnok")
    default = load_fighter_data("default")
    assert gnok.stand_size != default.stand_size  # default has None (global PLAYER_SIZE)
    assert gnok.weight != default.weight
    assert gnok.move_speed != default.move_speed
    assert gnok.hurtbox != default.hurtbox


def test_gnok_reuses_default_moves_this_slice():
    # No moves authored in slice 1 (like narz slice 1): the kit is the default cat's until
    # slices 2-7 (#779) add Gnok's heavy normals/smashes.
    gnok = load_fighter_data("gnok")
    default = load_fighter_data("default")
    assert gnok.moves == default.moves


def test_gnok_is_in_the_selectable_roster():
    # char-select / watch.py read ARCHETYPE_ROSTER + ARCHETYPE_NAME (indexed directly);
    # registry.py indexes all four roster dicts, so a missing entry would KeyError there.
    assert "gnok" in roster.ARCHETYPE_ROSTER
    assert roster.ARCHETYPE_NAME["gnok"] == "Gnok"
    assert roster.ARCHETYPE_DEFAULT_SKIN["gnok"] == "brown-tan"  # Gnok's DK-brown base theme (#779)
    assert roster.ARCHETYPE_EXTRA_SKINS["gnok"] == ("brown-tan",)  # Gnok owns it (not a shared skin)
    assert roster.palette_for("gnok") is not None  # never raises; real palette set
