# Game lag — intermittent 1–2s full-game freezes: profiling targets & churn hotspots

**Ticket:** #1236 (RESEARCH, `area:cross-cutting`) · **Date:** 2026-08-05 · **Agent:** FIG

## Symptom (reported)

The whole game intermittently **freezes for 1–2 seconds**, with **no visual change** during
the stall — the loop hangs, then resumes. Observed **in battle** and **in the menu on exit**
(leaving a screen). No crash, no error line.

## Interpretation

A freeze *with no visual change* is a **single blocking burst on the game thread** — one
frame (or a short run of frames) doing seconds of work — not steady per-frame slowness (that
would show as a low but stable FPS, not a hang). The three blocking-burst mechanisms that fit
this profile, in order of how well they match "1–2s, no visual change":

1. **A fontconfig / SysFont build burst** (can hard-hang hundreds of ms → seconds on Linux).
2. **A Python GC pause** triggered by sustained short-lived allocation (surfaces/dicts).
3. **Repeated blocking disk IO** on the game thread (uncached `settings.load()` / fighter JSON).

This document lists concrete, code-grounded candidates for each, ranked, with the exact
call site. **This is static analysis** — it names *where to point a profiler*, not a confirmed
root cause. Confirmation is a live per-frame timing profile (see "Profiling plan"), whose
result decides which follow-up DEV tickets are worth filing. Evidence sufficiency and the
go/no-go on each fix are the maintainer's call.

---

## Part A — Menu-exit stall (strongest single match)

### A1. `settings.load()` (uncached disk read) runs **every frame** during the exit hold — TOP menu suspect
- **Site:** `ScreenStateManager._tick_esc_hold` in `pycats/shell/screen_manager.py` — called at the top of `.update()` every frame; body does `from ..storage.settings import load` then `if not load().get("esc_hold_to_navigate", True):`.
- **Confirmed:** `settings.load()` in `pycats/storage/settings.py` does `open(config_path()) + json.load(f) + _validated(raw)` on **every** call — **no cache**.
- **Why it matches:** "Exiting the menu" is a **timed ESC/B hold** (~`ESC_HOLD_FRAMES` ≈ 120 frames ≈ 2s). For the whole duration of that hold the game re-opens and re-parses `~/.config/pycats/settings.json` once per frame — ~120 back-to-back disk reads precisely while the player holds to leave. Matches the reported location *and* duration. A live in-memory mirror (`runtime_settings`) already holds this value; this path bypasses it and hits disk.
- **Cheap fix direction:** read `esc_hold_to_navigate` from `runtime_settings` (already seeded at boot) instead of `settings.load()`, or memoize `load()`.

### A2. Options screen re-reads the same value from disk **every render frame**
- **Site:** `_row_label` (the `esc_quit` arm) in `pycats/screens/options_menu.py` — `"Hold-ESC Back: " + ("ON" if settings.load()... )`.
- **Why:** Called per visible row per frame while Options is up (and during the exit-from-Options hop named in the ticket), stacking another full `settings.load()` disk read on top of A1. Every *other* row reads the cached `runtime_settings`; only this one goes to disk.

> The `_on_enter_*` state handlers themselves are **cheap** (scalar/bool resets) and were ruled out — the menu stall is the per-frame disk reads above, not scene rebuild on enter.

---

## Part B — Battle freeze candidates

### B1. Font construction burst (fontconfig hang) — TOP battle suspect for a one-shot freeze
- **Site:** `TextRenderer._get_font` / `TextRenderer.sys_font` in `pycats/ui/text_utils.py`. Fonts are cached by `(font_name, size)`, but a **cache miss** calls `pygame.font.SysFont(...)` → on failure `pygame.font.match_font(...)` + `pygame.font.Font(path, ...)`. The code's own comment (from #375): *"calling `SysFont()` every frame … hard-hangs on a real display."*
- **Why it matches:** Every distinct **size** is a new cache key, and size flows through `runtime_settings.scaled_font_size(size)` (global `font_scale`). **Changing `font_scale` in Options, or a screen that introduces many new sizes, forces a burst of SysFont/match_font builds** — a one-shot multi-hundred-ms-to-second stall with no visual change. Best single match for the symptom on a real display.
- **Fix direction:** pre-warm the sizes actually used; eliminate the `SysFont`/`match_font` miss path at runtime (build from a known font path).

### B2. Sustained per-frame **surface allocation** → GC pauses
Render-only, downstream of the sim, so none of these affect determinism/goldens — but together they are a steady stream of short-lived `pygame.Surface` objects, the classic trigger for an intermittent GC hitch:
- **`_attack_surface()`** (via `render_attacks`) in `pycats/render/battle.py` — `pygame.Surface(a.rect.size, SRCALPHA)` **rebuilt per frame per live attack** (self-documented "rebuilt per frame", uncached). Worst during attack-heavy exchanges.
- **Breath/crouch scaling** in `render_battle()` — `pygame.transform.scale(...)` allocates **two fresh surfaces per player every frame** while crouching or **idle-breathing** (which defaults ON and is the common resting state), defeating the downstream `_body_layers_cache`.
- **Shield bubble** in `render_battle()` — `pygame.Surface((r*2, r*2), SRCALPHA)` fresh every frame a fighter is shielding.

### B3. High-frequency small allocations / recompute (GC pressure + CPU)
- **`runtime_settings.get()`** in `pycats/storage/runtime_settings.py` — `return _state.get(key, settings.defaults().get(key))`: Python evaluates the default arg **unconditionally**, so `settings.defaults()` (a fresh ~15-key `dict(_DEFAULTS)` copy) allocates on **every** settings read, even on a cache hit. These reads happen dozens of times per frame (every `scaled_font_size()`, plus each HUD toggle). This is the #1092 `settings.defaults()` concern.
- **`render_text_simple()`** in `pycats/ui/text_utils.py` — the *simple* text path has **no surface cache** (only the mixed path caches). Every frame re-rasterizes HUD/status/lives/damage/FPS via `font.render(...)` (13 `render_text(` call sites on the battle path, several looping per row per player). This is the core of #1092.
- **`active_tint()`** in `pycats/render/tint.py` — `sorted(STATUS_SOURCES, key=…)` rebuilds a sorted list + lambda on every call (called repeatedly per player per frame, even on body-cache hits to compute the key). Sort a constant once at module load.

### B4. Mixed-text cache **cliff**
- **Site:** `_compose_mixed` in `pycats/ui/text_utils.py` — at `_MIXED_CACHE_CAP` it does a wholesale `self._mixed_surface_cache.clear()`. Dynamic HUD strings (damage %, timer) mint a new key every value, fill to cap, then **all** live compositions are dropped at once → every on-screen mixed string recomposes next frame. A **periodic** micro-hitch (not 1–2s, but recurring). LRU/ring eviction removes the cliff.

---

## Part C — Transition into battle (secondary)

### C1. `load_fighter_data` is completely uncached
- **Site:** `load_fighter_data` in `pycats/combat/data.py` — `_fighter_from_json(json.loads(path.read_text()))`, **no `lru_cache`/memo**; a stat+read+parse+**full nested frozen-dataclass hydrate** (every move/hitbox/hurtbox/status) on every call.
- **Why:** Players are built **once per match** (`BattleScreen.create_from_selection`, not per frame), so this is not a per-frame cost — but each **battle start** does disk IO + a big allocation burst on the char-select→playing transition, a plausible entry-hitch that scales with move/hitbox volume. The JSON is static at runtime → safe to memoize by key. (Contrast `loadout/cards.py`, which *is* `@cache`d.)

---

## Ruled out (checked, not the cause)

- **Per-frame fighter-JSON IO** — `load_fighter_data` is only in `Player.__init__`, not in `update`/`step`. No per-frame disk reads on the battle path other than the settings reads in Part A.
- **`provenance.py` runtime recompile** — data-only registry; the `derivation` re-eval runs **only** in `tests/test_tuning_provenance.py`, never at runtime.
- **Body/tail render caches** (`_body_cache`, `_body_layers_cache`, `_tail_*` in `pycats/render/body.py`) — keys are effectively finite (discrete tints, bool facing, int degrees), so they saturate to a bounded size and don't churn per frame. Unbounded (no eviction) but low key cardinality.
- **`pygame.image.load`** — no occurrences anywhere; all art is drawn procedurally.
- **Palettes / cards / og-skins** — loaded once at import, then read from cache.
- **O(n²) scans** — `resolve_player_push` (players²=4) and `_resolve_clanks` (live-attacks²) are over tiny n; negligible.

---

## Profiling plan (the confirming step)

Static analysis points the profiler; it does not replace it. Recommended sequence:

1. **Per-frame timing probe (cheapest first).** Add a wall-clock delta around the body of
   `App.step()` in `pycats/shell/app.py` and log any frame over a threshold with the active
   FSM state and a coarse phase breakdown (poll / update / render / present). A drop-in probe:

   ```python
   # in App.step(), wrapping the existing body — REMOVE before shipping (diagnostic only)
   import time
   _t0 = time.perf_counter()
   # ... existing step body ...
   _dt = (time.perf_counter() - _t0) * 1000.0
   if _dt > 100.0:  # any frame doing >100ms of work
       print(f"[slowframe] {_dt:6.1f}ms state={self.screen_manager.get_state()}")
   ```

   This alone will tell you **which state** stalls and **how long** — separating Part A
   (menu) from Part B (battle) empirically.

2. **Sampling profile around a reproduced stall** — `cProfile` (stdlib, no new dep) around a
   session, or `pyinstrument` for a wall-clock flame view. **Adding `pyinstrument` needs
   maintainer approval per RULES.md (Dependencies) — propose, don't install.** `cProfile` is
   already available.

3. **GC visibility** — set `gc.set_debug(gc.DEBUG_STATS)` (or log `gc.callbacks` durations)
   for one session to confirm/deny whether the 1–2s stalls coincide with full collections
   (validates the Part B2/B3 GC-pressure hypothesis).

4. **Repro metadata to capture:** does the stall correlate with a specific action (exiting a
   specific menu, changing `font_scale`, a specific move/hitbox event, first-time vs steady
   state)? Cold-start-only or recurring? Reporter is on **Linux (pygame)** — the fontconfig
   path (B1) is Linux-relevant.

---

## Prioritized follow-up candidates (file downstream, one at a time)

Each is a self-contained DEV ticket; **file after the profile confirms which stall dominates**
— don't fan out speculatively.

| Rank | Fix | Site | Kind | Notes |
|------|-----|------|------|-------|
| 1 | Read `esc_hold_to_navigate` from `runtime_settings`, not `settings.load()` | `screen_manager._tick_esc_hold`, `options_menu._row_label` | correctness/perf | Removes ~120 per-hold disk reads; strongest menu-exit match (A1/A2) |
| 2 | Eliminate the runtime `SysFont`/`match_font` miss path; pre-warm used sizes | `text_utils.TextRenderer._get_font` | perf | Top battle-freeze suspect on Linux (B1) |
| 3 | Memoize `load_fighter_data` by key | `combat/data.py` | perf | Battle-entry hitch (C1); JSON is static at runtime |
| 4 | Cache `render_text_simple` output + fix `settings.defaults()` unconditional eval | `text_utils`, `runtime_settings.get` | perf | The existing #1092 work — GC pressure baseline (B3) |
| 5 | Cache the per-frame attack/shield/breath surfaces | `render/battle.py` | perf | Surface-alloc GC pressure (B2) |
| 6 | LRU eviction for `_mixed_surface_cache` (replace wholesale `.clear()`) | `text_utils._compose_mixed` | perf | Removes the periodic recompose cliff (B4) |
| 7 | Sort `STATUS_SOURCES` once at module load | `render/tint.active_tint` | perf | Micro; constant recompute (B3) |

**Overlap with existing work:** #1092 (render-CPU headroom: `settings.defaults()`,
`font_scale`, `render_text_simple`) already covers ranks 4 and part of 2 — check it before
filing. #810 is the **test-suite** runtime (out of scope here). This doc is the closing
artifact for #1236; the DEV tickets are its downstream, gated on the profiling step.
