"""ROUNDS v1 stocks/lives match-setup hook — the `starting_lives` helper (#1202).

The `stocks` seam (ADR-0013 seam 10, the Phoenix card) can't ride the FighterData
patch `apply()` builds (#1196): `fighter.lives` is a match-level value, not a
FighterData field. `loadout.starting_lives(selection)` derives a fighter's starting
stock count from its drafted `stocks` cards, reusing the same compound-factors +
floor rule the apply-layer uses (`modifiers._effective`):

    starting_lives = round(INITIAL_LIVES × Π(1 + pct/100) + Σ add_n), floored at 1.
"""

from __future__ import annotations

from pycats.config.stage import INITIAL_LIVES
from pycats.loadout import PLACEHOLDER_SKIN, Selection, character_for, starting_lives
from pycats.loadout.cards import Card, load_cards


def _selection(*cards: Card) -> Selection:
    """A minimal Selection carrying the given drafted cards (skin irrelevant here)."""
    return Selection(character_for(None), PLACEHOLDER_SKIN, tuple(cards))


def _stocks_card(op: str, value: float, *, card_id: str = "synthetic") -> Card:
    return Card(id=card_id, name=card_id, deltas=[{"seam": "stocks", "op": op, "value": value}], stackable=True)


def test_no_cards_is_initial_lives():
    """The no-op default: a Selection with no cards starts at INITIAL_LIVES."""
    assert starting_lives(_selection()) == INITIAL_LIVES


def test_phoenix_adds_a_stock():
    """The real Phoenix card (stocks add_n +1) starts the fighter at INITIAL_LIVES + 1."""
    phoenix = load_cards()["phoenix"]
    assert starting_lives(_selection(phoenix)) == INITIAL_LIVES + 1


def test_two_stocks_add_n_stack():
    """Two stocks add_n cards sum: INITIAL_LIVES + 2."""
    assert starting_lives(_selection(_stocks_card("add_n", 1), _stocks_card("add_n", 1))) == INITIAL_LIVES + 2


def test_below_one_floors_at_one():
    """A stocks delta that would drive lives below 1 floors at 1 (a fighter needs a stock)."""
    assert starting_lives(_selection(_stocks_card("add_n", -100))) == 1


def test_mult_pct_compounds_over_base():
    """A stocks mult_pct scales the INITIAL_LIVES base (round(3 × 2.0) = 6)."""
    assert starting_lives(_selection(_stocks_card("mult_pct", 100))) == 6


def test_non_stocks_cards_do_not_change_lives():
    """A card touching only a non-stocks seam leaves starting lives at INITIAL_LIVES."""
    weight_card = Card(id="w", name="w", deltas=[{"seam": "weight", "op": "mult_pct", "value": 30}], stackable=True)
    assert starting_lives(_selection(weight_card)) == INITIAL_LIVES
