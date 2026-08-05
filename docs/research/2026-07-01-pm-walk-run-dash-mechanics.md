# Does Project M have distinct walk + run/dash? — the grounded-movement catalogue (#373)

> Research findings (#373, the research half of the walk/run/dash movement-parity work;
> the pycats *design* is #374). Answers: does PM have distinct walk vs run/dash, what are
> the mechanics, and what are the values. **Findings only — no pycats design, no code.**
> Date: 2026-07-01. Agent: FIG. Area: `area:entities`.
>
> **nohelp note:** the repo already answers most of this. `docs/pm-reference/movement-and-tech.md`
> (epic #147) owns the movement *model*, and `docs/research-spec-119-mario-cat-pm.md` (#119)
> already sourced PM Mario's *values* from SmashWiki/rukaidata. This doc **consolidates** the
> walk/run/dash answer for #374 and adds the pycats-gap framing; it does not re-derive them.

## TL;DR

**Yes — PM has distinct walk, initial-dash, and run as separate grounded states, plus
dash-dance / pivot / skid.** They are separate per-character *attributes* (PM tunes "walk
maximum velocity", "walk acceleration", and "dash initial velocity" independently — e.g. the
documented Bowser change bumps dash-initial 1.1→1.3 and walk-max 0.65→0.75). pycats has **none
of this split**: one `MOVE_SPEED` and one `run` state.

**The finding that matters for #374:** pycats' single grounded speed (`MOVE_SPEED = 6` ≈ 6 px/f)
is, in effect, **PM Mario's WALK** speed (1.1 u/f × 5.4 ≈ 5.9 px), *not* its dash/run (1.5 u/f ≈
8.1 px). So today every cat "walks everywhere" and there is no faster dash/run, no initial-dash
burst, and no dash-dance. Reaching parity is therefore *adding the dash/run layer on top of the
existing walk*, gated on the digital-input question #374 owns (PM's walk↔run split is driven by
**analog stick magnitude**, which a keyboard does not have).

## Q1 — Does PM have distinct walk AND run/dash? (Yes)

Grounded-movement states in PM (Melee-derived; from `docs/pm-reference/movement-and-tech.md`):

| State | What it is |
|-------|-----------|
| **Walk** | Analog-speed stroll (stick tilt); fully actionable; the slowest grounded move. |
| **Initial dash** | A stick *tap* → a burst of speed; the window in which dash-dance/foxtrot live. |
| **Run** | Holding the dash direction *past* the initial-dash window; you can't freely turn (must skid / pivot). |
| **Dash-dance** | Rapidly reversing within the initial-dash window (a spacing/bait tool). |
| **Pivot** | A frame-perfect turnaround at the end of a dash, to attack the other way with run momentum. |
| **Skid / turnaround** | Deceleration when reversing out of a run. |

External confirmation (structure): SmashWiki *Walk* / *Dash* and community PM stat lists treat
**walk-max-velocity, walk-acceleration, and dash-initial-velocity as separate character
attributes** — i.e. walk and dash/run are genuinely distinct, not one speed.

## Q2 — Mechanics & transitions

- **Trigger:** walk = partial analog tilt; initial dash = a hard tap; run = holding the tap
  direction past the initial window. The **magnitude of the stick** is what selects walk vs
  dash — the crux for a digital port (#374).
- **Transitions:** idle → walk (tilt) or → initial-dash (tap) → run (hold). Reversing from run
  requires a **skid/turnaround** or a **pivot**; you cannot instantly flip run direction.
- **Signature tech in the dash layer:** **dash-dance** (reverse within the initial-dash window)
  and **foxtrot** (re-dash forward repeatedly) — Melee-isms PM restores that base Brawl lacks.
  (Wavedash is air-dodge-into-ground, a *separate* tech — `#202`, not this ticket.)

## Q3 — Values (PM Mario, the reference archetype)

From `#119` (sourced from SmashWiki/rukaidata; `× PX_PER_UNIT ≈ 5.4` for pixels):

| Quantity | PM3.6 Mario (u/f) | × 5.4 → px/f | pycats today |
|----------|------------------:|-------------:|--------------|
| **Walk max** | 1.1 | 5.9 | `MOVE_SPEED = 6` — this **is** the walk |
| **Dash / run** | 1.5 / 1.55 | 8.1 | — (no dash/run; single speed) |
| Air speed (drift) | 0.86 | 4.6 | modelled via `AIR_FRICTION`, no cap |
| Gravity | 0.095 | 0.51 | `GRAVITY = 0.5` ✅ |
| Fall / fast-fall | 1.7 / 2.3 | 9.2 / 12.4 | `MAX_FALL_SPEED = 13` ≈ fast-fall; no FF mechanic |
| Ground friction | 0.06 (decel) | 0.32 | `GROUND_FRICTION` (multiplier — different model) |
| Initial-dash length / dash-dance window | frame-window (per-char) | — | — (not modelled) |

**Confidence:** walk/dash/run/gravity/fall values = **explicit** (sourced by #119). The exact
initial-dash *frame window* and per-character dash-dance timings = **gap** for non-Mario cats
(would need rukaidata per-character attribute pulls when those archetypes are built).
walk:dash ratio ≈ **1.1 : 1.5 ≈ 0.73** (walk is ~73% of dash).

## Handoff to #374 (the design)

The facts #374 needs are settled:
1. **PM has walk + initial-dash + run + dash-dance** — a real, multi-state grounded layer.
2. **pycats currently implements only the walk** (`MOVE_SPEED` ≈ Mario walk); everything faster
   is missing.
3. **The blocker is input, not values:** PM's walk↔dash split is analog (stick magnitude); a
   keyboard is digital. So #374's core job is choosing how a digital control scheme expresses
   walk vs dash/run (hold-to-walk/tap-to-dash, a modifier, a double-tap, or a reduced model),
   then which states/scalars to add and how to migrate the single `MOVE_SPEED`.
4. **Values are ready** for Mario; per-character dash values + dash-dance windows are a `gap` to
   fill per archetype (via rukaidata) when #117's cats are built.

## Non-goals (unchanged)

- The pycats parity design (input scheme, states, scalars, migration) — **#374**.
- Any movement code; per-character balance tuning (#117); wavedash (#202) / fast-fall / air-speed
  (#229 caveat).

---

# Addendum (#407): the `DOUBLE_TAP_WINDOW` value — PM has no literal number to copy

> Research findings for **#407** (`config.DOUBLE_TAP_WINDOW`, stamped `= 8` as a placeholder
> in slice 2b **#403**). Date: 2026-07-03. Agent: FIG. Area: `area:entities`. Findings +
> a recommended value only — no code.

## TL;DR

**PM/Melee has no "double-tap window" to port, because its walk↔dash split is analog** (stick
magnitude, per #374/D2). The closest analog quantity — the **smash-input detection window** — is
**1 frame in vanilla Melee** (2 with UCF), which is the number of frames the stick has to cross
from neutral to the dash threshold. **That 1–2 frame value is the wrong thing to copy into
`DOUBLE_TAP_WINDOW`:** a keyboard double-tap is *press → release → press*, physically impossible
in 1–2 frames (≈17–33 ms). So `DOUBLE_TAP_WINDOW` is a **keyboard-port surrogate** that must be
tuned to **human double-tap ergonomics**, not to PM's analog smash window. **Recommendation:
`DOUBLE_TAP_WINDOW = 10` (≈167 ms) as a forgiving default, acceptable range 8–15 (≈133–250 ms);
the current `8` is valid-but-tight, so this is a game-feel tuning call, not a parity bug.**

## Q1 — Analog smash-input (dash) detection window · confidence: **explicit**

Melee decides dash-vs-walk from a single stick motion, not a double press. From a neutral stick,
a **dash (smash input)** registers when the X-axis goes from inside the **deadzone**
(`|X| < 0.2875`, <23 stick units) on one frame to the **dash range** (`|X| ≥ 0.8`, ≥64 units) on
the **next frame** — the documented **"one-frame dashback window."** A smash input is defined as
crossing `X ≥ 0.8` **within ~2 frames** of leaving neutral. The **Universal Controller Fix (UCF)**
widens the dashback window from **1 → 2 frames**; a proposed 2→3 widening (dash out of crouch) was
rejected as making the input "too easy." So the analog anchor for our digital window is **1 frame
(vanilla) / 2 frames (UCF-standard)** — cross the 0.8 threshold that fast and it's a dash; cross it
slower and it's a walk.

## Q2 — Dash-dance / initial-dash reversal window · confidence: **explicit, per-character**

The window in which a reversed input reads as a **dash-dance** equals each character's
**initial-dash animation length: 7–18 frames** depending on character (e.g. Fox's initial dash is
21 frames but transitions to run on frame 12; a character can *turn around* after a single frame).
This is a per-character `gap` to fill per archetype (rukaidata) when #117's cats are built; it does
**not** bound `DOUBLE_TAP_WINDOW` (which gates dash *entry*, not dash-dance reversal) — noted for
the dash-dance/pivot spike **#387**.

## Q3 — Digital-controller precedent (B0XX / Smash Box) · confidence: **inferred**

Box controllers (B0XX, Smash Box) replace the analog stick with buttons; a direction press maps to
**full deflection (`|X| = 1.0`), which clears the 0.8 dash threshold instantly** — so the
smash/dash transition is effectively **a single frame** and these controllers **do not expose a
separate tunable "double-tap window."** (They're tuned to *match* GCC dash behaviour, and
documented dash-speed differences between digital and analog inputs exist.) Takeaway: the box-controller
precedent is *instant* dash on press — it offers **no digital double-tap window** number to borrow,
which is why our surrogate has to come from ergonomics (Q4), not hardware precedent.

## Q4 — Keyboard / fighting-game convention (the actual basis) · confidence: **convention, not parity**

With no analog magnitude and no box-controller window to copy, the faithful anchor is **human
double-tap ergonomics**. Double-tap-to-dash/run in keyboard fighters and RTS UIs conventionally
sits around **~150–250 ms** between the two presses; at 60 FPS that is **≈9–15 frames**. The
current `8` (≈133 ms) is at the tight/technical end — executable, but demands a fast repeat. This
band is a **convention sanity-check, explicitly not a Melee-faithful number** (marked `gap` — no
single sourced keyboard value exists).

## Recommendation for pycats (60 FPS)

- **PM has no faithful single number** for `DOUBLE_TAP_WINDOW` — it is analog. State this in
  `config.py` beside the constant (drop the bare `⚠` guess framing; this value is a *justified
  surrogate*, not an un-sourced guess).
- **Recommended value: `DOUBLE_TAP_WINDOW = 10`** (≈167 ms) — a forgiving default squarely inside
  the ergonomic band. **Acceptable range 8–15** (≈133–250 ms). Keep `8` if a deliberately tight,
  technical feel is wanted; widen toward 12–15 if playtesting reports missed dashes.
- **This is a game-feel tuning call, not a parity defect** — the one-line config change (value +
  sourced comment) is filed as follow-up **#489**. No engine code in this research ticket.

## Sources (#407)

[SmashWiki — Universal Controller Fix](https://www.ssbwiki.com/Universal_Controller_Fix)
(dashback window 1→2 frames), [SmashWiki — Dash](https://www.ssbwiki.com/Dash) &
[SmashWiki — Dashdance](https://www.ssbwiki.com/Dashdance) (initial-dash 7–18 f, reversal =
initial-dash length), [Smashboards — UCF](https://smashboards.com/ucf/) & [20XX — UCF](https://www.20xx.me/ucf.html)
(deadzone `<0.2875`, dash range `≥0.8`, one-frame window), [SmashWiki — Control stick](https://www.ssbwiki.com/Control_stick),
[B0XX](https://b0xx.com/) & [Smash Box (Wikipedia)](https://en.wikipedia.org/wiki/Smash_Box_controller)
(digital→full-deflection mapping). Confidence tags per section above.

---

## Cross-refs & sources

Feeds **#374**. In-repo (primary, already-sourced): `docs/pm-reference/movement-and-tech.md`
(#147 movement model), `docs/research-spec-119-mario-cat-pm.md` (#119 Mario values),
`docs/research/pm-mechanics-implementation-analysis.md` (dash-vs-run phasing), `docs/glossary.md`
(initial-dash/dash-dance/foxtrot). External: [SmashWiki — Dash](https://www.ssbwiki.com/Dash),
[SmashWiki — Walk](https://www.ssbwiki.com/Walk), [Project M (SmashWiki)](https://www.ssbwiki.com/Project_M),
[The Smash Bros Movement System (CritPoints)](https://critpoints.net/2015/12/28/the-smash-bros-movement-system/).
Per-character scalars #126/#229. Orientation map #185.
