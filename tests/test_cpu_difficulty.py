"""CPU difficulty scaffold — deterministic core (#232, #231 / #148 step 1).

A `level` (1-9) sets the deterministic AI knobs (reaction_delay / attack_period /
standoff) from the #148 Q5 table; a level-less controller is unchanged (golden-safe).
RNG knobs (follow-through / shield) are a later child. Numbers per #148 (tuning
starting points).
"""

import random
import types

import pygame as pg

from pycats.sim.controllers import AttackerController, level_params


def _knobs(p):
    return (p.reaction_delay, p.attack_period, p.standoff)


def test_level_params_anchor_values():
    assert _knobs(level_params(1)) == (30, 48, 45)
    assert _knobs(level_params(3)) == (20, 36, 40)
    assert _knobs(level_params(5)) == (12, 24, 35)
    assert _knobs(level_params(7)) == (6, 16, 32)
    assert _knobs(level_params(9)) == (1, 10, 30)


def test_intermediate_levels_interpolate_distinct():
    # #703: even levels are no longer snapped to a neighbouring odd anchor — they
    # linearly interpolate the continuous knobs, so every level 1-9 is distinct.
    for even, odd in ((2, 3), (4, 5), (6, 7), (8, 9)):
        assert level_params(even).reaction_delay != level_params(odd).reaction_delay
    # The full reaction_delay ladder (half-up rounded ints between the anchors).
    assert [level_params(n).reaction_delay for n in range(1, 10)] == [30, 25, 20, 16, 12, 9, 6, 4, 1]
    assert [level_params(n).attack_period for n in range(1, 10)] == [48, 42, 36, 30, 24, 20, 16, 13, 10]
    assert [level_params(n).standoff for n in range(1, 10)] == [45, 43, 40, 38, 35, 34, 32, 31, 30]


def test_standoff_lv2_rounds_half_up():
    # #703 pinned rounding case: midpoint(45, 40) = 42.5 → half-up 43 (NOT banker's 42).
    assert level_params(2).standoff == 43


def test_all_nine_levels_distinct():
    seen = [_knobs(level_params(n)) for n in range(1, 10)]
    assert len(set(seen)) == 9


def test_continuous_knobs_monotonic_across_1_to_9():
    seq = [level_params(n) for n in range(1, 10)]
    # non-increasing: harder levels react/attack faster and stand closer.
    for attr in ("reaction_delay", "attack_period", "standoff"):
        vals = [getattr(p, attr) for p in seq]
        assert all(a >= b for a, b in zip(vals, vals[1:])), (attr, vals)
    # non-decreasing: commit/shield/evade propensity rises with level.
    for attr in ("follow_through_p", "shield_chance", "evade_chance"):
        vals = [getattr(p, attr) for p in seq]
        assert all(a <= b for a, b in zip(vals, vals[1:])), (attr, vals)


def test_discrete_flags_inherit_lower_odd_rung():
    # #703: interpolation is for continuous knobs; discrete capability flags stay
    # threshold-gated — an even level inherits the LOWER odd anchor's kit (a capability
    # unlocks on its odd rung, not a half-step early).
    assert level_params(4).enabled_moves == level_params(3).enabled_moves
    assert level_params(4).reactive_shield is False  # unlocks at Lv5
    assert level_params(6).reactive_shield is True
    assert level_params(6).edge_hog is False  # unlocks at Lv7
    assert level_params(8).edge_hog is True


def test_out_of_range_level_clamps():
    assert level_params(0) == level_params(1)
    assert level_params(12) == level_params(9)


def test_attacker_controller_pulls_knobs_from_level():
    c9 = AttackerController(level=9)
    assert (c9.attack_period, c9.standoff, c9.reaction_delay) == (10, 30, 1)
    c1 = AttackerController(level=1)
    assert (c1.attack_period, c1.standoff, c1.reaction_delay) == (48, 45, 30)


def test_default_controller_has_zero_reaction_delay():
    # level-less default must be unchanged (golden-safe): no reaction latency.
    assert AttackerController().reaction_delay == 0


# ---- reaction_delay actually gates the first attack ----

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}


def _stub(cx, cy, alive=True, on_ground=True):
    s = types.SimpleNamespace()
    s.rect = pg.Rect(0, 0, 40, 60)
    s.rect.center = (cx, cy)
    s.fighter = types.SimpleNamespace(is_alive=alive, on_ground=on_ground)
    s.controls = _CTRL
    return s


def _first_attack_frame(level):
    c = AttackerController(attacker_num=1, level=level)
    a, t = _stub(100, 300), _stub(140, 300)  # adx=40, dy=0 → in range for Lv1 and Lv9
    for k in range(60):
        fi = c(a, t, frame=k)
        if _CTRL["attack"] in fi.pressed:
            return k
    return None


def test_reaction_delay_gates_first_attack_higher_level_attacks_sooner():
    lv9, lv1 = _first_attack_frame(9), _first_attack_frame(1)
    assert lv9 is not None and lv1 is not None, f"both should attack; lv9={lv9} lv1={lv1}"
    assert lv9 < lv1, f"Lv9 (delay 1) must attack before Lv1 (delay 30): lv9={lv9} lv1={lv1}"


# ---- #238: seeded follow-through + shield propensity ----


def test_level_params_includes_seeded_knobs():
    assert (level_params(1).follow_through_p, level_params(1).shield_chance) == (0.15, 0.00)
    assert (level_params(5).follow_through_p, level_params(5).shield_chance) == (0.55, 0.15)
    assert (level_params(9).follow_through_p, level_params(9).shield_chance) == (1.00, 0.85)


def test_controller_pulls_seeded_knobs_from_level():
    c9 = AttackerController(level=9)
    assert (c9.follow_through_p, c9.shield_chance) == (1.00, 0.85)
    c1 = AttackerController(level=1)
    assert (c1.follow_through_p, c1.shield_chance) == (0.15, 0.00)


def test_default_controller_always_commits_never_shields():
    c = AttackerController()  # golden-safe default: no rng-driven divergence
    assert c.follow_through_p == 1.0
    assert c.shield_chance == 0.0


def _count(level_kwargs, key, frames=360, seed=0):
    c = AttackerController(attacker_num=1, rng=random.Random(seed), **level_kwargs)
    a, t = _stub(100, 300), _stub(140, 300)  # in range, dy=0
    n = 0
    for k in range(frames):
        fi = c(a, t, frame=k)
        if _CTRL[key] in fi.held:
            n += 1
    return n


def test_low_follow_through_commits_fewer_attacks_than_high():
    # same cadence/reaction, different follow-through; fixed seed → deterministic.
    base = dict(attack_period=12, reaction_delay=0, shield_chance=0.0)
    high = _count({**base, "follow_through_p": 1.0}, "attack")
    low = _count({**base, "follow_through_p": 0.1}, "attack")
    assert low < high, f"low follow-through should attack less: low={low} high={high}"


def test_shield_chance_raises_shield_and_seed_changes_pattern():
    base = dict(attack_period=12, reaction_delay=0, follow_through_p=1.0, shield_chance=0.5)

    def shield_frames(seed):
        c = AttackerController(attacker_num=1, rng=random.Random(seed), **base)
        a, t = _stub(100, 300), _stub(140, 300)
        return [k for k in range(60) if _CTRL["shield"] in c(a, t, frame=k).held]

    s1, s2 = shield_frames(1), shield_frames(2)
    assert len(s1) >= 1, "shield_chance>0 should raise shield on at least one frame"
    assert s1 != s2, "different seeds should change the shield pattern (#166)"


# ---- #248: moveset-aware CPU (specials/fireball when enabled) ----


def test_enabled_moves_anchors():
    assert level_params(1).enabled_moves == frozenset({"jab"})
    assert "aerials" in level_params(5).enabled_moves
    assert "specials" not in level_params(5).enabled_moves
    assert "specials" in level_params(9).enabled_moves


def test_controller_enabled_moves_from_level():
    assert "specials" in AttackerController(level=9).enabled_moves
    assert "specials" not in AttackerController(level=1).enabled_moves
    assert "specials" not in AttackerController().enabled_moves  # default golden-safe


def _special_presses(enabled, adx=150, frames=40):
    # isolate the capability: no shield/follow noise, target in the ranged band.
    c = AttackerController(
        attacker_num=1,
        enabled_moves=enabled,
        shield_chance=0.0,
        follow_through_p=1.0,
        reaction_delay=0,
        rng=random.Random(0),
    )
    a, t = _stub(100, 300), _stub(100 + adx, 300)
    return sum(1 for k in range(frames) if _CTRL["special"] in c(a, t, frame=k).held)


def test_specials_capability_throws_fireball_at_range():
    assert _special_presses(frozenset({"jab", "specials"})) >= 1, (
        "a specials-enabled bot should poke with a fireball at range"
    )
    assert _special_presses(frozenset({"jab"})) == 0, "a bot without specials must never press the special key"


def _battle_spawns_fireball(p1_level, frames=120, seed=3):
    """Run a leveled two-Nalio battle; True if a moving projectile (fireball) spawns."""
    import pygame

    import watch
    from pycats.core.input import merge_frames
    from pycats.sim import runner

    plats = runner.build_stage()
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    c1, c2 = watch.cpu_controllers(p1_level, 1, random.Random(seed))
    attacks = pygame.sprite.Group()
    for f in range(frames):
        fi = merge_frames(c(p1, p2, f) for c in (c1, c2))
        for p in players:
            p.update(fi, plats, attacks)
        attacks.update()
        if any(getattr(a, "velocity", None) for a in attacks):
            return True
    return False


def test_lv9_nalio_throws_fireball_in_battle_lv1_does_not():
    assert _battle_spawns_fireball(9) is True, "Lv9 (specials) should throw a fireball in a real battle"
    assert _battle_spawns_fireball(1) is False, "Lv1 (no specials) should never throw one"


# ---- #254: threat-aware shielding (reactive at high level; random at low) ----


def _atk(owner, cx, cy, velocity=None, active=True):
    """A stub Attack sprite: an opponent's hitbox/projectile in the `attacks` group.
    Melee hitboxes have velocity=None; projectiles carry a (vx, vy)."""
    s = types.SimpleNamespace()
    s.owner = owner
    s.rect = pg.Rect(0, 0, 30, 30)
    s.rect.center = (cx, cy)
    s.velocity = velocity
    s.active = active
    return s


def _reactive(**kw):
    base = dict(
        attacker_num=1,
        reactive_shield=True,
        shield_chance=1.0,
        reaction_delay=0,
        follow_through_p=1.0,
        rng=random.Random(0),
    )
    base.update(kw)
    return AttackerController(**base)


def test_level_params_reactive_shield_flag():
    # Low levels shield at random (#238 flavour); mid/high shield reactively (#251 Q2).
    assert level_params(1).reactive_shield is False
    assert level_params(3).reactive_shield is False
    assert level_params(5).reactive_shield is True
    assert level_params(9).reactive_shield is True


def test_controller_pulls_reactive_shield_from_level():
    assert AttackerController(level=9).reactive_shield is True
    assert AttackerController(level=1).reactive_shield is False
    assert AttackerController().reactive_shield is False  # default golden-safe


def test_reactive_shield_does_not_shield_in_open_space():
    # THE user complaint: a high-level bot must NOT shield with nothing near it.
    c = _reactive()
    a, t = _stub(100, 300), _stub(140, 300)
    held = [k for k in range(30) if _CTRL["shield"] in c(a, t, frame=k, attacks=[]).held]
    assert held == [], "reactive bot must NOT shield with no threat present"


def test_reactive_shield_shields_when_opponent_melee_incoming():
    c = _reactive()
    a, t = _stub(100, 300), _stub(180, 300)
    threat = [_atk(owner=t, cx=140, cy=300)]  # opponent melee hitbox near the bot
    shielded = any(_CTRL["shield"] in c(a, t, frame=k, attacks=threat).held for k in range(5))
    assert shielded, "reactive bot should shield a detected incoming melee hitbox"


def test_reactive_shield_reacts_to_closing_projectile():
    c = _reactive()
    a, t = _stub(100, 300), _stub(300, 300)
    incoming = [_atk(owner=t, cx=200, cy=300, velocity=(-10, 0))]  # right of bot, moving left → closing
    shielded = any(_CTRL["shield"] in c(a, t, frame=k, attacks=incoming).held for k in range(5))
    assert shielded, "a projectile closing on the bot is an incoming threat"


def test_reactive_shield_ignores_receding_projectile():
    c = _reactive()
    a, t = _stub(100, 300), _stub(300, 300)
    away = [_atk(owner=t, cx=150, cy=300, velocity=(10, 0))]  # right of bot, moving further right → away
    held = [k for k in range(10) if _CTRL["shield"] in c(a, t, frame=k, attacks=away).held]
    assert held == [], "a projectile moving away is not an incoming threat"


def test_reactive_shield_ignores_own_attacks():
    c = _reactive()
    a, t = _stub(100, 300), _stub(180, 300)
    mine = [_atk(owner=a, cx=140, cy=300)]  # the bot's OWN hitbox is not a threat
    held = [k for k in range(10) if _CTRL["shield"] in c(a, t, frame=k, attacks=mine).held]
    assert held == [], "the bot must not shield because of its own attack"


def test_reactive_shield_ignores_distant_threat():
    c = _reactive(shield_threat_range=160)
    a, t = _stub(100, 300), _stub(900, 300)
    far = [_atk(owner=t, cx=800, cy=300)]  # well beyond the threat band
    held = [k for k in range(10) if _CTRL["shield"] in c(a, t, frame=k, attacks=far).held]
    assert held == [], "a hitbox outside the threat range is not yet incoming"


def test_low_level_shield_unchanged_random_in_open_space():
    # Non-reactive (low) level keeps the unconditional random shield flavour (#238).
    c = AttackerController(
        attacker_num=1,
        reactive_shield=False,
        shield_chance=0.8,
        reaction_delay=0,
        follow_through_p=1.0,
        rng=random.Random(1),
    )
    a, t = _stub(100, 300), _stub(140, 300)
    held = [k for k in range(30) if _CTRL["shield"] in c(a, t, frame=k, attacks=[]).held]
    assert len(held) >= 1, "non-reactive bot still shields at random in open space (#238 preserved)"


def test_default_controller_ignores_attacks_never_shields():
    # Golden-safe: default path ignores the new attacks arg and never shields.
    c = AttackerController()
    a, t = _stub(100, 300), _stub(140, 300)
    threat = [_atk(owner=t, cx=140, cy=300)]
    held = [k for k in range(20) if _CTRL["shield"] in c(a, t, frame=k, attacks=threat).held]
    assert held == [], "default controller never shields, even with the attacks arg"


# --- #248-gotcha guards: prove the behaviour in REAL battle loops, not just stubs ---
# (A green unit test ≠ a working feature; #248 proved a capability can pass a stubbed
#  decide() yet not manifest in a real battle. These step the real Player.update +
#  attacks-group loop and assert the reactive shield actually fires.)


def _defensive_reactive(num, **kw):
    """A purely-defensive reactive shielder: never commits a melee attack
    (follow_through_p=0), shields any detected threat reliably (shield_chance=1.0)."""
    base = dict(
        attacker_num=num,
        rng=random.Random(4),
        reaction_delay=0,
        follow_through_p=0.0,
        shield_chance=1.0,
        reactive_shield=True,
        enabled_moves=frozenset({"jab"}),
    )
    base.update(kw)
    return AttackerController(**base)


def test_reactive_bot_shields_incoming_melee_in_real_battle():
    # Real AI battle: an aggressive Lv7 attacker (p1) vs a reactive defender (p2).
    # p2 should be in `shield` state while p1 is winding up an attack in range.
    import pygame

    from pycats.core.input import merge_frames
    from pycats.sim import runner

    plats = runner.build_stage()
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    c1 = AttackerController(attacker_num=1, level=7, rng=random.Random(3))
    c2 = _defensive_reactive(2, standoff=40)
    attacks = pygame.sprite.Group()
    shielded_while_threatened = False
    for f in range(160):
        fi = merge_frames(c(p1, p2, f, attacks) for c in (c1, c2))
        for p in players:
            p.update(fi, plats, attacks)
        attacks.update()
        threatened = (
            p1.current_move is not None
            and abs(p1.rect.centerx - p2.rect.centerx) <= 160
            and abs(p1.rect.centery - p2.rect.centery) <= 80
        )
        if threatened and p2.state == "shield":
            shielded_while_threatened = True
            break
    assert shielded_while_threatened, "reactive bot should raise shield while the opponent winds up an attack in range"


def test_reactive_bot_shields_incoming_projectile_in_real_loop():
    # Real loop with a REAL Attack projectile (its circles/rect advanced by
    # attacks.update()). The opponent (p1) is idle and FAR (400px), so the ONLY
    # in-band threat is the projectile — proving the projectile branch end-to-end.
    import pygame

    import pycats.characters.nalio_cat as nalio
    from pycats.core.input import merge_frames
    from pycats.entities.attack import Attack
    from pycats.sim import runner
    from pycats.sim.controllers import IdlerController

    fb_move = next(v for v in vars(nalio).values() if getattr(v, "projectile_speed", None) is not None)
    plats = runner.build_stage()
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    c1 = IdlerController(attacker_num=1)  # p1 stays put at spawn (far from p2)
    c2 = _defensive_reactive(2, standoff=400)  # p2 holds its ground near spawn
    attacks = pygame.sprite.Group()
    shielded_projectile_only = False
    for f in range(60):
        if f == 5:  # inject a real projectile at p2's level, closing from the left
            atk = Attack(p1, hitboxes=fb_move.hitboxes, velocity=(8, 0), lifetime=73, disappear_on_hit=True)
            atk.rect.center = (p2.rect.centerx - 120, p2.rect.centery)
            attacks.add(atk)
        fi = merge_frames(c(p1, p2, f, attacks) for c in (c1, c2))
        for p in players:
            p.update(fi, plats, attacks)
        attacks.update()
        proj_near = any(getattr(a, "velocity", None) and a.owner is p1 for a in attacks)
        p1_threatening = p1.current_move is not None and abs(p1.rect.centerx - p2.rect.centerx) <= 160
        if proj_near and p2.state == "shield" and not p1_threatening:
            shielded_projectile_only = True
            break
    assert shielded_projectile_only, "reactive bot should shield a real closing projectile (projectile the sole threat)"
