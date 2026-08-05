# Ledge-regrab count reset — canon findings (PM / Brawl / Melee)

> **RESEARCH** · area:combat · combat:ledge · follow-up to
> [#906](https://github.com/avidrucker/pycats/issues/906) · filed as
> [#994](https://github.com/avidrucker/pycats/issues/994).
>
> **Question:** when does the consecutive-ledge-grab (anti-plank) count reset across
> the PM lineage, and — specifically — does **climbing back up from the ledge (ledge
> getup)** reset it? This doc sources canon so the display/timing of pycats'
> grabs-left dots ([#657](https://github.com/avidrucker/pycats/issues/657)) can be
> made PM-faithful. **No code change here**; a DEV fix follows downstream.

## TL;DR

The canon reset event is **"becoming grounded / landing on the stage"** (plus getting
hit, dying, and a handful of other state changes) — **not the ledge-climb action
itself**. A ledge getup is simply one *path to* becoming grounded; canon resets the
count when the fighter is grounded, and the getup animation flips "grounded" partway
through its climb (`[inference]` from the Melee reimplementation). Melee proper has **no
consecutive-grab count** at all — the count is a PM/Balanced-Brawl addition — so the
"when does the count reset" question has no Melee-primary answer; it is answered by the
PM primary (PMDT) and its Balanced Brawl ancestor.

---

## Q1 — Reset trigger (canon)

**In PM 3.6, the count resets when the fighter lands on the stage or is hit** (plus the
broader Balanced-Brawl state-change list its counter is inherited from).

- **PM primary — PMDT 3.5, "Ledge Invincibility"** (already quoted in-repo at
  `docs/pm-reference/ledge-regrab-intangible-and-display.md`):
  > "After a character regrabs the ledge five times without touching the ground, that
  > character no longer receives intangibility for grabbing the ledge again (except for
  > a few frames during the initial ledge snap) **until he or she either lands on the
  > stage or gets hit**."

  → the reset events named by PM primary are **land on the stage** and **get hit**.

- **Balanced Brawl (BBrawl) — direct ancestor of PM's ledge-grab-limit counter**
  ([balancedbrawl.net/global-changes/ledgegrab-limit](https://balancedbrawl.net/global-changes/ledgegrab-limit/)),
  verbatim:
  > "Every time a character grabs a ledge, a counter is incremented." (tether grabs
  > excluded)
  >
  > "This counter is reset to zero under the following circumstances: **Death**,
  > **Transformation** into another character (Zelda & Sheik, etc.), **Entering
  > hitstun**, including Zero Suit Samus's stun and being hit by a Deku Nut, **Being
  > grabbed**, including by special grabs, **Tripping**, **Being frozen**, **Being
  > grounded** (Donkey Kong side special, etc.), **Being put to sleep**."

  Note: BBrawl's cutoff *behaviour* differs from PM's — at count ≥ 5 BBrawl forces an
  automatic ledge climb, whereas PM 3.5/3.6 instead withholds intangibility (PMDT
  above). But the **counter machinery** (increment per grab, this reset list) is the
  system PM inherited, so the reset conditions transfer. `[inference: BBrawl→PM for the
  full reset list beyond "land / get hit"; PM primary confirms the two main events]`

**Neither source lists "performing a ledge climb / getup" as its own reset trigger.**
The listed trigger is **being grounded**; getup only matters insofar as it *results in*
being grounded.

## Q2 — Engine model (meleelight, Melee) `[inference: Melee→PM]`

**Melee has no consecutive-grab count with a cutoff** — so meleelight (the Melee
engine reimplementation, [#616](https://github.com/avidrucker/pycats/issues/616)) has
no "count reset" to expose. It models a different, older mechanic:

- `player.phys.ledgeRegrabCount` is a **boolean** (in-DRP or not), paired with a
  frame timer `ledgeRegrabTimeout` — a per-drop **Disabled Regrab Period**, not a
  running tally. The engine loop (`src/physics/physics.js`, the
  `if (player[i].phys.ledgeRegrabCount)` block) decrements the timer and clears the
  boolean when it hits zero; a fresh ledge grab is gated on `!ledgeRegrabCount` and
  re-arms the 30-frame timer. This is Melee's ledgestall spacing rule (SmashWiki's
  "Disabled Regrab Period", ~29–30 f), **not** an anti-plank count.

**Consequence:** the PM 5-grab count cutoff is a **PM/BBrawl-specific mechanic**; there
is no Melee-primary answer to "when does the count reset" because Melee has no such
count. This is a **`[GAP]` for a Melee-primary reset event** — expected, and resolved by
the PM/BBrawl sources in Q1.

## Q3 — Getup as "landing": the exact moment

**The reset is tied to *becoming grounded*, and the getup animation flips "grounded"
mid-climb — not at climb-start, and not a frame after climb-end.**

- In meleelight's getup states, the grounded flag is set **during** the animation, not
  at its terminal frame: `characters/marth/moves/CLIFFGETUPQUICK.js` sets
  `player[p].phys.grounded = true` at `timer === 16` (the action's `interrupt` to WAIT
  only fires later, at `timer > 32`); `CLIFFGETUPSLOW.js` sets `grounded = true` at
  `timer === 45` (interrupt at `timer > 58`). So the "lands on the stage" instant is the
  frame the body reaches the lip, partway through the climb. `[inference: Melee→PM]`

- **Mapping to pycats' #906 finding:** during pycats' ~16-frame `ledge_getup` window
  the fighter is *not yet grounded* (normal physics is skipped while `grabbed_ledge` is
  set), so the count legitimately has **not** reset — a non-zero count there is
  **canon-defensible**, not a stale flag. pycats already resets on
  `Fighter._handle_landing` (the air→ground edge), i.e. **at grounding** — so its reset
  *timing* is essentially canon-correct. #906's symptom is purely that the grabs-left
  dots *render* over the climb window, when the body is visually on the platform but the
  grounding-reset has not yet fired.

## Q4 — Option space for pycats' reset point

The two fix directions from #906, restated against the canon above. (Reported neutrally;
a recommendation with rationale follows at the bottom of this doc — the pick is the
owner's, in the downstream DEV ticket.)

| Option | What it changes | Canon alignment |
| --- | --- | --- |
| **A — Display-only gate** (fix-Direction 1) | Suppress `grabs_left_dots` while `ledge_getup` is active; leave `ledge_regrab_count` untouched. | Count value stays as-is (canon-defensible during the not-yet-grounded climb). Only hides the cosmetic oddity. No gameplay change. |
| **B — Reset at getup grounding frame** (fix-Direction 2, refined) | Reset `ledge_regrab_count` (and thus drop the dots) at the moment the getup grounds the fighter — when the body reaches the lip — instead of one frame later. | Matches canon's "being grounded / lands on the stage" reset *precisely*; clears the dots at the same instant. Changes a gameplay-facing count by ~a handful of frames. |
| **C — Reset at getup commit (start)** | Reset `ledge_regrab_count` the frame the up-input is accepted. | **Contradicts canon** — resets before the fighter is grounded (still mid-climb). Listed only to mark it out of bounds. |

Current pycats behaviour sits between A and B: the reset fires ~1 frame after the getup
completes (when post-getup physics detects ground), and the dots render throughout the
climb.

## Sourcing tiers

| Claim | Tier | Source |
| --- | --- | --- |
| PM resets the count on **land-on-stage** / **get-hit** | **PM primary** | PMDT 3.5 "Ledge Invincibility" (in-repo quote) |
| Full reset list (death / transform / hitstun / grabbed / trip / frozen / **grounded** / sleep); increment per grab | BBrawl primary; **`[inference]`** BBrawl→PM for items beyond land/hit | balancedbrawl.net ledgegrab-limit |
| Melee has **no** anti-plank count (per-drop DRP instead) | Melee-reimplementation (meleelight) | `src/physics/physics.js`, `characters/*/moves/CLIFF*.js` |
| Grounded flips **mid-getup** (frame 16 quick / 45 slow) | **`[inference: Melee→PM]`** | meleelight `CLIFFGETUPQUICK.js` / `CLIFFGETUPSLOW.js` |
| PM-primary for the **exact frame** grounding occurs within a PM getup | **`[GAP]`** | not found in PMDT / rukaidata (per-move scripts don't expose the count-reset hook) |

## Recommendation (author's, non-binding)

**Option B — reset `ledge_regrab_count` at the getup's grounding frame.**

Rationale: canon's reset event is *being grounded / landing on the stage* (PM primary,
Q1), and a ledge getup's grounding frame **is** that instant (Q3, `[inference]` from
meleelight). Option B therefore aligns the reset to the exact canon event and, as a free
consequence, drops the grabs-left dots at the right moment — fixing #906's symptom
through the model rather than around it. Option A (display-only) is a valid lighter
touch — the count during the climb is already canon-defensible, so hiding the dots is not
*wrong* — but it leaves the reset a frame late and treats a modelling question as a
rendering one. Option C is ruled out: it resets before grounding, against canon.

Caveat on tier: the reset **event** (grounded/land) is PM-primary; the claim that the
getup's grounding frame is the right *sub-frame* to hook is an `[inference]` from the
Melee reimplementation, with a `[GAP]` on a PM-primary exact-frame source. If the DEV
ticket wants only PM-primary-grounded changes, Option A is the conservative floor and
Option B the faithful-but-inference target.

## Refs

Follow-up to [#906](https://github.com/avidrucker/pycats/issues/906) (repro + spec).
Anti-plank counter [#656](https://github.com/avidrucker/pycats/issues/656); 5-regrab
cutoff ratified [#670](https://github.com/avidrucker/pycats/issues/670); CliffCatch
intangibility [#683](https://github.com/avidrucker/pycats/issues/683); hang-timeout
removal [#475](https://github.com/avidrucker/pycats/issues/475); grabs-left dots
[#657](https://github.com/avidrucker/pycats/issues/657) /
[#658](https://github.com/avidrucker/pycats/issues/658); meleelight engine source
[#616](https://github.com/avidrucker/pycats/issues/616); ledge state
[#14](https://github.com/avidrucker/pycats/issues/14); ledge epic
[#751](https://github.com/avidrucker/pycats/issues/751).

Companion in-repo: `docs/pm-reference/ledge-regrab-intangible-and-display.md`,
`docs/pm-reference/ledge-mechanics.md`.

External: [BBrawl — Ledgegrab Limit](https://balancedbrawl.net/global-changes/ledgegrab-limit/) ·
[SmashWiki — Planking](https://www.ssbwiki.com/Planking) ·
[SmashWiki — Ledgestall](https://www.ssbwiki.com/Ledgestall).
