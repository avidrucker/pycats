"""Flattened lingering aerials — V1 has no sex-kick/juggle mechanic (#911, ruling #893).

The 5 two-window "lingering" aerials (`nalio.bair`/`uair`, `birky.nair`/`bair`/`uair`)
each carried a strong early "clean" hitbox overwritten by a weaker "late" one, and — under
the #204 per-window model — spawned a separate Attack per window, so a stationary target was
double-hit (#879/#890 Facet 3). The #893 game-designer ruling flattens each to ONE window
spanning the full active duration, with placeholder values = the average of the old clean+late
numeric fields (angle kept from the clean window where the two differed — never averaging the
Sakurai sentinel 361). These are `human-designer-temporary-placeholder-values-for-v1-only`;
the mechanic is restored post-V1 on top of #888 (B-full).

All assertions read the move through the public path (`load_fighter_data(<cat>).moves[<key>]`,
i.e. the shipped JSON), so they guard the runtime data, not just the Python oracle.

Able-to-fail: revert any move to its two-window form and
  - `test_flattened_move_is_one_window` reddens (two distinct windows / wrong averaged value),
  - `test_moveclock_spawns_one_window` reddens (the old data spawns TWO windows — the #890
    double-hit), and
  - `test_stationary_target_takes_one_hit_of_averaged_damage` reddens (wrong landed damage).
"""

from __future__ import annotations

import types
from pathlib import Path

import pygame
import pytest

from pycats.combat.data import Circle, FighterData, Hurtbox, load_fighter_data
from pycats.combat.move_clock import MoveClock
from pycats.entities.attack import Attack
from pycats.systems.hit_resolution import process_hits

# (cat, move-key, avg damage, avg bkb, avg kbg, angle, window, box-count) — the #893 ruling
# table (raw averages; angle = clean-window value where the two windows differed).
CASES = [
    ("nalio", "bair", 10.0, 31.5, 82.5, 28, (6, 17), 2),
    ("nalio", "uair", 10.5, 0.0, 100.0, 55, (4, 9), 2),
    ("birky", "nair", 10.5, 7.5, 100.0, 55, (3, 29), 1),
    ("birky", "bair", 12.0, 5.0, 100.0, 361, (6, 20), 2),
    ("birky", "uair", 13.5, 7.5, 102.5, 75, (10, 15), 2),
]
_IDS = [f"{cat}.{key}" for cat, key, *_ in CASES]

MARKER = "human-designer-temporary-placeholder-values-for-v1-only"


@pytest.mark.parametrize("cat,key,dmg,bkb,kbg,ang,win,boxes", CASES, ids=_IDS)
def test_flattened_move_is_one_window(cat, key, dmg, bkb, kbg, ang, win, boxes):
    """Exactly one temporal window over the full active span; every box carries the
    averaged placeholder values (angle = the clean window's where they differed)."""
    move = load_fighter_data(cat).moves[key]
    assert len(move.hitboxes) == boxes
    windows = {(hb.active_start, hb.active_end) for hb in move.hitboxes}
    assert windows == {win}, f"{cat}.{key} must be one window {win}, got {sorted(windows)}"
    for hb in move.hitboxes:
        assert hb.damage == dmg
        assert hb.base_knockback == bkb
        assert hb.knockback_growth == kbg
        assert hb.angle == ang


@pytest.mark.parametrize("cat,key,dmg,bkb,kbg,ang,win,boxes", CASES, ids=_IDS)
def test_moveclock_spawns_one_window(cat, key, dmg, bkb, kbg, ang, win, boxes):
    """Driven through MoveClock, the flattened move fires exactly ONE window — so the
    #204 model spawns ONE Attack, removing the #890 double-hit. The old two-window data
    fired two spawns here."""
    move = load_fighter_data(cat).moves[key]
    clk = MoveClock()
    clk.start(move)
    spawns = 0
    for _ in range(move.startup + move.active + move.recovery + 2):
        if clk.tick().spawn is not None:
            spawns += 1
    assert spawns == 1, f"{cat}.{key} should fire one window, fired {spawns}"


def _defender_at(cx, cy, r=40):
    """A minimal duck-typed defender whose single hurtbox circle sits at absolute
    (cx, cy) — rect top-left is (0, 0), so the circle's dx/dy ARE its absolute centre."""
    p = types.SimpleNamespace(
        rect=pygame.Rect(0, 0, 40, 60),
        facing_right=True,
        intangible=False,
        is_alive=True,
        fighter_data=FighterData(hurtbox=Hurtbox(circles=(Circle(dx=int(cx), dy=int(cy), r=r),)), moves={}),
        hits_received=0,
        last_damage=None,
    )

    def receive_hit(atk, is_crouching=False):
        p.hits_received += 1
        p.last_damage = atk.damage

    p.receive_hit = receive_hit
    p.record_hit_landed = lambda: None
    p.fighter = p
    return p


@pytest.mark.parametrize("cat,key,dmg,bkb,kbg,ang,win,boxes", CASES, ids=_IDS)
def test_stationary_target_takes_one_hit_of_averaged_damage(cat, key, dmg, bkb, kbg, ang, win, boxes):
    """A stationary overlapping target takes exactly ONE hit, of the averaged damage."""
    pygame.init()
    attacker = _defender_at(0, 0)  # owner (never self-hit); position irrelevant
    move = load_fighter_data(cat).moves[key]
    atk = Attack(attacker, hitboxes=move.hitboxes, in_air=True, lifetime=win[1] - win[0] + 1)
    px, py, _pr, _hb = atk.resolved[0]  # place the victim on the primary box
    defender = _defender_at(px, py)

    process_hits([attacker, defender], [atk])

    assert defender.hits_received == 1
    assert defender.last_damage == dmg


def test_flattened_moves_are_listed_in_the_breadcrumb_doc():
    """The post-V1 restore breadcrumb (docs/flattened-v1-aerials.md) carries the
    greppable `-v1-only` marker and lists every flattened move. #1141 retired the
    Python oracle where this list used to live as source comments (the JSON mirror
    carries no comments), so the greppable anchor moved to the doc. Able-to-fail:
    drop a move from the doc and its CASES row reds here."""
    doc = (Path(__file__).resolve().parents[1] / "docs" / "flattened-v1-aerials.md").read_text()
    assert MARKER in doc, "the breadcrumb doc must carry the -v1-only marker token"
    for cat, key, *_ in CASES:
        assert f"{cat}.{key}" in doc, f"{cat}.{key} must be listed in docs/flattened-v1-aerials.md"
