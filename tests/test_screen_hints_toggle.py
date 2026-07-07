"""Per-screen action hints + their two toggles (#681, from the #549 discoverability audit).

Two independent, on-by-default toggles gate the "which key does what" hints:
- `show_controls` — BATTLE screens only (playing, pause) — existing (#284).
- `show_screen_hints` — NON-battle screens (main_menu, char_select, options, win) — NEW.

The previously-hidden ESC-hold hint follows its own screen: the in-battle leave-match hint
is gated by `show_controls`; the non-battle quit/back hint is gated by `show_screen_hints`.
Each is also suppressed when the ESC-hold affordance itself is off (`esc_hold_to_navigate`).
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

import pycats.text_utils as tu  # noqa: E402
from pycats import runtime_settings, settings  # noqa: E402
from pycats.char_select import CharacterSelector  # noqa: E402
from pycats.main_menu import MainMenuManager  # noqa: E402
from pycats.options_menu import ROW_DESCRIPTIONS, OptionsMenu  # noqa: E402
from pycats.pause_menu import PauseMenuManager  # noqa: E402
from pycats.render_battle import draw_shell_chrome  # noqa: E402

_P1 = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6}
_P2 = {"left": 11, "right": 12, "up": 13, "down": 14, "attack": 15, "special": 16}


@pytest.fixture(autouse=True)
def _fresh_settings(monkeypatch):
    """Every test starts from schema defaults (all toggles ON), restored after.
    PYCATS_NO_PERSIST is set per-test via monkeypatch — NEVER at module scope, which
    would leak into the whole session and break the settings save/load tests."""
    pygame.init()
    monkeypatch.setenv("PYCATS_NO_PERSIST", "1")  # _activate()'s settings.save no-ops
    runtime_settings.seed(settings.defaults())
    yield
    runtime_settings.seed(settings.defaults())


def _capture(monkeypatch):
    """Record every text string drawn through the shared text paths during a render."""
    seen = []
    orig_rt = tu.render_text

    def spy_rt(surface, text, *a, **k):
        seen.append(text)
        return orig_rt(surface, text, *a, **k)

    monkeypatch.setattr(tu, "render_text", spy_rt)

    tr = tu.text_renderer
    for name in ("render_text_mixed", "render_text_simple"):
        orig = getattr(tr, name)

        def mk(orig):
            def spy(text, *a, **k):
                seen.append(text)
                return orig(text, *a, **k)

            return spy

        monkeypatch.setattr(tr, name, mk(orig))
    return seen


def _text(seen):
    return " || ".join(seen)


def _surf():
    return pygame.Surface((960, 540))


# ---- toggle infrastructure ----------------------------------------------------


def test_show_screen_hints_defaults_on():
    assert settings.defaults()["show_screen_hints"] is True
    assert runtime_settings.show_screen_hints() is True


def test_controls_caption_scopes_to_battle_and_screen_hints_row_exists():
    # OG toggle's caption must state battle-only so it no longer reads as all-screens.
    assert "battle" in ROW_DESCRIPTIONS["controls"].lower()
    assert "only" in ROW_DESCRIPTIONS["controls"].lower()
    assert "screen_hints" in ROW_DESCRIPTIONS
    assert "screen_hints" in OptionsMenu(_P1, _P2).rows


def test_options_screen_hints_row_toggles_and_labels():
    om = OptionsMenu(_P1, _P2)
    assert om._row_label("screen_hints") == "Screen Hints: ON"
    om._activate("screen_hints")
    assert runtime_settings.show_screen_hints() is False
    assert om._row_label("screen_hints") == "Screen Hints: OFF"


# ---- non-battle gating (show_screen_hints) ------------------------------------


def test_main_menu_action_hints_gated_by_screen_hints(monkeypatch):
    seen = _capture(monkeypatch)
    MainMenuManager(_P1, _P2).render(_surf())
    assert "navigate" in _text(seen).lower()  # hints present when ON (default)

    seen.clear()
    runtime_settings.set("show_screen_hints", False)
    MainMenuManager(_P1, _P2).render(_surf())
    # Able-to-fail: hints must vanish when the non-battle toggle is OFF.
    assert "navigate" not in _text(seen).lower()
    assert "Hold ESC to quit" not in _text(seen)


def test_main_menu_esc_quit_hint_requires_esc_hold_enabled(monkeypatch):
    # Non-battle ESC-hold hint is gated by show_screen_hints AND the affordance itself.
    seen = _capture(monkeypatch)
    MainMenuManager(_P1, _P2).render(_surf())
    assert "Hold ESC to quit" in _text(seen)

    seen.clear()
    runtime_settings.set("esc_hold_to_navigate", False)
    MainMenuManager(_P1, _P2).render(_surf())
    assert "Hold ESC to quit" not in _text(seen)  # a disabled ESC must not be advertised
    assert "navigate" in _text(seen).lower()  # the other hints still show


def test_char_select_instructions_gated_by_screen_hints(monkeypatch):
    seen = _capture(monkeypatch)
    runtime_settings.set("show_screen_hints", False)
    CharacterSelector(_P1, _P2).render(_surf())
    assert "move cursor" not in _text(seen).lower()


# ---- battle gating (show_controls) + the context mapping ----------------------


def test_playing_esc_hold_hint_gated_by_show_controls_not_screen_hints(monkeypatch):
    # The in-battle ESC-hold hint follows the BATTLE toggle: turning the non-battle
    # toggle OFF must NOT hide it, and turning the battle toggle OFF must.
    seen = _capture(monkeypatch)
    runtime_settings.set("show_screen_hints", False)  # non-battle OFF …
    runtime_settings.set("show_controls", True)  # … battle ON
    draw_shell_chrome(_surf(), 60.0, False, None)
    assert "Hold ESC to leave match" in _text(seen)  # gated by OG, not NEW

    seen.clear()
    runtime_settings.set("show_controls", False)
    draw_shell_chrome(_surf(), 60.0, False, None)
    assert "Hold ESC to leave match" not in _text(seen)  # able-to-fail


def test_pause_instructions_gated_by_show_controls(monkeypatch):
    seen = _capture(monkeypatch)
    runtime_settings.set("show_controls", False)
    PauseMenuManager(_P1, _P2).render(_surf())
    assert "navigate" not in _text(seen).lower()

    seen.clear()
    runtime_settings.set("show_controls", True)
    PauseMenuManager(_P1, _P2).render(_surf())
    assert "navigate" in _text(seen).lower()
