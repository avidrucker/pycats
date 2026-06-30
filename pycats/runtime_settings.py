"""Present-layer live settings (#121).

Holds the current values of user-tunable settings so the render path and game
loop read *live* values the Options menu can change mid-session — not the frozen
module constants they replaced (e.g. config.SHOW_STATUS_TIMER_BARS). Seeded from
settings.load() at startup (game.py).

Like settings.py this is **present-layer only**: the deterministic sim and the
golden tests never read it. Keys mirror the persisted schema in settings.py.
"""
from . import settings

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
