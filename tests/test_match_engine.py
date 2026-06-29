# tests/test_match_engine.py
from pycats.systems.match_engine import make_match_engine


class _P:
    def __init__(self, lives):
        self.lives = lives
        self.fighter = self


def _run(p1_lives, p2_lives):
    # ADR-0002 (#178): statechart is the only match-engine backend.
    players = [_P(p1_lives), _P(p2_lives)]
    eng = make_match_engine(players)
    eng.tick()
    return eng.phase, eng.winner


def test_in_play_when_both_alive():
    assert _run(3, 3) == ("in_play", 0)


def test_p1_out_means_p2_wins():
    assert _run(0, 2) == ("match_over", 2)


def test_p2_out_means_p1_wins():
    assert _run(1, 0) == ("match_over", 1)
