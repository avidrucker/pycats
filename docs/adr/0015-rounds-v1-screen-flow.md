# ADR-0015 — ROUNDS v1 screen-flow: menu entry, dedicated point-loop states, draft-inline results

## Status

Accepted — 2026-08-02. Resolves the **ROUNDS Mode v1 wayfinder map** (#1096) decision
#1120 ("screen-flow — ROUNDS-specific menu screen? + between-round/match interaction
design"). Coupled to the format-params ruling **#1098** and the draft screen **#1103**;
routes through **ADR-0014**'s per-round recompute boundary. Epic #347.

This ADR picks the **approach + screen sequence** (an architecture decision), not the
pixel-level layout — detailed screen visuals are downstream.

## Context

The connective screen tissue around the ROUNDS card-draft loop was unspecified. Grounding
facts, read from source 2026-08-02:

- **The screen FSM is a flat string-ID statechart**, defined as the `transitions` dict in
  `pycats/shell/screen_manager.py` : `ScreenStateManager`. Its states are `main_menu`,
  `options`, `char_select`, `playing`, `pause`, `win_screen`. There is **no game-mode
  concept, no stage-select, and no best-of/rounds notion** anywhere in the live path.
- **The flow today:** `main_menu` →(the `"play"` action, `MainMenuManager._ACTIONS`)→
  `char_select` → (the first `playing` frame lazily builds the match via
  `BattleScreen.create_from_selection`, invoked from `ScreenStateManager._update_playing`)
  → `playing` → (win detected by `systems/win_condition.py::winner_loser`) → `win_screen`
  → (both players confirm) → back to `char_select` (an **implicit rematch**; the battle
  resets when winner/loser are cleared).
- **`win_screen` is terminal and shared:** its only exit is `_guard_win_screen_to_char_select`,
  and it is reused by the pause "End Match" path (`from_pause=True`). There is **no
  `win_screen → playing` edge** — nothing loops back into a match.
- **No match-config object is threaded** menu→battle. `create_from_selection` takes only
  selected character keys + palettes; there is nowhere to carry a "mode" or a running score.
- **`build_fighter` (`pycats/loadout/build_fighter.py`) is the clean per-match construction
  seam** both the headless sim and live game call; `create_from_selection` invokes it once
  per match today.
- **`ScreenStateManager` is a god object** (holds every sub-screen manager, the whole
  transition table, all guards, the ESC-hold timer, and winner/loser match state), and
  **render dispatch is duplicated** across `ScreenStateManager.render` and
  `pycats/shell/screen_render.py::render_active_screen` (a documented past-bug: a screen
  wired to update but not drawn).

The ROUNDS loop this must wrap (per #1098 + the mechanics findings §2/§8): a **match** is
scored in **points**; a **point** is a base-1-stock duel; the **point-loser drafts** 1 of 5;
**both** draft a starting card at match start; **first-to-5** points wins. HP + spawn reset
between points (findings §2.2), so "next point" is a clean rebuild.

## Decision

### 1. Mode entry — a menu item, not a new screen (D1)

The main menu gains a **"Rounds"** entry; the existing **"Play" is renamed "3-Stock"**.
Selecting one sets a **mode flag** carried into a new **match-config carrier** threaded
`main_menu → char_select → create_from_selection` (which today carries only char keys +
palettes). No new FSM state is added for mode selection.

Rejected: a dedicated mode-select screen (adds a whole new state to the god object, which the
v1 slice does not need — deferred as the eventual "proper" home) and a config/launch-flag-only
toggle (not player-selectable in-game, undercutting the map's *playable-slice* destination).

### 2. The point-loop — dedicated ROUNDS between-point states (D2)

The point-loop lives in **dedicated ROUNDS-scoped FSM states**, not by overloading the
terminal `win_screen` with a score-conditional loopback. This keeps two lifecycles apart —
*"point ended → draft → next point"* vs *"match ended → final results → exit"* — instead of
making one shared screen mean both via hidden score state. It also hosts the `draft` state
that #1103 already introduces.

Rejected: reusing `win_screen` + a new `win_screen → playing` loopback (conflates point-loop
and match-end on the pause-shared terminal screen); a nested/hierarchical sub-statechart
(introduces FSM hierarchy the flat string-FSM has never had — over-built for v1, and leans on
unvalidated `statecharts-py` nesting).

### 3. The sequence — draft-inline results, per-round rebuild (D3)

```
char_select ──(mode=Rounds)──▶ starting draft (BOTH pick 1 card)      ← #1098 rubber-band
                                        │
                                        ▼
                    playing (a POINT = base 1-stock duel)
                                        │  a player loses all stocks
                                        ▼
                    draft (LOSER picks 1 of 5; winner waits)           ← #1103's screen
                          · pip-score shown INLINE (no separate results state)
                                        │  both ready-up
                                        ▼
        rebuild via create_from_selection / build_fighter             ← ADR-0014 recompute
                                        │
                        ┌──── point-target hit? ────┐
                        │ no                         │ yes
                        ▼                            ▼
                   next point               win_screen (final) ──▶ char_select
```

Point-results are **folded into the draft screen** (the pip-score shows inline on #1103's
screen) — no standalone point-results state in v1. The **starting-draft for both players**
rides on the #1098 ruling. Match-end reuses the existing terminal `win_screen` → `char_select`.

The per-point rebuild re-invokes the `create_from_selection` / `build_fighter` seam — which
is exactly **ADR-0014**'s once-per-round recompute-from-baseline boundary — so the load-time
card apply and the point-reset share one seam. (Today that seam runs once per match, gated by
`battle.player1 is None` in `_update_playing`; ROUNDS makes it run once per point on each
`playing` re-entry.)

Rejected: a standalone point-results beat (deferred post-v1, #1146).

### 4. Card management — no delete step in v1 (D4)

The v1 flow is **draft-pick only**; there is **no card-delete/management step**. Base ROUNDS
does allow deleting card buffs/debuffs (per the designer), and **ADR-0014**'s
recompute-from-baseline is the enabling architecture — a deleted card just drops from the
`list[Card]` and effective stats recompute from the immutable baseline. That capability stays
**latent** in v1; the player-facing delete flow is deferred post-v1 (#1143).

> Note: the mechanics findings doc `2026-08-02-rounds-game-mechanics-findings.md` §3 currently
> states picks are permanent ("you cannot remove or swap a card once taken"), which contradicts
> both the designer and ADR-0014's premise. Reconciling/correcting that doc is filed as #1144
> — this ADR does not edit the findings doc.

## Consequences

- **A match-config carrier is now required** (§1) — a new object threaded menu→battle to carry
  the mode flag (and, for ROUNDS, the running pip-score / point-target). `create_from_selection`
  gains a parameter beyond char keys + palettes. This is v1 build scope (a downstream #347 child).
- **`create_from_selection` must become re-entrant per point** (§3) — the once-per-match
  `player1 is None` gate becomes a once-per-point rebuild on each `playing` entry, feeding the
  ADR-0014 recompute. Build scope.
- **The god object deepens before it's split** — v1 adds the between-point states + score
  tracking onto `ScreenStateManager`. Extracting a ROUNDS point-loop sub-controller is deferred
  post-v1 (#1145). Any new state must add **both** render branches
  (`ScreenStateManager.render` + `screen_render.py`) to avoid the documented not-drawn bug.
- **Follow-ups filed** (post-v1 unless noted): card-delete/management flow (#1143), findings §3
  reconciliation (#1144, research), ROUNDS sub-controller refactor (#1145), standalone
  point-results beat (#1146).

## References

- Map #1096 (ROUNDS Mode v1 wayfinder map) · epic #347.
- #1120 (this decision) · #1098 (format params) · #1103 (draft screen).
- ADR-0014 (modifier apply-layer / per-round recompute) · ADR-0013 (fighter-seam modifier
  contract) · ADR-0002 (FSM → statecharts migration precedent).
- `docs/research/2026-08-02-rounds-game-mechanics-findings.md` §2 (core loop), §8 (wiki
  reconciliation).
- Source: `pycats/shell/screen_manager.py` (`ScreenStateManager`), `pycats/shell/screen_render.py`
  (`render_active_screen`), `pycats/screens/battle_screen.py` (`create_from_selection`),
  `pycats/loadout/build_fighter.py` (`build_fighter`), `pycats/systems/win_condition.py`.
