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


def _past_grace(ws):
    """Advance past the initial input-grace window with no input."""
    for _ in range(ws.INITIAL_INPUT_GRACE_FRAMES):
        ws.update(set())


def test_single_confirmation_does_not_return():
    """Both players must confirm before the win screen yields (issue #11).

    This pins a *deliberate* parity divergence from Project M, which advances
    past its results screen on a single button press (documented in #99). pycats
    keeps the both-confirm gate from #10. One player's confirm must NOT be
    enough to leave for character select.
    """
    ws = _fresh_screen()
    _past_grace(ws)
    ws.update({P1_CONTROLS["attack"]})  # only P1 confirms
    assert ws.p1_confirmed and not ws.p2_confirmed
    assert not ws.ready_to_return(), "one confirm left the win screen (need both)"


def test_both_confirmations_return_after_delay():
    """Once both confirm, the screen yields — but only after the return delay."""
    ws = _fresh_screen()
    _past_grace(ws)
    ws.update({P1_CONTROLS["attack"]})  # P1 confirms
    ws.update({P2_CONTROLS["attack"]})  # P2 confirms -> starts the return delay
    assert ws.both_confirmed()
    assert not ws.ready_to_return(), "returned before the post-confirm delay elapsed"

    # Burn the post-confirm delay; the bound comfortably exceeds the 30-frame delay.
    for _ in range(ws.return_delay + 5):
        ws.update(set())
    assert ws.ready_to_return(), "both confirmed but never became ready to return"
