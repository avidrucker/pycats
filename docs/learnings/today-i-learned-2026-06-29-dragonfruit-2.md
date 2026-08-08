# TIL 2026-06-29 — DRAGONFRUIT (2nd session — value sourcing)

**Context:** Took the air-dodge tuning-values umbrella **#192** and chased the
`DODGE_AIR_SPEED` magnitude all the way to a sourced, pinned value — through the
sourcing writeup (**#216**), the value hunt (**#215** → pinned in **#222**), the
deferred-threads catch (**#218**), an open-source code catalog (**#224**), and a
data-organization spike (**#226**). The sequel to FIG's morning TIL, which had
said "guess loudly" about these same magnitudes (#192). *Jargon: a **decomp** is a
reverse-engineered C source of a game; a **reimpl** is a clean re-coding of its
physics in a high-level language; a **golden** is a byte-for-byte recorded sim
snapshot test; an **umbrella** is a tracker issue that coordinates many children.*

---

## 1. Engine-hardcoded constants aren't on rukaidata — go to the decomp + a reimpl

**What happened:** #192 assumed `DODGE_AIR_SPEED` was "derivable via rukaidata
units/frame × `PX_PER_UNIT`≈5.4." It isn't. rukaidata's PM3.6 Mario `EscapeAir`
*subaction* (0x46) lists the animation, intangibility flags (4–29/49), and SFX but
has **no Self-Velocity command**; the full 64-row *attributes* table has **no dodge
stat** either. The air-dodge velocity is applied by the engine's hardcoded handler,
not the per-fighter `.pac`. The breakthrough came from open-source code: the Melee
decomp [`doldecomp/melee`](https://github.com/doldecomp/melee) `ftCo_EscapeAir.c`
gave the **model** (`self_vel = escapeair_force × (cosθ,sinθ)`; neutral → `(0,0)`;
per-frame `× escapeair_decay`), and the [`meleelight`](https://github.com/schmooblidon/meleelight)
reimplementation gave the **literal** — `ESCAPEAIR.js`: `3.1 * Math.cos(ang)`.

**What I learned:** rukaidata (and `brawllib_rs`) expose *scripted* move data —
hitbox sizes/positions/BKB/KBG — which is why `nalio_cat.py` could author radii as
`round(units × 5.4)`. They do **not** expose engine globals. Those live in the
decomp (model) and a faithful reimpl (literal value), or in `PlCo.dat` via a data
sheet.

**The rule:** **For an engine-hardcoded constant, read the decompilation for the
model and a faithful reimplementation for the value; rukaidata is only for scripted
move/hitbox data.** (Homed in the #224 catalog's "where to look for X" guide.)

---

## 2. Corroborate before pinning — three lines beat a remembered number

**What happened:** I "knew" the Melee air-dodge speed was ≈3.1 from training. I
refused to pin it on that. Only after three independent lines agreed —
`meleelight`'s `3.1` literal, the decomp's `escapeair_force × (cosθ,sinθ)` model,
and a ~2.79 max-angle-wavedash back-solve (≈2.9–3.1) — did I pin
`DODGE_AIR_SPEED = round(3.1 × 5.4) = 17` (#222).

**What I learned:** a value you bake into the live sim is exactly where a confident
hallucination does damage. The "delegated finding is a lead, not a fact" rule from
my morning TIL (#196) applies just as hard to a number I recall as to one an agent
hands me.

**The rule:** **A constant you'll commit to the sim needs a primary source, not
recall — corroborate across independent sources before pinning.**

---

## 3. "Ready to take" ≠ "completable in this environment"

**What happened:** I ran `/issue-review` on #215 before taking it. The rubric
scored it **READY (13/15)**. But its stated method — a `brawllib_rs`/ISO datamine
or a PM playtest — **isn't runnable headless**. I surfaced that ceiling, did only
the cheap web step, and sharpened the ticket instead of fabricating a value. (The
ceiling then *moved*: the cheap step led to `meleelight`, which closed it anyway.)

**What I learned:** readiness is a property of the *ticket* (is it well-specified?);
executability is a property of the *agent × environment* (can *I* finish it *here*?).
The issue-review rubric scores the first and is silent on the second — so a clean
READY can still be uncompletable by a headless agent, and the honest move is to say
so, not to force a number.

**The rule:** **Before claiming, sanity-check executability against your actual
environment; a well-formed ticket can still be uncompletable here — surface the
ceiling, don't fabricate past it.** (Candidate dimension for the issue-review-skill;
see Open threads.)

---

## 4. An umbrella can't be "closed" to make progress — release it, land via children

**What happened:** #192 is an umbrella that must stay **open** while rows remain.
But `pmtools close` is the *only* way to land a commit on `main` (`release` just
drops the claim without pushing). To land the sourcing writeup, I **released** the
#192 claim, then landed the doc via a closeable child (#216) and filed the open
follow-up (#215). Later the same pattern: a DEV child (#222) carried the pin and
auto-closed #215 via `Closes #215`.

**What I learned:** claiming the umbrella is a trap — you hold it, can't close it,
and can't push. Claim a *child* per increment; release the umbrella so it's free
for the next round.

**The rule:** **For an umbrella research ticket, claim a child per increment (not
the umbrella) and `release` the umbrella; the umbrella closes only when its last row
resolves.**

---

## 5. Assert the model, not the literal — so a retune lands golden-clean

**What happened:** Changing `DODGE_AIR_SPEED` 14→17 touched **zero** tests and
**zero** goldens. `test_wavedash.py` / `test_air_dodge_helpless.py` assert the burst
magnitude *relative to* the constant (`vel.x == DODGE_AIR_SPEED`, magnitude ≈ the
angled decomposition), and the combat golden's air dodge is *neutral* → `(0,0)`,
which the change doesn't touch.

**What I learned:** the #202 tests I wrote earlier — phrased as "a directional dodge
sets vel to `DODGE_AIR_SPEED` in the stick direction" rather than "sets vel to 14" —
paid off: they pin the *model* and survive a tuning pass. A test hardcoding `14`
would have churned for no behavioural reason.

**The rule:** **Pin the relationship/model, not the literal value — tests asserting
`x == THE_CONSTANT` survive retuning; tests asserting `x == 14` are tuning debt.**

---

## 6. Type the work before doing it — architect-first

**What happened:** Asked to "organize all our data into modules or JSON with
provenance + a drift-guard," the obvious move was a refactor. But *where* the data
lives (typed Python registry vs JSON+loader vs hybrid) and *how* drift is guarded
are open **design** choices with real trade-offs (golden byte-stability, the
no-new-dependency rule). I filed a **research/architecture spike (#226)** that
decides the design — carrying a human `decision` point on module-vs-JSON — and
*spawns* the refactor, rather than a lone refactor.

**What I learned:** "organize the data" silently presumes the target structure is
decided. It wasn't. Bundling the design into the migration lets whoever writes code
first pick the architecture by accident — the architect-as-courier trap.

**The rule:** **When the target structure is itself in question, design-first
(a `research`/architecture spike) and spawn the refactor — don't bundle the design
into the migration.** (Homed in #226.)

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/config.py` | `DODGE_AIR_SPEED` 14→17 (PM-faithful `escapeair_force` 3.1 × 5.4), sourced comment (#222) |
| `GUESSED_VALUES_TO_RESEARCH.md` | 4 rows flipped GUESS→FOUND-primary + the in-dodge decay divergence row (#216/#222) |
| `docs/research/pm-air-dodge-values-sourcing.md` | New — the sourcing pass + the engine-hardcoded finding (#216) |
| `docs/research/open-source-smash-implementations.md` | New — 16-source code catalog, "where to look for X" (#224) |
| #226 | Filed — data-organization architecture spike |

## Open threads

- **Issue-review-skill could gain an "executability" dimension** (lesson 3) — a
  ticket can be READY yet uncompletable by a headless agent. No ticket filed (the
  skill is a personal tool, not the project repo); recorded here + on #215's thread.
- **The exact `escapeair_decay`** is 0.95 (PlCo.dat 0xA170) vs 0.9 (meleelight) —
  pycats doesn't model in-dodge decay at all (#218 feel decision).
- **`PX_PER_UNIT` is still a magic 5.4** in comments (#195, held — touches `nalio_cat.py`);
  the data-org spike (#226) folds it in.

## Related artifacts

- Morning TIL: [TIL 2026-06-29 DRAGONFRUIT](./today-i-learned-2026-06-29-dragonfruit.md) (verify delegated findings, #196)
- Sibling: [TIL 2026-06-29 FIG](./today-i-learned-2026-06-29-fig.md) ("guess loudly" about these same magnitudes, #192) — this session sourced the guess.
- `docs/research-120-smash-units-and-sources.md` (#120, the `PX_PER_UNIT` anchor)
- Issues #192 / #215 / #216 / #218 / #222 / #224 / #226
