"""Options 'Input History' toggle — persisted, default ON (#21).

Mirrors the show_hitbox_overlay / show_status_timer_bars toggle chain:
settings default + coercion, runtime live accessor, Options row label + activate.
Default ON preserves the (new) always-visible strip; a user can hide it.
"""
import json

import pygame  # noqa: E402

from pycats import runtime_settings, settings  # noqa: E402
from pycats.options_menu import OptionsMenu  # noqa: E402

_P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
           attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
_P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
           attack=pygame.K_PERIOD, special=pygame.K_SLASH, shield=pygame.K_RSHIFT)


# ---- settings.py: persisted default-ON + bool coercion --------------------- #
def test_show_input_history_defaults_on(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    assert settings.defaults()["show_input_history"] is True
    assert settings.load()["show_input_history"] is True  # missing file -> default


def test_show_input_history_round_trips_and_coerces_bool(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"show_input_history": False})
    assert settings.load()["show_input_history"] is False
    with open(settings.config_path(), "w", encoding="utf-8") as f:
        f.write(json.dumps({"show_input_history": 1}))
    assert settings.load()["show_input_history"] is True  # coerced from 1


def test_old_settings_without_key_still_load(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    with open(settings.config_path(), "w", encoding="utf-8") as f:
        f.write(json.dumps({"windowed_scale": 1.0}))  # pre-feature file
    assert settings.load()["show_input_history"] is True  # merged over default


# ---- runtime_settings.py: live accessor ------------------------------------ #
def test_runtime_default_on():
    runtime_settings.seed(settings.defaults())
    assert runtime_settings.show_input_history() is True


def test_runtime_set_flips():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_input_history", False)
    assert runtime_settings.show_input_history() is False


# ---- options_menu.py: row present, label, activate flips + persists -------- #
def test_options_row_present_labelled_and_toggles(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    runtime_settings.seed(settings.defaults())
    m = OptionsMenu(_P1, _P2)
    assert "input_history" in m.rows
    assert m._row_label("input_history") == "Input History: ON"
    m._activate("input_history")
    assert runtime_settings.show_input_history() is False
    assert settings.load()["show_input_history"] is False
    assert m._row_label("input_history") == "Input History: OFF"
