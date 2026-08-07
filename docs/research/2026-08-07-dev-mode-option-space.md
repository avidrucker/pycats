# `--dev` mode option space + minimal surface (#1293)

**Role:** RESEARCH · **Ticket:** #1293 · **Date:** 2026-08-07 · **Agent:** dragonfruit

> **Question (from #1293).** pycats has no dev/debug launch mode today —
> `pycats.game`'s `parse_args` (`pycats/game.py`) defines only `--speed`. What
> should a `--dev` mode offer, and how should it be structured? Survey the option
> space and recommend a minimal first `--dev` surface plus a phased roadmap.
> **Findings only — no implementation.** Each recommended affordance becomes its own
> downstream DEV ticket, filed one-at-a-time after this doc.

---

## TL;DR

- pycats already has most of the *machinery* a debug mode wants — a hitbox/hurtbox
  overlay (`pycats/render/debug.py`), a dev-info HUD (`pycats/render/hud.py`),
  live-toggle `runtime_settings`, a full headless snapshot harness
  (`pycats/sim/runner.py`), and a `PYCATS_DEV_LOG` env var. What is missing is a
  **single launch switch that turns the debug affordances on together**, plus a way
  onto **char-select for the dev-only cats** (`default`/`testcat`).
- Recommended **structure:** a **single boolean `--dev` flag** on `pycats.game` that
  sets one process-wide `runtime_settings.dev_mode` flag, which (a) gates the
  char-select roster addition (#1292) and (b) flips the presentation-only debug
  toggles ON by default. Keep sub-toggle granularity in the **existing Options menu /
  key bindings**, not in flag syntax. This keeps the shipping (no-flag) build
  byte-identical and keeps the sim deterministic (every dev affordance is
  presentation/inspection-only unless a future sub-toggle is explicitly labeled a
  sim cheat).
- Recommended **minimal first surface (Phase 1):** `--dev` exposes `default`/`testcat`
  on char-select (**#1292**, already filed) + turns on the hitbox overlay and the
  dev-info HUD rows by default. Everything else (frame-step, live-speed, velocity
  readout, god-mode) is Phase 2+ and each is its own DEV ticket.

---

## RQ2 — What already exists to build on

Inventory of debug/inspection surfaces present at HEAD (worktree
`wt-dragonfruit-pycats-1293`). A `--dev` mode should **compose with these**, not
duplicate them.

| Surface | Where (symbol + file) | How invoked today | Reusable for `--dev`? |
|---|---|---|---|
| Hitbox/hurtbox overlay | `render_hitbox_overlay` (`pycats/render/debug.py`), gated by `runtime_settings.show_hitbox_overlay()` | Options-menu row `hitbox_overlay`; no key binding | **Yes** — flip the toggle on under `--dev` |
| Dev-info HUD rows (FSM state, shield-attempting) | `hud_rows` / `draw_hud` (`pycats/render/hud.py`), gated by `runtime_settings.show_dev_info()` | **File-only** — no Options row, no key | **Yes** — the highest-value reuse; today it is unreachable without editing the settings file |
| Movement-status row / input-history grid | `show_movement_status()` / `draw_input_history` (`pycats/render/hud.py`) | Options-menu rows | Yes — candidate to default-on under `--dev` |
| Shell chrome (FPS, raw input string, fullscreen hint) | `draw_shell_chrome` (`pycats/render/hud.py`) | Always-on while playing | Already on; nothing to do |
| Live runtime toggles | `runtime_settings` (`pycats/storage/settings.py`) | Options menu / persisted settings | **Yes** — the natural home for a `dev_mode` flag |
| Env-var debug log | `PYCATS_DEV_LOG` / `PYCATS_DEV_LOG_PATH` (`pycats/storage/dev_log.py`) | Env var; writes `logs/LOGS.txt` breadcrumbs for unimplemented actions | Yes — orthogonal; `--dev` could default it on |
| Headless sim + per-frame snapshots | `run_battle`, `snapshot`, `PlayerSnap` (`pycats/sim/runner.py`) | Tests, `bench.py`, `watch.py` | **Yes** — `PlayerSnap` already carries `vel_x/vel_y` and every timer; the source for an on-screen velocity/timer readout |
| Battle event-log ("git-diff for the fight") | `events_from_snaps` / `render` (`pycats/sim/battle_log.py`) | `watch.py --log` | Yes — candidate in-game debug console feed |
| Deterministic seed | `random.Random(args.seed)` at the `watch.py` edge (#166) | `watch.py --seed`; **not** in `pycats.game` | Partial — seed plumbing lives in the sim CLI, not the live game |
| Sim CLI / spectator modes | `watch.py` (`--match`, `--vs`, `--demo`, `--show-inputs`, `--demo-speed`, `--shots`, …) | Separate entry point | Reference, not merge target — `watch.py` is already the "dev/debug surface" for sim replay |
| `--speed` present-rate factor | `parse_args` → `App(speed=...)` → `_present_speed` (`pycats/shell/app.py`) | CLI arg; **not live-changeable** (#933 is the planned Options picker) | Yes — a live-speed dev toggle would build on this |
| Pause (full-advance) | `_guard_playing_to_pause` (`pycats/shell/screen_manager.py`), `K_p` | In-game key | Foundation for frame-step (which does **not** exist yet) |
| Debug key bindings | `K_e`/`K_SEMICOLON` cycle cat-face style (#108), `K_F10`/`K_F11` fullscreen (`pycats/shell/app.py`) | In-game keys | F1–F9, F12, backtick/tilde are **all free** — room for a dev toggle key |
| Dev-only cat `testcat` | `CHARACTERS = list(ARCHETYPE_ROSTER) + ["testcat"]` in `watch.py` | Sim CLI only; deliberately kept out of `ARCHETYPE_ROSTER` | **Yes** — precedent that dev surfaces expose `testcat`; #1292 brings it to char-select under `--dev` |

**Gaps a `--dev` mode fills (not duplicated anywhere):**

1. No single switch turns the debug affordances on together.
2. `show_dev_info` (FSM/shield HUD rows) has **no** UI or key toggle at all — file-only.
3. No frame-step / single-advance (pause exists; step does not).
4. `--speed` is not live-changeable in the live game.
5. No on-screen velocity/timer readout, though `PlayerSnap` already carries the data.
6. `default`/`testcat` are resolvable but not selectable on char-select (#1292).

---

## RQ1 — Affordance census

Each candidate `--dev` affordance, with rationale, rough cost, and whether it is
**sim-safe** (presentation/inspection-only — does not change the deterministic sim)
or a **sim cheat** (mutates sim state; must be an explicit opt-in sub-toggle, never
default-on, and never active in golden/CI runs).

| Affordance | Rationale | Rough cost | Sim-safe? | Reuses |
|---|---|---|---|---|
| Expose `default`/`testcat` on char-select | Play/inspect the minimal fixture cat end-to-end without editing the roster (#1292) | **S** (already filed) | ✅ safe (roster gate only) | `char_select.py`, `registry.py` |
| Default-on hitbox/hurtbox overlay | See attack/vulnerable regions live; the #1 fighting-game debug view | **S** | ✅ safe | `render/debug.py` |
| Default-on dev-info HUD (FSM state, shield-attempting) | Read the state machine live; today unreachable without file edits | **S** | ✅ safe | `render/hud.py` |
| On-screen velocity + timer readout | Surface `vel_x/vel_y`, `*_timer` from the snapshot for physics/hitstun debugging | **M** (new HUD rows) | ✅ safe | `PlayerSnap` (`sim/runner.py`) |
| Frame-step / single-advance | Step one sim frame at a time to inspect startup/active/recovery frames | **M** (loop change; net-new) | ✅ safe (pacing only) | pause FSM (`screen_manager.py`) |
| Live `--speed` toggle (in-game slow-mo) | Slow the presentation to watch fast interactions; #933 already planned | **M** | ✅ safe (present-rate only) | `_present_speed` (`app.py`) |
| Debug toggle key (F1 / backtick) | One key to flip overlays without diving into Options | **S** | ✅ safe | free keys (RQ2) |
| Deterministic-seed display / set | Show/set the NPC PRNG seed for reproducible repros in the live game | **M** (seed plumbing is CLI-only today) | ✅ safe (display); set = config, still deterministic | `watch.py --seed` pattern |
| In-game battle event-log console | Live "git-diff for the fight" feed (jumps/hits/KOs/state changes) | **M–L** | ✅ safe | `battle_log.py` |
| Default-on `PYCATS_DEV_LOG` | Auto-capture unimplemented-action breadcrumbs during a dev session | **S** | ✅ safe (log only) | `dev_log.py` |
| God-mode / no-KO | Hold a fighter alive to study a move indefinitely | **M** | ⚠️ **cheat** — explicit sub-toggle only | fighter damage/KO path |
| Instant-respawn / stock refill | Reset quickly between trials | **M** | ⚠️ **cheat** | match/respawn path |
| Damage / knockback inspector (last-hit readout) | Show the damage + KB the last hit produced | **M** | ✅ safe (read-only) | hit-resolution + snapshot |
| Free camera / fixed zoom | Frame a specific interaction | **L** (camera is auto today) | ✅ safe | camera/render sizing |
| Stage/spawn tweaks | Place fighters at arbitrary positions for setups | **M** | ⚠️ **cheat** (sim state) | `build_players`/`build_stage` |
| Hurtbox-only / hitbox-only overlay split | Reduce overlay clutter when studying one side | **S** | ✅ safe | `render/debug.py` |

Cost key: **S** ≈ hours, **M** ≈ a day, **L** ≈ multi-day.

---

## RQ3 — Structure

Four candidate structures for modeling `--dev`.

| Option | Shape | Pros | Cons |
|---|---|---|---|
| **A. Single boolean flag** | `--dev` → one `runtime_settings.dev_mode` bool; presets a bundle of presentation toggles ON | Smallest surface; one obvious switch; trivial to keep no-flag build byte-identical; sub-granularity already lives in Options/keys | Bundle is coarse — can't pick a subset from the CLI (but Options/keys can override live) |
| **B. Comma-list sub-toggles** | `--dev=hitboxes,frame-step,testcat` | CLI-selectable granularity | Duplicates what Options/keys already do; parser + validation cost; two places to change a toggle; over-engineered for current needs |
| **C. In-game debug menu** | A dedicated debug screen reachable by a key | Discoverable; no CLI needed | Largest build; the Options menu already hosts most toggles; premature |
| **D. Env var** (`PYCATS_DEV=1`) | Mirror `PYCATS_DEV_LOG` | Consistent with existing env convention; scriptable | Less discoverable than a `--help`-listed flag; env vars suit *log/persistence* switches, flags suit *launch modes* |

**Recommendation: Option A — a single boolean `--dev` flag**, for now.

- It is the minimal change that delivers the value (turn debug affordances on
  together + open char-select to the dev cats).
- Granularity is not lost: the **Options menu and key bindings already exist** for
  per-toggle control, and `--dev` just changes their *defaults* for the session.
  If CLI-level granularity is ever needed, `--dev` can grow an optional value later
  (`--dev=hitboxes,...`) **without breaking the bare `--dev`** — so Option A does not
  foreclose Option B.
- Env var (D) stays reserved for its current role (log/persistence switches like
  `PYCATS_DEV_LOG`, `PYCATS_NO_PERSIST`); a *launch mode* belongs in `--help`.

**Invariants the structure must hold:**

1. **No-flag build unchanged.** With `--dev` absent, char-select shows exactly
   `ARCHETYPE_ROSTER` and every debug toggle keeps its shipping default — no
   player-visible change. (#1292 already states this for the roster half.)
2. **Sim determinism preserved.** Every default-on `--dev` affordance is
   presentation/inspection-only. Anything that mutates sim state (god-mode, spawn
   tweaks, instant-respawn) is a **cheat sub-toggle**: never default-on, never active
   in golden/CI/`runner`-driven runs. The golden harness (`sim/runner.py`) never
   constructs `App`, so CLI `--dev` cannot leak into snapshots — but a cheat routed
   through `runtime_settings` could, so cheats must check a separate explicit flag,
   not `dev_mode`.
3. **One flag, one owner.** `--dev` sets a single `runtime_settings.dev_mode`; every
   consumer reads that, so there is one place to reason about.

---

## RQ4 — Prior art (inference; labeled)

Comparable Smash-like / fighting-game debug builds, from general knowledge of the
scene. **Inference — not cited to pycats source; treat as directional, not
authoritative.**

- **Project M / Project+ debug mode.** PM ships a debug menu (roster of
  developer/test characters, hitbox display, frame-advance, infinite-shield / damage
  toggles, stage/spawn control). It is the closest analog to what pycats' `--dev`
  gestures at: a *bundle* of inspection + cheat affordances behind one entry, with
  hitbox display and frame-step as the flagship tools.
- **Melee 20XX Hack Pack / UnclePunch Training Mode.** Community training builds add
  hitbox/hurtbox overlays, frame-advance, save/load state, damage-per-hit readouts,
  DI/SDI displays, infinite shields, and CPU behavior scripting. The **save/load
  state** and **frame-advance** are the two most-praised affordances — both are
  inspection tools, not cheats, which supports pycats defaulting the *safe* set on
  and gating cheats behind explicit sub-toggles.
- **General game debug overlays** (engine-level): FPS/frame-time, entity state
  readouts, collision-shape rendering, a toggle key (often `~`/backtick or F1), and a
  console. pycats already has FPS + input string (`draw_shell_chrome`) and collision
  rendering (`render/debug.py`); the missing common piece is the single toggle key and
  the state/velocity readout.

**Takeaway for pycats:** the two affordances every training build converges on are
**hitbox display** and **frame-step**. pycats already has the first (just needs a
switch); the second is the highest-value net-new Phase-2 item.

---

## Recommended minimal first `--dev` surface (Phase 1)

The smallest `--dev` that is worth shipping:

1. **`--dev` boolean flag** on `pycats.game` `parse_args`, threaded to a single
   `runtime_settings.dev_mode` (structure Option A).
2. **Char-select opens to `default`/`testcat`** when `dev_mode` is set — this is
   **#1292**, already filed; it becomes Phase 1's concrete DEV slice.
3. **Hitbox/hurtbox overlay defaults ON** under `--dev` (flip
   `show_hitbox_overlay`).
4. **Dev-info HUD rows default ON** under `--dev` (flip `show_dev_info` — today
   file-only, so this is the first time those rows become reachable).

All four are cost-**S**, all sim-safe, all reuse existing machinery. Nothing in
Phase 1 touches the sim or the no-flag build.

---

## Phased roadmap (candidate downstream DEV tickets)

Filed **one-at-a-time downstream of this doc**, not here. #1292 is the only one
already filed.

**Phase 1 — the switch + the safe defaults (S each):**

- **#1292** *(filed)* — expose `default`/`testcat` on char-select behind `--dev`.
- **DEV** — add the `--dev` flag + `runtime_settings.dev_mode` plumbing (the switch
  #1292 gates on). *Sequencing:* #1292's roster gate reads `dev_mode`, so this and
  #1292 are coupled — file/land the flag first (or fold the flag into #1292's scope).
- **DEV** — under `dev_mode`, default the hitbox overlay + dev-info HUD rows ON.

**Phase 2 — the high-value inspection tools (M each, sim-safe):**

- **DEV** — frame-step / single-advance (net-new; builds on the pause FSM).
- **DEV** — live `--speed` toggle in-game (aligns with the planned #933 Options
  picker).
- **DEV** — on-screen velocity + timer readout from `PlayerSnap`.
- **DEV** — debug toggle key (F1 or backtick) to flip overlays without the Options
  menu.
- **DEV** — last-hit damage/knockback inspector.

**Phase 3 — cheats + heavier tooling (explicit sub-toggles; never default-on, never
in CI):**

- **DEV** — god-mode / no-KO (cheat sub-toggle).
- **DEV** — instant-respawn / stock refill (cheat).
- **DEV** — stage/spawn position tweaks (cheat).
- **DEV** — in-game battle event-log console (reuse `battle_log.py`).
- **DEV** — deterministic-seed display/set in the live game.
- **DEV** — free camera / fixed zoom.

Each Phase-2/3 ticket must state whether it is sim-safe or a cheat, and cheats must
carry an able-to-fail test proving they do **not** perturb `sim/runner.py` snapshots.

---

## Out of scope (per #1293)

- Implementing any affordance — the `testcat`/`default` slice is #1292; others become
  their own DEV tickets after this doc.
- Sim/balance changes; changing the shipping roster or resolution behavior.

## Cross-refs

- Companion DEV slice **#1292** (expose `default`/`testcat` behind `--dev`) — Phase 1.
- Entry point + `--speed`: `pycats/game.py`; live-speed picker planned in **#933**.
- Existing overlay/HUD: `pycats/render/debug.py`, `pycats/render/hud.py`.
- Snapshot harness: `pycats/sim/runner.py` (`PlayerSnap`); event log
  `pycats/sim/battle_log.py`.
- Sim CLI / spectator surface: `watch.py` (`area:watch`).
- Env debug convention: `PYCATS_DEV_LOG` (`pycats/storage/dev_log.py`).
