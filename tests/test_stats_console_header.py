"""#501 — the console stats header must source its labels from stats_table["header"],
not hardcode `P1`/`P2`, so named player profiles (epic #438/#441) show through to the
console the same way they already do on the win screen (win_screen.py:251).

Able-to-fail: monkeypatch get_match_summary to a summary carrying custom header labels
and assert they reach the console. With the old hardcoded `f"{'Stat':>18} {'P1'...}"`
line, the custom labels never appear (P1/P2 print instead), so this is red pre-fix.
"""
from pycats import stats_print


def _fake_summary(header):
    return {
        "winner_announcement": "WINNER!",
        "final_stocks": "Final stocks: ...",
        "restart_instruction": "Press R to restart",
        "stats_table": {
            "header": header,
            "rows": [{"stat_name": "KOs", "p1_value": "1", "p2_value": "2"}],
        },
    }


def test_console_header_uses_stats_table_header(monkeypatch, capsys):
    custom = {"stat_label": "Metric", "p1_label": "Alice", "p2_label": "Bob"}
    monkeypatch.setattr(stats_print, "get_match_summary", lambda *a, **k: _fake_summary(custom))

    stats_print.print_match_summary_to_console(winner=None, loser=None)
    out = capsys.readouterr().out

    # The table's labels reach the console — these appear ONLY when the header is
    # sourced from stats_table["header"]; the old hardcoded `P1/P2/Stat` line could
    # never print them, so this is the able-to-fail discriminator (red pre-fix).
    assert "Alice" in out and "Bob" in out and "Metric" in out
    # And precisely: the header ROW (not the "Game Statistics:" title) shows the custom
    # labels, not the old hardcoded P1/P2.
    header_row = next(ln for ln in out.splitlines() if "Alice" in ln)
    assert "Bob" in header_row and "Metric" in header_row
    assert "P1" not in header_row and "P2" not in header_row
