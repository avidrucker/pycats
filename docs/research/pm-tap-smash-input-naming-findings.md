# PM/Smash naming for the stick-flick ("single-tap") smash input — findings (#436)

**Role:** RESEARCH · lane `area:combat` · 2026-07-05 · **No production code.**
Names a *future* feature (a stick-flick smash input) with correct PM/Smash nomenclature
before the implementation ticket is filed. Relates to #327 (smash epic, done), #331
(current dedicated-button smash), #142 (moveset super-epic), #423 (charge refinement).

## TL;DR
- The canonical input term is **"tapping the control stick"** (+ attack button pressed
  together). There is **no single-word noun** for it in the sources; SmashWiki describes
  it verbally. The hardware shortcut that maps a stick to smashes is the **C-stick**
  ("smash stick"); the opposite setting (C-stick does tilts) is **"tilt stick" / "A-sticking."**
- **Input method** (stick-flick+A vs a dedicated button) and **charge state**
  (uncharged vs charged) are **two orthogonal axes.** The maintainer's "single-tap smash"
  is the **input-method** axis. pycats already covers the charge axis (uncharged via a
  quick button tap, #366; charging, #327) — this feature is *not* about charge.
- **Recommended pycats term: `tap-smash`** (a "tap-smash" *input*), contrasted with the
  existing **`smash button`** input. Reject the maintainer's "quick/simple/direct-smash"
  (they read as charge/speed, not input method, and have no PM provenance).
- Map to pycats: an **addition** alongside the dedicated smash button (PM offers *both*
  routes), not a replacement. Primary seam: `fighter_input.py:288`. **Goldens caveat:**
  the sim keymaps have `attack`+directions but no `smash` key — a tap-smash that infers a
  smash from *attack + a directional tap* would make sims able to smash and perturb the
  golden sims unless gated/opt-in.

---

## 1. Official term for the stick-flick smash input

**Source — SmashWiki, *Smash attack* (ssbwiki.com):**
> "It is performed by **'tapping' the control stick** and pressing the attack button at
> the same time."
> "It can also be done by **tapping the C-stick** in the multi-player modes of Super
> Smash Bros. Melee, or any mode in Super Smash Bros. Brawl onward."

So the input is described as **"tapping the control stick"** (a fast directional flick)
performed **simultaneously with the attack button**. There is **no canonical single noun**
("tap smash" is community shorthand, not a wiki term). The two hardware routes to a smash:
1. **Main control stick, tapped + A** — the input this ticket wants to add.
2. **C-stick** — a stick dedicated to smashes; "primarily used to perform smash attacks"
   in Melee/Brawl/SSB4/Ultimate.

**Source — SmashWiki, *C-Stick*:**
> The C-Stick "is primarily used to perform smash attacks."
> "Setting input to tilt attacks is often referred to as **A-sticking** (or as **tilt
> stick**, especially in Ultimate)."

**Terminology mapping to pycats.** pycats' dedicated `smash` key (`smash=K_b`/`K_QUOTE`,
#331) is functionally a **C-stick / "smash stick"** — a single input bound to "do a smash."
The feature the maintainer wants is the **main-stick tap route**: a smash triggered by a
directional tap/flick combined with attack, *without* a dedicated smash key.

**Keyboard note (important).** pycats is keyboard-only — there is no analog stick or
tap-magnitude. The faithful keyboard analog of "tapping the control stick" is a
**directional press edge + attack within a short window** (an edge/timing-detected "tap"),
not an analog flick. So in pycats the mechanic is really *"attack + a fresh directional
tap → smash."* Name it for the input intent (`tap-smash`), not the (absent) analog stick.

## 2. Uncharged vs charged — a separate axis (don't conflate)

**Source — SmashWiki, *Smash attack*:**
> "**Uncharged** smash attacks typically do around 13% to 24% damage… In every game since
> Melee, they **can be charged by holding the buttons down**, giving them more damage and
> knockback."

So the charge-state terms are **"uncharged smash attack"** and **"charged smash attack"**;
charging = **holding**. This is **orthogonal** to the input method:

| | Dedicated button (pycats today) | Stick-flick + A (the ask) |
|---|---|---|
| **Uncharged** (fire instantly) | ✅ #366 (quick button tap) | the feature, uncharged |
| **Charged** (hold) | ✅ #327 (hold to charge) | the feature, held |

**Answering the ticket's Q2 directly:** the maintainer's "single-tap smash" is about the
**input method** (stick-flick vs button), **not** the charge state. pycats already fires
*uncharged* smashes via a quick tap of the dedicated button (#366); this feature adds a
second *input route*, which itself can be uncharged or charged like any smash.

## 3. Evaluate the proposed names → recommendation

| Proposed | Verdict | Why |
|---|---|---|
| "quick-smash" | ✗ reject | Reads as *fast/uncharged* — the **charge** axis (already done, #366). Misleads. |
| "simple-smash" | ✗ reject | Vague; no PM provenance; says nothing about the input. |
| "direct-smash" | ✗ reject | Ambiguous ("direct" = uncharged? unbuffered? a straight line?). No provenance. |
| **`tap-smash`** | ✅ **recommend** | Matches SmashWiki's "**tapping** the control stick"; names the *input method*; distinct from charge. |

**Recommended naming for pycats:**
- **Feature / mechanic:** **tap-smash** — "a smash triggered by a directional tap + attack."
- **Config/flag:** model the *input source*, not a new move — e.g. `smash_input: "button" | "tap"`
  (or allow both). The **move is still a "smash attack"** (fsmash/usmash/dsmash); only the
  **trigger** differs, so nothing in `move_select` needs renaming.
- **Contrast term for today's mechanic:** the existing dedicated key is the **smash button**
  (the pycats "C-stick"/"smash stick" analog). Use that phrase in docs when distinguishing.

## 4. Map to pycats: addition vs replacement + input seam

**Addition, not replacement.** In PM you can smash via the C-stick **and** by tapping the
main stick + A — multiple routes to the same move. So pycats should **keep the dedicated
`smash` key** and **add** tap-smash as a second route (opt-in), matching PM rather than
forcing one input style.

**Seam touch points (from the ticket + verified):**
- **`pycats/entities/fighter_input.py:288`** — today:
  `ground_smash = self._pressed(pressed, "smash") and p.fighter.on_ground`.
  A tap-smash adds an **alternate trigger**: detect *attack pressed **and** a fresh
  directional tap/flick* (an edge within a short window) → set `is_smash = True`. Needs
  press-edge/timing state (a "tap" = a direction newly pressed within N frames), which
  pycats does not track for this purpose yet.
- **`pycats/combat/move_select.py`** — **no change.** `resolve_move_key(..., is_smash)`
  already maps direction × `is_smash` → the smash move; the new path just sets `is_smash`
  via a different condition.
- **`pycats/sim/runner.py` keymaps (`P1_KEYS`/`P2_KEYS`)** — currently `attack`+directions
  but **no `smash` key**, which is *why sims never smash today* (fighter_input comment:
  "control maps without 'smash' … simply never smash"). **Goldens caveat:** a tap-smash
  that infers a smash from existing *attack + direction* inputs would make the sim **able
  to smash**, changing golden sim outcomes. So tap-smash must be **gated/opt-in** (a flag
  or a distinct input mode the sim keymaps don't enable), or the detection must be strict
  enough that no existing golden input sequence trips it. Flag this in the implementation
  ticket.

## Recommendation for the follow-up implementation ticket(s)
- Title/name the feature **tap-smash** (input route), not "quick/simple/direct-smash."
- Frame it as an **input-source addition** (`smash_input`: button and/or tap), the move
  unchanged.
- Call out the **tap-detection window** (how many frames define a "tap" direction edge)
  as a design decision needing a value basis (PM control-stick sensitivity is analog; the
  keyboard window is a pycats invention → `FOUND`/decision, per RULES "Changing values").
- Preserve golden stability: keep the sim keymaps smash-less / gate tap-smash so existing
  golden inputs don't newly smash.

## Sources
- SmashWiki — *Smash attack*: https://www.ssbwiki.com/wiki/Smash_attack
- SmashWiki — *C-Stick*: https://www.ssbwiki.com/wiki/C-Stick

(Canonical competitive **SmashWiki** at `ssbwiki.com`; note `smashwiki.com` 301-redirects to
Fandom's *Smashpedia*, a separate lower-authority wiki — the ssbwiki.com pages above are the
cited source.)
