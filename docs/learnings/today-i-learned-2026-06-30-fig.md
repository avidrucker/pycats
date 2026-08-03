# TIL 2026-06-30 — FIG

**Context:** A long NPC-AI + ledge session. Shipped the reactive-AI triad (#251 research → #254 threat-aware shielding → #274 whiff-punish), a fireball-physics thread (#263 research → #266 gravity+bounce `Projectile` → #271 tuning), then reach/spacing (#285 research, #277 parked), and a ledge-recovery research thread (#297) that filed follow-ups #311/#312. The through-line, in hindsight: **almost every misstep was an unverified premise** — a ticket's state, a test's validity, a ticket's value, a mechanic's provenance, a bug's stated cause. This TIL collects those.

---

## 1. Verify a ticket's state before calling it a blocker

**What happened:** The #250 umbrella body lists child 4 as "edge-guarding + ledge behaviour (overlaps #148 step 4 / **ledge #14**)." I read that soft cross-reference and, across ~6 turns (the #274 close, the #277 body + its issue-review, a yegor-council reading, a "park" recommendation), asserted **"edge-guard is blocked by #14."** When the user finally asked me to review #14, `gh issue view 14` showed it **CLOSED** — ledge-hang shipped that morning. I'd escalated "overlaps #14" into "blocked by #14," assumed the ticket was open, and then anchored on my own claim. Logged as error #26; the spillover (a mislabeled #277, a stale umbrella note, a wrong dependency chain in my recommendation) took a cleanup pass to unwind.

**What I learned:** A cross-reference (`overlaps`, `see`, `related`) is not a dependency, and a ticket number in prose says nothing about the ticket's *state*. Repeating an unchecked claim doesn't make it truer — it just makes the eventual correction bigger.

**The rule:** **Before writing "blocked by #N", "#N is pending", or labeling `blocked`, run `gh issue view <N> --json state`.** (Captured as error #26 + project memory `verify-ticket-state-before-blocker-claims`; the ticket-state analogue of "verify the named file still exists.")

---

## 2. A "real battle" test must be *discriminating* — able to fail when the feature is off

**What happened:** On #274 (whiff-punish) I wrote an integration test that ran a real `run_battle`-style loop and asserted the bot landed a hit. It passed. Then my revert-check (mutate the feature to a no-op) showed the **unit** tests going red but the **integration** test **still green** — a Lv9 bot lands cadence hits regardless, so the test proved nothing about whiff-punish. I rebuilt it to assert an **off-cadence attack during the opponent's recovery** (something a cadence-only bot *structurally* cannot do), and compared feature-on vs feature-off. Now the mutation reddens both.

**What I learned:** This is the #248 gotcha one level deeper. "Prove it in a real battle, not a stub" isn't enough — a real-loop test that passes whether or not the feature works is as useless as a stub. The mutation/revert-check is what exposes it.

**The rule:** **An integration test must be constructed so it FAILS with the feature disabled — assert a state or timing only the feature can produce, and run the revert-check on the integration test too, not just the units.** (Extends RULES.md "every fix lands a test able to fail" to real-loop tests.)

---

## 3. Ground a "READY" ticket in the actual code before claiming — readiness ≠ value

**What happened:** #277 (reactive spacing/approach) passed an issue-review at 14/15 and I was about to TDD it. Reading the controller first: it already walks to `standoff` (30px) and attacks from `standoff-18..attack_range` (12–45px), so it was **already** approaching and attacking when safe. The only genuinely-new bit (retreat) is preempted ~85% of the time by the #254 shield, and real footsies needs reach asymmetry — which exists in the *move data* (Nalio jab dx≈54 vs Birky ≈38) but is invisible to the controller (hardcoded `attack_range=45`). I paused, filed #285 (reach-awareness research), and parked #277.

**What I learned:** An issue-review scores *clarity*, not *value*. A ticket can be perfectly specified and still describe work that's already done or marginal — and only reading the implementation reveals it.

**The rule:** **Before claiming even a well-reviewed ticket, confirm its premise against the code that would change; "READY" answers "is it clear," not "is it worth building."**

---

## 4. Confirm a mechanic is actually in PM before speccing it — one mis-attribution propagates

**What happened:** The ledge research (#297) hit the reference doc's claim that **ledge-trump** is "first-class in the Brawl/PM family." Two SmashWiki fetches contradicted each other, so — fresh off error #26 — I dug into PM-specific sources instead of picking a side. Result: **ledge-trump (auto-removing a ledge occupant) is a Smash-4/Ultimate mechanic and is NOT in Project M; PM uses edge-hogging.** pycats' one-occupant lockout was therefore already PM-faithful, and #267's slated "ledge-trump" slice was a Smash-4 mechanic on a PM roadmap. Removed it.

**What I learned:** "PM is Brawl-derived" cuts both ways — a mechanic can look like it belongs and actually postdate PM. A single mis-attributed line in a reference doc had been about to spawn DEV work for a mechanic the game shouldn't have.

**The rule:** **Before implementing a "PM" mechanic, verify it's in PM (not a later Smash) with a PM-specific source — and when two secondary sources conflict, go to the primary community, don't average them.**

---

## 5. Root-cause the symptom in a real loop before accepting the reported cause

**What happened:** The fireball "sailed over grounded foes." The parent ticket guessed a **spawn-height bug** (tied to the #192/#195 guessed-value trackers). Stepping a real loop with `process_hits`: the fireball spawns at the thrower's body-centre (correct), and a **same-elevation** shot connects (+7%). The whiff was purely **cross-elevation** — a *flat* projectile fired from the upper thin platform (cy≈260) flies over a foe on the main platform (cy≈380). The real gap: #223 shipped flat travel = **Luigi's** fireball, but Nalio is the PM **Mario** archetype (gravity + ground-bounce). Fixed the trajectory model (#266), not a spawn height.

**What I learned:** The reporter's diagnosis is a hypothesis. Had I "fixed" the spawn height I'd have chased a non-bug; the actual fix was a different subsystem entirely.

**The rule:** **Reproduce to ground truth and root-cause in a real loop before accepting the stated cause — the diagnosis in the ticket can point at the wrong subsystem.**

---

## 6. An umbrella is not a work unit — slice, cap WIP, record the decision

**What happened:** Asked whether #250 was "ready to take," the honest answer was that it's a *tracker*, not claimable. I convened the yegor personas, kept WIP=1, filed scoped children one at a time (splitting whiff-punish #274 from spacing #277 for single-deliverable), and recorded each decision as a ticket comment (incl. the council convergence on #250).

**What I learned:** "Take the umbrella" is a category error; the takeable unit is always a scoped child. And a decision that isn't written on the ticket effectively didn't happen — the correction comments on #250 were only possible because the reasoning was recorded there.

**The rule:** **Never claim an umbrella; file its next scoped child (WIP=1) and write the decision on the ticket.**

---

## What landed

| Ticket | Outcome |
|---|---|
| #251, #263, #285, #297 | Research/findings docs (AI decision model, fireball trajectory, reach-blindness, ledge recovery) |
| #254, #274, #266 | DEV shipped (threat-aware shield, whiff-punish, gravity+bounce `Projectile`) |
| #271, #311, #312 | Follow-up trackers filed (fireball tuning, true PM edge-hog, AI ledge usage) |
| #277 | Parked (`blocked` by #285) after grounding revealed a thin premise |
| #267 | "Ledge-trump" slice removed (not a PM mechanic) |

## Open threads

- **Meta:** five of six lessons here are the same shape — *verify the premise before acting*. Worth watching whether that's an over-general takeaway or a real recurring failure mode across sessions.
- The exact PM per-character percent→ledge-invincibility schedule is still a gap (#311 will pull it at implementation).

## Related artifacts

- Errors #26 (blocker mis-attribution), #27 (transient classifier outage)
- Memory: `verify-ticket-state-before-blocker-claims`
- Research docs: `docs/research/2026-06-30-{cpu-ai-decision-model,nalio-fireball-trajectory-hurtbox,ledge-recovery-mechanics}.md`
