"""
Purpose: Persisted user preferences (#95) — currently display only.

Stores a small JSON file in the user config dir. Deliberately stdlib-only (no
new dependency, per #94) and **present-layer only**: the deterministic sim and
golden tests never read it — game.py is the sole caller (a leaf entry), so this
stays out of the sim path.

Env overrides (PYCATS_* convention):
- PYCATS_CONFIG_DIR — redirect the config dir (tests point this at a tmp_path).
- PYCATS_NO_PERSIST=1 — disable all I/O (load returns defaults, save is a no-op).

Use: settings.load() at startup; settings.save({...}) on a display change.
"""

import json
import os

from .config import FONT_SCALES
from .display import WINDOWED_SCALE_PRESETS

SCHEMA_VERSION = 1
_DEFAULTS = {
    "version": SCHEMA_VERSION,
    "windowed_scale": 1.0,
    "fullscreen": False,
    # HUD overlay toggle (#111), migrated from a config.py constant into persisted
    # prefs by #121 so the Options menu can flip it live + remember it.
    "show_status_timer_bars": True,
    # Hit/hurtbox debug overlay (#219): a dev-facing box visualiser toggled live
    # from the Options sub-menu, mirroring show_status_timer_bars. TEMPORARILY
    # defaulted ON (#239) for the #125 combat-visuals work; revert to OFF before
    # release (#241).
    "show_hitbox_overlay": True,
    # In-battle input-history HUD strip (#21): per-fighter last-10 raw inputs,
    # toggleable from the Options sub-menu (mirrors show_status_timer_bars).
    "show_input_history": True,
    # In-battle fighter-controls display (#284): the per-fighter control-scheme
    # readout below the HUD, now toggleable + persisted (was always-on). BATTLE
    # ONLY — the non-battle screens use show_screen_hints below (#681).
    "show_controls": True,
    # Non-battle screen action-hints (#681): when True, the menu / character-select /
    # win screens show their per-screen "which key does what" hints (incl. the
    # hold-ESC affordance the #549 audit found hidden). This is the NON-battle
    # counterpart of show_controls (battle only). Toggleable in Options; ON by default.
    "show_screen_hints": True,
    # Hold-ESC-to-navigate (#113, generalised #453): when True, holding ESC for 2s
    # pops one level up the screen ladder (sub-menu/battle → its parent) and quits
    # the app from main_menu. When False, ESC is inert (use B / the menus).
    # Toggleable in the Options sub-menu.
    "esc_hold_to_navigate": True,
    # Global font-scale (#345): "small"/"standard"/"large" — a UI-text size
    # multiplier the Options menu cycles. "standard" (1.0) is byte-identical.
    "font_scale": "standard",
    # Dev-info HUD flag (#545): when True the HUD shows the implementation-jargon
    # rows (FSM state, Shield Attempting bool); when False (default) only the
    # player-facing stats render. Mirrors show_status_timer_bars; an Options
    # toggle is a later child (#544).
    "show_dev_info": False,
    # Idle-stance breathing animation (#567): when True, a fighter in the idle FSM
    # state renders a subtle looping vertical body-height oscillation (feet planted)
    # so an idle cat reads as alive. Off → the idle body is byte-identical to a
    # static render. Mirrors show_status_timer_bars; an Options toggle is a later
    # child. ON by default (the feature is player-facing polish, not a dev tool).
    "show_idle_breathing": True,
}


def defaults():
    """A fresh copy of the default preferences."""
    return dict(_DEFAULTS)


def _config_dir():
    override = os.environ.get("PYCATS_CONFIG_DIR")
    if override:
        return override
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
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
    out["show_status_timer_bars"] = bool(raw.get("show_status_timer_bars", out["show_status_timer_bars"]))
    out["show_hitbox_overlay"] = bool(raw.get("show_hitbox_overlay", out["show_hitbox_overlay"]))
    out["show_input_history"] = bool(raw.get("show_input_history", out["show_input_history"]))
    out["show_controls"] = bool(raw.get("show_controls", out["show_controls"]))
    out["show_screen_hints"] = bool(raw.get("show_screen_hints", out["show_screen_hints"]))
    out["esc_hold_to_navigate"] = bool(raw.get("esc_hold_to_navigate", out["esc_hold_to_navigate"]))
    out["show_dev_info"] = bool(raw.get("show_dev_info", out["show_dev_info"]))
    out["show_idle_breathing"] = bool(raw.get("show_idle_breathing", out["show_idle_breathing"]))
    fs = raw.get("font_scale")
    if fs in FONT_SCALES:  # snap an unknown preset back to the default
        out["font_scale"] = fs
    return out


def load():
    """Persisted preferences merged over defaults. Returns defaults on a missing,
    unreadable, or malformed file — never raises."""
    if _persist_disabled():
        return defaults()
    try:
        with open(config_path(), encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):  # missing / unreadable / not valid JSON
        return defaults()
    if not isinstance(raw, dict):
        return defaults()
    return _validated(raw)


def save(prefs):
    """Write `prefs` merged over the currently-persisted prefs (validated, stamped
    with the schema version) as JSON, creating the config dir if needed. No-op when
    persistence is disabled.

    Merge-over-current (not over bare defaults) so a *partial* save — e.g. the
    Options menu flipping one HUD toggle — preserves the other saved keys instead
    of resetting them (#121)."""
    if _persist_disabled():
        return
    data = _validated({**load(), **prefs})
    data["version"] = SCHEMA_VERSION
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
