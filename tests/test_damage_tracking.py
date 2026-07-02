"""Regression tests for cumulative Damage Given / Taken tracking (issue #98).

The win screen needs match-long damage totals, but ``fighter.percent`` is reset
to 0 on every death (it is the *current* damage). #98 adds separate accumulators
``damage_given`` / ``damage_taken`` that:

* add up the percent damage of each landed hit, crediting both the attacker
  (given) and the defender (taken);
* are **not** cleared by the per-life respawn reset, so they survive across
  deaths and only restart when a fresh Player is built for a new match;
* ignore shielded hits, which deal shield damage rather than percent.

The respawn-survival case is the one that matters most: it is exactly where a
naive "reuse percent" implementation would be wrong.
"""

import os
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402  (must follow the dummy-driver env setup)

from pycats.entities.player import Player  # noqa: E402

P1_KEYS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
               attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
P2_KEYS = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP,
               down=pygame.K_DOWN, attack=pygame.K_SLASH, special=pygame.K_PERIOD,
               shield=pygame.K_RSHIFT)


def _mk(char_name, keys, x):
    return Player(x, 300, keys, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name=char_name, facing_right=True)


def _hit(owner, damage):
    """A minimal attack satisfying Fighter.receive_hit's read surface."""
    return types.SimpleNamespace(
        owner=owner, damage=float(damage),
        base_knockback=0.0, knockback_growth=0.0, angle=0,
    )


def test_hit_credits_both_given_and_taken():
    attacker = _mk("P1", P1_KEYS, 100)
    defender = _mk("P2", P2_KEYS, 300)

    defender.fighter.receive_hit(_hit(attacker, 15))

    assert defender.fighter.damage_taken == 15.0
    assert attacker.fighter.damage_given == 15.0
    # The mirror identity the win screen relies on (1v1): given == opponent taken.
    assert attacker.fighter.damage_given == defender.fighter.damage_taken


def test_damage_survives_respawn():
    """The whole point of #98: percent resets on death, damage totals do not."""
    attacker = _mk("P1", P1_KEYS, 100)
    defender = _mk("P2", P2_KEYS, 300)

    defender.fighter.receive_hit(_hit(attacker, 40))
    assert defender.fighter.damage_taken == 40.0
    assert defender.fighter.percent == 40.0

    # Simulate the death/respawn: reset_to_spawn is what zeroes percent.
    defender.fighter.reset_to_spawn()
    assert defender.fighter.percent == 0.0, "respawn should clear current percent"
    assert defender.fighter.damage_taken == 40.0, "cumulative damage must survive the death"
    assert attacker.fighter.damage_given == 40.0

    # Damage from the next life keeps accumulating onto the match total.
    defender.fighter.receive_hit(_hit(attacker, 25))
    assert defender.fighter.damage_taken == 65.0
    assert attacker.fighter.damage_given == 65.0


def test_shielded_hit_is_not_counted():
    """A shielded hit deals shield damage, not percent, so it must not count."""
    attacker = _mk("P1", P1_KEYS, 100)
    defender = _mk("P2", P2_KEYS, 300)
    defender.fighter.shield_attempting = True  # raise the shield

    defender.fighter.receive_hit(_hit(attacker, 30))

    assert defender.fighter.damage_taken == 0.0, "shielded hit must not add to damage taken"
    assert attacker.fighter.damage_given == 0.0, "shielded hit must not add to damage given"
    assert defender.fighter.percent == 0.0, "shielded hit must not add percent"
