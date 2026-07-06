"""Menu render creates no fonts per frame (#375, #372 follow-up).

main_menu/pause_menu called pygame.font.SysFont(None, size) EVERY frame — a
font-system (fontconfig) lookup building a new font each frame, ~173x slower than
the cached path and a real-display hard-hang source. After the fix all font
access is cached, so a steady-state render frame makes zero SysFont calls.
"""


import pygame  # noqa: E402

from pycats.main_menu import MainMenuManager  # noqa: E402
from pycats.pause_menu import PauseMenuManager  # noqa: E402

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def _spy_on_sysfont(monkeypatch):
    calls = {"n": 0}
    orig = pygame.font.SysFont

    def spy(*a, **k):
        calls["n"] += 1
        return orig(*a, **k)

    monkeypatch.setattr(pygame.font, "SysFont", spy)
    return calls


def test_main_menu_render_creates_no_font_per_frame(monkeypatch):
    pygame.font.init()
    mm = MainMenuManager(_P1, _P2)
    surf = pygame.Surface((960, 540))
    mm.render(surf)  # warm: populate all font caches
    calls = _spy_on_sysfont(monkeypatch)
    mm.render(surf)  # steady-state frame
    assert calls["n"] == 0  # no per-frame SysFont / fontconfig lookup


def test_pause_menu_render_creates_no_font_per_frame(monkeypatch):
    pygame.font.init()
    pm = PauseMenuManager(_P1, _P2)
    surf = pygame.Surface((960, 540))
    bg = pygame.Surface((960, 540))
    pm.render(surf, bg)  # warm
    calls = _spy_on_sysfont(monkeypatch)
    pm.render(surf, bg)  # steady-state frame
    assert calls["n"] == 0
