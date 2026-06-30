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


def test_intermediate_level_uses_nearest_anchor():
    # even levels are equidistant between odd anchors → tie resolves to the higher.
    assert level_params(2) == level_params(3)
    assert level_params(4) == level_params(5)
    assert level_params(8) == level_params(9)


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
    c = AttackerController(attacker_num=1, enabled_moves=enabled, shield_chance=0.0,
                          follow_through_p=1.0, reaction_delay=0, rng=random.Random(0))
    a, t = _stub(100, 300), _stub(100 + adx, 300)
    return sum(1 for k in range(frames) if _CTRL["special"] in c(a, t, frame=k).held)


def test_specials_capability_throws_fireball_at_range():
    assert _special_presses(frozenset({"jab", "specials"})) >= 1, \
        "a specials-enabled bot should poke with a fireball at range"
    assert _special_presses(frozenset({"jab"})) == 0, \
        "a bot without specials must never press the special key"


def _battle_spawns_fireball(p1_level, frames=120, seed=3):
    """Run a leveled two-Nalio battle; True if a moving projectile (fireball) spawns."""
    import pygame
    import watch
    from pycats.sim import runner
    from pycats.core.input import merge_frames
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
