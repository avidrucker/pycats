"""Toggleable hit/hurtbox debug overlay (#219, split from #217).

A render-only DEV tool: a persisted, default-OFF toggle (mirroring the #111
status-bars toggle) that draws every active attack's hitbox circles and every
fighter's hurtbox circles as coloured outlines, reading the SAME data
combat.process_hits resolves (``atk.resolved`` + ``resolve_circle`` on the
fighter hurtbox). Combat is untouched; ``Attack.rect`` is untouched (Attack.image was removed in #326).
"""
import json
import types

import pygame  # noqa: E402
import pytest  # noqa: E402

from pycats import render_battle as rb  # noqa: E402
from pycats import runtime_settings, settings  # noqa: E402
from pycats.combat.data import Circle, Hurtbox  # noqa: E402
from pycats.options_menu import OptionsMenu  # noqa: E402


# --------------------------------------------------------------------------- #
# settings.py — persisted default-OFF toggle (mirrors show_status_timer_bars)
# --------------------------------------------------------------------------- #
def test_show_hitbox_overlay_defaults_on(tmp_path, monkeypatch):
    # #239: temporary dev default flipped ON for the #125 visuals work; reverted
    # to OFF before release (#241).
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    assert settings.defaults()["show_hitbox_overlay"] is True
    assert settings.load()["show_hitbox_overlay"] is True  # missing file


def test_show_hitbox_overlay_round_trips_and_coerces_bool(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    settings.save({"show_hitbox_overlay": True})
    assert settings.load()["show_hitbox_overlay"] is True
    with open(settings.config_path(), "w", encoding="utf-8") as f:
        f.write(json.dumps({"show_hitbox_overlay": 1}))
    assert settings.load()["show_hitbox_overlay"] is True  # coerced from 1


# --------------------------------------------------------------------------- #
# runtime_settings.py — live accessor the render path honours
# --------------------------------------------------------------------------- #
def test_runtime_hitbox_overlay_default_on():
    # #239 temporary dev default (ON); reverted to OFF before release (#241).
    runtime_settings.seed(settings.defaults())
    assert runtime_settings.show_hitbox_overlay() is True


def test_runtime_hitbox_overlay_set():
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_hitbox_overlay", True)
    assert runtime_settings.show_hitbox_overlay() is True


# --------------------------------------------------------------------------- #
# options_menu.py — Options row toggles live + persists (mirrors status_bars)
# --------------------------------------------------------------------------- #
P1 = {"up": pygame.K_w, "down": pygame.K_s, "attack": pygame.K_v, "special": pygame.K_c}
P2 = {"up": pygame.K_UP, "down": pygame.K_DOWN, "attack": pygame.K_SLASH,
      "special": pygame.K_PERIOD}
ATTACK = pygame.K_v


def test_hitbox_overlay_row_toggles_runtime_and_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_hitbox_overlay", False)  # known starting state
    m = OptionsMenu(P1, P2)
    m.selected_option = m.rows.index("hitbox_overlay")
    m.update({ATTACK})
    assert runtime_settings.show_hitbox_overlay() is True   # live flip
    assert settings.load()["show_hitbox_overlay"] is True   # persisted


def test_hitbox_overlay_row_label_reflects_state():
    runtime_settings.seed(settings.defaults())
    m = OptionsMenu(P1, P2)
    runtime_settings.set("show_hitbox_overlay", False)
    assert m._row_label("hitbox_overlay") == "Hitbox Overlay: OFF"
    runtime_settings.set("show_hitbox_overlay", True)
    assert m._row_label("hitbox_overlay") == "Hitbox Overlay: ON"


# --------------------------------------------------------------------------- #
# render_battle.render_hitbox_overlay — the drawing itself
# --------------------------------------------------------------------------- #
def _fake_player(x=100, y=100, w=40, h=60, facing_right=True, alive=True,
                 state="idle", hurtbox=None, crouch_hurtbox=None,
                 prone_hurtbox=None):
    hb = hurtbox or Hurtbox(circles=(Circle(dx=20, dy=30, r=25),))
    fighter = types.SimpleNamespace(
        is_alive=alive, facing_right=facing_right,
        crouch_hurtbox=crouch_hurtbox, prone_hurtbox=prone_hurtbox,
    )
    return types.SimpleNamespace(
        rect=pygame.Rect(x, y, w, h), state=state, fighter=fighter,
        fighter_data=types.SimpleNamespace(hurtbox=hb),
    )


def _fake_attack(circles):
    # circles: list of (cx, cy, r); box payload is irrelevant to the overlay.
    return types.SimpleNamespace(
        resolved=[(cx, cy, r, object()) for (cx, cy, r) in circles]
    )


def _spy_circles(monkeypatch):
    captured = []

    def spy(surface, color, center, radius, width=0, *a, **k):
        captured.append((tuple(color), tuple(center), radius, width))

    monkeypatch.setattr(pygame.draw, "circle", spy)
    return captured


@pytest.mark.usefixtures("render_isolation")
def test_overlay_off_draws_nothing(monkeypatch):
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_hitbox_overlay", False)  # explicitly OFF
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))
    rb.render_hitbox_overlay(surf, [_fake_player()], [_fake_attack([(50, 50, 10)])])
    assert captured == []


@pytest.mark.usefixtures("render_isolation")
def test_overlay_on_draws_hit_and_hurtbox_outlines(monkeypatch):
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_hitbox_overlay", True)
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))

    player = _fake_player(x=100, y=100, w=40, facing_right=True,
                          hurtbox=Hurtbox(circles=(Circle(dx=20, dy=30, r=25),)))
    attack = _fake_attack([(200, 150, 12)])
    rb.render_hitbox_overlay(surf, [player], [attack])

    colors = {c[0] for c in captured}
    assert rb.HITBOX_OVERLAY_COLOR in colors
    assert rb.HURTBOX_OVERLAY_COLOR in colors
    assert rb.HITBOX_OVERLAY_COLOR != rb.HURTBOX_OVERLAY_COLOR  # distinct

    # Hitbox drawn at the resolved attack circle.
    assert any(c[0] == rb.HITBOX_OVERLAY_COLOR and c[1] == (200, 150) and c[2] == 12
               for c in captured)
    # Hurtbox drawn at resolve_circle(dx=20,dy=30) for a right-facer at (100,100):
    # cx = 100 + 20, cy = 100 + 30, r = 25.
    assert any(c[0] == rb.HURTBOX_OVERLAY_COLOR and c[1] == (120, 130) and c[2] == 25
               for c in captured)
    # Every circle is an OUTLINE (positive line width), never a filled disc.
    assert all(c[3] > 0 for c in captured)


@pytest.mark.usefixtures("render_isolation")
def test_overlay_skips_dead_fighters(monkeypatch):
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_hitbox_overlay", True)
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))
    rb.render_hitbox_overlay(surf, [_fake_player(alive=False)], [])
    assert all(c[0] != rb.HURTBOX_OVERLAY_COLOR for c in captured)
    assert captured == []  # no attacks, dead fighter → nothing


@pytest.mark.usefixtures("render_isolation")
def test_overlay_uses_active_crouch_hurtbox(monkeypatch):
    """Mirrors combat.process_hits: a crouching fighter shows its crouch box."""
    runtime_settings.seed(settings.defaults())
    runtime_settings.set("show_hitbox_overlay", True)
    captured = _spy_circles(monkeypatch)
    surf = pygame.Surface((400, 400))

    crouch = Hurtbox(circles=(Circle(dx=20, dy=50, r=15),))
    player = _fake_player(x=100, y=100, state="crouch", crouch_hurtbox=crouch,
                          hurtbox=Hurtbox(circles=(Circle(dx=20, dy=30, r=25),)))
    rb.render_hitbox_overlay(surf, [player], [])

    hurt = [c for c in captured if c[0] == rb.HURTBOX_OVERLAY_COLOR]
    assert hurt and all(c[2] == 15 for c in hurt)  # crouch radius, not stand's 25
    assert any(c[1] == (120, 150) for c in hurt)   # crouch dy=50 → cy=150
