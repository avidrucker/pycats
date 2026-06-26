"""
Purpose: Persisted user preferences (#95) — currently display only.

Stores a small JSON file in the user config dir. Deliberately stdlib-only (no
new dependency, per #94) and **present-layer only**: the deterministic sim and
golden tests never read it — game.py is the sole caller (a leaf entry), so this
stays out of the sim path.

Env overrides (mirroring PYCATS_STATE_BACKEND):
- PYCATS_CONFIG_DIR — redirect the config dir (tests point this at a tmp_path).
- PYCATS_NO_PERSIST=1 — disable all I/O (load returns defaults, save is a no-op).

Use: settings.load() at startup; settings.save({...}) on a display change.
"""
import json
import os

from .display import WINDOWED_SCALE_PRESETS

SCHEMA_VERSION = 1
_DEFAULTS = {"version": SCHEMA_VERSION, "windowed_scale": 1.0, "fullscreen": False}


def defaults():
    """A fresh copy of the default preferences."""
    return dict(_DEFAULTS)


def _config_dir():
    override = os.environ.get("PYCATS_CONFIG_DIR")
    if override:
        return override
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    return os.path.join(base, "pycats")


def config_path():
    """Absolute path of the settings file."""
    return os.path.join(_config_dir(), "settings.json")


def _persist_disabled():
    return bool(os.environ.get("PYCATS_NO_PERSIST"))


def _validated(raw):
    """Known keys merged over defaults, validated. Unknown keys ignored, missing
    keys defaulted, out-of-range values snapped — a settings file is a hint, not
    an authority."""
    out = defaults()
    scale = raw.get("windowed_scale")
    if scale in WINDOWED_SCALE_PRESETS:  # snap invalid scales to a valid preset
        out["windowed_scale"] = float(scale)
    out["fullscreen"] = bool(raw.get("fullscreen", out["fullscreen"]))
    return out


def load():
    """Persisted preferences merged over defaults. Returns defaults on a missing,
    unreadable, or malformed file — never raises."""
    if _persist_disabled():
        return defaults()
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):  # missing / unreadable / not valid JSON
        return defaults()
    if not isinstance(raw, dict):
        return defaults()
    return _validated(raw)


def save(prefs):
    """Write `prefs` (validated, stamped with the schema version) as JSON,
    creating the config dir if needed. No-op when persistence is disabled."""
    if _persist_disabled():
        return
    data = _validated(prefs)
    data["version"] = SCHEMA_VERSION
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
