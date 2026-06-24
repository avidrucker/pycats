"""Regression tests for win-screen input timing (issue #10).

The win screen must not accept a confirmation on the first frames after it
appears: the attack key that landed the killing blow is often still being
mashed, which used to confirm instantly and bounce players back to character
select before they could read the stats.
"""

import pygame  # type: ignore

from pycats.win_screen import WinScreenManager

P1_CONTROLS = {"attack": pygame.K_v, "special": pygame.K_c}
P2_CONTROLS = {"attack": pygame.K_SLASH, "special": pygame.K_PERIOD}


def _fresh_screen():
    ws = WinScreenManager(P1_CONTROLS, P2_CONTROLS)
    ws.set_match_data(winner="cat1", loser="cat2")
    return ws


def test_attack_on_first_frame_is_ignored():
    """A confirm press on the very first win-screen frame must be ignored."""
    ws = _fresh_screen()
    ws.update({P1_CONTROLS["attack"]})
    assert not ws.p1_confirmed, "win screen confirmed on frame 0 (too early)"


def test_confirm_ignored_during_initial_grace_window():
    """Mashing attack for the whole grace window must not confirm."""
    ws = _fresh_screen()
    for _ in range(ws.INITIAL_INPUT_GRACE_FRAMES):
        ws.update({P1_CONTROLS["attack"]})
    assert not ws.p1_confirmed, "confirmed during the initial input grace window"


def test_confirm_works_after_grace_window():
    """Once the grace window elapses, a fresh press confirms as before."""
    ws = _fresh_screen()
    # Burn through the grace window with no input.
    for _ in range(ws.INITIAL_INPUT_GRACE_FRAMES):
        ws.update(set())
    ws.update({P1_CONTROLS["attack"]})
    assert ws.p1_confirmed, "confirm did not register after the grace window"
