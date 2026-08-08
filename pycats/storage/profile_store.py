# pycats/profile_store.py
#
# Persistence for named player profiles (#478, slice 1 of #441). A profile is
# `{ "keybinding_set": name|null, "stats": {} }`, saved under a nickname in
# `profiles/profiles.json` (the #95 config dir). Keybindings are referenced by the
# NAME of a saved set (#440's keybind_store), not inlined — one scheme, many
# profiles; `stats` is reserved empty for #442. Pure I/O + JSON; no UI. Mirrors
# keybind_store (#440): a missing or corrupt file degrades to empty, never crashes.
from __future__ import annotations

import json
import os

from . import settings


def _store_path():
    return os.path.join(settings._config_dir(), "profiles", "profiles.json")


def _read():
    """All profiles as {nick: profile}. Missing/corrupt file -> {} (no crash)."""
    try:
        with open(_store_path(), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, ValueError, OSError):
        return {}


def _write(data):
    path = _store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def save_profile(nick, profile):
    """Save `profile` under `nick` (overwrites an existing nick)."""
    data = _read()
    data[nick] = profile
    _write(data)


def load_profile(nick):
    """The profile saved under `nick`, or None if there is none."""
    return _read().get(nick)


def list_profiles():
    return sorted(_read().keys())


def delete_profile(nick):
    """Remove the named profile (a no-op if it doesn't exist)."""
    data = _read()
    if data.pop(nick, None) is not None:
        _write(data)
