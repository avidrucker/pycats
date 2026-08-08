# Animation / movement ↔ hit-box / hurt-box coupling — a data-model survey

> **Role:** RESEARCH findings (#1082) · **area:combat** · parent #792 (editor family).
> **Status:** findings + option space only. This doc does **not** choose or
> ratify an architecture — per RULES, the design decision is a separate
> follow-on ARC/decision ticket, filed one-at-a-time downstream of this doc.

## The question

When a move plays, a game has to move two things together: the character's
**body through space** (the sprite/skeleton) and the **hit/hurt boxes** attached
to it — and it has to keep the data model simple enough to author and test. This
doc surveys how mainstream games do that, maps each approach onto pycats' current
model (per-frame circles offset from a body origin), and lays out the option
space with trade-offs.

Three seams recur throughout and are worth naming up front:

- **Anchoring** — what a box's authored offset is measured *relative to*: the
  body origin (flat), a named anchor point, or a skeleton bone.
- **Time** — whether box data is authored **per frame** or **interpolated**
  between sparser keyframes.
- **Movement** — whether the body's displacement during a move is **authored in
  the animation** (root motion) or **driven by code/physics** (velocity), with
  the animation playing "in place".

Every approach below is a point in that three-axis space.

---

## 1. The seams: how the sprite AND its boxes move together

There are two dominant strategies for keeping a box glued to the part of the
character it represents:

**(a) Bone-attached (transform inheritance).** The character has a skeleton
(a tree of bones). The animation moves the bones. A box is authored *once* in a
bone's local space (bone id + local offset + radius) and **rides that bone** — its
world position is the bone's animated world transform composed with the authored
local offset. The author never re-places the box per frame; the animation carries
it. This is the retained-mode / scene-graph model.

**(b) Frame-authored offset.** There is no skeleton (or it's ignored for boxes).
Each animation frame carries its own box list, each box authored as an offset in
the *frame's* local space (relative to the character's origin/pivot). When the
frame advances, a fresh box list replaces the old one. The author places every box
on every active frame by hand. This is the immediate-mode / tabular model.

The trade is the classic one: (a) pays a large up-front cost (rig, interpolation,
tooling) to make per-move authoring cheap and articulated; (b) pays nothing
up-front but makes authoring cost scale with frames × boxes, and caps fidelity at
whatever the author hand-places.

---

## 2. Movement: root motion vs. code-driven velocity

Independent of how boxes are anchored, the body's *position* during a move is
owned by one of two things:

- **Root motion** — the animation moves the character's root; the engine extracts
  that per-frame delta and applies it to the body. Movement is animation-accurate
  (a lunge lunges exactly as animated, feet don't slide), but it couples movement
  to frame data and complicates responsiveness, interrupts, and physics blending.
- **Code / physics velocity** — the body's position is owned by a physics
  integrator (velocity, gravity, friction); the animation plays "in place" and is
  purely cosmetic to movement. Responsive and simple to reason about, but the
  animation and the actual displacement can desync (foot-slide), and a move that
  should lunge has to encode that lunge as a code-side velocity impulse rather than
  in the animation.

Most platform fighters and action games are a **hybrid**: physics owns the common
case (walk, fall, knockback) while specific moves inject authored displacement.

---

## 3. Survey

### 3.1 Melee / Brawl / Project M (skeletal, bone-attached boxes)

*Confidence: high on the structural model (bone-attached boxes + shared skeleton +
per-subaction script); this matches the brawllib_rs / PMDT box+bone datamine the
project already runs. Specific numeric claims about any one move are out of scope
here and belong in the datamine, not this survey.*

The Smash lineage is the archetypal **(a) bone-attached** model:

- Each fighter has **one shared skeleton** (a bone tree) reused by every move.
- A move is a **subaction**: an *animation* (per-bone keyframe transforms,
  interpolated between keyframes) plus a *script* of timed commands.
- A **hitbox command** in that script carries a **bone id**, a **size** (radius),
  an **x/y/z offset** from that bone, and the combat params (damage, angle, base
  knockback, knockback growth, …). The box therefore **rides the bone**: its world
  position is the bone's animated transform ∘ the authored local offset. Turning a
  hitbox on/off is a timed script event ("hitbox on at frame 5, off at frame 8").
- **Hurtboxes** are likewise bone-attached (capsules defined per bone in the model
  data); they follow the skeleton automatically, no per-frame authoring.
- **Movement**: primarily physics/velocity, but the engine supports
  animation-driven translation of the top/root bone for moves that reposition the
  character — a hybrid.

Why the data model stays "simple" despite the machinery: the *skeleton is
authored once per character*, animations are *sparse keyframes interpolated*, and
box data is a *short script keyed by bone*. The cost is moved up-front into the rig
and the interpolation engine (which is exactly what brawllib_rs has to reimplement
to read the data back out).

### 3.2 Traditional 2D fighters (frame-authored offset tables)

*Confidence: high on the general model; it is the textbook sprite-fighter
structure (Street Fighter / KOF / classic sprite-based Guilty Gear-era tooling).*

Classic sprite fighters are the archetypal **(b) frame-authored** model:

- A move is an **ordered list of frames**. Each frame is a row in a **frame-data
  table**: `{ sprite, duration, hitboxes[], hurtboxes[], pushbox, movement dx/dy,
  cancel/flags }`.
- Boxes are **rectangles authored per frame** in the sprite's local space
  (relative to the sprite origin/pivot). There is no skeleton; when the frame
  advances, the whole box set is replaced. The author hand-places boxes on every
  active frame.
- **World placement** is `character_position + facing_mirror(frame_local_offset)`
  — facing flips the X of every box offset.
- **Movement** is typically **authored per-frame displacement** (a lunge encodes
  `dx` on its frames) — i.e. frame-baked root motion — combined with code physics
  for jumps/gravity. So 2D fighters often author movement in the frame table even
  though they don't have a skeleton.

This is the model pycats most resembles today (flat, per-frame, tabular), with the
one difference that pycats currently owns movement in **code velocity**, not in the
frame table.

### 3.3 General engine practice (Unity / Unreal / Godot)

*Confidence: high on the mainstream patterns; these are standard engine features.*

- **Skeletal animation + attached colliders**: colliders are **children of bones**
  in the transform hierarchy (retained-mode scene graph). The animation drives bone
  transforms; the colliders inherit — the engine's **(a)** model.
- **Active-frame gating** is done with **animation events / notifies**: a track on
  the animation timeline toggles a hitbox collider on during active frames and off
  otherwise — the engine analogue of the Smash subaction script.
- **Root motion vs. in-code velocity** is a first-class, much-debated engine
  toggle (Unreal's "Root Motion", Unity's `applyRootMotion`): the same character
  can be driven either way. Root motion → animation-accurate movement but harder to
  make responsive; code velocity → responsive but can foot-slide.
- **Retained vs. immediate**: engines keep live collider objects that transform
  each frame (retained). pycats, by contrast, **recomputes** its boxes from plain
  data at resolution time (immediate) — cheaper to test, since a box is a pure
  function of `(move, frame, fighter state)` with no persistent object to drift.

---

## 4. Where pycats sits today (code-grounded)

pycats' model is deliberately the **simplest corner** of the survey space:
flat-anchored, window-static, code-velocity — even simpler than a classic 2D
fighter. The coupling between "where the fighter is" and "where its boxes are"
happens at **exactly one seam**: the body box's origin + width + facing.

**Position / movement** — `pycats/entities/fighter.py::Fighter`. A fighter's
world position is a single immutable `FrozenRect` (`self.rect`, positioned by its
midbottom / feet point); velocity is a mutable `pygame.Vector2` (`self.vel`);
facing is a bool (`self.facing_right`). Position advances each tick purely by
gravity + velocity integration in
`pycats/entities/fighter_physics.py::step_physics` (via the pure primitives in
`pycats/core/physics.py`). There is **no root motion** — the animation never moves
the collision body; knockback too is just a velocity write in
`Fighter.receive_hit`. This is the §2 **code-velocity** model, with nothing
authored in the animation.

**Box primitive** — `pycats/combat/data.py::Circle` is the only box shape: a
frozen `(dx, dy, r)`. `Hitbox` wraps a `Circle` with `damage / angle /
base_knockback / knockback_growth`, an optional per-hitbox active window
(`active_start / active_end`, else the move default `[startup+1, startup+active]`),
and a stable `label` (A–Z). `MoveData` is `name / in_air / startup / active /
recovery` + a `hitboxes` tuple. `Hurtbox` is a tuple of `Circle`s, resolved from
the fighter's **posture** (stand/crouch/prone), shared across all moves; a per-move
`hurtbox` override exists in the type but no shipped move sets it.

**The transform (the one seam)** — `pycats/combat/geometry.py::resolve_circle`.
Offsets are **facing-right-relative**, measured from the body box's **top-left
origin**:

```python
cx = origin_x + circle.dx                 # facing right
cx = origin_x + width - circle.dx         # facing left — mirror about body CENTRE (#64)
cy = origin_y + circle.dy
```

Facing-left mirrors **about the body centre** (`+ width - dx`), not the left edge,
so a centered box is facing-invariant. `width` comes from `rect.width`, seeded by
`config/render.py::PLAYER_SIZE = (40, 60)`. Hitboxes are resolved **once at spawn**
(`pycats/entities/attack.py::Attack.__init__`) from the attacker's rect; hurtboxes
are resolved **every frame** (`pycats/systems/hit_resolution.py::process_hits`)
from the defender's rect; overlap is then a pure circle test.

**No rig.** There is no skeleton, bone, or anchor anywhere — flat circles off one
origin. The only articulated thing is a **render-only** Verlet `tail`, which never
enters collision.

**On-disk shape** — `pycats/characters/data/<cat>.json` (`schema_version 1`, thin
mirror: circles inline as `[dx, dy, r]`, default-valued fields omitted). One move:

```json
"attack": {
  "name": "down tilt", "in_air": false,
  "startup": 5, "active": 4, "recovery": 21,
  "hitboxes": [
    { "damage": 9.0, "angle": 80, "base_knockback": 30.0,
      "knockback_growth": 80.0, "label": "A", "circle": [37, 30, 13] }
  ]
}
```

**The editor is already more expressive than the runtime.** The offline editor's
`WorkingMove` (pycats-editor `src/pycats_editor/working.py`) is **frame-major**:
`frames: dict[frame → list[FrameBox]]`, a box identified across frames by a stable
`id`. On **load** it *explodes* each frozen `Hitbox` across its window into one
per-frame row; on **save** it *collapses* per-frame rows back into per-move-window
`Hitbox`es and writes the same `schema_version 1` JSON. So the authoring model can
already talk per-frame, but the runtime flattens it to **one static circle per
window**. That collapse is the exact place a future "box that moves or grows across
its active frames" would have to be represented — the runtime can't hold it today
without splitting into several adjacent-window hitboxes.

### What extends cleanly vs. what fights us

**Extends cleanly:**
- **More moves / characters** — just more tabular JSON; nothing structural.
- **Immediate-mode purity** — a resolved box is a pure function of
  `(move, frame, fighter state)`; no persistent collider to drift, so the sim
  goldens + provenance tests stay strong and cheap.
- **Facing** — handled in one function (`resolve_circle`); a symmetric box is
  facing-invariant for free.

**Fights us:**
- **Articulated motion within a move** — a limb swinging through an arc over its
  active frames has no bone to ride and no per-frame geometry in the runtime; it
  must be hand-authored as several adjacent-window hitboxes (the editor can express
  the per-frame path, but `collapse` throws the motion away).
- **Root-motion moves** — a lunge / dash-attack that repositions via the animation
  has no representation; it must be a code-side velocity impulse. The only existing
  precedent is the narrow `grants_recovery / recovery_vx / recovery_vy` per-move
  velocity for recovery specials — a per-move authored impulse, not per-frame
  displacement.
- **Shared sub-anchors** — every box offset is measured from the one body origin;
  there is no "hand" or "foot" anchor to attach a cluster of boxes to, so
  articulated or asymmetric poses re-author each offset by hand.

---

## 5. Options / strategies (trade-offs — not a choice)

The design space is three orthogonal axes: **anchoring** (flat origin → named
anchor → bone), **time** (per-move window-static → per-frame authored →
interpolated keyframes), and **movement** (code velocity → authored root motion).
pycats today is `{flat, window-static, code-velocity}` — the simplest corner. The
options below are moves along one or more axes; they **compose** (e.g. B+F, or
D+C), and none is chosen here — that is the follow-on ARC ticket's job.

| # | Strategy | Axis move | Simplicity | Authoring cost | Fidelity | Testability | pycats fit |
|---|---|---|---|---|---|---|---|
| **A** | **Status quo** — flat window-static circles + code velocity | (none) | Highest | Low for simple moves; rises as poses articulate | Circles only; no motion within a window | Highest (pure immediate-mode, already golden-tested) | It's what we have; extends by adding JSON |
| **B** | **Per-frame geometry in the runtime** — let the editor's frame-major model reach the game (stop collapsing, or store a per-frame circle track) | time: window→per-frame | Medium (JSON grows per frame; the `collapse` seam inverts) | Higher (place every frame) — but the editor already authors this | Higher — a box can move/grow across its window | High (still pure data, more rows) | Closes the gap the editor's `collapse` currently hides |
| **C** | **Interpolated keyframes** — author sparse box keyframes, tween `dx/dy/r` between them | time: →interpolated | Medium (tween math) | Lowest for smooth motion (few keyframes) | Medium–high (smooth arcs) | Medium (interpolation to test; goldens get float-sensitive) | Extends B with tweening; editor gains a keyframe timeline |
| **D** | **Named anchors ("bones-lite")** — author a few per-frame anchor points (hand/foot); boxes attach to `anchor + local offset` | anchor: flat→anchor | Medium | Medium (author anchors once; box clusters ride them) | Medium (articulation without a full rig) | High (still pure data) | Incremental layer between flat-origin and a rig; editor gains anchors |
| **E** | **Full skeletal rig + bone-attached boxes** (the Smash / engine model) | anchor→bone, time→interpolated | Lowest (rig + IK + interpolation + big tooling rewrite) | Lowest per move *once the rig exists* (huge up-front) | Highest | Lowest (float interpolation; loses the immediate-mode golden purity) | Large rewrite; the box editor becomes a rig/animation editor |
| **F** | **Authored root motion** — author per-move/per-frame body displacement instead of a pure code impulse (generalizes `grants_recovery/recovery_vx/vy`) | movement: velocity→root motion | Medium | Medium | Movement matches the animation (lunges land where drawn) | Medium (movement now depends on frame data; physics/interrupt interaction to test) | Orthogonal to A–E; composes with any |

**Reading the table.** Simplicity and fidelity trade off along every axis, and
pycats' current strength is **testability** — the immediate-mode, pure-data model
is what makes the sim goldens and provenance registry cheap and strong. Options A,
B, and D preserve that purity (pure data, immediate recompute); C and E spend it on
interpolation. F is an independent axis about *movement*, not boxes, and the
`grants_recovery` fields show the runtime already has a narrow foothold for it.

**Natural increments (smallest step first), for the ARC ticket to weigh — not a
recommendation:** A → B (runtime per-frame, since the editor already authors it)
→ D (anchors) and/or C (tweening) → E (full rig) only if articulation demand
justifies losing immediate-mode purity. F can be picked up independently whenever a
move needs animation-accurate travel.

## Open questions for the follow-on ARC / decision ticket

These are the decisions this survey surfaces but does **not** make:

1. Is there real demand for **motion within a move's active window** (a box that
   moves/grows across frames), or do adjacent-window hitboxes cover every case we
   actually need? (Drives A vs. B/C.)
2. Do we want **articulated poses** (limbs) enough to add anchors or a rig, or do
   flat circles stay adequate for the art direction? (Drives D vs. E vs. staying
   flat.)
3. Should any move author **root motion** (lunge/dash-attack travel), or do we keep
   all displacement as code-side velocity impulses? (Axis F, independent.)
4. If we lift the runtime to per-frame (B), do we **keep the `collapse` step** as an
   optimization for static moves, or drop it and store per-frame everywhere?
5. What is the cost to the **sim-golden / provenance test model** of each option —
   which ones keep box geometry a pure function of `(move, frame, state)` and which
   introduce float interpolation the goldens must tolerate?

Follow-up ARC/DEV tickets are filed one-at-a-time downstream of this doc.

