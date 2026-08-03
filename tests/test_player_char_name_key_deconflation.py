"""
tests/test_player_char_name_key_deconflation.py

#894 (child of #792, prereq for #887): `Player.char_name` is the seat's DISPLAY
label, resolved SEPARATELY from the `load_fighter_data` key. A char_name that
names a known character loads that character; any other label loads the default
kit ("testcat"), while char_name stays the label. This lets ~28 test fixtures
across 21 files pass arbitrary labels ("Cat", "P", "AirCat", …) without the label
being read as a fighter key — the seam #887 relies on to raise on an unknown key.

Why the key-argument assertions: on today's main `load_fighter_data` still has a
catch-all, so a raw label and its resolved key hydrate to the same (default) data
— the two are indistinguishable by the returned FighterData alone. The observable
contract this slice adds is *which key Player loads by*, so the able-to-fail
guards assert the key handed to `load_fighter_data`. They become behavioral teeth
once #887 removes the catch-all (a raw label would then raise).
"""

from helpers import mk_player

import pycats.entities.player as player_mod
from pycats.combat.data import load_fighter_data


def _record_key(monkeypatch):
    """Patch load_fighter_data as seen by Player to record the key it is called
    with (returning the real default kit so construction still succeeds)."""
    seen = []

    def spy(key):
        seen.append(key)
        return load_fighter_data("testcat")

    monkeypatch.setattr(player_mod, "load_fighter_data", spy)
    return seen


def test_non_key_char_name_resolves_to_the_default_key(monkeypatch):
    # A throwaway display label is NOT used as the load key: Player resolves it to
    # "testcat" (the default kit). Able-to-fail: drop the de-conflation and Player
    # loads by the raw label "Cat", so `seen == ["Cat"]` and this reddens.
    seen = _record_key(monkeypatch)
    mk_player(char_name="Cat")
    assert seen == ["testcat"]


def test_known_char_name_is_used_verbatim_as_the_key(monkeypatch):
    # A char_name that names a known character IS the load key. Able-to-fail: a
    # de-conflation that routes everything to "testcat" would give `seen ==
    # ["testcat"]` and redden here.
    seen = _record_key(monkeypatch)
    mk_player(char_name="nalio")
    assert seen == ["nalio"]


def test_char_name_is_preserved_as_the_display_label():
    # The de-conflation touches only the load key — char_name stays the label,
    # whatever it is (win-attribution / PlayerName read it downstream).
    assert mk_player(char_name="Cat").char_name == "Cat"


def test_non_key_char_name_loads_the_default_kit():
    # End-to-end (no patch): a non-key label yields the default/testcat kit by
    # value — the data every such fixture got before, via the removed catch-all.
    assert mk_player(char_name="Cat").fighter_data == load_fighter_data("testcat")


def test_injected_fighter_data_wins_over_the_label():
    # The live/sim path injects a resolved fighter_data; it is used verbatim,
    # regardless of char_name, and no key resolution happens.
    nalio = load_fighter_data("nalio")
    assert mk_player(char_name="P1", fighter_data=nalio).fighter_data is nalio
