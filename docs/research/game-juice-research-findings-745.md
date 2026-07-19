# Game juice in pygame — what the engine actually supports (#745)

**Ticket:** #745 (WRITER · `area:docs`) · **Agent:** DRAGONFRUIT · **Date:** 2026-07-19
**Parent:** #742 (rectangular-character liveliness survey — the design-space catalog this maps to code)

This is the **pygame-capability map** for the "juice" / game-feel techniques catalogued in #742:
which ones the engine supports, how, and which it lacks. It exists so future look-and-feel work
(squash/stretch, screen-shake, particles, hit-stop) starts from a concrete API map instead of
re-deriving it.

---

## What pygame actually supports (and doesn't)

pygame is an **immediate-mode 2D blitter** — you redraw every frame yourself. It has **no
skeletal/bones rigging, no tweening/easing library, no particle system, no scene graph, no
animation timeline.** So "bones" isn't a thing here — but you don't need it. Every technique in
the #742 survey is a few lines you write by hand each frame:

| Technique | How you do it in pygame |
|---|---|
| **Squash & stretch** | `pygame.transform.scale`/`smoothscale` for non-uniform scaling — or, since pycats draws *rectangles*, just vary the rect's `w`/`h` around an anchor point. Tip: conserve area (wider ⇒ shorter) so it reads as a squash, not a resize. |
| **Lean / tilt / rotation** | `pygame.transform.rotate` / `rotozoom` on a small surface; couple the angle to horizontal velocity for a "lean into the run." |
| **Screen shake** | Offset the whole-frame blit (a camera offset) by a random vector that decays to zero over ~50–300 ms. |
| **Particles** (dust, sparks) | Hand-rolled: a list of `{pos, vel, life, size, color}`, update + draw as tiny rects/circles, drop when `life ≤ 0`. Lightweight. |
| **Motion trails / afterimages** | Keep the last N positions and blit semi-transparent copies (a `Surface` with `SRCALPHA` + `set_alpha`), or fade a full-screen layer each frame. |
| **Hit-stop / freeze-frame** | Skip the sim update for a few frames while still rendering — trivial in a fixed-timestep loop, and huge for impact feel. |
| **Easing / anticipation / overshoot** | Write ~5-line helpers (`lerp`, `easeOutQuad`, `easeOutBack`) — no library. Overshoot easing is what makes squash/stretch feel springy. |
| **Flash / color pulse** | Modulate the fill color, or blit with `special_flags=pygame.BLEND_RGB_ADD` for an additive hit-flash. |

**Why this is easy for pycats specifically:** because fighters render as boxes, squash/stretch
(vary `w`/`h`) and lean (rotate a small surface) are nearly free, and particles are just more
little rects. That's exactly the cheap, high-leverage set the #742 findings doc flagged.

---

## Where it ties back

These are candidate follow-ups in #742's findings doc — squash-on-land, velocity-lean, landing
particles, screen-shake/hit-stop (and #567 idle breathing is already scoped). This doc is the
implementation-feasibility half: each row above is a self-contained DEV ticket when the direction
is worth pursuing, filed one-at-a-time.

## Further learning (game-feel references)

- *Juice it or lose it* — Jonasson & Purho, GDC Europe 2012 (live-juices a Breakout clone).
- *Secrets of Game Feel and Juice* — Game Maker's Toolkit (Mark Brown).
- *The Art of Screenshake* — Jan Willem Nijman / Vlambeer, 2013 (screen shake, hit-stop, recoil).
- DaFluffyPotato's pygame tutorials — hands-on particles / screenshake in pygame specifically.

*Note: the pygame API references above (`transform.scale`/`rotate`, `SRCALPHA` + `set_alpha`,
`BLEND_RGB_ADD`) are standard engine facts; the "no bones/tween/particles/scene-graph" points
describe pygame's core, which ships none of those subsystems.*
