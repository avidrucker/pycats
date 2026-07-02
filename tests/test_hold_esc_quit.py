"""Tests for hold-ESC-to-quit feature (#113).

RED phase: these tests should FAIL before implementation, PASS after.
"""
import os
import sys
import tempfile

# Isolate settings to a tmp dir so save/load don't touch the user's config.
_TMP_CONFIG = tempfile.mkdtemp(prefix="pycats_test_")
os.environ["PYCATS_CONFIG_DIR"] = _TMP_CONFIG
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

# Initialize pygame before importing pycats modules
pygame.init()

from pycats.settings import load, save, defaults


class TestSettingsToggle:
    """Test the esc_hold_to_quit settings key."""

    @pytest.fixture(autouse=True)
    def _isolated_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))

    def test_default_is_true(self):
        """esc_hold_to_quit should default to True (on by default)."""
        prefs = load()
        assert prefs.get("esc_hold_to_quit") is True, \
            "esc_hold_to_quit should default to True"

    def test_save_and_load_toggle(self):
        """Toggling the setting should persist across load."""
        save({"esc_hold_to_quit": False})
        prefs = load()
        assert prefs.get("esc_hold_to_quit") is False, \
            "esc_hold_to_quit=False should persist"

        save({"esc_hold_to_quit": True})
        prefs = load()
        assert prefs.get("esc_hold_to_quit") is True, \
            "esc_hold_to_quit=True should persist"

    def test_unknown_keys_ignored(self):
        """Unknown keys in settings file should be ignored."""
        save({"esc_hold_to_quit": False, "unknown_key": 42})
        prefs = load()
        assert "unknown_key" not in prefs
        assert prefs.get("esc_hold_to_quit") is False

    def test_defaults_contain_all_required_keys(self):
        """The defaults dict must contain esc_hold_to_quit."""
        d = defaults()
        assert "esc_hold_to_quit" in d
