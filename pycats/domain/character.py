"""Character — a fighter's identity + mechanics reference (#672 domain, spec §1).

Pure: imports no pygame / sim / UI. A Character is a small identity value — the
mechanics key that ``combat.data.load_fighter_data`` understands, a display name,
and a *reference* to a default Skin. The actual ``FighterData`` is resolved lazily
by ``domain.resolvers.fighter_data_of`` — it is deliberately NOT embedded here, so
this value stays pure and cheap.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Character:
    """A selectable fighter identity. Today's "archetype"."""

    key: str  # mechanics key load_fighter_data knows: "nalio"/"birky"/"narz"/"testcat"
    name: str  # display name, e.g. "Nalio"
    default_skin_key: str  # a Skin.key — the skin worn until a player cycles it (#650)
