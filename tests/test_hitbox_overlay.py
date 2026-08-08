"""Hit/hurtbox debug overlay (#219, split from #217) — dev-gated + backtick-coupled (#1324).

A render-only DEV tool that draws every active attack's hitbox circles and every
fighter's hurtbox circles as coloured outlines, reading the SAME data
hit_resolution.process_hits resolves (``atk.resolved`` + ``resolve_circle`` on the
fighter hurtbox). Combat is untouched; ``Attack.rect`` is untouched (Attack.image was removed in #326).

#1324 (B2 reconciliation on #1297) retired the persisted ``show_hitbox_overlay`` pref
and its Options-menu row. The overlay now renders only when BOTH the process-wide
dev-mode gate (#1312) AND the dev-HUD master switch (#1319) are on:
  - Outside dev mode it never draws (the shipping build no longer shows it).
  - Inside dev mode it follows backtick — game.main seeds dev_hud = dev_mode() at boot,
    so it defaults ON, and each backtick press flips the text dev HUD and this overlay
    together.
"""

import types

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import render_battle as rb  # noqa: E402
from pycats.combat.data import Circle, Hurtbox  # noqa: E402
from pycats.screens.options_menu import OptionsMenu  # noqa: E402
from pycats.storage import runtime_settings, settings  # noqa: E402

P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v, "special": pygame.K_c}
P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH, "special": pygame.K_PERIOD}


# --------------------------------------------------------------------------- #
# #1324 — persisted pref + Options row retired
# --------------------------------------------------------------------------- #
def test_show_hitbox_overlay_pref_retired():
    # The overlay is no longer a persisted player toggle (#1324) — the schema
    # default and the runtime accessor are both gone.
    assert "show_hitbox_overlay" not in settings.defaults()
    assert not hasattr(runtime_settings, "show_hitbox_overlay")


def test_hitbox_overlay_row_absent_from_options():
    runtime_settings.seed(settings.defaults())
    m = OptionsMenu(P1, P2)
    assert "hitbox_overlay" not in m.rows


# --------------------------------------------------------------------------- #
# render_battle.render_hitbox_overlay — the drawing itself
# --------------------------------------------------------------------------- #
def _enable_overlay():
    """Put the overlay's gate (#1324) into its rendering state: dev mode ON + dev HUD ON."""
    runtime_settings.set_dev_mode(True)
    runtime_settings.set_dev_hud(True)


def _fake_player(
    x=100,
    y=100,
    w=40,
    h=60,
    facing_right=True,
    alive=True,
    state="idle",
    hurtbox=None,
    crouch_hurtbox=None,
    prone_hurtbox=None,
):
    hb = hurtbox or Hurtbox(circles=(Circle(dx=20, dy=30, r=25),))
    fighter = types.SimpleNamespace(
        is_alive=alive,
        facing_right=facing_right,
        crouch_hurtbox=crouch_hurtbox,
        prone_hurtbox=prone_hurtbox,
    )
    return types.SimpleNamespace(
        rect=pygame.Rect(x, y, w, h),
        state=state,
        fighter=fighter,
        fighter_data=types.SimpleNamespace(hurtbox=hb),
    )


def _fake_attack(circles):
    # circles: list of (cx, cy, r); box payload is irrelevant to the overlay.
    return types.SimpleNamespace(resolved=[(cx, cy, r, object()) for (cx, cy, r) in circles])


def _spy_circles(monkeypatch):
    captured = []

    def spy(surface, color, center, radius, width=0, *a, **k):
        captured.append((tuple(color), tuple(center), radius, width))

    monkeypatch.setattr(pygame.draw, "circle", spy)
    return captured


# ---- the gate (#1324): dev_mode() AND dev_hud() ---- #
@pytest.mark.usefixtures("render_isolation")
def test_overlay_off_outside_dev_mode(monkeypatch):
    # Even with the dev-HUD master switch ON, no dev mode → the overlay never draws
    # (the shipping build). Able-to-fail: drop the dev_mode() half of the gate and the
    # dev_hud() ON below would draw the circles.
    runtime_settings.seed(settings.defaults())
    runtime_settings.set_dev_mode(False)
    runtime_settings.set_dev_hud(True)
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))
    rb.render_hitbox_overlay(surf, [_fake_player()], [_fake_attack([(50, 50, 10)])])
    assert captured == []


@pytest.mark.usefixtures("render_isolation")
def test_overlay_off_when_dev_hud_off_inside_dev_mode(monkeypatch):
    # Inside dev mode the overlay follows the backtick master switch (dev_hud). HUD OFF
    # → overlay OFF. Able-to-fail: drop the dev_hud() half of the gate and this draws.
    runtime_settings.seed(settings.defaults())
    runtime_settings.set_dev_mode(True)
    runtime_settings.set_dev_hud(False)
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))
    rb.render_hitbox_overlay(surf, [_fake_player()], [_fake_attack([(50, 50, 10)])])
    assert captured == []


@pytest.mark.usefixtures("render_isolation")
def test_overlay_on_draws_hit_and_hurtbox_outlines(monkeypatch):
    runtime_settings.seed(settings.defaults())
    _enable_overlay()
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))

    player = _fake_player(x=100, y=100, w=40, facing_right=True, hurtbox=Hurtbox(circles=(Circle(dx=20, dy=30, r=25),)))
    attack = _fake_attack([(200, 150, 12)])
    rb.render_hitbox_overlay(surf, [player], [attack])

    colors = {c[0] for c in captured}
    assert rb.HITBOX_OVERLAY_COLOR in colors
    assert rb.HURTBOX_OVERLAY_COLOR in colors
    assert rb.HITBOX_OVERLAY_COLOR != rb.HURTBOX_OVERLAY_COLOR  # distinct

    # Hitbox drawn at the resolved attack circle.
    assert any(c[0] == rb.HITBOX_OVERLAY_COLOR and c[1] == (200, 150) and c[2] == 12 for c in captured)
    # Hurtbox drawn at resolve_circle(dx=20,dy=30) for a right-facer at (100,100):
    # cx = 100 + 20, cy = 100 + 30, r = 25.
    assert any(c[0] == rb.HURTBOX_OVERLAY_COLOR and c[1] == (120, 130) and c[2] == 25 for c in captured)
    # Every circle is an OUTLINE (positive line width), never a filled disc.
    assert all(c[3] > 0 for c in captured)


@pytest.mark.usefixtures("render_isolation")
def test_overlay_skips_dead_fighters(monkeypatch):
    runtime_settings.seed(settings.defaults())
    _enable_overlay()
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))
    rb.render_hitbox_overlay(surf, [_fake_player(alive=False)], [])
    assert all(c[0] != rb.HURTBOX_OVERLAY_COLOR for c in captured)
    assert captured == []  # no attacks, dead fighter → nothing


@pytest.mark.usefixtures("render_isolation")
def test_overlay_uses_active_crouch_hurtbox(monkeypatch):
    """Mirrors hit_resolution.process_hits: a crouching fighter shows its crouch box."""
    runtime_settings.seed(settings.defaults())
    _enable_overlay()
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))

    crouch = Hurtbox(circles=(Circle(dx=20, dy=50, r=15),))
    player = _fake_player(
        x=100, y=100, state="crouch", crouch_hurtbox=crouch, hurtbox=Hurtbox(circles=(Circle(dx=20, dy=30, r=25),))
    )
    rb.render_hitbox_overlay(surf, [player], [])

    hurt = [c for c in captured if c[0] == rb.HURTBOX_OVERLAY_COLOR]
    assert hurt and all(c[2] == 15 for c in hurt)  # crouch radius, not stand's 25
    assert any(c[1] == (120, 150) for c in hurt)  # crouch dy=50 → cy=150
