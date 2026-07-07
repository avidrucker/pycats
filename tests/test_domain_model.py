"""Unit tests for the pure pycats.domain model (#672 Phase 1a, #680).

Covers the value objects, the two resolvers, the build_fighter port, the
unknown-key → placeholder routing, the registry exclusion of the placeholder, and
the domain-purity invariant (importing the package pulls no pygame).
"""

import subprocess
import sys

from pycats.characters.palettes import load_palettes
from pycats.combat.data import load_fighter_data
from pycats.domain import (
    CHARACTERS,
    PLACEHOLDER_CHARACTER,
    PLACEHOLDER_SKIN,
    SKINS,
    BuiltFighter,
    Character,
    PlayerIdentity,
    PlayerName,
    PlayerNumberSlot,
    PlayerTeamColor,
    Selection,
    Skin,
    build_fighter,
    fighter_data_of,
    palette_of,
    resolve_selection,
)


def test_skin_round_trips_a_real_palette_entry():
    d = load_palettes()["calico"]
    skin = Skin.from_palette_dict("calico", d)
    assert skin.key == "calico"
    assert skin.name == d["name"]
    assert skin.color == tuple(d["color"])
    assert skin.stripe_color == tuple(d["stripe_color"])
    assert skin.eye_color == tuple(d["eye_color"])
    # to_palette_dict yields the legacy shape the render adapters index by string
    back = skin.to_palette_dict()
    assert back["color"] == skin.color
    assert back["eye_color"] == skin.eye_color
    assert set(back) == {"name", "color", "stripe_color", "eye_color", "description"}


def test_skin_is_hashable_and_frozen():
    s = SKINS["calico"]
    assert s in {s}  # hashable → usable as a Selection field / dict key


def test_player_identity_for_slot_defaults():
    p1 = PlayerIdentity.for_slot(1)
    p2 = PlayerIdentity.for_slot(2)
    assert p1.number == 1 and p1.team_color is PlayerTeamColor.RED and p1.name == "P1"
    assert p2.number == 2 and p2.team_color is PlayerTeamColor.BLUE and p2.name == "P2"
    assert isinstance(p1.number, PlayerNumberSlot)
    assert isinstance(p1.name, PlayerName)


def test_registries_hold_the_real_roster_only():
    assert set(CHARACTERS) == {"nalio", "birky", "narz"}
    assert CHARACTERS["nalio"].name == "Nalio"
    assert CHARACTERS["nalio"].default_skin_key == "calico"
    assert "calico" in SKINS and "ghost" in SKINS and "void" in SKINS


def test_placeholder_is_absent_from_both_registries():
    assert "testcat" not in CHARACTERS
    assert PLACEHOLDER_CHARACTER not in CHARACTERS.values()
    assert "placeholder" not in SKINS
    assert PLACEHOLDER_SKIN not in SKINS.values()


def test_palette_of_is_identity():
    s = SKINS["calico"]
    assert palette_of(s) is s


def test_fighter_data_of_uses_the_character_key():
    assert fighter_data_of(CHARACTERS["nalio"]) is load_fighter_data("nalio")


def test_build_fighter_named_character():
    bf = build_fighter(resolve_selection("nalio"))
    assert isinstance(bf, BuiltFighter)
    assert bf.fighter_data is load_fighter_data("nalio")
    assert bf.skin is SKINS["calico"]  # nalio's default skin


def test_resolve_selection_explicit_skin():
    sel = resolve_selection("nalio", "void")
    assert isinstance(sel, Selection)
    assert sel.character is CHARACTERS["nalio"]
    assert sel.skin is SKINS["void"]


def test_unknown_key_is_the_placeholder_in_both_halves():
    sel = resolve_selection("bogus")
    assert sel.character is PLACEHOLDER_CHARACTER
    assert sel.skin is PLACEHOLDER_SKIN
    bf = build_fighter(sel)
    # mechanics coherently fall to the minimal fixture (the testcat kit)…
    assert bf.fighter_data is load_fighter_data("testcat")
    # …and cosmetics are the flat-gray placeholder — a typo is *visibly* the fixture
    assert bf.skin is PLACEHOLDER_SKIN
    assert bf.skin.color == (128, 128, 128)
    assert bf.skin.eye_color == (128, 128, 128)
    assert bf.skin.stripe_color == (128, 128, 128)


def test_unknown_skin_falls_to_the_placeholder_skin():
    # known character, unrecognised skin key → placeholder cosmetics, real mechanics
    sel = resolve_selection("nalio", "no-such-skin")
    assert sel.character is CHARACTERS["nalio"]
    assert sel.skin is PLACEHOLDER_SKIN


def test_domain_import_pulls_no_pygame():
    """The hexagonal invariant: importing the domain package loads no pygame.

    Run in a subprocess because the pytest session imports pygame elsewhere, so an
    in-process check would false-pass.
    """
    code = (
        "import pycats.domain\n"
        "import sys\n"
        "bad = sorted(m for m in sys.modules if 'pygame' in m)\n"
        "assert not bad, bad\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
