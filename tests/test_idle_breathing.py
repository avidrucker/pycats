"""Idle-stance breathing animation (#567, retuned #760).

A fighter in the `idle` FSM state renders a subtle looping breathing motion so a resting
cat reads as alive. GIF frame-analysis of Mario `Wait1` (#760) showed the motion is
mostly a whole-body vertical **bob** (translation, ±5.3% of body height — feet lift too),
plus a minor in-phase **squash** (body-height change, ±2.4%). So the effect is a bob
(`IDLE_BREATH_BOB_PX`) plus a small squash (`IDLE_BREATH_SQUASH_PX`), driven by one gated
waveform, NOT the feet-planted squash-only of the first #567 pass. Render-only (the
`_breath_phase` accumulator, never the sim), gated on the `show_idle_breathing` toggle
(default ON) and PER ARCHETYPE (only archetypes with a datamined `Wait1` period breathe).
Nalio's period = PM Mario `Wait1` loop 51f ÷ 2 breaths = 25.5 f/breath (brawllib_rs
#753 + GIF #567).

These tests pin: (1) the pure gate+waveform helper, (2) that the render path advances the
phase ONLY when the effect is live, and (3) that at the top of the breath the whole body
LIFTS (feet included) by ~the bob amplitude, with the head lifting more (the squash).
Able-to-fail: revert the render wiring and the integration tests go red; break the gate
and the "no phase when …" tests go red.
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
    IDLE_BREATH_BOB_PX,
    idle_breath_wave,
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


def _body_rows(surf, cx):
    """(topmost, bottommost) non-background pixel y in column cx — head top and feet."""
    top = bot = None
    for y in range(surf.get_height()):
        if tuple(surf.get_at((cx, y)))[:3] != _SENTINEL:
            if top is None:
                top = y
            bot = y
    return top, bot


# --- the pure gate + waveform helper -----------------------------------------


def test_wave_zero_at_phase_zero():
    assert idle_breath_wave("nalio", "idle", 0.0) == 0.0


def test_wave_peaks_at_quarter_period():
    # sin(2π · (P/4) / P) = sin(π/2) = 1 → full positive amplitude
    assert idle_breath_wave("nalio", "idle", _PERIOD / 4) == pytest.approx(1.0)


def test_wave_troughs_at_three_quarter_period():
    assert idle_breath_wave("nalio", "idle", 3 * _PERIOD / 4) == pytest.approx(-1.0)


def test_wave_returns_to_zero_at_half_period():
    assert idle_breath_wave("nalio", "idle", _PERIOD / 2) == pytest.approx(0.0, abs=1e-9)


def test_wave_bounded_by_unit():
    for i in range(400):
        v = idle_breath_wave("nalio", "idle", i * 0.5)
        assert -1.0 - 1e-9 <= v <= 1.0 + 1e-9


def test_wave_zero_when_not_idle():
    for st in ("crouch", "prone", "fall", "jump", "shield", "walk"):
        assert idle_breath_wave("nalio", st, _PERIOD / 4) == 0.0


def test_wave_zero_when_disabled():
    assert idle_breath_wave("nalio", "idle", _PERIOD / 4, enabled=False) == 0.0


def test_wave_zero_for_archetype_without_period():
    # Narz/Birky are not datamined yet; None is the sim/test path. Neither breathes.
    assert idle_breath_wave("birky", "idle", _PERIOD / 4) == 0.0
    assert idle_breath_wave("narz", "idle", _PERIOD / 4) == 0.0
    assert idle_breath_wave(None, "idle", _PERIOD / 4) == 0.0


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


# --- at the top of the breath the whole body lifts (bob), head more (squash) --


def test_breathing_bobs_whole_body_at_peak():
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
    off_top, off_low = _body_rows(off, cx)

    # ON at peak: seed phase so the render advances to the quarter period → w = +1.
    runtime_settings.seed(settings.defaults())
    p_on = _nalio()
    _settle(p_on, _ground())
    p_on._breath_phase = _PERIOD / 4 - 1.0  # render_battle adds 1.0 → quarter period
    on = pygame.Surface((640, 480))
    on.fill(_SENTINEL)
    render_battle(on, [p_on], [])
    on_top, on_low = _body_rows(on, cx)

    assert None not in (off_top, off_low, on_top, on_low)
    # whole-body BOB: at peak the feet LIFT by ~IDLE_BREATH_BOB_PX (feet are no longer
    # planted — this is the #760 motion change from the #567 feet-planted squash).
    feet_lift = off_low - on_low
    assert feet_lift > 0
    assert abs(feet_lift - IDLE_BREATH_BOB_PX) <= 1
    # in-phase SQUASH: the head lifts MORE than the feet (the body also stretches taller).
    head_lift = off_top - on_top
    assert head_lift > feet_lift
    # effect is real: at peak the composite differs from the static frame.
    assert pygame.image.tobytes(on, "RGBA") != pygame.image.tobytes(off, "RGBA")
