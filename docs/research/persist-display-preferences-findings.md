# Persisting display preferences — research findings (#86)

> How to make the player's display choices (window scale #82, fullscreen #85,
> zoom #92) survive a restart. This is pycats' **first persisted user-state**, so
> the choice sets the precedent for all future prefs. Read-only research; the
> downstream **ARCHITECT decision** ticket rules on the options below, then files
> the **DEV** ticket. Companion to #82/#85/#89/#92.
> Confidence: high — grounded in the code at `main` and standard platform/stdlib
> conventions; not run through the deep-research harness. Date: 2026-06-25.

## TL;DR / recommendations

| # | Question | Recommendation |
|---|----------|----------------|
| 1 | Where | User config dir: `$XDG_CONFIG_HOME/pycats/settings.json` (fallback `~/.config/pycats/`). Not repo-local. |
| 2 | Dependency | **Stdlib** tiny path helper (minimal-deps ethos, Linux-primary). `platformdirs` only if Windows/macOS becomes a real target. |
| 3 | Format | **JSON** (stdlib read+write; `tomllib` is read-only in 3.12, INI is awkward for typed/nested). |
| 4 | Lifecycle | Load once at startup **before the first `set_mode`**; **save on each change** (F10/F11) — tiny, rare writes, crash-safe. |
| 5 | Schema | Flat dict with an integer `version`; missing keys → defaults, unknown keys ignored; migrate on bump. |
| 6 | Robustness | Missing/corrupt/ill-typed file → **fall back to defaults, never crash**. Treat the file as a hint, not authority. |
| 7 | Test isolation (HARD) | Persistence lives only in `game.py` (a leaf entry); add a `PYCATS_*` env override to redirect/disable, mirroring the existing `PYCATS_STATE_BACKEND`. |
| 8 | Shape | A small **general** `pycats/settings.py` (load/save a dict + path logic) so future prefs reuse it; keep the persisted payload small now. |

## What there is to persist (grounded in code)

Display state lives as `game.py` module globals:
- `windowed_scale` (float: 1.0/1.5/2.0/2.5) — **clean to persist**.
- `is_fullscreen` (bool) — **clean to persist**.
- Fullscreen zoom is `fullscreen_zoom_index` into `fullscreen_scales`, and that
  list is **computed per-monitor** (`display.achievable_zoom_scales`, #92). The
  index has **no stable cross-session/cross-monitor meaning** — persisting it is a
  trap (a different monitor yields a different list).

**Wrinkle → decision point.** For v1, recommend persisting **`windowed_scale` +
`is_fullscreen` only**, and keep fullscreen-zoom defaulting to "Fit" on entry
(current behavior). If a remembered fullscreen zoom is wanted later, persist a
*preferred zoom* as a scale/choice (e.g. `"fit"` or a target float) and
**re-resolve to the nearest achievable scale on load**, never the raw index. Flag
this for the architect; do not block v1 on it.

Suggested v1 schema:
```json
{ "version": 1, "windowed_scale": 1.5, "fullscreen": false }
```

## Q1 — Where to store

Use the OS user-config dir, namespaced `pycats/`:
- Linux: `$XDG_CONFIG_HOME/pycats/settings.json`, fallback `~/.config/pycats/settings.json`.
- (Windows `%APPDATA%\pycats\`, macOS `~/Library/Application Support/pycats/` if cross-platform is ever pursued.)

**Not** repo-local / cwd: that pollutes the working tree (needs a .gitignore entry),
breaks when the game is launched from another directory, and is wrong for a
per-user preference. The dir should be created lazily on first save.

## Q2 — Dependency vs stdlib

- **Stdlib (recommended):** a ~10-line helper reading `XDG_CONFIG_HOME`/`HOME`.
  Zero new deps (pycats today: pygame-ce + pytest only), correct on the Linux
  Mint target.
- **`platformdirs`:** the right answer for *correct* Windows/macOS paths, but adds
  a dependency for a personal, Linux-first project. Defer unless cross-platform
  becomes a goal. (This is a genuine decision point, not a slam-dunk.)

## Q3 — Format

**JSON.** Stdlib `json` reads *and* writes; maps cleanly to the flat typed dict;
human-readable/editable. `tomllib` (3.11+) is **read-only** (no stdlib writer), and
`configparser`/INI is clumsy for typed values and a `version` field. (Confirmed env
is Python 3.12.3.)

## Q4 — Lifecycle

- **Load:** once, at game startup, **before the first `pygame.display.set_mode`**,
  so the window opens at the saved scale/fullscreen with no visible re-init fl. The
  natural site is `game.py`'s top-level setup block.
- **Save:** on each change (the F10/F11 handlers). Writes are a few bytes and
  happen only on an explicit user action, so frequency is a non-issue, and you
  never lose a change to a crash (vs save-on-quit, which can). Recommend
  save-on-change; if write cost ever matters, debounce later.

## Q5 — Schema & versioning

Flat dict with an integer `version`. On load: take known keys, fill missing with
defaults, ignore unknown. On a shape change, bump `version` and migrate (or reset
to defaults for that key). Keeping it flat + versioned makes future prefs
(keybinds, audio) additive.

## Q6 — Robustness

The settings file is a **hint, not authority**. Missing file → defaults. JSON parse
error, wrong types, out-of-range values → log once and use defaults; **a bad file
must never brick the game**. Validate loaded values against the known presets
(e.g. clamp/snap `windowed_scale` to `WINDOWED_SCALE_PRESETS`).

## Q7 — Determinism & test isolation (hard requirement)

- The deterministic sim and goldens render at a fixed 960×540 and are **invariant**
  to display prefs; persistence is **present-layer only**. Confirmed: **nothing
  imports `game.py`** (it is the leaf interactive entry), and `sim/` is separate —
  so load/save placed in `game.py` cannot leak into the sim or the test suite.
- Provide an **env override mirroring the existing `PYCATS_STATE_BACKEND`** pattern
  (`os.environ.get` in `game.py`): e.g. `PYCATS_CONFIG_DIR` to redirect the file
  (point CI/headless at a temp dir) and/or `PYCATS_NO_PERSIST=1` to disable I/O.
  Any unit test for the load/save logic uses a `tmp_path`, never the real dir.
- Net: the headless runner / CI must never read or write the user's real settings
  file. This is a constraint on **whatever** approach the architect picks.

## Q8 — Precedent shape

Build a small **general** `pycats/settings.py` (resolve path, load dict, save dict,
defaults/validation) rather than a display-only loader — so the next pref reuses
the mechanism. Keep the *persisted payload* tiny for v1 (display only). General
mechanism, small data.

## Decision points for the ARCHITECT ticket

1. Store location confirm (user config dir) + **dependency: stdlib helper vs `platformdirs`**.
2. Format confirm (JSON).
3. Save-on-change vs save-on-quit.
4. **v1 scope: persist `windowed_scale` + `is_fullscreen` only?** (defer fullscreen-zoom persistence, or do the re-resolve-by-scale approach now).
5. General `settings.py` vs display-only.
6. Exact env-override name(s) for test isolation.

## Downstream (not done here)

- **ARCHITECT decision ticket #94** rules on the points above, then files the —
- **DEV implementation ticket** (`pycats/settings.py` + load-at-startup + save-on-change in `game.py`, with the env override and tmp-path tests).
