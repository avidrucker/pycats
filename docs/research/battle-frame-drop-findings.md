# Battle frame-rate drop (~60 → 20–40fps) with two cats active — findings

**Ticket:** #812 (RESEARCH, `area:display`) · **Date:** 2026-07-20 · **Agent:** ELDERBERRY

> **Scope.** #812 asks four questions: (Q1) can the drop be reproduced repeatably and
> re-watchably — fullscreen sim, windowed 1x, or both; (Q2) does the on-screen HUD showing
> vs not matter; (Q3) are there per-frame battle calculations that are currently unnecessary;
> (Q4) where does the frame budget actually go (sim vs render vs present). The **fix** is out
> of scope — it lands as a separate DEV ticket downstream of this doc.

## TL;DR

**The drop is a MOMENTARY dip, not a sustained low rate** — reproduced live on x11 (1920×1080),
**fullscreen, 60-capped**, during a **heavy ground-level exchange** (both cats attacking / dodging
/ jumping close together — the scenario Avi flagged). Individual frames spike to **20–47 ms
(≈21–50 fps instantaneous)** while the mean stays ~7–14 ms, so the on-screen counter (a rolling
average) momentarily reads 20–40 before recovering. Plain jumping / spread-out play does **not**
dip — it takes a busy exchange to push frames over the 16.6 ms budget.

Two additive causes, both amplified by a busy scene:

- **(A) Per-frame transient-surface churn → GC pauses.** The render allocates fresh surfaces every
  frame — `_attack_surface` per live attack, the shield-bubble `SRCALPHA` per shielding fighter,
  mixed-text, dilated silhouettes on tint flips, the breathing/crouch `transform.scale`. In a
  busy exchange this garbage triggers periodic `gc` collections that stall a frame. In the
  heaviest scene, **disabling GC cut over-budget frames from 27% to 9.5% and the worst spike from
  47 ms (21 fps) to 27 ms (37 fps)** — but the effect is scene-dependent and noisy across lighter
  scenes, so GC is *a* contributor, not the whole story.
- **(B) High baseline render in heavy exchanges.** With many attacks/effects on screen the mean
  frame climbs toward the 16.6 ms budget at fullscreen 2x, so ordinary jitter (GC, an OS
  scheduling blip, a cache miss) tips individual frames over. The worst frames stay 20–27 ms even
  with GC off — i.e. some frames are genuinely over budget on compute alone.

- **The present-scale blit is a real but secondary cost here.** Fullscreen on 1920×1080 is a clean
  **integer 2.0x → fast `scale`** and holds ~135 fps uncapped. Fractional scales (windowed 1.5x /
  2.5x, or a 1.5x F10 fullscreen zoom) take the ~2× slower `smoothscale`; windowed 2.5x is the one
  steady-state mode that flirts with the budget. Not the cause of the fullscreen momentary dip.
- **Sim is not a factor** (`BattleScreen.step` ≈ 0.05 ms). **HUD does not move the live needle**
  (Q2). **No leak** — caches bounded, render flat over 3000 frames.

**Highest-value fix (double win): cache the per-frame transient surfaces** (`_attack_surface`, the
shield bubble). It cuts baseline render (cause B) *and* the allocation churn that drives the GC
pauses (cause A) at once. GC tuning (`gc.freeze()`/disable-during-battle) is a secondary,
noisier lever. Details in "Recommended downstream work".

## Method

Two harness families, both scripting two nalio cats through a jump-and-move loop (`up` press
every 20 frames + an oscillating lateral hold) — the closest deterministic analogue to "two cats
jumping around the stage" — plus a full-combat variant driven by two real `AttackerController`
bots (so attacks / shields / fireball projectiles fire).

- **Live** (`prof_live.py` / `prof_fs.py` / `prof_fszoom.py` / `prof_combat.py`): the real x11
  video driver + a real `DisplayManager` window, uncapped, driving the actual present path
  (`dm.present()` → `scale_surface` + `pygame.display.flip()`). This is the reproduction Avi
  asked for and the primary evidence below.
- **Headless** (`prof_frame*.py`, SDL dummy): used only to *split* the per-phase budget
  (sim vs render vs present) and `cProfile` the render internals, since the dummy driver makes the
  present path nearly free and isolates the compute. Its absolute numbers understate the real
  present cost and are treated as relative shares only.

All scripts live in the scratchpad (not committed).

## Q4 — where the frame budget goes (per-phase split, headless, two cats jumping)

*Headless split isolates the phases; for real fps see the live table in Q1. The present row is
free headless and is the dominant real cost — the point of the split is to show sim ≈ 0 and render
≈ 1 ms, i.e. neither is the bottleneck.*

| Phase | Windowed 1x | Windowed 2x | Fullscreen (fractional 2.3x) |
|---|---|---|---|
| `BattleScreen.step` (sim) | 0.04 ms | 0.06 ms | 0.06 ms |
| `BattleScreen.render` (battle + HUD) | 1.03 ms | 1.14 ms | 1.14 ms |
| `display.scale_surface` present blit | 0.00 ms (no scale) | **3.87 ms** | **8.07 ms** |
| **total** | ~1.1 ms | ~5.1 ms | ~9.3 ms |
| headless ceiling | ~930 fps | ~197 fps | ~108 fps |

- **Sim is negligible** and constant. Whatever is happening on Avi's machine, it is not the
  battle simulation.
- **The present blit is the one cost that grows with the display mode.** At windowed 1x the game
  renders straight to the window (`DisplayManager`: `game_surface is screen`, no scale) — zero
  present cost. At any scale >1x or fullscreen, every frame pays a full-surface upscale.
- Fractional fullscreen zoom is **~2x** the cost of the integer windowed 2x because it takes the
  `smoothscale` branch (`display.scale_surface` → `pygame.transform.smoothscale` for non-integer
  scales; `pygame.transform.scale` for whole multiples).

## Q2 — does the HUD showing matter? Live: barely.

**On the live backend, no meaningful difference.** Windowed 2x, two cats jumping:

| HUD state | uncapped fps |
|---|---|
| HUD **on** (`show_controls` + `show_input_history` + `show_status_timer_bars`, all default ON) | ~129 |
| HUD **off** (all three overlays off) | ~125 |

Within noise — the present blit dominates so heavily that the HUD's cost disappears. So toggling
the HUD off is **not** a fix for the frame drop.

For completeness, *headless* (where the present path is free and the compute is isolated), HUD-off
halves battle render (0.71 ms → 0.37 ms), because the HUD goes through `text_utils.render_text` →
`render_text_simple`, the **uncached** text path (see Q3): 11 `render_text_simple` calls/frame with
two cats' HUD, each a fresh `font.render` + a separate `font.size` measure + a burst of
`runtime_settings` lookups. That is real waste worth fixing (Q3-1) — but it is second-order behind
the present blit, and the live test confirms it is not what causes the drop.

(The battle overlays are `show_controls` / `show_input_history` / `show_status_timer_bars`, all
default ON — `runtime_settings.py`. The bottom-right `FPS: xx.xx` readout in `draw_shell_chrome`
is ungated and always drawn during play.)

## Q3 — per-frame work that is currently unnecessary (named call sites)

All in the **render** path — the sim has none. Ranked by how hot the site is per frame:

1. **`text_utils.render_text` → `render_text_simple` re-rasterizes every frame (no cache).**
   `render_text_simple` calls `regular_font.render(...)` on every invocation; only the *mixed*
   text path (`_compose_mixed`) is cached. Worse, `render_text` (the convenience wrapper) *also*
   calls `font.size(text)` separately just to compute alignment width — a second per-call font
   measurement. Every HUD/timer-bar/dizzy/FPS readout hits this each frame. **Fix direction:**
   give `render_text_simple` the same `(text, size, color)` surface cache the mixed path already
   has (and cache the width alongside it).

2. **`runtime_settings.get` rebuilds the whole defaults dict on every call.**
   `get(key)` is `return _state.get(key, settings.defaults().get(key))` — Python evaluates the
   default argument eagerly, so `settings.defaults()` (which does `dict(_DEFAULTS)`) runs on
   **every** `get`, ~94 times/frame in the text path, purely as a fallback that is almost never
   taken. **Fix direction:** memoize `settings.defaults()` (or split the fallback so it's only
   built on a miss).

3. **Idle-breathing `pygame.transform.scale` per idle cat, every frame.**
   In `render_battle.render_battle`, an idle cat in an archetype with a datamined breath period
   (`nalio`) takes the breathing branch, which does `pygame.transform.scale` on *both* the ring
   and body layers each frame. This is why, headless, **two idle cats (1.78 ms) cost more than
   two jumping cats (0.90 ms)** — jumping cats aren't in the `idle` state, so they skip the
   scale and blit the cached layers directly. Not the reported (jumping) case, but a constant
   background cost whenever cats rest, and it grows per idle cat.

4. **`_attack_surface` is rebuilt from scratch every frame per live attack** (`render_battle`).
   Only fires while an attack is on screen, so it is not implicated in the plain jumping repro,
   but it is uncached per-frame surface construction worth noting for the DEV pass.

**No leak / no progressive degradation.** Over a 3000-frame jumping run the render time is flat
(~0.58 ms) and every cache is bounded: `_body_layers_cache` = 4, `_tail_seg_cache` plateaus at
340, `_mixed_surface_cache` = 36, `attacks` = 0. The drop is not a slow-growing structure.

## Q1 — can we reproduce it? Live x11, uncapped, two nalio cats

Reproduced on the actual display (`DISPLAY=:0`, x11 driver, monitor 1920×1080), real
`DisplayManager` present path, uncapped so the number is the *true achievable* rate:

| Mode | zoom | present transform | uncapped fps (jumping) | uncapped fps (full combat) |
|---|---|---|---|---|
| windowed 1x | 1.0 | none (renders to window) | ~511 | — |
| windowed 1.5x | 1.5 | `smoothscale` (fractional) | ~161 | — |
| windowed 2x | 2.0 | `scale` (integer) | ~123 | ~123 (worst frame 13 ms) |
| **windowed 2.5x** | **2.5** | **`smoothscale` (fractional)** | **~63–70** | **~63 (mean 16 ms, worst 19 ms)** |
| fullscreen | 2.0¹ | `scale` (integer) | ~134–148 | ~136 |
| fullscreen F10 zoom | 1.5 | `smoothscale` → 1440×810 | ~145 | — |

¹ On a 1920×1080 monitor the fullscreen "Fit" zoom is a clean **2.0x → 1920×1080**, the fast
integer `scale` path — so native fullscreen is *not* a hotspot here. F10 cycles the achievable
zooms `[1.0, 1.5, 2.0]`; only 1.5 takes `smoothscale`, and it still holds ~145 fps.

**Steady-state uncapped, no mode dips to 20–40.** Every mode holds ≥60 fps under the 60-cap in
plain play; windowed 2.5x (`smoothscale`) is the only steady-state mode near the budget. The
20–40 fps Avi saw is **not** a steady-state number — it is a momentary dip (below).

### The momentary dip — fullscreen, 60-capped, heavy ground exchange (Avi's scenario)

Per Avi: the drop is a **momentary dip**, **fullscreen**, most easily triggered with **both cats
on the ground attacking/dodging/jumping** together. Reproduced with two `AttackerController` bots,
fullscreen, `clock.tick(60)` as the game runs. Per-frame time distribution (1200 frames/cell):

| scene weight | GC mode | mean ms | frames over 16.6 ms budget | worst frame |
|---|---|---|---|---|
| heavy exchange | GC default | 14.0 ms | **27.3%** | **47 ms → 21 fps** |
| heavy exchange | GC disabled | 13.1 ms | 9.5% | 27 ms → 37 fps |
| medium | GC default | 7–11 ms | 1.3–4.0% | 22–28 ms → 36–45 fps |
| medium | GC disabled | 9–11 ms | 0.4–6.8% | 20–27 ms → 37–50 fps |
| light (jumping only) | GC default | 6.9 ms | 0.4% | 21 ms → 48 fps |

So the dip **is** the 20–40 fps Avi reported — but as *individual over-budget frames* in a busy
exchange, not a sustained rate (mean stays well under budget). The on-screen `FPS` readout is a
rolling average (`clock.get_fps()`), so a cluster of 25–47 ms frames pulls it down to 20–40 for a
moment, then it recovers — matching "momentary dip."

**Cause split (from the table):** disabling GC roughly halves over-budget frames and caps the
worst spike at ~27 ms in the heaviest scene → **GC pauses (cause A) are a large share of the worst
spikes**. But over-budget frames don't vanish with GC off, and the worst are still 20–27 ms →
**a real over-budget-compute share (cause B) remains** in heavy frames. The two stack. `gc.freeze()`
after warmup was tested too — noisy, no consistent win over default, so it is not a reliable fix
on its own.

Repro tooling (already in the game): the live game draws `FPS: xx.xx` bottom-right every frame
(`draw_shell_chrome`, ungated); `python watch.py --vs chase --uncapped` gives two fighting cats +
a true-rate overlay.

## Recommended downstream work (file one at a time, downstream of this doc)

Ordered by live evidence against the reproduced fullscreen momentary dip:

1. **DEV (primary — double win, attacks both cause A and B):** cache the per-frame transient
   surfaces so a busy exchange stops allocating (and re-drawing) them every frame:
   - `render_battle._attack_surface(a)` — a fresh `pygame.Surface` per live attack per frame; key
     by the resolved circle-shape.
   - the shield bubble in `render_battle.render_battle` — a fresh `SRCALPHA` circle surface per
     shielding fighter per frame; key by radius.
   This cuts the heavy-scene baseline (cause B) *and* the allocation churn that drives the GC
   pauses (cause A) at the same time. Highest confidence it moves the dip.
2. **DEV (secondary — GC pauses, cause A):** reduce collection stalls during a match — e.g.
   `gc.freeze()` after startup/warm objects settle, or `gc.disable()` during the playing state with
   a bounded manual `gc.collect()` at a quiet moment (menu/KO). The measured effect is real in the
   heaviest scene (27%→9.5% over-budget) but noisy; do it *with* #1, not instead of it, and
   re-measure. **Ship behind a live FPS check, not by feel.**
3. **DEV (minor render churn):** skip the idle-breathing / crouch `pygame.transform.scale` when the
   scaled height rounds to the same px (no visible change but a new surface + GC garbage each frame).
4. **DEV (efficiency, not the dip):** cache `render_text_simple` surfaces (+ widths) and memoize
   `settings.defaults()` (rebuilt ~94×/frame via `runtime_settings.get`'s eager default arg). Clear
   wins, low risk; the live HUD test shows they don't move the dip, so lower priority.
5. **DEV (mode-dependent, separate from the dip):** the fractional-scale `smoothscale` present cost
   (windowed 1.5x/2.5x, 1.5x F10 fullscreen zoom) — prefer integer zooms or a fast-scale toggle if
   a player reports a *sustained* low rate in a scaled window.

These are candidate directions, not decisions. Every perf change must ship **measured against the
on-screen/uncapped FPS in the heavy-exchange repro**, not by game-feel.
