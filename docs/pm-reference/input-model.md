# PM input model — the interpretation taxonomy (how PM reads a controller)

> **Audience:** an agent scoping pycats' input layer against Project M. Answers one
> question: *across the full input space — **held, tapped, double-tapped, released,
> buffered, analog-magnitude, smash** — how does PM interpret controller input, and
> which fighter actions key off each interpretation?*
>
> **Thread 1 of the #476 input-parity epic** (RESEARCH). This is the **PM-side
> reference model** — the "ideal" target. It deliberately does **not** audit pycats'
> current handling (that is thread 2, [#553](https://github.com/avidrucker/pycats/issues/553))
> or propose architecture (thread 3). Keyboard-port implications appear only as ⚠
> flags that hand off to thread 2 / the scope decision
> ([#554](https://github.com/avidrucker/pycats/issues/554)).
>
> **Sourcing:** primary/decomp where it exists, SmashWiki as citable secondary, per
> [`where-to-find-source-data.md`](./where-to-find-source-data.md) and RULES #562.
> Reasoning-derived claims are marked **(inference)**; engine-hardcoded values no
> primary carries are marked **⚠ best-guess**. Much of this consolidates already-sourced
> repo findings (#374/#407/#436/#458) rather than re-deriving them.

## The seven interpretation modes at a glance

| # | Mode | One-line | PM anchor |
|---|------|----------|-----------|
| 1 | **Held** (continuous sample) | state persists while input is down / stick tilted | analog tilt + button-hold |
| 2 | **Tapped** (rising edge) | a fresh press fires an action once | button/direction press-edge |
| 3 | **Double-tapped** | two presses in a window | **PM has none — walk↔dash is analog** |
| 4 | **Released** (falling edge) | press *duration* / release selects the outcome | short-hop, shield-drop |
| 5 | **Buffered** | inputs queue at the end of an action | **Melee/PM: essentially none**; Brawl: 10 f |
| 6 | **Analog magnitude / threshold** | *how far* the stick deflects selects the action | deadzone 0.2875 / dash 0.8 |
| 7 | **Smash input** | tap-stick+A **or** C-stick → smash | orthogonal to charge |

---

## 1. Held — continuous per-frame sample

The engine samples the control every frame; the action lasts as long as the input is
held (or the stick stays deflected).

| Behavior | Actions that use it | Source |
|---|---|---|
| **Analog tilt magnitude** sampled each frame → grounded speed | **Walk** (speed scales with stick tilt); aerial **drift**; **ledge-hang** facing | [movement-and-tech](./movement-and-tech.md) / #374; SmashWiki [*Walk*](https://www.ssbwiki.com/Walk) — walk is the analog-magnitude stroll |
| **Button held down** → sustained state | **Shield** (hold raises the bubble: GuardOn → Guard → GuardOff); **crouch** (hold down); **run** (hold the dash direction past the initial-dash window) | [defense-shield-dodge](./defense-shield-dodge.md) (shield sub-states); [movement-and-tech](./movement-and-tech.md) (run) |
| **Hold the buttons after the hit-frame** → charge | **Smash-attack charge**, **special charge-holds** | SmashWiki [*Smash attack*](https://www.ssbwiki.com/Smash_attack): smashes *"can be charged by **holding the buttons down**, giving them more damage and knockback."* |

---

## 2. Tapped / fresh press — rising edge

A newly-pressed button or direction (an edge, not a held state) fires an action once.

| Behavior | Actions | Source |
|---|---|---|
| Fresh **button** press | **Jump** (press → jumpsquat begins), **attack/tilt** (A), **grab**, **special** (B), **ledge getup** (up/toward) | [movement-and-tech](./movement-and-tech.md) — jumpsquat is the grounded startup a jump press enters |
| Fresh **directional** hard tap → dash | **Initial dash** (a stick tap to ≥0.8 within ~1–2 f of neutral) — analog-defined, see §6 | [pm-walk-run-dash §Q1](../research/2026-07-01-pm-walk-run-dash-mechanics.md); SmashWiki [*Dash*](https://www.ssbwiki.com/Dash) |

Note: in PM the "tap" that starts a dash is **not** a digital press-edge but an
*analog* magnitude crossing (§6). It is listed here because functionally it is the
"fresh-press" family; the mechanism is analog.

---

## 3. Double-tapped — within a window

**PM has no digital double-tap interpretation.** Its walk↔dash split is decided by a
single **analog** motion (stick magnitude, §6), not two presses.

| Quantity | Value | Confidence | Source |
|---|---|---|---|
| **Smash-input / dashback window** (neutral → dash) | cross `\|X\|<0.2875` → `\|X\|≥0.8` within **1 frame (vanilla) / 2 frames (UCF)** | **explicit** | [pm-walk-run-dash §Q1](../research/2026-07-01-pm-walk-run-dash-mechanics.md); SmashWiki [*Universal Controller Fix*](https://www.ssbwiki.com/Universal_Controller_Fix), [20XX/UCF](https://www.20xx.me/ucf.html) |
| **Dash-dance reversal window** | = each character's **initial-dash length, 7–18 frames** | explicit, per-character | SmashWiki [*Dashdance*](https://www.ssbwiki.com/Dashdance); rukaidata per-char |
| **Digital "double-tap window"** (press→release→press) | **no PM number exists** — a keyboard surrogate only (~150–250 ms ≈ 9–15 f) | ⚠ keyboard-port, not parity | [pm-walk-run-dash Addendum #407](../research/2026-07-01-pm-walk-run-dash-mechanics.md) |

⚠ **Keyboard-port flag (hands off to thread 2 / #554):** since a keyboard has no
magnitude, any "double-tap to dash" is a *surrogate* for PM's analog tap, tuned to
human ergonomics — it is explicitly **not** a Melee-faithful number. This is where
pycats' `DOUBLE_TAP_WINDOW` lives; auditing it is thread 2's job, not this one.

---

## 4. Released — falling edge / press duration

The **length** of a press (when the button is released) selects the outcome.

| Behavior | Actions | Source |
|---|---|---|
| **Press duration** at jump | **Short hop vs full hop** — a *quick* jump press (released before jumpsquat ends) = short hop; a *held* press = full hop | [movement-and-tech](./movement-and-tech.md): *"a quick jump press = short hop (lower); a held [press] = full hop"*; SmashWiki [*Short hop*](https://www.ssbwiki.com/Short_hop) |
| **Release** of a held input | **Shield drop** (release shield → GuardOff lag); **charged special** release | [defense-shield-dodge](./defense-shield-dodge.md) (GuardOff on release) |

---

## 5. Buffered — inputs queued at the end of an action

| Game | Universal buffer | Source (verbatim) |
|---|---|---|
| **Melee** | **none** (save a few special cases) | SmashWiki [*Input buffering*](https://www.ssbwiki.com/Input_buffering): *"Super Smash Bros. Melee does not buffer inputs in general, save for a select few."* |
| **Brawl** | **10 frames** | *"there is a window of 10 frames at the end of most moves and animations where the player can buffer any action."* |
| **Project M** | **Melee-style — essentially none** | **(inference)** PM is a Brawl mod that restores Melee behavior, so it removes Brawl's 10-frame universal buffer. ⚠ **best-guess** — SmashWiki's buffering page does not name PM; firm against a **PMDT changelog / Project+** primary before citing a hard number. |

The Melee/PM "select few" that *do* buffer: **DI / SDI** are set during **hitlag**
(the buffered defensive window), and a **jump out of jumpsquat** is buffered. Source:
[combat-knockback-hitstun](./combat-knockback-hitstun.md) (*"DI/SDI are buffered here"*
during hitlag). Takeaway for parity: PM fighters do **not** get Brawl's forgiving
end-of-move queue — inputs are largely read live, frame-by-frame.

---

## 6. Analog magnitude / threshold

*How far* the stick is deflected — not just its direction — selects the action. This
is the mode with **no digital-keyboard analog** (a key is either full-deflection or
nothing), so it is the crux of the #554 scope decision.

| Behavior | Threshold | Actions | Source |
|---|---|---|---|
| **Deadzone** (below = neutral) | `\|X\| < 0.2875` (<23/128 units) | nothing registers | [20XX/UCF](https://www.20xx.me/ucf.html), [pm-walk-run-dash §Q1](../research/2026-07-01-pm-walk-run-dash-mechanics.md) |
| **Dash / smash range** | `\|X\| ≥ 0.8` (≥64 units) | dash entry, smash input | same |
| **Tilt vs smash** | soft/slow deflection = **tilt**; hard/fast past 0.8 = **smash** | tilt attacks vs smash attacks | SmashWiki [*Smash attack*](https://www.ssbwiki.com/Smash_attack), [*Control stick*](https://www.ssbwiki.com/Control_stick) |
| **Ledge drop** | down/away **past a magnitude threshold** (a slight tilt does *not* drop) | release the ledge | [ledge-mechanics](./ledge-mechanics.md) / #458 |
| **Fast-fall** | down past threshold while falling | fast-fall | SmashWiki [*Fast-falling*](https://www.ssbwiki.com/Fast-falling) |

⚠ **Keyboard-port flag:** a digital press = full deflection (`|X| = 1.0`), which
clears every threshold instantly. So tilt-vs-smash-by-magnitude and threshold ledge-drop
have **no keyboard analog without emulation** — this is exactly the "how faithful vs
how simple" line #554 must draw, and #458 documented the resulting accidental-ledge-drop
symptom.

---

## 7. Smash input — two routes, orthogonal to charge

A smash attack can be triggered two ways, and the **input method** is a separate axis
from the **charge state** (uncharged vs charged). Full treatment:
[pm-tap-smash-input-naming-findings (#436)](../research/pm-tap-smash-input-naming-findings.md).

| Route | Mechanism | Source (verbatim) |
|---|---|---|
| **Tap-stick + A** | *"performed by **'tapping' the control stick** and pressing the attack button at the same time"* | SmashWiki [*Smash attack*](https://www.ssbwiki.com/Smash_attack) |
| **C-stick** ("smash stick") | a stick dedicated to smashes; *"primarily used to perform smash attacks"* | SmashWiki [*C-Stick*](https://www.ssbwiki.com/C-Stick) |

**Orthogonal axes** (don't conflate):

| | Uncharged (fire instantly) | Charged (hold) |
|---|---|---|
| **Tap-stick + A** | tap-smash, uncharged | tap-smash, held |
| **C-stick / dedicated button** | button-smash, uncharged | button-smash, held |

⚠ **Keyboard-port note:** the pycats "smash button" is the **C-stick / dedicated-button**
route; the tap-stick route's keyboard analog is *attack + a fresh directional press-edge*
(there is no analog flick). Naming/seam is #436's; whether to add it is #554's.

---

## Handoff to thread 2 (#553)

Each mode above names the **PM behavior + which actions use it + a source**. Thread 2
audits pycats' *current* handling against this table — for each action, which mode
pycats actually uses and the fidelity gap. The ⚠ keyboard-port flags (§3, §6, §7) are
the open decision points that feed the scope decision (#554) and the architecture plan
(thread 3).

## Open / to-firm

- **PM buffering (§5)** — the only category with no PM-specific primary; currently
  Melee-inheritance **inference**. Firm against a PMDT changelog or Project+ before any
  buffer value is used in code.
- **Per-character initial-dash lengths (§3)** — the 7–18 f range is general; exact
  per-archetype values come from rukaidata when the cats are built (#117).

## Refs

Epic [#476](https://github.com/avidrucker/pycats/issues/476) · thread 2
[#553](https://github.com/avidrucker/pycats/issues/553) · scope decision
[#554](https://github.com/avidrucker/pycats/issues/554). Consolidates: #374/#407
(walk/dash/double-tap), #436 (smash input naming), #458 (analog ledge-drop).
Sources map: [`where-to-find-source-data.md`](./where-to-find-source-data.md).
