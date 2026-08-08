"""Gnok's smashes — fsmash/usmash/dsmash (#947, slice 7/7 of epic #779, spec #794 §4).

DK's chargeable KO tools, datamined from the brawllib_rs PM3.6 dump (`-f Donkey -a
AttackS4S / AttackHi4 / AttackLw4`; env #614). Unlike Birky's early/late smashes, all three
are SINGLE active windows (no #204 sub-windows in the DK smash data), so no `set_id` — the
engine resolves overlapping same-window boxes to one hit per target per move. The angled
f-smash and the charge mechanic are both engine-side already (#383/#327, #371/#377): this
slice authors data only, no engine change.

Golden-safe: the sim/golden path loads the default ("P1"/"P2") cat, which has no chargeable
smash; a test pins that. Loaded by name through the JSON flip (#860), so these also prove the
on-disk gnok.json carries the smashes.
"""

from pycats.combat.charge import scale_hitboxes
from pycats.combat.data import load_fighter_data
from pycats.combat.move_select import resolve_move_key

_GNOK = load_fighter_data("gnok")
# The minimal one-move test fixture, loaded by name (#591) — the golden-safety stand-in.
_TESTCAT = load_fighter_data("testcat")


def test_smashes_exist_chargeable_and_grounded():
    # Able-to-fail: drop any smash from the moves dict (or its chargeable/in_air flag) → red.
    for k in ("fsmash", "usmash", "dsmash"):
        m = _GNOK.moves[k]
        assert m.in_air is False
        assert m.chargeable is True
        assert m.hitboxes  # authored, not an empty placeholder


def test_smashes_reachable_through_the_331_input_seam():
    # The player-reachability guarantee: up+smash → usmash, down+smash → dsmash,
    # forward/neutral/back+smash → fsmash, via combat/move_select._SMASH + resolve_move_key.
    # Able-to-fail: if a smash key were missing, resolve_move_key falls back to the tilt and
    # these equalities break.
    keys = set(_GNOK.moves)
    assert resolve_move_key(keys, "forward", True, False, is_smash=True) == "fsmash"
    assert resolve_move_key(keys, "neutral", True, False, is_smash=True) == "fsmash"
    assert resolve_move_key(keys, "back", True, False, is_smash=True) == "fsmash"
    assert resolve_move_key(keys, "up", True, False, is_smash=True) == "usmash"
    assert resolve_move_key(keys, "down", True, False, is_smash=True) == "dsmash"


def test_smashes_are_single_window_not_early_late():
    # DK's smash data has one active window each (no clean/late decay), unlike Birky's — so
    # the boxes carry no per-hitbox active_start/active_end. Able-to-fail: adding a sub-window
    # box (or the wrong template) trips this.
    for k in ("fsmash", "usmash", "dsmash"):
        for h in _GNOK.moves[k].hitboxes:
            assert h.active_start is None
            assert h.active_end is None
            assert h.set_id is None  # single window → no B-full set tag needed


def test_fsmash_is_a_sakurai_forward_clap_with_strong_fists():
    # AttackS4S: 4 boxes, all trajectory 361 (Sakurai); the two big fists (dmg 21/20, BKB 30)
    # outdamage + outlaunch the two inner link boxes (dmg 19/18, BKB 18).
    m = _GNOK.moves["fsmash"]
    assert m.startup == 7 and m.active == 2 and m.recovery == 31  # IASA 40
    assert len(m.hitboxes) == 4
    assert all(h.angle == 361 for h in m.hitboxes)
    fists = [h for h in m.hitboxes if h.base_knockback == 30.0]
    links = [h for h in m.hitboxes if h.base_knockback == 18.0]
    assert len(fists) == 2 and len(links) == 2
    assert min(h.damage for h in fists) > max(h.damage for h in links)
    # spec damage values pinned — a wrong datamine transcription fails here.
    assert sorted(h.damage for h in m.hitboxes) == [18.0, 19.0, 20.0, 21.0]


def test_usmash_launches_straight_up():
    # AttackHi4: an overhead clap, both boxes trajectory 90 (straight up); the big box is
    # stronger. Anti-air / juggle KO.
    m = _GNOK.moves["usmash"]
    assert m.startup == 7 and m.active == 3 and m.recovery == 31  # IASA 41
    assert len(m.hitboxes) == 2
    assert all(h.angle == 90 for h in m.hitboxes)
    strong = max(m.hitboxes, key=lambda h: h.circle.r)
    weak = min(m.hitboxes, key=lambda h: h.circle.r)
    assert strong.damage == 18.0 and weak.damage == 16.0


def test_dsmash_hits_front_and_back_in_one_window():
    # AttackLw4: DK's two-sided ground pound — front (dx>0) and back (dx<0) boxes live in the
    # SAME window (not Marth/narz's front-then-back temporal split). Both pop up (angle > 90).
    m = _GNOK.moves["dsmash"]
    assert m.startup == 7 and m.active == 4 and m.recovery == 41  # IASA 52
    front = [h for h in m.hitboxes if h.circle.dx > 0]
    back = [h for h in m.hitboxes if h.circle.dx < 0]
    assert len(front) == 2 and len(back) == 2
    assert all(h.angle > 90 for h in m.hitboxes)  # near-vertical up-pop (98 / 115)
    # front and back mirror each other (same damage per size tier)
    assert sorted(h.damage for h in front) == sorted(h.damage for h in back) == [16.0, 17.0]


def test_charged_smash_scales_damage_only():
    # #437: a full charge scales DAMAGE, never BKB/KBG (avoids the compounded over-scale).
    # Applies to Gnok's smashes because they are chargeable — able-to-fail if chargeable
    # were dropped (the input path would never build a charged hitbox set).
    boxes = _GNOK.moves["fsmash"].hitboxes
    scaled = scale_hitboxes(boxes, 1.0)
    assert scaled is not boxes
    for orig, sc in zip(boxes, scaled):
        assert sc.damage > orig.damage
        assert sc.base_knockback == orig.base_knockback
        assert sc.knockback_growth == orig.knockback_growth


def test_default_cat_has_no_chargeable_smash_golden_safety():
    # The sim/golden path never sees these: the stand-in cat has no chargeable smash.
    for k in ("fsmash", "usmash", "dsmash"):
        assert k not in _TESTCAT.moves
    assert not any(mv.chargeable for mv in _TESTCAT.moves.values())
