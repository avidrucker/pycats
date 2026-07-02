# TIL 2026-07-01 — DRAGONFRUIT

**Context:** A long fleet session that shipped two whole feature epics — above-head timer bars (#334) and smash attacks + the charge mechanic (#327) — then font-size centralisation + scalar (#344/#345), and finally the situation-aware-AI ledge line (#312: edge-hog #404, recovery #409, edge-guard #413), which closed its umbrella #250. Most of the hard-won lessons were about *not building the wrong thing* and *testing behaviour honestly*.

---

## 1. A stale umbrella tracker will mis-route you to already-done work

**What happened:** Asked to "file the whiff-punish child" of #250, I nearly filed a duplicate — whiff-punish had already shipped as **#274** (closed, tested). This happened *three times in a row* against #250: its body still listed child 3 as "filing now" while #274/#277/#338/#379/#285 were all closed and merged. Each time I only caught it by grepping the code (`_whiff_open` already wired, `tests/test_whiff_punish.py` passing) and checking `gh issue view <child> --json state` before acting.

**What I learned:** An umbrella's prose decays faster than anything else in the repo, because agents close its children out-of-band and rarely sync the parent. The body is the *least* trustworthy source of "what's left." The fix that finally stuck: I synced #250's body against reality (ticked #274/#277/#338/#285, flagged only #312 open), and that immediately stopped the mis-routing.

**The rule:** **Before scoping an umbrella's "next child," verify each listed child's live state (`gh issue view N`) and grep the code — then sync the tracker body. Never trust an umbrella's prose over its closed children.** (Extends error #26 / the "verify ticket state before blocker claims" memory.)

---

## 2. Golden-safe by *default-identity*, not by hand

**What happened:** Every feature this session had to leave the deterministic sim + goldens byte-identical, and every one used the same trick: make the feature's **default an exact identity on the golden path**. Smashes (#327): the default cat has no smash move, so the whole charge/scale/angle machinery is unreachable by the scripted controllers. Font scale (#345): `standard` ⇒ `round(base*1.0) == base`, so the render is byte-identical at the default. AI ledge (#404/#409/#413): the level-less controller has every flag (`edge_hog`/`recover`/`edge_guard`) False and receives `ledges=None`, so the seeded input stream is untouched.

**What I learned:** I never once had to "keep the goldens green" by inspecting diffs — the identity default made green *structural*, and a single byte-identity/parity assertion proved it. When I did flip a golden-adjacent test (the SHIELD/DIZZY recolour #364), it turned out the parity oracle is a two-path self-comparison and couldn't flip anyway. Reasoning about the *default* up front is far cheaper than reasoning about the diff after.

**The rule:** **A new present-layer/behavioural feature is golden-safe when its default is an exact identity on the sim/golden path; gate it behind an off-by-default flag/None and assert the identity with a byte-identity or parity test.** (Filed for RULES.md as #418.)

---

## 3. An AI behavioural test must drive the real loop AND fail with the feature off

**What happened:** The #248/#370 gotcha — a controller decision that `decide()` emits but the game loop drops (a roll during hitstun) — bit me twice more, one level deeper. (a) My AI edge-guard **melee-poke** unit test passed *with edge-guard mutated off*, because the normal attack cadence also emits `{attack}` at that close, level position — a non-discriminating test. I fixed it by placing the foe **below the lip** (`dy>60`), where the on-stage poke's `dy<60` gate blocks the normal attack and only edge-guard fires. (b) My recovery real-loop test compared final `y`, but the feature-off bot fell → KO'd → **respawned to `y=-1000`**, inverting the comparison; I switched the discriminator to "did the recovery jump *emit in the loop*."

**What I learned:** "Runs the real loop" and "discriminates the feature" are two separate requirements, and the second is the one that quietly fails. A revert-check on the *integration* test (not just the units) is what exposed both — the mutant-off run must go red.

**The rule:** **An AI behavioural test must (1) drive `run_battle`/the real update loop and (2) go red with the feature disabled; if the control passes, the test isn't testing the feature — pick a scenario the baseline can't satisfy.** (Filed for RULES.md as #418; extends the #248/#370 gotcha.)

---

## 4. Setting an env var at a test module's top level poisons the whole pytest session

**What happened:** My first `test_font_scale.py` opened with `os.environ.setdefault("PYCATS_NO_PERSIST", "1")` at module scope. The full suite then failed **15 unrelated** settings save/load + Options-row tests. Cause: pytest imports every test module during collection, so that line ran once and left persistence disabled for the *entire* run.

**What I learned:** Module-scope side effects in test files aren't local to that file — collection executes them globally, before any test runs. My tests didn't even need it (they use `_validated`/in-memory `set` + a monkeypatched `settings.save`).

**The rule:** **Never mutate `os.environ` at a test module's top level — isolate persistence per-test (`monkeypatch`, in-memory setters, fixture teardown).** (Saved to agent memory: `pytest-env-at-import-pollutes-session`.)

---

## 5. When a spike defers a slice's design, decide it *in the ticket* — the review's job is to catch the undecided fork

**What happened:** Two slices had designs the #328 spike explicitly deferred. Angleable f-smash (#383): the input scheme was open (up = jump, so "up+forward+smash" is ambiguous), so I chose "horizontal decides the f-smash, vertical is an angle modifier" and recorded it in the ticket before building. Edge-guard (#413): my own issue-review caught that edge-guard and the #404 edge-hog grab *both* fire when the opponent is off-stage, with no precedence specified — a level-9 bot would edge-hog and never reach the guard. I amended the ticket with the locked precedence (guard fires first when a safe on-stage attack is in range) + pinned the tuning bands *before* claiming.

**What I learned:** The most valuable thing `/issue-review-skill` did all session was flag the *undecided interaction* on a ticket I'd written myself. A deferred design doesn't disappear; it resurfaces mid-implementation unless the child ticket resolves it. Recording the decision in the ticket (yegor "decisions in writing") made the build a clean courier task.

**The rule:** **A slice whose design a spike deferred is not build-ready until the design (input scheme, representation, precedence vs sibling features) is decided and written in the child ticket — and the review must hunt for that undecided fork.**

---

## What landed

| Epic | Shipped |
|---|---|
| Above-head timer bars (**#334**, closed) | drawer+recency (#340/#357), HANG #348, DOWN #350, LOCKOUT #357, INVULN #358, SHIELD/DIZZY #364, CHARGE fill #380 |
| Smash attacks + charge (**#327**, closed) | Nalio smashes #366, charge state/timer #371, charge scaling #377, angleable f-smash #383, Narz tipper smashes #381 |
| Fonts | single source #344, global scale scalar #345 |
| Situation-aware AI (**#312**+**#250**, closed) | edge-hog #404, deliberate recovery #409, edge-guard #413 |

## Open threads

- **#418** — codify rules #2 and #3 above into RULES.md (the authority path for this TIL).
- **#336** — respawn-countdown indicator (split from #334); still open.

## Related artifacts

- [TIL 2026-06-30 FIG](./today-i-learned-2026-06-30-fig.md) — the #248 discriminating-test gotcha and "umbrella isn't a work unit," one session earlier.
- Agent memory: `pytest-env-at-import-pollutes-session`, `verify-ticket-state-before-blocker-claims`.
- Issues #250, #312, #327, #334, #418.
