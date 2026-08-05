# Rect-coordinate write audit — sub-pixel truncation (#985)

**Role:** RESEARCH (audit). Follow-up to #979 (which fixed the `move_rect` `vel.x`
truncation bias, itself the fix for #949 — the Gnok left/right drift).
**Date:** 2026-08-04. **Branch:** `br-banana/pycats-985-research-audit-rect-coordinate-writes`.
**Sources:** all as-of this branch's HEAD; sites cited by symbol + file, not line number.

## TL;DR

The invariant — *"any value written to a body/collision box coordinate is an integer at
the point of the write"* — **holds everywhere, and now holds by construction.** Since #979
the sim's box is no longer a mutable `pygame.Rect`; it is the immutable
`FrozenRect` (`core/geometry.py`, #975/#833 §6). Every coordinate is truncated toward
zero at construction (`__post_init__` → `int(v)`), and every mutator (`with_*`, `moved`)
`int()`-truncates its input before building a new box. **A fractional coordinate cannot
rest in a box.** The ticket's "known map" — which described direct `rect.x += …` /
`rect.midbottom = …` mutation — predates that refactor and is obsolete as a *map of write
mechanics* (the sites moved to `with_*`/`moved`), though its *list of concern sites* still
maps 1:1 onto the new calls.

So the audit's real question is narrower than "is any coord fractional at rest" (answer:
no, structurally). It is: **at each site where a possibly-fractional source value meets
that truncation, is truncating the right thing, or a #949-class bias?** Two sites merit a
follow-up; the rest are safe. The `vel.y` question gets a verdict below (leave it
truncating — no basis to change).

## Method

- Enumerated every box-coordinate write in `pycats/` — every `FrozenRect(...)`
  construction, every `.with_*(...)`, every `.moved(...)`, plus every `pygame.Rect`
  coordinate assignment (`.center`/`.x`/`.y`/`.midbottom`/… and `.move`/`.move_ip`) in
  render/UI code.
- For each, traced the **source** value to its origin (not just its static type) to decide
  whether it can ever be fractional at runtime.
- Split the results by the box's role: **sim** (physics/collision `FrozenRect` — the #949
  class) vs **render/UI** (`pygame.Rect` for drawing/text layout — no effect on motion).

## The seam: FrozenRect truncates by construction

`core/geometry.py::FrozenRect`:

- `__post_init__` coerces `x, y, w, h` via `int(...)` (truncate toward zero — pygame
  assignment semantics), so **no box holds a fractional coord**.
- `with_x/with_y/with_left/with_right/with_top/with_bottom/with_center*/with_midbottom/with_topleft`
  each `int()` their argument and build a fresh box.
- `moved(dx, dy)` builds `FrozenRect(int(self.x + dx), int(self.y + dy), …)` — the one
  translate seam, used by `move_rect`.
- `test_geometry.py` pins this truncation/centre-floor/collide parity against real
  `pygame.Rect`.

Because truncation is centralized here, the audit reduces to **classifying the source of
each write**, not re-checking the write itself.

## Sim box (`FrozenRect`) write sites

| Site (symbol · file) | Write | Source of value | Verdict |
|---|---|---|---|
| `move_rect` · `core/physics.py` | `rect.moved(round(vel.x), vel.y)` | `vel.x` (rounded, #979); `vel.y` (truncated) | **safe (x)** / **see vel.y question (y)** |
| `solve_vertical` snaps · `core/physics.py` | `with_top/with_bottom(p.rect.top/bottom)` | another box's coord accessor → int | **safe** |
| `solve_horizontal` snaps · `core/physics.py` | `with_left/with_right(p.rect.right/left)` | another box's coord accessor → int | **safe** |
| `resolve_fighter_overlap` push-apart · `core/physics.py` | `with_x(rect.x ± JOSTLE_PUSH_PX)` | int coord ± `JOSTLE_PUSH_PX = u(...)` (u returns `round()` → int) | **safe** |
| `would_dodge_off_platform` · `core/physics.py` | `actor_rect.moved(dodge_velocity, 0)` | `dodge_velocity = fighter.vel.x` (**fractional**) | **latent — align to `round` (see F1)** |
| platform-edge clamps · `entities/fighter_physics.py` | `with_left/with_right(platform_rect.*)` | platform box coords → int | **safe** |
| land-on-platform snap · `entities/fighter_physics.py` | `with_bottom(current_platform.rect.top)` | box coord → int | **safe** |
| `Fighter.place` · `entities/fighter.py` | `FrozenRect(0,0,w,h).with_midbottom((x, y))` | `x,y` = `PLAYER{1,2}_START_{X,Y}` (`config/render.py`, all `//`/int arithmetic) | **safe** |
| `Fighter` KO offscreen · `entities/fighter.py` | `with_center(_KO_OFFSCREEN_POS)` | `(-1000, -1000)` int literal | **safe** |
| `Fighter.reset_to_spawn` · `entities/fighter.py` | `with_midbottom(self.spawn_point)` | `spawn_point = Vector2(x, y)` where x,y are the int spawn coords → integer-valued float; `int()` is a no-op | **safe** |
| ledge get-up snap · `entities/player.py` | `with_topleft(ledge.getup_topleft(size))` | `ledge.ax/ay` = platform `r.left/right/top` (int) ± int size | **safe** |
| ledge hang snap · `entities/player.py` | `with_topleft(ledge.hang_topleft(size))` | same ledge int anchors | **safe** |
| posture resize · `entities/player.py` | `with_size(target).with_midbottom(midbottom)` | `midbottom = self.rect.midbottom` (box coord → int) | **safe** |
| attack box place/track · `entities/attack.py` (×3) | `with_center((int(hit_cx), int(hit_cy)))` | `hit_cx/hit_cy` are **float** accumulators | **latent-low — `int` vs `round` (see F2)** |

## Render / UI box (`pygame.Rect`) write sites — out of the #949 class

These write to throwaway `pygame.Rect`s used for **drawing and text layout**, not motion.
Truncating a draw position by <1px cannot bias physics. Listed for completeness:

- `render/body.py` — `rect.center = (int(segment.x), int(segment.y))` on a `surf.get_rect()`
  (explicit cast; render).
- `sim/captions.py` — `rect.midtop/center/midbottom = (w // 2, …)` (int arithmetic; caption
  layout).
- `ui/menu_widgets.py`, `shell/esc_hold.py`, `screens/options_menu.py` —
  `rect.center = <int tuple / meta constant>`; `options_menu` `sm.move(dx, dy)` (scroll,
  int deltas).
- `ui/text_utils.py` — `rect.y += baseline_adjustment` (glyph baseline; render).

**Verdict: all safe / non-sim.** No action.

## Findings (actionable)

### F1 — dodge off-platform predicate truncates where the real move rounds *(latent, low-med)*

`move_rect` now commits horizontal motion with `round(vel.x)` (#979). But
`would_dodge_off_platform` (`core/physics.py`), which predicts *"would this dodge walk me
off the edge?"*, builds its lookahead box with `actor_rect.moved(dodge_velocity, 0)` — and
`moved` **truncates toward zero**. So at any fractional dodge speed the predicate models a
step of `trunc(vel.x)` while the actual move takes `round(vel.x)` — they can disagree by
1px, and the truncation carries the same toward-zero directional lean #949 was about (just
on a boolean, not a committed position). Consequence: a dodge near the lip can be judged
on-platform yet actually step 1px further, or vice-versa, asymmetrically by facing.

- **Recommendation:** align the predicate with the committed move — `actor_rect.moved(round(dodge_velocity), 0)`.
- **Basis:** consistency with #979's own fix; no game-value change (the *speed* is
  unchanged — only the lookahead's rounding matches the real step). A DEV ticket with a
  regression test (fractional dodge speed at a lip: predicate agrees with the realized
  `move_rect` step) is appropriate. File one-at-a-time downstream.

### F2 — attack box snapshot uses `int()` truncation, not `round()` *(latent-low)*

`entities/attack.py` places/tracks the attack collision box with
`with_center((int(hit_cx), int(hit_cy)))`, where `hit_cx/hit_cy` are **float** accumulators
(`hit_cx += vx` etc.). This is the **correct sub-pixel pattern** — the precise position is
retained in the float and only the *box snapshot* is integerized each frame, so there is
**no drift/accumulation** (contrast the body box, which carries no remainder — see the
vel.y question). The only artifact is that the snapshot leans up to 1px toward zero versus
the true centre on a given frame.

- **Recommendation:** optional — switch `int()` → `round()` here for symmetric box
  centring. Low priority (no drift; sub-pixel box placement of a transient hitbox). If
  touched, needs a golden check (attack goldens may shift by ≤1px). Not required for
  correctness.

## The `vel.y` / vertical-rounding question — verdict

**Verdict: leave `vel.y` truncating. Do not round it in `move_rect` absent a game-feel
basis + a reviewed golden regen.**

Reasoning:

1. **It is not a #949-class bias.** #949 was a *directional drift*: at a positive x,
   truncation-toward-zero makes a leftward step `ceil` and a rightward step `floor`, so a
   fighter walking left vs right at the same position is treated asymmetrically and creeps
   one way over time. Vertical motion has no symmetric-action counterpart — gravity is
   monotonic (always downward while falling) and the vertical velocity is **recomputed each
   frame by the accelerator**, not carried forward from a truncated position. Truncation
   toward zero uniformly *reduces* both fall and rise magnitude by <1px/frame with **no net
   creep**. It is a small fidelity loss, not a drift bug.
2. **Rounding is a game-value change.** Rounding `vel.y` alters gravity/jump fall
   trajectories, which **moves the golden sims**. Per RULES "Changing a game value", a
   fall-feel change needs a **research/data citation or a game-designer decision** plus a
   reviewed golden regeneration (`tests/golden/REGEN_PROTOCOL.md`, present). No such basis
   exists today — so this audit does not authorize it.
3. **If vertical fidelity is ever wanted, rounding is the wrong tool.** The fidelity-correct
   fix is a **sub-pixel remainder accumulator** — carry the fractional part of the position
   frame-to-frame (the pattern `attack.py` already uses for `hit_cx/hit_cy`) — which
   preserves the exact rate in *both* axes without the per-frame magnitude loss that
   rounding still leaves. That is a larger DEV + a designer decision on whether exact
   fractional rates are desired at all (they were explicitly deferred as out-of-scope in
   #979's `move_rect` docstring), and it would also revisit the `round(vel.x)` choice.

**Option space (human decides — this is research, not a decision):**

- **A — status quo (recommended default):** leave `vel.y` truncating; no change, no basis
  required. The current behavior is stable and golden-pinned.
- **B — round `vel.y`** like `vel.x`: requires a fall-feel basis + golden regen. Only on a
  designer decision.
- **C — sub-pixel remainder accumulator** for both axes: highest fidelity, largest change;
  requires a designer decision on exact-rate motion + full golden regen; supersedes the
  round-vs-truncate framing entirely.

## Downstream (file one-at-a-time, after this doc)

- **DEV** — F1: round the dodge off-platform lookahead to match `move_rect` (with a
  fractional-speed-at-lip regression test).
- **DEV (optional, low)** — F2: `int()` → `round()` for the attack box snapshot.
- **DECISION (ARC), only if pursued** — the `vel.y` vertical-motion question (Option B/C),
  needing a basis + golden regen. Not filed unless a human wants to change vertical feel.

## Scope honesty

- Enumeration covers `pycats/` (source; tests excluded per the ticket). It is grep-based
  across all coordinate-attribute writes + all `FrozenRect`/`with_*`/`moved`/`move`/`move_ip`
  call sites, then source-traced. No dynamic `setattr` on a box coord was found.
- "Safe" means *the source is provably integer-valued at the write* (traced to int literals,
  `//` arithmetic, or another box's int accessor), so truncation is a no-op — not merely
  "integer-typed today".
- The two latent sites (F1, F2) are the only places a fractional source reaches truncation;
  neither is a resting-fractional-coord violation of the invariant, and only F1 carries a
  #949-style directional lean (on a predicate).
