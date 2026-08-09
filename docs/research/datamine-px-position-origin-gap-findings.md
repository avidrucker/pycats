# Datamine→px position-origin gap in `_circle_from_world` / `propose()`

> **Agent:** APPLE · **Authored:** 2026-08-09 · **Ticket:** #1294

## TL;DR

A datamine hitbox candidate emitted by `datamine_proposer.propose()` /
`propose_per_frame()` lands **~a full body-height (60 px) too high** because the
world→px seam `_circle_from_world` applies the correct **scale** but **no origin
translation**. The gap decomposes into two independent halves:

| Half | Cause | Magnitude (nalio / mario fixtures) | Recoverable? |
|---|---|---|---|
| **(a) Vertical — origin** | `_circle_from_world` pins the datamine world root (**feet-centre**) straight onto the pycats Circle origin (**rect top-left**); no `+h` translation. | mean **\|dy error\| 64.1 px → 9.9 px** once the feet-centre anchor `(w/2, h)` is applied. | **Yes — mechanical.** A single `(w/2, h)` translation removes almost all of it. |
| **(b) Horizontal — position scale** | After anchoring, `dx` still disagrees with authored: `u()` is a playtest-chosen **radius** factor pressed into service as a **position** scale (#120/#195), so it over/under-projects the forward `z` axis. | residual mean **+16.4 px**, but ranges **−41 … +73 px** and **flips sign across moves** (fair pulls back, jab/dsmash push forward). | **No — inherent.** Not a constant factor; no single world→px position scale recovers it. Human-nudge / feel territory. |

**Recommendation in one line:** apply the `(w/2, h)` feet-centre anchor at the
**editor accept step** (pycats-editor `ghost.py::accept_candidate`, which knows the
target fighter's `stand_size`), fixing (a) mechanically; leave (b) — the small,
sign-inconsistent forward residual — to the human nudge the proposer docstring
already anticipates. Do **not** attempt a global position-scale correction for (b).

---

## 1. The mechanism (primary quotes)

Three source facts, each quoted, compose the gap:

**Datamine world origin = character root (feet-centre), y-up.**
`datamine_hitboxes.py::DatamineHitBox` (@bce5178):
> `pos`: resolved WORLD position (x=depth, y=vertical up+, z=horizontal), unscaled

**The seam applies scale but no translation.**
`datamine_proposer.py::_circle_from_world` (@5801b71):
```python
return Circle(dx=u(z), dy=-u(y), r=u(size), status={...})
```
`dx = u(z)`, `dy = -u(y)`, `r = u(size)` — every axis routed through the radius
factor `u()`, **with no origin term**. So `pos = (·, 0, 0)` (a box at the feet-centre)
maps to `Circle(dx=0, dy=0)`.

**But pycats reads `(dx, dy)` from the rect top-left.**
`entities/attack.py::Attack` (@684cd5a):
> Attack carries absolute hitbox circles resolved … using the owner's rect
> **top-left** as origin

`combat/geometry.py::resolve_circle`: `cx = origin_x + dx`, `cy = origin_y + dy`,
with `origin_x/origin_y = owner.rect.x/owner.rect.y` (the top-left).

**And the rect's top-left is one body-height above the feet.**
`entities/fighter.py`: `self.rect = FrozenRect(0,0, w, h).with_midbottom((x, y))` —
the rect is placed by its **midbottom** at the feet, so the feet-centre in Circle
coordinates is the rect **midbottom** `(w/2, h)`, and `dy = 0` is the rect **top**
(head), `+dy` running **down**.

**The mismatch:** `_circle_from_world` produces a `(dx, dy)` measured from the
**feet-centre**; `resolve_circle` interprets that same `(dx, dy)` as measured from
the **rect top-left**. The two frames differ by exactly the feet-centre offset
`(w/2, h)`. The `dy = -u(y)` sign inversion (world y-up → screen y-down) is correct
and independent of this; the bug is purely the missing translation.

**The physically-impossible tell (from the ticket, reproduced):** nalio **dsmash** —
a move that hits **low** along the ground — converts to raw `dy ≈ -21` (i.e. 21 px
**above the head**). A ground-hitting box above the head is a pure origin artifact,
not bad data.

---

## 2. Quantification (all committed datamine fixtures)

Corpus: the **four** committed mario datamine dumps
(`pycats/combat/datamine_data/mario_{attack11,attackhi4,attackairf,attacklw4}.json`)
= jab / usmash / fair / dsmash, **11 datamine boxes** total, compared against nalio's
authored circles (nalio `stand_size = None` → `PLAYER_SIZE = (40, 60)`, so anchor
`(w/2, h) = (20, 60)`). Method: `propose(table, FIRST_ACTIVE)`, then `ANCHORED = RAW +
(20, 60)`, paired to authored boxes in id order.

```
                      RAW            ANCHORED (+20,+60)   authored        Δdx    Δdy    Δr
jab   id0   dx  66  dy -32  r19   dx  86  dy  28        ( 54, 27,19)     +32     +1     0
      id1   dx  33  dy -27  r13   dx  53  dy  33        ( 44, 28,13)      +9     +5     0
      id2   dx  24  dy -42  r15   dx  44  dy  18        ( 34, 29,15)     +10    -11     0
usmash id0  dx -59  dy -47  r19   dx -39  dy  13        (  2,  2,19)     -41    +11     0
      id1   dx -36  dy -45  r19   dx -16  dy  15        ( 12,  4,19)     -28    +11     0
      id2   dx  63  dy -55  r19   dx  83  dy   5        ( 10, 12,19)     +73     -7     0
      id3   dx  45  dy -44  r19   dx  65  dy  16        (  0, 12,19)     +65     +4     0
fair  id0   dx  11  dy -46  r17   dx  31  dy  14        ( 42, 18,17)     -11     -4     0
      id1   dx  14  dy -71  r24   dx  34  dy -11        ( 48, 26,24)     -14    -37     0
dsmash id0  dx  70  dy -21  r21   dx  90  dy  39        ( 40, 48,21)     +50     -9     0
      id1   dx  39  dy -21  r17   dx  59  dy  39        ( 24, 48,17)     +35     -9     0

  mean |dy error|  RAW (no anchor)      = 64.1 px   (≈ the 60 px body height)
  mean |dy error|  ANCHORED (+h)        =  9.9 px
  mean  dx residual after anchor (fwd)  = +16.4 px  (range −41 … +73, sign-inconsistent)
  Δr everywhere                          =  0 px    (radius scale is shared, exact)
```

**Reading:**

- **(a) is dominant and mechanical.** Anchoring collapses the vertical error from
  64.1 px to 9.9 px — the vertical gap was ~entirely the missing `+h = +60`
  translation. The "body-height high" of the ticket title is literal: the error
  equals `h`.
- **(b) is inherent, not a missing constant.** The post-anchor `dx` residual is not a
  fixed factor: usmash id2/id3 over-project by +65…+73, fair id0/id1 **under**-project
  by −11…−14. A single position scale cannot be both. This matches #120/#195 — `u()`
  is a radius factor and there is no fixed world→px position scale.
- **Radius is exact.** `Δr = 0` on all 11 boxes confirms whoever authored nalio took
  box **sizes** through the same `units.u()` seam — the scale half is already shared
  and correct; only the **position frame** differs.

**Two sub-causes fold into (b), and they should not be conflated:**
1. `u()` mis-serving as a position scale on the forward `z` axis (the #120/#195 story).
2. The `FIRST_ACTIVE` representative-frame choice (#1217, still open): a swing box read
   at its first-active frame sits at a different point along its arc than the authored
   "representative" box. fair id1's large residual (`Δdy −37`, `Δdx −14`) is the clearest
   case — a big sweeping box whose first-active frame is high and back in the swing. So
   part of the residual is a *frame-selection* artifact, resolved by #1217, not by any
   spatial anchor or scale.

---

## 3. Sub-question answers

**Q2 — Where should the anchor live? Does the editor already anchor (double-count risk)?**

- **The editor applies NO spatial anchor today.** `pycats-editor/ghost.py::accept_candidate`
  authors the candidate verbatim — `geom = {frame: (c.dx, c.dy, c.r) …}` — and
  `mapped_frames` remaps only the **time** axis (datamine frame index → MoveClock),
  never the spatial coordinates. The ghost **draw** path (`_resolved_circle` →
  `resolve_circle(circle, ox, oy, …)` with `origin` = fighter rect **top-left**)
  likewise applies no anchor. So the editor currently **draws and accepts datamine
  boxes a full body-height high**, internally consistent with the un-anchored proposer.
  **No existing anchor → a fix at accept-time is additive, zero double-count risk.**
- **The accept step is the right home**, not `_circle_from_world`/`propose()`. The
  proposer seam takes only `(z, y, size)` — it has **no access to the target fighter's
  dimensions**, so anchoring there would require threading `(w, h)` into `propose()` /
  `_circle_from_world` (a signature change that couples the pure, fighter-agnostic
  proposer to a specific target cat). The accept step already knows the target cat
  (hence its `stand_size`), so the anchor rides naturally there — alongside the
  frame→MoveClock map (#1220). The ghost **draw** must apply the same anchor so the
  preview matches what accept authors.
- The **#1278 QA viewer** (`scripts/datamine_hitbox_qa_viewer.py`, toggle `o`) already
  applies exactly this `(w/2, h)` feet-centre anchor **for display** — a visualization
  workaround, and independent confirmation the anchor value is right. It does not
  pre-empt the fix.

**Q3 — Is `(w/2, h)` universally the right anchor?**

- **Horizontal `w/2` is facing-safe.** `resolve_circle` mirrors a facing-left offset
  **around the body centre** (`cx = origin_x + width − dx`), and `w/2` **is** the body
  centre → the horizontal anchor is facing-invariant. No per-facing special-casing.
- **Vertical `h` holds for aerials.** Brawl's world root is the character root
  (feet-centre) regardless of grounded/aerial state; the aerial fixture (fair) anchors
  into the authored vertical band (id0 anchored `dy 14` vs authored `18`), modulo the
  #1217 frame-selection residual. `pos` is already a resolved per-frame world position,
  so any character-root motion during the animation is in the data; the anchor is only
  the static fighter→Circle frame offset.
- **Must be computed per-fighter, NOT hardcoded `(20, 60)`.** The anchor is
  `(w/2, h)` where `(w, h) = fighter.stand_size or config.PLAYER_SIZE`. nalio falls back
  to `PLAYER_SIZE = (40, 60)`; a small-archetype cat with a real `stand_size` override
  (Kirby-like, #275/#286) gets a proportionally smaller anchor. A future fix must read
  the target fighter's `stand_size`, not bake nalio's numbers.

**Q4 — Does a corrected world→px POSITION scale exist for (b)?**

No. #120/#195 (`docs/research/parity-notes-regarding-hurtbox-values.md`) established
there is **no fixed world→px position scale** — `u()` is a radius factor, and brawllib
renders the reference GIFs through a per-subaction perspective auto-fit camera
(`brawllib_rs/src/renderer/camera.rs`), so no single orthographic `k` exists. The
sign-inconsistent residual measured here (fair under-projects, jab/dsmash over-project)
is the empirical confirmation: no constant factor can satisfy both. A future fix ticket
should therefore treat (b) as the irreducible feel remainder handled by human nudge —
**not** chase a global position-scale constant.

---

## 4. Gap table (open questions / follow-ups)

| # | Gap | Status | Feeds |
|---|---|---|---|
| G1 | Apply `(w/2, h)` anchor at the editor accept step + matching ghost-draw. | **Ready to file as a DEV ticket** (this doc establishes where + the value). | hitbox-authoring epic (#1206 / #1191 / #1299) |
| G2 | `FIRST_ACTIVE` representative-frame choice contributes to the horizontal/vertical residual. | Open — **#1217** (render each strategy, eyeball vs reference). Distinct from the anchor. | #1217 |
| G3 | Horizontal residual (b) is position-dependent + sign-inconsistent; no global position scale recovers it. | **Confirmed inherent** — no fix ticket; documents *why* the forward nudge stays manual. | design note |
| G4 | Corpus is 4 mario moves / 11 boxes (all committed fixtures). Anchor value confirmed on `PLAYER_SIZE`; not yet exercised on a real `stand_size` override. | Open — re-confirm when a datamine dump for a small-archetype cat exists. | future validation |

**Scope honesty:** the quantification rests on the four committed datamine dumps (11
boxes, mario subactions, one fighter body size). The vertical finding (a) is robust and
pairing-insensitive — every anchored `dy` lands in the authored band. The horizontal
finding (b)'s per-box magnitudes carry pairing noise (fair has 2 datamine ids vs 4
authored boxes; id↔label pairing is by order), but its qualitative shape
(position-dependent, sign-inconsistent, not a constant) is not pairing-sensitive.

---

## Refs

- Seam: `pycats/combat/datamine_proposer.py::_circle_from_world` / `propose` /
  `propose_per_frame` (@5801b71); `datamine_hitboxes.py::DatamineHitBox` (@bce5178).
- Origin convention: `entities/attack.py::Attack` ("rect top-left as origin", @684cd5a);
  `entities/fighter.py` (`with_midbottom`); `combat/geometry.py::resolve_circle`
  (facing mirror around body centre); `combat/units.py::u` (radius factor).
- Editor accept path (no existing anchor): pycats-editor
  `src/pycats_editor/ghost.py::accept_candidate` / `draw_ghosts` / `_resolved_circle`.
- Display-side anchor (independent confirmation): `scripts/datamine_hitbox_qa_viewer.py`.
- Related: #1278 (QA viewer) · #1210 (`_circle_from_world` / `propose`) · #1207 (loader +
  fixtures) · #1220 (editor accept: datamine→MoveClock) · #1217 (representative-frame
  choice) · #1243 (`propose_per_frame`) · #782/#310 (box position is a feel quantity) ·
  #120/#195 (no fixed world→px POSITION scale; `u()` is a radius factor) · ADR-0011/#962
  (`units.u` seam).
