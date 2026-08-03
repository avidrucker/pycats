# ADR-0012 — PM-faithful character jostling (position-only ground nudge) for V1

- **Status:** Accepted  *(2026-08-01 — owner ratified the model across the #1003 forks and signed off on this record.)*
- **Date:** 2026-08-01

## Context

Character-on-character **jostling** is the Smash mechanic where two overlapping
fighters are slowly pushed apart. #594 research
(`docs/research/character-collision-push-findings.md`) established the canon rule and
where pycats diverges; the owner wants PM-faithful jostling as a **V1** mechanic.

Today `resolve_player_push` (`pycats/core/physics.py`) already matches canon on the
structural choices — **horizontal-only, no vertical resolution, stacking tolerated** —
but diverges on the push **model** three ways:

1. it resolves the entire overlap in a **single frame** (`overlap // 2 + 1` each way),
2. it **rewrites `vel.x`** (zero / average / half via `COLLISION_PUSH_SPLIT = 0.5`), and
3. it **pushes airborne** fighters, gated by an 80 % vertical-overlap check
   (`JOSTLE_MIN_VOVERLAP_FRAC = 0.8`, the #68 flyover-ratchet fix).

Those two constants are provenance-classified **TUNED** (deliberate, not canon-seeking).

**The concrete source** is a faithful Melee reimplementation, meleelight
(`schmooblidon/meleelight` @ `27af171`, 2018-05-30), `src/physics/physics.js`,
`physics(i, input)`, grounded push block (~lines 1159–1170):

```js
if (player[i].phys.grounded) {                                    // pusher grounded
    if (player[j].phys.grounded &&                                // pushee grounded
        player[j].phys.onSurface[0] === player[i].phys.onSurface[0] &&   // same surface TYPE
        player[j].phys.onSurface[1] === player[i].phys.onSurface[1]) {   // same surface INDEX
        // TODO: this pushing code needs to account for players on slanted surfaces
        const diff = Math.abs(player[i].phys.pos.x - player[j].phys.pos.x);
        if (diff < 6.5 && diff > 0) {                             // trigger: centre-dist < 6.5 units
            player[j].phys.pos.x += Math.sign(...) * -0.3;        // push: 0.3 units/frame, position only
```

**Confidence tiers, stated plainly (no overclaiming):**
- meleelight is a faithful **reimplementation**, not the retail ROM → **[SECONDARY]**.
- The exact retail Melee/Brawl/PM 3.6 push magnitude is **⚠ UNDOCUMENTED**; the push is an
  engine global, not per-move script data, so per-move datamine tools don't expose it.
  meleelight's `0.3 u` / `6.5 u` are the **accepted proxy**, not the ROM value.
- PM 3.6 runs on the Brawl engine and SmashWiki says Brawl's jostle is "unchanged" from
  Melee → PM inherits Melee jostle **[INFERENCE]**.

## Decision

Model = a **full literal port of the meleelight *ground* jostle**, with all **airborne**
behavior deferred to research (#1015) rather than shipped on a placeholder. Six parts:

**1 — Trigger: horizontal centre-distance `< 35 px`.** `= round(6.5 × PX_PER_UNIT)` where
`PX_PER_UNIT ≈ 5.4`. **[FOUND — meleelight `if (diff < 6.5 && diff > 0)`, `diff = |pos_i.x −
pos_j.x|`.]** Replaces today's AABB-overlap activation. The `35 px` trigger is an **absolute**
centre-distance; per-fighter body widths vary (`PLAYER_SIZE` is only the default box), so the
overlap it corresponds to differs per pair. The meleelight range is character-*relative*, so a
body-relative (percentage-of-width) trigger is a candidate refinement noted for later — not V1.

**2 — Push: gradual, position-only, ~`2 px`/frame each.** A named, cited constant
`JOSTLE_PUSH_UNITS = 0.3` → `round(0.3 × PX_PER_UNIT) = 2` px/frame per fighter, added to
`rect.x` each frame the pair overlaps (so a wide overlap separates over several frames, not
one). **[FOUND — meleelight `pos.x += sign(...) * -0.3`.]** Replaces the one-frame full
separation.

**3 — Velocity is never touched.** Drop the `vel.x` rewrite entirely and remove
`COLLISION_PUSH_SPLIT`. **[FOUND — meleelight mutates only `pos.x`.]** This removes the
single most un-canonical behavior: fighters keep their own momentum through a jostle.

**4 — Grounded + same-platform gate.** Full push only when **both** fighters are
`on_ground` **and** on the **identical** platform (same surface *type* and *index*).
**[FOUND — meleelight requires `player[i].phys.grounded`, `player[j].phys.grounded`,
`onSurface[0]` type match, `onSurface[1]` index match.]** pycats realizes this as
`a.on_ground and b.on_ground and same_platform(a, b)`, where `same_platform` compares each
fighter's `find_current_platform(rect, platforms)` result.

**5 — No airborne jostle in V1.** The grounded gate (4) means an airborne fighter never
pushes — meleelight-literal. The former airborne push **and** its #68 flyover-ratchet guard
(`JOSTLE_MIN_VOVERLAP_FRAC`) are **removed**: a grounded-only gate excludes the flyover by
construction, so the sideways ratchet can no longer occur. A weaker (e.g. 50 %) air push was
considered and **rejected as unsourced** — whether/how to add air jostle plus overlap
("ratchet") handling is **deferred to RESEARCH #1015**.

**6 — Grab exemption: N/A.** pycats has no fighter-vs-fighter grab mechanic (only
*ledge*-grab), so meleelight's `grabbing`/`grabbedBy` exemption has nothing to exempt. The
existing `"dodge"`-state skip is a separate pycats mechanic, kept unchanged.

### Values (raw unit → derived px)

| Quantity | raw (meleelight `27af171`) | pycats px | provenance |
|---|---|---|---|
| trigger centre-distance | `6.5 u` | `round(6.5 × 5.4) = 35` | **FOUND** |
| push per fighter / frame | `0.3 u` | `round(0.3 × 5.4) = 2` | **FOUND** |

Store the **raw units** as named, cited constants and derive the pixel via
`pycats/combat/units.py::u()` (per ADR-0011: raw unit is the source of truth, integer px
derived at the seam) — **never** a bare `× 5.4`. Movement/trigger distances round to an int
because the sim is integer-pixel (#80).

### Provenance classification (per RULES → "Changing values", ADR-0003 / #233)

- **New — FOUND:** `JOSTLE_TRIGGER_UNITS = 6.5`, `JOSTLE_PUSH_UNITS = 0.3`. Source =
  meleelight @ `27af171` (**SECONDARY** proxy; retail PM 3.6 magnitude **⚠ UNDOCUMENTED** —
  the row's derivation note must say so, not claim the ROM). Register in
  `pycats/combat/provenance.py`.
- **Removed:** `JOSTLE_MIN_VOVERLAP_FRAC` (was **TUNED** — a `provenance.py` row + a
  `TUNING_CONSTANT_NAMES` entry + an inventory-doc §2b row) and `COLLISION_PUSH_SPLIT` (a
  bare local in `core/physics.py`, unregistered). Removing the former also updates the
  drift-guard `tests/test_tuning_provenance.py` and the §2b completeness count in
  `docs/research/2026-07-07-custom-mechanics-inventory.md`.

## Consequences

- **Player-visible (lands in the DEV ticket; needs golden regen + eyeball OK):**
  fighters now **slide apart over several frames** instead of snapping apart in one; they
  **keep their momentum** through a jostle (no `vel.x` cancel); **airborne fighters no longer
  push** grounded ones.
- **The able-to-fail regression anchor:** `tests/test_player_push.py` today asserts the
  one-frame full separation **and** the velocity match — exactly the two behaviors this ADR
  removes. It must be **rewritten** to assert the gradual, position-only nudge: red against
  the new code with the old assertions, green with the new ones (revert-the-fix check).
- **#68 flyover test:** should stay green under the grounded gate — an airborne flyer fails
  the both-grounded check, so it never pushes. The DEV ticket must **verify** this, since it
  removes the gate the #68 fix originally added.
- **Faithful & greppable:** every ground number traces to one meleelight block via a
  `round(unit × PX_PER_UNIT)` derivation with its citation.
- **Ruled out:** keep-as-is (declines the V1 ask); pycats' AABB-overlap activation (the `6.5
  u → 35 px` literal was chosen instead, Fork 1); a 50 %-air placeholder (unsourced →
  deferred to #1015).

### Follow-up tickets (filed one-at-a-time downstream, on ratification)

1. **RESEARCH #1015** *(already filed)* — air jostle strength + vertical-overlap ("ratchet")
   mechanics in Melee/Brawl/PM/meleelight. Unblocks a later air-jostle ARC + DEV enhancement.
2. **DEV — *to file on ratification*** — implement Decisions 1–6 in `resolve_player_push`;
   add the FOUND constants + `provenance.py` rows; remove `JOSTLE_MIN_VOVERLAP_FRAC` +
   `COLLISION_PUSH_SPLIT` (with their drift-guard + inventory-doc references); **rewrite
   `test_player_push.py`** as the able-to-fail regression; regenerate any moved goldens
   (author ≠ reviewer, `REGEN_PROTOCOL.md`) + eyeball.

### Relationships

Downstream of #594 findings (`docs/research/character-collision-push-findings.md`) / ARC
#1003. Airborne behavior → RESEARCH #1015. Conversion seam `pycats/combat/units.py::u()`
(#785, ADR-0011). Provenance method ADR-0003 / #233. **Supersedes** the #68 vertical-overlap
gate. Source: meleelight `schmooblidon/meleelight` @ `27af171`, `src/physics/physics.js`.
