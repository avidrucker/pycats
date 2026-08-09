# CPU selection + leveling mechanics, and options to host a CPU in the live game

**Ticket:** #1338 (RESEARCH) · **Unblocks:** #1311 slice 7 (B8 "seed display/set in the live game") · **Feeds:** an ARC/decision follow-up (not this doc)
**As-of:** 2026-08-09 · **Anchor SHA:** `57064a3` (branch base = `main`)
**Scope:** findings + options only. No implementation, no chosen option, no AI-behavior tuning (see [Scope](#scope)).

---

## TL;DR

The CPU machinery (selection, leveling, seeded RNG) already exists and is complete — but it lives entirely on the sim/`watch.py` path and never touches `pycats.game`. The live game builds two **human** seats and has no RNG. The good news: both paths converge on one primitive — a single `InputFrame` handed to `Player.update()`, filtered per-player by that player's own keymap — and controllers already emit the **target player's own keymap keycodes**, so a controller-produced frame is union-compatible with a human frame (the exact merge `run_battle(controllers=…)` already does). Hosting a CPU is therefore a wiring problem (select a CPU seat + construct a controller + merge its frame + plumb a seed), not a mechanics-invention problem. B8 ("seed display/set") has no target until at least a seeded controller exists in the live loop.

---

## Q1 — How are CPUs selected today?

### The controller archetypes (`pycats/sim/controllers.py`)

Four controller classes, all subclassing `BaseController`:

- `BaseController` (`controllers.py:315`) — owns per-frame bookkeeping: resolves `(attacker, target)` from `attacker_num` (1 or 2), edge-detects `pressed`/`released` from the prior frame's `held`, captures each emitted `InputFrame` into `self.emitted`, and holds the injected `rng`. Subclasses implement `decide(a, t, frame, attacks, ledges) -> set` returning the keycodes to **hold** this frame. `__call__(p1, p2, frame, attacks, ledges)` (`controllers.py:349`) resolves the seat, calls `decide`, computes edges, and returns an `InputFrame`.
- `AttackerController` (`controllers.py:361`) — hunts the target and attacks; the only leveled archetype.
- `IdlerController` (`controllers.py:1042`) — stands, optional periodic shield.
- `FollowerController` (`controllers.py:1069`) — mirrors position at a standoff.

**Key vocabulary fact:** a controller emits the **target seat's own keymap keycodes**, not abstract tokens. `decide` reads `keys = a.controls` and does `held.add(keys["up"])`, `held.add(keys["attack"])`, etc. (`controllers.py:603`, `:906`, `:971`, `:1031`; idler `a.controls["shield"]` at `:1063`). Because P1/P2 keymaps are disjoint, a controller frame for seat 2 unions cleanly with a human frame for seat 1.

### The selection surface (`watch.py` — sim/demo CLI)

`watch.py::main` (`watch.py:93`) parses:
- `--vs <archetype>` (`watch.py:109`) — `chase`/`idler`/`follower`, mapping to `AttackerController` / `IdlerController` / `FollowerController` (P1 is always an attacker; P2 takes the `--vs` archetype).
- `--p1-level` / `--p2-level` (`watch.py:140`, `:147`) — integers 1–9; when set, routes through the leveled factory.
- `--seed` (`watch.py:125`) — see [Q3](#q3--how-does-the-seed-166-reach-the-controllers-and-what-is-byte-identical-safe).
- `--p1-char` / `--p2-char` (`watch.py:133`, `:138`).

The leveled factory is `cpu_controllers(p1_level, p2_level, rng)` (`watch.py:67`): returns `(c1, c2)` of `AttackerController(attacker_num=…, level=…, rng=rng)`, with a `None` level leaving that seat uncontrolled (idle).

### How a controller drives a battle (`pycats/sim/runner.py`)

`run_battle(…, controller=…, controllers=…)` (`runner.py:213`) is the headless per-frame loop. When `controllers=(c1, c2)` is passed:
- each frame calls every controller on the **same** frame-start snapshot, then merges by set-union before applying — `fi = merge_frames(c(p1, p2, f, attacks) … for c in controllers)` (`runner.py:269`);
- the merged `fi` goes to `p.update(fi, platforms, attacks, ledges)` for each player (`runner.py:275`).

This is the seam every option below reuses: **N controllers → per-seat `InputFrame` → `merge_frames` → one frame → `Player.update`.**

### Golden/CI paths

Golden and parity runs drive `run_battle` **directly** (with `frame_inputs` timelines or fixed-seed controllers), not through `App`/`pycats.game`. That separation is why adding a controller to the live loop cannot perturb goldens (see [Determinism](#determinism--golden-safety-the-constraint-every-option-shares)).

---

## Q2 — How is a CPU's level adjusted?

`LevelParams` (`controllers.py:123`) is a frozen dataclass of per-level AI knobs: `reaction_delay`, `attack_period`, `standoff` (deterministic core), plus seeded-RNG knobs (`follow_through_p`, `shield_chance`) and discrete capability flags (`reactive_shield`, `whiff_punish`, `enabled_moves`, `reach_aware`, `reactive_spacing`, `evade_chance`, `edge_hog`, `recover`, `edge_guard`).

- `LEVEL_PARAMS` (`controllers.py:183`) — sourced **anchor** rows for levels 1/3/5/7/9 (#148 Q5).
- `level_params(level)` (`controllers.py:282`) — returns anchors unchanged; **linearly interpolates** the continuous knobs for even levels between bracketing anchors (`_lerp`, `:297`); discrete capability flags **inherit the lower odd anchor** (a rung, not a half-step); out-of-range clamps to 1 or 9.
- `AttackerController.__init__` (`controllers.py:369`) applies the table when `level is not None` (`:398`) — every knob above is overwritten from `level_params(level)`. `level=None` keeps explicit defaults and is golden-safe.

**Tuning caveat (relevant to any player-facing level picker):** the level *axes* are sourced, but many *numbers* and *level cuts* are explicit placeholders. `LEVEL_PARAMS` header (`controllers.py:181`): "The axes are sourced; the numbers are pycats interpolations — tuning starting points, not measured PM data." `SMASH_KILL_PERCENT = 100.0` carries a `⚠ PLACEHOLDER_MECHANIC_DECISION` (`controllers.py:109`); the per-level smash policy is deferred to #915; the level=5 `enabled_moves` "smashes" unlock is a "PLACEHOLDER cut" (`controllers.py:212`). Several flag `⚠ values are tuning starting points` / `⚠ which levels = tuning` inline (`:162`, `:167`, `:172`). So a "pick difficulty 1–9" UI would expose knobs that are still being tuned (#714/#915/#751 strands) — a product decision, not a code blocker.

---

## Q3 — How does the seed (#166) reach the controllers, and what is byte-identical-safe?

- **Default seed → reproducible by construction.** `BaseController.__init__` (`controllers.py:330`) sets `self.rng = rng if rng is not None else random.Random(DEFAULT_CONTROLLER_SEED)`, with `DEFAULT_CONTROLLER_SEED = 0` (`controllers.py:307`). So an un-injected controller is deterministic; sims/goldens/parity stay reproducible.
- **The RNG lives only at the controller edge.** The docstring at `controllers.py:337` records the invariant: the RNG "can influence the chosen `InputFrame` but never reaches the (input-only) FSM backends." A seed changes *which keys the controller chooses*, never how the fighter FSM resolves them.
- **Seed home is the CLI edge.** `watch.py::main` builds `rng = random.Random(args.seed) if args.seed is not None else random.Random()` (`watch.py:203`) and passes it to `cpu_controllers`. An explicit `--seed` is reproducible; an absent `--seed` uses a clocktime seed and the battle varies per run.
- **Golden-safe default.** The seeded-RNG knobs (`follow_through_p`, `shield_chance`, `evade_chance`) default to values that never touch the rng stream (always commit; never shield; never roll) — `controllers.py:418`. So a controller with default knobs is not just seeded-deterministic, it is rng-inert.

**This is the thread B8 depends on.** "Seed display/set in the live game" only has meaning once the live game constructs a controller with an injectable `rng`. Today `pycats.game`/`App` construct no `Random` and take no `--seed`, so there is nothing to display or set.

---

## Q4 — What must change to host a CPU in the live game?

### The live input path today (all human)

- `game.main()` (`pycats/game.py:70`) boots pygame, builds shared P1/P2 keymaps, and drives `while app.running: app.step()` (`:108`).
- `App.step()` (`pycats/shell/app.py:148`) calls `self._poll()` (`:152`) → `input_poll.poll()` builds **one** `InputFrame` from pygame KEYDOWN/KEYUP for **all** keys (both keymaps): `InputFrame(held=_currently_held.copy(), pressed=keys_down, …)` (`pycats/shell/input_poll.py:17`).
- That single frame flows `screen_manager.update(frame_input, battle, platforms)` (`app.py:210`) → `BattleScreen.step(frame_input, platforms)` (`pycats/screens/battle_screen.py:156`) → `p.update(frame_input, …)` for **each** player (`:168`).
- Each `Player.update(input_frame, …)` (`pycats/entities/player.py:323`) filters `input_frame.held`/`.pressed` against `self.controls` (its own keymap; set at `player.py:175`, read throughout `fighter_input.py`, e.g. `:38`, `:130`). So both seats reading the same frame is already the norm — disjoint keymaps make it work.
- `BattleScreen.__init__` (`battle_screen.py:50`) builds `player1`/`player2` from `p1_keys`/`p2_keys` only (`:105`, `:116`). No controller field exists.

### The seams a CPU seat needs

1. **A controller frame merged into the live frame.** The one behavioral change: for the CPU seat, replace the human keys with `controller(player1, player2, frame, attacks, ledges)` and union it with the other seat's human frame — i.e. do in the live loop what `run_battle` does at `runner.py:269`. Natural home: `BattleScreen.step` (it already holds `player1/player2/attacks/_ledges`, `battle_screen.py:169`) or the `App`→battle boundary. `merge_frames` (`pycats/core/input.py:26`) is the ready-made union.
2. **A place to select the CPU seat + level.** Char-select (`pycats/screens/char_select.py`) builds two human seats today; there is no "P2 = CPU (level N)" affordance. A CPU choice must enter somewhere (char-select option, a new pre-battle toggle, or a dev-only affordance) and reach `BattleScreen` construction.
3. **A live RNG + seed plumb.** `game.py::parse_args` has only `--speed`/`--dev` (no `--seed`); `App` constructs no `Random`. A CPU seat needs an `rng` built at boot (or at battle start) and handed to the controller — the live analogue of `watch.py:203`. This is the concrete B8 hook.
4. **A frame counter + battle context for `decide`.** Controllers take a frame index and (optionally) the live `attacks` group + `ledges` for threat-aware/edge-hog policies (`controllers.py:341`, `runner.py:269`). `BattleScreen` already owns `self.attacks` and `self._ledges` (`battle_screen.py:151`, `:158`) and can supply a per-battle frame counter.

### Coupling: importing a controller into the live game is cheap

`pycats/sim/controllers.py` imports only `random`, `dataclasses`, `decimal`, `..combat.geometry` (`move_reach`), and `..core.input` (`InputFrame`) — `controllers.py:9-16`. It does **not** import `pycats.sim.runner`, `watch.py`, or pygame. So the live game (`pycats/shell`, `pycats/screens`) can import `AttackerController` / `level_params` without pulling in the sim harness. The only mild awkwardness is a `pycats.screens`/`pycats.shell` → `pycats.sim` import direction; whether to leave the controller in `pycats/sim/` or extract the archetype into a neutral package (e.g. `pycats/ai/`) is an ARC call, not a hard blocker.

### Loop-rate / timestep

The live loop advances the sim **one `battle.step` per `App.step`**; `--speed` gates only `self.clock.tick(tick_fps(self._present_speed()))` in the playing state (`app.py:151`, `:144`), i.e. it changes wall-clock pacing, not sim-steps-per-frame. So a controller's per-frame `decide` sees the same one-call-per-sim-frame cadence it sees under `run_battle`. **Flagged to verify at implementation time**, but the evidence points to no timestep mismatch: both loops call `Player.update` once per sim frame.

---

## Gap list (what blocks a CPU appearing in `pycats.game` today)

| # | Gap | Landmark |
|---|-----|----------|
| G1 | No controller is constructed anywhere on the live path; `BattleScreen` has no controller field. | `battle_screen.py:50` |
| G2 | The live frame is 100% human (`input_poll.poll`); nothing merges a controller frame. | `input_poll.py:17`, `app.py:152` |
| G3 | No CPU-seat selection UI; char-select builds two human seats. | `char_select.py`, `battle_screen.py:105` |
| G4 | No live RNG / `--seed`; `parse_args` has only `--speed`/`--dev`. | `pycats/game.py` (`parse_args`) |
| G5 | No per-battle frame counter exposed to a controller on the live path. | `battle_screen.py:156` (`step`) |
| G6 | Import-direction question: controller lives in `pycats/sim/`; live game would import from the sim package (low-cost, not blocking). | `controllers.py:9-16` |
| G7 | Level knobs are partly placeholder-tuned; a player-facing 1–9 picker exposes un-finalized values. | `controllers.py:181`, `:109`, `:212` |

---

## Options matrix — wiring CPU selection into the live game

Each option is scored on **cost** (S/M/L), **determinism/golden-safety**, and **seed/B8 dependency**. None is chosen here.

### Option A — Dev-mode-only CPU toggle (minimal seam)

Behind the dev-mode gate (#1312), a key toggles "P2 = CPU (fixed level)". `BattleScreen.step` (or the App→battle boundary) constructs an `AttackerController(attacker_num=2, level=<const>, rng=<seeded>)` on toggle and merges its frame via `merge_frames`. No char-select changes; no shipping-path change.

- **Cost:** **S–M.** One controller field + merge call + a dev-gated toggle + a boot-time `Random`. Reuses `cpu_controllers`/`AttackerController` and `merge_frames` verbatim.
- **Determinism / golden-safety:** **High.** The CPU path is entered only under dev mode (false in golden/CI/`runner`, per #1312/#1332 discipline); goldens drive `run_battle` directly and never construct `App`. The shipping build is unchanged.
- **Seed/B8:** Directly creates the B8 hook — the dev toggle needs a live `rng`, so seed display/set has an owner. Smallest surface that unblocks B8.

### Option B — Char-select "P2 = CPU (level N)" picker (product feature)

Add a CPU seat + level selector to `char_select.py`; carry the choice into `BattleScreen` construction so the battle starts with a leveled controller on the chosen seat.

- **Cost:** **M–L.** Char-select UI/state changes, a battle-config seam from select → `BattleScreen`, plus the controller merge (Option A's core). Player-visible → an eyeball-OK gate (per #1297 constraint 1).
- **Determinism / golden-safety:** **High for goldens** (same `App`-vs-`run_battle` separation), **but ships to players** — so it exposes the placeholder-tuned levels (G7) as a product surface. That is a design decision, not a golden risk.
- **Seed/B8:** Needs the same live `rng`; B8 could surface as a seed field in char-select or a dev readout. Larger blast radius than A.

### Option C — Input-source abstraction (refactor-first)

Introduce a per-seat "input source" seam (human-keys source vs controller source) so `BattleScreen`/`App` treats both uniformly, then plug `cpu_controllers` in behind it. Optionally extract the archetype from `pycats/sim/` into a neutral package to fix the import direction (G6).

- **Cost:** **L.** A new abstraction over the input path + migration of the human path onto it + optional package move. Highest up-front cost; cleanest end state and the most reusable for future modes (replays, netplay, demos).
- **Determinism / golden-safety:** **High if the human path stays byte-identical** — the abstraction must be a pass-through for the two-human default (an able-to-fail no-drift test vs `run_battle`, mirroring the #1332/#587 discipline, would guard it).
- **Seed/B8:** Same live-`rng` requirement; the abstraction gives seed plumbing a natural home (the controller input-source owns its `rng`).

**Relationship:** A is a strict subset of B and C — the controller-frame merge is common to all three. A can ship first (unblocks B8 fastest); B or C can subsume it later without rework of the merge seam.

---

## Determinism / golden-safety: the constraint every option shares

- Goldens/parity/CI drive `run_battle` **directly** (fixed `frame_inputs` or fixed-seed controllers), never `App`/`pycats.game`. So a CPU on the live loop cannot perturb a golden **as long as** the two-human default path stays byte-identical.
- The same discipline #587 (dev_log) and #1332 (default-on dev-log under dev mode) already hold applies: keep the CPU construction out of the default (non-CPU, non-dev) path, and any live `rng` opt-in.
- A no-drift able-to-fail test (two-human `App` step sequence vs the pre-change baseline, or vs a `run_battle` reference) is the guard the ARC option should mandate — especially for Option C's pass-through claim.

---

## Decisions for ARC (this doc does NOT make them)

1. **Which option** (A dev-only toggle / B char-select picker / C input-source abstraction) — or A-now-then-C-later.
2. **Is CPU-in-live-game V1 or post-V1?** #1311 scopes dev-mode V1; a shipping CPU picker (Option B) is arguably a separate feature, while a dev-only toggle (Option A) fits the dev-mode epic.
3. **Does B8 fold into the CPU work or stay deferred?** B8 has no target without a live controller; ARC should decide whether B8 becomes "seed the dev CPU toggle" (folds into A) or stays parked until a CPU seat ships.
4. **Which seat(s) can be CPU** — P2 only, either, or both — and **fixed level vs 1–9 picker** (the latter exposes G7's placeholder-tuned knobs).
5. **Import direction / package** — leave the archetype in `pycats/sim/` (live game imports sim) or extract to a neutral package (`pycats/ai/`), resolving G6.
6. **Level-tuning readiness** — whether a player-facing difficulty picker is gated on closing the #714/#915/#751 tuning strands (G7), or ships with placeholder values behind a "beta"/dev label.

---

## Scope

- **No implementation** — no controller is wired into the live game here.
- **No decision** — no option is chosen; B8 is not re-ruled.
- **No AI-behavior tuning** — the open `LevelParams` placeholders (#714/#915/#751) are noted as context, not resolved.

## Refs

- Blocked slice: #1311 slice 7 (B8) · ruling #1297 (`docs/design/dev-mode-v1-rulings.md`, B8 row) · option-space research #1293 (`docs/research/2026-08-07-dev-mode-option-space.md`).
- CPU machinery: `pycats/sim/controllers.py` (`BaseController`, `AttackerController`, `LevelParams`, `LEVEL_PARAMS`, `level_params`), `watch.py` (`cpu_controllers`, `--vs`/`--p*-level`/`--seed`), `pycats/sim/runner.py` (`run_battle`). Seed thread: #166. Level system: #231/#232/#148/#244/#703.
- Live-game seams: `pycats/game.py` (`main`, `parse_args`), `pycats/shell/app.py` (`step`, `_poll`), `pycats/shell/input_poll.py` (`poll`), `pycats/screens/battle_screen.py` (`__init__`, `step`), `pycats/screens/char_select.py`, `pycats/entities/player.py` (`update`), `pycats/core/input.py` (`InputFrame`, `merge_frames`).
