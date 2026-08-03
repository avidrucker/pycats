# Screen / camera / map sizing — findings (#45)

> Read-only scoping research for the display + camera system: multi-resolution
> support, fullscreen, and a PM-style in-battle camera. Informs #15 (fullscreen
> wiring) and #18 (screen system). Companion to
> [pm-framerate-fidelity.md](./pm-framerate-fidelity.md) and
> [brawl-projectm-fighter-states.md](./brawl-projectm-fighter-states.md).
>
> Confidence: the **pycats grounding** (Q1–Q3) is read directly from the code at
> the commit below and is high-confidence. The **Project M camera** section (Q4)
> is well-established community knowledge (SmashWiki) plus the standard
> bounding-box camera pattern — it was NOT run through the deep-research harness;
> treat it as sound background, not adversarially-verified numbers.
> Date: 2026-06-25. Code as of `main` @ ab150ec.

## TL;DR

- **Resolution independence is already the architecture and already works.** The
  sim runs at a fixed 960×540; only the *final blit* scales to the display
  (integer-preferred, letterboxed). Mechanics and framerate never change with
  window size. **Q2 is "expose what already exists," not "build it."**
- **Fullscreen already works at runtime** — `F11` toggles it, `ESC` exits it
  (`game.py:440-444`), with an on-screen hint on char-select. The issue's
  grounding ("scaffolded, not wired to a control") is **out of date**. So #15 is
  really *menu option + windowed-scale presets + persisting the choice*, not
  first-time wiring.
- **There is no camera, and the stage is hard-coupled to the screen.** Blast
  zones are defined as `screen ± BLAST_PADDING` (`player.py:358-363`), so a
  larger-than-screen map is **impossible today** without decoupling KO bounds
  from `SCREEN_WIDTH/HEIGHT`. **Recommendation: stay single-screen for now;**
  a camera is a real feature, not a tweak — defer behind combat (#38/#67).
- A PM-style camera, if/when built, is a **presentation-only viewport layer**
  between sim coords and `render_battle`. The deterministic sim is untouched, so
  it's golden-safe in principle — **but it changes rendered pixels**, so it needs
  its own golden baselines and must be defaultable to identity (no-camera) to
  keep existing snapshots valid.

---

## Q2 — Multiple screen sizes without changing mechanics/framerate

**Already solved.** The pattern is fixed internal resolution + scale-to-fit:

- The deterministic sim and every mechanic run at a fixed **960×540**
  (`SCREEN_WIDTH/HEIGHT`, `config.py:19`) at a fixed **60 FPS** (`FPS`,
  `config.py:20`). Nothing in the sim reads the display size.
- All drawing targets a 960×540 surface chosen by `get_render_surface()`
  (`game.py:337-339`): in windowed mode that's the window itself; in fullscreen
  it's an off-screen `game_surface`.
- `present_frame()` (`game.py:342-374`) does the only size-dependent work: in
  fullscreen it scales `game_surface` up (integer `scale_by` when the factor is a
  clean ≥2× integer, else `transform.scale`) and blits it centred with
  letterbox offsets; in windowed mode it just `flip()`s.

**Why this is the right pattern:** physics, timers, knockback, and the golden
oracle all live in sim space and are *invariant* to the display. Only the last
blit scales. This is exactly the resolution-independence model PM-style fixed
-timestep games want (see [pm-framerate-fidelity.md](./pm-framerate-fidelity.md)).

**What's missing (the actual #15/#18 work):**
- No **windowed-scale presets** (e.g. 1×/2×/3× → 960×540, 1920×1080, 2880×1620).
  The window is locked to 1× (`game.py:145`). Adding presets is "open the window
  at `N×` and set `scale_factor`", reusing the existing fullscreen scale/letterbox
  math — no sim changes.
- No **settings/menu surface** for any of this — only the `F11` hotkey. That UI
  belongs to the screen system (#18).
- **Input mapping caveat:** the game is keyboard-only today, so scaled/letterboxed
  output has no coordinate bugs. The moment any **mouse/touch** input is added,
  clicks must be mapped display→game by inverting `scale_factor` + `offset_x/y`.
  Flagging now so it's designed in, not retrofitted.

## Q3 — Is fullscreen an option currently?

**Yes — it works at runtime, today.** `toggle_fullscreen()` (`game.py:290-333`)
switches `pygame.display.set_mode` between a 960×540 window and a borderless
`(0,0) FULLSCREEN` surface, recomputing `scale_factor`/offsets. It's bound to
`F11`, with `ESC` exiting fullscreen, in the main loop (`game.py:440-444`), and
char-select shows a "F11: Toggle Fullscreen" hint (`game.py:480-484`).

The only thing that's "dormant" is the **default**: `start_fullscreen = False` is
hardcoded (`game.py:117`). So the residual #15 work is: a menu toggle (not just a
hotkey), windowed-scale presets, and persisting the preference — all UI/state, no
new rendering primitive.

## Q1 — How big can/should the map be? Single-screen vs camera'd larger map

**Today the playfield IS the screen** — one static 960×540 view, no camera, no
scroll. The hard constraint is the **blast zone**: `_outside_blast_zone()`
(`player.py:358-363`) KOs a fighter when its rect leaves
`[-BLAST_PADDING, SCREEN_WIDTH+BLAST_PADDING] × [-BLAST_PADDING, SCREEN_HEIGHT+BLAST_PADDING]`
(`BLAST_PADDING = 50`, `config.py:186`). KO geometry is therefore **defined in
screen coordinates** — the stage cannot be bigger than the screen by
construction. Platforms are likewise laid out relative to `SCREEN_WIDTH/HEIGHT`
(`config.py:65-104`).

**Recommendation: keep single-screen stages for now.** Rationale:
1. A larger map is gated on *two* decouplings, not one: (a) blast zones must move
   from `SCREEN_*` to explicit **stage/world bounds**, and (b) a **camera/viewport
   layer** must map world→screen for every draw. Both are real features.
2. The current combat tuning (knockback launch/decay, `config.py:57-63`) was
   sized to "pycats' 960px stage." Changing stage size reopens that tuning and
   the off-stage launch spec (#51, currently blocked).
3. There is live structural work in the same files (D1 Player decomposition,
   #69/#79). Adding a world/camera concept now would collide and churn.

When a larger map *is* wanted, the clean order is: **first decouple blast zones
into stage bounds** (small, sim-side, testable in isolation), **then** add the
camera (presentation-side). Don't do them together.

## Q4 — How Project M / Brawl handle the in-battle camera

PM inherits Brawl's **automatic framing camera**: it continuously pans and zooms
so all active fighters stay on screen ([SmashWiki: Camera](https://www.ssbwiki.com/Camera)).
The well-established shape of that algorithm (and the standard way to build one):

1. **Bounding box** — each frame, compute the AABB enclosing all live fighters
   (and often important objects), expanded by a fixed **margin** so nobody hugs
   the edge.
2. **Zoom to fit** — derive the zoom/scale so that box fits the viewport aspect
   (the limiting axis wins), then **clamp** to `[min_zoom, max_zoom]`: a max
   zoom-*in* for when players are close (so it doesn't get claustrophobic) and a
   max zoom-*out* cap. Brawl's lack of a tight out-cap is exactly why huge stages
   (Temple, 75m, New Pork City) "zoom out excessively."
3. **Center / pan** — target the box center; on stages larger than the view this
   is what produces panning.
4. **Smoothing** — lerp both camera position and zoom toward their targets each
   frame (critically-damped / exponential ease) so motion is smooth, not jerky.
   Tuning the lerp rate is most of the "feel."
5. **Off-screen indicator (the "magnifying-glass bubble")** — when the clamp
   prevents showing a fighter (they're past max zoom-out), Smash draws a small
   framed bubble at the screen edge showing that fighter, so a launched player
   stays legible. This is a *fallback* for when framing alone can't keep everyone
   in view.

**How it would fit pycats' fixed-resolution determinism:**
- A camera is **purely presentational**: a `world→screen` transform
  `(scale, offset)` applied where `render_battle` currently draws sprite
  `rect`s **verbatim** in world coords. Every draw site uses `p.rect` directly
  today, so the seam is one transform threaded into `render_battle` (and the
  attack/HUD draws), *not* a sim change.
- **Determinism is preserved** *iff* the camera reads sim state but never feeds
  back into it — KO/blast logic must stay in world/stage coords (see Q1), never
  "off the visible screen." If KO ever keys off the camera, replays/goldens break.
- **Golden implications:** the golden oracle snapshots *rendered* surfaces, so a
  camera changes pixels and would invalidate every battle snapshot. Mitigation:
  the camera must default to an **identity transform** (full-stage, no zoom) that
  reproduces today's framing byte-for-byte, with the dynamic camera opt-in and
  given its **own** golden baselines. Frame-rate is unaffected (camera math is
  O(#fighters)/frame).

---

## Recommended follow-on work (file one slice at a time, per RULES)

These are *candidates*, not pre-filed tickets — lazy decomposition per the #50
lesson. Ordered by value/independence:

1. **#15 (existing): menu fullscreen toggle + windowed-scale presets.** Pure
   UI/state on top of the working scale path. Highest value, lowest risk, no sim
   changes. The natural next ticket.
2. **#18 (existing): screen system** owns the settings surface that hosts the
   above (display options live there, not on a hotkey).
3. **NEW (when larger maps are wanted, gated behind combat): decouple blast
   zones from `SCREEN_*` into explicit stage/world bounds.** Sim-side, testable
   in isolation, prerequisite for any camera. *Do not file yet* — only once a
   bigger stage is actually on the roadmap.
4. **NEW (after #3): presentation-only camera/viewport layer** (bounding-box
   framing + clamp + lerp + off-screen bubbles), default-identity for golden
   safety. Largest, file last, only after #3 lands.

**Do not bundle 3+4.** Decouple-then-camera; each is independently shippable and
testable.

## Sources

- [SmashWiki — Camera](https://www.ssbwiki.com/Camera) (Brawl auto-framing /
  zoom-to-show-all-players; excessive zoom-out on large stages)
- [Source Gaming — Smash Bros. Dojo: Camera Mode](https://sourcegaming.info/2016/05/18/camera/)
- [Smashboards — how the in-game camera zoom works](https://smashboards.com/threads/how-does-the-zoom-on-the-ingame-camera-work-exactly-and-is-it-possible.398848/)
- [GameDev.net — "Smash Bros style camera"](https://gamedev.net/forums/topic/672978-smash-bros-style-camera/)
  (standard bounding-box → zoom-to-fit → clamp → lerp pattern)
- pycats code: `pycats/config.py`, `pycats/game.py`, `pycats/entities/player.py`,
  `pycats/render_battle.py` (read @ ab150ec)
