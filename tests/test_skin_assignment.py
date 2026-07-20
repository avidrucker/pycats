"""Unit tests for the domain skin-assignment layer (#755, ratified #748).

Two rules, both pure-domain and golden-neutral (no render, no sim):

- **Availability** — each Character's pool is the shared OG six + its own extra
  skin keys; never another Character's theme.
- **Distinctness** — two players who pick the same Character get distinct Skins.
"""

from pycats.domain import (
    CHARACTERS,
    SHARED_SKIN_KEYS,
    SKINS,
    Selection,
    assign_distinct_skins,
    available_skins,
)


def test_character_owns_its_base_theme_as_an_extra_skin():
    # representation (ii): each Character lists its own extra skin keys (#748)
    assert CHARACTERS["nalio"].extra_skin_keys == ("red-blue",)
    assert CHARACTERS["narz"].extra_skin_keys == ("blue-black",)
    assert CHARACTERS["birky"].extra_skin_keys == ("pink-red",)


def test_shared_pool_is_the_original_six():
    assert set(SHARED_SKIN_KEYS) == {"ghost", "calico", "tabby", "void", "tiger", "bengal"}


def test_available_skins_is_shared_pool_plus_own_theme():
    keys = [s.key for s in available_skins(CHARACTERS["nalio"])]
    for shared in SHARED_SKIN_KEYS:
        assert shared in keys  # every shared skin is available
    assert "red-blue" in keys  # Nalio's own base theme
    assert "blue-black" not in keys  # Narz's theme — not available to Nalio
    assert "pink-red" not in keys  # Birky's theme — not available to Nalio


def test_available_skins_resolves_to_exact_rgbs():
    pool = {s.key: s for s in available_skins(CHARACTERS["nalio"])}
    assert pool["calico"].color == SKINS["calico"].color
    assert pool["red-blue"].color == SKINS["red-blue"].color


def test_available_skins_has_no_duplicates():
    keys = [s.key for s in available_skins(CHARACTERS["nalio"])]
    assert len(keys) == len(set(keys))


def test_same_character_players_get_distinct_skins():
    nalio = CHARACTERS["nalio"]
    both = [Selection(nalio, SKINS["red-blue"]), Selection(nalio, SKINS["red-blue"])]
    out = assign_distinct_skins(both)
    assert out[0].skin.key != out[1].skin.key
    assert out[1].skin in available_skins(nalio)  # P2's fallback is from Nalio's pool


def test_first_same_character_player_keeps_their_skin():
    nalio = CHARACTERS["nalio"]
    both = [Selection(nalio, SKINS["red-blue"]), Selection(nalio, SKINS["red-blue"])]
    out = assign_distinct_skins(both)
    assert out[0].skin.key == "red-blue"


def test_different_characters_are_untouched():
    nalio, narz = CHARACTERS["nalio"], CHARACTERS["narz"]
    sels = [Selection(nalio, SKINS["red-blue"]), Selection(narz, SKINS["blue-black"])]
    out = assign_distinct_skins(sels)
    assert out == sels  # no same-Character collision → identity
