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


# The moves Gnok has authored so far (grows one slice at a time under #779): slice 2 the
# jab, slice 3 (#841) the three tilts. Every OTHER slot still reuses the default cat.
_GNOK_AUTHORED = {"jab", "ftilt", "utilt", "dtilt"}


def test_gnok_authored_moves_are_its_own_the_rest_reuse_default():
    # Slices 2-3 author the jab + tilts; every OTHER slot still reuses the default cat until
    # its slice (#779) lands. Able-to-fail: a wrong wiring that drops an authored move or
    # clobbers a default slot fails here.
    gnok = load_fighter_data("gnok")
    default = load_fighter_data("default")
    assert "jab" in gnok.moves and "ftilt" in gnok.moves
    # each authored move is Gnok's own, not the default's
    for key in _GNOK_AUTHORED & set(default.moves):
        assert gnok.moves[key] is not default.moves[key]
    # the untouched slots (e.g. the default "attack" fallback) are still the default's
    for key, mv in default.moves.items():
        if key in _GNOK_AUTHORED:
            continue
        assert gnok.moves[key] == mv


def test_gnok_ftilt_is_authored_from_attacks3s():
    # Slice 3 (#841) f-tilt: DK's AttackS3S — 4 same-set boxes, damage 11, angle 361
    # (Sakurai sentinel), BKB 10, KBG 100; frames startup 7 / active 4 / recovery 23
    # (rukaidata FAF 34, active 8-11). Able-to-fail: a missing/mis-datamined ftilt fails.
    ftilt = load_fighter_data("gnok").moves["ftilt"]
    assert (ftilt.startup, ftilt.active, ftilt.recovery) == (7, 4, 23)
    assert len(ftilt.hitboxes) == 4
    assert all(hb.damage == 11.0 and hb.angle == 361 for hb in ftilt.hitboxes)
    assert all(hb.base_knockback == 10.0 and hb.knockback_growth == 100.0 for hb in ftilt.hitboxes)


def test_gnok_ftilt_maps_to_forward_a():
    # The "ftilt" key is what move-select picks for grounded forward-A (and back-A), so
    # authoring it under that key means it fires in-game, not an orphaned move.
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    for direction in ("forward", "back"):
        key = resolve_move_key(gnok.moves, direction=direction, on_ground=True, is_special=False)
        assert key == "ftilt"


def test_gnok_jab_is_a_two_hit_1_2():
    # DK's Attack11 → Attack12, modeled as one move with two SEQUENTIAL windows (#204).
    # Able-to-fail: a single-window jab (or overlapping windows) collapses this.
    jab = load_fighter_data("gnok").moves["jab"]
    windows = sorted({(hb.active_start, hb.active_end) for hb in jab.hitboxes})
    assert len(windows) == 2, "jab must fire in two distinct windows (1 then 2)"
    (s1, e1), (s2, e2) = windows
    assert e1 < s2, "the second hit must start strictly after the first ends"


def test_gnok_jab1_links_and_jab2_launches():
    # Faithful to the datamine: hit 1 is a weight-SET link (WDSK 20, low dmg/angle), hit 2
    # is the real-BKB up-forward launcher (higher dmg, steeper angle, no set-knockback).
    # Able-to-fail: swapping the link/launch roles or dropping the set-knockback fails here.
    jab = load_fighter_data("gnok").moves["jab"]
    hit1 = [hb for hb in jab.hitboxes if hb.active_start == 3]
    hit2 = [hb for hb in jab.hitboxes if hb.active_start == 10]
    assert hit1 and hit2
    # hit 1: the set-knockback LINK — Attack11 damage 4, angle 65
    assert all(hb.set_knockback == 20 for hb in hit1)
    assert all(hb.damage == 4.0 and hb.angle == 65 for hb in hit1)
    # hit 2: the real-knockback LAUNCHER — Attack12 damage 6, angle 75, bkb 40, no WDSK
    assert all(hb.set_knockback is None for hb in hit2)
    assert all(hb.damage == 6.0 and hb.angle == 75 and hb.base_knockback == 40.0 for hb in hit2)


def test_gnok_jab_maps_to_neutral_a():
    # The "jab" key is what the move-select seam picks for grounded neutral-A, so authoring
    # it under that key means it actually fires in-game (not an orphaned move).
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    key = resolve_move_key(gnok.moves, direction="neutral", on_ground=True, is_special=False)
    assert key == "jab"


def test_gnok_is_in_the_selectable_roster():
    # char-select / watch.py read ARCHETYPE_ROSTER + ARCHETYPE_NAME (indexed directly);
    # registry.py indexes all four roster dicts, so a missing entry would KeyError there.
    assert "gnok" in roster.ARCHETYPE_ROSTER
    assert roster.ARCHETYPE_NAME["gnok"] == "Gnok"
    assert roster.ARCHETYPE_DEFAULT_SKIN["gnok"] == "brown-tan"  # Gnok's DK-brown base theme (#779)
    assert roster.ARCHETYPE_EXTRA_SKINS["gnok"] == ("brown-tan",)  # Gnok owns it (not a shared skin)
    assert roster.palette_for("gnok") is not None  # never raises; real palette set
