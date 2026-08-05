"""BattleScreen feeds each fighter's InputHistory every frame (#21, #875).

step() records this frame's pressed + held keys into per-player buffers, split by
each keymap (P1_KEYS / P2_KEYS are disjoint). This is a side buffer — it must
NOT perturb the golden sim path (test_battle_screen_step_matches_runner_sim_path
still passes). reset() clears the buffers for a fresh match.
"""

import pygame  # noqa: E402

from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.core.input import InputFrame  # noqa: E402
from pycats.screens.battle_screen import BattleScreen  # noqa: E402
from pycats.shell.input_history import HELD, PRESSED  # noqa: E402
from pycats.sim.runner import build_stage  # noqa: E402
from pycats.storage import runtime_settings, settings  # noqa: E402

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


def _frame(pressed):
    """One frame with `pressed` freshly down (held == pressed, the edge case)."""
    s = set(pressed)
    return InputFrame(held=set(s), pressed=s, released=set())


def _bs():
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("calico", "tabby")
    return bs, build_stage()


def test_step_records_per_player_pressed_edge():
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v]), platforms)  # P1 attack only
    assert bs.p1_history.frames() == [{"attack": PRESSED}]
    assert bs.p2_history.frames() == [{}]  # idle column, no P2 input this frame


def test_step_separates_players_by_keymap():
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v, pygame.K_PERIOD]), platforms)  # both attack same frame
    assert bs.p1_history.frames() == [{"attack": PRESSED}]
    assert bs.p2_history.frames() == [{"attack": PRESSED}]


def test_step_marks_simultaneous_presses_in_one_frame():
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_w, pygame.K_v]), platforms)  # P1 up+attack same frame
    assert bs.p1_history.frames() == [{"up": PRESSED, "attack": PRESSED}]


def test_held_key_logs_as_held_not_pressed():
    """#875: a still-held key IS recorded — as HELD — so held-while-pressed reads
    apart from a fresh tap (the #21 strip dropped held keys entirely)."""
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v]), platforms)  # press A
    # next frame: A still HELD but not in `pressed`
    bs.step(InputFrame(held={pygame.K_v}, pressed=set(), released=set()), platforms)
    assert bs.p1_history.frames() == [{"attack": PRESSED}, {"attack": HELD}]


def test_reset_clears_history():
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v]), platforms)
    assert bs.p1_history.frames() == [{"attack": PRESSED}]
    bs.reset()
    assert bs.p1_history.frames() == []


def test_draw_battle_gates_input_history_on_toggle():
    """_draw_battle draws the grid only when show_input_history() is ON."""
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v]), platforms)  # P1 has an attack mark to show
    runtime_settings.seed(settings.defaults())

    on = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    off = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    runtime_settings.set("show_input_history", True)
    bs._draw_battle(on, platforms)
    runtime_settings.set("show_input_history", False)
    bs._draw_battle(off, platforms)

    assert pygame.image.tobytes(on, "RGB") != pygame.image.tobytes(off, "RGB")
