"""
pycats/loadout/cards.py

Purpose: the ROUNDS v1 card catalog — the `Card` model plus `load_cards()`, the
read-once loader over `characters/data/cards.json`.

Spec: docs/adr/0020-rounds-v1-card-modifier-catalog.md (ADR-0020). Seams:
docs/adr/0013-rounds-v1-fighter-seam-modifier-contract.md (ADR-0013).

Scope (DEV 1, #1190): data + loader only. A card is a `FighterData`/`MoveData`
patch expressed as a list of ADR-0014 modifiers; this module reads the authored
catalog and validates each delta's shape. It does NOT apply anything — the
apply-layer (`Modifier`, the `card -> [Modifier]` derivation, the functional
`apply(baseline, deltas)` at the `build_fighter` seam) is DEV 2 (ADR-0014).

Design notes:
- Magnitudes are by-feel v1 starting points (re-tuned under #1156), not sourced
  game values — an author choice, not a FOUND/TUNED citation.
- `load_cards()` reads the file once and caches (functools.cache); the returned
  dict is keyed by each card's `id` (draft + catalog lookups key on id, never the
  display `name`).
- The two Leech cards (Vampire, Health Regen) are absent by design: their seams
  (`lifesteal_fraction` / `regen_rate` / `regen_interval`, ADR-0013 seam 14) are
  not live yet, so they join cards.json under DEV 3 once those FighterData fields
  land. DEV 1 ships the nine stat cards.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

CARDS_PATH = Path(__file__).parent.parent / "characters" / "data" / "cards.json"

# The two fixed ADR-0014 ops. `mult_pct` = multiplicative ±%, `add_n` = additive ±N.
VALID_OPS: frozenset[str] = frozenset({"mult_pct", "add_n"})

# The live v1 seam vocabulary — ADR-0013's per-seam ledger, seams 1–10 plus the
# Leech family (14). A `seam` names the field a delta patches; the DEV 2 apply-layer
# maps each to its target. Deferred/out seams are deliberately absent so authoring one
# raises: frame data (11) & recovery (13) are DEFERRED, angle (12) is OUT. The novel
# "%-per-second" Leech family (14 — lifesteal_fraction/regen_rate/regen_interval) was
# registered by DEV 3 (#1208); its cards' consumers (Vampire DEV 5, Health Regen DEV 4)
# read the knobs, not this catalog.
LIVE_SEAMS: frozenset[str] = frozenset(
    {
        "weight",  # seam 1
        "jump_vel",  # seam 2
        "move_speed",  # seam 3 (speed family)
        "dash_speed",  # seam 3
        "run_speed",  # seam 3
        "max_fall_speed",  # seam 3
        "gravity",  # seam 4
        "max_jumps",  # seam 5
        "damage",  # seam 6 (Hitbox.damage)
        "reach",  # seam 7 (Hitbox reach / size)
        "body_size",  # seam 8 (stand_size / hurtbox)
        "base_knockback",  # seam 9
        "knockback_growth",  # seam 9
        "stocks",  # seam 10 (fighter.lives)
        "lifesteal_fraction",  # seam 14 (Leech: Vampire on-hit lifesteal — #1208)
        "regen_rate",  # seam 14 (Leech: Health Regen heal chunk — #1208)
        "regen_interval",  # seam 14 (Leech: Health Regen interval frames — #1208)
    }
)


class CardCatalogError(ValueError):
    """Raised when cards.json contains a malformed card or delta."""


@dataclass(frozen=True)
class Card:
    """One draftable ROUNDS card: a named bundle of fighter-seam deltas.

    Fields:
        id        — stable string key; draft + catalog lookups reference it.
        name      — human display label.
        deltas    — list of ADR-0014 modifiers, each a
                    {"seam": <LIVE_SEAMS>, "op": <VALID_OPS>, "value": number} dict.
        stackable — draw-filter flag (ADR-0020 §5): drawable iff
                    `stackable or not owned`. Metal is the sole v1 non-stacker.
    """

    id: str
    name: str
    deltas: list[dict]
    stackable: bool


def _card_from_json(raw: dict) -> Card:
    """Validate one raw card dict and build a Card (raises on a bad shape)."""
    try:
        card_id = raw["id"]
        name = raw["name"]
        deltas = raw["deltas"]
        stackable = raw["stackable"]
    except KeyError as exc:
        raise CardCatalogError(f"card missing required field: {exc}") from exc

    if not isinstance(stackable, bool):
        raise CardCatalogError(f"card {card_id!r}: stackable must be a bool")
    if not isinstance(deltas, list) or not deltas:
        raise CardCatalogError(f"card {card_id!r}: deltas must be a non-empty list")

    for delta in deltas:
        if set(delta) != {"seam", "op", "value"}:
            raise CardCatalogError(f"card {card_id!r}: delta must have exactly seam/op/value, got {sorted(delta)}")
        if delta["op"] not in VALID_OPS:
            raise CardCatalogError(
                f"card {card_id!r}: unknown op {delta['op']!r} (expected one of {sorted(VALID_OPS)})"
            )
        if delta["seam"] not in LIVE_SEAMS:
            raise CardCatalogError(f"card {card_id!r}: unknown seam {delta['seam']!r} — not a live ADR-0013 seam")

    return Card(id=card_id, name=name, deltas=deltas, stackable=stackable)


@cache
def load_cards() -> dict[str, Card]:
    """Read `cards.json` once into a cached `{id: Card}` catalog.

    Static data → read-once, no RNG, no per-round I/O (ADR-0020 §4). A duplicate
    id raises rather than one card shadowing another.
    """
    raw = json.loads(CARDS_PATH.read_text())
    catalog: dict[str, Card] = {}
    for entry in raw["cards"]:
        card = _card_from_json(entry)
        if card.id in catalog:
            raise CardCatalogError(f"duplicate card id {card.id!r} in cards.json")
        catalog[card.id] = card
    return catalog
