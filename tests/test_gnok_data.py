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
from pycats.combat.units import u, vel


def test_gnok_speeds_derive_from_datamine_units():
    # #1209 (ADR-0011): walk/dash/run are raw PM units in gnok.json; the shipped px
    # derives via the INTEGER u() (constant speeds truncate each frame, #80). Jump /
    # gravity / fall keep the float vel() seam (accelerating velocities accumulate, so
    # sub-pixel precision matters). A hand-typed px literal that drifts fails here.
    gnok = load_fighter_data("gnok")
    assert (gnok.walk, gnok.dash, gnok.run) == (1.2, 1.8, 1.8)
    assert gnok.move_speed == u(1.2) == 6
    assert gnok.dash_speed == u(1.8) == 10  # fastest-dashing cat
    assert gnok.run_speed == u(1.8) == 10
    assert gnok.jump_vel == -vel(2.8)  # -15.12 — jumps highest (float vel, unchanged)
    assert gnok.gravity == vel(0.1)  # 0.54
    assert gnok.max_fall_speed == vel(2.4)  # 12.96


def test_gnok_is_the_fastest_dashing_and_highest_jumping_cat():
    # The archetype is heavy AND mobile (spec §1/§3) — not the generic slow-heavy trope.
    # Its walk UNIT (1.2) tops the default's (1.1), but the integer u() rounds both to 6
    # px (#1209), so the mobility edge shows in the dash/run/jump, not the walk pixel.
    gnok = load_fighter_data("gnok")
    default = load_fighter_data("default")
    assert gnok.walk > default.walk  # 1.2u > 1.1u (unit-level)
    assert gnok.move_speed == default.move_speed == 6  # both round to 6 px
    assert gnok.dash_speed > default.dash_speed  # 10 > 8
    assert gnok.run_speed > default.run_speed  # 10 > 8
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
    assert gnok.dash_speed != default.dash_speed  # 10 vs 8 (walk px ties at 6 post-#1209)
    assert gnok.hurtbox != default.hurtbox


# The moves Gnok has authored so far (grows one slice at a time under #779): slice 2 the
# jab, slice 3 (#841) the three tilts, slices 5-6 (#914) the aerials (one per commit).
# Every OTHER slot still reuses the default cat.
_GNOK_AUTHORED = {"jab", "ftilt", "utilt", "dtilt", "nair", "fair", "bair", "uair", "dair"}


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


def test_gnok_utilt_is_authored_from_attackhi3():
    # Slice 3 (#841) u-tilt: DK's AttackHi3 — 3 boxes, angle 100, BKB 40; escalating
    # damage 9/10/11 + KBG 105/110/115 (id2 the sweetspot); startup 5 / active 6 /
    # recovery 25 (rukaidata FAF 36, active 6-11). Able-to-fail: a missing/mis-datamined
    # utilt (or flat damage/kbg instead of the escalation) fails here.
    utilt = load_fighter_data("gnok").moves["utilt"]
    assert (utilt.startup, utilt.active, utilt.recovery) == (5, 6, 25)
    assert len(utilt.hitboxes) == 3
    assert all(hb.angle == 100 and hb.base_knockback == 40.0 for hb in utilt.hitboxes)
    assert [hb.damage for hb in utilt.hitboxes] == [9.0, 10.0, 11.0]
    assert [hb.knockback_growth for hb in utilt.hitboxes] == [105.0, 110.0, 115.0]


def test_gnok_utilt_maps_to_up_a():
    # The "utilt" key is what move-select picks for grounded up-A, so authoring it there
    # means it fires in-game, not an orphaned move.
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    key = resolve_move_key(gnok.moves, direction="up", on_ground=True, is_special=False)
    assert key == "utilt"


def test_gnok_dtilt_is_authored_from_attacklw3():
    # Slice 3 (#841) d-tilt: DK's AttackLw3 — 4 same-set boxes, damage 9, angle 40 (a low
    # diagonal), BKB 25, KBG 95; startup 5 / active 4 / recovery 14 (rukaidata FAF 23,
    # active 6-9). Able-to-fail: a missing/mis-datamined dtilt fails here.
    dtilt = load_fighter_data("gnok").moves["dtilt"]
    assert (dtilt.startup, dtilt.active, dtilt.recovery) == (5, 4, 14)
    assert len(dtilt.hitboxes) == 4
    assert all(hb.damage == 9.0 and hb.angle == 40 for hb in dtilt.hitboxes)
    assert all(hb.base_knockback == 25.0 and hb.knockback_growth == 95.0 for hb in dtilt.hitboxes)


def test_gnok_dtilt_maps_to_down_a():
    # The "dtilt" key is what move-select picks for grounded down-A, so authoring it there
    # means it fires in-game, not an orphaned move.
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    key = resolve_move_key(gnok.moves, direction="down", on_ground=True, is_special=False)
    assert key == "dtilt"


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


def test_gnok_nair_is_a_sex_kick_early_strong_late_weak():
    # Slices 5-6 (#914) n-air: DK's AttackAirN — a "sex kick" with two temporal windows
    # (#204). EARLY [7,10] is the strong hit (dmg 14, angle 361 Sakurai, BKB 20); LATE
    # [11,24] is the long weak lingering hit (dmg 10, angle 50, BKB 10). startup 6 / active
    # 18 / recovery 12 (datamine FAF 36, active frames 7-24). Able-to-fail: a single-window
    # nair, or early/late not decaying, collapses this.
    nair = load_fighter_data("gnok").moves["nair"]
    assert (nair.startup, nair.active, nair.recovery) == (6, 18, 12)
    windows = sorted({(hb.active_start, hb.active_end) for hb in nair.hitboxes})
    assert windows == [(7, 10), (11, 24)], "n-air must fire an early then a late window"
    early = [hb for hb in nair.hitboxes if hb.active_start == 7]
    late = [hb for hb in nair.hitboxes if hb.active_start == 11]
    assert early and late
    assert all(hb.damage == 14.0 and hb.angle == 361 and hb.base_knockback == 20.0 for hb in early)
    assert all(hb.damage == 10.0 and hb.angle == 50 and hb.base_knockback == 10.0 for hb in late)
    assert max(hb.damage for hb in early) > max(hb.damage for hb in late)  # sex-kick decay


def test_gnok_nair_maps_to_air_neutral_a():
    # The "nair" key is what move-select picks for airborne neutral-A, so authoring it under
    # that key means it fires in-game. Able-to-fail: without a "nair" move the seam falls
    # back to the "attack" alias.
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    key = resolve_move_key(gnok.moves, direction="neutral", on_ground=False, is_special=False)
    assert key == "nair"


def test_gnok_fair_is_a_two_window_downward_smash():
    # Slices 5-6 (#914) f-air: DK's AttackAirF — a two-hand overhead smash with an EARLY
    # link window and a LATE spike window (#204). startup 22 / active 5 / recovery 21
    # (datamine FAF 48, active frames 23-27). EARLY [23,25]: angle 361, BKB 20, KBG 100.
    # LATE [26,27]: the spike box swings to angle 290 (down-forward) with BKB 50 / KBG 73.
    # All boxes damage 17. Able-to-fail: a single-window fair, or a missing late spike, fails.
    fair = load_fighter_data("gnok").moves["fair"]
    assert (fair.startup, fair.active, fair.recovery) == (22, 5, 21)
    windows = sorted({(hb.active_start, hb.active_end) for hb in fair.hitboxes})
    assert windows == [(23, 25), (26, 27)]
    early = [hb for hb in fair.hitboxes if hb.active_start == 23]
    late = [hb for hb in fair.hitboxes if hb.active_start == 26]
    assert early and late
    assert all(hb.damage == 17.0 for hb in fair.hitboxes)
    assert all(hb.angle == 361 and hb.base_knockback == 20.0 and hb.knockback_growth == 100.0 for hb in early)
    # the late window is the finisher: higher BKB, and its big box spikes at angle 290
    assert all(hb.base_knockback == 50.0 and hb.knockback_growth == 73.0 for hb in late)
    assert any(hb.angle == 290 for hb in late), "the late window must carry the down-forward spike"


def test_gnok_fair_maps_to_air_forward_a():
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    key = resolve_move_key(gnok.moves, direction="forward", on_ground=False, is_special=False)
    assert key == "fair"


def test_gnok_bair_is_a_sakurai_sex_kick():
    # Slices 5-6 (#914) b-air: DK's AttackAirB — a Sakurai-angle (361) sex kick, both
    # windows launching at 361 but decaying in damage/knockback. startup 6 / active 14 /
    # recovery 11 (datamine FAF 31, active frames 7-20). CLEAN [7,8]: dmg 13, BKB 20; LATE
    # [9,20]: dmg 9, BKB 10. Able-to-fail: a single-window bair or no decay collapses this.
    bair = load_fighter_data("gnok").moves["bair"]
    assert (bair.startup, bair.active, bair.recovery) == (6, 14, 11)
    windows = sorted({(hb.active_start, hb.active_end) for hb in bair.hitboxes})
    assert windows == [(7, 8), (9, 20)]
    clean = [hb for hb in bair.hitboxes if hb.active_start == 7]
    late = [hb for hb in bair.hitboxes if hb.active_start == 9]
    assert clean and late
    assert all(hb.angle == 361 and hb.knockback_growth == 100.0 for hb in bair.hitboxes)
    assert all(hb.damage == 13.0 and hb.base_knockback == 20.0 for hb in clean)
    assert all(hb.damage == 9.0 and hb.base_knockback == 10.0 for hb in late)


def test_gnok_bair_maps_to_air_back_a():
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    key = resolve_move_key(gnok.moves, direction="back", on_ground=False, is_special=False)
    assert key == "bair"


def test_gnok_uair_is_a_single_upward_headbutt():
    # Slices 5-6 (#914) u-air: DK's AttackAirHi — a single-window straight-up juggle hit (no
    # early/late decay). startup 5 / active 4 / recovery 28 (datamine FAF 37, active frames
    # 6-9). One box: damage 14, angle 90 (straight up), BKB 32, KBG 90. Able-to-fail: a
    # missing/mis-datamined uair, or a spurious second window, fails here.
    uair = load_fighter_data("gnok").moves["uair"]
    assert (uair.startup, uair.active, uair.recovery) == (5, 4, 28)
    assert len(uair.hitboxes) == 1
    hb = uair.hitboxes[0]
    assert hb.damage == 14.0 and hb.angle == 90
    assert hb.base_knockback == 32.0 and hb.knockback_growth == 90.0
    assert hb.active_start is None  # single window spans the whole active period


def test_gnok_uair_maps_to_air_up_a():
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    key = resolve_move_key(gnok.moves, direction="up", on_ground=False, is_special=False)
    assert key == "uair"


def test_gnok_dair_is_the_downward_spike():
    # Slices 5-6 (#914) d-air: DK's AttackAirLw — the SPIKE. A single window whose boxes all
    # launch straight down (angle 270); the sweetspot box (dmg 16, BKB 38) meteors, the two
    # sour boxes (dmg 13, BKB 20) are weaker. startup 17 / active 6 / recovery 19 (datamine
    # FAF 42, active frames 18-23). Able-to-fail: a non-270 (non-spike) dair, or a missing
    # sweetspot, fails here.
    dair = load_fighter_data("gnok").moves["dair"]
    assert (dair.startup, dair.active, dair.recovery) == (17, 6, 19)
    assert len(dair.hitboxes) == 3
    assert all(hb.angle == 270 and hb.knockback_growth == 90.0 for hb in dair.hitboxes)  # straight down = spike
    sweet = [hb for hb in dair.hitboxes if hb.damage == 16.0]
    sour = [hb for hb in dair.hitboxes if hb.damage == 13.0]
    assert len(sweet) == 1 and len(sour) == 2
    assert sweet[0].base_knockback == 38.0  # the meteor sweetspot
    assert all(hb.base_knockback == 20.0 for hb in sour)


def test_gnok_dair_maps_to_air_down_a():
    from pycats.combat.move_select import resolve_move_key

    gnok = load_fighter_data("gnok")
    key = resolve_move_key(gnok.moves, direction="down", on_ground=False, is_special=False)
    assert key == "dair"
