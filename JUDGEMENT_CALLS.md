# Judgement calls — Nalio playable-kit initiative (#142)

A running log of non-obvious decisions CHERRY made while executing the
"finish Nalio's playable kit" plan, so they're auditable and reversible.
Each entry: what was decided, why, and how to undo/revisit.

---

## A1 — Sakurai-angle (361) gate (#203, landed @ 4808e59)

1. **Constants: airborne 40°, grounded max 40°, KB thresholds 60→88.**
   - *Why:* Brawl/PM-derived (SmashWiki "Sakurai angle" lists Brawl-onward
     low/high KB ≈ 60/88 and a 0→~40° range; Melee is ~44°). pycats' `knockback()`
     returns Smash-unit-comparable magnitudes, so the raw thresholds map directly.
   - *Status:* ⚠ playtest starting points, not exact PM values — exposed as
     `SAKURAI_*` in `config.py` and labelled as such, like the crouch/prone numbers.
   - *Revisit:* tune after playtesting; could move per-character into `FighterData`.

2. **Corrected docs beyond the strict code change.**
   - Fixed the *inverted* prose in `docs/pm-reference/combat-knockback-hitstun.md`
     (it claimed weak hits = ~44°, flattening as KB rises — backwards from real
     Smash) and flipped the `current-parity-progress-report.md` Sakurai row ⬜→✅.
   - *Why:* the doc would have actively misled the next agent authoring an aerial,
     and a regression test was about to pin the *correct* behaviour. In the spirit
     of #194 (keep the parity report honest).
   - *Revisit:* if either doc is "owned" elsewhere, fold these into that owner's flow.

3. **Test pins the mechanism, not magic angles.**
   - `test_sakurai_angle.py` asserts airborne-fixed, grounded flat→max, monotonic,
     and the end-to-end launch — but keys off the `SAKURAI_*` constants rather than
     hard-coded degrees, so retuning the playtest values won't make it brittle.

---

## A2 — per-hitbox temporal windows (#TBD, ticket drafting)

1. **Low-churn design: `MoveTick` and `player.py` stay untouched.**
   - *Why:* the first draft widened `MoveTick` to a list of spawn-groups, which
     would have forced `test_move_clock.py` to change and risked the goldens.
     Instead, `MoveClock` tracks *which windows have spawned* in a `set` (not a
     single `_spawned` bool) and returns **at most one** spawn-group per frame, so
     `MoveTick`'s `(spawn, lifetime, in_air)` shape is unchanged and `player.py`'s
     consumer loop is unchanged. Only `data.py` (+2 optional `Hitbox` fields) and
     `move_clock.py` (spawn tracking) change.
   - *Constraint accepted:* hitboxes that share a start frame must share the same
     window (same end) — they spawn as one `Attack`. Rare in practice; documented
     v1 limit, rejected by validation rather than silently merged.
   - *Revisit:* if a real move ever needs two different-length windows starting on
     the same frame, lift the constraint (then `MoveTick` does need the list shape).

2. **Scope: engine capability + synthetic test only; no real-move enrichment.**
   - *Why:* the approved plan separates the gate (A2) from move authoring (C) and
     n-air's late-hit enrichment (D). Council (REQ/plan rung-1) confirmed
     engine+synthetic-test is the complete, single deliverable.

3. **One ticket, not split into schema vs spawn-wiring.**
   - *Why:* a schema with no spawn-wiring is a non-functional dead-field
     intermediate; the two can't ship independently. ~50m fits the microtasks
     budget. (architect rung-5 + objective budget.)
