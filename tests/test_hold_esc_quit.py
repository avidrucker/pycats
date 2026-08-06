"""Tests for hold-ESC-to-quit feature (#113).

RED phase: these tests should FAIL before implementation, PASS after.

Config isolation is scoped per test by the ``_isolated_config`` fixture below
(``monkeypatch.setenv("PYCATS_CONFIG_DIR", tmp_path)``, auto-restored on
teardown) — not an import-time ``os.environ`` write. See #1257 (the #345
env-at-import class): ``settings._config_dir`` reads ``PYCATS_CONFIG_DIR``
lazily at call time, so no module-level override is needed, and pygame is not
used here at all.
"""

import pytest

from pycats.storage.settings import defaults, load, save


class TestSettingsToggle:
    """Test the esc_hold_to_navigate settings key."""

    @pytest.fixture(autouse=True)
    def _isolated_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))

    def test_default_is_true(self):
        """esc_hold_to_navigate should default to True (on by default)."""
        prefs = load()
        assert prefs.get("esc_hold_to_navigate") is True, "esc_hold_to_navigate should default to True"

    def test_save_and_load_toggle(self):
        """Toggling the setting should persist across load."""
        save({"esc_hold_to_navigate": False})
        prefs = load()
        assert prefs.get("esc_hold_to_navigate") is False, "esc_hold_to_navigate=False should persist"

        save({"esc_hold_to_navigate": True})
        prefs = load()
        assert prefs.get("esc_hold_to_navigate") is True, "esc_hold_to_navigate=True should persist"

    def test_unknown_keys_ignored(self):
        """Unknown keys in settings file should be ignored."""
        save({"esc_hold_to_navigate": False, "unknown_key": 42})
        prefs = load()
        assert "unknown_key" not in prefs
        assert prefs.get("esc_hold_to_navigate") is False

    def test_defaults_contain_all_required_keys(self):
        """The defaults dict must contain esc_hold_to_navigate."""
        d = defaults()
        assert "esc_hold_to_navigate" in d
