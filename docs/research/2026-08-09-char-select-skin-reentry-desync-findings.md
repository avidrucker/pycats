# Char-select skin/theme on battle re-entry: the applied fighters are stale, the display is fresh

> **Agent:** DRAGONFRUIT · **Authored:** 2026-08-09 · **Ticket:** #1345

**Ticket:** #1345 (RESEARCH) · **Feeds:** a follow-up bug/DEV fix ticket (filed one-at-a-time downstream of this doc)
**As-of:** 2026-08-09 · **Anchor SHA:** `f3db9ea` (branch base = `main`)
**Scope:** findings + repro only. No fix implemented; no cross-session persistence design. See [Scope](#scope-out).

## TL;DR

The reported symptom is the visible corner of a larger defect. On the **second and later** battles of a
session, the char-select **re-selection is ignored entirely** — not just the skin display. The battle
reuses the `Player` objects built for the **first** battle, because:

1. `BattleScreen` is constructed once per app session (`App.__init__`, `pycats/shell/app.py`), and
2. `BattleScreen.reset()` (`pycats/screens/battle_screen.py`) never nulls `player1`/`player2`, and
3. `_update_playing` (`pycats/shell/screen_manager.py`) only builds fighters
   `if battle.player1 is None or battle.player2 is None`.

So the guard is never true after battle 1, `create_from_selection` is never called again, and the new
selection (character **and** skin) is dropped. Meanwhile the char-select **display** *is* reset on every
re-entry (`char_selector.reset()`), so it correctly shows the archetype default. The "skin persisted but
the screen shows default" report is exactly this divergence: **display = fresh, applied fighters = stale.**

**Confirmed bug** (headless repro below). The observed "the skin stays the same between battles" is not a
remembered preference — it is stale first-battle fighters that happen to match when the player re-picks the
same character.

## How the two halves diverge

There are two independent stores for "who is P1/P2 wearing what", and only one of them is refreshed on
re-entry.

| Store | Lives in | Reset on char-select re-entry? | Landmark |
|---|---|---|---|
| **Selection intent** (what the player picks + what the screen shows) | `CharacterSelector.p1_selected`/`p2_selected` + `p1_palette`/`p2_palette` | **Yes** — `char_selector.reset()` nulls all four | `CharacterSelector.reset`, `pycats/screens/char_select.py` |
| **Applied fighters** (what the battle actually renders/plays) | `BattleScreen.player1`/`player2` | **No** — `reset()` re-spawns the *same* objects | `BattleScreen.reset`, `pycats/screens/battle_screen.py` |

The intended bridge between them is `_update_playing` →
`battle.create_from_selection(p1_char, p2_char, p1_palette, p2_palette)`
(`ScreenStateManager._update_playing`, `pycats/shell/screen_manager.py`). That bridge fires **only** when a
player object is `None`, which is true exactly once — before the first battle.

## Questions answered

### Q1 — Where is the per-(player+character) skin persisted such that the next battle reuses it?

**Nowhere — there is no skin-preference store.** The apparent persistence is the *first battle's `Player`
objects still being alive*. `BattleScreen.player1`/`player2` are built once by `create_from_selection`
(`pycats/screens/battle_screen.py`, the `self.player1 = Player(...)` / `self.player2 = Player(...)` block),
which sets `char_color`/`stripe_color`/`character` from that selection's skin. Those attributes are never
recomputed afterward, so the next battle "reuses the prior skin" only in the sense that it is literally the
prior fighter.

### Q2 — On returning to char-select and re-selecting, what resets the displayed skin to default?

`ScreenStateManager._on_enter_char_select` (`pycats/shell/screen_manager.py`) calls
`char_selector.reset()`. `CharacterSelector.reset` (`pycats/screens/char_select.py`) nulls
`p1_selected`/`p2_selected` and `p1_palette`/`p2_palette` (the "Reset chosen skins (#650)" block). On the
next A-confirm, `_default_skin` (`CharacterSelector._default_skin`) sets the palette to the archetype
default (`ARCHETYPE_DEFAULT_SKIN`). So the display starts each re-entry at the archetype default **by
design** — the display path is correct; it is the applied-fighter path that is wrong.

### Q3 — Single source of truth, or do display and applied skin diverge?

**They diverge** (see the table above). The selection intent is rebuilt from the player's picks every
re-entry; the applied fighters are frozen at the first battle. They are *supposed* to reconcile through
`create_from_selection`, but the `player is None` guard in `_update_playing` blocks it for battle 2+.
Reconciliation should happen at the **char-select → playing** boundary: the fighters must be (re)built from
the current `CharacterSelector` selection every time a match starts, not only on the first.

### Q4 — What is the battle → char-select transition; does it carry the prior selection forward or start fresh?

The single long-lived `BattleScreen` (`App.__init__`, `pycats/shell/app.py`) is threaded into
`ScreenStateManager.update` every frame. Returning to char-select runs
`ScreenStateManager._update_char_select` (`pycats/shell/screen_manager.py`), which calls `battle.reset()`
when `winner`/`loser` are `None`. `BattleScreen.reset` is a **match-scoped** reset (full lives, cleared
stats, FSM→idle, `reset_to_spawn`) that deliberately keeps the same `Player` objects — it is also the
**rematch** path. So the battle does **not** start fresh; char-select's own state **does**
(`char_selector.reset()`). That asymmetry is the defect.

### Q5 — Reproduction

Confirmed headlessly. The repro drives the exact `_update_playing` create-guard against a single
long-lived `BattleScreen`:

```
battle 1  p1char=nalio p2char=birky p1color=(210, 55, 50)
after reset: player1 is None? False  player2 is None? False
battle 2  rebuilt=False  p1char=nalio p2char=birky p1color=(210, 55, 50)

RESULT: BUG — battle 2 kept selection A (nalio/birky); the new selection
narz/gnok was ignored because create_from_selection was skipped
(reset() left players non-None).
```

- **Expected** (battle 2): `p1char=narz`, `p2char=gnok`, and P1 color = narz's skin.
- **Observed** (battle 2): `p1char=nalio`, `p2char=birky`, P1 color `(210, 55, 50)` = nalio's `red-blue`
  default — identical to battle 1.

The `rebuilt=False` line is the mechanism: `battle.player1`/`player2` are non-`None` after `reset()`, so the
create-guard skips the rebuild. (Repro script kept in the ticket's scratch, not committed; it constructs a
`BattleScreen`, calls `create_from_selection` for selection A, `reset()`, then re-runs the
`if player is None` guard for selection B.)

## Is this a confirmed bug?

**Yes.** And its scope is wider than the report: any change on re-entry — different character, different
skin, or a skin cycled to non-default — is dropped for the 2nd+ battle. The report noticed only the skin,
because the repro path re-selected the same characters, where the stale fighters coincidentally match on
character and differ only where the player expected a cosmetic refresh.

## Two distinct pieces of work fall out (hand off one-at-a-time)

The user's stated expectation — *"the char-select screen should show the active/current/selected skin, and
that skin should stay the same between battles for a given selection"* — needs **both** of these, and they
are separable:

1. **Bug fix (this defect): rebuild fighters from the current selection at every match start.** Make the
   char-select → playing transition (re)build `player1`/`player2` from the live `CharacterSelector`
   selection each time, not only when they are `None`. After this fix alone, the battle matches whatever
   char-select **displays** — which, today, is the archetype default after re-entry. This makes display and
   applied skin *consistent*; it does **not** by itself restore a previously-cycled non-default skin.

2. **Enhancement (delivers the "stays the same" half): remember each (player+character) skin choice for the
   session and restore it into the char-select display on re-entry.** Only this makes re-entry *show* the
   prior non-default skin (instead of the archetype default), which — combined with fix #1 — makes the next
   battle apply it too. This is a session-scoped preference store, out of scope for the bug fix.

Filing order: the **bug fix first** (it is the broken promise — the selection is ignored), then the
enhancement as a separate ticket downstream if the user wants the remembered-skin behavior.

## Minimal fix seam(s) — for the follow-up DEV/bug ticket

Two candidate seams for piece #1; the researcher recommends the first. DEV decides.

- **Recommended — rebuild once per match start, at the state boundary.** Have the char-select → playing
  transition build fighters from the current selection exactly once (e.g. a `playing` `on_enter` action, or
  a "selection dirty" flag set when leaving char-select that `_update_playing` consumes). This keeps
  `BattleScreen.reset()` untouched, so the **rematch** semantics (same fighters, fresh stocks) stay intact,
  and cleanly separates "new match from a new selection" from "rematch the same fighters".

- **Alternative — a dedicated return-to-char-select reset that nulls the players.** Add a method distinct
  from `reset()` that sets `player1 = player2 = None` when leaving a match for char-select, letting the
  existing lazy `is None` guard rebuild. Do **not** simply null inside `reset()` — that path is shared with
  rematch, and nulling there would discard fighters a rematch is meant to keep.

**Test hook (able-to-fail):** at the `ScreenStateManager` seam — after a first battle built from selection
A and a return-to-char-select (`battle.reset()`), a second selection B must produce `battle.player1`/
`player2` whose `character`/`char_color` reflect **B**. The repro's guard logic is the test skeleton; the
test must fail on today's code (it rebuilds A) and pass once the seam rebuilds from the live selection.

## Landmarks (SHA `f3db9ea`)

- `BattleScreen.__init__`, `BattleScreen.create_from_selection`, `BattleScreen.reset` — `pycats/screens/battle_screen.py`
- `ScreenStateManager._update_playing`, `._update_char_select`, `._on_enter_char_select` — `pycats/shell/screen_manager.py`
- `CharacterSelector.reset`, `._default_skin`, `.get_selected_palettes`, `.get_selected_characters` — `pycats/screens/char_select.py`
- `App.__init__` (single long-lived `BattleScreen`) — `pycats/shell/app.py`

## Scope (out)

- **No code fix** — this doc is repro + findings only; the fix lands in a follow-up bug/DEV ticket.
- **No cross-session persistence** — session-scoped only is the expected behavior; nothing here saves a
  skin choice across a full game quit.
- **No AI/CPU or netplay interaction** — unrelated to the CPU-in-live-game work (#1338/#1341/#1342).
