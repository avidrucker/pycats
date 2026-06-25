"""Single win-condition rule (#72 / D4).

The "who is out of lives → who wins" rule lives in one pure place
(`pycats/systems/win_condition.py`); both the headless `match_engine` and the
live `game.check_win_condition` delegate to it. These tests pin that rule.
"""
from pycats.systems.win_condition import winner_index, winner_loser


class _P:
    """Minimal fighter stand-in: only `.lives` matters to the rule."""
    def __init__(self, lives):
        self.lives = lives


# ---- winner_index: 0 none / 1 first / 2 second, by lives ----

def test_winner_index_no_winner_when_both_alive():
    assert winner_index((_P(3), _P(2))) == 0


def test_winner_index_second_wins_when_first_out_of_lives():
    assert winner_index((_P(0), _P(2))) == 2


def test_winner_index_first_wins_when_second_out_of_lives():
    assert winner_index((_P(1), _P(0))) == 1


# ---- winner_loser: (winner, loser) refs, or (None, None) ----

def test_winner_loser_returns_second_then_first_when_first_out():
    p1, p2 = _P(0), _P(2)
    assert winner_loser((p1, p2)) == (p2, p1)


def test_winner_loser_returns_first_then_second_when_second_out():
    p1, p2 = _P(1), _P(0)
    assert winner_loser((p1, p2)) == (p1, p2)


def test_winner_loser_none_when_both_alive():
    assert winner_loser((_P(3), _P(3))) == (None, None)


def test_winner_loser_none_when_players_not_initialized():
    assert winner_loser((None, None)) == (None, None)
    assert winner_loser((None, _P(3))) == (None, None)
