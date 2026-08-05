# Air-dodge deferred threads — scoping (#218, child of #192)

> Scopes the two `GUESSED_VALUES_TO_RESEARCH.md` rows that the #192 sourcing pass
> (`pm-air-dodge-values-sourcing.md`, #216) deliberately left open and that **#215
> does not cover**. Consolidates the capture out of issue comments into a durable
> artifact, frames each thread for when it is *actually scheduled*, and records the
> recommended split. Date: 2026-06-29. Agent: DRAGONFRUIT. Area: `area:combat`.
> **No code/sim change** — pure scoping; nothing here pins a value or moves a constant.

## TL;DR

- **Thread A — intangibility window + `DODGE_TIME`** is **not a research gap**: the canon
  is already confirmed (intangible **frames 4–29 of a 49f** air dodge). The only open
  item is a **feel decision the owner reserves** — adopt the 4–29/49f model, or keep
  pycats' 14-frame full-window invuln. No datamine remains; this is a design call that,
  when scheduled, wants a `decision` sign-off **before** any code. A coupled in-dodge
  velocity-decay (`escapeair_decay ×0.95`) rides along with that same decision.
- **Thread B — per-character waveland traction** is a **genuine research/playtest** item
  with a **trap**: the one sourced number (Mario PM traction **0.06**) is in a *different
  friction model* than pycats' `GROUND_FRICTION = 0.5`, so adopting it faithfully is a
  **model change**, not a constant swap. It also belongs to the #117 archetype epic.
- **Recommended split (file when actually scheduled, not now):** A → a `decision`
  sub-ticket; B → a `research`/playtest sub-ticket folded into #117. Both stay low
  priority. This doc is the durable capture so neither is lost meanwhile.

---

## Thread A — intangibility window + `DODGE_TIME` (a FEEL DECISION)

### What is settled (not in question)

The PM/Melee air dodge is **49 frames** total, **intangible on frames 4–29** — confirmed
three ways in the #216 pass: rukaidata PM3.6 Mario `EscapeAir` (`IntangibleFlashing`@3 →
`Normal`@29), SmashWiki Air dodge, and FightCore. pycats instead runs a **14-frame
full-window** invuln (`config.DODGE_TIME = 14`, `invulnerable = True` for the whole
window) — a **conscious divergence** at pycats' own time scale, recorded in
`GUESSED_VALUES_TO_RESEARCH.md` (rows "Air-dodge intangibility window" and "DODGE_TIME").

### The open question (owner's call — I am NOT deciding it here)

**Adopt the canonical 4–29/49f model, or keep the 14f full-window?** This is a design /
feel decision, not a sourcing task. Scoping the *consequences* so the decision can be made
cleanly:

- **It is a coupled change, not a one-constant edit.** Moving to 49f means `DODGE_TIME`,
  the *sub-window* of intangibility (a new concept — pycats today has no "vulnerable tail"
  of the dodge), and the helpless/landing timing all move **together**. pycats' dodge is
  currently "intangible for its whole short life"; the canon dodge is "long, intangible
  only in the middle, vulnerable on entry and recovery."
- **It changes feel and almost certainly goldens.** A longer dodge with a vulnerable
  recovery tail is punishable in a way the 14f dodge is not; any golden battle that dodges
  will diverge → a *semantic* golden regen (per `tests/golden/REGEN_PROTOCOL.md`), gated on
  the decision being made first.
- **Coupled rider — in-dodge velocity decay (`escapeair_decay`).** The Melee decomp
  `ftCo_EscapeAir.c` multiplies air-dodge `self_vel` by **×0.95** (PlCo.dat 0xA170; ×0.9 in
  meleelight's rounding) **every frame** during the dodge. pycats does **not** model this
  (it holds the burst velocity, then zeroes it at dodge end). If the dodge is lengthened to
  ~49f, holding a constant burst for 49 frames feels very different from a decaying one — so
  the decay is part of the *same* decision, not a separate later thread. (Captured in
  GUESSED_VALUES' air-dodge-core table as a documented divergence.)

### Recommendation for Thread A

When scheduled, file a **`decision`** sub-ticket: "Air-dodge: adopt PM 4–29/49f
intangibility + `escapeair_decay`, or keep the 14f full-window?" with this doc's coupling
analysis attached, and **no code until it is signed off**. Default if undecided: **keep the
14f full-window** (the shipped, golden-stable status quo) — the divergence is deliberate and
costs nothing while unsourced numbers elsewhere are higher priority.

---

## Thread B — per-character waveland traction (RESEARCH / PLAYTEST, with a model trap)

### Current state

The wavedash/waveland slide (#202) is governed by a **single global**
`config.GROUND_FRICTION = 0.5` (a per-frame velocity *multiplier*: `vel.x *= 0.5`). PM canon
makes slide length **per-character traction** (Luigi longest, Peach shortest), but the wikis
describe it only **qualitatively** — no traction table is published.

### The trap (from the owner's #215-pass data point)

rukaidata PM3.6 Mario + SmashWiki Mario (PM) **do** give a number: **traction = 0.06**
(plus empty-landing-lag 4f). But it is **a different friction model**:

| | pycats `GROUND_FRICTION` | PM traction |
|---|---|---|
| Value | 0.5 | 0.06 |
| Meaning | per-frame velocity **multiplier** (`vel.x *= 0.5`) | per-frame **deceleration** (units/frame², *subtracted* from speed each frame) |
| Maps by ×`PX_PER_UNIT`? | — | **No.** 0.06 is a decel, not a speed; ×5.4 does not convert a multiplier to a subtractor. |

So **0.06 does not become 0.5 by any unit scaling.** Adopting per-character traction
*faithfully* means **switching pycats to a subtractive-deceleration friction model**
(`speed -= traction` clamped at 0), then giving each fighter its own traction — a physics
change that touches the waveland slide, normal ground deceleration, and likely goldens. The
cheaper alternative is to keep the multiplier model and just **playtest** a per-character
multiplier (no canon fidelity, but no model rewrite).

### Dependencies / ownership

Per-character anything is the **#117 archetype epic's** territory (per-fighter attributes
live in `FighterData`, see `combat/data.py` — `gravity`, `move_speed`, etc. are already
per-fighter; traction would join them). A faithful datamine of all-character traction is the
same engine-attribute path as #215 (per-fighter table), or empirical measurement.

### Recommendation for Thread B

When scheduled, file a **`research`/playtest** sub-ticket under **#117**: "Per-character
waveland traction — subtractive-decel model (faithful, 0.06-style) vs per-character
multiplier (cheap, playtested)?" Decide the **model** before sourcing a table; a table of
0.06-style values is useless under the current multiplier model. Low priority until more of
#117 lands.

---

## Why these were one ticket, and how they split

Both are deferred #192 follow-ups the maintainer asked to capture **together for later**.
They are otherwise unrelated — A is a settled-canon **feel decision** (no research left), B
is an **open research/playtest** with a model decision in front of it. They split cleanly:

| Thread | Filed as | Lands under | Blocking pre-req |
|---|---|---|---|
| A — intangibility/`DODGE_TIME` (+ `escapeair_decay`) | **#242** (`decision`) | #192 / combat | owner sign-off before code |
| B — per-character traction | **#243** (`research`) | #117 archetype epic | pick friction model first |

**Both children were filed when this ticket was scheduled** (#242, #243); this doc is their
shared analysis. They are deliberately low priority — #242 is a feel decision the owner
reserves (default: keep the 14f status quo), #243 is parked until more of #117 lands and its
friction-model question is answered.

## Sources / cross-refs

- Prior pass: `docs/research/pm-air-dodge-values-sourcing.md` (#216), `GUESSED_VALUES_TO_RESEARCH.md` (#192).
- SmashWiki [Air dodge](https://www.ssbwiki.com/Air_dodge), [Wavedash](https://www.ssbwiki.com/Wavedash); rukaidata [PM3.6 Mario `EscapeAir`](https://rukaidata.com/PM3.6/Mario/subactions/EscapeAir.html); [FightCore](https://www.fightcore.gg/).
- Melee decomp [`ftCo_EscapeAir.c`](https://github.com/doldecomp/melee/blob/master/src/melee/ft/chara/ftCommon/ftCo_EscapeAir.c) (`escapeair_decay`); meleelight [`ESCAPEAIR.js`](https://github.com/schmooblidon/meleelight/blob/master/src/characters/shared/moves/ESCAPEAIR.js).
- Issues: #192 (umbrella), #215 (magnitude sibling), #202 (wavedash shipped), #117 (archetype epic). Owner data-point comments on #218 (traction 0.06; `escapeair_decay ×0.95`) are folded in above.
