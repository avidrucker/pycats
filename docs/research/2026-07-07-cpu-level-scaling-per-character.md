# CPU level scaling 1–9, per character — mechanic gating, near-miss, accidental-press (#702)

**Role:** RESEARCH (spike) · `area:combat` · 2026-07-07 · DRAGONFRUIT
Related: #231 (difficulty epic), #691 (in-game picker), #684 (balance sim), extends #148 / #251 / #48 / #285 / #343.

> **What this doc is.** A recommended parameter model for making **every CPU level 1–9 play
> measurably differently, per character**, covering four axes the current ladder does not: a full
> 1–9 curve, per-character exclusive-mechanic gating, a **near-miss** model, and an
> **accidental-press / human-error** model. It is investigation + a recommended design — **no code
> changes**. Follow-up DEV tickets are *listed* at the end, not filed (RULES: research epics file
> children one at a time, downstream of the doc).

> **Provenance discipline (grounded-claim rule).** Each knob below is tagged **[SOURCED]** (traceable
> to a Smash/PM primary or an existing repo findings doc, cited by path + heading) or
> **[PYCATS-ORIGINAL]** (a pycats design choice with no Smash source — needs a game-designer
> `decision:` before a DEV ticket ships it, per the "changing values needs a basis" rule). No knob is
> presented as sourced-when-guessed.

---

## TL;DR

1. **Full 1–9 curve — recommend interpolation, not anchor-snapping.** Today `level_params()`
   (`pycats/sim/controllers.py :: level_params`) snaps each level to the nearest of 5 anchors, tie
   resolving **up**, so **Lv2≡Lv3, Lv4≡Lv5, Lv6≡Lv7, Lv8≡Lv9** — only 5 distinct behaviors, not 9.
   Fix: **linearly interpolate the continuous knobs** (`reaction_delay`, `attack_period`, `standoff`,
   `follow_through_p`, `shield_chance`) between the sourced anchors, and keep the **discrete
   capability flags** as explicit per-level thresholds. This is exactly the option #148 §Q5 floated
   ("intermediate levels interpolate or reuse the nearest filled row") — the *axes* stay sourced, only
   the fill method changes. **[SOURCED]** (method), values already in `LEVEL_PARAMS`.

2. **Per-character mechanic gating — a per-character × per-level usage matrix.** The 3 implemented
   fighters each have one identity mechanic (Nalio = fireball zoning; Birky = 6-jump floaty recovery;
   Narz = tipper spacing). The CPU should *unlock* each at a per-character level and scale *how
   accurately* it uses it. Most of this is **[PYCATS-ORIGINAL]** (Smash sources give only the shared
   0–100 scalar, not per-character CPU tuning) → **decision-gated**.

3. **Near-miss** (a deliberately mis-spaced/mistimed attack, prevalent low-mid, tapering high) and
   **accidental-press** (a spurious/dropped input, prevalent low, ~0 at Lv9) are **[PYCATS-ORIGINAL]
   human-error simulations**. Smash CPU AI does *not* model either — low-level Smash CPUs look weak via
   *low follow-through + slow reaction*, not via injected error. Both are implementable golden-safe on
   the existing seeded-RNG seam (#166), but both need a **game-designer `decision:`** before build
   (they are new game-feel systems, not parity fixes).

**Bottom line:** axis 1 (interpolation) is sourced and can proceed to a DEV ticket now; axes 2–4 are
mostly original design and should route through a short `decision:` before any DEV work.

---

## Axis 1 — the full 1–9 scaling curve

### Current behavior (measured from source)

`LEVEL_PARAMS` (`pycats/sim/controllers.py :: LEVEL_PARAMS`) fills 5 anchor rows:

| Knob | Lv1 | Lv3 | Lv5 | Lv7 | Lv9 |
|---|---|---|---|---|---|
| `reaction_delay` (f) | 30 | 20 | 12 | 6 | 1 |
| `attack_period` (f) | 48 | 36 | 24 | 16 | 10 |
| `standoff` (px) | 45 | 40 | 35 | 32 | 30 |
| `follow_through_p` | 0.15 | 0.35 | 0.55 | 0.80 | 1.00 |
| `shield_chance` | 0.00 | 0.05 | 0.15 | 0.40 | 0.85 |
| `enabled_moves` | jab | +tilts | +aerials | (=5) | +specials |
| reactive_shield / whiff_punish | — | — | ✓ | ✓ | ✓ |
| reach_aware / reactive_spacing / recover / edge_guard | — | — | ✓ | ✓ | ✓ |
| evade_chance | 0 | 0 | 0 | 0.15 | 0.30 |
| edge_hog | — | — | — | ✓ | ✓ |

`level_params(level)` docstring: *"Intermediate levels reuse the nearest filled anchor; a tie … resolves
to the HIGHER anchor."* **Consequence (the gap this spike targets):** the four even levels are not
distinct — each collapses **up** to the next odd anchor. A player toggling Lv2→Lv3→Lv4 sees change only
every other step.

### Recommendation

- **Continuous knobs → piecewise-linear interpolation** between the 5 sourced anchors, rounding frame
  counts to `int`. e.g. `reaction_delay`: Lv2 = round(30 + (20−30)·½) = **25**; Lv4 = round(20 + (12−20)·½)
  = **16**; Lv6 = **9**; Lv8 = round(6 + (1−6)·½) = **4** (≈3–4). Same for `attack_period`, `standoff`,
  `follow_through_p`, `shield_chance`. **[SOURCED]** — #148 §Q5 sanctions interpolation; only the anchors
  are sourced, so an interpolated intermediate carries the same (low, playtest-TBD) confidence as its
  neighbors, no worse.
- **Discrete capability flags → explicit per-level thresholds** (interpolation is meaningless for a
  bool). Proposed thresholds, filling the even gaps (all **[SOURCED]**-shaped from #148 §Q1–Q3, exact
  cut **[PYCATS-ORIGINAL]** tuning):
  - `reactive_shield` / `whiff_punish` / `reach_aware` / `reactive_spacing`: on at **Lv5+** (unchanged).
  - `recover` / `edge_guard`: on at **Lv5+** (unchanged; #148 notes the recovery-variety threshold is
    the one *explicitly-sourced* discrete flip, at ~Lv6 — so a **Lv6** cut for a *recovery-variety*
    sub-flag is the most defensible single threshold in the whole ladder, see #148 §Q1–Q3 "Recovery").
  - `edge_hog`: on at **Lv7+** (unchanged).
  - `enabled_moves`: keep the ramp jab → +tilts (Lv3) → +aerials (Lv5) → +specials (Lv9); **even levels
    inherit the lower odd tier's kit** (a capability unlock should feel like a distinct rung, not a
    half-step). **[SOURCED]** ramp shape, thresholds inferred.
- **`evade_chance`**: interpolate 0 (≤Lv5) → 0.15 (Lv7) → 0.30 (Lv9), i.e. Lv6≈0.075, Lv8≈0.225.
  **[PYCATS-ORIGINAL]** (already flagged `⚠ tuning` in source).

**Golden-safety:** interpolation changes only *non-anchor* levels; Lv1/3/5/7/9 outputs are unchanged, so
all existing level-anchored goldens/tests stay byte-identical. `level=None` remains the legacy default.

---

## Axis 2 — per-character exclusive-mechanic gating

### The implemented roster's identity mechanics (measured from source)

| Character | File | Identity mechanic | How it's expressed today |
|---|---|---|---|
| **Nalio** (Mario all-rounder) | `pycats/characters/nalio_cat.py` | **Fireball zoning** — a ranged neutral-B projectile | The bot's *only wired* special: `AttackerController` fires B when `"specials" in enabled_moves and attack_range < adx <= fireball_range` (`controllers.py`, `fireball_range=450`). Gated to **Lv9 only** today. |
| **Birky** (Kirby featherweight) | `pycats/characters/birky_cat.py` | **6-jump floaty recovery** (`max_jumps 6`, low gravity/fall) | Pure movement scalars; the `recover` flag (Lv5+) makes *any* bot aim for the ledge, but nothing tunes Birky's *multi-jump* usage specifically. |
| **Narz** (Marth swordfighter) | `pycats/characters/narz_cat.py` | **Tipper + disjoint** — the far tip box hits harder than the base (tuple-order priority) | Pure move geometry; `reach_aware` (Lv5+) derives melee range from the committed move, but nothing makes the bot *deliberately space to land the tip*. |

**Key finding:** two of the three identities (Birky multi-jump, Narz tipper) are **latent** — they exist
as data but the CPU has no per-character policy that uses them *better as level rises*. Only Nalio's
fireball has a CPU hook, and it is a single on/off at Lv9.

### Recommended per-character × per-level usage matrix

Notation: **—** = mechanic not used; **rare/some/often/max** = usage frequency; **loose→tight** = spacing/
timing accuracy. All cells **[PYCATS-ORIGINAL]** unless marked — Smash sources do not tune CPU behavior
per character, so this whole matrix is **decision-gated design**, not parity data.

| Level | Nalio — fireball zoning | Birky — multi-jump recovery | Narz — tipper spacing |
|---|---|---|---|
| 1–2 | — (never zones) | burns jumps early, often SDs | hits with base box by accident; no spacing |
| 3–4 | — | uses ~2 jumps, poor angle | occasional tip, mostly base |
| 5–6 | rare, loose spacing | conserves jumps (`recover` on), predictable angle | *aims* for tip (`reach_aware`), ~50% |
| 7–8 | often, mid spacing | mixes jump count, harder to edge-guard | tips often, tight spacing |
| 9 | max, tight zoning (holds `fireball_range` band) | optimal jump conservation + angle | near-always tips (max spacing reward) |

**Two knobs generalize this** (so it is not 3 bespoke policies):
1. **`special_usage_level`** (per character): the level at which the character's signature move
   (fireball / other future specials) *unlocks*, plus a **frequency scalar** that ramps with level.
   Generalizes Nalio's Lv9-only fireball into a graded ramp and gives future specials the same seam.
2. **`spacing_accuracy`** (already latent in `reach_aware` / `reactive_spacing`): a per-level [0,1] that
   governs how close the bot tries to land the *rewarded* part of a move — the **tip** for Narz, the
   fireball *band* for Nalio, the ledge *angle* for Birky. One accuracy knob, three payoffs. Ties
   directly into Axis 3 (a low `spacing_accuracy` *is* a near-miss).

**Provenance:** the *existence* of per-character kits is sourced (the character files + #285 reach
finding); the *CPU tuning of them per level* is **[PYCATS-ORIGINAL]**. #343 (`docs/research/2026-06-30-
npc-spacing-footsies-models.md`) constrains this: Smash CPUs *approach committally and attack by
proximity* — so **do not** model tipper spacing as footsies/baiting; model it as *proximity-band
accuracy* (aim the commit at the tip's range band), consistent with the existing approach model.

---

## Axis 3 — near-miss model

**Definition (proposed).** A *near-miss* is an attack the CPU commits that is **deliberately mis-spaced
or mistimed so it visibly almost connects** — the fighter swings, the hitbox falls just short or just
late, the opponent is nicked or clean-misses. It is the *visual tell* of a weaker opponent.

**Provenance — candid:** Smash CPU AI does **not** inject near-misses. Low-level Smash CPUs look weak via
**low `follow_through_p` + long `reaction_delay`** (#148 §Q1: *"almost never commits,"* *"waits a long
time before eventually acting"*) — i.e. they *hesitate*, they don't *whiff on purpose*. So near-miss is
**[PYCATS-ORIGINAL]** game-feel. It is defensible (it reads as human error and is more legible than
hesitation), but it is a **new system → `decision:` gated.**

**Recommended model** (if the designer greenlights it):
- Reuse the **`spacing_accuracy`** knob from Axis 2. On a committed attack, offset the effective commit
  distance by a seeded error `±ε` drawn from a per-level band: **ε large at Lv2–4, shrinking to 0 by
  Lv9**, with the distribution **peaked in the low-mid band** (the ask: "more prevalent in lower-mid
  levels") rather than monotonic — e.g. near-miss *probability* rises Lv1→Lv3 then falls Lv3→Lv9, while
  *magnitude* falls monotonically. Concretely a per-level `near_miss_p` and `near_miss_px`:

  | Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
  |---|---|---|---|---|---|---|---|---|---|
  | `near_miss_p` | 0.20 | 0.30 | **0.35** | 0.30 | 0.22 | 0.15 | 0.08 | 0.03 | 0.00 |
  | `near_miss_px` | 22 | 20 | 17 | 14 | 11 | 8 | 5 | 2 | 0 |

  (All values **[PYCATS-ORIGINAL]** ⚠ tuning starting points — the *shape* — low peaked in the mid, zero
  at 9 — is the sourced-intent from the ask; the numbers are guesses to be playtested.)
- **Golden-safe** via #166: rolled against `self.rng` with the fixed default seed → byte-identical
  goldens; only live/`--seed` matches vary. Lv1 note: Lv1's near-miss can be *lower* than Lv3's because
  Lv1 barely commits at all (`follow_through_p=0.15`) — the peak sits at Lv3 where the bot commits often
  but spaces badly. That interaction (`follow_through_p` × `near_miss_p`) needs a playtest check so the
  two systems don't cancel.

---

## Axis 4 — accidental-press / human-error model

**Definition (proposed).** An *accidental press* is a **spurious, wrong, or dropped input** the CPU emits
to simulate human fumbling — a stray jump, a shield that comes a frame late, an attack button pressed
with no target. Frequent at low levels, **~0 at Lv9**.

**Provenance — candid:** like near-miss, **[PYCATS-ORIGINAL]**. No Smash source models input error;
Toomai's finding (#148 §Sources) is the opposite — *Lv9 CPUs are frame-perfect and do not read inputs*,
so the top of the ladder is *error-free by design*, which this model already respects (rate → 0 at Lv9).
**`decision:` gated.**

**Recommended model + guardrails** (the guardrails are the load-bearing part):
- A per-level **`misinput_p`** rolled against `self.rng`, high at Lv1, 0 at Lv9:

  | Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
  |---|---|---|---|---|---|---|---|---|---|
  | `misinput_p` (per decision) | 0.12 | 0.10 | 0.07 | 0.05 | 0.03 | 0.02 | 0.01 | 0.00 | 0.00 |

  Monotonic (unlike near-miss) — human error falls steadily with skill. **[PYCATS-ORIGINAL]** ⚠ tuning.
- **Guardrails (mandatory, or the feature reads as a bug, not a skill floor):**
  1. **Never an accidental self-KO.** A misinput must be suppressed whenever the bot is off-stage or
     near a blast line — precedent: the #424 edge-hog self-destruct was a *bug*; a system that *injects*
     self-KOs would re-introduce it deliberately. Gate misinput on `on_stage and not recovering`.
  2. **Bounded blast radius.** Restrict the misinput vocabulary to *harmless* fumbles (a stray jab into
     air, a late shield, a single wrong-direction step) — **never** a self-damaging or momentum-killing
     input that a human would instantly recognize as the CPU "breaking."
  3. **Determinism contract.** Rolled against `self.rng` only; default seed → goldens byte-identical.
     Any test that asserts a *specific* leveled input timeline must seed explicitly (cf. the #345 /
     env-at-import isolation lesson — seed per-test, never globally).
- **Interaction with `follow_through_p`:** at Lv1 the bot already barely commits; stacking a high
  `misinput_p` on top risks a bot that does *nothing coherent*. Recommend the designer treat
  `follow_through_p` (hesitation) and `misinput_p` (fumbling) as **one "sloppiness" budget** at low
  levels, not two independent maxed knobs — else Lv1 becomes unwatchable rather than beatable.

---

## Faithfulness summary (per the grounded-claim / values-need-a-basis rules)

| Axis / knob | Provenance | Gate before DEV |
|---|---|---|
| 1 · interpolate continuous knobs across 1–9 | **[SOURCED]** method (#148 §Q5) | none — proceed to DEV |
| 1 · discrete-flag per-level thresholds | **[SOURCED]** shape, cut **[PYCATS-ORIGINAL]** | none (cuts already in source as ⚠ tuning) |
| 2 · per-character mechanic unlock + frequency | **[PYCATS-ORIGINAL]** | **`decision:`** (per-character CPU tuning is unsourced) |
| 2 · `spacing_accuracy` (tip / fireball-band / ledge-angle) | **[PYCATS-ORIGINAL]**, constrained by #343 (proximity-band, not footsies) | **`decision:`** |
| 3 · near-miss (`near_miss_p` / `near_miss_px`) | **[PYCATS-ORIGINAL]** — Smash uses hesitation, not injected whiffs | **`decision:`** (new game-feel system) |
| 4 · accidental-press (`misinput_p` + guardrails) | **[PYCATS-ORIGINAL]** — Smash Lv9 is error-free by design | **`decision:`** (new system; guardrails non-optional) |

**Provenance ceiling (unchanged from #148):** no PM-specific CPU source exists; everything sourced here
is Brawl-derived secondary (SmashWiki + Toomai) or a repo findings doc. Confidence on *exact numbers* is
low-by-provenance across the board — these are playtest starting points, recorded as **FOUND/design**,
never as PM-pinned.

---

## Recommended follow-up tickets (listed, NOT filed — one at a time downstream)

Per RULES (research epics file children one at a time, downstream of the doc). Sequence by gate:

1. **DEV — interpolate the 1–9 curve** (`level_params` → piecewise-linear for continuous knobs; explicit
   even-level thresholds for flags). *No decision gate — sourced method.* Golden-safe; the able-to-fail
   test asserts Lv2≠Lv3 (and Lv4≠Lv5, Lv6≠Lv7, Lv8≠Lv9) on at least one continuous knob, where today they
   are equal. **File first.**
2. **DECISION — approve the human-error direction** (near-miss + accidental-press + per-character CPU
   tuning as pycats-original systems). A single `decision:` ticket citing this doc; blocks tickets 3–5.
   *Gate for everything below.*
3. **DEV — generalize special usage** (Nalio fireball Lv9-only → graded `special_usage_level` +
   frequency ramp; seam reusable by future specials). *After #2.*
4. **DEV — `spacing_accuracy` / tipper-band aiming** (Narz tip, Nalio fireball band, Birky ledge angle
   off one per-level accuracy knob). *After #2; depends on 3's seam.*
5. **DEV — near-miss model** (`near_miss_p`/`near_miss_px`, seeded, peaked-low). *After #2 & #4 (shares
   `spacing_accuracy`).*
6. **DEV — accidental-press model** (`misinput_p` + the mandatory off-stage / bounded-vocabulary
   guardrails). *After #2; independent of 3–5.*
7. *(optional)* **DEV — leveled-per-character balance rows in the #684 sim** so the matrix is
   benchmarkable (win-rate by level should be monotonic within a mirror; a non-monotone rung flags a
   mis-tuned knob).

Each feeds #231's controller and is consumable by #691's in-game picker.

## Sources

- `docs/research/2026-06-29-pm-cpu-difficulty-levels-1-9.md` (#148) — §TL;DR (Brawl 0–100 scalar; two
  continuous knobs + discrete unlocks), §Q1–Q3 (per-level behavior table; recovery-variety threshold
  ~Lv6 = the one explicitly-sourced discrete flip), §Q4 (stochastic→seeded via #166), §Q5 (interpolate-
  or-snap; anchors are pycats interpolations of sourced axes).
- `docs/research/2026-06-30-cpu-ai-decision-model.md` (#251) — reactive (high-level) vs random
  (low-level) shielding; the "known-weakness" flaws are level-independent.
- `docs/research/2026-06-25-npc-behaviors-and-dual-controller.md` (#48) — borrow taxonomy, not the
  stochastic Smash mechanism; the RNG-free controller protocol.
- `docs/research/2026-06-30-ai-controller-reach-awareness.md` (#285) — reach is real, asymmetric,
  per-move; basis for `spacing_accuracy` targeting the rewarded box.
- `docs/research/2026-06-30-npc-spacing-footsies-models.md` (#343) — Smash CPUs approach committally by
  proximity; model tipper as a proximity band, **not** footsies. Constrains Axis 2.
- Source of record for current knobs: `pycats/sim/controllers.py :: LevelParams` / `LEVEL_PARAMS` /
  `level_params` / `AttackerController` (fireball branch); characters `nalio_cat.py`, `birky_cat.py`,
  `narz_cat.py`. Seeded-RNG seam: #166. Self-KO guardrail precedent: #424.
