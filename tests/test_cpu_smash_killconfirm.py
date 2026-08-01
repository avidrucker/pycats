"""CPU kill-confirm smash (#714, child of #231).

The `AttackerController` gains its first smash: at/above a kill-percent threshold and
in melee range, a smash-enabled leveled bot throws a fully-charged **forward-smash**
instead of its low-knockback tilt/jab — the finisher #706 surfaced as missing (a Lv9
chase bot racked idle Nalio to ~18% and never KO'd).

V1 policy (all deliberately provisional, marked in-code / see #915, #916):
  - trigger: flat SMASH_KILL_PERCENT for every level (PLACEHOLDER_MECHANIC_DECISION);
  - charge: always full (TEMPORARY_MECHANIC_DECISION);
  - levels: Lv5+ (placeholder cut);
  - direction: forward-smash only (up/down deferred to #916).

Golden-safety: the branch is gated on `level is not None` AND `"smashes" in enabled_moves`,
so the level-less default and Lv1-4 never evaluate it (byte-identical, no extra rng draw).
"""

import random

import pygame

from pycats.core.input import merge_frames
from pycats.sim import runner
from pycats.sim.controllers import SMASH_KILL_PERCENT, AttackerController

# indices into the snapshot player tuple (see sim/runner.snapshot)
_PERCENT, _LIVES = 7, 9


def _adjacent_grounded(p1, p2, gap=30):
    """Stand P2 just within P1's melee reach, both grounded and level — the geometry
    the in-range attack gate wants (standoff-margin <= adx <= melee_range, |dy| < 60)."""
    p2.rect.centerx = p1.rect.centerx + gap
    p2.rect.centery = p1.rect.centery
    p1.fighter.on_ground = True
    p2.fighter.on_ground = True


def _drive(level, target_percent, frames=30, seed=0, gap=30):
    """Build a nalio-vs-nalio pair, park P2 in melee range at `target_percent`, and run
    a level-`level` AttackerController on P1 (P2 idle) for `frames`. Return the set of
    P1 control keys ever *pressed* across those frames."""
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    _adjacent_grounded(p1, p2, gap)
    p2.fighter.percent = target_percent
    ctrl = AttackerController(attacker_num=1, level=level, rng=random.Random(seed))
    pressed = set()
    for f in range(frames):
        fi = ctrl(p1, p2, f)
        pressed |= set(fi.pressed)
        # keep P2 pinned + damaged so the geometry/threshold hold across the window
        _adjacent_grounded(p1, p2, gap)
        p2.fighter.percent = target_percent
    return pressed, p1.controls


def test_lv5_bot_presses_smash_at_kill_percent():
    """Able-to-fail: at/above the kill threshold, a Lv5 (smash-enabled) bot presses the
    `smash` key. Without the kill-confirm branch it only ever presses `attack`."""
    pressed, controls = _drive(level=5, target_percent=SMASH_KILL_PERCENT + 20)
    assert controls["smash"] in pressed, (
        f"a Lv5 bot at {SMASH_KILL_PERCENT + 20:.0f}% (>= kill {SMASH_KILL_PERCENT:.0f}%) "
        f"must press smash; pressed={sorted(pressed)}"
    )


def test_bot_does_not_smash_below_kill_percent():
    """Below the threshold the bot commits its normal attack, never the smash — the
    kill-confirm is a finisher, not the default poke."""
    pressed, controls = _drive(level=5, target_percent=SMASH_KILL_PERCENT - 40)
    assert controls["smash"] not in pressed, (
        f"a Lv5 bot below the kill threshold must not smash; pressed={sorted(pressed)}"
    )
    assert controls["attack"] in pressed, "the bot should still throw its normal attack below kill %"


def test_low_and_default_levels_never_smash():
    """Golden-safety: Lv1 (no `smashes`) and the level-less default never press smash,
    even parked at a lethal percent — the branch is gated off for them."""
    lv1_pressed, lv1_controls = _drive(level=1, target_percent=SMASH_KILL_PERCENT + 50, frames=60)
    assert lv1_controls["smash"] not in lv1_pressed, "Lv1 (no smashes) must never press smash"

    p1, p2, _ = runner.build_players(p1_char="nalio", p2_char="nalio")
    _adjacent_grounded(p1, p2)
    p2.fighter.percent = SMASH_KILL_PERCENT + 50
    ctrl = AttackerController(attacker_num=1, rng=random.Random(0))  # level=None default
    default_pressed = set()
    for f in range(60):
        fi = ctrl(p1, p2, f)
        default_pressed |= set(fi.pressed)
        _adjacent_grounded(p1, p2)
        p2.fighter.percent = SMASH_KILL_PERCENT + 50
    assert p1.controls["smash"] not in default_pressed, "the level-less default must never press smash (golden-safe)"


def test_leveled_bot_smashes_and_kos_a_high_percent_opponent():
    """Acceptance: a smash-enabled leveled bot commits a smash AND converts a KO on an
    idle, high-percent opponent within a short window. Full-charge fsmash off the side
    (#588). Nalio attacker vs an idle Birky (light/floaty) primed near lethal."""
    plats = runner.build_stage()
    ledges = runner.ledges_from_platforms(plats)
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="birky")
    from pycats.systems import combat

    attacks = pygame.sprite.Group()
    empty = merge_frames([])  # no-input frame
    # Let both fighters fall from their spawn and settle onto the platform, so the bot
    # is genuinely grounded at the decision frame (the kill-confirm is ground-only).
    for _ in range(40):
        for p in players:
            p.update(empty, plats, attacks, ledges)
    assert p1.fighter.on_ground and p2.fighter.on_ground, "fighters failed to settle on the ground"
    # Park the idle Birky in melee range at a lethal percent, both grounded and level.
    p2.rect.centerx = p1.rect.centerx + 34
    p2.rect.bottom = p1.rect.bottom
    p2.fighter.percent = 140.0
    ctrl = AttackerController(attacker_num=1, level=9, rng=random.Random(0))
    lives0 = p2.fighter.lives
    smashed = False
    ko = False

    for f in range(400):
        fi = ctrl(p1, p2, f, attacks, ledges)
        if p1.controls["smash"] in fi.pressed:
            smashed = True
        for p in players:
            p.update(fi, plats, attacks, ledges)
        attacks.update(plats)
        combat.process_hits(players, attacks)
        if p2.fighter.lives < lives0:
            ko = True
            break

    assert smashed, "the Lv9 bot never pressed smash against a lethal-percent target"
    assert ko, f"the bot's smash did not convert a KO (P2 lives stayed {p2.fighter.lives})"
