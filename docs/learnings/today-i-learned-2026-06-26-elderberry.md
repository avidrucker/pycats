# TIL 2026-06-26 — ELDERBERRY

**Context:** Took the "Nalio" (Project M *Mario* archetype) cat from research to
playable mechanics: unit-system research (#120), the Mario→pycats spec (#119),
the per-character `FighterData` slice (#123), per-character movement constants
(#126), and crouch (#124). These lessons are about porting Smash data faithfully
and adding behaviour to a deterministic, dual-backend, golden-oracled sim without
breaking it.

---

## 1. PM combat numbers drop in raw; only *spatial* values need one scale constant

**What happened:** #120 asked whether pycats can consume raw Melee/Brawl/PM
values. I verified term-by-term that `combat/knockback.py` *is* the Brawl/PM
knockback formula, so BKB/KBG/weight/damage/percent/angle and frame counts (both
run fixed 60 FPS) feed it **unchanged**. The only thing that needs converting is
length/speed/gravity — and there's no canonical unit→pixel mapping in Smash (the
camera zooms). The surprise: reverse-deriving from PM3.6 Mario, pycats' *existing*
`GRAVITY 0.5`, `MOVE_SPEED 6`, and full-hop height all independently land on
**≈5.4 px per Smash unit** — pycats' movement was already de-facto calibrated to
PM Mario.

**What I learned:** "Can we use the raw values?" splits cleanly into two layers.
The *combat* layer is unit-agnostic in its inputs (the formula doesn't care about
px), so it's literally raw. The *spatial* layer needs exactly one anchored
constant, not a per-value guess.

**The rule:** **Enter PM combat data raw; convert spatial values with a single
`PX_PER_UNIT ≈ 5.4` anchored on Mario — never hand-convert per value.**

---

## 2. A new archetype key / state is golden-safe *because of what the replay never presses*

**What happened:** Before adding the Nalio key (#123) and crouch (#124) I assumed
goldens were at risk. They weren't: `load_fighter_data` is called with
`char_name="P1"/"P2"` (not the cosmetic cat key), so a new `"nalio"` key is
unreachable by the sim path; and the golden `default_timeline` has **zero `down`
spans**, so mapping down→crouch can't perturb the default/combat goldens. The
full_match/two_npc goldens *did* change — because the chase bot holds `down` on
the main floor, which now legitimately crouches.

**What I learned:** Golden-safety isn't "did I touch sim code," it's "can the
recorded scenarios reach the new branch." Five minutes grepping the actual input
timelines and the `load_fighter_data` call sites told me exactly which goldens
were safe and *why* the others changed — so regenerating them was a confident
semantic review (only crouch-driven diffs, all state labels valid), not a
rubber-stamp.

**The rule:** **Before adding a branch, find the exact inputs/keys the goldens
actually drive; only regenerate goldens once you can explain every diff.**
(Reinforces the golden-discipline convention in `off-pixel-coordinates-findings.md`.)

---

## 3. Every new fighter state must land in BOTH backends, in identical order

**What happened:** Crouch (#124) is a `grounded` leaf. pycats runs two
parity-locked state engines — the statechart (`charts/fighter_chart.py`) and the
legacy FSM (`systems/fighter_fsm.py`) — and `test_parity` asserts byte-identical
snapshots. I had to add the `crouch` leaf to the statechart, the matching state +
transitions to the FSM **in the same priority order**, and the label to
`state_engine_sc.LABELS`. I added a down-holding parity test so the crouch path
is provably identical, not just the no-down default.

**What I learned:** The legacy FSM isn't dead code — it's the parity oracle. A
state added to only one backend passes its own unit tests and then explodes in
`test_parity`. Transition *order* is part of the contract, not just the set.

**The rule:** **A new fighter state is three coordinated edits (statechart leaf +
legacy FSM state in identical order + `LABELS`), and isn't done until a
scenario that reaches it is byte-identical across backends.**

---

## 4. Snap the sim, animate the render — keep visual state off the snapshot

**What happened:** The crouch "rect goes squarish" animation could have meant
interpolating the *collision* Rect over frames — which would churn the
deterministic integer-rect sim. Instead the collision Rect **snaps** to the
crouch box (deterministic, derived from the state label so both backends agree),
and `render_battle` eases a *render-only* `_crouch_anim` progress var to squash
the drawn body. The snapshot never sees the tween, so determinism/parity are
untouched, and the headless sim simply never runs it.

**What I learned:** "Animated" is a render concern; "resized" is a sim concern.
Conflating them would have put float interpolation into the part of the system
whose whole value is integer determinism.

**The rule:** **Put smoothing/easing in the render layer with state that never
enters the snapshot; let the sim make discrete, label-derived jumps.**

---

## 5. Don't ship a no-op seam you can't test — defer it until a real case makes it able-to-fail

**What happened:** #123's scope included threading the live `weight` into the
Fighter. But Nalio's weight is 100 == the default, so the wiring would have been
a behaviourally invisible no-op with no able-to-fail test. I deferred it and
filed #126, where lifting *all* movement constants (gravity/fall/speed/jumps)
into `FighterData` finally had a non-default case — an injected custom-gravity
`FighterData` whose Player measurably falls faster — making the wiring
revert-verified able-to-fail.

**What I learned:** The repo's "tests must be able to fail" rule (RULES.md →
Fixing bugs) is also a scoping signal: if you can't write a test that goes red
without the change, the change is premature. The honest move is to defer the seam
to the slice that introduces an observable difference.

**The rule:** **If a seam is a no-op for the only data that exercises it, don't
ship it — defer to the slice where a non-default case makes it able-to-fail.**

---

## What landed

| Ticket | Change |
|---|---|
| #120, #119 | Research: Smash unit systems + sources; PM3.6 Mario→pycats spec |
| #123 | `FighterData.weight` + Nalio archetype data + down-tilt (golden-safe) |
| #126 | Per-character movement constants + live weight, read per-fighter |
| #124 | Crouch state (both backends) + collision-Rect resize + crouch hurtbox + render squash |
| #125, #135 | Filed: per-move claw/fist visuals (blocked on #38); crouch-cancel follow-up |

## Open threads

- The chase bot (#46) now freezes in crouch when it taps `down` on the main floor
  — a side effect of crouch, surfaced on #124. Bot input semantics may want
  scoping so it only presses `down` to drop through *thin* platforms.
- Wiring a *selected cat → its archetype* `FighterData` is still unfiled; it's
  what makes Nalio actually playable in the live game (distinct from the cosmetic
  skin selection #16).

## Related artifacts

- `docs/research-120-smash-units-and-sources.md`, `docs/research-spec-119-mario-cat-pm.md`
- Issues #119 #120 #123 #124 #125 #126 #135
- Sibling TILs: [cherry](./today-i-learned-2026-06-26-cherry.md),
  [dragonfruit](./today-i-learned-2026-06-26-dragonfruit.md)
