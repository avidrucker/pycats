"""Regression tests for the win-screen stats table (issue #11).

#11 added end-of-match **KOs** and **Falls** rows, computed from data the
fighters already track (lives + suicides, against ``INITIAL_LIVES``). The two
key contracts these tests pin:

* KOs scored == stocks taken *off the opponent*, i.e. excluding the opponent's
  self-destructs; Falls == times KO'd *by the opponent*, also excluding own SDs.
  (So a naive "deaths = INITIAL_LIVES - lives" implementation that double-counts
  SDs is red against these tests.)
* By construction P1's KOs equal P2's Falls and vice-versa.

The rows are computed by :func:`pycats.stats_print.format_stats_table`, which
only reads ``char_name``, ``lives``, ``suicides``, ``hits_landed`` and
``attacks_made`` off each player — so a tiny stand-in avoids constructing a real
pygame-backed Player.
"""

from pycats import stats_print
from pycats.config import INITIAL_LIVES


class _FakePlayer:
    def __init__(self, char_name, lives, suicides, hits_landed=0, attacks_made=0,
                 damage_given=0.0, damage_taken=0.0):
        self.char_name = char_name
        self.lives = lives
        self.suicides = suicides
        self.hits_landed = hits_landed
        self.attacks_made = attacks_made
        self.damage_given = damage_given
        self.damage_taken = damage_taken
        self.fighter = self


def _rows_by_name(winner, loser):
    table = stats_print.format_stats_table(winner, loser)
    return {row["stat_name"]: row for row in table["rows"]}


def test_kos_and_falls_present():
    """The table grows KOs and Falls rows (the #11 deliverable)."""
    p1 = _FakePlayer("P1", lives=INITIAL_LIVES, suicides=0)
    p2 = _FakePlayer("P2", lives=0, suicides=0)
    rows = _rows_by_name(winner=p1, loser=p2)
    assert "KOs" in rows, "win screen is missing the KOs row"
    assert "Falls" in rows, "win screen is missing the Falls row"


def test_clean_sweep_no_suicides():
    """P1 wins 3-0 with no SDs: P1 has 3 KOs / 0 Falls, P2 the mirror."""
    p1 = _FakePlayer("P1", lives=INITIAL_LIVES, suicides=0)  # never died
    p2 = _FakePlayer("P2", lives=0, suicides=0)  # lost all 3 stocks to P1
    rows = _rows_by_name(winner=p1, loser=p2)

    assert rows["KOs"]["p1_value"] == str(INITIAL_LIVES)  # 3
    assert rows["KOs"]["p2_value"] == "0"
    assert rows["Falls"]["p1_value"] == "0"
    assert rows["Falls"]["p2_value"] == str(INITIAL_LIVES)  # 3


def test_suicides_excluded_from_kos_and_falls():
    """An SD is neither a KO for the opponent nor an opponent-inflicted Fall.

    P2 lost all 3 stocks but one was a self-destruct, so P1 only KO'd P2 twice
    and P2 only *fell* (to P1) twice. The lone SD still shows in the separate
    Suicides row. This is the discriminator that fails a total-deaths impl.
    """
    p1 = _FakePlayer("P1", lives=2, suicides=0)  # P1 died once (to P2)
    p2 = _FakePlayer("P2", lives=0, suicides=1)  # P2 died 3x, one self-inflicted
    rows = _rows_by_name(winner=p1, loser=p2)

    assert rows["KOs"]["p1_value"] == "2", "P1's KOs must exclude P2's suicide"
    assert rows["Falls"]["p2_value"] == "2", "P2's Falls must exclude its own SD"
    assert rows["Suicides"]["p2_value"] == "1", "the SD still belongs in Suicides"

    # P2 KO'd P1 once; P1 fell once. The KOs/Falls mirror identity must hold.
    assert rows["KOs"]["p2_value"] == rows["Falls"]["p1_value"] == "1"


def test_damage_given_taken_rows():
    """Damage Given/Taken render as whole-percent values (issue #98).

    In a 1v1 a player's Damage Given equals the opponent's Damage Taken, so the
    rows must mirror across columns; values are formatted as integer percents.
    """
    p1 = _FakePlayer("P1", lives=2, suicides=0,
                     damage_given=312.0, damage_taken=188.0)
    p2 = _FakePlayer("P2", lives=0, suicides=1,
                     damage_given=188.0, damage_taken=312.0)
    rows = _rows_by_name(winner=p1, loser=p2)

    assert "Damage Given" in rows and "Damage Taken" in rows
    assert rows["Damage Given"]["p1_value"] == "312%"
    assert rows["Damage Taken"]["p2_value"] == "312%"
    # given(P1) == taken(P2) and given(P2) == taken(P1)
    assert rows["Damage Given"]["p1_value"] == rows["Damage Taken"]["p2_value"]
    assert rows["Damage Given"]["p2_value"] == rows["Damage Taken"]["p1_value"] == "188%"
