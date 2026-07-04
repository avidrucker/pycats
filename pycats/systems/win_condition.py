# pycats/systems/win_condition.py
"""The single win-condition rule: who has won a match, by lives.

One source of truth shared by the headless `match_engine` (via `winner_index`)
and the live `game.check_win_condition` (via `winner_loser`). Pure — depends only
on each player's `.lives`.
"""

from __future__ import annotations


def winner_index(players) -> int:
    """0 = no winner yet; 1 = players[0] wins; 2 = players[1] wins (by lives).

    players[0] is checked first, so a same-frame double-out resolves to 2
    (players[1] wins) — preserving the historical match_engine/game behaviour.
    """
    p1, p2 = players
    if p1.fighter.lives <= 0:
        return 2
    if p2.fighter.lives <= 0:
        return 1
    return 0


def winner_loser(players):
    """`(winner, loser)` player refs, or `(None, None)` when there is no winner
    yet or a player is not initialised (falsy)."""
    if not all(players):
        return None, None
    w = winner_index(players)
    if w == 1:
        return players[0], players[1]
    if w == 2:
        return players[1], players[0]
    return None, None
