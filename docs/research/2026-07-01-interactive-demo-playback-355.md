# Research/spike #355 — interactive demo playback (skippable sections + wait-for-input pause)

**Agent:** ELDERBERRY · **Date:** 2026-07-01 · **Parent:** #308 · Builds on #351 (`--demo-speed`), #352 (caption dwell), #314 (demo playback), #356 (caption numbering).
**Scope:** consider/scope/spike only — no production code. Deliverable = this findings/design doc + a recommendation + proposed DEV children (filed only on go-ahead).

---

## TL;DR verdict

| Feature | Feasibility | Cost | Sim coupling | Recommendation |
|---|---|---|---|---|
| **Wait-for-input pause** (manual advance) | **Feasible — easy** | Presenter-only; ~1 method | **None** (golden-safe) | **Build first.** Direct generalization of the #352 dwell loop. |
| **Skippable sections** (→ jumps to next caption) | **Feasible — moderate** | Presenter signal **+** a small opt-in runner seam | None to the *sim*, but adds a runner↔presenter control channel | Build second, as its own DEV child. Mechanism = silent fast-forward (no cheaper jump exists). |

Both are **live-only** (video mode is non-interactive — N/A, per the issue). Neither touches the deterministic sim, so both stay golden-safe like #351/#352.

---

## Q1 — Where does input live? Can `show()` consume advance/skip/pause keys without coupling the sim?

**Yes, cleanly — and there is already precedent.** The playback input stream is fully separate from the sim's input stream:

- The **sim** reads inputs *only* through `run_battle`'s `frame_inputs` / `controller` path (`runner.py:143-150`) — a scripted `InputFrame` timeline compiled from the demo (`demo_timeline`). It never reads `pygame.event.get()`.
- The **presenter** already calls `pygame.event.get()` inside `show()` and its dwell loop (`presenters.py:72-74`, `86-90`), today only to catch `QUIT`. Consuming additional keys (→ / space) there reads from the *same* OS event queue but feeds *playback control*, not the sim. The two streams never mix.

So playback keys in the presenter are a clean seam with **zero sim coupling**. This is not speculative — the #352 dwell loop already pumps events mid-hold without any sim effect. Live-game controls (`game.py`) are a different code path entirely and are untouched (out of scope: no rebinding).

**Answer:** input lives in the presenter's event loop; adding advance/skip/pause keys does not couple the sim.

---

## Q2 — Skip vs the deterministic sim: what does "skip to next section" actually mean?

**The premise in the issue is correct: you cannot drop sim frames.** A fighter's state at frame N is the fold of all frames `0..N-1` through the statechart (`runner.py:151-157`: `p.update` → `resolve_player_push` → `attacks.update` → `process_hits` → `match.tick`). Skipping any of these desyncs the fighters and the captions (whose windows are frame-indexed).

Therefore **"skip to next section" = silent fast-forward**: keep running every sim frame, but **suppress rendering + display pacing** until the playback cursor reaches the next segment boundary, then resume normal rendering. Because Python runs the sim far faster than 60 FPS when it isn't pacing/rendering, the skipped span elapses near-instantly — desync-free by construction.

**Segment→frame boundaries already exist.** They are the caption windows: `demo_captions(demo)` yields one `Caption` per segment with `frames=(start, end)` (`demo.py:63-76`). The sorted list of segment starts is simply:

```python
boundaries = sorted(c.frames[0] for c in captions if c.frames)
```

"Next section" from the current frame `f` = the least boundary strictly greater than `f`.

**Is there a cheaper jump? No — and the two tempting alternatives are worse:**

1. *Random-access replay from stored snapshots.* `run_battle` already returns per-frame `snaps`, but `snapshot()` reduces state to golden primitives (`runner.py:82-102`) — not the live `Player`/`attacks` objects the renderer needs. Storing full renderable frames to allow scrubbing is a heavier, different architecture (essentially a recorded, scrubbable player ≈ video mode), which the issue rules N/A for interactivity.
2. *Teleport the sim to the boundary state.* Impossible without re-running the intervening frames — that's exactly what fast-forward does, just without the render/pace overhead.

**Answer:** fast-forward the sim silently through the skipped frames (suppress render + clock pacing), using the caption windows as boundaries. No cheaper mechanism exists.

---

## Q3 — Wait-for-input pause: feasible in `LivePresenter`, or does the runner need a pause hook?

**Feasible entirely in the presenter — no runner hook needed.** This is the single most important finding of the spike, and it is grounded in existing code.

The #352 caption dwell is *already* a "freeze the display for a while without advancing the sim" primitive that lives wholly inside `show()`:

```python
# presenters.py:86-90 — dwell hold (#352)
for _ in range(caption_hold_frames(self.captions, frame)):
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            raise KeyboardInterrupt
    self.clock.tick(...)          # re-present the SAME frame; sim does NOT advance
```

Control has not returned to the runner during this loop — the sim is frozen on frame `f` while the window stays live and quittable. **Wait-for-input pause is this exact loop with a different exit condition:** instead of looping a fixed `caption_hold_frames(...)` times, loop *until a resume key is pressed* (or QUIT). The freeze-frame guarantee, the event pumping, and the "sim doesn't advance" property all come for free from the dwell precedent.

Two flavors, both presenter-only:

- **Explicit manual-advance mode** (a `--demo-manual` / `pause_each_section` flag): at each caption's start frame, block until the viewer presses advance — self-paced reading, replacing the timed dwell.
- **Toggle pause** (space at any time): flips a `self.paused` flag; while set, `show()` spins the freeze loop until space is pressed again.

Neither requires the runner to expose a pause hook, because the pause happens *between* the runner handing frame `f` to the presenter and the presenter returning — the runner's loop is naturally suspended inside `show()`. **Golden-safe** for the same reason dwell is: it paces the display, never the sim.

**Answer:** feasible in `LivePresenter`; generalize the #352 dwell loop's exit condition. The runner needs no pause hook.

---

## Q4 — Presenter shape: new `InteractivePresenter`, or a flag/mode on `LivePresenter`?

**Recommend a flag/mode on `LivePresenter`, not a subclass.** Rationale:

- The interactive behaviors are *variations of pacing* — the same domain `LivePresenter` already owns (it already carries `cap_fps`, `overlay`, `captions`, `speed`, and the dwell loop). A subclass would duplicate the render body just to change the freeze/skip conditions.
- Pause composes with `--demo-speed` (#351) and dwell (#352) trivially: `speed` still sets `tick_fps` for the frames that *do* play; dwell becomes the *default* auto-advance timing that manual mode overrides. Manual pause and a fixed dwell are mutually exclusive per caption (manual wins when enabled) — a clean precedence rule.
- Skip's fast-forward needs the *runner's* cooperation regardless of presenter class (see Q2/Q5), so subclassing the presenter wouldn't localize the change anyway.

**Composition rules to encode:**
- `speed` (#351): unchanged — governs played frames; irrelevant during fast-forward (no pacing) and during a pause (frozen).
- `dwell` (#352): in **auto** mode, dwell holds as today. In **manual** mode, dwell is superseded by wait-for-input at each section start (don't double-hold).
- Skip during a dwell/pause: a → press should cancel the current hold and begin fast-forward to the next boundary.

**Answer:** flag/mode on `LivePresenter` (e.g. `interactive=` with `manual`/`toggle`), not a new class.

---

## Q5 — The one real architectural seam: the skip control channel

Pause is self-contained in the presenter. **Skip is the only feature that crosses the runner↔presenter boundary**, because the sim advance it must fast-forward is owned by `run_battle`, and future frames don't pre-exist — they're generated in the loop (`runner.py:137-159`). Control flows runner→presenter (the presenter is a passive sink called *after* each frame), so the presenter must signal *back*.

**Proposed minimal, opt-in seam** (byte-identical when unused):

1. **`show()` returns an optional intent.** Today it returns `None` implicitly; let it return `"skip"` when the viewer pressed → this frame, else `None`. `HeadlessPresenter`/`VideoPresenter` keep returning `None` — no signature break, the runner just reads `intent = presenter.show(...)`.
2. **`run_battle(..., boundaries=None)`** gains an optional sorted list of segment start frames (demo mode only; `None` everywhere else keeps the sim path untouched). The runner owns the frame math — "next boundary > f" — so the presenter stays dumb (reports *intent*, not target).
3. **Fast-forward loop in the runner:** on `intent == "skip"` with boundaries present, compute `ff_target = next boundary > f`; advance sim frames **without calling `presenter.show()`** (so no render, no clock tick → the sim runs at full speed) until `f == ff_target`, then resume normal `show()`.

`watch.py` wires it: it already builds `captions`, so it passes `boundaries=[c.frames[0] for c in captions if c.frames]` to `run_battle` in demo mode.

**Why report intent, not a target frame:** keeps the boundary list in one place (the runner) and avoids the presenter needing to reason about frame indices it only partially owns. It also keeps `show()`'s contract tiny (one nullable string).

**Coupling added:** one nullable return from `show()` + one optional `boundaries` kwarg on `run_battle`. Both default to the current behavior — golden goldens and the render-parity oracle stay byte-identical when interactivity is off.

---

## Q6 — UX (key bindings + on-screen hint)

Proposed default bindings (live-only):

| Key | Action |
|---|---|
| `→` / `Space` (context) | **Skip** to next section (fast-forward) / **advance** past a manual-pause hold |
| `P` or `Space` (toggle mode) | **Pause / resume** toggle |
| `Esc` / window close | Quit (existing `QUIT` path) |

Recommendation: pick **one** meaning for `Space` per mode to avoid overload —
- **manual-advance mode:** `Space`/`→` = advance to next section; no separate pause needed (every section is a pause).
- **toggle mode:** `Space` = pause/resume; `→` = skip section.

On-screen hint: a small bottom-right/HUD line drawn by the presenter (reuse `text_utils.render_text`, like `_draw_overlay`), e.g. `→ next · space pause · esc quit`, gated behind the interactive flag and ideally auto-hiding after a few seconds. This is pure overlay (golden-safe; only affects the live window, never video/goldens).

---

## Perceived ROI & sequencing

- **Pause (manual advance): High ROI, low cost.** Delivers most of the ask's value (a viewer reads each captioned beat at their own pace) with a presenter-only change that reuses the #352 loop. No new architectural seam.
- **Skip: Medium ROI, moderate cost.** Nice-to-have for jumping past a known beat; requires the runner↔presenter control channel. Lower marginal value than pause for a curated showcase (where you usually *want* to watch each beat), but the seam is small and reusable.

**Recommended order:** pause first (self-contained, high value), skip second (adds the one seam).

---

## Recommendation

**Feasibility verdict: both features are feasible and golden-safe.** Decompose into **two DEV children** of #308 (area:watch), sequenced:

1. **DEV (pause):** wait-for-input / manual-advance mode on `LivePresenter` — generalize the #352 dwell loop's exit condition to block on a resume key. Flags: `--demo-manual` (per-section pause) and/or a `Space` toggle. Presenter-only; regression test asserts the freeze loop exits on a synthesized key event and the sim frame index does not advance during the hold. **No runner changes.**
2. **DEV (skip):** skippable sections via silent fast-forward. Adds the opt-in seam — `show()` returns a `"skip"` intent; `run_battle(boundaries=…)` fast-forwards the sim (suppress render+pace) to the next boundary; `watch.py` passes `boundaries` in demo mode. Regression test: given boundaries and a synthesized → on frame `f`, the presenter is not called between `f` and the next boundary while `snaps` stays continuous (no dropped/duplicated sim frames).

Plus optionally a tiny **overlay-hint** follow-up (or fold it into #1).

**Both children remain unfiled pending explicit go-ahead** (per RULES.md → "Filing work": a suggestion is not authorization). This doc is the scope artifact; on go-ahead I'll file the two DEV children with the mechanisms above.

## Key code sites (for the DEV children)

- `pycats/sim/presenters.py:71-90` — `LivePresenter.show()` event loop + the #352 dwell hold (the loop to generalize for pause; the `show()` return for skip intent).
- `pycats/sim/runner.py:137-164` — `run_battle` frame loop (where fast-forward + the `boundaries` kwarg land).
- `pycats/sim/captions.py:51-59` — `caption_hold_frames` (the dwell-exit pattern pause mirrors).
- `pycats/sim/demo.py:63-76` — `demo_captions` (source of segment→frame boundaries).
- `watch.py:146-183` — demo wiring (passes `boundaries`; adds the interactive flag).
