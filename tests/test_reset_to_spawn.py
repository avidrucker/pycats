"""Issue #34 — Player.reset_to_spawn() is the single authoritative per-life reset.

The key invariant the consolidation protects: facing is restored from
`original_facing_right`, NOT a hardcoded literal (reset_game used to hardcode
True/False per player, which is correct only by coincidence on the current
config and would drift the moment a player is constructed facing the other way).
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.config import P1_COLOR, WHITE

C = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
     "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _player(facing_right):
    return Player(x=460, y=360, controls=C, color=P1_COLOR, eye_color=WHITE,
                  char_name="Cat", facing_right=facing_right)


def test_reset_restores_original_facing_left():
    p = _player(facing_right=False)   # constructed facing LEFT
    p.fighter.facing_right = True             # turned around during play
    p.reset_to_spawn()
    assert p.fighter.facing_right is False    # back to original, not a literal


def test_reset_restores_original_facing_right():
    p = _player(facing_right=True)
    p.fighter.facing_right = False
    p.reset_to_spawn()
    assert p.fighter.facing_right is True


def test_reset_clears_transient_state_and_position():
    p = _player(facing_right=True)
    # dirty a spread of per-life state
    p.fighter.is_alive = False
    p.fighter.dodge_timer = p.fighter.hurt_timer = p.fighter.stun_timer = 9
    p._clock.start(p.fighter_data.moves["attack"])  # dirty the move clock -> attack_timer > 0
    p.fighter.invulnerable = True
    p.fighter.percent = 80
    p.fighter.vel.update(7, -7)
    p.rect.center = (9999, 9999)
    p.reset_to_spawn()
    assert p.fighter.is_alive
    assert (p.fighter.dodge_timer, p.fighter.hurt_timer, p.fighter.stun_timer, p.attack_timer) == (0, 0, 0, 0)
    assert p.fighter.invulnerable is False
    assert p.fighter.percent == 0
    assert (p.fighter.vel.x, p.fighter.vel.y) == (0, 0)
    assert p.rect.midbottom == (int(p.fighter.spawn_point.x), int(p.fighter.spawn_point.y))


def test_fighter_does_not_reach_owner_clock_tail_or_size():
    """#286/S3: the Fighter aggregate must not reach into the Player adapter for
    lifecycle/construction wiring — `Player.reset_to_spawn` owns the clock/tail
    reset and `size` comes from config. AST-checked (ignores the comments that
    still *describe* the old wiring). Able-to-fail: re-add any reach and this reds.
    """
    import ast
    import pathlib
    import pycats.entities.fighter as fm

    tree = ast.parse(pathlib.Path(fm.__file__).read_text(encoding="utf-8"))
    bad = {"_clock", "tail", "SIZE"}
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in bad:
            base = node.value
            reaches_owner = (
                (isinstance(base, ast.Attribute) and base.attr == "owner")  # self.owner._clock/.tail
                or (isinstance(base, ast.Name) and base.id == "owner")       # owner.SIZE
            )
            if reaches_owner:
                offenders.append(f"line {node.lineno}: owner.{node.attr}")
    assert offenders == [], "Fighter reaches the Player adapter: " + "; ".join(offenders)


def test_fighter_has_no_player_back_reference():
    """#264/S6 capstone: the Fighter->Player dependency is strictly one-way. The
    aggregate holds no `self.owner` and `Fighter.__init__` takes no `owner` param —
    domain methods return intent for the adapter to apply. Able-to-fail:
    reintroduce the back-reference (the param or any `self.owner`) and this reds.
    """
    import ast
    import pathlib
    import pycats.entities.fighter as fm

    tree = ast.parse(pathlib.Path(fm.__file__).read_text(encoding="utf-8"))

    self_owner = [
        f"line {n.lineno}"
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute) and n.attr == "owner"
        and isinstance(n.value, ast.Name) and n.value.id == "self"
    ]
    assert self_owner == [], "Fighter has a Player back-reference at " + ", ".join(self_owner)

    fighter_cls = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "Fighter"
    )
    init = next(n for n in fighter_cls.body
                if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    params = [a.arg for a in init.args.args]
    assert "owner" not in params, f"Fighter.__init__ still takes `owner`: {params}"
