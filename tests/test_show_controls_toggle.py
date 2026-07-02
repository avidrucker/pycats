"""Options 'Controls' toggle — gate the in-battle controls display (#284).

The fighter-controls display (draw_controls) was hard-wired always-on — the odd
one out among the toggleable HUD extras (status bars #111, hitbox overlay #219,
input history #21). This makes it a persisted Options toggle, default ON (so a
fresh config is unchanged). Mirrors the show_input_history chain landed in #21.
"""
import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from pycats import runtime_settings, settings  # noqa: E402
from pycats.battle_screen import BattleScreen  # noqa: E402
from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.options_menu import OptionsMenu  # noqa: E402
from pycats.sim.runner import build_stage  # noqa: E402

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


# ---- settings.py: persisted default-ON + bool coercion --------------------- #
def test_show_controls_defaults_on(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    assert settings.defaults()["show_controls"] is True
    assert settings.load()["show_controls"] is True  # missing file -> default


def test_show_controls_round_trips_and_coerces_bool(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"show_controls": False})
    assert settings.load()["show_controls"] is False
    with open(settings.config_path(), "w", encoding="utf-8") as f:
        f.write(json.dumps({"show_controls": 1}))
    assert settings.load()["show_controls"] is True  # coerced from 1


def test_old_settings_without_key_still_load(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    with open(settings.config_path(), "w", encoding="utf-8") as f:
        f.write(json.dumps({"windowed_scale": 1.0}))  # pre-feature file
    assert settings.load()["show_controls"] is True  # merged over default


# ---- runtime_settings.py: live accessor ------------------------------------ #
def test_runtime_default_on():
    runtime_settings.seed(settings.defaults())
    assert runtime_settings.show_controls() is True


def test_runtime_set_flips():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_controls", False)
    assert runtime_settings.show_controls() is False


# ---- options_menu.py: row present, label, activate flips + persists -------- #
def test_options_row_present_labelled_and_toggles(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    runtime_settings.seed(settings.defaults())
    m = OptionsMenu(_P1, _P2)
    assert "controls" in m.rows
    assert m._row_label("controls") == "Controls: ON"
    m._activate("controls")
    assert runtime_settings.show_controls() is False
    assert settings.load()["show_controls"] is False
    assert m._row_label("controls") == "Controls: OFF"


# ---- battle_screen.py: _draw_battle gates draw_controls -------------------- #
def test_draw_battle_gates_controls_on_toggle():
    bs = BattleScreen(_P1, _P2)
    bs.create_from_selection("calico", "tabby")
    platforms = build_stage()
    runtime_settings.seed(settings.defaults())

    on = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    off = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    runtime_settings.set("show_controls", True)
    bs._draw_battle(on, platforms)
    runtime_settings.set("show_controls", False)
    bs._draw_battle(off, platforms)

    assert pygame.image.tobytes(on, "RGB") != pygame.image.tobytes(off, "RGB")
