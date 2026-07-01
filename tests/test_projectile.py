"""#266: Nalio fireball gravity + ground-bounce — PM Mario-faithful projectile.

A `Projectile` subclass of `Attack` owns the moving/physics behaviour (gravity +
ground-bounce); `Attack` stays the static melee hitbox. Per #263 research the flat
projectile (vy=0) sailed over foes on lower terrain — a Mario fireball arcs down and
bounces along the ground. Numbers (gravity/restitution/max_bounces) are tuning guesses.
"""
import types

import pygame as pg

from pycats.entities.attack import Attack, Projectile
import pycats.characters.nalio_cat as nalio

pg.init()

_FB = next(v for v in vars(nalio).values()
           if getattr(v, "projectile_speed", None) is not None)


def _owner(facing_right=True):
    return types.SimpleNamespace(
        rect=pg.Rect(0, 0, 40, 60),
        fighter=types.SimpleNamespace(facing_right=facing_right),
    )


def _proj(cx, cy, vx=8, vy=0, gravity=0.5, restitution=0.6, max_bounces=3):
    p = Projectile(_owner(), hitboxes=_FB.hitboxes, velocity=(vx, vy), lifetime=500,
                   gravity=gravity, restitution=restitution, max_bounces=max_bounces)
    # Pin to a deterministic single-circle position for predictable physics asserts.
    r = p.hit_r
    p.hit_cx, p.hit_cy = float(cx), float(cy)
    p.resolved = [(float(cx), float(cy), r, _FB.hitboxes[0])]
    p.rect.center = (cx, cy)
    return p


def _plat(left, top, width=400, height=20):
    return types.SimpleNamespace(rect=pg.Rect(left, top, width, height))


def test_projectile_is_an_attack_subclass():
    assert issubclass(Projectile, Attack)
    assert isinstance(_proj(100, 100), Attack)  # process_hits treats it as a hitbox


def test_gravity_makes_projectile_descend_while_advancing():
    p = _proj(100, 100, vx=8, vy=0, gravity=0.5)
    y0, x0 = p.hit_cy, p.hit_cx
    for _ in range(10):
        p.update()  # no platforms → pure free-fall arc
    assert p.hit_cy > y0, "gravity should pull the projectile downward"
    assert p.hit_cx > x0, "it should keep advancing horizontally"


def test_zero_gravity_projectile_travels_flat():
    # Backward-compat / Fox-laser-style: gravity=0 → straight line (the old #223 model).
    p = _proj(100, 100, vx=8, vy=0, gravity=0.0)
    y0 = p.hit_cy
    for _ in range(10):
        p.update()
    assert p.hit_cy == y0, "a zero-gravity projectile must travel perfectly flat"


def test_projectile_bounces_off_platform_top():
    # Falling projectile over a platform should reflect upward (vy flips +→-) and not
    # sink below the platform top.
    plat = _plat(0, 300, width=960)
    p = _proj(100, 250, vx=6, vy=0, gravity=0.5, restitution=0.6)
    bounced = False
    for _ in range(80):
        p.update([plat])
        if p.velocity[1] < 0:          # moving upward ⇒ it bounced
            bounced = True
            break
    assert bounced, "projectile should bounce (vy turns negative) off the platform top"
    assert p.hit_cy + p.hit_r <= plat.rect.top + 1, "must rest on/above the platform top"


def test_bounce_loses_vertical_momentum():
    plat = _plat(0, 300, width=960)
    p = _proj(100, 250, vx=6, vy=0, gravity=0.5, restitution=0.6)
    speed_before = None
    for _ in range(80):
        prev_vy = p.velocity[1]
        p.update([plat])
        if prev_vy > 0 and p.velocity[1] < 0:  # the bounce frame
            speed_before, speed_after = prev_vy, -p.velocity[1]
            break
    assert speed_before is not None, "expected a bounce"
    assert speed_after < speed_before, \
        f"restitution<1 should lose vertical speed: after={speed_after} before={speed_before}"


def test_projectile_expires_after_max_bounces():
    plat = _plat(0, 300, width=960)
    p = _proj(100, 250, vx=2, vy=0, gravity=0.5, restitution=0.6, max_bounces=2)
    for _ in range(400):
        p.update([plat])
        if not p.alive():
            break
    assert not p.alive(), "projectile should despawn after exceeding max_bounces"


def test_static_attack_update_accepts_platforms_arg():
    # attacks.update(platforms) forwards the arg to EVERY sprite; a static melee
    # Attack must accept and ignore it (golden-safe).
    a = Attack(_owner(), hitboxes=_FB.hitboxes, lifetime=5)
    before = (a.hit_cx, a.hit_cy)
    a.update([_plat(0, 300)])           # must not raise, must not move (static)
    assert (a.hit_cx, a.hit_cy) == before


def test_player_spawns_projectile_for_projectile_move_static_stays_attack():
    # Real spawn path: a Lv9 (specials) bot throws → the moving attack is a Projectile;
    # a Lv1 (melee) bot's hitbox is a plain Attack, never a Projectile.
    import random
    import pygame
    from pycats.sim import runner
    from pycats.core.input import merge_frames
    from pycats.sim.controllers import AttackerController

    def spawned_types(level, frames=120):
        plats = runner.build_stage()
        p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
        c1 = AttackerController(attacker_num=1, level=level, rng=random.Random(3))
        c2 = AttackerController(attacker_num=2, level=1, rng=random.Random(3))
        attacks = pygame.sprite.Group()
        seen = set()
        for f in range(frames):
            fi = merge_frames(c(p1, p2, f, attacks) for c in (c1, c2))
            for p in players:
                p.update(fi, plats, attacks)
            attacks.update(plats)
            for a in attacks:
                seen.add(type(a))
        return seen

    lv9 = spawned_types(9)
    assert Projectile in lv9, "a specials bot should spawn a Projectile (fireball)"
    lv1 = spawned_types(1)
    assert Projectile not in lv1, "a melee-only bot must never spawn a Projectile"
    assert Attack in lv1, "melee hitboxes are plain Attack sprites"


def test_fireball_reaches_lower_platform_foe_in_real_battle():
    # #248 gotcha guard + the #263 fix: a fireball thrown from the thin platform
    # (cy~260) should arc/bounce DOWN and hit a foe on the main platform (cy~380) —
    # the cross-elevation case that whiffed with flat travel.
    import pygame
    from pycats.sim import runner
    from pycats.core.input import merge_frames
    from pycats.sim.controllers import BaseController, IdlerController
    from pycats.systems import combat

    class Thrower(BaseController):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.fired = False

        def decide(self, a, t, frame, attacks=None, ledges=None):  # ledges: protocol (#404)
            if not self.fired and a.fighter.on_ground and self._f > 40:
                self.fired = True
                return {a.controls["special"]}
            return set()

    plats = runner.build_stage()
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    # p1 on the left thin platform (high); p2 grounded on the main platform (low),
    # to p1's right within the fireball's travel + descent.
    p1.rect.center = (280, 260)
    p2.rect.center = (560, 380)
    c1, c2 = Thrower(attacker_num=1), IdlerController(attacker_num=2)
    attacks = pygame.sprite.Group()
    start_pct = p2.fighter.percent
    hit = False
    for f in range(200):
        fi = merge_frames(c(p1, p2, f, attacks) for c in (c1, c2))
        for p in players:
            p.update(fi, plats, attacks)
        attacks.update(plats)
        combat.process_hits(players, attacks)
        if p2.fighter.percent > start_pct:
            hit = True
            break
    assert hit, "a bouncing fireball from a higher platform should reach a lower-platform foe"
