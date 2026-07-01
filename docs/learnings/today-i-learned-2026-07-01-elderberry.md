# TIL 2026-07-01 — ELDERBERRY

**Context:** A long session almost entirely on NPC AI. The centrepiece was the
cross-platform-stall epic **#365** — pin the mechanism (**#367**), fix it (**#369**),
validate the follow-up design against Smash CPU AI (**#376**), then build the guarded
backstop (**#368**) — plus a related controller cleanup (**#379**). Alongside: demo
readability (#351/#352/#356), `PX_PER_UNIT` naming (#195), and the position-fidelity
research verdict (#310). Several lessons repeated across tickets, which is why they're
here.

---

## 1. A held key is one press, not a stream

**What happened:** #367 pinned why two level-9 bots froze on separate platforms and
idled for 30 seconds. The controller's jump-toward-elevated-target did
`held.add(keys["up"])` on *every* frame the gate held. But a jump fires on a fresh
*press edge* — `__call__` computes `pressed = held - prev` — so holding `up`
continuously produced **exactly one** press, one jump, and then a permanent
idle-holding-`up` limit cycle. The bot was "acting" every frame (its policy emitted a
valid key) yet never moved. #379 was the same shape in miniature: a reactive-roll
emitted every frame but got dropped.

**What I learned:** "the AI decides an action every frame" is not the same as "the AI
*does* something every frame" when the input layer is edge-triggered. A policy that
keeps asserting an edge action is indistinguishable, at the game's input boundary, from
a policy that asserted it once.

**The rule:** **Edge-triggered inputs (jump, dodge) must be PULSED — released
periodically so a fresh press re-fires; a continuously-held key emits exactly one
action, however situation-aware the policy is.** (#367/#369.)

---

## 2. Narrow a sim-behaviour fix so goldens + seeded tests stay byte-identical — let data pick the threshold

**What happened:** #369's first cut pulsed *every* jump-up (`frame % 2`). It broke the
golden full-match AND a seeded `reactive_spacing` test, because it perturbed every
leveled battle. I narrowed it to pulse *only when genuinely stuck* (a counter that
resets the moment the bot leaves the ground), then measured the gap: normal
grounded-below-target runs top out at ~40 frames (seed-1), the actual stall ran 643 —
so a threshold of 90 sits cleanly between them. #368 (leveled-only, fires only on true
no-progress) and #379 (default controller never reaches the gate) followed the same
discipline.

**What I learned:** in a deterministic sim, *any* behaviour change ripples into every
seeded and golden trajectory. The fix has to be scoped so the normal / level-less /
pinned paths are untouched, and when a threshold separates "normal" from "pathological,"
the separating value should come from *measured* data, not a guess.

**The rule:** **Gate an AI/sim behaviour change so the golden and normal paths stay
byte-identical; when a threshold divides normal from pathological, measure both
distributions and pick a value in the gap.** (#369/#368/#379.)

---

## 3. A legitimate fix can invalidate a seeded test's PREMISE — re-scope it faithfully, don't re-seed to green

**What happened:** #379 gated the reactive-roll on `hurt_timer`/`stun_timer`. That made
an existing real-battle test's `assert on > 0` (evade bot emits rolls) go red — because,
per the #370 diagnosis, *every* roll in that jab-lock scenario was a wasted hitstun emit
the fix correctly removes. The test's premise ("a dodge-able label implies a valid
roll") was the exact assumption #370 disproved. I repurposed the test to assert the
*wasted* count is 0 (the real acceptance criterion), rather than seed-hunting for a
scenario that still produced a roll. Same shape earlier: #309 widened a `battle_log`
observation window (the fix shifted the seed-3 trajectory), and #352's caption-dwell
pivoted from "insert idle frames" to a presenter freeze once I saw the choreography was
frame-tuned.

**What I learned:** when a fix breaks a deterministic seeded test, there are two very
different causes. Either the fix merely *perturbed* the seed (widen/adjust the
observation) — or the test was *asserting the bug* (rewrite the assertion to the
corrected behaviour). Re-seeding to restore a now-false claim hides the second case.

**The rule:** **When a fix breaks a seeded test, decide whether the fix perturbed the
seed or invalidated the test's premise; rewrite the assertion to the corrected reality —
never re-seed just to go green.** (#379/#309/#352.)

---

## 4. Controller code touching `fighter.*` must use `getattr` — the stubs are minimal namespaces

**What happened:** I hit the same `AttributeError` three times. New controller code read
`a.fighter.percent` (#368) and `a.fighter.hurt_timer` (#379); both broke
`test_cpu_difficulty` / roll stubs built as `SimpleNamespace(is_alive=…, on_ground=…)`
with nothing else. (#291's `grabbed_ledge` was the first instance.) Each cost a red test
and a defensive rewrite to `getattr(a.fighter, "x", default)`.

**The rule:** **AI/controller code reading `a.fighter.*` must `getattr(..., default)` —
unit-test stubs are minimal namespaces, not real `Fighter`s.** (Memory:
`getattr-stub-safety`; #368/#379/#291/#137.)

---

## 5. `cat`/`grep` does not satisfy the Edit read-gate in a worktree

**What happened:** six `EDIT_PRECOND` error rows over the session (ids 31/36/39/40 mine).
Each time I'd `sed`/`grep` a *worktree* file to plan an edit, then call `Edit` and get
"File has not been read yet." Shell reads don't register with the harness's file-state
tracker, and a worktree is a *different path* than the main checkout, so reading the
main copy doesn't count either. I saved a memory mid-session; the recurrence dropped to
zero across the last several tickets once I made Read-before-Edit a habit.

**The rule:** **Use the Read tool on the exact worktree path before the first Edit —
`cat`/`grep`/`sed` do not satisfy the read-gate, and the main-repo copy is a different
path.** (Memory: `read-before-edit-in-worktrees`.)

---

## 6. Validate a fix's DESIGN against domain authenticity before building it

**What happened:** #376 was a spike I filed and took *before* building the anti-stall
backstop (#368). The obvious mechanism — "force an approach after N idle frames" — turned
out to be both a band-aid *and* unfaithful: pycats bots legitimately hold at standoff
spacing (`decide()` returns no horizontal move in the standoff band), and real Smash CPUs
space and bait, so a blanket idle timer would make them abandon spacing and rush in —
strictly *less* Smash-faithful (#343). The spike reshaped #368 into a narrow
no-progress detector (with a faithfulness-guard test) and named situation-aware
robustness (#250) as the primary direction. Building the naïve version first would have
shipped a regression to authenticity.

**What I learned:** the intuitive fix mechanism is sometimes the wrong one on
*authenticity* grounds, not correctness grounds. A cheap design-validation spike — scoped
to confirm the *approach*, not just tune the numbers — can change what you build.

**The rule:** **Before building a behaviour fix, validate its design against the domain's
ground truth; the intuitive mechanism may be unfaithful, and a spike that confirms the
approach is cheaper than reverting a shipped regression.** (#376/#368/#250.)

---

## What landed

| Ticket | Change |
|---|---|
| #367 | research: pinned the held-not-pulsed jump-up limit cycle (instrumented the real controller) |
| #369 | fix: pulse the jump-up only when stuck; standoff 625→74 frames |
| #376 | research: verdict — blanket idle timer is a band-aid + unfaithful; situation-aware is primary |
| #368 | feat: narrow no-progress anti-stall backstop (defence-in-depth) with a faithfulness guard |
| #379 | fix: gate the reactive-roll on hurt/stun timers, not the lagging FSM label |
| #351/#352/#356 | demo readability: `--demo-speed` slow-mo, presenter caption-dwell, numbered captions |
| #195 | `PX_PER_UNIT` named constant + `u()` helper; single-sourced the ×5.4 comments |
| #310 | research: hitbox positions are a "feel" provenance ceiling (no unit→pixel), scalars stay datamined |

## Related artifacts

- Epic wrap-up: issue #365
- Prior ELDERBERRY TIL: [2026-06-26](./today-i-learned-2026-06-26-elderberry.md) (PM units, golden-safe archetype seams)
- The one-frame FSM-label-lag lesson this session's #379 builds on: [TIL 2026-06-24 CHERRY](./today-i-learned-2026-06-24-cherry.md) (#8)
