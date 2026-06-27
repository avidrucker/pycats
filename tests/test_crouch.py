"""Crouch state + body resize (#124).

Crouch is a new grounded state (both engine backends, in parity): hold down on
solid ground -> the body resizes to a per-cat squarish crouch box (feet planted)
and swaps to a shorter crouch hurtbox; release -> stand. Crouch-cancel (KB
reduction) is a separate follow-up.

The golden replay never presses 'down', so existing goldens are unaffected;
these tests pin the new behaviour.
"""
import pygame

from pycats.combat.data import load_fighter_data, FighterData, Hurtbox, Circle
from pycats.entities import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


def _mk(backend="legacy"):
    return Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True, state_backend=backend)


def _ground():
    # Wide thick (solid) platform under the player at y=100.
    return [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]


def _frame(*keys):
    ks = {_CONTROLS[k] for k in keys}
    return InputFrame(held=set(ks), pressed=set(ks), released=set())


def _settle(p, plats):
    grp = pygame.sprite.Group()
    for _ in range(3):
        p.update(_frame(), plats, grp)


def _run(p, plats, frame, n=3):
    grp = pygame.sprite.Group()
    for _ in range(n):
        p.update(frame, plats, grp)


# --- Slice 1: per-cat crouch geometry on FighterData -------------------------

def test_fighter_data_crouch_defaults_none():
    """A FighterData that doesn't define crouch can't crouch (crouch_size None)."""
    fd = FighterData(hurtbox=Hurtbox(circles=(Circle(0, 0, 1),)), moves={})
    assert fd.crouch_size is None
    assert fd.crouch_hurtbox is None


def test_nalio_has_crouch_geometry():
    """Nalio (Mario archetype) defines a squarish crouch box + shorter hurtbox."""
    fd = load_fighter_data("nalio")
    assert fd.crouch_size is not None
    w, h = fd.crouch_size
    assert h < 60 and w == 40           # shorter than the 40x60 stand box
    assert isinstance(fd.crouch_hurtbox, Hurtbox)
    # crouch hurtbox sits lower than the standing one (top circle is lower)
    stand_top = min(c.dy - c.r for c in fd.hurtbox.circles)
    crouch_top = min(c.dy - c.r for c in fd.crouch_hurtbox.circles)
    assert crouch_top > stand_top, "crouch hurtbox should be lower/shorter"


# --- Slices 2+3: crouch state (both backends) + collision-Rect resize --------

def test_down_on_solid_ground_enters_crouch_both_backends():
    for backend in ("legacy", "statechart"):
        p = _mk(backend)
        plats = _ground()
        _settle(p, plats)
        assert p.state == "idle", backend
        _run(p, plats, _frame("down"))
        assert p.state == "crouch", backend


def test_crouch_resizes_collision_rect_feet_planted():
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    stand_bottom = p.rect.bottom
    assert p.rect.height == 60
    _run(p, plats, _frame("down"))
    assert p.state == "crouch"
    assert p.rect.height == 40                 # squarish crouch box
    assert p.rect.bottom == stand_bottom       # feet planted


def test_release_down_stands_back_up():
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    bottom = p.rect.bottom
    _run(p, plats, _frame("down"))
    assert p.state == "crouch"
    _run(p, plats, _frame())                   # release down
    assert p.state == "idle"
    assert p.rect.height == 60
    assert p.rect.bottom == bottom


def test_shield_plus_down_is_not_crouch():
    """shield+down is a spot dodge, not a crouch — crouch must require no shield."""
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    _run(p, plats, _frame("shield", "down"), n=2)
    assert p.state != "crouch"


# --- Slice 4: crouching lowers the hurtbox (high attacks whiff) ---------------

def _high_attack(owner, cx, cy, r=8):
    from types import SimpleNamespace
    return SimpleNamespace(active=True, owner=owner, hit_cx=cx, hit_cy=cy,
                           hit_r=r, disappear_on_hit=False, damage=10.0,
                           base_knockback=0.0, knockback_growth=0.0, angle=0)


def test_crouch_lowers_hurtbox_high_attack_whiffs():
    from pycats.systems import combat
    plats = _ground()
    attacker = _mk()

    standing = _mk(); _settle(standing, plats)
    # A small hitbox up at the head connects with the standing hurtbox.
    cx, cy = standing.rect.centerx, standing.rect.top + 5
    combat.process_hits([standing], [_high_attack(attacker, cx, cy)])
    assert standing.fighter.percent == 10.0, "high hit should connect standing"

    crouched = _mk(); _settle(crouched, plats)
    _run(crouched, plats, _frame("down"))
    assert crouched.state == "crouch"
    # Same world-space point now sits above the lowered crouch hurtbox -> whiff.
    combat.process_hits([crouched], [_high_attack(attacker, cx, cy)])
    assert crouched.fighter.percent == 0.0, "high hit should whiff over the crouch"


# --- Slice 5: crouch is byte-identical across both engine backends ------------

def test_crouch_scenario_parity_both_backends():
    """A down-holding scenario must be byte-identical legacy vs statechart, and
    must actually reach the crouch state (so the parity is meaningful)."""
    from pycats.sim.runner import run_battle, KEYMAPS
    from pycats.sim.input_script import compile_timeline, InputSpan
    spans = [InputSpan(start=10, end=120, player=1, action="down")]
    frame_inputs = compile_timeline(spans, KEYMAPS)
    legacy = run_battle(backend="legacy", frames=len(frame_inputs),
                        frame_inputs=frame_inputs)
    state = run_battle(backend="statechart", frames=len(frame_inputs),
                       frame_inputs=frame_inputs)
    assert legacy == state, "crouch scenario diverged between backends"
    assert any(p[1] == "crouch" for snap in legacy for p in snap[0]), (
        "scenario never reached crouch — parity check is vacuous"
    )
