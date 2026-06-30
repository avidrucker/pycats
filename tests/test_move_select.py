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
          attack=pg.K_v, special=pg.K_c, shield=pg.K_x)


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
