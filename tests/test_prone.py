"""Prone / knockdown state (#13).

Prone is a driven state: force-entry via
`Player.force_prone(frames)` (mirroring how shield-break drives `stun`), the only
self-initiated action is standing up, and the getup window is the `prone_timer`
counting to 0 -> stand to idle (on ground) / fall (airborne). The automatic
landing-velocity trigger is #145; getup-roll / getup-attack are #146.

The golden replay never forces prone, so existing goldens are unaffected; these
tests pin the new behaviour.
"""
import pygame

from pycats.entities import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


def _mk():
    return Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True)


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


def _run(p, plats, frame, n=1):
    grp = pygame.sprite.Group()
    for _ in range(n):
        p.update(frame, plats, grp)


# --- Slice 1: force-entry into prone -----------------------------------------

def test_force_prone_enters_prone():
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    assert p.state == "idle"
    p.force_prone(20)
    assert p.state == "prone"


# --- Slice 2: getup window — prone persists, then stands to idle --------------

def test_prone_persists_then_stands_up():
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    p.force_prone(5)
    # holds prone while the getup window runs down...
    for _ in range(4):
        _run(p, plats, _frame())
        assert p.state == "prone"
    # ...then the window elapses and the fighter stands up.
    _run(p, plats, _frame())
    assert p.state == "idle"


# --- Slice 3: only stand-up is allowed — actions are locked out --------------

def test_prone_locks_out_actions():
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    p.force_prone(10)
    # Mashing attack must not start a move...
    _run(p, plats, _frame("attack"), n=3)
    assert p.state == "prone"
    assert p.attack_timer == 0
    # ...and mashing jump ('up') must not launch the fighter off the ground.
    _run(p, plats, _frame("up"), n=3)
    assert p.state == "prone"
    assert p.fighter.on_ground


# --- Slice 4: prone runtime drives a stable state sequence -------------------

def test_prone_state_sequence_reaches_prone_then_stands():
    """A force_prone + getup scenario produces a prone run that stands back up
    (the golden in test_golden.py guards byte-stability)."""
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    p.force_prone(6)
    seq = []
    for _ in range(10):
        _run(p, plats, _frame())
        seq.append(p.state)
    assert "prone" in seq, "scenario never reached prone"
    assert seq[-1] == "idle", f"fighter never stood up: {seq}"


# --- #146: getup-roll — a directional getup with intangibility ----------------

def test_getup_roll_when_direction_held_rolls_out_intangible():
    """Holding a direction as the getup window ends rolls out — an intangible,
    displaced getup — instead of the neutral stand to idle."""
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    x0 = p.fighter.rect.x
    p.force_prone(3)
    for _ in range(3):                      # hold 'right' through the prone window
        _run(p, plats, _frame("right"))
    assert p.state == "getup_roll", "a held direction at getup should roll, not stand"
    assert p.fighter.invulnerable, "getup-roll grants intangibility"
    for _ in range(30):                     # roll plays out -> recovers to idle
        _run(p, plats, _frame())
        if p.state == "idle":
            break
    assert p.state == "idle"
    assert p.fighter.rect.x > x0, "the roll displaced the fighter forward"
    assert not p.fighter.invulnerable, "intangibility ends when the roll ends"


def test_neutral_getup_still_stands_without_direction():
    """No direction held at getup => unchanged neutral stand to idle (#13)."""
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    p.force_prone(3)
    for _ in range(4):
        _run(p, plats, _frame())            # no direction
    assert p.state == "idle"


# --- #225 (#146 slice 2): getup-attack — a wake-up attack out of prone ---------

def test_getup_attack_when_attack_held_swings_intangible_and_spawns_hitbox():
    """Holding attack as the getup window ends performs a wake-up attack — a
    getup_attack state that spawns a hitbox, intangible, then recovers to idle."""
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    grp = pygame.sprite.Group()
    p.force_prone(3)
    for _ in range(3):                       # hold attack through the prone window
        p.update(_frame("attack"), plats, grp)
    assert p.state == "getup_attack", "attack held at getup should swing, not stand"
    assert p.fighter.invulnerable, "getup-attack has getup intangibility"
    spawned = len(grp) > 0
    for _ in range(30):                      # the swing spawns a hitbox, then recovers
        p.update(_frame(), plats, grp)
        spawned = spawned or len(grp) > 0
        if p.state == "idle":
            break
    assert spawned, "getup-attack should spawn a hitbox"
    assert p.state == "idle"
    assert not p.fighter.invulnerable, "intangibility ends with the getup-attack"


def test_getup_roll_beats_getup_attack_when_both_held():
    """A held direction (roll) takes precedence over attack at getup."""
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    p.force_prone(3)
    for _ in range(3):
        _run(p, plats, _frame("right", "attack"))
    assert p.state == "getup_roll"


# --- #173: prone posture geometry — body lowers, high attacks whiff -----------

def test_prone_resizes_collision_rect_feet_planted():
    """While prone the body Rect is shorter than the 40x60 stand box AND shorter
    than the 40x40 crouch box (lying-down posture), with the bottom unchanged."""
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    stand_bottom = p.rect.bottom
    assert p.rect.height == 60
    p.force_prone(20)
    _run(p, plats, _frame())                   # one update applies the resize
    assert p.state == "prone"
    assert p.rect.height < 40                   # lower than the crouch box (40)
    assert p.rect.bottom == stand_bottom        # feet planted


def test_prone_stands_back_up_restores_box():
    """When the getup window elapses the stand box is restored, feet planted."""
    p = _mk()
    plats = _ground()
    _settle(p, plats)
    bottom = p.rect.bottom
    p.force_prone(3)
    for _ in range(6):                          # run past the getup window
        _run(p, plats, _frame())
    assert p.state == "idle"
    assert p.rect.height == 60
    assert p.rect.bottom == bottom


def _high_attack(owner, cx, cy, r=8):
    from types import SimpleNamespace
    return SimpleNamespace(active=True, owner=owner, hit_cx=cx, hit_cy=cy,
                           hit_r=r, disappear_on_hit=False, damage=10.0,
                           base_knockback=0.0, knockback_growth=0.0, angle=0)


def test_prone_lowers_hurtbox_high_attack_whiffs():
    """A high hit that connects on a standing fighter whiffs over a prone one
    (mirrors test_crouch_lowers_hurtbox_high_attack_whiffs)."""
    from pycats.systems import combat
    plats = _ground()
    attacker = _mk()

    standing = _mk(); _settle(standing, plats)
    cx, cy = standing.rect.centerx, standing.rect.top + 5
    combat.process_hits([standing], [_high_attack(attacker, cx, cy)])
    assert standing.fighter.percent == 10.0, "high hit should connect standing"

    downed = _mk(); _settle(downed, plats)
    downed.force_prone(20)
    _run(downed, plats, _frame())
    assert downed.state == "prone"
    # Same world-space point now sits above the lowered prone hurtbox -> whiff.
    combat.process_hits([downed], [_high_attack(attacker, cx, cy)])
    assert downed.fighter.percent == 0.0, "high hit should whiff over the prone fighter"


def test_prone_uses_purpose_built_hurtbox_not_resized_standing():
    """Load-bearing on the prone_hurtbox SELECTION (#173 combat.py branch): a hit
    just below the planted feet falls OUTSIDE the short purpose-built prone hurtbox
    but INSIDE the tall standing hurtbox mis-resolved against the shrunk prone Rect.
    It must whiff — so disabling the combat.py prone branch makes this connect."""
    from pycats.systems import combat
    plats = _ground()
    attacker = _mk()
    downed = _mk(); _settle(downed, plats)
    downed.force_prone(20)
    _run(downed, plats, _frame())
    assert downed.state == "prone"
    near_ground_cy = downed.rect.bottom + 6
    combat.process_hits(
        [downed], [_high_attack(attacker, downed.rect.centerx, near_ground_cy, r=2)])
    assert downed.fighter.percent == 0.0, (
        "near-ground hit must whiff the short prone hurtbox (not the mis-resolved "
        "standing box)"
    )


def test_nalio_has_prone_geometry():
    """Nalio (Mario archetype) defines a prone box lower than its crouch box, with
    a hurtbox that sits lower than the standing one (mirrors the crouch data test)."""
    from pycats.combat.data import load_fighter_data, Hurtbox
    fd = load_fighter_data("nalio")
    assert fd.prone_size is not None
    w, h = fd.prone_size
    assert w == 40 and h < fd.crouch_size[1]      # lower than the crouch box
    assert isinstance(fd.prone_hurtbox, Hurtbox)
    stand_top = min(c.dy - c.r for c in fd.hurtbox.circles)
    prone_top = min(c.dy - c.r for c in fd.prone_hurtbox.circles)
    assert prone_top >= stand_top, "prone hurtbox should not sit above the standing one"


def test_prone_pose_renders_without_error():
    """The prone render pose draws without raising (visual-only / playtested)."""
    import pygame
    from pycats import render_battle
    p = _mk(); plats = _ground(); _settle(p, plats)
    p.force_prone(20); _run(p, plats, _frame())
    assert p.state == "prone"
    surf = pygame.Surface((400, 300))
    render_battle.render_battle(surf, [p], pygame.sprite.Group())


# --- #145: auto landing-velocity knockdown -> prone --------------------------

def _land_in_hitstun(vy, hurt, frames=8):
    """Drop a fighter onto the ground from just above it, airborne, with the given
    downward velocity and hitstun, then run a few frames. Returns (player, states)."""
    p = _mk()
    plats = _ground()                 # solid platform, top at y=100
    p.rect.bottom = 90                # airborne, just above the platform top
    p.fighter.on_ground = False
    p.fighter.vel.y = vy
    p.fighter.hurt_timer = hurt
    grp = pygame.sprite.Group()
    states = []
    for _ in range(frames):
        p.update(_frame(), plats, grp)
        states.append(p.state)
    return p, states


def test_hard_landing_in_hitstun_knocks_down_to_prone():
    """Landing hard (impact >= threshold) while still in hitstun forces prone."""
    p, states = _land_in_hitstun(vy=11, hurt=12)
    assert p.fighter.on_ground, "fixture: fighter should have landed"
    assert "prone" in states, f"hard landing in hitstun did not knock down: {states}"
    assert p.state == "prone", f"expected to stay prone after knockdown: {p.state}"


def test_normal_landing_not_in_hitstun_does_not_knock_down():
    """Same hard impact but NOT in hitstun (hurt_timer == 0) — an ordinary landing,
    no knockdown. This is the gate that separates knockdown from a normal jump."""
    p, states = _land_in_hitstun(vy=11, hurt=0)
    assert p.fighter.on_ground
    assert "prone" not in states, f"normal landing wrongly knocked down: {states}"


def test_soft_landing_in_hitstun_below_threshold_does_not_knock_down():
    """In hitstun but landing gently (impact below KNOCKDOWN_VY_THRESHOLD) — the
    velocity gate suppresses the knockdown."""
    p, states = _land_in_hitstun(vy=2, hurt=12)
    assert p.fighter.on_ground
    assert "prone" not in states, f"soft landing wrongly knocked down: {states}"


# --- #145 auto-knockdown-on-landing + S5/#298 engine-inversion guards ----------
def test_hard_landing_in_hitstun_forces_prone_through_update():
    """#145: landing while in hitstun (hurt_timer > 0) at/above
    KNOCKDOWN_VY_THRESHOLD downward forces prone — exercised THROUGH update /
    step_physics (this path had no test). Guards the S5/#298 wiring: able-to-fail
    if Player drops the force_prone after step_physics, the fighter won't be prone.
    """
    from pycats.config import KNOCKDOWN_VY_THRESHOLD
    plats = _ground()
    p = _mk()
    p.fighter.on_ground = False
    p.rect.bottom = plats[0].rect.top - 2     # just above the ground
    p.fighter.vel.y = KNOCKDOWN_VY_THRESHOLD + 4  # hard downward impact
    p.fighter.hurt_timer = 10                  # in hitstun / tumble
    _run(p, plats, _frame())                   # one update -> land -> knockdown
    assert p.state == "prone"


def test_fighter_does_not_drive_the_player_engine():
    """#298/S5: Fighter rules return intent; the Player adapter applies the FSM
    transition. `entities/fighter.py` must make no `owner.engine` / `owner.force_prone`
    reach. AST-checked. Able-to-fail: re-adding either reach reds this."""
    import ast
    import pathlib
    import pycats.entities.fighter as fm

    tree = ast.parse(pathlib.Path(fm.__file__).read_text(encoding="utf-8"))
    bad = {"engine", "force_prone"}
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in bad:
            base = node.value
            if isinstance(base, ast.Attribute) and base.attr == "owner":
                offenders.append(f"line {node.lineno}: owner.{node.attr}")
    assert offenders == [], "Fighter drives the Player engine: " + "; ".join(offenders)
