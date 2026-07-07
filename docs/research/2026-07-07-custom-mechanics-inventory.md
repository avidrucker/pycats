# Custom / PM-divergent mechanics inventory (spike #605)

**Role:** RESEARCH spike · child of **#604** (the WRITER doc `custom-pycats-mechanics.md`).
**Deliverable:** this categorized inventory — the raw source material #604 composes into a
clean reference. **Survey + catalogue only; this spike does NOT write `custom-pycats-mechanics.md`.**

Scope: engine mechanics/conventions that are **invented by pycats** or **divergent from
Project M**. PM-faithful mechanics (`docs/pm-reference/`) are out of scope. Each entry:
**name · invented-or-divergent · code landmark (function/file) · how-it-works · gotchas ·
cross-refs**. Grouped by domain. Landmarks are named symbols, not raw line numbers
(they drift).

Suite state at survey time: `1313 passed, 1 xfailed` (worktree, main-repo venv).

---

## 1. Render / status feedback

### 1.1 `StatusSource` — declarative status table (invented)
- **Kind:** pycats-invented render architecture.
- **Landmark:** `StatusSource` (NamedTuple) + the `STATUS_SOURCES` list in
  `pycats/render_battle.py`; consumers `active_tint(p)` and `timer_bar_specs(p)`.
- **How it works:** one declarative record per status (hurt / shield / stun / dodge / lockout /
  invuln / …) is the single source both the body-flash tint and the above-head timer bars
  derive from. A record carries `precedence`, an `active(f, p)` predicate, an optional `tint`,
  and bar fields (`bar_color`, `bar_label`, `bar_class`, `ratio`, `readout`, `recency`). Adding
  a status (e.g. #531 ledge-invuln, #506 respawn) is one record, no new branches.
- **Gotchas:** the migration (#522) is **byte-identical** to the pre-existing `active_tint`
  if-chain and `timer_bar_specs` branch logic — that identity is the guard, so edits must
  preserve it. The dizzy star-halo (`draw_dizzy_stars`) is a **separate** render path, not
  modelled in the table.
- **Cross-refs:** #522, #357, #364, #380.

### 1.2 `precedence` + `bar_class` — exclusive-vs-overlay bar selection (invented)
- **Kind:** pycats-invented priority model (the #604 trigger example).
- **Landmark:** `StatusSource.precedence` / `StatusSource.bar_class`; `active_tint` and
  `timer_bar_specs` in `render_battle.py`.
- **How it works:** `precedence` is a **low-wins** order. `active_tint` returns the first live
  source's `tint` (single body flash). `timer_bar_specs` adds the **first live `"exclusive"`
  bar** (shield / stun / hang / prone are mutually exclusive states — shield wins the elif
  chain) **plus every live `"overlay"` bar** (LOCKOUT #357, INVULN #358 — state-independent,
  so they co-activate).
- **Gotchas:** overlay bars are returned **newest-on-top**, sorted by `recency = max −
  remaining` (frames elapsed) ascending, so `specs[0]` is drawn nearest the head. The shield
  resource gauge has no elapsed-frame notion and sorts **last** via the `_SHIELD_RECENCY_KEY`
  sentinel. Ordering is stable (equal recency keeps insertion order).
- **Cross-refs:** #522, #357, #358, #531, #506.

### 1.3 Status-bar / dev-info runtime flags (invented tooling-in-render)
- **Kind:** pycats-invented toggles.
- **Landmark:** `show_status_timer_bars()` and `show_dev_info()` in `pycats/runtime_settings.py`;
  `timer_bar_specs` early-returns `[]` when the former is off.
- **How it works:** `show_status_timer_bars` (#111/#121) gates the above-head timer bars;
  `show_dev_info` (#545) gates HUD **dev-jargon rows** (`FSM:` / `Shield Attempting:`),
  default **off**. Both are pure runtime-settings reads, so the sim/golden path is unaffected.
- **Gotchas:** these are render-only; flipping a **default-on** render flag can shift the
  render-parity oracle (§5.2) even though sim goldens are render-free (§5.1).
- **Cross-refs:** #111, #121, #545.

### 1.4 `char_name` vs archetype key vs cosmetic skin (invented naming split)
- **Kind:** pycats-invented identity/cosmetic separation.
- **Landmark:** `ARCHETYPE_DEFAULT_SKIN` / `ARCHETYPE_PALETTE` / display-name map in
  `pycats/characters/roster.py`; `char_name` consumers across `battle_screen.py`,
  `render_battle.py`, `sim/runner.py`, `entities/player.py`, `domain/player_identity.py`.
- **How it works:** an **archetype key** is the fighter identity `load_fighter_data` knows
  (Nalio #142, Birky #228, Narz #294); each archetype has a **default cosmetic skin** (an OG
  colour-palette, `ARCHETYPE_DEFAULT_SKIN`, single source per #650) that the char-select
  skin-cycle can change. The display name shown on the tile is the **archetype**, not the
  palette.
- **Gotchas:** the default palette is flagged **⚠ playtest-TBD / cosmetic-only** in the roster
  — not a sourced value. The domain layer (#672/#680) is mid-migration off the bare-string
  path onto a `Selection`/`Skin` model; the anonymous-default retirement is #586.
- **Cross-refs:** #268, #127, #650, #586, #672, #680.

---

## 2. Combat / physics values (provenance registry)

The ground-truth list of marked divergences is `TUNING_PROVENANCE` in
`pycats/combat/provenance.py` (ADR-0003, #233). Each row is a `Provenance(value, unit,
source, status, issue, derivation)` keyed by the exact `config` constant name; the
drift-guard `tests/test_tuning_provenance.py` asserts (1) no drift vs live `config`, (2) no
orphans vs `TUNING_CONSTANT_NAMES`, (3) derivation integrity. The status taxonomy is itself
a pycats convention: **FOUND** (traced to cited canon), **GUESS** (unsourced playtest start),
**TUNED** (deliberate design value, not seeking canon), **DIVERGENCE** (intentional departure
from a known canon value). **FOUND rows are PM-faithful and out of scope** — listed only as
the complement. This section enumerates **every DIVERGENCE and TUNED row** (the completeness
gate), plus the GUESS rows.

### 2a. DIVERGENCE rows (intentional departures from known canon) — all 4

| Constant | value·unit | Departs from | Why (landmark: `provenance.py` row) |
|---|---|---|---|
| `MAX_FALL_SPEED` | 13 px/f | Melee/PM base 1.7 / fast-fall 2.3 u/f **split** | Single global fall speed ≈ PM Mario fast-fall; the base/fast-fall split is **not modelled**. (#120/#384) — this is seed #8. |
| `KNOCKBACK_LAUNCH_FACTOR` | 0.085 factor | Smash `launch_speed = KB*0.03` | Deliberately scaled to the **960px stage** (`knockback-launch-physics-findings.md`, #43). (#44) — seed #8. |
| `KNOCKBACK_DECAY` | 0.145 px/f | Smash decay 0.051/frame | Scaled to the 960px stage, **preserving the 1.7 decay/launch ratio**. (#44) — seed #8. |
| `GETUP_ROLL_FRAMES` | 16 frames | Melee getup roll 35f, intangible 1-14..1-24 | pycats runs a **shorter roll on its own scale**; duration == its intangibility window. (#146) |

### 2b. TUNED rows (deliberate design values, not seeking canon) — all 24

| Constant | value·unit | Note (from `provenance.py`) |
|---|---|---|
| `DODGE_SPEED` | 14 px/f | pycats ground-roll boost; Melee rolls animation-driven, no single canon. |
| `JOSTLE_MIN_VOVERLAP_FRAC` | 0.8 factor | vertical-overlap gate for the PM X-only push heuristic (#68). |
| `SHIELD_MAX_HP` | 50 hp | pycats shield-HP model; Melee uses a different shield-health/decay model (#12). |
| `SHIELD_DRAIN_PER_FRAME` | 0.2 hp/f | pycats shield drain/regain rate, no canon equivalent (#111). |
| `HITSTUN_FLOOR` | 1 frame | pycats floor ≥1f for any clean hit; SmashWiki documents no canon minimum (#138). |
| `SAKURAI_AIRBORNE_DEG` | 40.0 deg | keyed to pycats `knockback()` magnitude, not Smash units (#203). |
| `SAKURAI_GROUNDED_MAX_DEG` | 40.0 deg | grounded max angle at HIGH_KB; pycats magnitude, no canon (#203). |
| `SAKURAI_GROUNDED_LOW_KB` | 60.0 kb | grounded angle stays flat below this pycats KB magnitude (#203). |
| `SAKURAI_GROUNDED_HIGH_KB` | 88.0 kb | grounded angle reaches max at this pycats KB magnitude (#203). |
| `KNOCKDOWN_VY_THRESHOLD` | 8.0 px/f | pycats auto-knockdown impact-speed gate; pycats-specific (#145). |
| `KNOCKDOWN_PRONE_FRAMES` | 30 frames | fixed getup window ~0.5s; Melee is variable + per-character (#145). |
| `GETUP_ROLL_SPEED` | 12.0 px/f | pycats getup-roll horizontal speed; animation-driven in canon (#146). |
| `LEDGE_GETUP_FRAMES` | 16 frames | pycats neutral ledge-getup climb; PM getup frames per-character (#311). |
| `GROUND_FRICTION` | 0.5 factor | pycats ground friction knob (1.0=ice); no PM equivalent. |
| `AIR_FRICTION` | 0.85 factor | pycats air friction knob; no PM equivalent. |
| `HURT_TIME` | 12 frames | pycats hurt/flinch timer; no PM canon. |
| `LEDGE_REGRAB_LOCKOUT_FRAMES` | 30 frames | pycats post-release regrab-suppression window (#14). |
| `PLAYER_ATTACK_DURATION` | 12 frames | pycats default attack duration; no PM canon. |
| `INITIAL_LIVES` | 3 stocks | match ruleset setting, not a PM physics value. |
| `RESPAWN_DELAY_FRAMES` | 120 frames | pycats respawn freeze ~2s (`int(2*FPS)`); ruleset value, no canon. |
| `PLAYER_SIZE` | (40,60) px | default fighter collision box; reclassified render→collision (#584/#598). |
| `LEDGE_CATCH_W` | 24 px | ledge-grab catch-region width; pycats geometry (#584). |
| `LEDGE_CATCH_H` | 64 px | ledge-grab catch-region height; pycats geometry (#584). |
| `BLAST_PADDING` | 50 px | KO boundary px beyond screen edge; pycats stage rule (#584). |

### 2c. GUESS rows (unsourced playtest starts — not divergences, flagged ⚠ in config)
`DODGE_FRAMES` (15f), `DODGE_TIME` (14f), `PROJECTILE_GRAVITY` (0.5), `PROJECTILE_RESTITUTION`
(0.6), `PROJECTILE_MAX_BOUNCES` (3), `DASH_DURATION` (12f), `FSMASH_ANGLE_UP` (50°),
`FSMASH_ANGLE_DOWN` (330°). The #319 value-sourcing pass resolves these; #604 may fold them
under "divergences worth flagging" or leave to the registry.

**Domain finding:** the registry is the complete marked-divergence surface. Beyond the 4
DIVERGENCE + 24 TUNED + 8 GUESS rows above, **nothing further in `provenance.py` is
non-canon** — the remaining rows are FOUND (PM-sourced, out of scope). One accuracy flag:
`SMASH_CHARGE_FRAMES` (59) is FOUND but **primary-unconfirmed** (single secondary, engine-
hardcoded; needs a PM DOL/RAM dump per #626) — not a divergence, but #604 might note the
soft sourcing.

---

## 3. Input / move selection

### 3.1 The `"attack"` legacy move-key alias (invented convention)
- **Kind:** pycats-invented naming convention (seed #5).
- **Landmark:** `resolve_move_key` / `select_move_key` in `pycats/combat/move_select.py`;
  the module docstring defines the key vocabulary.
- **How it works:** `"attack"` is the **legacy neutral-ground alias** kept as the generic A
  fallback — Nalio's d-tilt and the default cat's jab both live under it, so a partial-kit
  character behaves as before the move-selection seam (#143). Canonical keys are
  `jab/ftilt/utilt/dtilt`, `nair/fair/bair/uair/dair`, `neutral_b/side_b/up_b/down_b`,
  `fsmash/usmash/dsmash`.
- **Gotchas:** the fallback ladder is asymmetric: smash → matching **tilt** → `"attack"`;
  **special (B) → None** (no fallback, silent no-op → §6 dev_log); ground A → `"attack"`;
  air A → `"nair"` else `"attack"`. Forward/back both collapse to ftilt on the ground (Smash
  has no b-tilt); neutral/back smash collapse to fsmash (no neutral smash, back = turnaround).
- **Cross-refs:** #143, #142, #327, #331.

### 3.2 `MoveClock` temporal windows (invented state consolidation)
- **Kind:** pycats-invented single-source-of-truth object.
- **Landmark:** `MoveClock` / `MoveTick` in `pycats/combat/move_clock.py`.
- **How it works:** one object owns the executing `MoveData` + frame counter and replaces the
  triple-tracked `current_move`/`move_frame`/`_move_hitbox_spawned` (plus the legacy
  `attack_timer`/`done_attacking` shims) that used to live on `Player`. `Player` **derives**
  `attack_timer` (== `remaining`), `current_move`, `move_frame` from it, so both the legacy FSM
  and the statechart read byte-identical values. Supports **multiple hitbox windows** opening
  on different frames (#130 multi-hitbox, #204 multi-window).
- **Gotchas:** POST-increment convention — `start()` sets frame 0, first `tick()` makes
  `frame == 1`; active window is `startup < frame <= startup+active`; move completes at
  `frame >= startup+active+recovery`. Golden invariant: while live, `remaining == total − frame`.
- **Cross-refs:** #130, #204.

### 3.3 up-B / special-recovery hook (invented `MoveData` extension)
- **Kind:** pycats-invented move-data fields (seed #6).
- **Landmark:** `MoveData.grants_recovery` / `recovery_vy` / `recovery_vx` in
  `pycats/combat/data.py`; consumed in `fighter_input.py` (arms on move start);
  `Fighter.recovery_active` flag in `pycats/entities/fighter.py`.
- **How it works:** a move with `grants_recovery=True` gives an **upward burst** on start
  (`vel.y = recovery_vy`, `vel.x = recovery_vx * facing`) and arms `recovery_active`. When the
  move ends airborne the statechart routes the fighter into the reused **`helpless`** state
  (special-fall), not `fall`.
- **Gotchas:** `recovery_active` is armed in `fighter_input` and **cleared on land** (and on
  respawn) — see the three `recovery_active = False` sites in `fighter.py`. It reuses the PM
  air-dodge `helpless` state rather than a new one (#184).
- **Cross-refs:** #578, #184.

**Domain finding:** beyond the alias, the clock, and the recovery hook, **nothing further
invented in input/moves** — the direction-token mapping and smash resolution are
PM-structural (no b-tilt / no neutral-smash mirror the real games).

---

## 4. Physics / state routing

### 4.1 Statechart flag→state routing (invented pattern)
- **Kind:** pycats-invented statechart convention.
- **Landmark:** `pycats/charts/fighter_chart.py` — guard lambdas reading `Fighter`
  boolean flags (`recovery_active`, air-dodge active) to pick the exit state.
- **How it works:** transitions are guarded by fighter flags rather than encoded purely in
  states: an attack that ends airborne with `recovery_active` → `helpless`; a PM air dodge →
  `helpless` (special-fall). The flags live on `Fighter`; the chart routes on them.
- **Gotchas:** `helpless` is **shared** by up-B recovery (#578) and air dodge (#184) — one
  state, two arming paths. Priority matters: the recovery→helpless guard sits **above** the
  fall exit.
- **Cross-refs:** #578, #184.

### 4.2 Single global fall speed (divergence) — see §2a `MAX_FALL_SPEED`
Cross-listed: physics consequence of the `MAX_FALL_SPEED` DIVERGENCE — no base/fast-fall split
exists in the physics step, so fast-fall input has no distinct terminal velocity.

### 4.3 Friction knobs (invented) — see §2b `GROUND_FRICTION` / `AIR_FRICTION`
Cross-listed: pycats-specific friction model (1.0=ice … 0.0=instant stop), no PM equivalent.

**Domain finding:** the pycats physics model is otherwise calibrated to PM via `PX_PER_UNIT`
(§5.3) — the divergences are the fall-speed simplification, the 960px-stage knockback scaling
(§2a), and the friction/getup design knobs (§2b). Nothing else invented here beyond the seeds.

---

## 5. Tests / oracles

### 5.1 Sim goldens — render-free byte detector + semantic sidecar (invented oracle model)
- **Kind:** pycats-invented test architecture (seed #4).
- **Landmark:** `tests/test_golden.py` + `tests/golden_util.py` (`check_or_update`);
  baselines `tests/golden/<name>.json` + `<name>.summary.json`; protocol
  `tests/golden/REGEN_PROTOCOL.md`.
- **How it works:** a deterministic battle's per-frame snapshots are compared against a
  committed baseline. The `.json` is an **opaque byte-identical detector**; the
  `.summary.json` sidecar is a **reviewable semantic digest** (frames, winner, states, lives
  start·end·min, percent_max, KO frames, attack-active frames). `check_or_update` keeps both
  in lock-step so a behaviour change fails with the **small summary diff first**.
- **Gotchas:** goldens run `sim/runner.py` — **no render path**, so render changes never touch
  them. `PYCATS_UPDATE_GOLDENS=1` re-records with **zero scrutiny**; the REGEN_PROTOCOL exists
  so a regen is reviewed (identify the causing code change; read sidecar diffs; a **disappearing
  KO / rising `lives_end` / `percent_max`→0 / dropped state** is a regression red flag).
- **Cross-refs:** REGEN_PROTOCOL.md, ADR-0003 interlock, #233.

### 5.2 Render-parity byte oracle (invented divergence guard)
- **Kind:** pycats-invented parity test.
- **Landmark:** `tests/test_battle_screen_render.py` (BattleScreen.render / render_paused must
  be **byte-identical** to game.py's inline composition); slice 2b of #100 (#205).
- **How it works:** render is **not** golden-covered, so this parity test is the real
  divergence guard for the render extraction — the render analogue of the sim-path parity test.
- **Gotchas:** because it is byte-identical, a **render-only** change or a **default-flag flip**
  (§1.3) **can** flip it even though sim goldens can't. `draw_hud`/`draw_controls` were moved
  to `render_battle.py` (their slice-2b home).
- **Cross-refs:** #100, #205.

### 5.3 Screen-flow parity — statechart == frozen golden (invented freeze)
- **Kind:** pycats-invented equivalence freeze.
- **Landmark:** `tests/test_screen_parity.py` (`test_statechart_screen_trace_matches_golden`);
  golden `tests/golden/screen_parity.json`.
- **How it works:** this is an **FSM transition trace**, not a pixel test. The legacy
  guard-table screen engine was deleted (ADR-0002 #174, epic #100); its per-step transition
  sequence was frozen as a recorded golden (#234) before deletion (#235), and the surviving
  statechart engine is checked **statechart == golden** — the frozen record standing in for
  the deleted second engine.
- **Gotchas:** it pins **flow semantics** (initial state, transition order, on_enter/on_update,
  force), not rendering — a char-select cosmetic change won't touch it. Regen only after a
  reviewed, intended screen-flow change.
- **Cross-refs:** ADR-0002, #100, #174, #234, #235, #176.

**Domain finding:** three distinct oracle families (sim-golden byte+sidecar, render-parity
byte, screen-flow trace) — each guards a different layer. Nothing else invented here beyond
the seeds; the many `test_render_*` files are unit-level, not new oracle models.

---

## 6. Tooling

### 6.1 `dev_log` — gated not-yet-implemented breadcrumb (invented, seed #7)
- **Kind:** pycats-invented dev tool.
- **Landmark:** `pycats/dev_log.py` (`enabled()`, `_log_path()`, `reset()`); consumed in
  `fighter_input.py` when `resolve_move_key` maps an attempted action to `None`.
- **How it works:** when a fighter attempts an unimplemented action (e.g. an undefined special),
  the input silently no-ops in play; `dev_log` instead writes one line per attempt to a
  **gitignored** `logs/LOGS.txt`. **OFF by default** — writes only when `PYCATS_DEV_LOG` is set
  (truthy), so the sim/golden/test path does **zero file I/O** and stays byte-identical (a hard
  #587 requirement). De-dupes per `(fighter, move)` per process; path overridable via
  `PYCATS_DEV_LOG_PATH` (tests point it at a tmp dir).
- **Gotchas:** the breadcrumb is the **only** signal for the silent special-B no-op (§3.1); if
  `PYCATS_DEV_LOG` is unset you get no trace. Not-yet-implemented is by design, not a bug.
- **Cross-refs:** #587.

### 6.2 Runtime-settings toggles — see §1.3
`show_status_timer_bars` (#111/#121) and `show_dev_info` (#545) live in
`pycats/runtime_settings.py`; cross-listed here as tooling flags.

**Domain finding:** `dev_log` + the two runtime flags are the invented tooling surface;
`PYCATS_UPDATE_GOLDENS` (§5.1) is the third env-gated knob. Nothing else beyond the seeds.

---

## Seed coverage (all 8 of #604's seeds)

1. StatusSource `precedence` + `bar_class` (exclusive vs overlay) → **§1.1 / §1.2**
2. Provenance status taxonomy (FOUND/GUESS/TUNED/DIVERGENCE) + drift-guard → **§2 intro**
3. Unit scaling `PX_PER_UNIT` (ratios not absolutes) → **§5.3 cross-ref + §2 intro; `config.py` `PX_PER_UNIT=5.4`**
4. Golden vs render-parity oracle → **§5.1 / §5.2 (and §5.3 screen-flow)**
5. `"attack"` legacy move-key alias → **§3.1**
6. up-B / special-recovery hook (`grants_recovery`) → **§3.3**
7. `dev_log` → **§6.1**
8. Divergences worth flagging (single fall speed, 960px-scaled knockback) → **§2a**

> Note on seed 3 (`PX_PER_UNIT`): it is a **FOUND** value (data-authoring calibration ≈5.4,
> `research-120`), not itself a divergence — the *invented convention* is "compare ratios, not
> absolutes." #604 should present it as the scaling model, not as a departure.

## Completeness gate

- [x] **Every DIVERGENCE row** (4) has an entry — §2a.
- [x] **Every TUNED row** (24) has an entry — §2b.
- [x] **All 8 seed mechanics** covered — table above.
- [x] **Each domain** ends with a found-or-"nothing beyond seeds" note — §§1–6.
- [x] Each item carries a **landmark + how-it-works line**.

**Un-swept / flagged for #604's judgment (not omissions):**
- GUESS rows (§2c) — divergence-adjacent; #604 decides whether to surface them.
- `SMASH_CHARGE_FRAMES` FOUND-but-primary-unconfirmed (§2 finding) — accuracy caveat, not a divergence.
- The domain `#672`/`#680` skin/character decomplect is **in flight** — §1.4's `char_name`
  split will move onto a `Selection`/`Skin` model; #604 should cite the current bare-string
  path and note the migration rather than freezing on a moving target.

## Refs
Parent **#604**; `pycats/combat/provenance.py` (ADR-0003, #233); `pycats/render_battle.py`
(`StatusSource`/`STATUS_SOURCES`/`active_tint`/`timer_bar_specs`); `pycats/combat/move_select.py`;
`pycats/combat/move_clock.py` (#204); `pycats/combat/data.py` (`grants_recovery`);
`pycats/charts/fighter_chart.py`; `pycats/dev_log.py` (#587); `pycats/runtime_settings.py`;
`tests/golden/REGEN_PROTOCOL.md`; `tests/test_battle_screen_render.py`;
`tests/test_screen_parity.py`; `pycats/characters/roster.py`; `docs/research-120-smash-units-and-sources.md`.
