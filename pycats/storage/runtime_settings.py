"""Present-layer live settings (#121).

Holds the current values of user-tunable settings so the render path and game
loop read *live* values the Options menu can change mid-session — not the frozen
module constants they replaced (e.g. config.SHOW_STATUS_TIMER_BARS). Seeded from
settings.load() at startup (game.py).

Like settings.py this is **present-layer only**: the deterministic sim and the
golden tests never read it. Keys mirror the persisted schema in settings.py.
"""

from .. import config
from . import settings

_state = settings.defaults()

# Process-wide dev-mode gate (#1312, ruling A1 on #1297). Deliberately NOT part of
# `_state`: dev_mode is a per-launch flag sourced from the --dev CLI arg / PYCATS_DEV
# env (game.main), never a persisted preference, so seed() must not touch it. One owner
# every dev-gated surface reads via dev_mode() (later #1311 slices: char-select, HUD,
# overlays, F1 screen). Default off — the shipping/default launch is unchanged.
_dev_mode = False

# Process-wide dev-HUD toggle (#1319, ruling C1–C4 on #1297). Like _dev_mode it is
# deliberately NOT part of `_state`: it is a per-session runtime toggle, never a
# persisted preference, so seed() must not touch it and it survives a pause/resume
# (nothing on the pause path resets it). Default OFF at every launch — the shipping
# default battle HUD is minimal (player label + emphasized Lives/Damage % only).
# Flipped by the backtick/tilde key (shell/app.py), available to everyone (not
# dev_mode-gated). ON shows the complete dev HUD; it is the SOLE battle-HUD driver. It
# superseded the legacy per-item flags show_dev_info / show_movement_status /
# show_input_history in battle (#1319), which are now retired entirely (#1328).
_dev_hud = False


def seed(prefs=None):
    """Replace the live state from `prefs` (or settings.load() if omitted).

    Called once at startup, after settings.load(). Copies so later mutation of the
    live state never writes back through the caller's dict."""
    global _state
    _state = dict(prefs) if prefs is not None else settings.load()


def get(key):
    """Current live value for `key`, falling back to the schema default.

    The present-key path (the hot one — the render loop reads ~160 keys/frame)
    allocates nothing: only a genuinely-absent key pays for a fresh defaults()
    dict. Guarding this, rather than passing settings.defaults() as `dict.get`'s
    default arg, avoids minting a throwaway ~15-key copy on every read (#1262/B3)."""
    if key in _state:
        return _state[key]
    return settings.defaults().get(key)


def set(key, value):
    """Update the live value for `key` (does not persist — caller saves)."""
    _state[key] = value


def set_dev_mode(value):
    """Set the process-wide dev-mode gate (#1312). Called once at boot (game.main) from
    the resolved --dev / PYCATS_DEV state; not persisted. Idempotent — pass a bool."""
    global _dev_mode
    _dev_mode = bool(value)


def toggle_dev_mode():
    """Flip the process-wide dev-mode gate and return the new state (#1328, A1's third
    door on #1297). The F1 key handler (shell/app.py) calls this once per press to
    enter/leave dev mode live in-game; the caller syncs dev_hud to the new state so
    F1-on shows the dev HUD + hit/hurtbox overlay and F1-off restores the shipping
    default look. Not persisted — like set_dev_mode it is a per-session flag."""
    global _dev_mode
    _dev_mode = not _dev_mode
    return _dev_mode


def dev_mode():
    """Live process-wide dev-mode flag (#1312, ruling A1 on #1297). False in the default
    launch; True when started with --dev or a truthy PYCATS_DEV, and flippable in-game by
    F1 (#1328). The single owner every dev-gated surface reads (char-select roster #1292,
    the hit/hurtbox overlay gate #1324)."""
    return _dev_mode


def set_dev_hud(value):
    """Set the process-wide dev-HUD toggle (#1319). Not persisted; survives pause.
    Idempotent — pass a bool."""
    global _dev_hud
    _dev_hud = bool(value)


def toggle_dev_hud():
    """Flip the dev-HUD toggle and return the new state (#1319). The backtick/tilde
    key handler (shell/app.py) calls this once per press."""
    global _dev_hud
    _dev_hud = not _dev_hud
    return _dev_hud


def dev_hud():
    """Live process-wide dev-HUD flag (#1319, ruling C1–C4 on #1297). Default OFF —
    the battle HUD is minimal (player label + emphasized Lives/Damage % corners). ON
    shows the complete dev HUD (jumps / Shield HP / FSM / Shield Attempting / Movement
    rows + FPS + raw input string + the input-history grid). The SOLE battle-HUD driver:
    ON shows the whole dev HUD; OFF hides all of it. (It superseded the legacy per-item
    flags show_dev_info / show_movement_status / show_input_history in #1319; those were
    retired in #1328.)"""
    return _dev_hud


def show_status_timer_bars():
    """Live HUD toggle the status-bar render path honours (#111/#121)."""
    return bool(get("show_status_timer_bars"))


# show_hitbox_overlay() retired #1324: the hit/hurtbox overlay (#219) is no longer a
# persisted player toggle. Its render gate (render_hitbox_overlay) now reads
# dev_mode() and dev_hud() — dev-gated + backtick-coupled, per B2 reconciliation (#1297).
#
# show_input_history() / show_dev_info() / show_movement_status() retired #1328: dev_hud
# became the sole battle-HUD driver in #1319, leaving these three per-item flags as no-ops
# in battle. #1328 removes them (accessors + persisted keys + the two Options rows) — the
# input-history grid, the FSM/Shield-Attempting jargon rows, and the Movement row all
# render as part of the complete dev HUD, gated on dev_hud() alone (render/hud.py).


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


def show_idle_breathing():
    """Live toggle the idle-stance breathing animation honours (#567). Default on —
    a subtle looping body-height oscillation in the idle state so cats read as alive;
    off renders the idle body byte-identical to a static frame."""
    return bool(get("show_idle_breathing"))


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
