# pycats-editor — simple BDD options over the existing pytest suite (findings)

**Ticket:** #1122 (RESEARCH, child of #792 editor tracker) · **Status:** findings + option space, **no decision, no code, no dependency installed**.
**Scope:** survey simple/no-nonsense BDD approaches for a solo, headless `pygame-ce` + `pytest` project that already has ~329 test functions across 38 files, and recommend a **coexistence model** — the pick is a downstream human-gated ARC ticket, not this doc.

Evidence tiers used below: **[IN-REPO]** = read directly from `avidrucker/pycats-editor` @ `5ec879c` (2026-08-02); **[EXTERNAL]** = general knowledge of the named tool (pytest-bdd / behave), labelled as such, not verified against a live install here.

---

## TL;DR

The editor **already has a de-facto BDD driver** and doesn't know it. `main(character, move_key, run_frames=N, …)` is documented in-source as "the headless test seam": a test monkeypatches `pygame.event.get` to feed synthetic event lists (the *given/when*), runs N frames, then asserts on `WorkingMove` / `selected` / stdout / a `_draw_*` recorder (the *then*). **22 of 38 files** drive tests this way; **16 files each re-implement the same event-injection helper** (`_frames` / `_run_with_keys` / `queued = iter(events)`), and canvas coordinates are re-hardcoded per file (`_CANVAS_PT = (700, 300)` appears verbatim in ≥2). So the missing thing is **a shared given/when/then vocabulary**, not a scenario capability and not a runner.

That fact reshapes the options: the cheapest, best-fitting approaches (plain-pytest discipline; a thin hand-rolled `Scenario` helper) **extract what the suite is already doing**, need **zero new dependency**, and leave all 329 tests untouched. The Gherkin options (pytest-bdd / behave) add a `.feature`/step-binding layer on top and **need human dependency approval** (CLAUDE.md / RULES.md gate); their cost buys English-readable specs, which for a solo maintainer is the main thing weighed against the extra moving part.

---

## Q1 — Which BDD styles fit, and at what cost?

| Approach | New dep? (gate) | Headless / pygame fit | Solo learning curve | Regression-guard strength | Coexistence with the 329 tests |
|---|---|---|---|---|---|
| **(a) Plain-pytest given/when/then** — shared fixtures + a naming/structure discipline | **None** | Native — it *is* the current substrate (`conftest.py` forces `SDL_VIDEODRIVER=dummy`) | Lowest — no new concept, just convention | As strong as the assertions you write; no enforced structure | Perfect — existing tests already are this, unstructured; new tests adopt the discipline, old stay as-is |
| **(b) pytest-bdd** — Gherkin `.feature` files + `@given/@when/@then` step fns, runs inside `pytest` | **Yes** — needs approval **[EXTERNAL]** | Good — steps are plain Python, so the same `main(run_frames=…)` + event injection works inside a step; runs in the same `pytest` process, same `conftest.py` | Medium — Gherkin syntax + step-binding + `.feature`↔step wiring to learn | Strong once written; Gherkin makes the *intended behavior* legible, which catches "test still green but asserts the wrong thing" | Additive — `.feature` tests collected alongside plain tests in one `pytest` run; 329 untouched |
| **(c) behave** — standalone Gherkin runner, **separate** from pytest | **Yes** — needs approval **[EXTERNAL]** | Workable but **two test commands** (`pytest` *and* `behave`); its own `environment.py` must re-establish the headless SDL env `conftest.py` sets today | Highest — new runner, new lifecycle hooks, new CLI, separate from the tooling already in `pyproject.toml` (`test = ["pytest"]`) | Strong for the scenarios written in it, but the guard is now **split across two runners** — CI/`make` must run both or coverage silently forks | Parallel, not layered — 329 pytest tests keep running under pytest; behave adds a second world beside them |
| **(d) Thin hand-rolled scenario harness** — a small local `Scenario` / `given`/`when`/`then` helper module in `tests/` | **None** | Native — wraps the exact `main(run_frames=…)` + `pygame.event` seam already in use | Low-medium — one small local module to read; no external docs | Strong *and* DRY — the 16 duplicated `_frames` helpers collapse to one; a canonical canvas-coordinate vocabulary kills the hardcoded `(700, 300)` drift | Excellent — new tests call the helper; old tests migrate opportunistically or never |

**Reading of the table for a solo maintainer.** (a) and (d) are the same bet at two ambitions: (a) is "agree on fixture names and a file-structure convention"; (d) is "write the ~40-line helper that names the given/when/then the suite is already performing." Neither trips the dependency gate. (b) buys human-readable `.feature` specs at the cost of one approved dependency and a binding layer. (c) is (b)'s cost **plus** a second runner and a duplicated headless-env setup — the weakest fit here precisely *because* the suite is already all-pytest.

---

## Q2 — What is the unit of "behavior" for THIS editor?

The behavior classes worth scenario-izing, each expressible **headlessly against the fixed 640×360 base surface** by injecting synthetic events and asserting on editor state. Counts are files in the current suite that already touch each seam [IN-REPO].

| Behavior class | *Given* (setup) | *When* (injected events) | *Then* (assert on) | Already exercised in |
|---|---|---|---|---|
| **Canvas box ops** — add / dup / delete / drag / resize on the current frame | a character + move loaded (`main(character, move_key)`) | `MOUSEBUTTONDOWN/MOTION/UP` at canvas points; `A`/dup/delete keys | `WorkingMove` box list, `selected` id | `working.` / `WorkingMove` in **23 files**; `selected` in **11** |
| **Save ↔ load round-trip** — edit, save, reload, assert persistence | move loaded, `tmp_path` config dir | `A` (edit) → `S` → destination key (`O/S/B/N`) | `save_document` output, on-disk JSON, reloaded `WorkingMove` | round-trip idiom in **22 files** |
| **Overlay / help toggles** | editor running | `F1` / `?` / `Esc` | a `_draw_help` recorder call count | `test_help_modal.py` |
| **Frame scrub persistence** — add on frame 3, scrub away and back | multi-frame move | timeline nav keys + an add | box present on return to frame 3 | per-frame tests (`test_e4_per_frame.py`, `test_save_e5.py`) |
| **GIF-compare view ops** | a discoverable `*-gifs/` set | view-toggle / scrub keys | compare-view state | `gif_map` / compare tests |

**How a scenario expresses one, headlessly (the current idiom, verbatim shape) [IN-REPO]:**

```python
# The recurring "when" — feed synthetic event lists frame-by-frame, then run:
def _frames(monkeypatch, event_lists):
    queued = iter(event_lists + [[pygame.event.Event(pygame.QUIT)]])
    monkeypatch.setattr(pygame.event, "get", lambda: next(queued, []))

_frames(monkeypatch, [[pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(700, 300))]])
assert editor_main.main(move_key="fsmash", run_frames=5) == 0
# ...then assert on click_selection calls / WorkingMove / selected
```

This `_frames` (or `_run_with_keys`) helper is **re-declared in 16 files** — that duplication *is* the unstructured behavior vocabulary the ticket names. Every behavior class above already has a "then" target in the suite; none needs a display.

---

## Q3 — Migration path (coexistence, not rewrite)

All four options support the same coexistence stance, and the ticket forbids rewriting the 329 tests:

- **Greenfield-only (recommended default whichever syntax wins).** New behavior lands as a scenario in the chosen style; the 329 existing tests stay exactly as-is and keep running. No mass migration.
- **Opportunistic retrofit.** When a file is touched for other reasons, its local `_frames`/`_run_with_keys` is swapped for the shared vocabulary. Over time the 16 duplicated helpers converge; no big-bang rewrite is ever required.
- **Never a forced rewrite.** Because (a)/(b)/(d) all collect inside the one `pytest` run, old and new coexist in a single `pytest` invocation. (c) behave is the exception: it forks the run into two commands, so "coexistence" there means "two worlds running side by side," which a solo maintainer must remember to invoke both of.

The pure-decision + wiring split the suite already follows (e.g. `test_1073_click_deselect.py`: `selection.click_selection` asserted directly, then two event-queue tests prove `main` feeds it) is **exactly** the given/when/then seam — a scenario layer formalizes the wiring half without disturbing the pure-unit half.

---

## Q4 — What "prevent regressions with confidence" concretely needs (independent of BDD syntax)

Two disciplines matter **regardless** of whether the answer is plain-pytest, a harness, or Gherkin — they are orthogonal to syntax choice:

1. **Round-trip / golden discipline.** The 22 save↔load files already assert edit→save→reload persistence; making that a **named, reused round-trip scenario** (rather than 22 bespoke setups) is where "with confidence" comes from — a single canonical round-trip that new moves/fields opt into.
2. **A generalized drift-guard.** `test_help_modal.py`'s pattern — scan the handler source for every `pygame.K_*` and assert the set equals *documented ∪ exempt* — is a reusable shape: "every registered X has a corresponding Y, or the test names the gap." It currently guards key-bindings only; generalized, the same shape can guard "every canvas op has a scenario," "every savable field survives a round-trip," etc. This guard's strength is **independent** of the BDD syntax layered above it.

The implication: the BDD-syntax decision (Q1) and the confidence disciplines (Q4) are **separable**. A team could adopt the round-trip + drift-guard disciplines under plain pytest today and defer the Gherkin question indefinitely.

---

## Example scenario — same behavior, top-2 candidate styles

Behavior under test: **"add a box on frame 3, scrub away and back — it persists."**

### Style (d) — thin hand-rolled harness (no dependency)

```python
# tests/scenario.py  (the ~40-line shared vocabulary — NOT yet written; sketch only)
class Scenario:
    def __init__(self, monkeypatch, character="nalio", move_key="jab"):
        self._mp, self._char, self._move, self._events = monkeypatch, character, move_key, []
    def given_frame(self, n):      self._events += _goto_frame(n); return self
    def when_add_box(self):        self._events.append([_key(pygame.K_a)]); return self
    def when_scrub(self, delta):   self._events += _scrub(delta); return self
    def run(self):
        _frames(self._mp, self._events)
        return editor_main.main(character=self._char, move_key=self._move, run_frames=len(self._events)+1)

# tests/test_frame3_persist.py
def test_box_added_on_frame_3_survives_a_scrub(monkeypatch):
    s = (Scenario(monkeypatch)
         .given_frame(3).when_add_box()
         .when_scrub(+2).when_scrub(-2))     # away and back
    assert s.run() == 0
    assert _boxes_on_frame(3), "box added on frame 3 did not persist across a scrub"
```

### Style (b) — pytest-bdd Gherkin (**needs dependency approval**) **[EXTERNAL]**

```gherkin
# features/frame_persistence.feature
Scenario: A box added on a frame survives scrubbing away and back
  Given the editor is editing nalio jab on frame 3
  When I add a hit box
  And I scrub forward 2 frames and back 2 frames
  Then frame 3 still has the added box
```
```python
# features/steps/test_frame_persistence.py  — steps wrap the SAME main(run_frames=…) seam
@given("the editor is editing nalio jab on frame 3"); @when("I add a hit box"); @then("frame 3 still has the added box")
```

Same headless seam underneath both; (b) adds an English spec file + a binding layer (and the dep gate); (d) keeps it all in Python with no new package.

---

## Dependency-gate note (explicit, per acceptance criteria)

| Option | Package to add | Gate |
|---|---|---|
| (a) plain-pytest discipline | — | **None** — adopt freely |
| (d) thin hand-rolled harness | — | **None** — a local `tests/` module, no package |
| (b) pytest-bdd | `pytest-bdd` | **Human approval required** — CLAUDE.md / RULES.md → "Dependencies" (new dep gated even as a dev/test tool) |
| (c) behave | `behave` | **Human approval required** — same gate, and adds a second test runner |

Nothing in this doc installs, adds to `pyproject.toml`, or pins a version — the two gated options are **proposals**, per the ticket.

---

## Recommendation-space (NOT a pick — the decision is a downstream ARC ticket)

- **If the priority is "cheapest, ships today, zero gate":** the no-dependency pair (a)/(d) — and specifically **(d) the thin harness**, because it *removes* real duplication (16 re-declared helpers, hardcoded canvas points) while giving the shared given/when/then vocabulary the ticket asks for. This is the lowest-risk, highest-DRY option and needs no approval.
- **If the priority is "English-readable specs a non-coder could review":** **(b) pytest-bdd** — but only after the dependency is approved, and accepting one binding layer to learn. It stays inside the single `pytest` run, so coexistence is clean.
- **(c) behave** is the weakest fit for *this* repo specifically: an all-pytest suite gains a second runner and a duplicated headless-env setup for no benefit (b) doesn't already provide inside pytest.
- **Orthogonal, adopt regardless (Q4):** name a canonical **round-trip scenario** and **generalize the `test_help_modal` drift-guard shape** — these deliver most of "prevent regressions with confidence" independent of which syntax wins.

The pick among these is a human-gated decision (research reports options; the decision is a separate ARC ticket).

---

## Sources / evidence ladder

- **[IN-REPO]** `avidrucker/pycats-editor` @ `5ec879c` (2026-08-02):
  - `pyproject.toml` — `test = ["pytest"]`, src-layout, `requires-python >=3.12`, deps `pygame-ce` + `Pillow`.
  - `tests/conftest.py` — forces `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` + `PYCATS_EDITOR_NO_PERSIST` → headless substrate.
  - `src/pycats_editor/__main__.py::main` — signature `main(character, move_key, run_frames, start_scale, gif_path, mario_gifs_dir, repros_root)`; docstring names `run_frames` "the headless test seam."
  - `tests/test_help_modal.py` — the drift-guard pattern (scan `pygame.K_*` in handler source, assert `handled == documented | exempt`).
  - `tests/test_1073_click_deselect.py`, `tests/test_989_save_diff.py` — the pure-decision + event-queue-wiring split; the `_frames` / event-injection idiom.
  - Corpus counts (grep, 38 test files): **329** `def test_` fns; **22** files call `main(…run_frames…)`; **16** re-declare a local event-injection helper; **23** touch `working`/`WorkingMove`; **11** touch `selected`; **22** do save/load round-trips.
- **[EXTERNAL]** pytest-bdd (Gherkin-in-pytest, step bindings) and behave (standalone Gherkin runner) — described from general knowledge, **not** verified against a live install (none installed, per the dependency gate). Any adoption should re-confirm current behavior at approval time.
- **Blocked / not consulted:** the editor repo is private and was read from the local clone only; no external BDD-tool docs were fetched. No source was blocked by an access error this session.

## Cross-refs

#1122 (this ticket) · #792 (editor tracker) · #826 (editor scope) · #1007 (help modal / drift-guard origin) · #983/#989 (save-prompt + diff wiring) · #1073 (click-deselect wiring pattern) · #908 (headless persistence env). Companion: the implementation-audit research (sibling of #1122).
