# Match-mode settings + UX — findings

- **Ticket:** #819 (RESEARCH child of epic #818) · closing artifact for that thread.
- **Scope:** what basic settings each match mode (Timed / Stock / Rounds) needs, sensible
  defaults, and a simple, keyboard-friendly mode-select flow that matches pycats' existing
  screen house-style. Convenience/UX-first — **not** a feature-parity study.
- **Method:** read the live screen layer (`main_menu`, `options_menu`, `screen_manager`,
  `menu_widgets`, `char_select`), the win-condition rule (`win_condition.py`), the config
  defaults (`config.py`, `settings.py`), and cross-checked the PM menus prior-art doc
  (`docs/pm-reference/menus-and-game-flow.md`, #172). No code changed.

---

## TL;DR / recommendations

| Decision | Recommendation | One-line rationale |
|---|---|---|
| Default mode | **Stock** | It is the only behavior today; last-one-standing is the least-surprising default and avoids a regression. |
| Stock — lives options | `1, 2, 3, 4, 5`, default **3** | 3 preserves today's `INITIAL_LIVES = 3`; the range brackets it symmetrically. |
| Timed — duration options | `1, 2, 3, 5` minutes, default **2 min** | UX default (game-feel is allowed for a UX default): a short arcade match for a fast 2-cat fight. |
| Timed — tie-break | most lives left → lower damage % → **Sudden Death** | Reuses `.lives` + `.percent` already tracked; deterministic; only the final tie needs new machinery. |
| Rounds tile | present but **disabled** (greyed, non-focusable), reads `Rounds (soon)` | Advertises the planned mode (#347) without implying it works. |
| Flow placement | new **`mode_select`** state **between `main_menu` (Play) and `char_select`** | "Pick how you win" is a match-level choice, above the per-player character choice. |
| Presentation | one **mode row** (Stock / Timed / Rounds) + the selected mode's **one dependent setting** below it, both as value-cycler rows | Matches the existing `draw_menu_button` + focused-caption idiom; nothing new to learn. |
| Persistence | persist last-used mode + per-mode values as the next defaults | Consistent with pycats' ratified move toward a consolidated, persisted settings model (#122). |

---

## 1. Per-mode settings

### Stock (implemented behavior today)
- **Setting:** number of lives. **Options `1,2,3,4,5`, default `3`.**
- Today `pycats/config.py :: INITIAL_LIVES = 3` is a module constant and
  `pycats/systems/win_condition.py :: winner_index` decides the winner purely by
  `.lives` (last fighter with `lives > 0` wins; same-frame double-out resolves to
  player 2). A stock selector simply makes that constant a per-match choice — **no new
  win rule needed**, just a chosen starting-lives value fed to fighter creation.

### Timed
- **Setting:** match duration. **Presets `1, 2, 3, 5` min, default `2 min`.**
- A timed match also needs an **end-of-clock tie-break**, because "the clock hit zero"
  is not itself a winner. Recommended deterministic ladder, friendliest-first:
  1. **Most lives remaining** wins (reuses `.lives`).
  2. Tie on lives → **lower damage taken** (`.percent`) wins (reuses `.percent`).
  3. Still tied → **Sudden Death**: a short 1-life overtime, first KO wins.
- **Why this shape:** it reuses state the sim already tracks and only introduces genuinely
  new machinery (an overtime) for the rare exact tie. It parallels the deterministic
  cap-time tiebreak that the sim-duration findings (#708,
  `docs/research/2026-07-20-sim-duration-and-termination-findings.md`) said #684 will need —
  same ordering principle (lives desc → percent asc → fixed fallback), so the human-facing
  timed rule and the headless sim rule can share one helper.
- **Alternative (PM-authentic, more machinery):** "most KOs in the time limit" with
  infinite lives and a falls counter (`menus-and-game-flow.md` §Match/ruleset settings:
  *time = highest KO count*). pycats does not count falls-dealt today, so this needs a new
  scored counter. Recorded as prior art, **not** recommended for the first build.

### Rounds
- **Disabled for now** (→ #347, post-V1). The screen must only show a **greyed, non-focusable
  tile** labelled e.g. `Rounds (soon)`. No settings, no navigation into it. See §4 for the
  disabled-tile treatment.

---

## 2. Defaults (with rationale)

- **Mode = Stock.** Only implemented behavior; picking it changes nothing about how a match
  plays today, so the screen is additive, not a behavior change.
- **Stock lives = 3.** Equals the current `INITIAL_LIVES`; anyone who never opens the screen
  keeps today's match.
- **Timed duration = 2 min.** A UX/game-feel default (explicitly allowed for a *convenience*
  default; any *balance/tuning* number would still need the RULES basis — none here).
- **Timed tie-break = lives → percent → Sudden Death.** Deterministic and reuses existing
  state; no bare tuning numbers involved.

These per-mode values should **persist** (last-used becomes next default), matching the
consolidated-persisted-settings direction pycats already ratified as its divergence from PM's
ephemeral per-match model (`options_menu.py` docstring; #121/#122).

---

## 3. Flow & placement

Today's screen FSM (`pycats/screen_manager.py`, statecharts-py engine):

```
main_menu ──Play──► char_select ──both ready──► playing ──► win_screen ──► char_select
   └──Options──► options ──B──► main_menu
```

**Recommendation: insert a new `mode_select` state between `main_menu` and `char_select`:**

```
main_menu ──Play──► mode_select ──confirm──► char_select ──► playing ──► ...
                        └──B / back──► main_menu
```

- **Why here (not after char_select):** the mode is a *match-level* rule ("how do you win?"),
  logically above the *per-player* character pick. Choosing it first also lets char-select
  stay unchanged.
- **Navigation (keyboard-only, house convention** — `options_menu` docstring, research #115):
  - **Up/Down** move between rows (mode row ↔ the selected mode's setting row).
  - **Left/Right** cycle the focused row's value (mirrors how `font_scale`/`window_scale`
    cycle in `options_menu`; here left/right is the natural value stepper).
  - **A / attack** confirms and advances to char_select.
  - **B / special** backs out to main_menu; the 2 s hold-ESC already pops one level via the
    shared `EscHoldTimer`, so `mode_select` gets that for free.
- **Return path:** backing out of char_select could return to `mode_select` (natural) or
  straight to `main_menu` (today's target). Either is fine; returning to `mode_select` is the
  more consistent "one level up." (Left as a DEV/UX call, not blocking.)

## 4. Presentation

A **two-row selector**, mirroring the `main_menu` / `options_menu` look
(`draw_menu_button` glowing-focus rect + redundant `►` marker, focused-row caption band,
bottom hint lines gated by `show_screen_hints`):

```
                     Match Mode

        ◄  Stock  ►            ← mode row (Left/Right cycles Stock ▸ Timed ▸ Rounds)
        Lives:  ◄ 3 ►          ← dependent setting for the selected mode

     "Most lives left wins."   ← focused-row caption (per-mode one-liner)

   Left/Right: change   A: start   B: back   (hint line, if screen hints on)
```

- The **dependent setting row swaps with the mode**: `Stock → Lives: ◄ 3 ►`,
  `Timed → Time: ◄ 2:00 ►`, `Rounds → (no setting; tile disabled)`.
- **Disabled Rounds tile:** when the mode cycler lands on Rounds it should read
  `Rounds (soon)` in a dimmed style and offer no setting row + no confirm. `draw_menu_button`
  has **no `disabled` state today** (only focused / pressed) — a small widget extension
  (a greyed fill + suppressed focus) is the cleanest home for this. Alternatively the cycler
  simply skips Rounds until #347 lands, but showing it disabled is what the epic asks for.
- Keep it to these two rows: one visible dependent setting per mode is enough for
  "easy, simple, user-friendly." Resist a full ruleset matrix (items/handicap/team) — out of
  scope and against the convenience framing.

---

## 5. Wiring touchpoints (survey only — no code changed)

A later DEV (the #820 child) would touch:

- **Screen layer (`area:screens`):** a new `ModeSelect` manager module (pattern-match
  `main_menu.py` / `options_menu.py`: `update(pressed)` / `render(surface)` / `reset()`,
  nav cooldown, press-pulse, `action_requested`), plus registration in
  `pycats/screen_manager.py` — a new `mode_select` state with its transitions
  (`main_menu → mode_select → char_select`), an `on_enter`/`on_update`, and a `render`
  branch. Store the chosen `(mode, value)` on the manager for `create_from_selection` to read.
- **`pycats/menu_widgets.py`:** add a **disabled** variant to `draw_menu_button`
  (greyed fill, non-focusable) for the Rounds tile.
- **`pycats/config.py`:** promote `INITIAL_LIVES` to a *default* plus the option lists /
  duration presets (e.g. `STOCK_OPTIONS`, `TIMED_DURATIONS`, default-mode constant); keep the
  current value as the default so headless/tests are unaffected.
- **`pycats/settings.py`:** add persisted keys for last-used mode + per-mode values (extend
  `_DEFAULTS` and `_validated`, same shape as the existing toggles).
- **`pycats/systems/win_condition.py`:** add a **timed win rule** alongside the stock
  `winner_index` — a duration-elapsed check that ranks by lives → percent → Sudden Death.
  `winner_index` stays the stock rule; the engine picks the rule by mode. (Timed also needs a
  match clock somewhere in the battle/sim loop — a frame countdown from `duration × FPS`.)

Named only; none changed here.

---

## Out of scope (unchanged from the ticket)

- Building the screen or editing any config / win-condition code — that is the #820 DEV child.
- Rounds-mode mechanics (card draft, round structure) — #347, post-V1.
- CPU / stage / profile match setup — #231 / #661 / #438.

## References

- Screen house-style: `pycats/main_menu.py`, `pycats/options_menu.py`,
  `pycats/screen_manager.py`, `pycats/menu_widgets.py`, `pycats/char_select.py`.
- Current win rule + defaults: `pycats/systems/win_condition.py`,
  `pycats/config.py` (`INITIAL_LIVES = 3`, `FPS = 60`), `pycats/settings.py` (`_DEFAULTS`).
- PM prior art (vocabulary only, not a parity mandate): `docs/pm-reference/menus-and-game-flow.md`
  §Match/ruleset settings; `docs/research/project-m-menu-architecture.md` (#115).
- Deterministic-termination sibling: `docs/research/2026-07-20-sim-duration-and-termination-findings.md` (#708),
  whose cap-time tiebreak ladder the timed win rule can share.
