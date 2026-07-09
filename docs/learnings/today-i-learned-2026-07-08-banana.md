# TIL 2026-07-08 — BANANA

**Context:** Completed the `game.py` shell extraction ruled in #280 — C1 `DisplayManager` (#698), C2 `main()` + import-safety (#701), C3 `App`/`step()` (#707) — plus a DP1 placeholder-render slice (#694). Along the way I reviewed, trimmed, and grilled the C2/C3 tickets before implementing them. The through-line: a decomposition is only as good as whether each slice's acceptance can actually be tested at that slice's stage.

---

## 1. An acceptance criterion is only real if its test can be written at that slice's stage

**What happened:** I filed #701 (C2: wrap the runtime in `main()`) with a "loop-wiring coverage" acceptance bullet — "a test that the QUIT path sets `running = False`." On review I realised that test *cannot be written at C2*: after the wrap, the loop body is still welded inside `while running:`, and the only way to reach the QUIT path is to run the real blocking loop (which opens a window and never returns). The sole writable test would be `assert callable(main)` — which passes the instant `def main():` exists, proving nothing.

**What I learned:** The tell wasn't a style nit; it was that the slice bundled two *testability tiers*. Import-safety was testable at C2; loop-body wiring only becomes testable once C3's `step()` seam exists. And the #280 ruling (Q2) already said so verbatim — "the real loop-wiring coverage payoff needs C3's `step()` seam anyway" — so this was a divergence from a ratified requirement, settled at rung 1 of the authority ladder, not a judgment call. I trimmed #701 to one deliverable + one able-to-fail test and moved the loop-wiring bullet to C3 (#707), where at close it landed as four real spied-order tests.

**The rule:** **Don't put an acceptance criterion in a slice whose test can't be written until a later slice — trim it out, and cite the ruling that already placed it downstream.** (Candidate for `RULES.md`; reinforces the BDD "work = a failing test" principle.)

---

## 2. When the pre-fix state *hangs*, prove able-to-fail with a revert-check that injects a fast side effect

**What happened:** C2's core test imports `pycats.game` under monitored `pygame.init`/`set_mode`/`settings.load` and asserts none fire. But I couldn't watch it fail the normal way: before the wrap, importing `game.py` runs the module-level loop and blocks forever — a hang, not a clean red. TDD says "watch it fail first," and here the honest red was unobservable in-process.

**What I learned:** The able-to-fail obligation still holds; you just satisfy it differently. I observed a clean red on the *AST* half (no `main()` defined yet → fail), and for the monitored-import half I did a revert-check *after* wrapping: inject a single module-scope `pygame.init()` and confirm the test reddens (`Left contains one more item: 'pygame.init'`), then remove it. A fast import-time side effect exercises the exact assertion without the infinite loop.

**The rule:** **If reverting the fix would hang rather than fail cleanly, demonstrate able-to-fail by injecting a fast import-time side effect and watching the guard redden — don't skip the proof.** (Reinforces CLAUDE.md's revert-check requirement.)

---

## 3. Ground interlocking design decisions in the codebase's own idioms, one fork at a time

**What happened:** #707 (App/`step()`) had three coupled design forks: how `App` gets events for testing, where `settings.load()` happens, and where the drive loop lives. I ran `grill-with-docs` + `guide-human-decision` — one question at a time, in dependency order — and every recommendation pointed at an existing pattern rather than my preference. The injection seam: the codebase already had `ScreenStateManager(p1, p2, display_hooks=None)` — a constructor taking a collaborator, inert-for-headless — so `App(prefs, poll=inp.poll)` just mirrored it. The settings boundary: `DisplayManager` was deliberately kept settings-free (plain values in) to dodge the #345 test-file-pollution trap, so `App` taking a plain `prefs` dict extended the same compose-not-inject line one layer up.

**What I learned:** The strongest design argument in a mature codebase isn't "this is cleaner" — it's "we already do exactly this over here." Grounding each fork in a named precedent made the decisions fast and made the ruling comment self-justifying. Resolving them in dependency order mattered too: the settings boundary and drive location both *fell out* of the injection choice once it was pinned.

**The rule:** **For a design decision in a mature repo, find the existing idiom that already solves the shape and cite it — precedent beats preference, and it makes the ruling defensible.**

---

## 4. `compose, not inject` propagates up the layers to keep test file-I/O out

**What happened:** Across C1→C3 the same principle recurred. `DisplayManager` (#698) knows nothing about `settings` — it takes `windowed_scale`/`start_fullscreen` as plain values, so its tests do zero file I/O. In C3 I extended that to `App`: `main()` does `settings.load()` + `seed()` and hands `App` a plain `prefs` dict, so constructing `App` in a test is file-I/O-free too — the four wiring tests pass `{"windowed_scale": 1.0, "fullscreen": False}` literally. `App` still *owns* the persist half (`save_prefs → settings.save`), which is spied, not executed.

**What I learned:** Keeping policy (persistence) at the orchestration edge and passing plain values inward isn't just tidy layering — it's what makes each layer headlessly testable without the #345 settings-file-pollution trap. The pattern compounds: every layer that takes plain values instead of a live dependency is a layer whose tests stay pure.

**The rule:** **Push side-effectful dependencies (settings, files) to the outermost layer and pass plain values inward; inner objects own *policy* but never *I/O* — that's what keeps their tests file-free.** (Reinforces the #280 compose-not-inject ruling.)

---

## 5. Dead code a refactor *surfaces* is forced work — flag it, don't silently delete

**What happened:** Wrapping the runtime into `main()` (#701) moved the font-setup block inside a function, which turned an already-dead `font` variable (assigned, never read since rendering was extracted) into a ruff `F841` gate failure. I had to remove the block to pass the gate — but a ~4-line deletion of code I didn't write is beyond a "mechanical wrap."

**What I learned:** The refactor didn't *create* the dead code; it *exposed* it (module-level unused vars aren't flagged by `F841`, function-local ones are). That makes removal forced and behavior-neutral — but the repo's "suggest, don't act" rule means I still surface it explicitly (in the commit body and the closing comment) rather than folding a silent deletion into an unrelated change.

**The rule:** **When a refactor forces a deletion (dead code a lint gate only now sees), do it — but flag it loudly in the commit and closing comment; forced ≠ silent.** (Reinforces CLAUDE.md "suggest, don't act".)

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/display_manager.py` | New `DisplayManager` — S2 display globals → object, render-hash guard (#698) |
| `pycats/game.py` | Runtime wrapped in `main()` + `if __name__` guard, import-safe (#701); then reduced to boot + drive (#707) |
| `pycats/app.py` | New `App` with a `step()` seam owning the loop body + persist composite (#707) |
| `pycats/characters/roster.py` | `_TESTCAT` → flat uniform gray + black feature outlines (DP1, #694) |
| `tests/test_app_step.py` | Four able-to-fail loop-wiring tests (QUIT / quit-check / update→render→present / F11) (#707) |
| `tests/test_game_no_star_import.py` | Flipped AST-only → monitored-import; extended to `pycats.app` (#701/#707) |

The C1→C2→C3 sequence is complete: #280 is realized and #386's untestable-loop blindspot is closed.

## Open threads

- **DEV-4** (font-pick move to `text_utils`) is likely moot — #701 removed that block as dead code. Recommend confirming and *not* filing.
- Lesson 1's meta-rule (testability-tier ticket splitting) is a candidate for `RULES.md` — file a follow-up if it recurs.

## Related artifacts

- Issues #280 (ruling), #687 (findings), #698, #701, #707, #694, #386
- Errors logged this stretch: #131 (sed restore no-op'd), #132 (recurring read-before-edit-in-worktree)
