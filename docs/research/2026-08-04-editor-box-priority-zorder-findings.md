# Editor box priority / z-order (G8) — findings

**Ticket:** #1167 (RESEARCH · `combat:editor` · child of #792) · from #1072 §4-G8 / §5, routed by #1078 Q3.
**Question:** What must author-settable box **priority / z-order** mean for the editor, and what is the smallest build that gives deterministic tipper-first authoring?

**Headline:** Overlap resolution in the sim is **order-only** — the first box (in tuple order) that overlaps the target wins and applies its params. That order is `collapse`'s `(window_start, id)` sort, i.e. author box order within a window. A **total order is sufficient; no numeric priority is needed.** The design's `(window_start, priority, id)` sort key already records that `priority` has no field and reduces to `id`. The gap is purely editorial: the author cannot **reorder** boxes after creation, and the winning box is not surfaced. Recommendation: **Option A — an editor reorder/promote control (no pycats model change).** Option B (add a numeric `priority` field) is redundant with order and costs a cross-repo change for no behavioral gain.

---

## 1. How the sim resolves overlapping hitboxes (primary evidence)

### 1.1 First-overlapping box wins, by tuple order
`pycats/systems/hit_resolution.py::process_hits` selects the connecting box:

> ```python
> # First box (priority order) that overlaps this defender wins — a
> # single move-instance hits a given target at most once.
> hit_box = next(
>     (box for (cx, cy, r, box) in boxes if circles_overlap(cx, cy, r, resolved_hurtbox)),
>     None,
> )
> ```

On a hit it then applies **that box's** params:

> ```python
> atk.damage = hit_box.damage
> atk.angle = hit_box.angle
> atk.base_knockback = hit_box.base_knockback
> atk.knockback_growth = hit_box.knockback_growth
> atk.set_knockback = getattr(hit_box, "set_knockback", None)
> ```

So when a tipper box and a base box both overlap the defender on the same frame, **the one earlier in `boxes` order wins**. This is exactly tipper priority — and it is decided entirely by order, not by any magnitude/priority number.

### 1.2 That order is preserved from the move's tuple
`pycats/entities/attack.py` builds `resolved` in move order and calls it priority order:

> `self.hitboxes = tuple(hitboxes)`  — *"priority order preserved."*
> `self.resolved` — *"priority-ordered (cx, cy, r, Hitbox)."*
> *"Primary (first) box backs the legacy single-circle fields + rendering."* (`prim = self.resolved[0]`)

`boxes` in §1.1 is `atk.resolved`; its order is the move's `hitboxes` tuple order.

### 1.3 The tuple order is `collapse`'s `(window_start, id)` sort
`pycats/combat/collapse.py` emits the canonical `Hitbox` tuple sorted deterministically:

> ```python
> # 4. Deterministic order — sort by (window_start, id). The design's
> #    (window_start, priority, id) reduces to this: `priority` has no field in
> #    the current Hitbox model, so id is the sole tiebreak. Stable regardless
> #    of author edit order, which keeps overlap resolution and golden bytes fixed.
> emitted.sort(key=lambda t: (t[0], t[1]))
> ```

`id` is the author box id from the provenance frames — *"Same box iff same id (geometry is NOT identity)"* (collapse step 1). So within a window, **the lower-`id` box wins overlap.**

### 1.4 Conclusion on Q1 (what overlap needs)
- The sim needs a **total order** over a move's boxes, nothing more. It never compares a numeric priority.
- `priority` in the design's sort key is **vestigial** — there is no `priority` field on `pycats/combat/data.py::Hitbox`, and `collapse` documents that it reduces to `id`.
- Therefore "box priority / z-order" for the author **is** "which box comes first within its window" = box `id` order.

---

## 2. The actual gap (why G8 exists)

- **No reorder / promote control.** The editor assigns box `id` at creation (insertion order). To make a tipper win, the author must **create the tipper box first**. If the base box was drawn first, the base wins overlap, and there is no control to promote the tipper short of deleting and recreating boxes in the right order. (Findings §4-G8: *"box order is insertion order."*)
- **The winner is not surfaced.** Nothing in the editor tells the author which overlapping box currently wins, so a wrong order is invisible until playtest.
- **`label` (A–Z) is a separate identity from order.** `collapse` *preserves* the editor-assigned letter rather than recomputing a rank (data.py `Hitbox.label`; collapse step 1b), so letters are stable across deletes. But `doc_diff` notes *"a reorder re-letters the surviving boxes"* — so the label↔order relationship under an explicit reorder is a design point (see §4).

---

## 3. Option space + tradeoffs

| Option | What it is | Repo split | Size | Verdict |
|---|---|---|---|---|
| **A — reorder / promote control** | Editor lets the author change a box's order within its window (promote/demote, or drag in a box list), re-emitting provenance/JSON so the winning box has the lower `id`. Editor surfaces which box wins. | **E-side only** (editor). No pycats change — sim + collapse already resolve by order. | S–M | **Recommended.** Matches the sim's real model exactly. |
| **B — numeric `priority` field** | Add `priority` to `Hitbox` (pycats) + JSON schema + `collapse` sort + serializer, then expose a numeric control in the editor inspector. | **Cross-repo** (pycats R-slice prereq, then editor DEV). | M–L | **Redundant.** Priority would only ever duplicate order; buys nothing the sim uses, and reactivates the vestigial sort slot. Justified *only* if a future need for priority *independent* of draw/insertion order appears — none found. |
| **C — variant: "priority index" mapped to reorder** | Show the author a per-box priority number in the inspector, but implement it as reordering under the hood (no new model field). | E-side only. | M | A UI skin over A. Viable if a number reads more clearly to authors than a list position; carries the same label-restability question as A. |

### pycats-side (R) vs editor-side (E)
- **A / C:** entirely **E-side**. The pycats sim (`hit_resolution.process_hits`), `attack.py`, and `collapse` are already order-driven and need no change.
- **B:** **R-slice in pycats first** (`Hitbox.priority` field, `_hitbox_from_json`/`_hitbox_to_json`, `collapse` sort, drift-guard/golden updates), **then** an E-side inspector control. The findings doc labelled G8 "E-side"; that is true for A/C but **not** for B — flag corrected here.

---

## 4. Recommendation

**Option A — an editor reorder/promote control, no pycats model change.**

Rationale, grounded in §1: the sim resolves overlap by first-overlapping-box-in-order, and `collapse` already fixes that order as `(window_start, id)`. The only thing an author cannot do today is **change that order after creating boxes**, and they cannot **see** which box wins. Both are editor concerns. Adding a numeric `priority` field (Option B) would encode the same information the order already carries, at the cost of a cross-repo model/schema/collapse/golden change — a U-turn on `collapse`'s deliberate "priority has no field" simplification — for zero behavioral difference. No evidence was found of any need for a priority that differs from box order.

### Design points for the downstream architect/decision + DEV slice (not decided here)
1. **Order mechanism:** reassign `id` within a window vs. carry an explicit order index the editor sorts on before emit. (`collapse` sorts on `id`; the simplest build makes promote/demote rewrite the per-window `id`s.)
2. **Label stability under reorder:** `label` is a preserved identity (A–Z), but `doc_diff` treats a reorder as re-lettering. Decide whether promoting a box keeps its letter (identity-stable) or the letter tracks position — this affects the drift-guard and diff readability.
3. **Winner-surfacing UI:** how the editor shows which overlapping box currently wins (e.g. highlight the winning letter, or an ordered box list with the top = winner).
4. **Scope of "within a window":** order only matters among boxes whose active windows overlap on a frame; the control need only reorder same-window boxes.

---

## 5. Refs
#1072 (§4-G8, §5) · #1078 (Q3 order: G8 after G7/#1012/G5) · #792 (tracker) · #299 / #313 (Narz tipper) ·
`pycats/systems/hit_resolution.py::process_hits` (first-overlapping-wins + param apply) ·
`pycats/entities/attack.py` (priority-ordered `resolved`, `prim = resolved[0]`) ·
`pycats/combat/collapse.py` (`(window_start, id)` sort + "priority has no field" note) ·
`pycats/combat/data.py::Hitbox` (no `priority` field; `label` is a preserved A–Z identity) ·
`pycats-editor` `src/pycats_editor/doc_diff.py` (reorder re-letters surviving boxes).
