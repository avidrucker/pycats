"""Present-layer live settings holder (#121).

runtime_settings mirrors the persisted schema but holds the *live* values the
render path / game loop read so the Options menu can change them mid-session.
"""
from pycats import runtime_settings, settings


def test_defaults_to_schema_defaults():
    runtime_settings.seed(settings.defaults())
    assert runtime_settings.show_status_timer_bars() is True
    assert runtime_settings.get("windowed_scale") == settings.defaults()["windowed_scale"]


def test_seed_from_prefs_sets_live_values():
    runtime_settings.seed({"show_status_timer_bars": False, "windowed_scale": 2.0})
    assert runtime_settings.show_status_timer_bars() is False
    assert runtime_settings.get("windowed_scale") == 2.0


def test_set_updates_live_value():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_status_timer_bars", False)
    assert runtime_settings.show_status_timer_bars() is False


def test_seed_copies_so_later_set_does_not_mutate_caller(tmp_path, monkeypatch):
    prefs = {"show_status_timer_bars": True}
    runtime_settings.seed(prefs)
    runtime_settings.set("show_status_timer_bars", False)
    assert prefs["show_status_timer_bars"] is True  # caller's dict untouched


def test_seed_without_arg_loads_from_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"show_status_timer_bars": False})
    runtime_settings.seed()  # no arg → settings.load()
    assert runtime_settings.show_status_timer_bars() is False


def test_unknown_key_falls_back_to_schema_default():
    runtime_settings.seed({})  # empty
    assert runtime_settings.show_status_timer_bars() is True
