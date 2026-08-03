# Project M framerate & timing model (fidelity findings)

> How Brawl / Project M gate frame rate and time, and what that means for a
> PM-faithful pycats. Companion to
> [brawl-projectm-fighter-states.md](./brawl-projectm-fighter-states.md).
>
> Confidence: the core facts here (60 Hz fixed timestep, integer-frame data,
> overload = whole-game slowdown, PAL = 50 Hz) are uncontroversial, long-
> established community knowledge (SmashWiki frame-data conventions, console
> behavior). This was NOT re-run through the deep-research harness; treat it as
> well-established background rather than adversarially verified claims.
> Date: 2026-06-21.

## TL;DR

**Project M is locked to a fixed 60 FPS.** It is a mod of *Super Smash Bros.
Brawl*, a fixed-timestep console game: simulation and display advance on the
same clock, one game tick per displayed frame at 60 Hz. There is no variable
frame rate and no separate "performance bandwidth" to tune. 60 is both the
target and the ceiling; there is no guaranteed floor — when the console can't
finish a frame in 1/60 s, the **entire game** (logic + visuals) slows down in
lockstep ("lag"/slowdown), then recovers.

## The model

- **Fixed timestep.** Every frame is exactly 1/60 s of game time. Physics,
  hitboxes, knockback, shield decay, dodge/intangibility windows are all computed
  once per frame. There is no separation of "simulation rate" vs "render rate" —
  they are the same clock.
- **60 is the ceiling, not exceeded.** On real hardware the game renders at the
  console's 60 Hz output (NTSC). It does not run faster than 60.
- **No floor — overload causes slowdown.** Heavy scenes (many particles/effects,
  4 players, item chaos, certain Final Smashes/stages) that can't render within
  1/60 s slow the whole game down together. It is not gated to a minimum frame
  rate; it just runs slower than real time when overloaded.
- **Region split.** The PAL (European) build runs at **50 FPS**, which is why PAL
  frame data differs slightly from NTSC. Project M inherits the NTSC 60 Hz model.
- **Everything is quantized to frames.** Move startup, active frames, recovery,
  intangibility, hitstun, shieldstun — all expressed in whole 60 Hz frames. This
  is why frame data is always integers (see
  [brawl-projectm-fighter-states.md](./brawl-projectm-fighter-states.md): shield
  depletion 0.28/frame, shieldstun `floor(damage × 0.345)` frames, etc.).
- **Emulator caveat.** Under Dolphin you can "uncap," but that does not raise the
  in-game frame rate — it speeds up or slows down the entire emulated console
  clock (the game runs in fast-/slow-motion). The authentic behavior is 60-locked.

## Implications for pycats

pycats already uses this exact model: a fixed-timestep 60 FPS loop
(`config.FPS = 60`), deterministic per-frame logic, no RNG, and integer-frame
timers (`DODGE_TIME`, `HURT_TIME`, `STUN_TIME`, `PLAYER_ATTACK_DURATION`, …).
That is the correct foundation for PM fidelity. Concretely:

1. **Keep the logic locked to 60 Hz.** All mechanics/frame data are *defined* at
   60 Hz; running the simulation faster or slower would change the mechanics.
   The right design is "advance exactly one fixed 60 Hz tick per rendered frame,"
   which is what the loop and the statechart `"tick"` event already do.
2. **Headroom is for holding 60, not exceeding it.** The benchmark
   ([statecharts-benchmark](../superpowers/specs/2026-06-21-statecharts-benchmark-design.md))
   shows the sim runs thousands of FPS with huge headroom, and the tail/body
   render caching widened it further. The goal of that headroom is to *never miss*
   the 60 Hz tick (avoid Brawl-style slowdown), not to run above 60.
3. **Measure uncapped, ship capped.** Separate measuring achievable rate from
   running the game: `bench.py` / `bench_render.py` and `watch.py --uncapped`
   measure headroom; the shipped game stays paced to 60.
4. **Frame data must be integer frames.** As PM mechanics land, every timing
   value (startup/active/recovery/hitstun/shieldstun/intangibility) should be
   stored and counted in whole frames, matching how Brawl/PM and all published
   frame data express them.

## Open follow-ups

- PAL/50 Hz is out of scope (pycats targets the NTSC 60 Hz model).
- If a future "training mode" wants slow-motion or frame-step, implement it as a
  *tick-rate multiplier on the same fixed timestep* (run N fewer ticks per real
  second), never as variable-timestep logic — to preserve determinism and frame
  data.
