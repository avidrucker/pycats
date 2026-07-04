# pycats/keybind_store.py
#
# Persistence for named keybinding sets (#440). A "set" is a per-player control scheme
# (action -> key), saved under a user name in `profiles/keybindings.json` (the #95
# config dir). Bindings serialize as key NAMES (pygame.key.name) — human-readable and
# resilient to keycode drift. Pure I/O + serialization; no UI.
from __future__ import annotations

import json
import os

import pygame

from . import settings


def _store_path():
    return os.path.join(settings._config_dir(), "profiles", "keybindings.json")


def _read():
    """All sets as {name: {action: keyname}}. Missing/corrupt file -> {} (no crash)."""
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


def save_set(name, keymap):
    """Save `keymap`'s bindings under `name` as key names (overwrites an existing name)."""
    data = _read()
    data[name] = {action: pygame.key.name(code) for action, code in keymap.items()}
    _write(data)


def list_sets():
    return sorted(_read().keys())


def delete_set(name):
    """Remove the named set (a no-op if it doesn't exist)."""
    data = _read()
    if data.pop(name, None) is not None:
        _write(data)


def _name_to_code(name):
    """Keycode for a key name, or None if missing / unparseable."""
    if not name:
        return None
    try:
        return pygame.key.key_code(name)
    except (ValueError, TypeError):
        return None


def load_set(name, into_keymap):
    """Apply the saved set `name` onto `into_keymap`, in place, by WHOLESALE REPLACE
    (not sequential rebinds — so an intra-set key swap can't raise a transient
    KeyBindingConflict). An action missing from the set, or whose saved name won't
    parse, falls back to that action's factory default. Returns `into_keymap`."""
    saved = _read().get(name, {})
    into_keymap.reset()                       # factory baseline for the fallbacks
    resolved = {}
    for action in list(into_keymap.keys()):
        code = _name_to_code(saved.get(action))
        resolved[action] = code if code is not None else into_keymap[action]
    into_keymap.clear()
    into_keymap.update(resolved)
    return into_keymap
