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


def _apply_saved(saved, into_keymap):
    """Apply a `{action: keyname}` dict onto `into_keymap`, in place, by WHOLESALE
    REPLACE (not sequential rebinds — so an intra-set key swap can't raise a transient
    KeyBindingConflict). An action missing from `saved`, or whose saved name won't
    parse, falls back to that action's factory default. Returns `into_keymap`.

    Shared by `load_set` (named schemes, #440) and `load_last_used` (the implicit
    slot, #1306)."""
    into_keymap.reset()  # factory baseline for the fallbacks
    resolved = {}
    for action in list(into_keymap.keys()):
        code = _name_to_code(saved.get(action))
        resolved[action] = code if code is not None else into_keymap[action]
    into_keymap.clear()
    into_keymap.update(resolved)
    return into_keymap


def load_set(name, into_keymap):
    """Apply the saved set `name` onto `into_keymap`, in place (wholesale replace with
    factory fallback — see `_apply_saved`). Returns `into_keymap`."""
    return _apply_saved(_read().get(name, {}), into_keymap)


# --- implicit "last used" slot (#1306, ruling C on #1305) ---------------------
# The auto-persisted counterpart of the explicit named schemes above: the bindings a
# player had when they quit are what they get on next launch. Stored in a DEDICATED
# file (not the named-sets file), keyed per player, so it never appears in
# `list_sets()`. An auto-trigger leaf entry (boot-load / exit-save, wired in game.py),
# so it honors the same PYCATS_NO_PERSIST kill-switch as settings (#95).


def _last_used_path():
    return os.path.join(settings._config_dir(), "profiles", "last_keybindings.json")


def _read_last_used():
    """The slot as {"p1": {action: keyname}, "p2": {...}}. Missing / corrupt /
    persistence-disabled -> {} (no crash)."""
    if settings._persist_disabled():
        return {}
    try:
        with open(_last_used_path(), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, ValueError, OSError):
        return {}


def save_last_used(p1_keymap, p2_keymap):
    """Persist BOTH players' live bindings to the implicit 'last used' slot as key
    NAMES (like `save_set`). No-op when persistence is disabled (PYCATS_NO_PERSIST)."""
    if settings._persist_disabled():
        return
    data = {
        "p1": {action: pygame.key.name(code) for action, code in p1_keymap.items()},
        "p2": {action: pygame.key.name(code) for action, code in p2_keymap.items()},
    }
    path = _last_used_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_last_used(p1_keymap, p2_keymap):
    """Apply the implicit 'last used' slot onto BOTH live keymaps, in place (wholesale
    replace with factory fallback — see `_apply_saved`). A missing slot / disabled
    persistence resets both to factory defaults. Returns `(p1_keymap, p2_keymap)`."""
    data = _read_last_used()
    _apply_saved(data.get("p1", {}), p1_keymap)
    _apply_saved(data.get("p2", {}), p2_keymap)
    return p1_keymap, p2_keymap
