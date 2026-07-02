"""Visual button-press feedback — the highlight-pulse (#332, split from #21).

On a confirm/navigation input the focused menu button flashes a brief, brighter
fill (``BUTTON_FILL_PRESSED``) distinct from the resting focused glow, then decays
back. The widget owns the pixels (``pressed`` kwarg); each screen owns the short
``press_pulse`` frame counter that drives it. Audio is out of scope (#445).

Default ``pressed=False`` keeps ``draw_menu_button`` byte-identical to before, so
render goldens / screen-parity are untouched.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats.menu_widgets import (  # noqa: E402
    BUTTON_FILL_FOCUSED,
    BUTTON_FILL_PRESSED,
    PRESS_PULSE_FRAMES,
    draw_menu_button,
)

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def _surf(w=400, h=80):
    pygame.font.init()
    s = pygame.Surface((w, h))
    s.fill((0, 0, 0))
    return s


def _bytes(s):
    return pygame.image.tobytes(s, "RGB")


def _row_has_fill(surface, y, color, x0=60, x1=340):
    return any(surface.get_at((x, y))[:3] == color for x in range(x0, x1))


# ---- widget: the pressed flash ------------------------------------------- #
def test_pressed_focused_button_draws_flash_fill():
    s = _surf()
    draw_menu_button(s, "Play", (200, 40), 36, focused=True, pressed=True)
    assert _row_has_fill(s, 40, BUTTON_FILL_PRESSED)  # brighter flash present


def test_pressed_differs_from_resting_focused():
    pressed, resting = _surf(), _surf()
    draw_menu_button(pressed, "Play", (200, 40), 36, focused=True, pressed=True)
    draw_menu_button(resting, "Play", (200, 40), 36, focused=True, pressed=False)
    assert _bytes(pressed) != _bytes(resting)  # the flash is visible


def test_default_pressed_false_is_byte_identical_to_bare_call():
    # Parity guard: the new kwarg must not perturb the default render (goldens).
    a, b = _surf(), _surf()
    draw_menu_button(a, "Play", (200, 40), 36, focused=True)
    draw_menu_button(b, "Play", (200, 40), 36, focused=True, pressed=False)
    assert _bytes(a) == _bytes(b)


def test_pressed_only_matters_when_focused():
    # An unfocused button shows no flash — the pulse rides the focused row only.
    a, b = _surf(), _surf()
    draw_menu_button(a, "Play", (200, 40), 36, focused=False, pressed=True)
    draw_menu_button(b, "Play", (200, 40), 36, focused=False, pressed=False)
    assert _bytes(a) == _bytes(b)
    assert not _row_has_fill(a, 40, BUTTON_FILL_PRESSED)


# ---- screen wiring: the press_pulse counter ------------------------------- #
from pycats.main_menu import MainMenuManager  # noqa: E402
from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402


def test_main_menu_pulse_set_on_select():
    m = MainMenuManager(_P1, _P2)
    assert m.press_pulse == 0
    m.update({_P1["attack"]})
    assert m.press_pulse == PRESS_PULSE_FRAMES


def test_main_menu_pulse_set_on_nav():
    m = MainMenuManager(_P1, _P2)
    m.update({_P1["down"]})
    assert m.press_pulse == PRESS_PULSE_FRAMES


def test_main_menu_pulse_decays_to_zero():
    m = MainMenuManager(_P1, _P2)
    m.update({_P1["down"]})
    for _ in range(PRESS_PULSE_FRAMES):
        m.update(set())
    assert m.press_pulse == 0


def test_main_menu_reset_clears_pulse():
    m = MainMenuManager(_P1, _P2)
    m.update({_P1["down"]})
    m.reset()
    assert m.press_pulse == 0


def test_main_menu_render_flashes_during_pulse():
    active = MainMenuManager(_P1, _P2)
    active.update({_P1["down"]})  # focus moves to option 1, pulse active
    resting = MainMenuManager(_P1, _P2)
    resting.selected_option = active.selected_option  # same focus, no pulse
    a = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    b = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    active.render(a)
    resting.render(b)
    assert _bytes(a) != _bytes(b)  # the pulse frame renders differently


# ---- pause menu ----------------------------------------------------------- #
from pycats.pause_menu import PauseMenuManager  # noqa: E402


def test_pause_menu_pulse_set_on_nav():
    m = PauseMenuManager(_P1, _P2)
    m.update({_P1["down"]})
    assert m.press_pulse == PRESS_PULSE_FRAMES


def test_pause_menu_pulse_set_on_select():
    m = PauseMenuManager(_P1, _P2)
    m.update({_P1["attack"]})  # V selects
    assert m.press_pulse == PRESS_PULSE_FRAMES


def test_pause_menu_pulse_decays_to_zero():
    m = PauseMenuManager(_P1, _P2)
    m.update({_P1["down"]})
    for _ in range(PRESS_PULSE_FRAMES):
        m.update(set())
    assert m.press_pulse == 0


def test_pause_menu_render_flashes_during_pulse():
    active = PauseMenuManager(_P1, _P2)
    active.update({_P1["down"]})
    resting = PauseMenuManager(_P1, _P2)
    resting.selected_option = active.selected_option
    a = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    b = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    active.render(a)
    resting.render(b)
    assert _bytes(a) != _bytes(b)


# ---- options menu (2D grid) ----------------------------------------------- #
from pycats import runtime_settings, settings  # noqa: E402
from pycats.options_menu import OptionsMenu  # noqa: E402


def _options():
    runtime_settings.seed(settings.defaults())
    return OptionsMenu(_P1, _P2)


def test_options_menu_pulse_set_on_nav():
    m = _options()
    m.update({_P1["down"]})
    assert m.press_pulse == PRESS_PULSE_FRAMES


def test_options_menu_pulse_set_on_select():
    m = _options()
    m.update({_P1["attack"]})  # activate the focused row
    assert m.press_pulse == PRESS_PULSE_FRAMES


def test_options_menu_render_flashes_during_pulse():
    active = _options()
    active.update({_P1["down"]})
    resting = _options()
    resting.selected_option = active.selected_option
    a = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    b = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    active.render(a)
    resting.render(b)
    assert _bytes(a) != _bytes(b)
