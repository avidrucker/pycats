# Screen-flow engine — findings & statecharts-py port design (#97)

**Question (#97):** does the main menu / top-level screen flow use the sibling
`statecharts-py` engine, or a separate FSM? And if separate, design the port.

## Verdict (confirmed)

**No — the screen flow does not use statecharts-py.** It runs on a hand-rolled
guard-table FSM in `pycats/systems/fsm.py`, driven by
`ScreenStateManager` (`pycats/screen_manager.py`). The `statecharts-py` engine is
confined to two lower layers:

- **Fighter** state — `charts/fighter_chart.py` → `Session`, wrapped by
  `systems/state_engine_sc.py::StatechartEngine`, selected by
  `systems/state_engine.py::make_engine(backend)`.
- **Match** phase — `systems/match_engine.py::StatechartMatchEngine`
  (`in_play`/`match_over`), selected by `make_match_engine(players, backend)`.

So "the game runs on statecharts" is only half true: fighters and match-phase do;
**menus, screen flow, and the battle screen itself do not.**

## Current architecture (evidence)

### The screen FSM (`systems/fsm.py`, ~40 LoC)
A minimal dataclass FSM: `state: str`, dicts of `on_enter`/`on_update` callbacks,
and a `table: {state -> [Transition(to_state, guard)]}`. `update(ctx)` runs the
current state's guards (first truthy fires), then its `on_update`. No hierarchy,
no parallel regions, no entry/exit beyond a single `on_enter`.

### `ScreenStateManager` (`screen_manager.py`)
Owns four screen managers (`MainMenuManager`, `CharacterSelector`,
`WinScreenManager`, `PauseMenuManager`) and an `FSM` with five states:

```
main_menu ──play──▶ char_select ──ready──▶ playing ──P──▶ pause
                         │  ▲                   │            │ resume → playing
                    back │  │ win→reset          │ KO         │ end_match → win_screen
                         ▼  │                     ▼            │ return_to_menu → main_menu
                     main_menu              win_screen ──play_again──▶ char_select
```

Guards mostly poll `action_requested` flags the managers set (`"play"`,
`"resume"`, `"end_match"`, `"return_to_menu"`) — a manual command channel.

### The split that makes this "not a real game-state machine"
The FSM only chooses **which screen is active**. The actual work is elsewhere:

- **`playing` and `pause` have empty FSM `on_update`/render** — the battle sim
  (player updates, `resolve_player_push`, `attacks.update`, `combat.process_hits`,
  win-check) and **all** battle/pause rendering live inline in `game.py`'s
  `while running` loop as a big `if current_state == "...":` ladder (lines ~519–664).
- **Battle state is module-global** in `game.py` (`player1`, `player2`, `players`,
  `attacks`, plus `reset_game`, `create_players_from_selection`) — not owned by any
  state object.
- **Transition side-effects leak into the loop**: `game.py` keeps its own
  `previous_state` and special-cases `pause → win_screen` to wire stats (lines
  ~507–517) — logic that belongs in a state entry action.

Net: the battle/"in-game" is **not** a first-class state; it's the loop's default
branch. That's the core of what "port fully to statecharts-py" must fix.

## The template to mirror — `match_engine.py`

`StatechartMatchEngine` is the existing, working pattern for orchestration (not
fighter) state on statecharts-py, and the port should copy its shape:

```python
chart = statechart({"initial": "in_play"},
    state({"id": "in_play"},
        transition({"event": "tick",
                    "cond": lambda e, d: winner_index(self._players) != 0,
                    "target": "match_over"})),
    state({"id": "match_over"}))
self._session = Session(chart)
# phase property reads self._session.in_state("match_over")
```

Key conventions it establishes (all reused below):
- **Dual backend behind a factory**: `make_match_engine(players, backend)` returns
  `LegacyMatchEngine` or `StatechartMatchEngine` with an identical surface; same
  for fighters via `make_engine`. Selected by `PYCATS_STATE_BACKEND`.
- **Explicit `tick` event** (no eventless transitions); `cond` guards; phase
  recovered via `in_state(...)`. Same authoring API as the fighter chart
  (`statechart/state/transition/parallel/on` from `statecharts`).

## Design for the DEV ticket — port screens + battle to statecharts-py

### Target chart (hierarchical; battle is a real state with a paused substate)
```
screen_flow (compound, initial=main_menu)
├── main_menu
├── char_select
├── playing (compound, initial=active)     ← battle is now a first-class state
│   ├── active     ─ P ─▶ paused           (owns the battle sim tick)
│   └── paused     ─ resume ─▶ active       (battle frozen but still mounted)
│                  ─ end_match ─▶ ../win_screen
│                  ─ return_to_menu ─▶ ../main_menu
│        └─ (nest match in_play/match_over here, or send KO → win_screen)
├── pause  → folded into playing.paused (no longer a top-level peer)
└── win_screen
```
Making `playing` a **compound** state with `active`/`paused` children is the win
the flat FSM can't express: pause naturally *keeps the battle mounted* (frozen
background render) instead of the current loop juggling a separate `pause` branch
that reaches back into `playing`'s globals.

### Work slices (lazy decomposition — keep as one ticket; split only if a slice grows)
1. **`StatechartScreenEngine` + `make_screen_engine(backend)`** mirroring
   `match_engine`. Port the five states and their guards (the `action_requested`
   polls become `cond`s; the `on_enter` callbacks become entry actions). Keep
   `LegacyScreenEngine` = today's `systems/fsm.py` path. Default stays legacy until
   parity is proven, then flip default to statechart (as fighters/match did).
2. **Extract a `BattleScreen`/`BattleManager`** that owns `player1/2`, `players`,
   `attacks`, `reset_game`, `create_players_from_selection`, the per-frame sim, and
   the battle+pause render — so all five screens are symmetric managers the chart
   drives via entry/`tick` actions. This removes the `game.py` `if state==`
   ladder; the loop shrinks to `poll → engine.update(ctx) → engine.render(surface)
   → present`. **Heaviest slice** (it de-globalizes `game.py`); split out if it
   balloons.
3. **Move transition side-effects into entry actions** (the `pause→win_screen`
   stats wiring; winner/loser reset on `win_screen→char_select`).
4. **Retire `systems/fsm.py`** once `LegacyScreenEngine` is gone (or keep it as the
   legacy backend twin, the way `fighter_fsm.py` shadows `fighter_chart.py`).

### Test strategy (this is the gate, per repo discipline)
- **Backend-parity test** (new): drive a scripted input/event trace through both
  `LegacyScreenEngine` and `StatechartScreenEngine` and assert identical
  state-transition sequences — the screen-flow analogue of the `fighter_fsm.py` ↔
  `fighter_chart.py` parity guarantee.
- **Goldens are the oracle for slice 2.** The battle sim is golden-tested
  (`tests/test_golden.py`, `REGEN_PROTOCOL.md`). Extracting the battle into a
  manager must be **sim-behaviour-preserving**: goldens must stay green
  *without* regen. Any required regen is a red flag that the extraction changed
  the sim — investigate, don't rubber-stamp.
- Keep `PYCATS_STATE_BACKEND` (or a dedicated `PYCATS_SCREEN_BACKEND`) so the
  frozen legacy path stays runnable for A/B during migration.

### Risks / call-outs
- **De-globalizing `game.py`** (slice 2) is the real cost and risk; the chart port
  (slice 1) alone is small and low-risk. Consider landing slice 1 first behind the
  legacy default, then slice 2.
- **Display/input shell** (F10/F11/ESC, fullscreen zoom) currently lives in the
  `game.py` event loop. Decide whether it stays in the thin shell (recommended) or
  becomes a chart-level global handler — it is orthogonal to screen flow.
- Statecharts-py transitions are **event-driven**; the screen engine needs a clear
  per-frame `send("tick")` plus discrete UI events, matching how the managers
  currently raise `action_requested`.

## Recommendation

**Port is warranted and low-architectural-risk for slice 1** (the chart mirrors a
pattern already in the tree twice). It pays off by (a) making the battle a real
state instead of the loop's default branch, (b) collapsing the `game.py` ladder +
`previous_state` bookkeeping, and (c) unifying on one state engine so "the game
runs on statecharts" becomes true end-to-end. The **battle-extraction slice is the
gating effort** and should be guarded by the existing goldens.

→ Spawned DEV ticket **#100**: *feat(screens): port menus + screen flow (incl.
battle as a game state) fully to statecharts-py*, scoped by the slices above.

## Refs
#18 (scope the screen system — manager + transitions), #59 (statecharts
name-collision cleanup), `systems/match_engine.py` & `systems/state_engine*.py`
(the dual-backend templates), `tests/golden/REGEN_PROTOCOL.md` (the oracle for
slice 2). Origin: #68 wrap-up, 2026-06-25.
