"""DEV 3 (#1208) — ROUNDS v1 Leech knob-fields + seam registration.

Spec: ADR-0019 (Leech card family) §2 · ADR-0020/#1178 (card-modifier catalog) ·
apply-layer ADR-0014/#1196. This slice adds three off-by-default `FighterData`
fields — `lifesteal_fraction` / `regen_rate` / `regen_interval` — and registers
them as seams (`modifiers._SCALAR_SEAMS`, `cards.LIVE_SEAMS`) so a card can patch
them. Nothing CONSUMES the fields yet: Vampire's on-hit lifesteal is DEV 5
(process_hits), Health Regen's per-interval tick is DEV 4 (systems/over_time.py).

The /decomplect ruling (#1208): three flat scalar fields (Option A), each floored
at 0 (no negative lifesteal/regen in v1); `regen_interval` is int-contracted
(round), floored at 0 (0 = off) — the divide/modulo guard is deferred to DEV 4.

Tests drive the public surface (apply / card_to_modifiers / load_cards) and use
synthetic cards for the leech deltas (the #1202 pattern — no cards.json entry is
authored here), so the base tuning values stay free to change.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from pycats.characters.roster import ARCHETYPE_ROSTER
from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData, load_fighter_data
from pycats.loadout.cards import LIVE_SEAMS, Card, _card_from_json, load_cards
from pycats.loadout.modifiers import Modifier, apply, card_to_modifiers

LEECH_SEAMS = ("lifesteal_fraction", "regen_rate", "regen_interval")


def _baseline() -> FighterData:
    """A minimal defaults FighterData (leech fields at 0) with one real move."""
    return FighterData(
        walk=1.1,
        dash=1.5,
        run=1.5,
        hurtbox=Hurtbox(circles=(Circle(0, -10, 20),)),
        moves={
            "attack": MoveData(
                name="jab",
                in_air=False,
                startup=3,
                active=2,
                recovery=6,
                hitboxes=(Hitbox(circle=Circle(30, 0, 10), damage=8.0, angle=45),),
            ),
        },
    )


def _leech_card(cid: str, seam: str, op: str, value) -> Card:
    return Card(id=cid, name=cid, deltas=[dict(seam=seam, op=op, value=value)], stackable=True)


# --- 1. Inert default -------------------------------------------------------


def test_leech_fields_default_off() -> None:
    fd = _baseline()
    assert fd.lifesteal_fraction == 0.0
    assert fd.regen_rate == 0.0
    assert fd.regen_interval == 0


def test_apply_no_cards_is_identity_with_leech_fields() -> None:
    # apply(fd, ()) returns the SAME object → sim goldens + render parity stay green.
    baseline = _baseline()
    assert apply(baseline, ()) is baseline


def test_default_selection_build_leaves_leech_off() -> None:
    from pycats.loadout.build_fighter import build_fighter
    from pycats.loadout.registry import SKINS, character_for
    from pycats.loadout.selection import Selection

    sel = Selection(character_for("nalio"), SKINS["red-blue"])
    built = build_fighter(sel).fighter_data
    assert (built.lifesteal_fraction, built.regen_rate, built.regen_interval) == (0.0, 0.0, 0)


# --- 2. Each seam patches only its field ------------------------------------


def test_card_to_modifiers_derives_leech_modifier() -> None:
    card = _leech_card("vampire", "lifesteal_fraction", "add_n", 0.3)
    assert card_to_modifiers(card) == [Modifier("lifesteal_fraction", "add_n", 0.3)]


def test_lifesteal_seam_patches_only_lifesteal_as_float() -> None:
    # add_n 0.3 onto a 0.0 float seam → 0.3, NOT rounded to 0.
    baseline = _baseline()
    result = apply(baseline, [_leech_card("vampire", "lifesteal_fraction", "add_n", 0.3)])
    assert result.lifesteal_fraction == pytest.approx(0.3)
    # untouched siblings
    assert result.regen_rate == 0.0
    assert result.regen_interval == 0
    assert result.weight == baseline.weight and result.move_speed == baseline.move_speed


def test_regen_rate_seam_patches_only_regen_rate_as_float() -> None:
    result = apply(_baseline(), [_leech_card("regen", "regen_rate", "add_n", 2.5)])
    assert result.regen_rate == pytest.approx(2.5)
    assert result.regen_rate != round(result.regen_rate)  # genuine float, not rounded
    assert result.lifesteal_fraction == 0.0 and result.regen_interval == 0


def test_regen_interval_seam_patches_only_interval_rounded_int() -> None:
    # int-contracted seam: add_n 30.4 → round → 30.
    result = apply(_baseline(), [_leech_card("regen", "regen_interval", "add_n", 30.4)])
    assert result.regen_interval == 30
    assert isinstance(result.regen_interval, int)
    assert result.lifesteal_fraction == 0.0 and result.regen_rate == 0.0


def test_apply_leech_does_not_mutate_baseline_and_returns_distinct_object() -> None:
    baseline = _baseline()
    before = replace(baseline)
    result = apply(baseline, [_leech_card("vampire", "lifesteal_fraction", "add_n", 0.3)])
    assert result is not baseline
    assert baseline == before  # in-place mutation would red this


# --- 3. Floor honored -------------------------------------------------------


def test_lifesteal_floor_clamps_at_zero() -> None:
    # A negative add_n cannot drive lifesteal below 0 (no negative lifesteal in v1).
    result = apply(_baseline(), [_leech_card("void", "lifesteal_fraction", "add_n", -0.5)])
    assert result.lifesteal_fraction == 0.0


def test_regen_rate_floor_clamps_at_zero() -> None:
    result = apply(_baseline(), [_leech_card("void", "regen_rate", "add_n", -3.0)])
    assert result.regen_rate == 0.0


def test_regen_interval_floor_clamps_at_zero() -> None:
    result = apply(_baseline(), [_leech_card("void", "regen_interval", "add_n", -10)])
    assert result.regen_interval == 0


# --- 4. Catalog legality ----------------------------------------------------


def test_leech_seams_are_registered_live() -> None:
    for seam in LEECH_SEAMS:
        assert seam in LIVE_SEAMS


def test_card_naming_leech_seam_is_catalog_legal() -> None:
    # A card whose delta names a leech seam passes _card_from_json (no raise).
    for seam in LEECH_SEAMS:
        card = _card_from_json(
            {
                "id": f"leech_{seam}",
                "name": seam,
                "deltas": [{"seam": seam, "op": "add_n", "value": 1}],
                "stackable": True,
            }
        )
        assert card.deltas[0]["seam"] == seam


# --- 5. Existing cats unchanged ---------------------------------------------


def test_shipped_cats_still_load_with_leech_off() -> None:
    # Every shipped <cat>.json omits the leech keys, so defaults absorb them; the
    # fighter still loads and its leech knobs read off (round-trip equality is
    # separately guarded by test_authored_value_ratchet / the JSON round-trip test).
    for name in ARCHETYPE_ROSTER:
        fd = load_fighter_data(name)
        assert (fd.lifesteal_fraction, fd.regen_rate, fd.regen_interval) == (0.0, 0.0, 0), name


def test_no_shipped_card_uses_a_leech_seam_yet() -> None:
    # The Vampire / Health Regen cards.json entries ride with their consuming DEV
    # (4 / 5); no shipped card patches a leech seam in this slice.
    for card in load_cards().values():
        for delta in card.deltas:
            assert delta["seam"] not in LEECH_SEAMS, card.id
