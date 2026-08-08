"""Either player's mapped B-action (special) key drives the hold-to-quit timer on
menu screens, identically to ESC (#867).

Mirrors ``test_hold_esc_navigation.py`` but holds a player's *special* key (the
"B" action) instead of ESC. Drives the real ScreenStateManager through its public
``update()`` / ``get_state()`` interface — no internal timer pokes.

Two invariants beyond "B behaves like ESC on menus":
  - the trigger is the *mapped* B-action key, resolved per-player from controls
    (rebinding moves it — no hardcoded key);
  - the match is sacred: holding B (the attack button) during ``playing`` /
    ``pause`` must NOT abandon the match, even though ESC-hold does drop from
    those states. B-as-quit is menu-only.
"""

import pygame
import pytest

from pycats.core.input import InputFrame
from pycats.shell.screen_manager import ScreenStateManager

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

HOLD = 120  # esc_quit_hold_frames (2s @ 60 FPS)


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    """Each test writes/reads settings under its own config dir (default = on)."""
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    pygame.init()


def _hold_key(key):
    return InputFrame(held={key}, pressed=set(), released=set())


def _empty():
    return InputFrame(held=set(), pressed=set(), released=set())


def _mk(state="main_menu"):
    sm = ScreenStateManager(_P1, _P2)
    if state != "main_menu":
        sm.engine.force(state)
    return sm


def _hold(sm, key, frames, battle=None):
    for _ in range(frames):
        sm.update(_hold_key(key), battle)


# --- B behaves like ESC on menu screens ------------------------------------


def test_p1_b_hold_quits_at_main_menu():
    sm = _mk("main_menu")
    _hold(sm, _P1["special"], HOLD)
    assert sm.get_state() == "main_menu"
    assert sm.should_quit_game() is True


def test_p2_b_hold_quits_at_main_menu():
    sm = _mk("main_menu")
    _hold(sm, _P2["special"], HOLD)
    assert sm.should_quit_game() is True


def test_p1_b_hold_backs_out_options_to_main_menu():
    sm = _mk("options")
    _hold(sm, _P1["special"], HOLD)
    assert sm.get_state() == "main_menu"


def test_char_select_b_hold_backs_out_at_2s():
    """#905: char_select B-hold backs out to main_menu at the shared 2s threshold
    (a T-frame hold pops on frame T+1, so hold past HOLD)."""
    sm = _mk("char_select")
    _hold(sm, _P1["special"], HOLD + 5)
    assert sm.get_state() == "main_menu"


def test_char_select_b_hold_below_2s_does_not_back_out():
    """#905 regression (able-to-fail): holding B for just under 2 seconds
    (HOLD - 1 frames) on char_select must NOT return to main menu — the hold is a
    full 2s, consistent with every other hold-to-back. Red while
    back_hold_frames == 60 (pops at ~1s), green once it is 120."""
    sm = _mk("char_select")
    _hold(sm, _P1["special"], HOLD - 1)
    assert sm.get_state() == "char_select"


def test_b_hold_win_screen_bypasses_confirm_to_char_select():
    sm = _mk()
    sm.set_winner(object(), object())
    sm.engine.force("win_screen")
    _hold(sm, _P2["special"], HOLD)
    assert sm.get_state() == "char_select"
    assert sm.winner is None and sm.loser is None


def test_b_below_threshold_does_not_pop():
    sm = _mk("options")
    _hold(sm, _P1["special"], HOLD - 1)
    assert sm.get_state() == "options"


def test_b_release_before_threshold_resets_the_hold():
    sm = _mk("options")
    _hold(sm, _P1["special"], HOLD - 1)
    sm.update(_empty())  # release
    _hold(sm, _P1["special"], HOLD - 1)  # not enough on its own
    assert sm.get_state() == "options"


# --- the trigger honors rebinds (no hardcoded key) -------------------------


def test_rebound_b_key_drives_the_timer():
    """Rebinding a player's special action moves the quit trigger to the new key.
    Able-to-fail for the rebind path: a hardcoded key would ignore K_j."""
    sm = _mk("options")
    sm.p1_controls["special"] = pygame.K_j  # rebind P1's B-action
    _hold(sm, pygame.K_j, HOLD)
    assert sm.get_state() == "main_menu"


def test_old_key_inert_after_rebind():
    sm = _mk("options")
    sm.p1_controls["special"] = pygame.K_j
    _hold(sm, pygame.K_c, HOLD)  # the pre-rebind key
    assert sm.get_state() == "options"


# --- the match is sacred: B is menu-only, never abandons play --------------


def test_playing_b_hold_does_not_abandon_match():
    """Holding B (the attack button) during a live match must NOT drop to
    char_select — even though ESC-hold does. Able-to-fail guard: a naive
    OR-B-into-the-timer would drop here."""
    sm = _mk("playing")
    _hold(sm, _P1["special"], HOLD * 2)
    assert sm.get_state() == "playing"
    assert sm.should_quit_game() is False


def test_pause_b_hold_does_not_quit():
    """Pause is the in-match overlay; B stays reserved there too."""
    sm = _mk("pause")
    _hold(sm, _P1["special"], HOLD * 2)
    assert sm.get_state() == "pause"


# --- ESC path stays unchanged ----------------------------------------------


def test_esc_still_drops_from_playing():
    """Generalising B to menus must not disturb ESC on gameplay screens."""
    sm = _mk("playing")
    _hold(sm, pygame.K_ESCAPE, HOLD)
    assert sm.get_state() == "char_select"
