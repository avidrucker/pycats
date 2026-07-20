"""Idle-stance breathing animation (#567).

A fighter in the `idle` FSM state renders a subtle looping vertical body-height
oscillation (feet planted) so a resting cat reads as alive. The effect is render-only
(driven by the per-player `_breath_phase` accumulator, never the sim), gated on a live
settings toggle (`show_idle_breathing`, default ON), and PER ARCHETYPE: only archetypes
with a datamined `Wait1` period breathe. Nalio's period is sourced from PM Mario's Wait1
loop (51 frames, brawllib_rs #753) split into the 2 breaths-per-loop read off the
rendered GIF (#567 review) → 25.5 frames/breath.

These tests pin: (1) the pure gate+waveform helper, (2) that the render path advances the
phase ONLY when the effect is live, and (3) that the effect changes pixels while keeping
the feet planted. Able-to-fail: revert the render wiring and the integration tests go red;
break the gate and the "no phase when …" tests go red.
"""

import pygame
import pytest

from pycats import runtime_settings, settings
from pycats.combat.data import load_fighter_data
from pycats.core.input import InputFrame
from pycats.domain.registry import character_for
from pycats.entities import Player
from pycats.entities.platform import Platform
from pycats.render_battle import (
    IDLE_BREATH_AMPLITUDE_PX,
    idle_breath_offset_px,
    render_battle,
)

_CONTROLS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)

# Nalio's breath period: 51-frame Wait1 loop / 2 breaths (see module docstring).
_PERIOD = 51 / 2
_SENTINEL = (1, 2, 3)  # background fill != any body colour, so black outline counts as body


def _nalio():
    return Player(
        100,
        100,
        _CONTROLS,
        (255, 0, 0),
        eye_color=(0, 0, 0),
        char_name="P1",
        facing_right=True,
        fighter_data=load_fighter_data("nalio"),
        character=character_for("nalio"),
    )


def _default_cat():
    # No `character` → character.key is None → no datamined period → never breathes.
    return Player(100, 100, _CONTROLS, (255, 0, 0), eye_color=(0, 0, 0), char_name="P1", facing_right=True)


def _ground():
    return [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]


def _settle(p, plats, n=6):
    grp = pygame.sprite.Group()
    for _ in range(n):
        p.update(InputFrame(held=set(), pressed=set(), released=set()), plats, grp)


def _lowest_body_row(surf, cx):
    """y of the bottommost non-background pixel in column cx (the fighter's feet)."""
    low = None
    for y in range(surf.get_height()):
        if tuple(surf.get_at((cx, y)))[:3] != _SENTINEL:
            low = y
    return low


# --- the pure gate + waveform helper -----------------------------------------


def test_offset_zero_at_phase_zero():
    assert idle_breath_offset_px("nalio", "idle", 0.0) == 0.0


def test_offset_peaks_at_quarter_period():
    # sin(2π · (P/4) / P) = sin(π/2) = 1 → full amplitude
    assert idle_breath_offset_px("nalio", "idle", _PERIOD / 4) == pytest.approx(IDLE_BREATH_AMPLITUDE_PX)


def test_offset_returns_to_zero_at_half_period():
    assert idle_breath_offset_px("nalio", "idle", _PERIOD / 2) == pytest.approx(0.0, abs=1e-9)


def test_offset_bounded_by_amplitude():
    for i in range(400):
        v = idle_breath_offset_px("nalio", "idle", i * 0.5)
        assert -IDLE_BREATH_AMPLITUDE_PX - 1e-9 <= v <= IDLE_BREATH_AMPLITUDE_PX + 1e-9


def test_offset_zero_when_not_idle():
    for st in ("crouch", "prone", "fall", "jump", "shield", "walk"):
        assert idle_breath_offset_px("nalio", st, _PERIOD / 4) == 0.0


def test_offset_zero_when_disabled():
    assert idle_breath_offset_px("nalio", "idle", _PERIOD / 4, enabled=False) == 0.0


def test_offset_zero_for_archetype_without_period():
    # Narz/Birky are not datamined yet; None is the sim/test path. Neither breathes.
    assert idle_breath_offset_px("birky", "idle", _PERIOD / 4) == 0.0
    assert idle_breath_offset_px("narz", "idle", _PERIOD / 4) == 0.0
    assert idle_breath_offset_px(None, "idle", _PERIOD / 4) == 0.0


# --- render path advances the phase clock ONLY when the effect is live -------


def test_render_advances_phase_in_idle():
    runtime_settings.seed(settings.defaults())
    p = _nalio()
    _settle(p, _ground())
    assert p.state == "idle"
    render_battle(pygame.Surface((640, 480)), [p], [])
    assert getattr(p, "_breath_phase", 0.0) == 1.0


def test_render_no_phase_when_not_idle():
    runtime_settings.seed(settings.defaults())
    p = _nalio()
    _settle(p, _ground())
    p.force_prone(30)
    assert p.state == "prone"
    render_battle(pygame.Surface((640, 480)), [p], [])
    assert getattr(p, "_breath_phase", 0.0) == 0.0


def test_render_no_phase_when_toggle_off():
    prefs = settings.defaults()
    prefs["show_idle_breathing"] = False
    runtime_settings.seed(prefs)
    p = _nalio()
    _settle(p, _ground())
    assert p.state == "idle"
    render_battle(pygame.Surface((640, 480)), [p], [])
    assert getattr(p, "_breath_phase", 0.0) == 0.0


def test_render_no_phase_for_non_archetype():
    runtime_settings.seed(settings.defaults())
    p = _default_cat()
    _settle(p, _ground())
    assert p.state == "idle"
    render_battle(pygame.Surface((640, 480)), [p], [])
    assert getattr(p, "_breath_phase", 0.0) == 0.0


# --- the effect changes pixels, and the feet stay planted --------------------


def test_breathing_changes_body_but_plants_feet():
    # OFF baseline: static idle body.
    prefs = settings.defaults()
    prefs["show_idle_breathing"] = False
    runtime_settings.seed(prefs)
    p_off = _nalio()
    _settle(p_off, _ground())
    off = pygame.Surface((640, 480))
    off.fill(_SENTINEL)
    render_battle(off, [p_off], [])
    cx = p_off.rect.centerx
    off_low = _lowest_body_row(off, cx)

    # ON at peak: seed phase so the render advances to the quarter period → +A px.
    runtime_settings.seed(settings.defaults())
    p_on = _nalio()
    _settle(p_on, _ground())
    p_on._breath_phase = _PERIOD / 4 - 1.0  # render_battle adds 1.0 → quarter period
    on = pygame.Surface((640, 480))
    on.fill(_SENTINEL)
    render_battle(on, [p_on], [])
    on_low = _lowest_body_row(on, cx)

    assert off_low is not None and on_low is not None
    # feet planted: the bottom of the body is unchanged by the breath lift.
    assert on_low == off_low
    # effect is real: at peak amplitude the composite differs from the static frame.
    assert pygame.image.tobytes(on, "RGBA") != pygame.image.tobytes(off, "RGBA")
