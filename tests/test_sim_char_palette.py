"""#648: the sim CLI colours players from the char key via `palette_for` (dev/debug
visual), so a chosen character renders in its own cosmetic palette — and `testcat`'s
gray placeholder (#636) is inspectable. The no-key default stays byte-identical to the
hardcoded calico/tabby so the sim goldens (#244 contract) are untouched."""

import pygame

from pycats.characters.roster import ARCHETYPE_ROSTER, palette_for
from pycats.config import CAT_CHARACTERS
from pycats.sim.runner import build_players

if not pygame.get_init():
    pygame.init()


def test_testcat_p1_renders_gray_placeholder():
    # Able-to-fail: today build_players hardcodes P1 = calico (orange). With the fix,
    # a testcat key colours P1 from palette_for("testcat") = the #636 achromatic gray.
    p1, _p2, _ = build_players("testcat")
    assert p1.char_color == tuple(palette_for("testcat")["color"])
    assert p1.char_color == (128, 128, 128)  # the #636 mid-gray placeholder, not calico orange
    assert p1.char_color != tuple(CAT_CHARACTERS["calico"]["color"])


def test_no_key_default_is_byte_identical_calico_tabby():
    # Golden-safe (#244): the no-arg path keeps today's exact hardcoded skins.
    p1, p2, _ = build_players()
    assert p1.char_color == tuple(CAT_CHARACTERS["calico"]["color"])
    assert p1.eye_color == tuple(CAT_CHARACTERS["calico"]["eye_color"])
    assert p2.char_color == tuple(CAT_CHARACTERS["tabby"]["color"])
    assert p2.eye_color == tuple(CAT_CHARACTERS["tabby"]["eye_color"])


def test_named_archetype_colours_from_its_own_palette():
    # A named key colours P1 from its palette (matches battle_screen), not hardcoded calico.
    p1, _p2, _ = build_players("narz")
    assert p1.char_color == tuple(palette_for("narz")["color"])


def test_same_character_mirror_defaults_to_distinct_skins():
    # #718: a Nalio-vs-Nalio mirror must NOT render two identical cats. P2's skin, when it
    # would collide with P1's, defaults to the next available skin in Nalio's pool
    # (via the #755 domain layer). Able-to-fail: today both resolve to palette_for("nalio").
    p1, p2, _ = build_players("nalio", "nalio")
    assert p1.char_color != p2.char_color


def test_testcat_is_not_in_player_facing_roster():
    # #648 out-of-scope guard: testcat stays a dev fixture, never in the char-select grid.
    assert "testcat" not in ARCHETYPE_ROSTER


def test_watch_cli_allows_testcat_but_roster_does_not():
    # #648: the sim CLI (dev surface) accepts --p1-char testcat; the roster still doesn't.
    import watch

    assert "testcat" in watch.CHARACTERS
    assert all(a in watch.CHARACTERS for a in ARCHETYPE_ROSTER)
    assert "testcat" not in ARCHETYPE_ROSTER
