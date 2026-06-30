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

---

## B1 — Nalio f-tilt (#206, PM3.6 Mario AttackS3)

1. **Hitbox values are rukaidata-sourced; FAF/total is the one inference.**
   - rukaidata gave damage 9, angle **361 (Sakurai)**, BKB 6, KBG 100, WDSK 0,
     sizes 3.91/3.13/2.73 u, active frames 5-7 directly. The **FAF (30 → recovery
     23)** wasn't in that result; used Mario f-tilt's well-known FAF 30 (Melee/PM),
     consistent with how d-tilt recorded its total. *Revisit:* confirm against the
     rukaidata move page if exact endlag ever matters.
2. **Only the forward/mid angle variant is authored.**
   - *Why:* `move_select` has a single ground-forward key (`ftilt`); the angled
     up/down AttackS3 variants have no input to reach them. Mid variant = 9 dmg.
3. **Positions approximated (no skeleton), same convention as jab/d-tilt.**
   - Along the forward arm at dy 28; mid box at the #64 reach dx 46; fist (id0,
     r21) outermost → dx 57/46/37. Documented in the move's code comment.
4. **First real consumer of the A1 Sakurai gate** — f-tilt uses `angle=361`, no
   literal placeholder (unlike n-air's 45). End-to-end validation that #203 works.

---

## B2 — Nalio u-tilt (#207, PM3.6 Mario AttackHi3)

1. **Rejected the web-search summary; read the rukaidata move page instead.**
   - *Why:* the search summary returned implausible u-tilt values (15-16 damage,
     259° angle) — a retrieval-trust red flag (a u-tilt is a ~8% poke). Fetching
     the actual `AttackHi3` page gave the believable set used: damage 8, angle 96,
     BKB 26, KBG 125/122/120, sizes 2.73/3.52/4.69. *Lesson:* verify search
     summaries of datamined values against the primary page before authoring.
2. **Per-box KBG recorded faithfully (125/122/120), not averaged.**
   - Unlike jab/d-tilt (uniform KBG), AttackHi3's three boxes have slightly
     different growth; the `_utilt_box` helper takes kbg per box.
3. **Active window 5-11 (active 7) taken from rukaidata as-is.**
   - Longer than a Melee-memory guess would suggest; trusted the PM3.6 page (the
     project's canonical reference) over recollection.
4. **Positions approximated** as an overhead arc (small dy, id2 r25 the big sweep),
   same no-skeleton convention as the other tilts.

---

## C1 — Nalio f-air (#208, PM3.6 Mario AttackAirF) — first A2 consumer

1. **Authored as a real two-window move (early hit → meteor), not clean-only.**
   - *Why:* unlike n-air (#136, authored clean-only because A2 didn't exist), the
     #204 gate now exists, so f-air uses it: early window [16,17] angle 60, late
     window [18,22] angle 280. This is the first real consumer of A2.
2. **Meteor uses literal angle 280 (no A1 sentinel).**
   - 280° resolves down-and-forward via the existing launch code (`vel.y = -sin280
     > 0` = downward). Only 361 needs the A1 path; 280 is a normal angle.
3. **Window frame coords map rukaidata frames 1:1.**
   - pycats startup convention (startup = first_active − 1) makes rukaidata "active
     frame N" == MoveClock frame N, so active_start/active_end take rukaidata's
     16/17 and 18/22 directly. Verified by the end-to-end test (Attacks on frames
     16 and 18).
4. **Positions approximated**, late meteor boxes swung lower (higher dy) than the
   early boxes — documented; same no-skeleton convention.

---

## C2 — Nalio b-air (#209, PM3.6 Mario AttackAirB) — first dual-gate consumer

1. **First move to exercise BOTH gates at once.** The clean window (angle 28) and
   Sakurai late window (angle 361) use #204 temporal windows; the 361 late hit
   resolves through the #203 Sakurai gate. End-to-end test pins both (Attacks on
   frames 6 and 9; the late one carries angle 361).
2. **Positions behind the body (negative dx).** b-air hits backward; circles are
   facing-right-relative, so a backward box is dx<0 (mirrored for left-facing by
   the existing consumer). Clean and late share x/y (same bones 16/17), differing
   only in timing/values.
3. **Active window 6-17 (active 12) is the full envelope;** the per-box windows
   carve it into clean [6,8] and late [9,17]. recovery = IASA 29 − 5 − 12 = 12.
4. **Landing-lag / L-cancel deferred** (no system), consistent with n-air/f-air.

---

## C3 — Nalio u-air (#210, PM3.6 Mario AttackAirHi)

1. **Authored both windows even though they differ only in damage (11→10).**
   - *Why:* rukaidata lists two windows ([4,5] and [6,9]); PM-faithful means
     authoring them, consistent with f-air/b-air. Same angle 55 / BKB 0 / KBG 100.
2. **total = IASA 28 (recovery 19), not the 34-frame full duration.**
   - Consistent with the dominant convention (jab=16=IASA, f-air=45=IASA): recovery
     ends at the interruptible point. rukaidata also lists a 34-frame total duration;
     used IASA as the move's pycats total.
3. **BKB 0 recorded faithfully** — u-air's knockback is pure KBG (juggle tool), so
   base_knockback is genuinely 0, not a placeholder.
