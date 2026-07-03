# TIL 2026-07-02 — CHERRY

**Context:** Two tickets this session — #332 (visual button-press feedback / highlight-pulse across the menu-button screens) and #424 (the AI edge-hog self-KO bug) — plus the issue-review + split work that fed them (#445 audio decision, #458 ledge-PX research). The bug fix is where most of the lessons came from: it fought back.

---

## 1. Reproduce the failing observable first — a *sibling feature* can mask the bug

**What happened:** #424 said a level-9 edge-hog bot self-destructs by holding the ledge past its own `ledge_hang_timer`. I set up the reported repro in a real `run_battle` loop (bot hanging, opponent pinned off-stage) and… it survived. Every time. The bot held to the timeout, dropped — and then the **`recover` branch (#409)**, also on at level 9, jumped it right back onto the stage. The self-KO only appeared once I set `jumps_remaining = 0` (a bot that grabbed the ledge after spending its recovery): then it dropped with no jump, fell, and KO'd at frame ~144 (lives 3→2).

**What I learned:** The bug was real, but a *different* level-9 feature was papering over it in the obvious scenario. Had I trusted the ticket and fixed blind, my "regression test" would have been green with **and** without the fix (recover rescues the bot either way) — a test that can't fail, guarding nothing. The masking condition (no jump left) was the whole key to a discriminating test.

**The rule:** **Reproduce the failing observable in a real loop before writing the fix; if it stubbornly won't fail, find the condition that's masking it — that condition is usually what your able-to-fail test must pin.** (Sharpens the RULES "revert-the-fix check": the check is only meaningful once the red is real.)

---

## 2. `git checkout <file>` to undo a revert-check *wipes your uncommitted fix*

**What happened:** Doing the revert-the-fix check, I neutered the guard in `controllers.py` with a script, ran the tests (confirmed the two facet-1 tests went red — good), then ran `git checkout pycats/sim/controllers.py` to "put it back." That command restores the file to **HEAD** — which was the claim commit, i.e. *before any of my edits*. My fix was uncommitted working-tree state, so both the new constant and the guard evaporated. Only the untracked test file survived. I caught it by grepping for `LEDGE_HOG_SAFETY_FLOOR` (MISSING) before committing, and re-applied from memory.

**What I learned:** A revert-check deliberately makes the working tree dirty; `git checkout` is the wrong "undo" because it doesn't distinguish "the temporary neuter" from "my real fix" — it drops both back to the last commit. This is a standing memory pin ([git-checkout-revert-check-footgun]) and it *still* bit me.

**The rule:** **Never `git checkout <file>` to reverse a revert-check while the fix is uncommitted — snapshot the fix first (copy aside, `git stash`, or commit), or re-apply by hand and grep to confirm it's back before committing.**

---

## 3. Don't manufacture a red for a facet you can't reproduce — ship a labeled guard + a finding

**What happened:** When I rewrote #424 during issue-review, I dutifully added a *second* able-to-fail assertion for facet 2 ("walk-off grab miss → self-KO, red if the go-to-ledge branch commits unbounded"). Then I tried to reproduce facet 2 and couldn't: across five start positions, with `recover` off and jumps spent, the `{left/right}` walk is arrested at the platform edge (min centerx ~74–77, always on-stage). `EDGE_HOG_RANGE` + platform collision already prevent the walk-off. There was no red to make green. Writing a "bot survives the walk" test that passes today regardless would be a Happy-Path / Liar test.

**What I learned:** I promised the able-to-fail test *before* reproducing the facet — the review rubric pushed me toward "cover both facets," and I mistook "coverage" for "a red." For an already-safe facet the right artifact is a **characterization guard** (green today, a tripwire that goes red only if a future change removes the safety), clearly labeled as such, plus a written finding on the ticket — not a fabricated failing test and not a speculative fix. The ticket's own escape hatch ("split if facet 2 wants a different fix") existed for exactly this; the answer was "no fix needed."

**The rule:** **Reproduce a facet before you promise it an able-to-fail test. If it's already safe, ship a labeled guard test + a written finding — never invent a passing test to look like coverage, and never force a fix nothing needs.**

---

## 4. Extend a shared render/sim primitive with a *default-identity* parameter to keep goldens byte-identical

**What happened:** #332 needed the focused menu button to flash on press. Rather than a parallel code path, I added a `pressed=False` kwarg to the shared `draw_menu_button` and a small per-screen `press_pulse` frame counter. Because `pressed=False` renders exactly as before, the default output is byte-identical — the render-parity / golden tests passed with no regen, and I added an explicit parity test asserting the bare call equals `pressed=False`.

**What I learned:** This is the same discipline the AI levels use (#312's flags default off → the level-less golden path is an exact identity). A new capability on a shared primitive is golden-safe *by construction* when its default is the identity, which beats hand-checking that nothing moved.

**The rule:** **Add new behaviour to a shared render/sim primitive behind a default-identity parameter, then assert byte-identity for the default — golden-safety becomes structural, not a manual audit.** (Same family as [render-parity-oracle-vs-sim-goldens].)

---

## Open threads

- **Split at the gated boundary.** #332 bundled a visual build with an *audio* half that needs a whole new subsystem (mixer + assets = human-approval dependency); I split the audio out as a `decision:` ticket (#445) rather than smuggling the dependency in. The #424 investigation likewise surfaced a player-experience concern (is the ledge too easy to fall off of?) → filed as research #458. Pattern worth a RULES note: *when a ticket couples a build with a gated decision, extract the decision as its own ticket.*

## Related artifacts

- Issues: #332 (visual press feedback), #424 (edge-hog self-KO), #445 (audio decision), #458 (ledge stay/leave research)
- Memory pins: `git-checkout-revert-check-footgun`, `render-parity-oracle-vs-sim-goldens`, `fleet-merge-race-run-suite-early`
- Sibling TIL: [TIL 2026-07-01 CHERRY](./today-i-learned-2026-07-01-cherry.md)
