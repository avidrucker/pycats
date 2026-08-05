# Research findings — how Project M resolves a same-time, same-damage attack trade

- **Ticket:** #141
- **Agent:** DRAGONFRUIT
- **Date:** 2026-06-26
- **Area:** combat
- **Question (as actually asked):** When two characters attack each other on the
  same frame with the **same damage**, how does Project M decide the outcome?
  Does it use **randomness**, or some other factor?

> Note on scope correction: #141 was originally filed/researched as "can two
> mirror-identical CPU AIs parry each other indefinitely". That answered a
> *nearby* question (stalemate loops), not the one asked. This doc is the
> corrected, on-target answer; the original mirror-loop finding is retained below
> as **secondary context** because it is still valid and useful.

---

## Answer (short)

Project M resolves a same-frame attack collision with a **deterministic priority
rule called "clank"** — **no randomness is involved.** The decision is made
purely from the two attacks' **damage**:

- **Damage within 9% of each other** (this includes *exactly equal*) → **both
  attacks cancel.** Neither hits; both fighters enter **rebound** (a brief
  bounce-back recovery). The cancel is the "clank" (a white flash in-game).
- **One attack more than 9% stronger** → the **stronger attack continues**
  normally; the **weaker attack ends** and that fighter rebounds.

So for the exact case asked — **same time, same damage** — the difference is 0%,
which is inside the 9% window, so **both attacks clank and cancel, dealing no
damage to either fighter.** The damage numbers decide it every time; there is no
coin-flip or RNG.

Extra rule worth knowing: **aerial attacks do not clank** — this priority system
applies to **ground** attacks (and ground-vs-projectile). Some moves also have
"transcendent priority" (they pass through without clanking), but that is a
per-move property, still deterministic.

### Source
- SmashWiki, *Priority* — the "priority range" is **9%** across the
  Melee → Brawl → Project M family; within range both rebound, outside it the
  stronger continues and the weaker rebounds; aerials do not clank.
  https://www.ssbwiki.com/Priority
- Supporting: *All About Priority In Smash Melee* (Dignitas);
  SmashWiki *Rebound*.

---

## What pycats already has (this was the miss)

pycats **already implements this exact rule** — it shipped in **#133**
("opposing-hitbox clank/priority (9% range) — #38 slice 4c"). The corrected
answer should have started here:

- `pycats/config.py` → `CLANK_PRIORITY_RANGE = 9` (with a comment citing
  SmashWiki *Priority*, "9% across the Melee/Brawl/PM family").
- `pycats/systems/combat.py` → `_resolve_clanks(attacks)`, run at the **top of
  `process_hits`** so a clanked hitbox neither connects nor survives the frame.
  - Pairwise over **active, non-air** hitboxes owned by **different** fighters
    that overlap (`geometry.circle_overlap`, multi-hitbox aware via
    `Attack.resolved`).
  - Representative strength = the attack's **max box damage**
    (`_clank_strength`).
  - `abs(da - db) <= CLANK_PRIORITY_RANGE` → **both** end (clank); otherwise the
    weaker is negated and the stronger survives.
- Tests: `tests/test_clank.py` — equal damage → both clank; diff ≤ 9 → both
  clank; diff > 9 → stronger survives / weaker negated; a defender caught in a
  both-clank overlap takes **no** damage; an aerial does **not** clank a ground
  attack.

**Deliberate simplifications still open in pycats (vs. real PM):**

- **No rebound *state* and no clank freeze-frames yet.** A clank in pycats simply
  **negates** the losing/both hitbox(es) for the frame; it does not yet put the
  fighter into a rebound animation/lockout or a hitlag freeze. Rebound state is a
  later (Phase-3-ish) fighter state; hitlag is the separate #138 slice.
- **Per-attack, not per-hitbox** clank resolution (representative = max box
  damage).
- Aerial/projectile special-priority interactions beyond "aerials don't clank"
  are not modelled (no aerials/projectiles authored yet, though `in_air` is
  threaded onto `Attack`/`MoveTick` so the rule is correct-by-construction once
  they exist).

---

## Secondary context — the original mirror-loop finding (still valid)

The first pass at #141 asked whether two **mirror-identical CPU AIs** could loop
forever (each defending the other's attack). Summary of that finding, kept for
reference:

- PM has **no Ultimate-style parry** (which stuns the attacker). The nearest
  mechanic is **powershield / perfect shield** (shield within ~4 frames; 2 for
  projectiles) — it reflects projectiles and cuts shieldstun but does **not**
  stun the attacker, so there is no parry→punish ratchet to loop on.
  (SmashWiki *Perfect shield*.)
- In a **perfect** mirror, the *mechanical* breakers are **symmetric** and do
  **not** break the tie by themselves: a held shield decays and breaks
  (~3.58s in Melee; SmashWiki *Shield*), but in a true mirror both shields break
  on the same frame, both dizzy together, both recover together. The same applies
  to clank itself — a symmetric trade just cancels symmetrically.
- What actually resolves a real-PM mirror is **symmetry-breaking** — CPU AI is
  flowcharted and not frame-perfect, plus RNG surfaces (DI, decision weighting)
  desync the two sides — **and** an **external resolver**, the **match timer**
  → time-out / sudden death, which always produces a winner.

**Implication for pycats:** our sim is **deterministic by design** (no RNG — that
is what makes replays/goldens reproducible). So a perfectly symmetric matchup has
no built-in resolver; **#61's 30s/KO cap on `--vs` is the correct analog of PM's
match timer.** The specific "parry loop" is not reachable today (no parry
mechanic, no *reactive* defensive controller — `IdlerController` only shields on a
fixed timer). A principled tie-resolver (canonical match timer → sudden death by
stocks-then-percent) is only needed **if/when** a reactive/defensive or
powershield-capable controller is added.

---

## Outcome

- **Same-time same-damage trade question: answered.** Deterministic clank/priority
  (9% range), no randomness; pycats already models it (#133). No engine change
  needed for the trade case.
- **Follow-up filed:** a dedicated research ticket on *whether and where Project M
  uses randomness at all* (DI, items, tie-breaks, move variance, CPU decisions),
  to produce its own findings doc.
