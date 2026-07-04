# Snapshot: current test-suite overview

A plain-language map of the pycats test suite — what it is at a high level, the
categories of tests in it, what `monkeypatch` is, and what the `x` in test output
means. Snapshot as of 2026-07-04; counts drift as the suite grows.

## High level

- **~1,088 tests across 179 files** in `tests/`.
- The suite is the **merge gate**: in fleet mode, agents run the whole thing after
  claiming and before closing work.
- A shared **`tests/conftest.py`** provides two safety fixtures so one test can't
  pollute the next:
  - **`_reset_runtime_settings`** (autouse — runs for every test): resets the global
    HUD/settings state before each test, so a test that flips a toggle can't leak into
    later render tests.
  - **`render_isolation`** (opt-in per render module): re-initialises pygame fonts and
    clears the render caches, so render tests pass regardless of execution order.
- That "don't let one test pollute the next" theme is the backbone — it exists because
  of real bugs (e.g. `os.environ` set at a module's top level once broke ~15 tests;
  `monkeypatch`, below, is the fix).

## The categories

| Type | What it does | Example files |
|---|---|---|
| **Sim / logic** | Build a real `Player`/`Fighter` (58 files) or run the deterministic sim via `run_battle` (44 files) and assert real behaviour — jumps, knockback, dodge, ledge | `test_dash.py`, `test_crouch.py`, `test_knockback_momentum.py` |
| **Golden / parity "oracles"** | Snapshot exact rendered pixels or sim output and assert **byte-identical** (66 files touch this). Catch *any* change | `test_battle_screen_render.py` |
| **Screen / menu wiring** | Feed synthetic pressed-key sets into a menu and assert the state machine reacts | `test_options_menu.py`, `test_options_keybind_sets.py` |
| **Persistence** | Save/load JSON to a temp dir; assert round-trips + graceful missing/corrupt handling | `test_settings.py`, `test_keybind_store.py`, `test_profile_store.py` |
| **Guard / meta** | Assert about the codebase itself, not runtime behaviour | `test_no_free_form_todos.py` |
| **The lone spy** | 1 of 179 files uses `unittest.mock` — verifies menus *route through* the shared widget | `test_menu_widget_rollout.py` |

Two distinctions matter most:

- **Behaviour tests vs. golden "oracles."** A behaviour test says "jumping should reduce
  `jumps_remaining`." A golden/parity test says "the rendered frame must be these exact
  bytes." Goldens catch everything — but also flip on *harmless* changes (a colour tweak
  reddens them even though nothing broke). Hence the **byte-identical-by-default**
  convention: new features hide behind a default path that leaves the goldens untouched
  (e.g. `nickname=None` in #478 rendered identically, so the parity oracle stayed green).
- **Real objects vs. test doubles.** Almost everything uses *real* objects — a real
  `Player`, a real store writing to a real temp directory. Only **1 of 179 files** uses a
  mock. That is the healthy posture the #497 doubles-policy doc wrote down: *real object →
  fake → stub → spy → mock (last)*. See
  [`docs/research/2026-07-03-test-doubles-policy.md`](research/2026-07-03-test-doubles-policy.md).

## What `monkeypatch` is

`monkeypatch` is a **built-in pytest fixture that temporarily changes something for the
duration of one test, then automatically undoes it** at test end. Add `monkeypatch` as a
test argument and pytest hands it to you. It's how you avoid the "leak into the next test"
problem. Two flavours appear in the suite:

**1. `monkeypatch.setenv` — set an environment variable** (`test_settings.py:12`):

```python
def test_save_then_load_round_trips(tmp_path, monkeypatch):
    monkeypatch.setenv("PYCATS_CONFIG_DIR", str(tmp_path))
```

`tmp_path` is another built-in fixture — a fresh empty temp directory per test. So this
says: "for *this test only*, point the config dir at a throwaway folder." The settings
code writes its JSON there instead of your real `~/.config/pycats/`; the env var is
restored when the test ends. This is why persistence tests never touch your real saved
settings.

**2. `monkeypatch.setattr` — swap out a function** (`test_demo_manual.py:73`):

```python
monkeypatch.setattr(pr, "render_battle", lambda *a, **k: None)
```

Replaces the real `render_battle` with a do-nothing stub *for this test*, so a demo-logic
test can run without painting pixels. Auto-restored after.

So: **monkeypatch = "temporarily replace an env var / attribute / function, auto-reverted
at test end."** The lightweight alternative to mocks — swap the real thing for the test,
rather than building a fake object that records calls.

## What the `x` means

The `x` is **not a failure** — it's the opposite of what it looks like. pytest prints one
character per test:

| Char | Meaning |
|---|---|
| `.` | passed |
| `F` | **failed** (real red) |
| `E` | error (crashed before asserting) |
| `s` | skipped |
| **`x`** | **xfailed — "expected to fail," and it did. This is fine / green.** |
| `X` | xpassed — expected to fail but *passed* (surprising) |

When a full run ends with **`1097 passed, 1 xfailed`**, that `1 xfailed` is a *green*
result. It comes from `test_no_free_form_todos.py` — a guard test that counts leftover
`#### TODO:` comments and asserts zero (tracked by #50). ~50 remain, so the assertion
genuinely fails — but it's wrapped in:

```python
@pytest.mark.xfail(strict=True, reason="#50: 50 free-form TODOs remain...")
```

`@pytest.mark.xfail` means **"I know this fails right now; mark it an *expected* failure so
it doesn't redden the suite, but keep it as a live reminder."** When #50 is finished and
the count hits zero the test starts *passing* — and because it's `strict=True`, an
unexpected pass (`X`) becomes a **real failure**, forcing whoever fixed it to delete the
marker. A self-clearing TODO tracker.

Two ways you'll see an `x`:

- **`x` in the per-test dots, or `1 xfailed` in the summary** → an expected failure; the
  suite is healthy; ignore it.
- **`F` in the dots / `1 failed` in the summary** → the real red you care about.

The trap: if you ever see **`X` (uppercase) or `1 xpassed`**, a test marked "expected to
fail" actually passed — usually a sign the underlying issue got fixed and the marker
should be removed.
