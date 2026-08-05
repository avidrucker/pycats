# Multi-hitbox / single-hurtbox same-frame overlap — canon resolution vs pycats (#829)

**Role:** RESEARCH (canon grounding + pycats code comparison). **Date:** 2026-08-04. **Agent:** ELDERBERRY.
**Spun out of:** #807. **Feeds:** verification of ledger claim `PYC-C-003-GRAPE`; the parity DEV #1214.
**Question restated:** when two or more of *one move's* hitboxes overlap *one* target's hurtbox on the
**same frame**, how does a real Smash engine pick which box's damage/angle/knockback apply — and does
pycats match?

---

## TL;DR

**Canon rule (grounded, two tiers agree): lowest hitbox ID wins; exactly one hitbox of a move
connects with a given target per frame; damage is NOT summed.** The priority key is the hitbox's
**ID** (the "hitbox stack"), *not* its damage and *not* its size — SmashWiki's own example is Marth's
Melee down-air, whose *smaller* tipper box sits at the top of the stack and wins.

**pycats already matches the STRUCTURE** — `process_hits` takes the **first** overlapping box in
`atk.resolved` order and stops (`PYC-C-003-GRAPE`, one-connect per target; #943 audit Guard A). The
**one gap** is the priority *key*: pycats orders boxes by **authored tuple position**, canon orders by
**explicit hitbox ID (lowest wins)**. These coincide only if every move is authored in id order.
pycats had no `hitbox_id` until #1213; #1214 is the DEV that makes the ordering explicit.

**Correction that #1214 needs:** #1214's body says pycats selects the box by **`max(damage)`**. That is
**not** the box-selection rule — `process_hits` selects first-in-authored-order, never by damage. The
only `max(damage)` in combat is `_clank_strength`, which is **opposing-hitbox clank** (a different
mechanism, out of #829's scope). #1214 should be re-worded to "make the same-frame box priority
explicit via `min(hitbox_id)`", not "swap `max(damage)`→`min(hitbox_id)`" (§5).

---

## Canon (cited primary + secondary)

### Tier 1 — engine reimplementation (meleelight, `~/Documents/Study/JavaScript/meleelight`)

`src/physics/hitDetection.js::hitDetect` is the hit-resolution loop. Structure (verbatim excerpts):

```js
for (var i = 0; i < 4; i++) {                 // i = candidate victim player
    if (playerType[i] > -1 && i != p) {
        // check if victim is already in hitList
        var inHitList = false;
        for (var k = 0; k < player[p].hitboxes.hitList.length; k++) {
            if (i == player[p].hitboxes.hitList[k]) { inHitList = true; break; }
        }
        if (!inHitList) {
            for (var j = 0; j < 4; j++) {      // j = attacker p's hitbox id, ASCENDING 0..3
                if (player[p].hitboxes.active[j] && ...) {
                    ...
                    } else if (player[i].phys.hurtBoxState != 1) {   // victim not intangible
                        if (...hitHurtCollision(i, p, j, ...)...) {
                            hitQueue.push([i, p, j, false, false, false, false]);  // ONE box j
                            player[p].hitboxes.hitList.push(i);                    // victim now hit
                            setHasHit(p, j);
                            break;             // <-- stop at first connecting box
                        }
                    }
                }
            }
        }
    }
}
```

What it establishes:
- **Boxes are checked in ascending id order** (`for j = 0..3`), and the **first** (lowest-id) box that
  collides with the victim's hurtbox connects: it pushes a **single** `hitQueue` entry carrying that one
  `j`, marks the victim in `hitList`, and **`break`s** the box loop. → lowest-id-wins, one connect, one
  box's params.
- **`hitList` also dedups across frames** — once a victim is in it the outer loop skips them, so the move
  connects **once per victim per instance** (the cross-frame guard, separate from the same-frame one).
- **No summing:** exactly one `hitQueue` entry per victim; the other overlapping boxes contribute nothing.
- Ids are **slots 0..3** — distinct by construction, so there is **no id-tie**; the lower slot index is a
  total, deterministic order.

Caveat (per [[meleelight-engine-logic-source]]): meleelight is **Melee**; Melee→PM is `[inference]`.
Hitbox-id priority is an engine-global that Brawl and PM inherit unchanged (the id/"stack" system is the
same across Melee/Brawl/PM), so the inference is strong; a PM-codeset override would be needed to break
it and none is known.

### Tier 2 — canon wiki (SmashWiki, secondary)

SmashWiki **Hitbox** article, "Normal Properties" (verbatim):

> "If multiple hitboxes of an attack connect within the same frame, the hitbox with the **lowest ID
> value** registers the hit."

> "Should multiple hitboxes of a single move connect with the opponent, **only one of them will count**.
> The order of precedence is known as the 'hitbox stack' — hitboxes higher in the stack will override
> ones lower should they both hit at the same time."

- Lower ID = higher stack position = higher priority. The article's worked example is Marth's Melee
  down-air: the **tipper** box is "on top of the stack" and wins **despite covering a smaller area** —
  proving priority is by **id**, not by **size** and not by **damage**.

SmashWiki **Priority** article is about *cross-character* clank (hitbox-vs-hitbox), not intra-move box
selection; it does confirm clank results apply move-wide ("if one hitbox clanks... the entire move
clanks"), which is why pycats' clank uses a per-move representative (§5, out of scope here).

---

## Answering #829's sub-questions

| # | Sub-question | Canon answer (grounded) | pycats |
|---|---|---|---|
| 1 | Selection rule + priority ordering | **Lowest hitbox ID wins**; others ignored, no stacking. Order = **id** (the "hitbox stack"), not size/damage/position. | First box in `atk.resolved` (= **authored tuple order**) that overlaps wins + `break`. **Structure matches; key differs** (position vs explicit id). |
| 2 | Damage — winning box only, or summed? | **Only the connecting box's damage.** One `hitQueue` entry; "only one of them will count". | `atk.damage = hit_box.damage` — one box. **Match.** |
| 3 | Knockback — which box's KB/angle? | The **connecting** box's angle / BKB / KBG (+ WDSK). | Copies `hit_box.angle / base_knockback / knockback_growth / set_knockback`. **Match.** |
| 4 | Same-frame vs cross-frame | Same-frame = id-stack (this ticket). Sequential windows (#204) and looping rehit (#213) are separate; `hitList` keeps them distinct. | Deactivate-after-connect (Guard B) + `_rehit_timer` (#213) + `set_id` (#888). **Match; mechanisms separated.** |
| 5 | Priority-tie | No true id-tie (ids are distinct slots) → deterministic lowest-wins. | Authored tuple order is total → deterministic. **Match** (but see §5 on stability if #1214 sorts). |
| 6 | Multiple hurtboxes on one target (mirror) | One hitbox overlapping several hurtbox bubbles = **one** hit (hurtbox set is OR'd). | `circles_overlap(cx,cy,r, resolved_hurtbox)` tests all defender circles, returns on first → one hit. **Match** (pycats already tests hit-once here). |

---

## pycats comparison — the enforcement site

`pycats/systems/hit_resolution.py::process_hits` (multi-box selection):

```python
boxes = getattr(atk, "resolved", None) or [(atk.hit_cx, atk.hit_cy, atk.hit_r, atk)]
...
hit_box = next(
    (box for (cx, cy, r, box) in boxes if circles_overlap(cx, cy, r, resolved_hurtbox)),
    None,
)
if hit_box is not None:
    atk.damage = hit_box.damage
    atk.angle = hit_box.angle
    atk.base_knockback = hit_box.base_knockback
    atk.knockback_growth = hit_box.knockback_growth
    atk.set_knockback = getattr(hit_box, "set_knockback", None)
    ...
    break  # only one hit allowed
```

`atk.resolved` is built in `pycats/entities/attack.py::Attack.__init__` as `self.hitboxes =
tuple(hitboxes)` (authored order, **no sort**) → `self.resolved` in that same order. So pycats'
same-frame priority key is **authored tuple position**. The #943 audit (`docs/research/
2026-07-31-one-connect-multihitbox-audit-findings.md`, Guard A) already pins this with an executed
revert-check: removing the `next()`/`break` and applying every overlapping box reds
`tests/test_multi_hitbox.py::test_overlapping_boxes_hit_once_in_priority_order` (`assert 2 == 1`).

**Verdict:** pycats **matches canon structurally** (one-connect, first-in-priority-order, KB from the
connecting box, multi-hurtbox one-hit, same/cross-frame separation). The **only divergence** is that the
priority order is **implicit** (authored tuple position) rather than an **explicit lowest-hitbox-ID**
sort. They agree exactly *iff* every move is authored id-ascending. This is precisely the gap #1214
closes now that `hitbox_id` is stored (#1213).

`PYC-C-003-GRAPE` ("first overlapping box in priority order wins, others ignored") is **confirmed
canon-faithful in structure**; its priority *key* is authored-order, which is a faithful stand-in only
while authored order == id order.

---

## §5 — Downstream note for #1214 (the parity DEV)

1. **Re-word the premise.** #1214 says "swap `max(damage)`→`min(hitbox_id)`". There is **no `max(damage)`
   box-selection rule** — `process_hits` selects **first-in-authored-order**. The actual change is: make
   the ordering **explicit** — select the overlapping box with the **lowest `hitbox_id`** instead of the
   first in authored tuple order. Re-word #1214's "Have" accordingly before implementing.
2. **`max(damage)` in combat is clank, not selection.** The only `max(damage)` is
   `hit_resolution.py::_clank_strength`, the representative-strength for **opposing-hitbox clank**
   (hitbox-vs-hitbox), which is **out of #829's scope** (this ticket is hitbox-vs-hurtbox). Do **not**
   touch `_clank_strength` under #1214. (Whether "strongest box represents the move for clank" is itself
   canon is a *separate* question — SmashWiki's Priority article says clank applies move-wide but does not
   fix the representative — could feed a future clank ticket; not #829, not #1214.)
3. **`None` handling.** Boxes with `hitbox_id = None` (all shipped moves today, #1213) must sort **after**
   any real id so authored order is preserved among un-id'd boxes → byte-identical goldens until real ids
   are datamined. Canon has no `None` (ids are always 0..N); `None`-last is a pycats migration convention.
4. **Stable sort.** Use a **stable** sort keyed on `hitbox_id` so equal/`None` ids keep authored order
   (canon never ties on id; pycats must stay deterministic). e.g. `min(boxes, key=id-with-None-last)` or a
   stable `sorted(..., key=...)`, not an order-losing selection.
5. **Reconciliation result:** #829 does **not** conclude a *different* resolution model from #1214 — it
   **confirms** #1214's direction (lowest id wins) and only corrects its wording. #1214 may proceed on
   this basis (after the re-word), still blocked/sequenced only by the schema predecessor #1213 (closed).

## Out of scope (unchanged from #829)

No implementation here (findings only). Opposing-hitbox clank representative (`_clank_strength`),
multi-**target** resolution (#843), and the smash-move authoring multi-hit question (#944) are separate.
