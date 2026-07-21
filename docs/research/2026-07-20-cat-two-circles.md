# The two circles rendered on each cat — what they are, why, and whether they work (#805)

**Role:** RESEARCH · `area:display` · findings only (any change is a downstream DEV ticket).
**Date:** 2026-07-20 · **Agent:** cherry.

## TL;DR

The two circles are each fighter's **hurtbox** — the 2-circle body stack (upper + lower) — outlined in **cyan** by the **hit/hurtbox debug overlay** (`render_hitbox_overlay`, #219). They are visible because the overlay is **shipping ON by default**, which is a **stale temporary default**: `settings.py` flipped it on (#239) for the #125 combat-visuals work with an explicit "revert to OFF before release" note. The revert is already an open ticket — **#241**. Recommendation: **execute #241** (flip the default to `False`); the overlay itself is correct and stays available via the Options toggle.

---

## Q1 — What are they?

Each cat shows **two cyan circle outlines** = its **hurtbox**, the vulnerable body the combat resolver tests against. For Nalio that is `_HURTBOX = Circle(dx=20, dy=15, r=14)` (upper body) + `Circle(dx=20, dy=45, r=14)` (lower body) — `pycats/characters/nalio_cat.py`. Every fighter's `FighterData.hurtbox` is a stack of such circles.

**Draw site:** `render_hitbox_overlay()` in `pycats/render_battle.py` (def at ~line 1188). The hurtbox loop (~line 1205) walks `_active_hurtbox(p).circles`, maps each facing-relative `Circle(dx,dy,r)` to an absolute centre via `resolve_circle(c, p.rect.x, p.rect.y, p.fighter.facing_right, p.rect.width)`, and outlines it in `HURTBOX_OVERLAY_COLOR = (0,255,255)` (cyan). Called from `pycats/battle_screen.py:156` and `:185`.

Same overlay also draws **red** hitbox circles from `atk.resolved` when a cat is attacking (`HITBOX_OVERLAY_COLOR = RED`) — so during an attack you additionally see red circles. The steady-state "two circles on each cat" are the cyan hurtbox pair.

**What they are NOT:** not cosmetic cat features, not an origin/anchor marker. (The separate *cosmetic* eye is `draw_eye()` — a single eye disc + a small glint — but that only renders on the primitive face path, `face_style == PRIMITIVES`, and reads as one eye-with-highlight, not a matched pair. The matched cyan pair is the hurtbox overlay.)

## Q2 — Why were they added?

A **dev-facing hit/hurtbox visualiser**, added in **#219** ("toggleable hit/hurtbox debug overlay — see the boxes live"), toggleable live from the Options sub-menu (mirroring the other battle HUD toggles).

Its default was then **temporarily flipped ON** in **#239** ("default the hit/hurtbox overlay ON during development — temporary, revert before release") to support the **#125** epic ("Nalio attack VISUALS — per-move animation + FX"). The intent is recorded verbatim at the setting:

> `pycats/settings.py:30-34` — *"Hit/hurtbox debug overlay (#219): a dev-facing box visualiser toggled live from the Options sub-menu… **TEMPORARILY defaulted ON (#239) for the #125 combat-visuals work; revert to OFF before release (#241).**"*
> `"show_hitbox_overlay": True`

## Q3 — Are they doing their intended job?

**As a visualiser: yes, correctly.** The overlay reads the *same* data the combat resolver uses — `_active_hurtbox(p)` mirrors `combat.process_hits`' hurtbox selection, including the #124 crouch / #173 prone lowered boxes — so the cyan circles faithfully track the live `FighterData.hurtbox`, not a stale copy. It is render-only and does not affect the sim.

**As a shipped default: no — it is drift.** It is a **debug** overlay, and it is currently visible in the **normal, player-facing** battle view. That contradicts two recorded intents:

- `render_hitbox_overlay`'s own docstring (`render_battle.py:~1193`): *"Default OFF, so the live game and goldens are untouched until a dev flips it on from Options."*
- The `settings.py` note to revert to OFF before release (#241).

So the circles are not a bug in the overlay; they are a **stale temporary development default** (`settings.py` `show_hitbox_overlay: True`) that outlived the #125/#239 work it was enabled for.

## Q4 — Recommendation

**Fix the drift: flip `settings.py` `show_hitbox_overlay` default to `False`.** This is exactly the already-open **#241** ("DEV: revert hit/hurtbox overlay back to default OFF before release") — no new ticket needed; this doc is the evidence to action it. The Options toggle stays, so devs can still turn the overlay on live.

Keep the overlay code as-is (it works). Do **not** repurpose it into an always-on player feature — if an always-on hurtbox display is ever wanted, that is a separate design decision, and the docstring/#241 would need reconciling; the default-ON state today is unintentional, not a chosen feature.

**Coupling to flag for the #241 DEV slice (render-affecting):** flipping this default changes the rendered battle frame, so it will move the render-parity oracle and the overlay's own tests — expect to update `tests/test_battle_screen_render.py` and `tests/test_hitbox_overlay.py` (and any #219 golden). This is a *render* change, not a sim change (the sim goldens are overlay-free).

---

## Landmarks

- Draw site: `pycats/render_battle.py` — `render_hitbox_overlay()` (~L1188; hurtbox loop ~L1205), `_active_hurtbox()` (~L1172), colours `HURTBOX_OVERLAY_COLOR`/`HITBOX_OVERLAY_COLOR` (L97-98).
- Coordinate map: `pycats/combat/geometry.py` `resolve_circle`.
- Data: `pycats/characters/nalio_cat.py` `_HURTBOX`; `FighterData.hurtbox` in `pycats/combat/data.py`.
- Toggle default: `pycats/settings.py:34` `"show_hitbox_overlay": True` (+ intent comment L30-33).
- Getter/consumer: `pycats/runtime_settings.py:41` `show_hitbox_overlay()`; `pycats/battle_screen.py:156,185`; Options row `pycats/options_menu.py:278-280`.
- Tests coupled: `tests/test_hitbox_overlay.py`, `tests/test_battle_screen_render.py`.

## Tickets

#805 (this research) · #219 (overlay feature, closed) · #239 (temporary default-ON, closed) · **#241 (revert to OFF — OPEN, the action item)** · #125 (Nalio attack VISUALS epic — the work #239 supported, open). Adjacent: #792 (hit/hurtbox editor tracker — the overlay's `render_hitbox_overlay` + `resolve_circle` are reused there).
