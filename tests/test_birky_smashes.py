"""Birky's smashes — fsmash/usmash/dsmash (#459, child of #228).

Birky (Kirby) smashes are short-range, single-box-per-window grounded smashes,
chargeable via the mechanic in #371/#377. Values are PM3.6-Kirby-shaped
(rukaidata AttackS4S / AttackHi4 / AttackLw4), ⚠ playtest.

Golden-safe: the sim path loads the default cat (no smash, not chargeable); a
test pins that.
"""
from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
from pycats.combat.charge import scale_hitboxes
from pycats.combat.data import load_fighter_data
from pycats.combat.move_select import resolve_move_key

_BIRKY = load_fighter_data("birky")


def test_smashes_exist_chargeable_and_grounded():
    for k in ("fsmash", "usmash", "dsmash"):
        m = _BIRKY.moves[k]
        assert m.in_air is False
        assert m.chargeable is True


def test_smashes_reachable_through_the_331_seam():
    keys = set(_BIRKY.moves)
    assert resolve_move_key(keys, "forward", True, False, is_smash=True) == "fsmash"
    assert resolve_move_key(keys, "up", True, False, is_smash=True) == "usmash"
    assert resolve_move_key(keys, "down", True, False, is_smash=True) == "dsmash"


def test_fsmash_early_hit_stronger_than_late():
    # rukaidata AttackS4S: early f8-14 (15 dmg / 40 BKB), late f15-17 (13 dmg / 25 BKB)
    m = _BIRKY.moves["fsmash"]
    early = min(m.hitboxes, key=lambda h: h.active_start)
    late = max(m.hitboxes, key=lambda h: h.active_start)
    assert early.active_start < late.active_start
    assert early.damage > late.damage
    assert early.base_knockback > late.base_knockback


def test_usmash_launches_up():
    # rukaidata AttackHi4: the strong hit launches up (angle near vertical)
    m = _BIRKY.moves["usmash"]
    strong = max(m.hitboxes, key=lambda h: h.damage)
    assert 45 < strong.angle < 135


def test_dsmash_hits_front_and_back_simultaneously():
    # Kirby's dsmash is a splits kick: front + back live TOGETHER (NOT Marth's
    # front-then-back temporal split). A front box and a back box share a window.
    m = _BIRKY.moves["dsmash"]
    front = [h for h in m.hitboxes if h.circle.dx > 0]
    back = [h for h in m.hitboxes if h.circle.dx < 0]
    assert front and back
    assert any(f.active_start == b.active_start for f in front for b in back)


def test_charged_smash_scales_damage_only():
    # #437: a full charge scales DAMAGE, never BKB/KBG (avoids the compounded over-scale).
    boxes = _BIRKY.moves["fsmash"].hitboxes
    scaled = scale_hitboxes(boxes, 1.0)
    assert scaled is not boxes
    for orig, sc in zip(boxes, scaled):
        assert sc.damage > orig.damage
        assert sc.base_knockback == orig.base_knockback
        assert sc.knockback_growth == orig.knockback_growth


def test_default_cat_has_no_chargeable_smash_golden_safety():
    for k in ("fsmash", "usmash", "dsmash"):
        assert k not in DEFAULT_FIGHTER_DATA.moves
    assert not any(mv.chargeable for mv in DEFAULT_FIGHTER_DATA.moves.values())
