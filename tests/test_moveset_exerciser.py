"""Moveset exerciser regression guard (#1203).

`pycats.sim.moveset_exerciser` drives every canonical move key (from
`move_select`, the single source) through the real input seam
(`Player.handle_actions`) for each roster character and reports which canonical
moves never activate. These tests pin:

  - the observed missing set == a committed expected-gaps baseline (NOT
    zero-missing: the V1 kits are intentionally partial, #1058/#1199), able to
    fail in BOTH directions — a move regressing present->missing reddens, and a
    newly-authored move reddens until the baseline is trimmed;
  - detection is DRIVEN, not a static `.moves`-dict read: unwiring a wired move
    makes it appear missing, and a present move actually starts on the clock.
"""

from __future__ import annotations

import copy

import pygame as pg

from pycats.characters.roster import ARCHETYPE_ROSTER
from pycats.combat.data import load_fighter_data
from pycats.combat.move_select import select_move_key
from pycats.sim import moveset_exerciser as mx

# Expected-gaps baseline — the canonical moves each V1 kit does not yet define
# (#1058 Narz specials in progress; the other cats' B-specials are unauthored).
# A move dropping out of a kit adds an entry here; a newly-wired move removes one.
EXPECTED_GAPS = {
    "nalio": {"down_b", "dtilt", "side_b"},
    "birky": {"down_b", "dtilt", "neutral_b", "side_b"},
    "narz": {"side_b"},
    "gnok": {"down_b", "neutral_b", "side_b", "up_b"},
}


def test_canonical_contexts_cover_the_full_move_select_catalog():
    """The exerciser's key list is derived from `move_select` (one source, no
    hand-copied second catalog) — every key the seam can select is covered."""
    seam_keys = set()
    for on_ground in (True, False):
        for direction in ("neutral", "up", "down", "forward", "back"):
            seam_keys.add(select_move_key(direction, on_ground, is_special=False, is_smash=False))
            seam_keys.add(select_move_key(direction, on_ground, is_special=True, is_smash=False))
            if on_ground:
                seam_keys.add(select_move_key(direction, on_ground, is_special=False, is_smash=True))
    assert set(mx.canonical_contexts()) == seam_keys


def test_missing_matches_expected_gaps_baseline():
    """The regression guard: driven-missing set == committed baseline, per cat."""
    for name in ARCHETYPE_ROSTER:
        assert set(mx.missing_moves(name)) == EXPECTED_GAPS[name], name


def test_roster_is_covered():
    results = mx.exercise()
    assert set(results) == set(ARCHETYPE_ROSTER)


def test_present_move_activates_through_the_seam():
    """A wired move (nalio jab) is NOT reported missing — and probing it returns
    True, i.e. the move actually started via the driven seam."""
    assert "jab" not in mx.missing_moves("nalio")
    assert mx.probe_move("nalio", "jab", fighter_data=load_fighter_data("nalio")) is True


def test_counter_special_counts_as_present():
    """Narz's down-B is a counter — it arms a stance, the MoveClock never runs it
    — so a clock-only check would wrongly flag it missing. It must count present."""
    assert "down_b" not in mx.missing_moves("narz")


def test_unwiring_a_move_makes_it_appear_missing():
    """Detection is driven, not a static baseline read: remove jab from a loaded
    kit and it now shows up as missing (able-to-fail)."""
    fd = load_fighter_data("nalio")
    fd = copy.deepcopy(fd)
    del fd.moves["jab"]
    assert mx.probe_move("nalio", "jab", fighter_data=fd) is False
    assert "jab" in mx.missing_moves("nalio", fighter_data=fd)


def test_report_names_each_missing_move():
    report = mx.format_report({"narz": ["neutral_b", "side_b"]})
    assert "narz" in report
    assert "neutral_b" in report
    assert "side_b" in report


def test_main_runs_headless_and_returns_zero(capsys):
    pg.display.quit()  # ensure no display dependency
    code = mx.main([])
    out = capsys.readouterr().out
    assert code == 0
    for name in ARCHETYPE_ROSTER:
        assert name in out
