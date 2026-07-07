"""watch.py CLI roster — must accept every implemented archetype (#272).

`watch.py`'s `--p1-char`/`--p2-char` choices come from `watch.CHARACTERS`, which must
stay synced to the real selectable roster (`pycats.characters.roster.ARCHETYPE_ROSTER`)
so a newly-built archetype (e.g. Birky #228) can't be silently left unselectable. Was
a hardcoded `["nalio"]` that drifted.
"""
import watch
from pycats.characters.roster import ARCHETYPE_ROSTER


def test_watch_characters_cover_the_archetype_roster():
    # Anti-drift (#272): every implemented archetype stays selectable in the CLI, so a
    # newly-built one can't be silently left out. #648 relaxed exact-equality to a
    # superset check because the sim CLI (a dev surface) also accepts the `testcat`
    # fixture — the only non-archetype entry, and never in the player-facing roster.
    assert all(a in watch.CHARACTERS for a in ARCHETYPE_ROSTER)
    assert set(watch.CHARACTERS) - set(ARCHETYPE_ROSTER) == {"testcat"}
    assert "testcat" not in ARCHETYPE_ROSTER


def test_watch_accepts_birky_and_nalio():
    assert "birky" in watch.CHARACTERS
    assert "nalio" in watch.CHARACTERS
