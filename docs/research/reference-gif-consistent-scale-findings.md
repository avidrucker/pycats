# Reference-GIF consistent character scale — findings (#1153)

**Ticket:** #1153 (research · area:display). **Asked:** can the brawllib_rs reference
GIFs be produced so a character is drawn at a **consistent size across every GIF of that
character**, instead of today's per-subaction auto-fit that shrinks the character in
movement-heavy animations?

**Answer (short):** The shrinking is real and comes from a **per-subaction auto-fit
camera** in brawllib_rs — verified from source. Consistent scale **is** achievable, by
three distinct routes (fixed-camera re-render · post-process rescale · editor-side
auto-scale), with different effort/fidelity trade-offs. This doc reports the mechanism +
the option space only; no route is picked here (a follow-on ARC/decision + DEV ticket does
that).

Sources are pinned to the local brawllib_rs clone at `~/Documents/Study/Rust/brawllib_rs`
@ `e8dc833` (2025-12-18), read on 2026-08-02. Empirical GIF measurements are from the
gitignored `repros/mario-gifs/` set.

---

## Q1 — Is the camera per-subaction or fixed? → **per-subaction auto-fit (confirmed)**

The GIF renderer builds the camera **from the subaction's own bounding extent**, so each
subaction gets its own framing. Primary quotes:

`src/renderer/gif.rs` (`render_gif`), inside the per-frame loop:

```rust
let camera = Camera::new(subaction, width, height);
```

The same `subaction` is passed every frame, so the camera is **fixed within one GIF** (the
character does not re-zoom frame-to-frame — matching the recipe's "silhouette height stays
~constant across frames" note). But it is rebuilt **per subaction**, from that subaction's
motion:

`src/renderer/camera.rs` (`Camera::new`):

```rust
let mut extent = subaction.hurt_box_extent();
...
extent.extend(&subaction.hit_box_extent());
extent.extend(&subaction.ledge_grab_box_extent());
```

`src/renderer/camera.rs` (`new_from_extent`) — the extent then sets the camera distance:

```rust
let radius = (extent.up - extent_middle_y).max(extent.right - extent_middle_z);
let fov = 40.0;
let fov_rad = fov * consts::PI / 180.0;
let mut camera_distance = radius / (fov_rad / 2.0).tan();
```

So a subaction whose motion sweeps a **larger extent** → larger `radius` → larger
`camera_distance` → the camera sits farther back → **the character renders smaller**. That
is exactly the reported effect ("moves a lot → appears as a smaller version of himself").

An upper clamp exists but only for extreme moves:
`src/renderer/camera.rs` — `const MAX_DIM: f32 = 400.0;` clamps each extent dimension to
400 render-units (comment: "e.g. P+ ivy solar beam"). Below that, framing is proportional
to motion, so ordinary attacks/getups still shrink.

The canvas itself is a fixed **400×300** (`src/renderer/gif.rs`: `let width: u16 = 400; let
height: u16 = 300;`) — so the canvas is constant and the *character's fraction of it* is
what varies. This matches every GIF in `repros/mario-gifs/` measuring 400×300.

### Empirical confirmation (Pillow silhouette height, `repros/mario-gifs/`)

Body pixel-height (non-black silhouette) per GIF — `maxBodyH` is the character at full
extension, the best cross-GIF scale proxy:

| GIF (subaction) | canvas | max body-H px | note |
|---|---|---|---|
| `mario_Wait1` (idle) | 400×300 | **275** | low motion → large |
| `mario_DownStandU` (getup) | 400×300 | 280 | low motion → large |
| `mario_Attack11` (jab) | 400×300 | 270 | low motion → large |
| `mario_AttackAirF` (fair) | 400×300 | 252 | some travel |
| `mario_AttackS4S` (fsmash) | 400×300 | 185 | more travel → smaller |
| `mario_AttackDash` (dash attack) | 400×300 | **125** | high travel → smallest |

Same Mario, same 400×300 canvas, rendered **275px** tall in `Wait1` vs **125px** in
`AttackDash` — a **~2.2× scale swing** driven entirely by motion extent. This is why the
editor author must currently re-scale each GIF by hand to line the reference up against the
fighter.

(Measurement script archived in this ticket's scratch; it reuses the recipe's silhouette
method. The min/max spread *within* one GIF reflects pose/limb extension and edge-on
frames, not per-frame re-zoom — the camera is fixed within a GIF per the source above.)

---

## Q2 — Can it render at a fixed camera/scale? → **yes, via a small local Rust change**

**No existing flag.** `examples/gif_generator.rs` exposes only `-d`/`-m`/`-f`/`-a`
(brawl dir, mod dir, fighter, subaction) — no camera/scale/zoom option. The render path
(`render_gif` → `Camera::new(subaction, …)`) hardcodes the per-subaction auto-fit; there is
no parameter to override it.

**But the pieces for a fixed camera already exist:**

- `Camera::new_from_extent(extent, w, h, facing)` is a separate constructor that accepts an
  **arbitrary** extent — feed it a shared extent and every subaction frames identically.
- `HighLevelFighter` exposes `pub subactions: Vec<HighLevelSubaction>` and each subaction
  has `hurt_box_extent()`, so a **per-fighter union extent** (or a fixed chosen extent) is a
  trivial iterate-and-`Extent::extend` — there is no fighter-wide helper today, but building
  one is a few lines.

Two shapes of fixed camera:

1. **Shared union extent** — frame every subaction to the union of all the fighter's
   subaction extents. Guarantees the character never leaves the frame, at the cost of the
   whole set being zoomed out to fit the single most-travelling move (so all GIFs get
   smaller-but-equal).
2. **Fixed units-per-pixel** — pick a constant world-units-tall window centred on the
   fighter origin (independent of motion). The body renders at a **constant pixel size**
   across the set; high-motion moves may travel out of the 400×300 frame (clipping). This
   is the closest to "Mario is always the same size."

Either needs: the gated brawllib_rs env live + a local change to `render_gif` (or a new
example that passes a pre-built `Camera`) + a re-render of the affected sets.

---

## Q3 — Post-process alternative (pure Python) → **feasible, some quality loss**

Instead of re-rendering: measure each existing GIF's character height (the recipe's Pillow
silhouette method — Pillow is already a pycats dep, and the numbers above prove it works)
and **rescale every GIF to a shared target body height**. No Rust, no gated env, operates
on the GIFs already in `repros/<source>-gifs/`.

Trade-offs:
- **Upscaling loss:** a zoomed-out small character (e.g. `AttackDash` at 125px) upscaled to
  ~275px is interpolated — softer than a native re-render at the right scale.
- **Clipping is unrecoverable:** if a high-motion source already clips at the canvas edge,
  post-process cannot restore what was never drawn.
- **Deterministic + cheap** otherwise; re-runnable over a whole set in seconds.

---

## Q4 — Editor-side auto-scale → **feasible, non-destructive**

Same measurement as Q3, but applied at **view time in the editor** rather than baked into
new files. `pycats_editor/gif_map.py` resolves the reference GIF per character+move, and the
editor already has a pan/zoom transform the author drives by hand. The editor could instead
**derive a per-GIF scale factor automatically** (from silhouette measurement on load, or
from a rendered scale-metadata sidecar) and apply it, removing the manual per-GIF step
without touching the source GIFs.

Trade-offs:
- Non-destructive (source GIFs unchanged); no re-render, no new asset files if measured on
  load.
- Same pixel-fidelity ceiling as Q3 (it works from already-rendered pixels).
- Per-GIF silhouette measurement at load has a small runtime cost; a cached sidecar avoids
  repeating it.

---

## Q5 — Effort + prerequisites

| Route | Env needed | Change surface | Re-render? | Fidelity | Relative effort |
|---|---|---|---|---|---|
| **Q2 fixed-camera render** | gated brawllib_rs env (Rust, wgpu, PM `.pac` data) | Rust: `render_gif` / new example + union-or-fixed extent | yes, all sets | highest (native at correct scale) | highest |
| **Q3 post-process rescale** | none (Pillow, already a dep) | pure-Python script | reprocess existing GIFs | medium (upscale loss) | medium |
| **Q4 editor-side auto-scale** | none | pure-Python in editor (`gif_map.py` / view transform) | none | medium (works from rendered px) | lowest |

Re-render cost for Q2: `gif_generator` renders **one subaction per invocation**; the Mario
set alone is **356 GIFs** in `repros/mario-gifs/`, so a full re-render is a batch of that
order per fighter (seconds each on GPU, but many invocations).

---

## Recommendation shape (for the downstream decision — not decided here)

Two dimensions the decider (Avi) will weigh:
1. **Where** to fix scale: at render (Q2, highest fidelity, gated env + Rust + full
   re-render) vs. in Python without re-rendering (Q3 bake / Q4 view-time).
2. **Which fixed model**: shared union extent (never clips, all smaller-but-equal) vs. fixed
   units-per-pixel (true constant size, may clip high-motion moves).

A cheap first step regardless of route: Q4 (editor-side auto-scale) removes the manual
per-GIF step immediately with no re-render and is fully reversible — it can stand alone or
buy time for a Q2 re-render later.

---

## Blocked sources

None. All primary evidence came from the **local** brawllib_rs clone (read-only) and the
existing `repros/mario-gifs/` set. The gated brawllib_rs **render** env was **not** run for
this research (not needed to answer Q1–Q5 from source); it *is* a prerequisite for the Q2
route if that route is chosen.

## Cross-refs

`docs/tooling-brawllib-rs-gif-recipe.md` (render recipe, #758) ·
`docs/tooling-brawllib-rs-datamine-recipe.md` · #777 (Mario reference set) · #758 ·
#567/#760 (silhouette-measurement precedent) · #778 (editor reference substrate) ·
#792 (WYSIWYG editor tracker — the workflow this unblocks) · editor
`pycats_editor/gif_map.py` (consumer) · brawllib_rs `src/renderer/{gif,camera}.rs`,
`examples/gif_generator.rs`.
