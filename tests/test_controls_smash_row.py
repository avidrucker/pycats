"""#462 — the in-battle controls legend shows each player's Smash key.

draw_controls() renders each legend line via text_utils.text_renderer.render_text_mixed;
we monkeypatch that to capture the emitted text lines and assert a 'Smash:' row with
the correct glyph, directly after 'Special:'. The battle-screen render parity test
(test_battle_screen_render.py) can't guard this — it re-composes with the SAME
draw_controls, so adding a row changes both sides identically and stays byte-equal.
This capture test is the able-to-fail guard: without the #462 row no 'Smash:' line
is emitted, so test_smash_row_present_after_special fails.
"""
import pygame

from pycats import text_utils
from pycats.render_battle import draw_controls


class _Player:
    def __init__(self, controls):
        self.controls = controls


# A full default-style P1 keymap incl. the smash binding (game.py P1 smash = K_b).
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


def test_smash_row_present_after_special(monkeypatch):
    lines = _capture_lines(monkeypatch, _FULL)
    assert "Special: C" in lines
    assert "Smash: B" in lines
    # its own row, immediately below Special
    assert lines.index("Smash: B") == lines.index("Special: C") + 1


def test_p2_quote_binding_renders_apostrophe_glyph(monkeypatch):
    # game.py P2 smash = K_QUOTE, whose pygame.key.name is the apostrophe.
    lines = _capture_lines(monkeypatch, dict(_FULL, smash=pygame.K_QUOTE), topright=True)
    assert "Smash: '" in lines


def test_missing_smash_binding_degrades_to_question_mark(monkeypatch):
    no_smash = {k: v for k, v in _FULL.items() if k != "smash"}
    lines = _capture_lines(monkeypatch, no_smash)
    assert "Smash: ?" in lines  # .get('smash') fallback, no KeyError
