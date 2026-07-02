# TIL 2026-07-01 — CHERRY

**Context:** A long screens-lane session on the Options/menu polish family: chase a
reported "freeze" opening Options (#386), add a 2-column grid + centered labels
(#389), add font-scale coverage tests that surfaced a cache bug (#399/#401), make the
menu layout scale and scroll (#402), groom three tickets to 15/15 (#414), roll the
button widget into the other menus (#360→#416), and add focused-option captions
(#390).

---

## 1. The "freeze" was a screen that never repainted — not a hang

**What happened:** Opening Options looked like a hard freeze — the main menu stayed
on screen and Options never appeared. I burned time on font/render-perf/audio
hypotheses and a faulthandler capture that pointed (misleadingly) at `render_text_mixed`.
The actual cause (#386): `game.py`'s main-loop render dispatch had branches for
`main_menu`/`char_select`/`playing`/`pause`/`win_screen` and **no `options` case** —
so `present_frame()` just re-flipped the stale main-menu buffer. The loop ran fine at
60fps the whole time; only the screen was frozen.

**What I learned:** Every headless repro missed it because the tests call
`ScreenStateManager.render()` **directly**, bypassing `game.py`'s loop dispatch — the
one layer that was actually broken. That loop is module-level code with no
`if __name__ == "__main__"` guard, so no test can import it; it had zero coverage.
"Freeze" also anchored me on a hang when the symptom was "no repaint."

**The rule:** **A frozen screen with a live process is a missing render, not a hang —
and untestable module-level loop code is a coverage blind spot; extract its dispatch
into an importable function so it can be tested.** (Anchored: `screen_render.py` +
`tests/test_game_render_dispatch.py`, and the `game-loop-untestable-dispatch-blindspot`
memory.)

---

## 2. A cache key that omits an input silently serves stale output

**What happened:** #399's font-scale coverage tests (render each menu at
small/standard/large, assert every text field's height tracks the scalar) went red on
the mixed-font fields: button labels and instructions were frozen at their
first-rendered size while the title resized. Root cause (#401): `_compose_mixed`
cached composed surfaces by `(text, authored_size, colour)` — the fonts were resolved
through the live `font_scale`, but the **key wasn't**. First scale to compose a string
won; later scales got the stale surface.

**What I learned:** `render_text_simple` (no cache) and `sys_font` (keyed by the
scaled size) both resized correctly — which is exactly why only *some* fields scaled
and the bug hid in plain sight. The tests only caught it because I rendered
standard-then-large through the *same* renderer, reproducing the live-change path.

**The rule:** **A memoization key must include every input that changes the output —
here the scale factor, not just the authored size.** (Anchored: fix + regression in
`text_utils._compose_mixed`, #401.)

---

## 3. When the content can't fit, that's a product decision — ask, don't guess

**What happened:** For #402 I measured that at Large (2×) the 9 Options rows can't fit
one 960×540 screen under any column count (buttons too wide for 2 columns, too tall
for 1). There was no clean default — the honest options were scroll, page, or cap the
menu scale. I stopped and used AskUserQuestion; the user chose scrolling.

**What I learned:** I built it on a small **pure** layout module (`menu_layout.py`:
`effective_columns` / `grid_dims` / `scroll_to_visible`) unit-tested with no display,
then wired the pygame render to it. The genuinely hard logic (scroll-to-selected,
column-fit) became trivially testable once separated from rendering.

**The rule:** **A "can't fit / can't satisfy all constraints" fork is the user's call,
not a silent default — surface it; and extract the integer layout math into a pure,
display-free module so the hard part is unit-tested.** (Anchored: #402, `menu_layout.py`
+ `tests/test_menu_layout.py`.)

---

## 4. Don't force a widget onto a screen it doesn't fit — split it

**What happened:** #360 said "adopt the menu-button widget in main_menu / char_select
/ pause_menu." main_menu and pause_menu are single-column option lists — a clean swap.
But `char_select` is a **2D character grid with two independent player cursors** (thick
coloured borders + P1/P2 labels): no vertical option list, no single "focused row," and
its focus is already *not* colour-only. The single-focused-row widget doesn't map onto
it. I shipped the two that fit and split char_select to #416 (a decision ticket) rather
than shoehorn it.

**What I learned:** The groomed ticket had already anticipated this with a
"split-if-structurally-distinct" clause — which made the call easy and legitimate
instead of a silent scope drop.

**The rule:** **If the abstraction doesn't fit the screen, split that screen to its own
ticket — a wrong-fit adoption is worse than none.** (Anchored: #360 shipped
main_menu+pause_menu; char_select → #416.)

---

## 5. A 15/15 ticket carries decisions, not "resolve in design"

**What happened:** An issue-review pass scored #390/#391/#360 at 12–14/15, dinged
mostly for open "decide during design" questions. I convened the Council of Yegors
(`yegor-personas`) on how to reach 15/15. It converged with no dissent: the fix isn't
more analysis, it's **freezing** each open question into a written decision + filling
the objective rubric gaps (name the test, name the file). `microtasks` (≤60m) killed a
proposed split; `spikes` said the questions were decidable, not unknown; the reporter
(rung 4) owns the frozen product calls. I groomed all three via #414.

**What I learned:** "Open question with a proposed default" still reads as *not ready*
to an agent picking up the ticket — it would stop and ask. Freezing the default (and
recording why the alternative was rejected) is what makes a ticket startable.

**The rule:** **An issue is ready when an agent can start with zero follow-up questions
— so freeze every open decision into the body before handing it off.** (Anchored: #414
groomed #360/#390/#391.)

---

## 6. Derive test expectations from live state, not hardcoded counts

**What happened:** Twice, a concurrent fleet merge broke my tests: the #345 `font_scale`
row landed mid-task (8 Options rows → 9), and my grid-nav tests hardcoded the 8-row
sequence `(2,4,6,0)`. I rewrote them to compute the expected column-0 down-sequence
from `NCOLS` and `len(rows)`, so adding a row can't break them again.

**What I learned:** In fleet mode `origin/main` moves under you constantly — I merged it
mid-task on almost every ticket, and a hardcoded structural fact is a time bomb.

**The rule:** **Derive test expectations from the code's live structure (row count,
column count), never a hardcoded snapshot — and merge `origin/main` early and often.**
(Anchored: `tests/test_options_grid.py`, and the `fleet-merge-race-run-suite-early`
memory.)

---

## What landed

| Ticket | Change |
|---|---|
| #386 | Fix Options never rendering — extract `game.py` loop dispatch to testable `screen_render.render_active_screen` |
| #389 | Options: 2-column grid + vertically-centered button labels |
| #399 | Menu font-scale coverage tests (assertion-based, not byte goldens) |
| #401 | Fix mixed-text cache keyed by authored (not scaled) size — font-scale now resizes menu text |
| #402 | Scale-aware menu geometry + scroll-to-selected Options list (pure `menu_layout` module) |
| #414 | Groomed #360/#390/#391 to 15/15 (Council-of-Yegors convergence) |
| #360 | Rolled the menu-button widget into main_menu + pause_menu |
| #390 | Focused-option captions with a reserved no-overlap caption band |

## Open threads

- **#416** — decide whether/how char_select's grid cursors get consistency treatment.
- **#391** — colour buttons by ON/OFF state (last polish-trio item; solo it — touches
  `options_menu.render` + `draw_menu_button`).
- **#361** — menu activation feedback (press-pop / invalid cue).
- Captions (#390) are Options-only; a fast-follow for the other menus isn't filed yet.
- Lessons 1, 2, and 6 are anchored in code + auto-memory; if any recurs across agents,
  promote it to `RULES.md`/`CLAUDE.md` (authority path).

## Related artifacts

- Issues #386, #389, #399, #401, #402, #414, #360, #390, #416
