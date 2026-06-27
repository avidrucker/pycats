# tests/test_og_skins.py
"""Part 1 of the alt-skin epic (#127, child #131).

The six OG colour-skins (ghost/calico/tabby/void/tiger/bengal) are archived into
a single source module, `pycats.characters.og_skins`, and `config.CAT_CHARACTERS`
re-exports it. These tests pin the relocation:

  1. every palette survives verbatim (exact RGB triples + names), and
  2. the archive module is the *single source* — `config.CAT_CHARACTERS` IS the
     same object, not a re-declared copy of the literals.

Both are able-to-fail: before the relocation, `og_skins` does not exist (import
error → red) and once it does but config still re-declares its own dict, the
identity check is red. Green only when config re-exports the archive.
"""
from pycats.characters.og_skins import OG_SKINS
from pycats.config import CAT_CHARACTERS


# The canonical six, pinned verbatim from the pre-relocation config.py literals.
EXPECTED = {
    "ghost":  {"name": "Ghost",  "color": (255, 255, 255), "stripe_color": (220, 220, 220), "eye_color": (100, 100, 255)},
    "calico": {"name": "Calico", "color": (255, 160, 64),  "stripe_color": (204, 102, 0),   "eye_color": (34, 139, 34)},
    "tabby":  {"name": "Tabby",  "color": (128, 128, 128), "stripe_color": (64, 64, 64),    "eye_color": (255, 215, 0)},
    "void":   {"name": "Void",   "color": (20, 20, 20),    "stripe_color": (0, 0, 0),       "eye_color": (0, 255, 0)},
    "tiger":  {"name": "Tiger",  "color": (255, 140, 0),   "stripe_color": (0, 0, 0),       "eye_color": (255, 215, 0)},
    "bengal": {"name": "Bengal", "color": (245, 245, 220), "stripe_color": (139, 69, 19),   "eye_color": (0, 191, 255)},
}


def test_archive_holds_exactly_the_six_skins():
    assert set(OG_SKINS.keys()) == set(EXPECTED.keys())


def test_each_skin_resolves_to_its_exact_rgb():
    """Palettes preserved byte-for-byte through the relocation."""
    for key, want in EXPECTED.items():
        got = OG_SKINS[key]
        assert got["name"] == want["name"], key
        for field in ("color", "stripe_color", "eye_color"):
            assert tuple(got[field]) == want[field], f"{key}.{field}"


def test_config_reexports_archive_as_single_source():
    """`config.CAT_CHARACTERS` must BE the archive object, not a copy.

    This is the seam: every consumer (char_select, game, sim/runner) imports
    CAT_CHARACTERS from config, so a re-export keeps them all reading the one
    archived source rather than duplicating the literals.
    """
    assert CAT_CHARACTERS is OG_SKINS
