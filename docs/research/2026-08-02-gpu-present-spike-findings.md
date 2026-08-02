# GPU-accelerated `present()` — scoping spike findings (#1091)

**Role:** RESEARCH / spike. **Date:** 2026-08-02. **Agent:** GRAPE.
**Parent decision:** #1090 (option A, "file the scoping spike"). **Basis:** #1077 profiling
(`docs/research/2026-08-02-headed-framerate-profiling-findings.md`).

Findings + option space only. **No production render-path change here** — the implementation
is a downstream child filed one-at-a-time after this spike lands (see §7).

---

## 0. TL;DR

- **Recommended backend: `pygame._sdl2.video` (SDL2 texture + `Renderer`).** It removes the
  per-frame CPU `transform.scale` scale-blit that #1077 localized as the #812 two-cat drop,
  keeps the fixed 960×540 logical-surface draw model untouched, needs **no new dependency**
  (ships inside pygame-ce 2.5.7), and — verified below — **constructs, presents, and reads
  back under `SDL_VIDEODRIVER=dummy`**, so headless CI keeps working.
- `Renderer.logical_size = (960, 540)` gives GPU-side letterboxing for free, replacing the
  manual `offset_x/offset_y` + `fill((0,0,0))` fullscreen math.
- **`pygame.SCALED` + `vsync=1`** is a lower-code alternative but collides with the existing
  fractional zoom presets (1.5×/2.5×) and the F10 fullscreen zoom-cycle UX — noted, not
  recommended, as it would force a zoom-model redesign (a player-visible change, which #1090
  deferred as option B).
- **`pygame.OPENGL`** is rejected: it disables pygame's 2D surface blitting entirely, forcing
  a full render-path rewrite, and needs a gated new dependency (PyOpenGL) — all cost, no
  benefit over the SDL2 Renderer.
- **The goldens are safe; one guard changes.** `tests/golden/` and `test_battle_screen_render`
  draw to the 960×540 `game_surface` and never call `present()` — untouched. The
  `test_display_manager.py` **render-hash guard** *does* interact: it byte-compares `present()`
  output against a CPU-`scale_surface` reference, and GPU scaling is not bit-identical to CPU
  `smoothscale`, so that guard must be re-pointed at the retained CPU fallback path (see §4).
- **Fallback is mandatory and cheap:** select the backend at `DisplayManager` init; when the
  SDL2 renderer can't be created (or under dummy, or on a software-SDL box), retain today's
  CPU `scale_surface` present path verbatim. Both paths coexist behind `present()`.

---

## 1. What #1077 established (the problem being fixed)

The render/sim CPU at the fixed 960×540 logical surface is cheap (~1.3 ms/frame). The #812
two-cat 20–40 fps drop is **`DisplayManager.present()`'s CPU `transform.scale` scale-blit**
(6 ms mean, 12–16 ms worst at 2×/fullscreen) plus the vsync `flip()` blocking a full ~15.6 ms
refresh. The drop **scales with window size, not cat count**; windowed 1× is never the problem
(at 1× `present()` does no scaling — `game_surface is screen`).

The cost lives entirely in `display.scale_surface()` →
`pygame.transform.scale` / `pygame.transform.smoothscale` (`pycats/shell/display.py`), called
from `DisplayManager.present()` (`pycats/shell/display_manager.py`). Moving that scale onto the
GPU is the fix.

## 2. Current present path (as-built, grounded)

`DisplayManager.present(display_target=None)` (`pycats/shell/display_manager.py`), per mode:

| Mode | Draw target | `present()` work |
|---|---|---|
| Windowed 1× | `game_surface is screen` | nothing (frame is presented as-is), then `flip()` |
| Windowed >1× | offscreen 960×540 `game_surface` | `target.blit(scale_surface(game_surface, factor), (0,0))`, then `flip()` |
| Fullscreen | offscreen 960×540 `game_surface` | `fill(black)` + `blit(scale_surface(..., factor), (offset_x, offset_y))` (letterbox), then `flip()` |

`scale_surface` (`pycats/shell/display.py`) picks `flip`/`crisp`/`smooth` via `blit_mode_for`:
identity at 1×, `transform.scale` (nearest) at whole multiples, `transform.smoothscale` at
fractional zooms. **The `scale_surface`/`blit_mode_for`/`window_size_for` math and the
`offset_x/offset_y` letterbox are exactly what a GPU present replaces or bypasses.**

The `display_target` parameter is a test seam: passing a scratch `pygame.Surface` captures the
present output without a live window, and only the `display_target is None` path calls
`pygame.display.flip()`.

## 3. Backend comparison

All three backends are present in the shipped runtime — verified under `SDL_VIDEODRIVER=dummy`
on the machine of record (pygame-ce 2.5.7, SDL 2.32.10, Python 3.12.3):

```
_sdl2.video: AVAILABLE  (Window, Renderer, Texture, Image)
SCALED flag: 512        set_mode(..., vsync=…) accepted
OPENGL flag: 2
```

| Criterion | A1 — `_sdl2.video` Renderer | A2 — `pygame.SCALED`+vsync | A3 — `pygame.OPENGL` |
|---|---|---|---|
| Removes CPU scale-blit | **Yes** — GPU scales the texture on present | **Yes** — SDL GPU-scales on `flip()` | Yes (as a textured quad) |
| Keeps 960×540 surface draw | **Yes** — draw to `game_surface` unchanged, upload as texture | **Yes** — draw to the logical-size window surface | **No** — 2D `Surface` blitting is disabled on an OPENGL surface |
| New dependency | **None** (in pygame-ce) | **None** (in pygame-ce) | **PyOpenGL** (gated — needs human approval) |
| Fractional-zoom / F10 UX fit | **Full** — arbitrary dst rect + `logical_size` letterbox | **Poor** — SDL auto-picks the scale to fit; the 1.5×/2.5× presets + F10 zoom-cycle don't map | N/A (own scaling anyway) |
| Headless (dummy) behaviour | **Constructs + presents + reads back** (verified §4) | Works (software renderer) | Needs a GL context — brittle headless |
| Effort | Medium — rework `present()` + a backend-select seam | Small — `present()` collapses to `flip()` | Large — full render-path rewrite |

**Recommendation: A1.** It is the only option that removes the scale-blit *and* preserves both
the surface-draw model and the current zoom UX, with no new dependency.

### Why not A2 (`SCALED`)
Lowest code (present() becomes a bare `flip()`; all the `scale_surface`/offset machinery
deletes), but `SCALED` fixes the logical size at `set_mode` time and lets SDL choose the
presentation scale to fit the window/monitor. The existing **fractional windowed presets
(1.5×, 2.5×)** and the **F10 in-fullscreen zoom-cycle** (`achievable_zoom_scales`, #85/#89/#92)
assume the app picks the exact scale. Adopting `SCALED` would force a zoom-model redesign —
a **player-visible** change, which is precisely option B that #1090 **deferred**. Revisit only
if the zoom UX is deliberately reopened.

### Why not A3 (`OPENGL`)
An `OPENGL` display surface cannot be blitted to with pygame's 2D API, so the entire
`render_battle`/screen draw path would have to move to GL, plus a gated PyOpenGL dependency.
The SDL2 Renderer already delivers GPU scaling with none of that. Rejected.

## 4. Goldens / render-oracle coexistence

**Unaffected:** the headless render tests draw to the 960×540 `game_surface` and never call
`present()`:
- `test_battle_screen_render` (inline byte-equality) and everything under `tests/golden/`
  operate on a `pygame.Surface` at logical resolution. The GPU path changes only *presentation*
  (surface → screen), not the *draw*, so these stay valid with **zero regen**.

**One guard interacts — `tests/test_display_manager.py` render-hash guard.** Three tests
(`test_present_windowed_above_1x_upscales_offscreen_to_the_window`,
`test_present_fullscreen_letterboxes_the_scaled_view_centred_on_black`,
`test_present_windowed_1x_leaves_the_frame_untouched`) pass a scratch `display_target` surface
and assert `present()` output is **byte-identical** to a CPU-`scale_surface` reference. GPU
texture scaling is **not** bit-for-bit equal to `transform.smoothscale`, so a GPU present cannot
satisfy a byte-equality assertion. Resolution for the impl ticket:
- The render-hash guard tests the **CPU fallback** contract — keep it pointed at the retained
  CPU path (the `display_target`-surface branch stays CPU, which is also what the fallback uses).
- If the GPU path itself needs oracle coverage, use `Renderer.to_surface()` readback (verified
  working, §below) with a **structural / tolerance** check, not byte-equality. Flag: even the
  *software* renderer under dummy may not byte-match CPU `smoothscale`, so byte-equality is off
  the table for any renderer-sourced pixels.

No other test branches on the display backend today; the backend-select seam (§6) is the only
new branch point.

## 5. `SDL_VIDEODRIVER=dummy` compatibility (verified)

Constructing and driving an SDL2 `Renderer` **works headless under the dummy driver** on the
machine of record — verified this spike:

```
Renderer under dummy: OK
logical_size set: (960, 540)
Texture.from_surface: OK (960, 540)
draw+present: OK
to_surface readback: OK (960, 540)
```

So the GPU present *code path* executes in headless CI (SDL falls back to a software renderer
under dummy — it exercises the branch, not real GPU acceleration). Two consequences:
1. Headless CI can run the GPU branch without a real display → **CI stays green** whether the
   backend-select picks GPU-under-dummy or the CPU fallback.
2. Because the dummy renderer is software, the *speedup* is **not** measurable headless — the
   before/after fps delta must be taken headed (see §7 — deferred to the impl ticket, needs a
   real window).

Recommended default for tests: force the **CPU fallback** under dummy (the render-hash guard
already pins that contract), keeping headless behaviour byte-stable and reserving the GPU branch
for headed runs.

## 6. Fallback + backend selection

`DisplayManager.__init__` gains a backend-select step:
1. Attempt to create the SDL2 `Renderer` for the window.
2. On success → **GPU present**: upload `game_surface` to a persistent `Texture` (`.update()`
   per frame), `renderer.clear()`, draw with `logical_size=(960,540)` for automatic letterbox
   (fullscreen) or an explicit dst rect (windowed >1×), `renderer.present()`.
3. On failure — no GPU, software SDL, dummy driver, or an env opt-out — **retain today's CPU
   `scale_surface` present path verbatim** (the code in §2 is the fallback, unchanged).

Both paths live behind the single `present()` entry point; callers (`App.step` →
`self.dm.present()`) are untouched. The 1× windowed path (`game_surface is screen`) already
does no scaling and can stay CPU regardless — GPU only earns its keep at >1×/fullscreen, the
exact sizes #1077 flagged.

Open sub-questions for the impl ticket (not blocking this spike):
- Texture re-upload cost: `Texture.update(game_surface)` every frame vs. `from_surface` — is the
  per-frame CPU→GPU upload of a 960×540 surface cheap enough to net-win? (Almost certainly yes
  vs. a 6 ms CPU smoothscale, but measure headed.)
- vsync: whether to keep `flip()`-side vsync or the renderer's present-vsync, and its interaction
  with the #1077 "flip() blocks a full refresh" half of the drop.
- Backend opt-out env/setting for debugging + the dummy-driver default.

## 7. Hand-off to the impl ticket

A single downstream DEV (or ARC-then-DEV) child, filed one-at-a-time after this spike lands:

- **Scope:** implement the A1 GPU present behind a backend-select seam in `DisplayManager`, CPU
  `scale_surface` retained as the fallback; 1× windowed stays as-is.
- **Tests:** re-point the three render-hash guards at the CPU fallback contract; add GPU-path
  coverage via `Renderer.to_surface()` with a tolerance/structural check (not byte-equality);
  full suite green with **zero `tests/golden/` regen**.
- **Before number (headed):** #1077's headed measurement is the baseline any impl must beat —
  present() **6 ms mean, 12–16 ms worst at 2×/fullscreen**, per-frame p99 ~25–28 ms over the
  16.67 ms budget. **A fresh `--headed` re-run is currently blocked** — the #1077 harness has
  bit-rotted (see the note below); repairing it is a prerequisite for the impl ticket's
  before/after capture.
- **Player-visible:** presentation pixels change (GPU scale vs. CPU smoothscale). The impl child
  needs a human eyeball-OK before close even on a green suite.

### Note — the `--headed` re-run is blocked: the #1077 harness bit-rotted
The ticket body asks to "re-run `scripts/profile_frame_budget.py --headed` to establish the
before number." **That harness no longer imports** on current main. It was last touched by the
#1077 merge (3036a02); a subsequent package reorg into `pycats/shell/` and `pycats/storage/`
subpackages relocated the modules it imports at top level, and its `from pycats import
runtime_settings, screen_render` (plus `pycats.app`, `pycats.display`, `pycats.display_manager`)
now raise `ModuleNotFoundError`:

| Harness import (stale) | Current location |
|---|---|
| `from pycats import runtime_settings` | `pycats.storage.runtime_settings` |
| `from pycats import screen_render` | removed (no `screen_render` module) |
| `from pycats.app import P1_KEYS, P2_KEYS` | `pycats.shell.app` |
| `from pycats import display` | `pycats.shell.display` |
| `from pycats.display_manager import DisplayManager` | `pycats.shell.display_manager` |

Because it is a script (not exercised by the suite), the reorg never reddened a test and the
rot went unnoticed. **Consequence for the impl ticket:** the before/after headed capture depends
on a working harness, so **repairing `scripts/profile_frame_budget.py` (repoint the imports +
add a smoke-import guard so it can't rot unnoticed again) is a prerequisite** — either folded
into the impl child or filed as a small standalone DEV ticket first. Until then the #1077 headed
numbers above stand as the baseline. (The re-run was authorized this spike but could not be
captured for this reason.)

## 8. Out of scope

- Implementing GPU present (the downstream child above).
- Option B (integer/fractional zoom presets — deferred in #1090) and options C/D/E (render-CPU
  cleanup — batched child #1092).

## 9. Refs

#1090 (decision parent) · #1077 (`docs/research/2026-08-02-headed-framerate-profiling-findings.md`
+ harness `scripts/profile_frame_budget.py`) · #812 (two-cat drop, CLOSED) ·
`pycats/shell/display_manager.py` (`DisplayManager.present`) · `pycats/shell/display.py`
(`scale_surface`, `blit_mode_for`) · `tests/test_display_manager.py` (render-hash guard).
