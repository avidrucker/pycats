# TIL 2026-07-03 — FIG

**Context:** A long session across three threads: finishing movement slice 2b (double-tap
dash, #403), running the whole **magic-number audit epic** (#410, 7 children), and the
**PM-parity marker sweep** (#408 Axis A) — which then spun a jump-mechanic ruling (#466 →
#473) into a full **spawn/respawn** research + epic (#480 → #482). The recurring theme:
when to *act*, when to *prove*, and when to *ask*.

---

## 1. Calibrate before executing a planned sweep

**What happened:** The #410 epic ordered its module sweep "formula-dense first" — combat,
then systems. I reconned before claiming the first child and found combat was *already*
factored: ADR-0003's provenance registry (`combat/provenance.py` + `test_tuning_provenance`)
already forces every combat/physics constant into `config.py` with a cited source. Systems
was clean too. The real magic-number debt was in **render/UI** (`render_battle.py` ~100
literals, `char_select.py` ~76), which has no provenance discipline. I reordered the whole
epic on the spot and reported the already-clean modules as findings.

**What I learned:** A plan's ordering encodes an assumption about where the work is. That
assumption can be stale — especially after prior tickets already did some of it. Ten minutes
of `grep` recon reordered a seven-child epic.

**The rule:** **Recon the actual state before trusting a multi-step plan's ordering; report "already clean" as a finding, not a silent skip.** (Authority: #484.)

---

## 2. An identity refactor needs a proof — and the proof needs its own able-to-fail check

**What happened:** Most audit children were identity refactors (literal → equal-value named
constant). For `render_battle.py` the golden render-parity test covered the HUD text but
**not** the fighter-sprite cosmetics — I proved that by flipping a stripe-offset constant and
watching the suite *stay green*. For `char_select.py`/menus there were no pixel goldens at
all (`test_screen_parity` is an **FSM state-trace**, not pixels). So I hashed `render()`
across states before and after, and — critically — flipped one constant to confirm the hash
harness actually *reds*. Without that flip, a hash harness that silently caught an exception
would "pass" vacuously.

**What I learned:** "Suite stays green" only proves identity if something actually tests the
changed code. When goldens are thin, build the proof (a render-hash) — and then prove the
proof can fail.

**The rule:** **For an identity refactor where goldens are thin, hash the render across states before/after; always able-to-fail-check the harness by flipping one value.** (Authority: #484.)

---

## 3. The stale-`.pyc` revert-check footgun

**What happened:** During an able-to-fail check I flipped a constant with `sed`, ran the
hash, then `sed` it back — and the "restored" hash still showed the *flipped* value. The two
`sed` edits landed in the **same wall-clock second** with **identical file size**
(`170`↔`171`), so Python's `.pyc` invalidation (mtime + size) saw no change and served the
**cached bytecode**. Clearing `__pycache__` (or running `python -B`) fixed it.

**What I learned:** Byte-for-byte-sized edits within one second are invisible to CPython's
bytecode cache. A revert-check can silently test stale code.

**The rule:** **Around same-second `sed` flip/restore revert-checks, clear `__pycache__` (or use `python -B`) before re-measuring.** (Reinforces the existing "mutation-check stale .pyc" memory.)

---

## 4. Convention-once over marker / constant soup

**What happened:** Two different tasks, one principle. In the marker sweep (#408), the audit
worklist said to mark ~27 near-identical "positions approximated (bones not modelled)"
comments with `⚠`. Doing it, I realized that's exactly the **"marker soup"** the #448 design
flags as a top risk — it drowns `grep ⚠` (a *guessed value*) under a repeated *convention*.
I stopped and surfaced it; the reporter chose **mark the convention once** (a docstring note),
leaving the repetitions clean. The same principle governed the config grouping pass (#450): I
consolidated genuinely-duplicated values (the P1/P2 accent colours, the `128` overlay alpha)
but **refused to merge coincidentally-equal font sizes** — `24` as HUD-font vs confirm-font
vs caption are different roles; merging them would couple unrelated screens.

**What I learned:** DRY applies to *concepts*, not to equal *values*. Marking or merging every
repetition/coincidence is anti-signal: it couples the unrelated and buries the meaningful.

**The rule:** **Mark or name a repeated convention in one authoritative place; never merge coincidentally-equal values of different roles.** (Authority: RULES.md → "PM-parity markers", added this session.)

---

## 5. Research produces a design *choice*, not a unilateral fix

**What happened:** A `#### TODO: determine whether walking off a ledge consumes a jump`
became research #466. The PM answer was unambiguous (walk-off forfeits the grounded jump;
pycats keeps both — a divergence). The reflex is to file the fix. But pycats has *open
game-feel* questions in that exact area (#458 "is the ledge too easy to fall off of?"), and
the extra jump is a recovery-leniency. So I presented **A (fix to PM) vs B (deliberate
divergence)** rather than auto-filing. The reporter picked A → DEV #473. Then, scoping #473's
edge cases, I found pycats spawns fighters **airborne with no invincibility** — a far bigger
divergence — which became research #480 (web-cited PM revival-platform mechanics) → the
**full-PM** decision → epic #482. One `❓` TODO reshaped into a multi-ticket workstream, each
step a reporter decision.

**What I learned:** Parity is a fact; whether to *adopt* it is a decision — and it collides
with game-feel intent that only the reporter owns. Research should hand over findings + a
framed choice, not a fait-accompli fix. Chasing the edge cases of one fix is also how you
find the *real* divergence.

**The rule:** **When a parity fix collides with possible game-feel intent, surface the options to the reporter; research delivers findings + a choice, not a unilateral fix.** (Authority: #484.)

---

## What landed

| Artifact | Change |
|---|---|
| `fighter_input.py` / `fighter.py` / `config.py` | Double-tap dash detection (#403, slice 2b of #388) |
| epic #410 (7 children #415–#450) | Magic-number audit: render_battle, char_select, entities, menus, sim, win_screen/physics, config grouping |
| `characters/*.py`, `config.py`, `RULES.md` | PM-parity marker sweep #408 Axis A (#454/#456/#461/#467); RULES "PM-parity markers" section |
| `docs/research/2026-07-03-pm-spawn-respawn-mechanics.md` | PM spawn/respawn spec (#480), ratified full-PM |

## Open threads

- Epic #482 (full-PM respawn) — slices filed one at a time; #473 (takeoff jump clamp) is the prerequisite.
- #484 — codify lessons 1/2/5 into RULES.md.

## Related artifacts

- Issues #410, #408, #466, #473, #480, #482, #484
- Sibling TIL: [today-i-learned-2026-07-02-cherry.md](./today-i-learned-2026-07-02-cherry.md)
