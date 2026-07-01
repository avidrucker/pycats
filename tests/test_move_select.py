"""tests/test_move_select.py

Move-selection seam (#143, Phase 2 epic #142).

A small table maps (direction × ground/air × A-vs-B) -> a canonical move key;
resolution then falls back to what the character actually defines so partial kits
(default cat = {"attack"}; Nalio = {"attack","jab","nair"}) behave incrementally.
"""
import pygame as pg

from pycats.combat.move_select import select_move_key, resolve_move_key
from pycats.combat.data import Circle, Hitbox, MoveData, FighterData, Hurtbox
from pycats.entities.player import Player
from pycats.core.input import InputFrame

P1 = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s,
          attack=pg.K_v, special=pg.K_c, shield=pg.K_x, smash=pg.K_b)


# ---- pure: canonical key per context --------------------------------------

def test_select_ground_normals():
    assert select_move_key("neutral", on_ground=True, is_special=False) == "jab"
    assert select_move_key("down", on_ground=True, is_special=False) == "dtilt"
    assert select_move_key("up", on_ground=True, is_special=False) == "utilt"
    assert select_move_key("forward", on_ground=True, is_special=False) == "ftilt"
    assert select_move_key("back", on_ground=True, is_special=False) == "ftilt"


def test_select_aerials():
    assert select_move_key("neutral", on_ground=False, is_special=False) == "nair"
    assert select_move_key("forward", on_ground=False, is_special=False) == "fair"
    assert select_move_key("back", on_ground=False, is_special=False) == "bair"
    assert select_move_key("up", on_ground=False, is_special=False) == "uair"
    assert select_move_key("down", on_ground=False, is_special=False) == "dair"


def test_select_specials():
    assert select_move_key("neutral", on_ground=True, is_special=True) == "neutral_b"
    assert select_move_key("forward", on_ground=True, is_special=True) == "side_b"
    assert select_move_key("back", on_ground=False, is_special=True) == "side_b"
    assert select_move_key("up", on_ground=False, is_special=True) == "up_b"
    assert select_move_key("down", on_ground=True, is_special=True) == "down_b"


# ---- pure: resolution with fallback ---------------------------------------

def test_resolve_prefers_exact_then_falls_back():
    full = {"jab", "dtilt", "utilt", "ftilt", "nair", "fair", "neutral_b"}
    assert resolve_move_key(full, "down", True, False) == "dtilt"
    assert resolve_move_key(full, "forward", False, False) == "fair"
    assert resolve_move_key(full, "neutral", True, True) == "neutral_b"


def test_resolve_ground_falls_back_to_attack_alias():
    avail = {"attack", "nair"}  # Nalio today
    assert resolve_move_key(avail, "down", True, False) == "attack"   # no dtilt key -> attack
    assert resolve_move_key(avail, "up", True, False) == "attack"
    assert resolve_move_key(avail, "neutral", True, False) == "attack"


def test_resolve_air_falls_back_to_nair_then_attack():
    assert resolve_move_key({"attack", "nair"}, "down", False, False) == "nair"
    assert resolve_move_key({"attack"}, "neutral", False, False) == "attack"  # no nair


def test_resolve_special_is_noop_when_absent():
    assert resolve_move_key({"attack", "nair"}, "neutral", True, True) is None


# ---- behaviour through the Player -----------------------------------------

def _mk(char="P1", fighter_data=None):
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name=char, facing_right=True, fighter_data=fighter_data)


def _press(*names, held_extra=()):
    keys = {P1[n] for n in names}
    return InputFrame(held=keys | {P1[h] for h in held_extra},
                      pressed=keys, released=set())


def test_default_cat_neutral_attack_unchanged():
    pg.init()
    p = _mk("P1"); p.fighter.on_ground = True
    p.handle_actions(_press("attack"), pg.sprite.Group())
    assert p.current_move is p.fighter_data.moves["attack"]


def test_nalio_neutral_attack_uses_jab_and_down_attack_uses_dtilt_alias():
    pg.init()
    p = _mk("nalio")
    p.fighter.on_ground = True
    p.handle_actions(_press("attack"), pg.sprite.Group())
    assert p.current_move is p.fighter_data.moves["jab"]

    p = _mk("nalio")
    p.fighter.on_ground = True
    p.handle_actions(_press("attack", held_extra=("down",)), pg.sprite.Group())
    assert p.current_move is p.fighter_data.moves["attack"]


def test_nalio_forward_ground_uses_ftilt_not_the_attack_alias():
    """Now that Nalio defines a real f-tilt (#206), forward-on-the-ground + A
    selects "ftilt" instead of falling back to the "attack" alias (d-tilt)."""
    pg.init()
    p = _mk("nalio")  # faces right, so held "right" == "forward"
    p.fighter.on_ground = True
    p.handle_actions(_press("attack", held_extra=("right",)), pg.sprite.Group())
    assert "ftilt" in p.fighter_data.moves
    assert p.current_move is p.fighter_data.moves["ftilt"]
    assert p.current_move is not p.fighter_data.moves["attack"]


def test_nalio_up_ground_uses_utilt_not_the_attack_alias():
    """Now that Nalio defines a real u-tilt (#207), up-on-the-ground + A selects
    "utilt" instead of the "attack" alias (d-tilt). 'up' is held (not pressed) so
    it sets direction without triggering a jump."""
    pg.init()
    p = _mk("nalio")
    p.fighter.on_ground = True
    p.handle_actions(_press("attack", held_extra=("up",)), pg.sprite.Group())
    assert "utilt" in p.fighter_data.moves
    assert p.current_move is p.fighter_data.moves["utilt"]
    assert p.current_move is not p.fighter_data.moves["attack"]


def test_nalio_airborne_forward_uses_fair_not_nair():
    """Now that Nalio defines a real f-air (#208), airborne forward + A selects
    "fair" instead of falling back to nair."""
    pg.init()
    p = _mk("nalio")  # faces right, so held "right" == "forward"
    p.fighter.on_ground = False
    p.handle_actions(_press("attack", held_extra=("right",)), pg.sprite.Group())
    assert "fair" in p.fighter_data.moves
    assert p.current_move is p.fighter_data.moves["fair"]
    assert p.current_move is not p.fighter_data.moves["nair"]


def test_nalio_airborne_back_uses_bair_not_nair():
    """Now that Nalio defines a real b-air (#209), airborne back + A selects
    "bair" instead of falling back to nair. Faces right, so held "left" == back."""
    pg.init()
    p = _mk("nalio")
    p.fighter.on_ground = False
    p.handle_actions(_press("attack", held_extra=("left",)), pg.sprite.Group())
    assert "bair" in p.fighter_data.moves
    assert p.current_move is p.fighter_data.moves["bair"]
    assert p.current_move is not p.fighter_data.moves["nair"]


def test_nalio_airborne_up_uses_uair_not_nair():
    """Now that Nalio defines a real u-air (#210), airborne up + A selects "uair"
    instead of nair. 'up' is held (not pressed) so it sets direction, no jump."""
    pg.init()
    p = _mk("nalio")
    p.fighter.on_ground = False
    p.handle_actions(_press("attack", held_extra=("up",)), pg.sprite.Group())
    assert "uair" in p.fighter_data.moves
    assert p.current_move is p.fighter_data.moves["uair"]
    assert p.current_move is not p.fighter_data.moves["nair"]


def test_nalio_airborne_down_uses_dair_not_nair():
    """Now that Nalio defines a real d-air (#214), airborne down + A selects
    "dair" instead of falling back to nair."""
    pg.init()
    p = _mk("nalio")
    p.fighter.on_ground = False
    p.handle_actions(_press("attack", held_extra=("down",)), pg.sprite.Group())
    assert "dair" in p.fighter_data.moves
    assert p.current_move is p.fighter_data.moves["dair"]
    assert p.current_move is not p.fighter_data.moves["nair"]


def test_b_button_starts_a_defined_special():
    pg.init()
    sb = MoveData(name="neutral b", in_air=False, startup=3, active=2, recovery=5,
                  hitboxes=(Hitbox(circle=Circle(20, 30, 12), damage=7, angle=0),))
    fd = FighterData(hurtbox=Hurtbox(circles=(Circle(20, 30, 14),)),
                     moves={"attack": _mk().fighter_data.moves["attack"], "neutral_b": sb})
    p = _mk("custom", fighter_data=fd); p.fighter.on_ground = True
    p.handle_actions(_press("special"), pg.sprite.Group())
    assert p.current_move is sb, "B should start the character's neutral_b"


def test_b_button_noop_when_no_special_defined():
    pg.init()
    p = _mk("P1"); p.fighter.on_ground = True
    p.handle_actions(_press("special"), pg.sprite.Group())
    assert p.current_move is None, "B with no special move is a no-op"


# ---- smash input + routing (#331, slice 1 of #327) ------------------------

def test_select_smash_keys():
    s = lambda d: select_move_key(d, on_ground=True, is_special=False, is_smash=True)
    assert s("forward") == "fsmash"
    assert s("back") == "fsmash"      # back-smash = turnaround f-smash
    assert s("neutral") == "fsmash"   # no neutral smash → treat as forward
    assert s("up") == "usmash"
    assert s("down") == "dsmash"


def test_resolve_smash_prefers_smash_then_tilt_then_attack():
    full = {"fsmash", "usmash", "dsmash", "ftilt", "utilt", "dtilt", "attack"}
    assert resolve_move_key(full, "forward", True, False, is_smash=True) == "fsmash"
    assert resolve_move_key(full, "up", True, False, is_smash=True) == "usmash"
    assert resolve_move_key(full, "down", True, False, is_smash=True) == "dsmash"
    # no smash keys → fall back to the matching TILT (graceful degradation)
    tilts = {"ftilt", "utilt", "dtilt", "attack"}
    assert resolve_move_key(tilts, "forward", True, False, is_smash=True) == "ftilt"
    assert resolve_move_key(tilts, "up", True, False, is_smash=True) == "utilt"
    assert resolve_move_key(tilts, "down", True, False, is_smash=True) == "dtilt"
    # no smash, no tilt → the "attack" alias
    assert resolve_move_key({"attack"}, "forward", True, False, is_smash=True) == "attack"


def test_smash_through_player_plays_real_smash_since_slice2():
    # Nalio now has real smashes (#327 slice 2) → smash-forward plays fsmash, not
    # the ftilt fallback the #331 seam used before the move data existed.
    pg.init()
    p = _mk("nalio"); p.fighter.on_ground = True
    p.handle_actions(_press("smash", held_extra=("right",)), pg.sprite.Group())
    assert p.current_move is p.fighter_data.moves["fsmash"]


def test_smash_in_air_alone_is_a_noop_this_slice():
    pg.init()
    p = _mk("nalio"); p.fighter.on_ground = False
    p.handle_actions(_press("smash", held_extra=("right",)), pg.sprite.Group())
    assert p.current_move is None, "smash is ground-only this slice; no air-smash"


def test_pressed_is_tolerant_of_a_missing_smash_binding():
    # sim keymaps omit "smash" — must not KeyError, just never smash (golden-safe)
    pg.init()
    no_smash = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s,
                    attack=pg.K_v, special=pg.K_c, shield=pg.K_x)  # no "smash"
    p = Player(100, 100, no_smash, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="nalio", facing_right=True)
    p.fighter.on_ground = True
    # a frame with K_b held (would be smash if bound) must not route a smash
    frame = InputFrame(held={pg.K_b, pg.K_d}, pressed={pg.K_b}, released=set())
    p.handle_actions(frame, pg.sprite.Group())
    assert p.current_move is None
