# ROUNDS v1 — the novel "%-per-second" seam (regen / heal / lifesteal / DoT) — findings

- **Role:** RESEARCH · **Resolves:** #1111 · **Date:** 2026-08-04 · **Findings-only** (no design decision, no spec, no implementation).
- Owner-decided later in a follow-on architect/decision ticket (ARC). This doc reports an **option space** and an **engine survey** only.

Seeded by **ADR-0013 §Per-seam ledger row 14** ("Novel %-per-second — INCLUDE v1, shape TBD via research").
Coordinates with **#1106** (broad buff catalog) and **#1115** (buff magnitudes) — this doc scopes strictly to the
**over-time percent-change family** (regen, heal-over-time, lifesteal analogs, self-DoT / poison) and cites those two rather than re-surveying the whole catalog.

---

## Summary

- **No per-tick percent accumulator exists in pycats today.** Combat is instantaneous: a hit adds `atk.damage` to `percent` in `Fighter.receive_hit` (`pycats/entities/fighter.py`). There is no field or hook that changes `percent` on a timer. A `%-per-second` seam is genuinely new state + a new per-frame hook — matching ADR-0013's row-14 note "none — new field + a per-tick hook".
- **The over-time family splits into three distinct shapes** that are NOT the same seam: **flat regen/DoT** (a signed constant delta per unit time, independent of combat), **lifesteal** (a fraction of damage *dealt* returned to the dealer as heal — fires on hit, not on a clock), and **on-hit / on-absorb heal** (a heal event triggered by a specific action, e.g. PSI Magnet absorb). A human must decide which of these "%-per-second" actually means for v1.
- **The engines have no generic regen mechanic** — Smash/PM/Brawl/Melee model this family only as **items and character moves**: Heart Container / Maxim Tomato / Food (instant heal), **Superspicy Curry** and **Flower/Lip's Stick** (self/inflicted DoT on a fixed frame interval), and **PSI Magnet** (Ness/Lucas absorb-a-projectile-as-heal — the closest lifesteal analog). Confirmed frame intervals exist for Flower (1% every 21 frames, cap 3000 frames). meleelight has none of these (5 fighters, no items). No PM 3.6 *primary* magnitude was found — all item numbers are **Brawl-inherited proxies** (per #1115).
- **percent→KB coupling is the flagged hazard.** Knockback is super-linear in the victim's post-hit percent (formula quoted below), so any DoT that inflates `percent` inflates *everyone's* knockback against that fighter — the same swinginess hazard ADR-0013 already named for the weight (row 1) and knockback (row 9) seams. Flag, don't solve.
- **Determinism is not at risk for a deterministic delta.** A flat regen/DoT driven by the integer frame counter needs **no RNG** and never touches the #166 seeded stream, so it stays golden-reproducible as long as the mutation is frame-exact and applied at a fixed point in the tick order. `percent` is snapshotted as `round(p.fighter.percent, 6)` (`pycats/sim/runner.py::snapshot`), which bounds float-accumulation drift.

---

## Part 1 — pycats implementation option space

All references are by symbol + file path (repo rule). This section enumerates options and tradeoffs; it does **not** pick one.

### 1.0 Grounding — where percent lives and moves today

- **Mutation site (instantaneous model).** `percent` changes in exactly one combat path: `Fighter.receive_hit` in `pycats/entities/fighter.py` does `self.percent += atk.damage` on the non-shield branch. The reset path (`Fighter.respawn`/KO) sets `self.percent = 0`. There is no timer-driven mutation anywhere.
- **`percent` is a guarded float.** The property setter in `Fighter` is `self._percent = max(0, value)` — a floor at 0 (a heal can never drive percent below 0), no ceiling. Type is float (unlike the int-contracted velocities).
- **Per-frame advance path.** The headless tick loop is `run_battle` in `pycats/sim/runner.py`: per frame it calls `p.update(...)` for each player, then `resolve_player_push`, then `attacks.update(...)`, then `hit_resolution.process_hits(players, attacks)`, then `match.tick()`, then appends `snapshot(...)`. Fighter-owned per-frame timers already live in `Fighter.tick_timers` / `Fighter.tick_action_timers` / `Fighter.tick_respawn` (`pycats/entities/fighter.py`), each a decrement loop with no RNG — the existing precedent for "advance a fighter's own per-frame state".
- **FPS is fixed at 60.** `pycats/config/screen.py` defines `FPS = 60` and `tick_fps(speed) = max(1, round(FPS * speed))`. So **1 second = 60 sim frames**, and a "per-second" rate converts to per-frame by dividing by 60. `RESPAWN_DELAY_FRAMES = int(2 * FPS)` (`pycats/config/stage.py`) is the existing precedent for a seconds→frames constant.
- **Golden seam.** `snapshot` (`pycats/sim/runner.py`) records `round(p.fighter.percent, 6)` per player per frame. Any per-tick percent change is directly observed by the golden tests; it must be frame-exact and byte-stable.

### 1.1 New state — what field(s), and which shape

The over-time family is not one shape. Enumerate:

| Shape | State it needs | Sign / semantics | Fires on |
|-------|----------------|------------------|----------|
| **Flat regen / DoT** | one signed rate, e.g. `percent_per_second: float` (heal = negative, DoT = positive, matching the `percent += damage` sign convention where + is worse for the victim) | constant delta, independent of combat | a clock (every frame or every N frames) |
| **Proportional lifesteal** | a fraction, e.g. `lifesteal_frac: float` on the *attacker* | heal to the dealer = `frac × damage_dealt` | the dealer landing a hit (an event, not a clock) |
| **On-hit / on-absorb heal** | a per-event heal amount or multiplier | a heal triggered by a specific action | a specific action (e.g. absorbing a projectile) |

Open sub-questions the shape choice forces (not decided here):
- Is the rate a **`FighterData` field** (serialized in `characters/data/<cat>.json`, part of the frozen dataclass like `weight`/`gravity`) or **runtime fighter state** (a mutable attr on the `Fighter` instance set by the modifier apply-layer, closer to how timers live)? ADR-0013's other seams (rows 1–10) are all `FighterData`/`MoveData` fields; a **DoT/regen that a card grants for a round** is more naturally a *runtime* modifier, since ADR-0013 §Consequences says the apply-layer (load-time vs per-tick) is itself an unresolved decision.
- **Duration:** is the effect permanent-for-the-match, or does it carry its own countdown timer (like Superspicy Curry's 13 s / Flower's 3000-frame cap)? A timed effect needs a second field (frames remaining) and a decrement in the tick path.
- **`gravity` is the only genuine float among the physics attrs** (ADR-0013 §Context fact 2); `percent` is also a float, so a percent-rate field is a natural float with **no int-contract** — unlike the velocity seams, it does not need `round()` on the field itself (though see §1.5 for accumulation rounding).

### 1.2 Hook site — three candidates

| Candidate | Where | Pros | Cons |
|-----------|-------|------|------|
| **A. Fighter per-frame tick** (new `Fighter.tick_percent_delta` alongside `tick_timers`) called from `Player.update` or directly from `run_battle`'s per-player loop | `pycats/entities/fighter.py` + the `for p in players: p.update(...)` line in `run_battle` | Mirrors the existing `tick_timers`/`tick_action_timers` precedent exactly; keeps percent logic in the `Fighter` domain object where `receive_hit` already lives; naturally frame-exact | Adds a per-frame mutation to a path currently only decrementing timers; must decide ordering vs. `process_hits` (does regen apply before or after this frame's hit?) |
| **B. In `hit_resolution.process_hits`** | `pycats/systems/hit_resolution.py` | Right home for **lifesteal** specifically (the dealer's heal is a function of the hit that just landed — `record_hit_landed`/`record_damage_given` already fire here) | Wrong home for **flat regen/DoT**, which is not hit-triggered — a fighter regenerates while standing idle, when `process_hits` may do nothing for them |
| **C. A new `systems/` module** (e.g. `systems/over_time.py`) called from `run_battle` once per frame over all players | new file under `pycats/systems/` + a call in the `run_battle` loop | Decomplects the over-time family from both combat and the Fighter object; a clean seam for the future modifier apply-layer to target; parallels `systems/win_condition.py` (already the home for the stocks seam, ADR-0013 row 10) | New module + wiring; must still reach into each `Fighter` to mutate `percent`, so it does not fully avoid coupling |

Note the **shape ↔ hook coupling**: flat regen/DoT wants a clock hook (A or C); lifesteal wants the hit hook (B); on-absorb heal wants whatever code handles the absorb action. A single "%-per-second" field and a single hook may not cover all three shapes — that is a design fork, not a settled fact.

### 1.3 Determinism / golden reproducibility

- **A deterministic delta needs no RNG.** Flat regen/DoT and lifesteal are pure functions of (rate, frame count) or (fraction, damage dealt). They never draw from the #166 seeded PRNG stream. The #166 seam is `random.Random(DEFAULT_CONTROLLER_SEED)` injected into the controllers (`pycats/sim/controllers.py`); it governs *controller decisions*, not sim math. So an over-time percent seam **does not interact with the seeded stream at all** unless the effect is deliberately probabilistic (e.g. "X% chance per frame to tick") — which none of the surveyed engine mechanics are (all are fixed-interval). Keeping the effect deterministic keeps ordinary and seeded battles byte-identical, the property `pycats/sim/controllers.py` header already relies on.
- **Frame-exactness is the constraint.** Because `snapshot` records `round(percent, 6)` every frame, the effect must mutate `percent` at a **fixed, documented point in the tick order** (before/after `process_hits`, before `snapshot`) and by a **frame-deterministic amount**. Any dependence on wall-clock, iteration order over a set, or un-rounded float divergence would desync the render oracle (`test_battle_screen_render`, see MEMORY: render parity oracle) and the sim goldens.
- **Render oracle:** the HUD reads `percent` (`pycats/render/hud.py`), so a per-tick percent change is player-visible and will move the render parity oracle every frame it changes — expected, but it makes the effect a **player-visible change** (eyeball-OK gate applies when it ships).

### 1.4 percent → knockback coupling (flagged risk, not a decision)

The knockback magnitude is super-linear in the victim's **post-hit percent** `p`. Verbatim from `pycats/combat/knockback.py`:

```
KB = (((((p/10) + (p*d/20)) * (200/(w+100)) * 1.4) + 18) * (KBG/100)) + BKB
where p = target percent AFTER the hit, d = damage, w = weight, BKB/KBG per hitbox.
```

The `p*d/20` term makes KB grow faster than linearly in `p`. **Consequence for a DoT:** a self-DoT or an inflicted poison that raises a fighter's `percent` over time raises the knockback *every subsequent hit* deals to that fighter — for **all** attackers, not just the DoT's source. A regen (negative rate) does the inverse: it lowers everyone's KB against that fighter by bleeding percent off between hits. This is the same swinginess hazard ADR-0013 already flagged for the **weight** seam (row 1, "nonlinear + inverse") and the **knockback** seam (row 9, "the premortem's #1 swinginess hazard"). The #1076 premortem owns swinginess. **Flagged here as an interaction, not mitigated or decided.**

A second coupling: high `percent` does **not** by itself KO in pycats (KO is blast-zone crossing after knockback, via `systems/win_condition.py`), so a pure DoT with no hits **cannot** KO on its own — it only makes the next hit launch further. Whether a DoT *should* be able to KO (a percent ceiling / self-KO rule) is an open design question, not a current behavior.

### 1.5 Rounding / precision / clamping

`percent` is a float with a floor at 0 and no ceiling (`Fighter.percent` setter, `pycats/entities/fighter.py`). Accumulation-rule options:

| Rule | Mechanism | Precision / observability tradeoff |
|------|-----------|-------------------------------------|
| **Per-frame fraction** | `percent += rate / FPS` every frame (rate in %/s, FPS=60) | Smoothest HUD motion (percent ticks visibly every frame). Accumulates float rounding over many frames; e.g. 2%/s → 0.03333…/frame, whose sum can differ from `2.0` at the ~7th decimal — but `snapshot` rounds to 6 decimals, bounding the visible drift. Determinism holds because the op sequence is fixed. |
| **Per-second batch** | apply `rate` once every `FPS` frames (a 60-frame counter, like `RESPAWN_DELAY_FRAMES`) | Exact integer-second amounts (no fractional accumulation); the HUD steps once per second (chunky, visible "tick"). Needs a per-fighter frame counter as extra state. Off-by-one risk on when the counter fires relative to KO/respawn resets. |
| **Per-N-frame interval** (the engine pattern) | apply a fixed amount every N frames, e.g. Flower's "1% every 21 frames" | Matches how Brawl/PM actually model DoT (fixed frame interval, not a per-second rate). Cleanest fidelity to the surveyed mechanics; the "per-second" framing becomes derived (60/N ticks per second). |

Clamping questions (open): the 0-floor already prevents a heal from going negative; should a heal-over-time also stop at 0 (idempotent once healed) or is that the floor doing the job? Should a DoT respect any ceiling, or interact with the (nonexistent) percent-KO rule from §1.4? These are decisions, not settled.

---

## Part 2 — engine survey of over-time percent mechanics

Scope: the **over-time percent-change family only**. Magnitudes reuse **#1115** (`docs/research/pm36-buff-magnitudes-findings.md`); the broad catalog is **#1106** (`docs/research/fighter-buffs-findings.md`). New primary quotes fetched here fill the DoT-interval and lifesteal-analog gaps those docs left open.

**Evidence labels:** *confirmed* = a verbatim primary quote / datamine; *inference* = reasoned, not directly quoted. Per #1115, **no value below is a PM-3.6 primary** — item numbers are **Brawl-inherited** SmashWiki proxies (PM 3.6 inherits Brawl item behavior absent a changelog override, and #1108 found none for these items).

| Mechanic | Engine(s) | Effect (over-time shape) | Magnitude | confirmed / inference | Source |
|----------|-----------|--------------------------|-----------|------------------------|--------|
| **Superspicy Curry** | Brawl / PM 3.6 (item) | **self-DoT emitter** — user spews flames that deal damage while active | **1% per flame hit**, duration **13 s** | *confirmed* (Brawl-inherited quote) | SmashWiki via #1115 §1: "for thirteen seconds" · "the flames deal only 1% per hit" |
| **Flower / Lip's Stick** | Melee → Ultimate (status; PM inherits) | **inflicted DoT** — a flowered fighter takes damage over time on a fixed frame interval | **1% every 21 frames**; total-duration cap **3000 frames = 50 s**; effect duration `20 + damage*40` frames, −16 frames per mash input (Brawl onward) | *confirmed* (quotes; game-split, not PM-specific) | SmashWiki *Flower*: "takes damage over time (1% every 21 frames)" · "duration cap of 3000 frames, equal to 50 seconds" · "20 + damage * 40" · "16 frames per input from *Brawl* onward" |
| **PSI Magnet (Ness)** | Brawl / PM 3.6 (move) | **lifesteal analog** — absorbs an energy projectile, heals user by a multiple of the projectile's damage; active while special is held | **~1.6× the projectile's damage** (Brawl onward; SSB64 was 2×) | *confirmed* (Brawl-inherited quote) | SmashWiki *PSI Magnet*: "recovers about 1.6x (or one and two thirds) the damage the projectile would have dealt normally" · "lasts as long as the special button is held" |
| **PSI Magnet (Lucas)** | Brawl / PM 3.6 (move) | **lifesteal analog** — as Ness, larger multiple | **2.5× the projectile's damage** (Brawl) | *confirmed* (Brawl-inherited quote) | SmashWiki *PSI Magnet*: "recovers more percentage than Ness … (2.5x the damage)" |
| **Heart Container** | Melee / Brawl / PM 3.6 (item) | **instant heal** (not over-time — included as the family's heal anchor) | **100 percentage points** (Brawl); fully clears (Melee) | *confirmed* (Brawl-inherited) | #1115 §1 / #1106: "heal 100 percentage points of damage" |
| **Maxim Tomato** | Melee / Brawl / PM 3.6 (item) | **instant heal** | **50%** | *confirmed* (Brawl-inherited) | #1115 §1: "the Maxim Tomato heals 50% from a character's damage percentage" |
| **Food** | Brawl / PM 3.6 (item) | **instant heal** (per piece) | top-end **9–12%**, majority **<6%** | *confirmed* (weak-quote, table-derived) | #1115 §1 / #1106 |
| **Wario — Chomp heal-by-eating** | SSB4 / Ultimate **only** (NOT Brawl / PM) | on-eat heal per item | **1% each** | *confirmed as out-of-scope for PM* | #1106 *Series context*: "eating items heals Wario 1% each, SSB4/Ultimate only (not Brawl/PM)" |
| **Fairy Bottle** | SSB4+ **only** | conditional instant heal | 100% but only if user already ≥100% | *confirmed as out-of-scope for PM* | #1106: *Fairy Bottle* |
| **Generic per-second regen** | — | — | **none found** — no Smash/PM/Brawl/Melee mechanic is a flat "%-per-second" regen; the family is entirely items + character moves | *confirmed absence* (survey) | #1106 catalog + this hunt |
| **(meleelight)** | Melee engine (JS, #616) | — | **no items, no DoT, no PSI Magnet** (5 fighters: marth/puff/falco/fox/falcon) | *confirmed* | #1115 §Sources |

**Reading of the survey (inference):** the engines model this family as **discrete events on fixed frame intervals** (Flower's 21-frame tick, Curry's per-flame-hit), and lifesteal only ever appears as **projectile-absorption** (PSI Magnet), never as a fraction of melee damage dealt. There is **no** generic "heal N% per second" primitive anywhere in the canon — so a pycats flat-regen seam would be a **novel** mechanic with no direct engine precedent, whereas a fixed-frame-interval DoT (§1.5 row 3) and a projectile-absorb heal both have confirmed analogs.

---

## Open questions for the follow-on decision (ARC ticket)

Posed as questions for the human, not recommendations:

1. **State shape** — Does "%-per-second" for v1 mean **flat regen/DoT** (a signed rate), **lifesteal** (a fraction of damage dealt, on the attacker), **on-hit/on-absorb heal** (an event-triggered heal), or **more than one** of these? They need different fields and different hooks (§1.1, §1.2).
2. **Field home** — Is the rate a **`FighterData` field** serialized in `characters/data/<cat>.json` (like weight/gravity, rows 1–10) or **runtime fighter state** the modifier apply-layer sets per round (closer to timers)? ADR-0013 §Consequences leaves load-time-vs-per-tick apply unresolved.
3. **Hook site** — Fighter per-frame tick (A), `hit_resolution.process_hits` (B, natural for lifesteal), or a new `systems/over_time.py` (C)? (§1.2)
4. **Accumulation rule** — per-frame fraction, per-second batch, or per-N-frame interval (the engine pattern)? (§1.5) And what **tick order** relative to `process_hits` and `snapshot`?
5. **"Leech" = lifesteal vs flat regen** — Is a leech/drain card a **fraction of damage dealt returned as heal** (lifesteal, hit-triggered, the PSI-Magnet-shaped analog) or a **flat regen** that happens to be framed as leech? The survey found lifesteal only as projectile-absorption, never melee-fraction — so a melee-fraction lifesteal would be novel.
6. **Duration** — permanent-for-the-match, or a timed effect with its own countdown (Curry 13 s / Flower 3000-frame cap)? A timed effect needs a second field + a decrement.
7. **KB-coupling mitigation** — The DoT-inflates-percent-inflates-KB interaction (§1.4) is handed to the swinginess thread (#1076). Does v1 accept it as-is, cap the percent a DoT can add, or exempt DoT-added percent from the KB term? (Decision for swinginess, flagged here.)
8. **Clamping / KO semantics** — Should a DoT be able to KO (a percent ceiling / self-KO), given a pure DoT currently cannot KO on its own (§1.4)? Should heal-over-time do anything beyond the existing 0-floor?
9. **Determinism guarantee** — Confirm v1 keeps the effect **deterministic** (no #166 RNG draw), preserving the byte-identical ordinary-vs-seeded property. A probabilistic per-frame tick would be the only reason to touch the seeded stream (§1.3).

---

## References

- **ADR-0013** — `docs/adr/0013-rounds-v1-fighter-seam-modifier-contract.md`, §Per-seam ledger **row 14** (this ticket's seed) + §Follow-up item 1.
- **#1096** — ROUNDS wayfinder map (parent map for the seam threads).
- **#1106** — `docs/research/fighter-buffs-findings.md` (broad buff catalog; owns the full catalog).
- **#1115** — `docs/research/pm36-buff-magnitudes-findings.md` (buff magnitudes; owns Brawl-inherited numbers).
- **#1108** — `docs/research/pm36-buff-primaries-findings.md` (primary-source citations; found no PM-3.6 per-item override).
- **#166** — seeded-controller PRNG seam: `DEFAULT_CONTROLLER_SEED` + injected `random.Random` in `pycats/sim/controllers.py`.
- **pycats source cited (by symbol + file):**
  - `Fighter.receive_hit`, `Fighter.percent` setter, `Fighter.tick_timers` / `tick_action_timers` / `tick_respawn`, `Fighter.respawn` — `pycats/entities/fighter.py`.
  - `knockback` (KB formula) — `pycats/combat/knockback.py`.
  - `process_hits` — `pycats/systems/hit_resolution.py`.
  - `run_battle`, `snapshot` — `pycats/sim/runner.py`.
  - `FighterData` dataclass — `pycats/combat/data.py`.
  - `FPS = 60`, `tick_fps` — `pycats/config/screen.py`; `RESPAWN_DELAY_FRAMES` — `pycats/config/stage.py`.
- **New primary sources fetched this hunt:** SmashWiki *Flower* (DoT interval + duration cap), SmashWiki *PSI Magnet* (Ness/Lucas absorb-as-heal multipliers).
- **Canon baseline:** PM 3.6 (`docs/project-m-parity.md`). Router: `docs/mechanics-index.md`.
