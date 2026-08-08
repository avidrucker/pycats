"""ROUNDS v1 stocks/lives match-setup hook (#1202).

The `stocks` seam (ADR-0013 seam 10, the Phoenix card) is the one drafted seam the
apply-layer (`modifiers.apply`, #1196) does NOT consume: `fighter.lives` is a
match-level value — the starting stock count — not a `FighterData` field, so it
cannot ride the `FighterData -> FighterData` patch. It needs its own match-setup
hook, and that is this module.

`starting_lives(selection)` derives a fighter's starting stock count from its
drafted `stocks` cards, reusing the apply-layer's `_effective` (`modifiers`) so the
math is the SAME compound-factors + floor rule ADR-0014 uses everywhere else:

    starting_lives = round(INITIAL_LIVES × Π(1 + pct_i/100) + Σ add_n_j), floored at 1.

- Base = INITIAL_LIVES (config/stage.py) — the fixed count every fighter starts at
  today. With no cards the product is 1 and the sum is 0, so the result is exactly
  INITIAL_LIVES → the no-op default is byte-identical to today.
- Int-contracted (lives are whole stocks → round) and floored at 1 (a fighter needs
  at least one stock to play).

Pure: imports no pygame / sim / UI (the loadout import-purity invariant). The setup
sites (BattleScreen, sim/runner) call this after `build_fighter` and set the result
on each Fighter's `lives`; ADR-0014's standalone-helper fork (owner ruling
2026-08-04) keeps this off `BuiltFighter` so card consumption for the match-level
seam is one explicit call the setup sites make.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..config.stage import INITIAL_LIVES
from .modifiers import _effective, card_to_modifiers

if TYPE_CHECKING:
    from .selection import Selection


def starting_lives(selection: Selection) -> int:
    """Return the fighter's starting stock count given its drafted cards.

    Only the `stocks` seam contributes; every other seam is a FighterData patch
    handled by `modifiers.apply` (#1196). No cards → INITIAL_LIVES.
    """
    stocks_mods = [m for card in selection.cards for m in card_to_modifiers(card) if m.seam == "stocks"]
    return _effective(INITIAL_LIVES, stocks_mods, rounds=True, floor=1)
