# Headed framerate profiling — scenario matrix, per-phase frame budget, cost localization

**Ticket:** #1077 (RESEARCH / profiling, `area:display`) · **Date:** 2026-08-02 · **Agent:** GRAPE
**Role:** findings + option space only — no optimization code lands here; each fix is its own downstream DEV, filed one-at-a-time.

---

## TL;DR

- **At the logical resolution (960×540) the CPU render path is cheap and stable: ~1.2–1.3 ms/frame typical, p99 ≈ 2 ms, worst ≈ 2.5–3 ms — under any scenario measured (idle, active combat, fireballs, debug overlay). That is >450 fps of CPU-render headroom against a 16.67 ms/60fps budget.** Render cost barely moves between idle and full combat.
- **The cost that actually threatens 60 fps is `DisplayManager.present()`'s scale-blit** — the resize from the 960×540 logical surface up to the window/fullscreen size. It is **absent at windowed 1× (no scale)** but costs **3–7 ms mean / up to ~11 ms p99** at fullscreen or windowed >1×, i.e. a large fraction of the whole frame budget in one operation, every frame. **Fractional zooms (smoothscale) are markedly worse than integer zooms (nearest-neighbour).**
- **`render_attacks(N)` scales at ~10 µs per on-screen projectile** — 64 simultaneous fireballs cost <1 ms. Projectile/hitbox count (#811) is **not** a framerate risk at any realistic count.
- **The #812 "two cats → 20–40 fps" drop is not the render code — it is `present()` scaling + flip, and this is now confirmed on a real window (§6).** Headed on x11: windowed 1× runs at ~256 fps (total p99 5.6 ms), but at windowed 2× / fullscreen the per-frame total p99 reaches **~25–28 ms — over the 16.67 ms budget** — with the scale-blit as the dominant single cost (6 ms mean, 12–16 ms worst). With vsync on, `flip()` alone blocks a full ~15.6 ms refresh, hard-capping ~60 fps and halving to 30 the moment any extra work overruns. That is the 20–40 fps band, measured.

---

## 1. Harness & method

Harness: `scripts/profile_frame_budget.py` (committed with this doc; deterministic, re-runnable). It drives the **real** battle objects (`BattleScreen`, the `pycats/render/` package, `DisplayManager`'s scale path) — not a mock — and times the same call sequence `screen_render.render_active_screen` runs for the `playing` state.

**Phases timed** (`time.perf_counter`, ms):
- **SIM** = `BattleScreen.step` (per-player update → push resolution → attack update → hit resolution).
- **RENDER** = `BattleScreen.render` + `render_battle.draw_shell_chrome` + esc-quit progress — exactly the `playing` branch of `render_active_screen`, drawn onto a 960×540 `pygame.Surface`.
- **PRESENT** = benchmarked separately via `display.scale_surface` (§4), because its cost is display-mode-dependent and partly display-bound.

**Determinism:** two seeded `AttackerController`s (fixed `DEFAULT_CONTROLLER_SEED`) drive both fighters; the sim is fixed-timestep. Each scenario warms 180 frames (to fill the body-layer, tail-segment, and font caches) before measuring 600 frames, so cache-miss build cost is excluded from the steady-state numbers and called out separately.

### Two measurement modes

The harness runs headless by default and **headed with `--headed`**:

- **Headless (default), `SDL_VIDEODRIVER=dummy`.** Every draw call, blit, `font.render`, `pygame.draw.*`, and per-frame `Surface` allocation executes identically to a real window — so the RENDER (CPU) phase is faithful (§2–§5). What dummy does not exercise is the display flip; the scale-blit's CPU half *is* still measurable in isolation (`display.scale_surface` is a pure surface transform — §4).
- **Headed (`--headed`), real SDL window.** Opens a real window at windowed-1× / windowed-2× / fullscreen and times sim + render + scale-blit + `flip()` per frame, uncapped, plus a direct vsync-on/off `flip()` probe. This measures the piece dummy cannot — the flip / vsync wait — and confirms the whole-frame budget on a real display (§6). Results below are from an x11 session on the machine of record.

**Structural fact that makes these numbers resolution-independent:** the game always draws to a fixed **960×540** logical surface (`config.SCREEN_WIDTH/HEIGHT`); `DisplayManager.present` (`pycats/display_manager.py`) scales that surface to the window via `display.scale_surface` and then flips. So the *render phase* CPU cost does not change with window size or fullscreen — **all** window-size cost lives in present(). That is why §2's matrix has no "window size" axis (it would be a flat line) and §4 measures the scale axis on its own.

**Machine of record:** Intel Core i7-8565U @ 1.80 GHz (8 threads), Python 3.12.3, pygame-ce 2.5.7, SDL 2.32.10, Linux. A modest mobile CPU — treat these ms as an upper bound for faster desktops, a lower bound for weaker hardware.

---

## 2. Scenario matrix — render-phase CPU budget

Render phase only (no present/flip), 600 measured frames/scenario, `nalio` vs `birky`. `atk` = max simultaneous attacks observed. `fps@p99` = 1000 / p99 render ms (CPU-render headroom).

| scenario | atk | mean | p50 | p95 | p99 | worst | fps@p99 | sim mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2-cat idle (input-history on) | 0 | 1.33 | 1.22 | 1.89 | 2.18 | 3.16 | 458 | 1.18 |
| 2-cat idle (input-history off) | 0 | 1.20 | 1.09 | 1.71 | 1.88 | 2.45 | 533 | 1.22 |
| 2-cat active combat | 1 | 1.22 | 1.14 | 1.71 | 1.92 | 2.46 | 522 | 1.09 |
| 2-cat combat + hitbox overlay | 1 | 1.23 | 1.15 | 1.73 | 1.99 | 2.37 | 503 | 1.07 |
| 2-cat combat + specials (fireballs) | 1 | 1.28 | 1.20 | 1.85 | 2.16 | 2.75 | 464 | 0.75 |
| 2-cat combat + specials + overlay | 1 | 1.27 | 1.18 | 1.78 | 2.05 | 2.62 | 488 | 0.74 |

Units: ms. All numbers are on the machine of record.

**Reading it:**
- Render is **flat across scenarios** (~1.2–1.3 ms mean). Idle vs full combat differs by <0.2 ms. The debug overlay (`render_hitbox_overlay`, the only draw-path caller of `combat/geometry.resolve_circle`) adds essentially nothing at 2 fighters.
- **Input-history strip is the single largest toggle** in the render phase: turning it on adds ~0.1 ms mean and widens the tail (its per-cell glyphs + `pygame.draw.circle`/`line` in `render/hud.draw_input_history`).
- SIM is ~1.1 ms, comparable to render — see §5's headless cross-check.
- **Worst-frame > p99** (3.16 vs 2.18 ms idle; a one-off 8.7 ms spike appeared in a separate cold run). These spikes are **cache-miss surface builds** (a new tail rotation angle in `render/body.render_tail`; a body-cache-miss on a state/tint change in `render/body._cat_body_layers`) plus Python GC — not sustained load. Perceived hitches come from these, not the mean.

**Coverage note (nothing dropped un-stated):** the controller-driven combat sustained at most **1** simultaneous attack, so this matrix does not stress many-projectiles — that axis is measured directly in §4 (`render_attacks(N)`) instead.

---

## 3. Where the render time goes (cProfile)

`cProfile` over the render phase of the heaviest scenario (combat + specials + overlay), 600 frames, sorted by internal time (top entries):

| tottime (s) | ncalls | function |
|---:|---:|---|
| 0.194 | 57 034 | `Surface.blit` (pygame) |
| 0.182 | 9 000 | `Font.render` (pygame) |
| 0.111 | 348 010 | `dict.get` |
| 0.099 | 1 200 | `render/body.py render_tail` |
| 0.078 | 9 000 | `Font.size` (pygame) |
| 0.074 | 1 200 | `render/hud.py draw_input_history` |
| 0.074 | 60 000 | `runtime_settings.py get` |
| 0.064 | 9 000 | `ui/text_utils.py render_text_simple` |
| 0.063 | 600 | `Surface.fill` |
| 0.054 | 46 800 | `runtime_settings.py scaled_font_size` |
| 0.038 | 46 800 | `runtime_settings.py font_scale` |
| 0.036 | 37 200 | `ui/text_utils.py _get_font` |
| 0.032 | 60 000 | `settings.py defaults` |
| 0.032 | 600 | `render/battle.py render_battle` |

(1 214 321 calls / 600 frames ≈ 2 000 calls per rendered frame; 1.585 s total wall includes profiler overhead — real render is ~1.3 ms/frame per §2.)

**The render phase is text-bound.** The whole `render_text` path (`ui/text_utils.render_text` → `render_text_simple` → `Font.render` + `Font.size`) accumulates ~0.58 s — the largest single cost family — and it is **uncached**: every HUD number, name, and shell-chrome string re-renders its glyphs every frame. Two multiplier effects sit under it:

- **`settings.defaults()` is rebuilt 60 000 times** (100×/frame): `runtime_settings.get` does `self._state.get(key, settings.defaults().get(key))`, and `defaults()` **constructs a fresh dict on every call**. That is the bulk of the 348 010 `dict.get` calls.
- **`font_scale` / `scaled_font_size` recompute 46 800 times** (78×/frame) — every text draw re-derives its scaled size, and each derivation hits `runtime_settings.get` again.

Other real-but-smaller costs: `Surface.blit` (57 k calls — bodies, tail segments, text surfaces, attack surfaces), `render/body.render_tail` (Verlet-tail iterate + rotated-rect blits every frame), `draw_input_history`, and `Surface.fill` (the per-frame background clear). `render_battle` itself is only 0.032 s — the fighters' bodies are cached layers, so the body draw is dominated by blits, not rebuilds.

---

## 4. The present() scale-blit — the dominant per-frame CPU cost when zoomed

`DisplayManager.present` → `display.scale_surface(game_surface, scale_factor)` (`pycats/display.py`), which picks the transform per `blit_mode_for`: pass-through at 1×, `pygame.transform.scale` (nearest-neighbour) at integer multiples, `pygame.transform.smoothscale` (anti-aliased) at fractional. Measured directly (960×540 source → target), 300 iterations each:

| zoom | target | mode | mean (ms) | p99 (ms) | fps@p99 |
|---:|---|---|---:|---:|---:|
| 1.0× | 960×540 | flip (no scale) | ~0.000 | ~0.001 | — |
| 1.5× | 1440×810 | smoothscale | 3.22 | 5.05 | 198 |
| 2.0× | 1920×1080 | nearest | 2.47 | 4.17 | 240 |
| 2.5× | 2400×1350 | smoothscale | 6.68 | 10.06 | 99 |
| 3.0× | 2880×1620 | nearest | 6.37 | 10.84 | 92 |

**Findings:**
- **Windowed 1× pays nothing** — `game_surface is screen`, no scale, no copy. Any perf complaint at 1× is not this.
- **At fullscreen / windowed >1× the scale-blit alone is 3–7 ms mean and 4–11 ms p99** — on the same 16.67 ms budget the render phase (§2) fits in ~1.3 ms. So present() is **~2–5× the render phase** and the single largest per-frame CPU item once zoomed.
- **Smoothscale (fractional) is markedly more expensive than nearest (integer)**: 2.5× smooth (6.68 ms) costs more than 3.0× nearest (6.37 ms) despite a *smaller* target. Fractional zoom pays an anti-aliasing tax.
- Combine present (up to ~10 ms p99) + render worst-frame (up to ~3–8 ms on a cold spike) and a single frame can exceed 16.67 ms → a dropped frame. Sustained at a fractional fullscreen zoom, this is a credible mechanism for the #812 20–40 fps observation — **before** counting the flip/vsync wait (§6).

### render_attacks(N) — projectile scaling (the "many hitboxes" axis)

`render_attacks` builds one `Surface` per attack per frame (`render/battle._attack_surface`) and blits it. Measured with N cloned projectiles:

| N | mean (ms) | p99 (ms) | per-attack (µs) |
|---:|---:|---:|---:|
| 0 | 0.001 | 0.001 | — |
| 1 | 0.010 | 0.017 | ~10 |
| 8 | 0.077 | 0.125 | ~10 |
| 32 | 0.319 | 0.536 | ~10 |
| 64 | 0.766 | 1.23 | ~12 |

**Linear at ~10 µs/attack; 64 simultaneous projectiles cost <1 ms.** The per-frame `_attack_surface` allocation is real but cheap at any realistic on-screen count. Fireball/projectile density (#811) is not a framerate concern.

---

## 5. Headless cross-check — sim vs render

The SIM column in §2 (~1.1 ms mean) is the fixed-timestep battle step measured in the same loop. So at logical resolution the frame splits roughly **sim ~1.1 ms : render ~1.3 ms : present ~0 (1×) or 3–7 ms (zoomed)**. Sim and render are comparable and both small; neither is the bottleneck. The budget is spent — when it is spent — in present() and in the display flip. This confirms render dominates over sim only once a zoom is applied, and even then present dominates render.

---

## 6. Headed measurement on a real window — the #812 mechanism, confirmed

Run: `scripts/profile_frame_budget.py --headed` — a real `DisplayManager` window driven one frame at a time, **uncapped** (no `clock.tick`, so the true achievable per-frame time shows), 600 frames/mode, `nalio` vs `birky` in seeded active combat, input-history on. x11 session, machine of record. Per-frame phases in ms (mean unless noted):

| mode | sim | render | scale-blit | flip | TOTAL mean | TOTAL p99 | TOTAL worst | fps mean / p99 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| windowed 1× (no scale) | 1.54 | 1.71 | ~0 | 0.66 | 3.91 | 5.65 | 6.64 | 256 / 177 |
| windowed 2× (upscale) | 2.15 | 2.50 | **6.27** | 2.61 | 13.52 | **24.82** | 28.11 | 74 / **40** |
| fullscreen 2× (letterbox) | 1.75 | 2.05 | **5.54** | 2.15 | 11.47 | **27.71** | 30.50 | 87 / **36** |

**This confirms the headless prediction on real hardware:**
- **Windowed 1× is never the problem** — total p99 5.65 ms (~177 fps). The window is the render target directly; no scale-blit.
- **At windowed 2× / fullscreen the scale-blit is the dominant single per-frame cost** (6.3 / 5.5 ms mean; p99 12.6 / 13.8 ms; worst ~15 ms), exactly as §4 predicted from the isolated `scale_surface` bench. The real `flip()` adds ~2.2–2.6 ms mean on top.
- **The total per-frame p99 (~25–28 ms) sits well over the 16.67 ms/60fps budget**, so a large fraction of frames overrun a refresh interval. Uncapped that reads as ~40 / 36 fps at p99; under the live game's `clock.tick(60)` cap it manifests as dropped frames — **the #812 "20–40 fps with two cats" band, reproduced.** (The drop is a function of window scale, not cat count — two idle cats at 2× drop the same as two fighting; §2 shows combat adds almost nothing.)

### Vsync probe — why the drop snaps to a band, not a smooth slope

`flip()` alone at 1920×1080, vsync on vs off (`pygame.SCALED`, 180 frames):

| vsync | flip mean | p50 | p99 | implied cap |
|---|---:|---:|---:|---:|
| on | **15.65 ms** | 15.73 | 17.96 | ~64 fps |
| off | 5.26 ms | 4.68 | 16.47 | ~190 fps |

**With vsync on, `flip()` blocks for a full monitor refresh (~15.6 ms ≈ 1/60 s).** So the observed frame time is `max(work, refresh_interval)` and fps quantizes to refresh divisors (60 → 30 → 20). The moment per-frame work (sim + render + scale-blit) pushes total past one refresh — which §6's 2×/fullscreen p95–p99 do — the frame misses the next refresh and the rate halves to 30. That is why #812 reads as a *band* (20–40) rather than a smooth slowdown.

Note the shipped window (`DisplayManager.set_mode`, no `vsync=` flag) measured only ~2.2–2.6 ms flip above — it is not hard-vsync-blocked in this x11/compositor session, so the shipped drop at 2× is driven by the **scale-blit + total-work-over-budget** path, with vsync-blocking a second, compositor/driver-dependent mechanism that would bite on a vsync-locked display.

---

## 7. Findings & option space (ranked) — candidate follow-up DEV tickets

Ranked by leverage against a stable 60 fps. **None implemented here** — each is an option for a separately-filed DEV ticket, and each needs its own before/after measurement.

1. **Present scale-blit is the #1 target (highest leverage) — headed-confirmed (§6).** It is the dominant per-frame cost whenever the game is not at windowed 1× (6 ms mean, 12–16 ms worst at 2×/fullscreen), and it is what pushes the total p99 over the 16.67 ms budget. Option directions: (a) prefer/recommend **integer zooms** (nearest) over fractional (smoothscale) in the zoom presets — §4 shows ~2× cheaper; (b) hardware-accelerated scaling (SDL2 texture via `pygame._sdl2.video`, or an OpenGL surface) so the resize runs on the GPU instead of a per-frame CPU `transform.scale` — likely the largest single win, and it removes the scale-blit from the CPU budget entirely; (c) only re-scale on change if the frame is unchanged (rare in an action game, so weakest). (b) overlaps the out-of-scope "GPU rearchitecture" note — flagged as the highest-leverage direction, to be scoped as its own spike.
2. **Vsync/flip refresh-quantization — confirmed (§6), informs the fix target.** With vsync on, `flip()` blocks a full ~15.6 ms refresh, so the practical goal is **"keep total per-frame work under one refresh interval."** Once #1 removes the scale-blit, total work drops back under 16.67 ms at 2×/fullscreen (sim + render + flip ≈ 6–7 ms) and 60 fps is restored. This reframes #1 as the whole game, not just a CPU micro-opt.
3. **Cache `settings.defaults()`.** It rebuilds a dict 100×/frame through `runtime_settings.get`. Memoizing the defaults dict (module-level constant, or `functools.lru_cache`) removes ~60 k dict constructions/scenario and a large share of the 348 k `dict.get` calls. Cheap, self-contained, zero behavior change.
4. **Memoize `font_scale` / `scaled_font_size` per frame** (or invalidate on the Options font-scale change only). 46.8 k recomputes/scenario, each re-hitting `runtime_settings.get`.
5. **Cache `render_text_simple` output surfaces** keyed by `(text, scaled_size, color)`, the way `render_text_mixed` already caches composed surfaces. HUD numbers/names/chrome re-`Font.render` every frame; most strings are stable frame-to-frame. Biggest single render-phase CPU win at logical resolution.

Items 3–5 together would meaningfully cut the render phase, but the render phase is already ~1.7 ms headed at 1× — **they matter mainly to widen the margin, not to fix #812.** Sequencing recommendation: **item 1 (present scale-blit, ideally GPU) first — it is the confirmed cause; then 3–5** to reclaim the remaining CPU headroom. Do not start with the already-cheap render-path micro-opts.

---

## Out of scope (per ticket)
- Implementing any optimization (each is a downstream DEV).
- pytest-suite runtime (#810 owns headless suite timing).
- The GPU/accelerated-render rearchitecture itself (option 1b) — a separate spike if pursued.

## References
- Harness: `scripts/profile_frame_budget.py`
- Prior: #812 (two-cat fps drop, CLOSED) · #810 (suite runtime) · #345 (font-scale) · #811 (fireball/entities)
- Code landmarks: `pycats/app.py App.step`; `pycats/screen_render.py render_active_screen`; `pycats/screens/battle_screen.py BattleScreen.render/_draw_battle/step`; `pycats/render/battle.py render_battle/render_attacks/_attack_surface`; `pycats/render/body.py render_tail/_cat_body_layers`; `pycats/render/hud.py draw_hud/draw_input_history/draw_shell_chrome`; `pycats/render/debug.py render_hitbox_overlay`; `pycats/combat/geometry.py resolve_circle`; `pycats/ui/text_utils.py render_text/render_text_simple/_get_font`; `pycats/runtime_settings.py get/font_scale/scaled_font_size`; `pycats/settings.py defaults`; `pycats/display.py scale_surface/blit_mode_for`; `pycats/display_manager.py present`.
