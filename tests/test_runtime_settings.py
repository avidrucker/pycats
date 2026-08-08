"""Present-layer live settings holder (#121).

runtime_settings mirrors the persisted schema but holds the *live* values the
render path / game loop read so the Options menu can change them mid-session.
"""

from pycats.storage import runtime_settings, settings


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


def test_present_key_get_does_not_evaluate_settings_defaults(monkeypatch):
    """#1262 (B3): get() must not build a throwaway defaults() dict on the hot path.

    The old body `_state.get(key, settings.defaults().get(key))` evaluated the
    default-arg expression `settings.defaults()` unconditionally — a fresh ~15-key
    dict minted on *every* read, even a present-key cache hit (measured 160
    get-calls/frame, the dict allocated 31.6k× over 600 profiled frames). The
    fallback must fire only when the key is genuinely absent."""
    runtime_settings.seed(settings.defaults())  # every schema key present
    calls = []
    real_defaults = settings.defaults
    monkeypatch.setattr(settings, "defaults", lambda: (calls.append(1), real_defaults())[1])

    val = runtime_settings.get("show_status_timer_bars")

    assert val is True  # return value unchanged
    assert calls == []  # defaults() NOT evaluated for a present key
