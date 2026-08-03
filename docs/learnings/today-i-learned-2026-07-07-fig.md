# TIL 2026-07-07 — FIG

**Context:** Shipped the demo/sim playback interaction trio (#514 any-key-skip, #515 hold-Esc-exit, #508 →-skip-to-section), then ran the research→decision pipeline for the `game.py` shell boundary: assessed #280, filed + closed the #687 modularization spike, and used a grill + `guide-human-decision` to rule #280 and file DEV-1 (#698).

---

## 1. Compose, don't inject — persistence is an app policy, not a component property

**What happened:** Grilling the #280 ruling, I proposed making `DisplayManager` (the extracted display object) take a `persist` callback so `toggle_fullscreen()` could save prefs. The human pushed back: "can we separate concerns, compose, and *not* inject?" That reframed it. The "toggle-then-save" pairing isn't a property of the display at all — F11 and the Options row both want "change the display **and** remember it," but *remember it* is an application decision. Injecting a callback still makes the display object responsible for *calling* persistence; it just hides the wiring.

**What I learned:** Injection and composition both decouple, but they answer different questions. Injection asks "who supplies the dependency?"; composition asks "who *owns the policy* that binds two independent things?" When the coupling is a policy (save-after-change), the clean move is to give the object **zero** knowledge of the second concern and let a higher layer compose them. `DisplayManager` ends up pure — constructor takes plain values (`windowed_scale`, `start_fullscreen`), not a settings object or a callback — so it has one reason to change and is headless-unit-testable with no file I/O (dodging the #345 settings-file test-pollution trap entirely).

**The rule:** **When two things are coupled by a *policy* rather than a *need*, compose them at the layer that owns the policy — don't inject the second into the first.** (Authority: ruled into #280's closing comment and baked into #698's acceptance.)

---

## 2. A closed dependency can *defer* the question, not answer it

**What happened:** #280 (a decision ticket) said "defer to the in-flight #257 hexagonal review." I found #257 CLOSED and almost reported "#280 is unblocked, its question resolved." But reading #257's actual comments — not just its state — showed it had **flagged #280 and explicitly scoped it out**: *"raises a concrete instance for the hexagonal lens to weigh… no action needed mid-spike… not a scope change to this spike."* The dependency closed *around* the question, not *through* it. I then verified the code premises still held (`game.py` still has the top-level `while running:` loop, the fullscreen/zoom globals) before declaring #280 ready.

**What I learned:** "Blocked-by #X" plus "#X is closed" does **not** imply "#X answered it." A blocker can close having deferred, re-scoped, or merely acknowledged the downstream question. Reading the closing *outcome* (and re-checking the code the ticket rests on) is the difference between "ready" and "stale-but-looks-ready."

**The rule:** **Before calling a deferred ticket ready, read the blocker's closing outcome and re-verify the ticket's code premises — a closed dependency may have deferred the question, not resolved it.** (Authority: an instance of RULES.md → "Read the source before asserting" / #562 — I grounded the readiness call in #257's actual comment + the current `game.py`, not in its CLOSED state.)

---

## 3. When the safety net is FSM-trace, prove byte-identity with a render-hash

**What happened:** Three times this session I extracted shared code that feeds the render path — the `EscHoldTimer` + `draw_esc_hold_arc` out of `screen_manager` (#515), the fast-forward seam (#508), and the same bar written into #698's acceptance for `DisplayManager.present()`. The repo's `screen_parity` test is an **FSM-trace** (state-transition) check, not a pixel check, so a blit/scale regression in a render helper would pass it silently. For #515 I hashed the arc surface (`pygame.image.tobytes(surf, "RGB")` → sha256) across a matrix of progress values, old-inline vs new-shared, and asserted IDENTICAL before trusting the extraction.

**What I learned:** Know what your green suite actually proves. A passing trace test is not a passing pixel test. For a behavior-neutral refactor of golden-*un*covered UI, the honest verification is an explicit before/after content hash across the relevant input matrix — otherwise "all tests green" quietly means "nobody looked at the pixels."

**The rule:** **Refactoring render code guarded only by FSM-trace tests? Prove byte-identity with a before/after render-hash across the state matrix — a green trace suite is not a pixel guarantee.** (Authority: the established pattern, now written as a per-slice acceptance bar in #280's ruling and #698's acceptance; memory note `render-hash-verify-uncovered`.)

---

## 4. Grill-then-guide turns a recommendation into a *recorded* ruling — and finds the sharpest design point

**What happened:** The #687 findings doc *recommended* option (b) with a sequence. But a recommendation in a doc isn't a decision. Running `grill-me` (one question at a time, each with my recommendation) down the decision tree — root ruling → sequence → C1 scope → verification bar → cadence — is what surfaced the compose-not-inject point (lesson 1); it didn't come from the doc, it came from being interrogated on the doc. Then `guide-human-decision` converted the confirmed answers into a structured ruling comment on #280, filed **only** DEV-1 (#698) per the one-at-a-time cadence, and closed the decision.

**What I learned:** The grill is not ceremony over an already-made decision — it's where the load-bearing sub-decisions (and their best answers) actually get found. And the two skills compose: grill to *reach* the shared answer, guide-human-decision to *record and execute* it (post the ruling, file the next slice, close the parent). Filing DEV-2/3/4 up front would have violated the one-child-at-a-time cadence; the guide step enforces that.

**The rule:** **To turn a recommendation into a decision, grill the whole tree one node at a time (that's where the real sub-decisions surface), then use guide-human-decision to record the ruling and file only the next slice.** (Authority: #280's ruling comment + the one-at-a-time cadence in CLAUDE.md → "Filing work" / "Research epics.")

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/sim/presenters.py` | Pure `_dwell_interrupt` — any key ends a timed caption dwell early (#514) |
| `pycats/esc_hold.py` + `screen_manager` + presenters | Shared `EscHoldTimer` + `draw_esc_hold_arc`; hold-Esc-2s exits CLI playback; retired #393 manual mode (#515) |
| `pycats/sim/runner.py` + presenters + `watch.py` | `boundaries` kwarg + unrendered fast-forward; → skips to next caption section (#508) |
| `docs/research/2026-07-06-game-py-modularization-spike.md` | #687 findings — map + feasibility driving the #280 ruling |
| #280 (closed) → #698 (filed) | Shell-boundary ruled option (b), C1→C2→C3; DEV-1 `DisplayManager` filed |

## Open threads

- **DEV-2 (C2 `main()`+guard) / DEV-3 (C3 `App`/`step()`) / DEV-4 (font)** — named in #687 §6, filed one-at-a-time after each predecessor closes. Handoff at `/tmp/handoff-698-game-py-shell-extraction.md`.
- **Recurring personal slip:** twice this arc I wrote a new test file into the *main* checkout instead of the claimed worktree (error rows #113 et al.), and hit a stale-`old_string` Edit (#119). Both already in the error store + auto-memory (`read-before-edit-in-worktrees`); flagging so the pattern stays visible.

## Related artifacts

- Sibling today: [TIL 2026-07-07 GRAPE](./today-i-learned-2026-07-07-grape.md)
- Issues #514, #515, #508, #687, #698; decision #280
