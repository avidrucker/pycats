# TIL 2026-07-04 — DRAGONFRUIT

**Context:** A long fleet session spanning combat data (#459 Birky smashes), a showcase
beat (#432 fireball), three grounded research docs (#487 library survey, #470 test-suite
audit, #497 test-double policy), a RULES codification (#418), several decision tickets
(#492 ruff, #493 statecharts-pip), and multiple orchestration + council passes. The
through-line: a ticket's *premise* is a hypothesis, and half the value was disproving one.

---

## 1. A ticket's premise is a hypothesis — prove it in the real loop before you build (or close)

**What happened:** #429 asked me to "add a `special` action so specials are scriptable,"
with an explicit "able to fail: without the action, `special` is never pressed." Before
claiming, I ran the actual `run_battle` loop headless with a scripted neutral `special` on
Nalio — the fireball spawned at frame 54 (press 40 + startup 14) and travelled 670px, on
**untouched `main`**. `compile_timeline` already accepted a `"special"` span (the keymaps
bind it) and *nothing validates spans against `ACTIONS`*. The feature already worked; the
acceptance criterion was unachievable (a behavioral test is green before any change).

**What I learned:** The ticket wasn't wrong about the goal — it was wrong about the
*current state*. If I'd "implemented" it (a one-line `ACTIONS += ("special",)`) and closed
it "fixed the gap," I'd have committed a false premise to the tracker. Instead I surfaced
the repro, convened the council (the empirical repro *settles* the premise — it's not a
vote), and the reporter chose option B: close as already-satisfied, unblock #432.

**The rule:** Run the real loop and reproduce a ticket's premise before claiming it; a
premise that's false on `main` is a finding to surface, not work to silently perform.
(Extends RULES → *Fixing bugs* "surface the contradiction before an outward-facing close.")

---

## 2. Pull the canonical source — it corrects your own ticket

**What happened:** For #459 (Birky's smashes) I wrote the ticket first, describing the
d-smash as a Marth-style *front-then-back temporal split* (mirroring Narz). When I fetched
the real rukaidata PM3.6 Kirby data (`AttackLw4`), it showed a **simultaneous** front+back
splits-kick with an early/late damage falloff — not a temporal split at all. The same pull
also refuted the "blocked by engine prereqs" framing: the charge engine was already
character-agnostic (built for Nalio/Narz), and fast-fall is an *air* mechanic irrelevant to
*grounded* smashes.

**What I learned:** My own ticket carried two assumptions that the canonical data quietly
overturned. Authoring-then-sourcing let the wrong shape reach the ticket body; sourcing
first would have caught it.

**The rule:** Pull the canonical source (rukaidata / the code) before finalizing a ticket's
values *and* its framing — it routinely corrects the assumptions you baked in.

---

## 3. The sim is the oracle for frame-tuned choreography — prototype the insert before editing

**What happened:** #432 asked for a fireball beat in the 7-beat showcase, whose beats are
each frame- and position-tuned and window-gated by tests. Rather than guess an insertion
point, I dumped per-frame P1/P2 position + grounded + facing across the run and found the
one spot that fit: post-combo (f335–344), Nalio idle at x=592 facing right, Birky 116px
ahead. Then I built the insert+shift in a throwaway script and confirmed the downstream
roll and ledge beats *still passed* before touching the real file — Nalio is stationary
while firing, so shifting the later beats +80 frames kept them byte-for-byte behaviorally
identical.

**What I learned:** For position/frame-tuned sim work, the sim itself tells you where a beat
can go and whether an edit desyncs the rest — cheaper and safer than editing then debugging.

**The rule:** Let a probe find the frames and prove no-desync *before* editing tuned
choreography; pick an insertion point where the actor is stationary so downstream beats
shift cleanly.

---

## 4. Ground research in the repo — and a deeper look will correct the quick read

**What happened:** Three research docs this session were only useful because they were
grounded in grep'd repo state, not generic advice. #487 concluded `ruff` dominates
`pyflakes` (its `F` rules *are* pyflakes) and reconciled with the same-day #486 pyflakes
decision — which I then superseded via #492 and closed #486. #470 audited the suite and
found it healthy (asserts real, 1-of-174 mock files). Then #497 (test-double policy) looked
harder at that one mock file and found it was a *justified spy* (verifying menu→widget
routing — the interaction is the contract), **downgrading my own #470 finding E** from
"Inspector anti-pattern" to "defensible, keep." #497 also found the project already
fake-friendly: seeded-RNG DI, frame-based time (no clock to fake), `PYCATS_CONFIG_DIR →
tmp_path` persistence.

**What I learned:** The parent audit's quick classification is a lead, not a verdict; the
child research that applies it will refine — sometimes reverse — it. Grounding in the actual
code is what makes both the finding and the correction real.

**The rule:** Anchor every research verdict in grep'd repo evidence, and let a follow-up's
deeper read revise the parent audit's quick reads rather than inheriting them.

---

## 5. Author ≠ reviewer — your self-scores are advisory; route your own tickets to someone else

**What happened:** I ran `/issue-review` on tickets I had filed (#462, #504) and scored them
15/15, and ran yegor-personas twice. The council's authority ladder kept resolving the same
way: an empirical repro settles a premise (rung 3, objective), the reporter owns the A/B
call on their ticket (rung 4), and my own review of my own ticket is **advisory only**
(author ≠ reviewer). #459 closed on its green suite (the binary gate), not on my blessing.
In orchestration I deliberately routed my own filed tickets to other agents (#462 → CHERRY,
#470 → GRAPE).

**What I learned:** Being the one who found the issue, wrote the ticket, and would do the
work makes my "READY 15/15" self-assessment carry no independent authority — it's easy to
grade your own homework generously.

**The rule:** Treat your review of your own ticket as advisory; the real gate is an
independent agent or a green binary gate, not your own score.

---

## 6. A lesson only counts once it's in RULES.md (and mind the worktree-import footgun)

**What happened:** #418 codified two recurring disciplines into a new RULES.md `## Testing`
section (golden-safe-by-default; AI tests must drive the real loop *and* be discriminating),
from TIL #417 — a diary lesson made into project law. Separately, a probe of mine threw
`StopIteration` looking for the fireball caption: I'd set `PYTHONPATH` to the **main repo**,
so it imported the un-edited `showcase.py` instead of my worktree's. Pointing `PYTHONPATH`
at the worktree fixed it.

**What I learned:** A lesson in `docs/learnings/` expires with the session unless it becomes
a RULES entry or a filed authority ticket. And a worktree edit is invisible to a script
unless the script's import path points at the worktree, not the main checkout.

**The rule:** Codify a new rule into RULES.md (or file the authority ticket) in the same
breath as the TIL; and set `PYTHONPATH` to the *worktree* for any probe of worktree-local
edits.

---

## 7. An empty bug queue is a valid state — don't fabricate work to fill it

**What happened:** A bugs-only orchestration pass found **zero** open bugs — no `bug`-label,
no `bug:`/`fix:` titles, no open `severity:*` defects, nothing in-flight. I distinguished a
*clean state* from a *detection gap* by confirming bugs had been actively closing (#437,
#424, #423, …), and declined to pull non-bug work into a "bugs only" round. The right way to
repopulate the queue is to *find* defects — which is exactly #504 (a sampled mutation /
revert-check pass to surface Liar tests as real, test-backed bugs).

**The rule:** When a scoped queue is empty, report it as a clean state (with evidence it's
not a detection gap) and don't manufacture out-of-scope assignments; point at the
bug-*finding* work instead.

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/characters/birky_cat.py` | Birky's chargeable f/u/d-smash MoveData (#459) |
| `pycats/sim/showcase.py` | Fireball showcase beat + shifted roll/ledge (#432) |
| `docs/research/2026-07-03-library-framework-survey.md` | Library survey; ruff ≻ pyflakes (#487) |
| `docs/research/2026-07-03-test-suite-audit.md` | Test-suite audit, ranked findings (#470) |
| `docs/research/2026-07-03-test-doubles-policy.md` | Fakes/stubs/spies/mocks house rule (#497) |
| `RULES.md` | New `## Testing` section (#418) |
| tickets | Filed #457/#459/#462/#469/#470/#492/#493/#496/#497/#504; closed #386-era premise #429 + superseded #486 |

## Related artifacts

- [TIL 2026-07-01 DRAGONFRUIT](./today-i-learned-2026-07-01-dragonfruit.md) — the golden-safe-by-default + discriminating-AI-test lessons #418 codifies
- [TIL 2026-07-03 ELDERBERRY](./today-i-learned-2026-07-03-elderberry.md) — "specials can't be scripted was wrong" (the pushback that seeded #429)
- Issues #429, #432, #459, #470, #487, #497, #418, #504
