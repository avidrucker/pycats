# Test-double policy for pycats — fakes vs mocks vs stubs vs spies (#497)

**Role:** RESEARCH (DRAGONFRUIT), 2026-07-03. Survey + house guidance; **no test rewrites**.
Grounded in the current suite (post-#470 audit) and the in-flight profile/keybind/audio work.

## TL;DR
pycats is **already doing this right** — the policy mostly needs writing down. Randomness is
injected + seeded, time is frame-based (no clock to fake), persistence is isolated via a real
temp dir (not a mocked filesystem), and the sole `unittest.mock` use is a *justified* spy. The
house rule: **prefer real object → fake → stub → spy → mock (last)**; reach for a mock/spy only
when the *interaction itself* is the contract under test.

## Taxonomy (Meszaros, *xUnit Test Patterns*) in pycats terms

| Double | What it does | Verifies | pycats example / where it applies |
|---|---|---|---|
| **Dummy** | Fills a parameter slot; never used | nothing | an idle controller passed as `None` in `run_battle(controllers=(c1, None))` |
| **Stub** | Returns canned answers (controls indirect *inputs*) | state | a settings loader returning a fixed dict |
| **Fake** | Real but simplified working implementation | state | a **seeded `random.Random(seed)`** for the AI; a temp-dir config store |
| **Spy** | A stub that *records* how it was called; test asserts after | interaction | `test_menu_widget_rollout.py` — records `draw_menu_button` calls |
| **Mock** | Pre-loaded with call *expectations*; the double asserts | interaction | (none in-repo; avoid unless the protocol is the SUT) |

The split that matters: **stub/fake feed inputs and let you check resulting state** ("does it do
the right thing?"); **spy/mock check interactions** ("did it call X with Y?").

## Decision rubric — which double when
- **Need a working collaborator, lightweight + deterministic?** → **fake** (seeded RNG, in-memory
  or temp-dir store). Default when a plain real object is too heavy or non-deterministic.
- **Only need to control what a dependency returns?** → **stub**.
- **Need to verify a side-effect you cannot see in state** (a sound played, a file written)? →
  **spy** — record and assert after, sparingly.
- **The interaction/protocol with a collaborator IS the thing under test?** → **mock** (rare).
- **A parameter must exist but is irrelevant?** → **dummy**.

## House rule (the ordered preference)
**real object → fake → stub → spy → mock — mock last.**
- **Avoid mocks whenever a fake or real object works.** A mock couples the test to the
  implementation's *internal call sequence*: a behavior-preserving refactor breaks it, and a
  green mock proves "the code called X", not "the code works" — the **Mockery** + **Inspector**
  anti-patterns (yegor-unit-tests).
- **Spies carry a milder version of the same coupling** — use only for genuinely unobservable
  side-effects; otherwise assert on observable output.
- **Stubs and fakes are the safe defaults** — they set up inputs without locking you to *how* the
  code consumes them.

## Current-usage audit (what the suite already does — keep it)
- **Randomness → injected + seeded (exemplar).** `AttackerController(rng=...)`; `rng=None`
  resolves to `random.Random(seed)` (`sim/controllers.py`, #166). This is dependency injection of
  a **fake-friendly real object** — seeded battles are reproducible without any mock. *This is the
  model to copy for any future nondeterminism.*
- **Time → frame-based, nothing to fake.** No `time.time`/`perf_counter`/`get_ticks` in product
  code; the sim advances by integer frame counters. **No fake clock is warranted** — a genuine
  non-gap. (If a wall-clock dependency ever appears, inject it and fake it; don't sprinkle
  `time.time()` into logic.)
- **Persistence → real store in a temp dir, not a mocked filesystem.** `keybind_store` / `settings`
  redirect `PYCATS_CONFIG_DIR` to `tmp_path` (the #95 pattern:
  `monkeypatch.setenv("PYCATS_CONFIG_DIR", tmp_path)`, `test_keybind_store.py:25`,
  `test_settings.py:11`). This tests the **real** JSON round-trip against a throwaway dir —
  strictly better than mocking `open`. **Reuse this verbatim for the #478 profile store.**
- **The one `unittest.mock` use is a *justified spy*, not an anti-pattern.**
  `test_menu_widget_rollout.py` patches `draw_menu_button` with a recording fake to assert the
  menus *route through the shared widget* (its own docstring notes the able-to-fail: pre-adoption
  the menus render plain text → the spy records no calls → red). Here the **interaction is the
  contract** (a rendering-consolidation refactor), and asserting pixels would be both brittle and
  unable to distinguish "plain text" from "via widget". **Verdict: keep.** *(This refines #470
  audit finding E, which flagged it as Inspector on a quick read — on inspection it is defensible.)*

## Fakes worth building (short — mostly already covered)
Ranked; most upcoming needs are met by existing patterns, so this is a small list:
1. **Audio sink fake / spy — only if #445 (audio subsystem) lands.** Audio is a side-effect with
   no observable state, so a fake sink that records "played sound X" (a spy) is the right tool —
   the one genuinely new double the roadmap implies.
2. **Profile store — no new fake; reuse the `PYCATS_CONFIG_DIR → tmp_path` pattern** for #478/#441.
3. **Keybind sets — same temp-dir pattern** for #440/#463 (extends the existing `keybind_store` tests).

## Proposed one-liner for RULES.md / testing docs (if adopted)
> **Test doubles:** prefer real object → fake → stub → spy → mock (mock last). Inject
> nondeterminism (seed the RNG), isolate persistence with `PYCATS_CONFIG_DIR → tmp_path`, and
> reach for a spy/mock only when the *interaction itself* is what's under test.

## Proposed follow-up tickets (listed, NOT filed — one at a time)
1. **convention: add the test-double house rule to RULES.md / a testing doc** (codify the
   one-liner + link this doc). Low effort, high durability.
2. **(gated on #445) DEV: add a fake audio sink + spy pattern** for menu/screen sound tests.
3. **(low) revisit `test_menu_widget_rollout.py`** only if `draw_menu_button`'s output becomes
   observably assertable — otherwise leave the justified spy as-is (supersedes #470 finding E).

## Method / limits
- Grounded in `sim/controllers.py` (RNG DI), a product-code grep for wall-clock time (none),
  `test_keybind_store.py` / `test_settings.py` (temp-dir persistence), and
  `test_menu_widget_rollout.py` (the spy). Not an exhaustive per-file classification of all 174
  files — the `monkeypatch`-heavy majority are stubs/fakes by the definitions above.
- Depth (building the audio fake, editing RULES) is deferred to the follow-ups.
