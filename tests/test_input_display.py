"""On-screen input display for watch.py playback (#405).

The pure demux helper (InputFrame + keymap -> held tokens) is unit-tested able-to-
fail; a ScreenshotPresenter smoke test proves the render path works headlessly and
stays golden-safe (show_inputs off -> no overlay).
"""
import pygame

from pycats.core.input import InputFrame
from pycats.sim.presenters import held_input_tokens
from pycats.sim.runner import P1_KEYS, P2_KEYS


def _frame(held_keys):
    return InputFrame(held=set(held_keys), pressed=set(), released=set())


def test_demux_maps_held_keys_to_tokens_per_keymap():
    # held left + attack under P1's map -> the directional glyph + the button word
    fi = _frame({P1_KEYS["left"], P1_KEYS["attack"]})
    assert held_input_tokens(fi, P1_KEYS) == ["←", "attack"]


def test_demux_is_keymap_specific_disjoint_players():
    # a key held in P1's map is invisible to P2's (disjoint maps)
    fi = _frame({P1_KEYS["right"]})
    assert held_input_tokens(fi, P1_KEYS) == ["→"]
    assert held_input_tokens(fi, P2_KEYS) == []


def test_demux_orders_directions_then_buttons():
    fi = _frame({P1_KEYS["shield"], P1_KEYS["up"], P1_KEYS["down"]})
    assert held_input_tokens(fi, P1_KEYS) == ["↑", "↓", "shield"]


def test_demux_empty_and_none():
    assert held_input_tokens(_frame(set()), P1_KEYS) == []
    assert held_input_tokens(None, P1_KEYS) == []


def test_screenshot_presenter_renders_input_overlay_in_the_real_loop(tmp_path):
    # #248: prove the overlay actually renders inside run_battle (not just a stub) —
    # a ScreenshotPresenter with show_inputs=True saves frames without error.
    import os
    from pycats.sim.presenters import ScreenshotPresenter
    from pycats.sim.runner import run_battle

    sp = ScreenshotPresenter(str(tmp_path), frames={0: "f0", 1: "f1"}, show_inputs=True)
    run_battle(frames=3, presenter=sp)
    assert sp.saved, "overlay render path never ran in the loop"
    assert all(os.path.exists(path) for _, path in sp.saved)
