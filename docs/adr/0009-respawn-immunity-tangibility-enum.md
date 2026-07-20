# ADR-0009 — Respawn immunity is invincibility, modeled by a `Tangibility` enum

- **Status:** Accepted
- **Date:** 2026-07-20

## Context

Respawn immunity (#506, slice 1 of #482) is not yet implemented. Building it forced a
model choice, recorded as decision **#784**.

Two mechanics look alike but differ observably (canon basis: #774,
`docs/research/2026-07-20-intangibility-vs-invulnerability-canon.md`):

- **Intangibility** — the attack **passes through**. No contact: no damage, no knockback,
  no hitstun, and **no attacker hitlag** (the swing meets nothing).
- **Invincibility** — the attack **connects**. The attacker gets hitlag, but the
  defender's damage / knockback / hitstun are zeroed. Per SmashWiki *Revival platform*,
  the respawn descent grants **invincibility** (120 frames), not intangibility.

pycats today has only the first. Every live immunity mechanic (spot/roll/air dodge, ledge
burst, ledge-getup, getup-roll, techs — 9 in all) flows through **one** gate:
`systems/combat.py::check_hits` skips the defender when a derived immunity flag is set — a
pure skip-the-hit path that can express only intangibility. #506's own title mixes the two
words ("respawn **invincibility** — **intangible** window"), which is the ambiguity #784
was filed to resolve.

The fork (from #784): model respawn as **(A)** true invincibility — a new connect-for-zero
path, canon-faithful, but new sim code that moves goldens — or **(B)** reuse the existing
skip-the-hit intangibility gate — zero new machinery, but the word *invincibility* would
then name nothing in the codebase and the respawn window would diverge from canon (no
attacker hitlag). The game-designer ruled this a values call (canon-faithfulness vs
simplicity), so it was decided by a human, provisional on research #797 confirming the
premise that PM's engine actually separates the two states.

**#797 confirmed the premise** (`docs/research/2026-07-20-pm-invincible-hitlag-findings.md`,
closed 2026-07-20): triangulating the meleelight Melee-engine reimplementation, series-level
SmashWiki, and the Project-M-CC 3.6 codeset (no override present), the attacker takes hitlag
on an invincible defender; the invincible defender takes none; and invincibility and
intangibility are distinct engine states. The A-vs-B fork does not reopen.

## Decision

**We will model respawn immunity as canon-faithful invincibility (option A), represented by
a `Tangibility` enum — not a second parallel bool.**

- **`Tangibility` enum** with exactly three members: `TANGIBLE`, `INTANGIBLE`, `INVINCIBLE`.
  It replaces the derived per-frame `intangible` (formerly `invulnerable`) bool.
- **Derived each frame as the most-protective state** among the fighter's active immunity
  timers. The 9 existing intangibility mechanics are behaviorally unchanged — each simply
  declares it contributes `INTANGIBLE`; the respawn window contributes `INVINCIBLE`.
- **The combat gate becomes a 3-way switch** (`systems/combat.py::check_hits`):
  `INTANGIBLE` → skip the pairing (exactly as today); `TANGIBLE` → normal hit resolution;
  `INVINCIBLE` → a new register-but-zero branch: register the hit, apply the **attacker's**
  hitlag, and zero the **defender's** damage, knockback, hitstun, **and** hitlag.
- **Precedence: `INTANGIBLE` outranks `INVINCIBLE`.** This is not an arbitrary tie-break: an
  attack that passes through (intangible) makes no contact, so there is nothing for
  invincibility — which acts only *on* contact — to modify. Intangibility subsumes
  invincibility. When a respawn window (invincible) and a dodge (intangible) overlap,
  pass-through wins and the attacker gets no hitlag. Whether PM literally sets both flags at
  once is `[inference]`; the observable result is the same either way (#797 Q4).
- **ARMOR is deferred.** It is a knockback-resistance axis ("not in code" per #774); it is
  **not** a fourth enum member here and is out of scope until separately decided.

## Consequences

**Easier / enabled:**
- The respawn descent window can be built faithfully to canon: the attacker freezes for
  hitlag while the respawning fighter takes nothing.
- `invincibility` becomes a truthful, live word in the codebase — the vocabulary #775
  reserved is realized rather than left describing nothing.
- One derived tangibility value covers all immunity mechanics under a single most-protective
  rule, instead of a growing set of parallel bools.

**Harder / follow-on work:**
- The bool→enum retype is **golden-moving**; that golden churn is expected and **owned by
  the enum DEV ticket (#802)**, which introduces `pycats/combat/tangibility.py` + the
  `INVINCIBLE` branch and re-points #506's respawn window at it.
- The rename #776 (`invulnerable` → `intangible`) stays a **pure, golden-neutral** bool→bool
  rename and lands first; #802 is blocked on it.
- #506 (respawn immunity) gains two upstream deps — #797 (now closed) and #802 — on top of
  its existing #513 tint/timer block, and sets `INVINCIBLE` via #802's machinery rather than
  a bare skip-the-hit flag.
- More test surface: #802 ships an able-to-fail regression asserting the `INVINCIBLE` branch
  (attacker `hitlag_timer > 0`; defender percent/knockback/hitstun unchanged; defender
  `hitlag_timer == 0`) and the `INTANGIBLE` tie-break.

**Ruled out:**
- Option B (reuse the skip-the-hit gate for respawn) — rejected for canon-faithfulness.
- A second parallel `invincible` bool alongside `intangible` — rejected in favor of the
  single derived enum.
- A fourth `ARMOR` enum member — deferred, not added.

**Refs:** decision #784; canon #774; plan #775 (superseded on the model shape — addendum on
#775); premise research #797 (findings doc); enum DEV #802 (implements); rename #776; respawn
DEV #506; tint/timer #513; epic #772. Glossary: `docs/glossary.md`
(*intangibility* / *invincibility* / *tangibility*).
