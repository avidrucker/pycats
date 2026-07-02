"""Persisted display preferences (#95).

All tests redirect the config dir to a tmp_path via PYCATS_CONFIG_DIR, so they
never read or write the real ~/.config/pycats file.
"""
import json

from pycats import settings


def test_save_then_load_round_trips(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"windowed_scale": 1.5, "fullscreen": True})

    assert settings.config_path().startswith(str(tmp_path))
    loaded = settings.load()
    assert loaded["windowed_scale"] == 1.5
    assert loaded["fullscreen"] is True


def test_load_missing_file_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))  # empty dir, no file
    assert settings.load() == settings.defaults()


def test_load_corrupt_file_falls_back_to_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text("{ this is not json ::::")
    assert settings.load() == settings.defaults()  # no crash


def test_load_snaps_invalid_windowed_scale_to_a_valid_preset(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(
        json.dumps({"version": 1, "windowed_scale": 3.7, "fullscreen": False})
    )
    from pycats.display import WINDOWED_SCALE_PRESETS

    assert settings.load()["windowed_scale"] in WINDOWED_SCALE_PRESETS


def test_load_coerces_fullscreen_to_bool(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(
        json.dumps({"windowed_scale": 1.0, "fullscreen": 1})
    )
    assert settings.load()["fullscreen"] is True


def test_no_persist_disables_load_and_save(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("PYCATS_NO_PERSIST", "1")
    settings.save({"windowed_scale": 2.0, "fullscreen": True})
    assert not (tmp_path / "settings.json").exists()  # save was a no-op
    assert settings.load() == settings.defaults()  # load ignores any file


def test_saved_file_includes_a_version(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"windowed_scale": 2.0, "fullscreen": False})
    data = json.loads((tmp_path / "settings.json").read_text())
    assert data["version"] == settings.SCHEMA_VERSION


# --- #121: status-timer-bars HUD toggle now persisted here ---

def test_show_status_timer_bars_defaults_on(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    assert settings.defaults()["show_status_timer_bars"] is True
    assert settings.load()["show_status_timer_bars"] is True  # missing file


def test_show_status_timer_bars_round_trips_and_coerces_bool(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"show_status_timer_bars": False})
    assert settings.load()["show_status_timer_bars"] is False
    (tmp_path / "settings.json").write_text(
        json.dumps({"windowed_scale": 1.0, "show_status_timer_bars": 0})
    )
    assert settings.load()["show_status_timer_bars"] is False  # coerced from 0


def test_partial_save_does_not_clobber_other_prefs(tmp_path, monkeypatch):
    """A save of one key must merge over existing prefs, not reset the rest.

    The Options menu persists settings one at a time; without merge-on-save,
    flipping the HUD toggle would wipe the saved windowed_scale/fullscreen.
    """
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"windowed_scale": 2.5, "fullscreen": True})
    settings.save({"show_status_timer_bars": False})  # partial, unrelated key
    loaded = settings.load()
    assert loaded["windowed_scale"] == 2.5
    assert loaded["fullscreen"] is True
    assert loaded["show_status_timer_bars"] is False
