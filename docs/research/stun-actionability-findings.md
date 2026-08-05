# Stun actionability in Project M — can a stunned fighter move? (#610)

> Determines what actions a fighter may take while **stunned** in Project M /
> Melee, and whether pycats matches. Trigger: in pycats a stunned fighter can
> still move *downward* — dropping through a soft platform by holding down.
>
> Inputs:
> - Primary sources: SmashWiki [Hitstun](https://www.ssbwiki.com/Hitstun), [Stun](https://www.ssbwiki.com/Stun), [Platform](https://www.ssbwiki.com/Platform)
> - Current pycats model: `Player.update` (`pycats/entities/player.py`), `step_physics` (`pycats/entities/fighter_physics.py`), the `hitstun`/`hurt`/`stun` states in `pycats/charts/fighter_chart.py`
> - Canonical reference: Project M 3.6 (the project's fidelity target)
> - Date: 2026-07-05
>
> **Verdict: parity bug.** In Melee/PM a stunned or hit-stunned fighter cannot
> initiate a soft-platform drop-through; it requires the *standing / actionable*
> state, which stun and hitstun are not. pycats's held-`down` drop-through fires
> during hitstun/dizzy and should be gated off. See §3 + the follow-on DEV
> outline in §5.

## 1. The question and the pycats "have"

pycats models two distinct "stunned" conditions, both leaves under the `hitstun`
compound state (`pycats/charts/fighter_chart.py`):

- **Hitstun** — the `hurt` state, driven by `hurt_timer` (knockback recovery, #44/#43).
- **Shield-break dizzy** — the `stun` state, driven by `stun_timer` (shield break, #12; the magenta DIZZY bar).

`Player.update` (`pycats/entities/player.py`) sets `in_hitstun = hurt_timer > 0 or
stun_timer > 0` and, while it holds, **skips both `handle_move` (walk) and
`handle_actions` (jump / dodge / attack / grab)** — those are correctly locked;
horizontal launch velocity bleeds off via `decay_velocity`.

**But** the same frame still calls `step_physics(self, platforms, held)`
(`pycats/entities/fighter_physics.py`), which passes `held`-`down` straight into
`solve_vertical` as the **soft-platform drop-through** trigger — gated only by the
shield+down spot-dodge guard, *not* by `in_hitstun`. So a stunned fighter standing
on a pass-through platform who holds **down drops through it**. (There is no
fast-fall in pycats yet — a `#### TODO: implement fast fall` note sits in
`Player.update` — so the observed "downward movement" is specifically the
drop-through, plus unconditional gravity on `vel.y`.)

## 2. Findings (primary sources)

### 2a. Hitstun — no self-initiated action

> "Hitstun (known as DamageFrame internally) is a period of time after being hit
> by an attack that a character is unable to act outside of directional influence
> or teching." — SmashWiki, [Hitstun](https://www.ssbwiki.com/Hitstun)

The only exceptions are **directional influence** (DI/SDI) and **teching**. DI and
SDI *alter the trajectory* of the existing knockback — they do not let the player
*initiate* a new action such as walking, jumping, or a platform drop-through.
Teching is a surface-collision input, not free movement. So a hit-stunned fighter
cannot self-initiate downward movement through a platform.

### 2b. Shield-break dizzy — no actions, and impossible while airborne

> "A stunned character is dazed for a few seconds and can't perform any actions
> until the condition ends." — SmashWiki, [Stun](https://www.ssbwiki.com/Stun)

And decisively for the drop-through question:

> "It is impossible to be stunned while airborne. Possibly as a result, any
> airborne state induced upon a stunned character will cancel the stunned state
> immediately." — SmashWiki, [Stun](https://www.ssbwiki.com/Stun)

So dizzy is a **grounded, action-less** state. A drop-through would make the
fighter airborne — which in Melee *cancels the stun outright*. "Stunned **and**
dropping through a platform" is therefore not a state that exists: the moment the
fighter leaves the platform they are no longer dizzy. (Only button-mashing
affects the timer: "Button mashing reduces the duration of shield break stun by
… 3 frames per input in later games.")

### 2c. Soft-platform drop-through requires the standing state

> "While standing on a soft platform, a character may fall down through it by
> tapping down on the control stick." — SmashWiki, [Platform](https://www.ssbwiki.com/Platform)

> "Shield platform dropping is a technique which can aid in attaining the
> **standing state necessary to drop through soft platforms**." — SmashWiki,
> [Platform](https://www.ssbwiki.com/Platform)

Drop-through is gated to the **standing (actionable)** state. Hitstun and dizzy
are, by 2a/2b, not actionable — so neither can drop through a platform.

## 3. Verdict — parity bug

pycats diverges from PM/Melee on **both** stun kinds:

| Condition | PM/Melee (sourced) | pycats (current) |
| --- | --- | --- |
| Hitstun (`hurt`) | Unable to act; only DI/teching. No self-initiated drop-through. | `step_physics` reads held-`down` → drops through a soft platform. **Diverges.** |
| Dizzy (`stun`) | No actions; cannot be stunned airborne (leaving the platform cancels stun). | Stays dizzy while dropping through via held-`down`. **Diverges twice** (drop-through *and* dizzy-persists-airborne). |

The held-`down` drop-through firing during `in_hitstun` is a **parity bug**. The
root cause is precise: `handle_move`/`handle_actions` are gated on `in_hitstun` in
`Player.update`, but the drop-through's held-`down` read lives downstream in
`step_physics`/`solve_vertical`, which is **not** gated on `in_hitstun`.

## 4. Project M applicability — labeled inference

SmashWiki documents **Melee**. The step "these Melee rules hold in Project M" is
**inference**, not a PM-specific primary quote — flagged per the project's
PM-parity sourcing discipline (cite primary; label inference). Basis: PM is built on Brawl but restores
Melee-style mechanics; PM notably restores **Melee hitstun** (removing Brawl's
hitstun-canceling), and shield-break dizzy + soft-platform drop-through are
Melee-identical in PM. No PM-specific source contradicts the Melee behavior above,
and pycats already treats PM 3.6 as its Melee-derived fidelity target for these
systems. If a PM-specific citation is later wanted, the
brawllib_rs / PMDT data is about *subaction* move data and would not speak to this
engine-level actionability gate — a PM replay / frame test would be the primary
check.

## 5. Follow-on DEV ticket (outline — not implemented, not yet filed)

A single-file gate fix, filed one-at-a-time after this lands (lazy decomposition):

- **Title:** `DEV: gate soft-platform drop-through off during hitstun/dizzy (PM parity, #610)`
- **Change:** suppress the held-`down` drop-through read in `step_physics`
  (`pycats/entities/fighter_physics.py`) while the fighter is in hitstun —
  i.e. thread the `in_hitstun` condition (or `hurt_timer > 0 or stun_timer > 0`)
  into the `should_prevent_drop_through` guard so a stunned fighter's held-`down`
  no longer drops them through a soft platform. Confirm no impact on the existing
  shield+down spot-dodge drop-through prevention.
- **Regression test (able-to-fail):** a fighter standing on a thin platform with
  `hurt_timer > 0` (and a second case `stun_timer > 0`) holding `down` stays on
  the platform (no `drop_platform` / no airborne transition); revert the gate →
  the fighter drops through (red). Pair with a still-passing case: an actionable
  fighter holding `down` still drops through.
- **Open sub-question for that ticket:** whether pycats should *also* cancel dizzy
  when a fighter becomes airborne (finding 2b) is a **separate** parity gap — note
  it, but keep the drop-through gate as the minimal fix; a dizzy-cancels-airborne
  change is its own ticket.

## Sources

- SmashWiki — [Hitstun](https://www.ssbwiki.com/Hitstun)
- SmashWiki — [Stun](https://www.ssbwiki.com/Stun)
- SmashWiki — [Platform](https://www.ssbwiki.com/Platform)
