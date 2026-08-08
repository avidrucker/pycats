# Loop profile — measured hot functions in `App.step()`

**Ticket:** #1247 (DEV, `area:cross-cutting`) · **Date:** 2026-08-05 · **Agent:** FIG

Follow-up to #1236 (static hypotheses) and #1241 (the freeze *detector*). This is the
*measurement*: `profile_loop.py` runs a bounded, headless `App.step()` loop under
`cProfile` and ranks the functions that actually burn the frame budget — the render/App
path `bench.py` never touches. It confirms or refutes each #1236 hypothesis **with a
number**, and surfaces one hotspot #1236 did not name.

## Method

- `profile_loop.py --state session --frames 600` — a representative run visiting
  `main_menu → char_select → playing → pause`. `cProfile` sums each function across the
  whole run, so one table answers every hypothesis.
- Headless (`SDL_VIDEODRIVER=dummy`); the 60-FPS `clock.tick` sleep is swapped for a
  no-sleep clock, so times measure **compute**, not the frame cap.
- Prefs come from the persisted `settings.json` — this run was **`fullscreen=True`,
  `windowed_scale=1.0`** (see the C1 caveat below; window scale changes the top result).
- Reproduce: `cd <worktree> && make profile` (or `make profile ARGS="--state playing"`).

Numbers below are one 600-frame session run (≈5.4s total compute); absolute times vary
run-to-run, the **ranking and call-counts** are the signal.

## #1236 hypotheses — all six confirmed

| # | Hypothesis | Measured (600-frame session) | Verdict |
|---|---|---|---|
| A1 | uncached `settings.load()` per frame | **1.0 call/frame**, 168ms cum (disk `open`+`json.load` each) | confirmed |
| B1 | font `SysFont`/`match_font` burst | `_get_font` 31186 cache-hit calls; **`SysFont` built only 6×** | confirmed, but **one-shot** in steady play |
| B2 | per-frame surface alloc in `render_battle` (breath/shield/attack) | `render_battle` 30ms self-time; breath rescale via `transform.scale` | confirmed (small in steady play) |
| B3 | `runtime_settings.get()`'s unconditional `settings.defaults()` copy | **160 calls/frame**; `defaults()` mints a fresh dict **31.6k×**; ~125ms self-time | confirmed — steady CPU waste |
| B4 | uncached `render_text_simple()` re-rasterizes HUD text | 12.8 calls/frame; 83ms self-time + drives `font.render` (242ms) | confirmed |
| B5 | `_compose_mixed()` wholesale cache clear at cap | 11.6 calls/frame | confirmed |

Notes that refine #1236's ranking:

- **B1 is not a per-frame burst in steady play.** `SysFont` builds **6 times total**
  (cache-warm); the 31k `_get_font` calls are cache *hits*. The burst #1236 predicted fires
  on a **`font_scale` change** or a screen minting many new sizes, and its fontconfig
  hard-hang only fully shows on a **real display** (`--headed`) — not in this headless run.
- **B3 is the biggest scale-independent CPU waste.** 160 settings reads per frame, each
  allocating a throwaway `defaults()` dict even on a cache hit. Pure overhead; cheap to fix.
- **A1's cost is disk I/O** (low self-time, 168ms cumulative) — it matters most on a real
  disk / during the ESC-hold the detector (#1241) flagged.

## C1 — a hotspot #1236 did NOT name: per-frame full-surface `smoothscale` in `present()`

The single largest self-time entry in this run was **not** one of the six hypotheses:

```
602  1.776s  {built-in method pygame.transform.smoothscale}
  └ display_manager.present() → display.scale_surface() → smoothscale   (once per frame)
```

`DisplayManager.present()` upscales the internal render surface to the window every frame.
`scale_surface` picks the transform by scale: **1.0 → "flip" (no copy)**, integer multiples
→ nearest-neighbour, **fractional → `smoothscale`**. This run was fullscreen, whose fit
scale is fractional — so every frame paid a full-surface anti-aliased scale.

**It is conditional on the window-scale setting** (same 300-frame session, three prefs):

| window scale | `smoothscale` calls | `smoothscale` self-time | total self-time |
|---|---|---|---|
| fullscreen (fractional fit) | 302 | 0.68s | 2.12s |
| windowed 1.0 | **0** | 0.00s | 1.52s |
| windowed 2.0 (integer) | **0** | 0.00s | 2.35s |

So a **fullscreen** player pays a large per-frame smoothscale a windowed-1x player does not
— a legitimate, previously-unnamed cost (Avi plays fullscreen). Fix directions: downgrade
fullscreen fit to nearest-neighbour, or cache/avoid the re-scale when the source is
unchanged.

## Priority for downstream fixes (measured)

1. **C1** — `present()` smoothscale (fullscreen only; the largest single cost when it applies).
2. **B3** — `runtime_settings.get()` / `defaults()` copy (largest scale-independent waste, trivial fix).
3. **B4 / B1** — text rendering: cache `render_text_simple`; pre-warm fonts / kill the `SysFont` miss path.
4. **A1** — read `esc_hold_to_navigate` from `runtime_settings` instead of `settings.load()` each frame.
5. **B2** — cache the breath/crouch/shield rescaled surfaces.
6. **B5** — LRU/ring eviction for `_compose_mixed` instead of a wholesale clear.

These are render-only / settings-read paths — **downstream of the sim**, so none affect
determinism or the goldens. Each is its own DEV fix; file them one at a time (#1247
acceptance). The go/no-go and ordering are the maintainer's call.
