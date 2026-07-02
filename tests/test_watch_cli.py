"""watch.py CLI roster — must accept every implemented archetype (#272).

`watch.py`'s `--p1-char`/`--p2-char` choices come from `watch.CHARACTERS`, which must
stay synced to the real selectable roster (`pycats.characters.roster.ARCHETYPE_ROSTER`)
so a newly-built archetype (e.g. Birky #228) can't be silently left unselectable. Was
a hardcoded `["nalio"]` that drifted.
"""
import watch
from pycats.characters.roster import ARCHETYPE_ROSTER


def test_watch_characters_match_the_archetype_roster():
    # pinned to the source of truth so the CLI list can't drift again
    assert tuple(watch.CHARACTERS) == ARCHETYPE_ROSTER


def test_watch_accepts_birky_and_nalio():
    assert "birky" in watch.CHARACTERS
    assert "nalio" in watch.CHARACTERS
