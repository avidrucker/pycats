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

## Cross-refs & sources

Feeds **#374**. In-repo (primary, already-sourced): `docs/pm-reference/movement-and-tech.md`
(#147 movement model), `docs/research-spec-119-mario-cat-pm.md` (#119 Mario values),
`docs/research/pm-mechanics-implementation-analysis.md` (dash-vs-run phasing), `docs/glossary.md`
(initial-dash/dash-dance/foxtrot). External: [SmashWiki — Dash](https://www.ssbwiki.com/Dash),
[SmashWiki — Walk](https://www.ssbwiki.com/Walk), [Project M (SmashWiki)](https://www.ssbwiki.com/Project_M),
[The Smash Bros Movement System (CritPoints)](https://critpoints.net/2015/12/28/the-smash-bros-movement-system/).
Per-character scalars #126/#229. Orientation map #185.
