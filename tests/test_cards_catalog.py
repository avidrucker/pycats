"""DEV 1 (#1190) — ROUNDS v1 card catalog: cards.json + load_cards()/Card model.

Spec: docs/adr/0020-rounds-v1-card-modifier-catalog.md (ADR-0020); seams from
ADR-0013 (0013-rounds-v1-fighter-seam-modifier-contract.md).

These tests exercise the catalog through its public surface — load_cards() and the
Card dataclass — never the file bytes directly. DEV 1 is data + loader only: the
apply-layer (Modifier / card -> [Modifier] / build_fighter wiring) is DEV 2 and is
out of scope here.
"""

from __future__ import annotations

import pytest

from pycats.loadout.cards import Card, load_cards

# The nine v1 stat starter cards (ADR-0020 §2; the two Leech cards wait for DEV 3,
# which adds their FighterData fields / seams).
STAT_CARD_IDS = {
    "phoenix",
    "chase",
    "springs",
    "compact",
    "glass_cannon",
    "metal",
    "bruiser",
    "long_arms",
    "floaty",
}

VALID_OPS = {"mult_pct", "add_n"}


def test_load_cards_returns_dict_keyed_by_id():
    cards = load_cards()
    assert isinstance(cards, dict)
    assert cards, "catalog must not be empty"
    for card_id, card in cards.items():
        assert isinstance(card, Card)
        # The dict key is the card's own id — draft/catalog lookups key on id.
        assert card.id == card_id


def test_card_exposes_id_name_deltas_stackable():
    card = load_cards()["glass_cannon"]
    assert card.id == "glass_cannon"
    assert card.name == "Glass Cannon"
    assert isinstance(card.deltas, list) and card.deltas
    assert isinstance(card.stackable, bool)
    for delta in card.deltas:
        assert set(delta) == {"seam", "op", "value"}


def test_all_nine_stat_cards_present():
    assert STAT_CARD_IDS <= set(load_cards())


def test_every_op_is_a_fixed_adr0014_op():
    for card in load_cards().values():
        for delta in card.deltas:
            assert delta["op"] in VALID_OPS


def test_every_seam_is_a_live_adr0013_seam():
    from pycats.loadout.cards import LIVE_SEAMS

    for card in load_cards().values():
        for delta in card.deltas:
            assert delta["seam"] in LIVE_SEAMS


def test_metal_is_sole_non_stacker():
    cards = load_cards()
    assert cards["metal"].stackable is False
    for card_id, card in cards.items():
        if card_id != "metal":
            assert card.stackable is True, f"{card_id} should be stackable"


def test_catalog_loaded_once_cached():
    assert load_cards() is load_cards()


# --- validation guards: a malformed card raises (able-to-fail on the raise path) ---


def test_unknown_op_raises():
    from pycats.loadout.cards import CardCatalogError, _card_from_json

    bad = {
        "id": "bogus",
        "name": "Bogus",
        "deltas": [{"seam": "weight", "op": "divide", "value": 2}],
        "stackable": True,
    }
    with pytest.raises(CardCatalogError):
        _card_from_json(bad)


def test_unknown_seam_raises():
    from pycats.loadout.cards import CardCatalogError, _card_from_json

    # `regen_rate` is ADR-0013 seam 14 (novel %-per-second) — not live until DEV 3.
    bad = {
        "id": "premature_leech",
        "name": "Premature Leech",
        "deltas": [{"seam": "regen_rate", "op": "add_n", "value": 2}],
        "stackable": True,
    }
    with pytest.raises(CardCatalogError):
        _card_from_json(bad)


def test_malformed_delta_shape_raises():
    from pycats.loadout.cards import CardCatalogError, _card_from_json

    bad = {
        "id": "bogus",
        "name": "Bogus",
        "deltas": [{"seam": "weight", "op": "add_n"}],  # missing "value"
        "stackable": True,
    }
    with pytest.raises(CardCatalogError):
        _card_from_json(bad)
