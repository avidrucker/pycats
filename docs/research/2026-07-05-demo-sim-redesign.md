# Demo / sim playback redesign — dual-surface (CLI + in-game tutorials) + one interaction model

**Ticket:** #507 (architect, design-only). **Parent:** #308. **Supersedes** the interactive-playback
design of #355 and #393's shipped interaction code. **Date:** 2026-07-05. **Author:** GRAPE (architect hat).

> **Status: proposed — awaiting human/architect ratification.** #514 and #515 are pre-filed and
> **blocked** until this design is confirmed thorough and well-designed. Nothing here is implementation.

---

## 1. The problem in one line

Make **one** demo definition + interaction model drive **two** surfaces — the terminal
`watch.py --demo …` presenter and a future in-game tutorial screen — without growing two copies
of the pause/exit logic, and without breaking golden byte-identity.

## 2. The central finding: the two surfaces have inverted control flow

This is the fact the whole design turns on, so it goes first.

| | **CLI (`watch.py`)** | **In-game (`ScreenStateManager` FSM)** |
|---|---|---|
| Who owns the loop | `run_battle` (`sim/runner.py`) — a tight pull loop that runs to completion or `KeyboardInterrupt` | the screen engine (`systems/screen_engine.py`, ADR-0002) — one `engine.update(ctx)` per game-loop frame |
| Who advances the sim | the runner, every iteration | the `playing`/tutorial state's `on_update`, which calls `battle.step` **once per frame** |
| How a "hold" works today | `LivePresenter._hold` **blocks the runner** inside `show()`, looping `caption_hold_frames` ticks (golden-safe *because* the runner is frozen — the sim can't advance) | you **cannot block** — the loop must keep pumping input and rendering every frame |
| How input arrives | `LivePresenter` reads **raw** `pygame.event.get()` inside `show()`/`_hold()` | a normalized `InputFrame` (held/pressed/released sets) is threaded into `ctx` |
| How exit works today | `_consume_advance` returns `"quit"` on tap-Esc/QUIT → `raise KeyboardInterrupt` (#393) | `_tick_esc_hold` counts frames while `K_ESCAPE in frame_input.held`; `esc_hold_complete()` pops one screen level (#453), with a progress arc |

**Consequence.** The blocking-`_hold` pattern that works for the CLI is illegal inside the FSM.
Any design that "embeds `run_battle` inside the tutorial screen" (ticket option 1a) inherits the
blocking loop and fights the FSM — the screen would go unresponsive for the whole demo, and
hold-Esc-2s back-out could not run. So the seam is **not** "reuse the runner's loop"; it is
**"decouple *advancing one frame* from *the loop that calls it*, and make the interaction logic a
pure per-frame reducer that neither blocks nor reads raw events."**

## 3. Recommended design

Two extractions plus one screen. Everything else (`demo.py`, `captions.py`, `input_script.py`,
`compile_timeline`, the `Demo`/`DemoSegment` data, `demo_timeline`/`demo_captions`) is **already
surface-agnostic and is reused unchanged** — a demo is plain data today, which is exactly why one
definition can serve both surfaces.

### 3a. A pure, non-blocking interaction reducer (the shared seam)

Extract the interaction logic out of the *blocking* CLI loop into a **pure per-frame reducer** that
both surfaces tick once per frame with a **normalized `InputFrame`**:

```
PlaybackController.tick(frame_input) -> Action        # Action ∈ {ADVANCE, HOLD, END}
```

- It holds the dwell countdown and the exit state. No pygame calls, no window, no clock — pure, so
  it is unit-testable and behaves **identically** on both surfaces by construction.
- **Any-key-ends-dwell (#514)** lives here as a property of the dwell: while a caption's dwell is
  counting down, a non-empty `frame_input.pressed` (any KEYDOWN) zeroes the remaining count → next
  `tick` returns `ADVANCE`. "Do nothing → it advances itself; press anything → skip the wait."
- **Hold-Esc-2s (#515)** lives here too, but delegates the timer to the shared `EscHoldTimer`
  below so CLI and in-app share one threshold + one progress semantic.

The reducer answers **Q3** (the pause model): interruptibility is a property of the *dwell itself*,
not a presenter mode — so it applies everywhere the dwell does.

### 3b. Extract `EscHoldTimer` from `ScreenStateManager` (#453) and share it

`_tick_esc_hold` / `esc_hold_complete` / `esc_quit_progress` in `screen_manager.py` already are the
correct non-blocking pattern: count frames while `K_ESCAPE` is *held*, reset on release, fire at
`esc_quit_hold_frames` (120 = 2s@60), expose a 0..1 progress for the arc. Lift that into a small
reusable `EscHoldTimer` (pure: `tick(held) -> None`, `.complete`, `.progress`). Then:

- `ScreenStateManager` uses it exactly as today (no behavior change — a pure refactor, guarded by
  the existing screen-parity trace tests).
- The CLI `PlaybackController` uses the **same** `EscHoldTimer` for its hold-Esc-2s, so the terminal
  gets the identical 2-second threshold **and** the progress-arc feedback (reuse
  `render_esc_quit_progress`'s arc). This is **Q2's** "identical on both surfaces" — same timer,
  same input field (`held`), same threshold — achieved by sharing code, not by re-implementing.

### 3c. Input normalization — the one adapter the CLI needs (Q2)

The FSM already has `InputFrame`. The CLI reads raw events. So the **only** surface-specific glue is
a per-frame normalizer on the CLI side: fold this frame's `pygame.event.get()` into an
`InputFrame`-shaped value (held set updated from KEYDOWN/KEYUP, `pressed` = this frame's KEYDOWNs,
plus a QUIT flag). Feed that to the reducer. Both surfaces then hand the reducer the same shape →
identical `any-key` and `hold-Esc` semantics with zero duplicated decision logic.

### 3d. In-app hold-Esc composes with #453 by being the same ladder rung (Q2)

In-app, a running tutorial is **just another screen on the ladder**. Holding Esc there should back
out one level (tutorial → tutorial menu → main_menu) — which is *exactly* what every other state's
back-guard already does via `esc_hold_complete()`. So **the in-app tutorial adds no second timer**:
its back-out guard reads the ScreenStateManager's existing esc timer like `options`/`char_select`
do. The reducer's hold-Esc branch is only exercised on the **CLI** surface (which has no
ScreenStateManager); sharing `EscHoldTimer` keeps the two identical. They compose cleanly precisely
because in-app we do **not** run the reducer's timer — we reuse the screen ladder's.

### 3e. A steppable runner — deferred, and needed only for the in-game surface

To run a demo *inside* the FSM (one sim frame per `on_update`), the sim advance must be callable one
frame at a time. Today `run_battle` fuses "advance one frame" with "the loop." Factor the loop body
into a **steppable** form (a generator yielding one snapshot per frame, or a `BattleStepper.step()`);
`run_battle` becomes a thin loop over it, preserving its current signature and **byte-identical**
output (same fold order: update players → `resolve_player_push` → `attacks.update` → `process_hits`
→ `match.tick` → `snapshot` → `presenter.show` → stop check). The in-game tutorial screen is then a
*different* loop over the same stepper, driven by the FSM.

**This extraction is only required for the in-app surface, which is deferred (ticket: "In-app —
later slice").** The near-term CLI items (#514/#515) keep using the existing blocking `run_battle`
untouched. Do not pull this refactor forward into the v1 slices.

### 3f. Presenter interface, reused; loop owner, swapped (Q1 answer)

Q1 asks which of (a) embed-runner-in-screen, (b) presenter-interface-the-screen-implements, (c)
runner-emits-frames. The answer is **(c) + (b), explicitly not (a)**:

- **(c)** the runner becomes steppable (3e), so the *loop owner* differs per surface;
- **(b)** both surfaces draw through the same presenter contract
  (`show(platforms, players, attacks, frame, inputs)`). The in-game presenter is a `LivePresenter`
  sibling that draws to the game's existing surface and **does not own the clock or the hold** (the
  FSM owns cadence; the reducer owns interaction);
- **not (a)** — embedding the blocking loop in the screen is the trap identified in §2.

The pause/exit logic lives in **neither** presenter — it is the reducer (3a), shared.

## 4. The tutorial series, minimal v1 (Q4)

A new `tutorial` rung on the `ScreenStateManager` ladder, reachable from `main_menu` via a
"Tutorials" entry:

- **Tutorial menu** — lists the registered `DEMOS` (already a name→`Demo` registry) as a browsable
  next/prev/select menu. Hold-Esc-2s → back to `main_menu`.
- **Tutorial playback** — selecting a demo runs it as an in-game sim via the steppable runner (3e) +
  a game-surface presenter (3f) + the shared reducer (3a). Hold-Esc-2s → back to the tutorial menu.

**Minimal v1 = menu + single-demo playback + hold-Esc back-out.** Progress tracking, in-playback
next/prev between demos, and completion state are **deferred** (later slices, filed one at a time).

## 5. Disposition of #393's shipped code (Q5)

| Symbol (`sim/presenters.py`, `watch.py`) | Fate | Why |
|---|---|---|
| `--demo-manual` flag; `interactive="manual"` | **Remove** | The new dwell is always timed + auto-advancing; there is no indefinite wait-for-key. #393's model is superseded. |
| `_wait_for_advance`, `_consume_advance`, `ADVANCE_KEYS`, `MANUAL_HINT_TEXT`, `_draw_manual_hint` | **Remove / reshape** | Replaced by the reducer's `any-key-ends-dwell` (#514) + `EscHoldTimer` (#515). Tap-Esc-quit is gone (replaced by hold-Esc-2s). |
| `LivePresenter._hold`'s timed loop (#352) | **Reshape** | Dwell length still = `caption_hold_frames`, but the loop becomes reducer-driven (any-key can end it early). |
| `caption_hold_frames` (#352), `dwell`/`dwell_at` (#412) | **Keep** | Dwell length is unchanged; the reducer only permits an early exit. |
| `frames_per_output`, `tick_fps`, `--demo-speed` (#351) | **Keep, unchanged** | Speed paces the *display tick*, not the dwell; any-key short-circuits the countdown regardless of speed (composes with Q3). |
| `render_esc_quit_progress` arc (#453) | **Reuse** | The CLI hold-Esc gets the same progress-arc feedback. |

## 6. Golden-safety (the non-negotiable constraint)

- The reducer is instantiated **only** on the live interactive path (`LivePresenter` + a real
  window + interactive on). `HeadlessPresenter`, `VideoPresenter`, `ScreenshotPresenter` never touch
  it. Goldens are produced headless → **byte-identical, no regen**.
- Even on `LivePresenter`, non-interactive playback feeds the reducer empty input every frame → the
  dwell always runs its full `caption_hold_frames` → identical to today.
- The steppable-runner extraction (3e) is a pure factor-out with **no change to fold order** — the
  existing golden + render-parity tests are its regression guard (must stay green, no regen). This
  is the `#352`/`#394` discipline preserved.
- The fixed-timestep invariant (#166/#80) is untouched: any "skip" is a display short-circuit of a
  *presentation* dwell, never a sim-frame jump. (Skip-to-next-section — a real fast-forward of
  gameplay — stays out of scope at #508.)

## 7. Follow-on implementation tickets (outline — file one at a time, after ratification)

Lazy decomposition. **Do not file these until this design is ratified.** #514/#515 already exist.

1. **#514 — DEV: any key ends a caption pause early (CLI, near-term, v1).** Introduces the
   reducer's interruptible-dwell in `LivePresenter`; CLI-local; blocking `run_battle` unchanged.
2. **#515 — DEV: hold-Esc-2s to exit the CLI run (near-term, v1).** Extracts `EscHoldTimer` from
   `screen_manager.py`, uses it in the reducer, removes `--demo-manual`/tap-Esc/`_wait_for_advance`
   machinery, adds the CLI progress arc.
   - **⚠ Sequencing:** #514 and #515 both edit `LivePresenter._hold` / the interaction region of
     `sim/presenters.py` — a **same-function collision**. Run them **sequentially (#514 → #515),
     not in parallel**, or a fleet merge will conflict.
3. *(later, deferred — not v1)* **Steppable-runner extraction** (3e) — golden-safe factor-out;
   prerequisite for the in-game surface only.
4. *(later, deferred)* **In-game tutorial screen + menu** (§4) — the `tutorial` ladder rung, using
   the shared presenter contract + reducer; hold-Esc back-out wired to the existing screen ladder.
5. *(post-v1, already filed)* **#508 — skip-to-next-section** — a *distinct* key from pause-ending;
   a real gameplay fast-forward, out of scope here.

## 8. Why this satisfies the evaluation criteria

- **One demo definition, two surfaces, no duplicated interaction logic** — the demo data is already
  shared; the interaction logic is a single reducer (3a) + one `EscHoldTimer` (3b).
- **Identical input model CLI vs in-app** — both feed the reducer a normalized `InputFrame`; the CLI
  needs one thin normalizer (3c), nothing more.
- **Golden-safety preserved** — reducer is live-path-only; steppable extraction keeps fold order
  (§6).
- **Minimal new surface area** — two small pure extractions + one screen; everything in `demo.py` /
  `captions.py` / `input_script.py` is reused as-is.
- **In-app hold-Esc composes with #453 rather than fighting it** — the tutorial is just another
  ladder rung reading the existing esc timer; no competing second timer (3d).

## 9. Out of scope

- Implementation (this is design-only).
- Skip-to-next-section (#508, post-v1).
- Tutorial progress tracking / in-playback demo browsing (deferred later slices, §4).

**Refs:** #507 #308 #355 #393 #394 #453 #351 #352 #412 #314 #514 #515 #508
