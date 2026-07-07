# TIL — 2026-07-06 (DRAGONFRUIT, session 3)

A char-select feature, a discoverability research doc, and a full file→groom→build
cycle for a hints system — the throughline was *confirm intent and reuse what exists
before writing new code or new specs*.

Tickets: **#662** (recolor preview cat to cycled skin), **#549** (research: hold-to-act
hint discoverability), **#681** (per-screen hints + two toggles — filed, groomed via a
clarification, then implemented). Error logged: **#127**.

---

## 1. Reuse an existing override param instead of adding a new code path (#662)

`_draw_cat_preview` already accepted a `palette_key` override (added in #650) — the grid
tiles and `_draw_confirmation` simply never passed it, so only a flat swatch was recolored.
The whole fix was *passing the param that already existed* into a per-player preview cat,
plus a `_confirmation_preview_pos` helper that offsets P1 left / P2 right of the tile centre
— which resolved the two-players-same-character overlap #650 had explicitly deferred. No new
render path, no new abstraction.

**Lesson:** before building a new draw path, check whether the seam is already there. A
deferred sub-problem ("same character → shared tile can't show two skins") often just needs
the existing override wired through with a positioning tweak.

## 2. A discoverability audit is per-screen verdicts with `file :: symbol` citations — and its follow-ups are *proposed, not filed* (#549)

The question was "is each hold-to-act findable *before* the hold?" The answer isn't one
verdict — it's one per screen: hold-B on `char_select` **is** discoverable (`screen_render.py
:: render_active_screen` draws "Hold B for 1 second…"), hold-ESC is **not** on any screen it's
used on (only progress-drawn mid-hold, word-documented in one Options row). Each verdict
carried its citing symbol so a reader can act without re-deriving. The findings doc
*recommended* two `enhancement`s and a possible `decision:` but **filed none** — the ticket's
out-of-scope said "propose follow-ups, do not file them here."

**Lesson:** a "not discoverable" finding that names no alternative is incomplete — every
screen also got "…but the action is reachable via <the Quit button / the pause menu>," which
is what downgraded it from a bug to a hint-gap. Cite the symbol; leave the filing to a
go-ahead.

## 3. When a user instruction self-contradicts, confirm the fork — don't encode the contradiction (#681)

The human set "OG toggle = battle, NEW = non-battle" (point 1), then said "by the above
logic, show ESC-hold intent in non-battle when the **OG** toggle is on, and during battle when
the **NEW** toggle is on" — which *inverts* point 1 for the ESC-hold. "By the above logic"
signalled they believed it consistent, but the literal text wasn't. Rather than guess a
reading (and bake a contradictory spec into a ticket a future agent implements), I put both
mappings up via `AskUserQuestion` with a preview of each. The human picked "follow its own
screen" and re-typed point 2 corrected.

**Lesson:** a self-contradicting instruction is a *fork*, not a typo to silently fix or a
literal to blindly encode — both are wrong. Surface the two readings; the cost of one round-
trip is far below a wrong-wired feature discovered in code review.

## 4. The env-at-import footgun recurred *despite* an existing memory note (#127)

Writing `os.environ["PYCATS_NO_PERSIST"] = "1"` at a test module's top level leaked into the
whole pytest process and broke ~7 unrelated settings / round-trip tests (`test_settings.py`,
`test_show_controls_toggle.py`) — a green→17-red swing. There is already a memory note about
this exact pattern, and it still happened, because a module-scope side effect is *invisible at
the point where it bites*: the failing tests are in other files. Fix: per-test
`monkeypatch.setenv(...)` in an autouse fixture (auto-undone).

**Lesson:** a known-footgun note doesn't fire if the smell isn't visible where you type. The
durable guard is mechanical, not memory: **never** mutate `os.environ` (or any global) at test
module scope — reach for `monkeypatch` reflexively. When a full-suite run swings from green to
many reds across files you didn't touch, suspect session pollution first.

## 5. Test the toggle *mapping*, not just presence — and keep byte-parity oracles mirroring their function (#681)

Two things the naive test would miss. (a) Asserting "the hint shows when the toggle is ON"
proves presence but not *wiring*: the able-to-fail test instead proves the **battle** ESC-hold
hint stays visible when the **non-battle** toggle is off (and vanishes when the battle toggle
is off) — that's the only assertion that catches a swapped-wire regression, which the
revert-check confirmed by failing exactly when I crossed the wires. (b) Adding a line to
`draw_shell_chrome` broke `test_shell_chrome`, a *byte-parity oracle* whose `_expected()` hand-
mirrors the function; the correct fix is to add the same gated line to the oracle (so it stays
a faithful mirror), not to weaken the assertion.

**Lesson:** for a routing/gating feature, the test that earns its keep asserts the *mapping's
distinctness*, not each output's existence. And a parity oracle is a mirror — when the function
grows, the oracle grows identically or it's testing the wrong thing.

---

## What I did

- **#662** — recolored per-player preview cat via the existing `palette_key` override +
  `_confirmation_preview_pos` offset; pixel-sampling regression test, revert-checked. Closed.
- **#549** — per-screen hold-to-act discoverability audit →
  `docs/research/2026-07-06-hold-to-act-hint-discoverability-findings.md`; verdicts + citations,
  follow-ups proposed not filed. Closed.
- **#681** — filed the hints `enhancement` (dup-checked the queue first), groomed it twice: once
  to record the human's two-toggle decision, once after the `AskUserQuestion` clarification;
  then implemented it (two toggles across 9 modules + 8 tests, incl. the mapping test) and
  closed. Full suite 1271→(main now 1286) green.
- Logged error **#127** (env-at-import pollution).

## Open threads (not filed — flagged for a go-ahead)

- The **#549 recommended follow-ups** are now *implemented* by #681 (the playing ESC-hold hint
  + main_menu quit hint landed as part of the per-screen layer), so they need no separate
  ticket — worth a note on #549 if anyone hunts for them.
- The **ESC-hold-intent** question from #549 (discoverable feature vs deliberate hidden safety
  gesture) was mooted by the human's decision to surface it; if that's ever revisited, it's a
  `decision:` not a code change.

## Related artifacts

- Findings doc: `docs/research/2026-07-06-hold-to-act-hint-discoverability-findings.md`
- Code: `pycats/{settings,runtime_settings,options_menu,main_menu,char_select,screen_render,win_screen,pause_menu,render_battle}.py`
- Tests: `tests/test_screen_hints_toggle.py`, `tests/test_char_select_skin_preview.py`, updated `tests/test_shell_chrome.py`
- Prior sessions today: [[today-i-learned-2026-07-06-dragonfruit]], [[today-i-learned-2026-07-06-dragonfruit-2]]
