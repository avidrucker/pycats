# tests/test_match_engine.py
from pycats.systems.match_engine import make_match_engine


class _P:
    def __init__(self, lives):
        self.lives = lives
        self.fighter = self


def _run(backend, p1_lives, p2_lives):
    players = [_P(p1_lives), _P(p2_lives)]
    eng = make_match_engine(players, backend)
    eng.tick()
    return eng.phase, eng.winner


def test_in_play_when_both_alive():
    for backend in ("legacy", "statechart"):
        assert _run(backend, 3, 3) == ("in_play", 0)


def test_p1_out_means_p2_wins():
    for backend in ("legacy", "statechart"):
        assert _run(backend, 0, 2) == ("match_over", 2)


def test_p2_out_means_p1_wins():
    for backend in ("legacy", "statechart"):
        assert _run(backend, 1, 0) == ("match_over", 1)
