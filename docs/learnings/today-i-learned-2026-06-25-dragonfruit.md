# TIL 2026-06-25 — DRAGONFRUIT

**Context:** A long session: closed the #47 watchable-2-NPC epic (slices A–E), a
dodge-test rewrite (#62) with two design-decision spin-offs, a jump-over-flush
repro spike (#22→#68), and a run of architecture-review cleanups (D3 #70, D4 #72,
#64 jab reach, S4 #74 golden de-risk). The throughline that kept recurring:
**the assigned task's premise was usually slightly wrong, and verifying first —
before removing, before "fixing" — is what caught it every time.**

---

## 1. Verify-before-removing keeps invalidating the premise — so verify first, always

**What happened:** three tasks in a row were handed to me with a confident premise
that the first ten minutes of checking falsified:

- **D3 (#70)** — "remove the dead `Attack(hitbox=None)` fallback and retire
  `ATTACK_SIZE/ATTACK_LIFETIME/HIT_DAMAGE` once confirmed unused." The fallback
  wasn't dead (two tests used it), and `ATTACK_SIZE` wasn't unused — it sizes the
  rendered hit-box rect for *every* attack and its top-left feeds the golden
  snapshots. The instruction's own gate ("once confirmed unused") was the escape
  hatch: I kept it.
- **#64** — assigned as "edit the moveset data + regen goldens." The reach value
  was *not* the (whole) bug; it was entangled with a `resolve_circle` facing
  defect (see §2).
- **D4 (#72)** — `game.check_win_condition` looked unit-testable; `game.py` turns
  out to be a *script* (`pygame.init()` + `while running:` at module level), so it
  hangs on import. That changed the fix shape (extract a pure module, test that).

**What I learned:** the value of the assignment is the *direction*, not the
*diagnosis*. Every premise deserves a cheap falsification pass before you act on
it. And a corollary footgun: my first `grep "Attack("` filtered with
`grep -v "...attacks\b"` and silently hid a third caller (`bench_render.py`) — a
filter meant to drop noise dropped a real hit. The full, unfiltered grep is the
one that counts before a removal.

**The rule:** treat a task premise as a hypothesis. Confirm "dead"/"unused"/"the
bug is X" with evidence *before* removing or fixing — and never let a convenience
grep filter narrow the "is it really unused?" check.

---

## 2. When the obvious fix overshoots, suspect a *second* bug compensating for the first

**What happened:** #64's symptom was "the jab can't hit an adjacent opponent."
The obvious fix — extend the jab's reach — *overshot and missed* in my probe.
That contradiction was the tell. Two defects were propping each other up:

1. `resolve_circle` mirrored the facing offset around the rect's **left edge**
   (`origin_x - dx`), so a **left-facing** fighter's hurtbox landed *off-body,
   toward the attacker*; and
2. the jab was too short to reach a *correctly* placed body-centre hurtbox.

In normal combat the defender faces the attacker (left), so bug #1 jutted the
hurtbox forward and **masked** bug #2 — combat "worked" by accident. A *fleeing*
target faces away → correct hurtbox → whiff (the #60 symptom). Fixing reach alone
overshoots the mis-placed near hurtbox; fixing the mirror alone makes the short
jab miss everyone. They only resolve **together** (mirror around the body centre +
extend reach).

**What I learned:** "the straightforward fix makes it *worse*" is not a tuning
problem, it's a signal that a second bug is compensating for the one you're
chasing. Two wrongs were making a right in the common case.

**The rule:** when extending/strengthening the obvious knob degrades behaviour,
stop tuning and look for a compensating defect elsewhere in the pipeline.

---

## 3. A revert-check that won't go red is telling you the *test* is wrong

**What happened:** rewriting the dodge scripts as real tests (#62), I revert-checked
every one by mutating the production code. Several mutations *didn't* fail the
tests — and each time the test (or my mutation target) was the problem, not the
code:

- A `vel.y`-based "spot dodge suppresses gravity" assertion passed even with
  gravity *on*, because the spot dodge keeps the player grounded and re-landing
  re-zeroes `vel.y` each frame. A **Liar**. I replaced it with a per-frame
  "stays planted on the thin platform" assertion.
- Mutating `DODGE_SPEED` didn't fail the air-dodge velocity tests, because they
  assert against the *same* `DODGE_SPEED` constant the code uses (a tautology) —
  the *logic* must be mutated, not the constant.
- The fall-through guard is **triple-defended** (gravity-suppression + drop-guard
  + ground-hold); no single-guard mutation changes observable behaviour. The test
  is honest, but the revert-check needs to remove *all three*.

**What I learned:** the revert-check isn't a formality you pass; it's a probe that
*finds* weak tests and reveals how the production code is actually layered. A
green mutation is a result, not a failure to ignore.

**The rule:** if you can't make a test go red by breaking the behaviour it claims
to guard, the test is a Liar (or asserts a tautology, or you're mutating the wrong
line) — fix that before trusting it.

---

## 4. Re-measure an audit's numbers before scoping the fix to them

**What happened:** S4 (#74) was scoped around "the 1.18 MB opaque `full_match.json`
rubber-stamp risk." By the time I picked it up it was **139 KB / 700 frames** —
my own #64 fix made the bot 3-stock at frame 700 instead of running 6000. The
size problem had largely solved itself; the residual risk was *reviewability* (a
139 KB diff is still unreadable), so the fix became a small semantic **summary
sidecar** per golden + a written regen-review protocol, not a size-reduction.

**What I learned:** an audit finding is a snapshot in time; intervening work moves
the numbers. Re-measure before you build to the stale figure, or you'll solve a
problem that no longer has the shape it was filed with.

**The rule:** confirm the current magnitude of a flagged problem before scoping —
the right fix follows the *present* measurement, not the audit's.

---

## Throughline

All four are the same instinct from a different angle: **the cheapest, most
reliable move is to reproduce/measure the ground truth first** — before removing,
before tuning, before trusting a test, before sizing a fix. Every place I did that
this session, the assigned framing turned out to be a useful approximation rather
than the literal truth, and surfacing the gap (then proceeding) beat barrelling
ahead on the premise.
