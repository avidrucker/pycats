"""Present-layer live settings (#121).

Holds the current values of user-tunable settings so the render path and game
loop read *live* values the Options menu can change mid-session — not the frozen
module constants they replaced (e.g. config.SHOW_STATUS_TIMER_BARS). Seeded from
settings.load() at startup (game.py).

Like settings.py this is **present-layer only**: the deterministic sim and the
golden tests never read it. Keys mirror the persisted schema in settings.py.
"""

from . import config, settings

_state = settings.defaults()


def seed(prefs=None):
    """Replace the live state from `prefs` (or settings.load() if omitted).

    Called once at startup, after settings.load(). Copies so later mutation of the
    live state never writes back through the caller's dict."""
    global _state
    _state = dict(prefs) if prefs is not None else settings.load()


def get(key):
    """Current live value for `key`, falling back to the schema default."""
    return _state.get(key, settings.defaults().get(key))


def set(key, value):
    """Update the live value for `key` (does not persist — caller saves)."""
    _state[key] = value


def show_status_timer_bars():
    """Live HUD toggle the status-bar render path honours (#111/#121)."""
    return bool(get("show_status_timer_bars"))


def show_hitbox_overlay():
    """Live toggle the hit/hurtbox debug overlay render path honours (#219)."""
    return bool(get("show_hitbox_overlay"))


def show_input_history():
    """Live toggle the in-battle input-history HUD strip honours (#21)."""
    return bool(get("show_input_history"))


def show_controls():
    """Live toggle the in-battle fighter-controls display honours (#284). BATTLE
    ONLY — non-battle screens read show_screen_hints instead (#681)."""
    return bool(get("show_controls"))


def show_screen_hints():
    """Live toggle the non-battle screens' per-screen action hints honour (#681):
    the menu / character-select / win screens' key→action hints, incl. the hold-ESC
    affordance. The battle counterpart is show_controls."""
    return bool(get("show_screen_hints"))


def esc_hold_to_navigate():
    """Live value of the hold-ESC-to-navigate affordance (#113/#453). An ESC-hold
    resting hint is only drawn while this is on (a disabled ESC would mislead, #681)."""
    return bool(get("esc_hold_to_navigate"))


def show_dev_info():
    """Live toggle the HUD's dev-jargon rows (FSM / Shield Attempting) honour
    (#545). Default off — players never see it; a dev turns it on for debugging."""
    return bool(get("show_dev_info"))


def font_scale():
    """Live UI-text size multiplier (0.5 / 1.0 / 2.0) from the font_scale preset
    (#345). Unknown presets fall back to 1.0 (standard)."""
    return config.FONT_SCALES.get(get("font_scale"), 1.0)


def scaled_font_size(base):
    """An authored font size resolved through the live font_scale, clamped so a
    scaled-down size never rounds below config.MIN_FONT_PX (never 0/unreadable).
    At the "standard" scale this is the identity (round(base*1.0) == base), so the
    default render is byte-identical (#345)."""
    return max(config.MIN_FONT_PX, round(base * font_scale()))
