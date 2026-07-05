"""#469 — the in-battle controls legend renders ANY bound key by name.

Split from #462. `draw_controls()` used a hardcoded `key_names` glyph dict with a
`.get(code, '?')` fallback, so a key outside that dict rendered as `?`. Since #439
lets a player rebind an action (Options -> Keybind) to any key and that live keymap
feeds the battle, an off-dict binding showed `?` in the legend. The fix resolves the
fallback via `pygame.key.name(code)` so no per-key hardcoding is needed for correctness.

Same capture harness as test_controls_smash_row.py: monkeypatch render_text_mixed to
collect the emitted lines. Able-to-fail: with the old `'?'` fallback the rebound-key
rows read `Attack: ?` / `Shield: ?`, so these assertions go red.
"""
import pygame

from pycats import text_utils
from pycats.render_battle import draw_controls


class _Player:
    def __init__(self, controls):
        self.controls = controls


# Default P1 keymap (game.py), then rebound below to keys OUTSIDE the glyph dict.
_FULL = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
             attack=pygame.K_v, shield=pygame.K_x, special=pygame.K_c, smash=pygame.K_b)


def _capture_lines(monkeypatch, controls, topright=False):
    pygame.init()  # topright path calls _get_font(...).size()
    lines = []

    def _fake(txt, size, color, surface, pos):
        lines.append(txt)

    monkeypatch.setattr(text_utils.text_renderer, "render_text_mixed", _fake)
    draw_controls(pygame.Surface((10, 10)), _Player(controls), "P1", topright=topright)
    return lines


def test_rebound_letter_key_renders_by_name_not_question_mark(monkeypatch):
    # K_p is not in the glyph dict; pygame.key.name(K_p) == 'p' -> 'P'.
    lines = _capture_lines(monkeypatch, dict(_FULL, attack=pygame.K_p))
    assert "Attack: P" in lines
    assert "Attack: ?" not in lines


def test_rebound_punctuation_key_renders_by_name(monkeypatch):
    # K_SEMICOLON has no glyph override; pygame.key.name gives ';'.
    lines = _capture_lines(monkeypatch, dict(_FULL, shield=pygame.K_SEMICOLON), topright=True)
    assert "Shield: ;" in lines
    assert "Shield: ?" not in lines


def test_glyph_overrides_still_win_over_raw_name(monkeypatch):
    # Arrow keys keep their glyph, not pygame's 'left'/'right' names.
    lines = _capture_lines(monkeypatch,
                           dict(_FULL, left=pygame.K_LEFT, right=pygame.K_RIGHT))
    assert "Move: ←/→" in lines  # ← / →


def test_unbound_action_still_degrades_to_question_mark(monkeypatch):
    # A None binding (missing key) has no name; it must stay '?', not crash.
    no_smash = {k: v for k, v in _FULL.items() if k != "smash"}
    lines = _capture_lines(monkeypatch, no_smash)
    assert "Smash: ?" in lines
