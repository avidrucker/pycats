# ADR-0024 — apply the datamine→editor origin translation at the editor accept step

> **Agent:** APPLE · **Authored:** 2026-08-09 · **Ticket:** #1351

- **Status:** Accepted  *(2026-08-09 — owner ruling on #1351)*
- **Date:** 2026-08-09

## Context

A datamined hitbox candidate (`combat/datamine_proposer.py::propose` / `propose_per_frame`)
lands ~a body-height (60px) too high. #1294 confirmed and quantified the cause: the
world→px seam `_circle_from_world` converts a box from **root**-frame to **top-left**-frame
but applies only the **unit-scale**, never the **top-left → feet** translation.

Coordinate vocabulary (locked in #1294; landed in code by #1350):

| Noun | Meaning | In code |
|---|---|---|
| **root** | datamine world origin = Brawl `TransN` root = the character's ground-contact centre; `y` up, world units | `DatamineHitBox.pos` is relative to this |
| **top-left** | pycats `Circle` origin = fighter rect top-left; screen `y` down, px | `Circle.dx/dy`, `resolve_circle` origin |
| **feet** | ground-contact centre in pycats = rect midbottom; **equals `root`** | `rect.with_midbottom(...)` |
| **body-box** | fighter `(w,h)` standing rect | `stand_size or PLAYER_SIZE` = `(40,60)` |
| **unit-scale** | px per world-unit (×5.4); **radius-scale** (correct) vs **position-scale** (unprincipled) | `u()` / `PX_PER_UNIT` |

Verified in #1294: **`root == feet`** (the dumper's `pos` is `TransN`-root world space; both
frames put the character's ground-contact centre at their origin), so the **top-left → feet**
vector is exactly `(w/2, h)`, read off the **body-box** — derived, not chosen.

The gap decomposes into two independent halves:
- **(a) origin** — the missing `(w/2, h)` translation; **vertical, dominant, mechanical.**
  Applying it collapses the measured vertical error from **64.1px → 9.9px** across the four
  committed mario datamine fixtures.
- **(b) position-scale residual** — after translation, a **horizontal** residual (mean +16px,
  range −41…+73, **sign-flips across moves**), because `unit-scale`'s radius factor has no
  principled meaning as a **position** scale (#120/#195), plus per-move `TransN` root-motion
  on lunging attacks. **No global constant recovers it.**

The editor already **draws** (`ghost.py::draw_ghosts`) and **accepts** (`ghost.py::accept_candidate`)
datamine candidates, both against the **top-left** origin with **no** translation today — so a
fix here is additive, not a double-count.

## Decision

**1. Where the origin translation applies → the editor accept step (`pycats-editor/ghost.py`),
not the proposer seam.** The proposer (`_circle_from_world` / `propose`) takes only `(z, y, size)`
and is deliberately fighter-agnostic; it has no access to the target's `body-box`. The accept
step already holds the target fighter, so the translation rides there without coupling the pure
proposer to a specific cat.

**2. How it is computed → per-fighter `(w/2, h)` from `body-box = stand_size or config.PLAYER_SIZE`.**
Derived from the rect, never a hardcoded `(20, 60)`. `(20, 60)` is correct only while the
`body-box` is the default `(40, 60)`; a fighter with a real `stand_size` override (small
archetype, #275/#286) has a different `body-box` and would be mis-placed by a literal.

**3. The ghost preview applies the same translation → in both `draw_ghosts` and accept.** They
already share the `_resolved_circle` / `resolve_circle` seam, so applying the translation once at
that seam covers both. WYSIWYG: the box the author sees is the box accept stores.

**4. The horizontal position-scale residual → left to the human feel-pick; no global
position-scale correction.** #120/#195 established there is no fixed world→px position-scale
(Brawl renders through a per-subaction perspective auto-fit camera). The residual sign-flips
across moves, so no constant satisfies all boxes; part of it is per-move root-motion, not a scale
at all. The author's final horizontal nudge is the feel quantity (#782/#310); manufacturing a
constant "correction" would be a tuning number with no basis (declined under RULES).

## Design (implementation shape for the DEV follow-up)

- **Seam:** apply the translation at the shared `pycats-editor/ghost.py::_resolved_circle` (used
  by both `draw_ghosts` and `ghost_at`) **and** at `accept_candidate` (which authors
  `geom = {frame: (c.dx, c.dy, c.r)}`), so preview and stored geometry agree.
- **Thread the `body-box` in:** the accept/draw callers already resolve against the fighter — pass
  its `(w, h) = stand_size or PLAYER_SIZE` and translate each candidate `Circle` by `(+w/2, +h)`
  before `resolve_circle`. The `+w/2` horizontal component is facing-safe: `resolve_circle`
  mirrors around the body centre (`= w/2`), so a body-centre translation is facing-invariant.
- **Provenance:** the translated geometry stays `source="datamine"` / `FOUND` — the translation is
  a frame correction, not a re-authoring.
- **No proposer change:** `_circle_from_world` / `propose` stay fighter-agnostic and untouched.

## Consequences

- The dominant, mechanical 60px vertical error is removed at the point candidates are authored;
  the author starts from a box in roughly the right place instead of one a body-height high.
- A ~16px horizontal nudge remains per box — the correct residual to leave manual.
- **Cross-repo:** implementation lands in **pycats-editor**, filed as a separate DEV ticket
  (and a thin editor-local design note pointing here). This ADR is the pycats-side decision home.
- **Independent of #1217** (`FIRST_ACTIVE` representative-frame choice), which separately affects
  the residual; this decision neither waits on nor pre-empts it.
- The `(w/2, h)` translation is validated on the default `body-box`; re-confirm on a real
  `stand_size` override when one is datamined (#1294 gap G4).

## References

#1294 (findings + `root == feet` verification) · #1350 (vocabulary in code) · #1220 (editor accept
path) · #1217 (representative-frame choice) · #120/#195 (no world→px position-scale) · #782/#310
(position is a feel-pick) · ADR-0011/#962 (`units.u` seam) · ADR-0021 (per-hitbox field schema).
