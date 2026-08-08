"""Dev-mode char-select roster (#1292, slice 2 of epic #1311).

When the game is in dev mode (the #1312 gate — `runtime_settings.dev_mode()`), char-select
exposes the intended-default fixtures `default` (the default.json cat) and `testcat` (the
gray placeholder, #591) as selectable + playable, on top of the shipping ARCHETYPE_ROSTER.
When dev mode is off, the roster is byte-identical to today's ARCHETYPE_ROSTER — no
player-visible change to the shipping build.

The two dev keys have no ARCHETYPE_NAME / ARCHETYPE_PALETTE entry, so the roster tile +
player-slot caption resolve their label through CharacterSelector._tile_name / DEV_KEY_NAMES
and their cosmetic through palette_for's existing testcat/neutral fallbacks — rendering must
not raise. A battle launched on either dev key must build both fighters (load_fighter_data
maps both to the default cat).

These tests are able-to-fail: without the dev_mode() gate the dev-off roster grows the two
keys (test_dev_off_* red); without the gate/append the dev-on roster stays 4 (test_dev_on_*
red); without _tile_name the dev-on render raises KeyError on ARCHETYPE_NAME[dev_key].
"""

import pygame  # type: ignore
import pytest  # type: ignore

from pycats.characters.roster import ARCHETYPE_ROSTER
from pycats.combat.data import load_fighter_data
from pycats.screens.battle_screen import BattleScreen
from pycats.screens.char_select import DEV_KEY_NAMES, DEV_ROSTER, CharacterSelector
from pycats.storage import runtime_settings, settings

_P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)
_P2 = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_PERIOD,
    special=pygame.K_SLASH,
    shield=pygame.K_RSHIFT,
)


@pytest.fixture(autouse=True)
def _reset_dev_mode():
    """dev_mode is a process-wide module flag; reset it around every test so a dev-on test
    never leaks into another test under pytest-randomly (e.g. test_archetype_selectability's
    dev-off roster assertion). Also restore settings defaults for the render smoke test."""
    pygame.init()
    runtime_settings.seed(settings.defaults())
    runtime_settings.set_dev_mode(False)
    yield
    runtime_settings.set_dev_mode(False)
    runtime_settings.seed(settings.defaults())


def _surf():
    return pygame.Surface((960, 540))


# --- roster gate -------------------------------------------------------------


def test_dev_off_roster_is_the_shipping_archetypes():
    runtime_settings.set_dev_mode(False)
    cs = CharacterSelector(_P1, _P2)
    assert tuple(cs.characters) == ARCHETYPE_ROSTER
    assert "default" not in cs.characters and "testcat" not in cs.characters


def test_dev_on_roster_appends_the_dev_fixtures():
    runtime_settings.set_dev_mode(True)
    cs = CharacterSelector(_P1, _P2)
    # archetypes still lead, in order; dev fixtures appended after.
    assert tuple(cs.characters[: len(ARCHETYPE_ROSTER)]) == ARCHETYPE_ROSTER
    assert tuple(cs.characters[len(ARCHETYPE_ROSTER) :]) == DEV_ROSTER
    assert "default" in cs.characters and "testcat" in cs.characters


# --- label fallback + render safety -----------------------------------------


def test_tile_name_defines_labels_for_dev_keys():
    cs = CharacterSelector(_P1, _P2)
    assert cs._tile_name("default") == DEV_KEY_NAMES["default"]
    assert cs._tile_name("testcat") == DEV_KEY_NAMES["testcat"]
    # archetype keys are unchanged (ARCHETYPE_NAME still wins)
    assert cs._tile_name("nalio") == "Nalio"


def test_dev_on_render_does_not_raise_on_dev_keys():
    """The dev keys have no ARCHETYPE_NAME entry; rendering the grid + a confirmed dev-cat
    player slot must resolve labels via _tile_name, not a bare ARCHETYPE_NAME[key] index."""
    runtime_settings.set_dev_mode(True)
    cs = CharacterSelector(_P1, _P2)
    # Confirm P1 on testcat and P2 on default so the player-slot caption path runs too.
    cs.p1_selected, cs.p1_confirmed = "testcat", True
    cs.p2_selected, cs.p2_confirmed = "default", True
    cs.render(_surf())  # must not raise


# --- playability -------------------------------------------------------------


@pytest.mark.parametrize("dev_key", DEV_ROSTER)
def test_dev_key_builds_a_fighter_for_battle(dev_key):
    """A dev-mode battle on `default`/`testcat` builds both fighters — create_from_selection
    resolves each dev key's FighterData (both map to the default cat) without error."""
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection(dev_key, dev_key)
    assert bs.player1 is not None and bs.player2 is not None
    assert bs.player1.fighter_data == load_fighter_data(dev_key)
