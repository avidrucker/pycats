"""BattleScreen feeds each fighter's InputHistory on the press-edge (#21).

step() records this frame's just-pressed keys into per-player buffers, split by
each keymap (P1_KEYS / P2_KEYS are disjoint). This is a side buffer — it must
NOT perturb the golden sim path (test_battle_screen_step_matches_runner_sim_path
still passes). reset() clears the buffers for a fresh match.
"""


import pygame  # noqa: E402

from pycats import runtime_settings, settings  # noqa: E402
from pycats.battle_screen import BattleScreen  # noqa: E402
from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.core.input import InputFrame  # noqa: E402
from pycats.sim.runner import build_stage  # noqa: E402

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


def _frame(pressed):
    s = set(pressed)
    return InputFrame(held=set(s), pressed=s, released=set())


def _bs():
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("calico", "tabby")
    return bs, build_stage()


def test_step_records_per_player_pressed_edge():
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v]), platforms)  # P1 attack only
    assert bs.p1_history.entries() == ["A"]
    assert bs.p2_history.entries() == []


def test_step_separates_players_by_keymap():
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v, pygame.K_PERIOD]), platforms)  # both attack same frame
    assert bs.p1_history.entries() == ["A"]
    assert bs.p2_history.entries() == ["A"]


def test_step_joins_simultaneous_presses():
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_w, pygame.K_v]), platforms)  # P1 up+attack -> one entry
    assert bs.p1_history.entries() == ["↑A"]


def test_hold_does_not_relog():
    bs, platforms = _bs()
    press = _frame([pygame.K_v])
    bs.step(press, platforms)
    # next frame: key still HELD but not in `pressed` -> no new entry
    bs.step(InputFrame(held={pygame.K_v}, pressed=set(), released=set()), platforms)
    assert bs.p1_history.entries() == ["A"]


def test_reset_clears_history():
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v]), platforms)
    assert bs.p1_history.entries() == ["A"]
    bs.reset()
    assert bs.p1_history.entries() == []


def test_draw_battle_gates_input_history_on_toggle():
    """_draw_battle draws the strip only when show_input_history() is ON."""
    bs, platforms = _bs()
    bs.step(_frame([pygame.K_v]), platforms)  # P1 has an "A" entry to show
    runtime_settings.seed(settings.defaults())

    on = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    off = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    runtime_settings.set("show_input_history", True)
    bs._draw_battle(on, platforms)
    runtime_settings.set("show_input_history", False)
    bs._draw_battle(off, platforms)

    assert pygame.image.tobytes(on, "RGB") != pygame.image.tobytes(off, "RGB")
