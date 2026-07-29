# Nalio Down+A — findings: the down-tilt fires (keyed as `attack`), but thin-platform Down+A drops through and forfeits a jump

**Ticket:** #886 (RESEARCH · area:combat). **Date:** 2026-07-28. **Author:** dragonfruit (opus-4.8).
**Status:** findings only — no code changed. Downstream fixes are separate DEV tickets, filed one at a time after this lands.

Every claim below is labelled **[primary]** (a documented source or the running code), **[inference]** (reasoned from primaries), or **[gap]** (no source found; needs confirmation), per the parity-citation rule.

---

## TL;DR

1. **The ground down-tilt DOES fire.** On solid ground, Nalio's Down+A produces the move named `"down tilt"` — the real 3-hitbox PM `AttackLw3` authored in #132. It is stored under the **`"attack"` key**, not a `"dtilt"` key, which is why an earlier probe that printed the resolved *key name* (`attack`) read as "no down-tilt." **That earlier claim was wrong** — corrected here with a live `Player.update` trace. **[primary]**
2. **The naming is legacy debt, not a bug.** Nalio (and Birky) keep their down-tilt under `attack`; the newer cats (Gnok, Narz) use a proper `dtilt` key. Two conventions coexist. **[primary]**
3. **The real functional bug is on thin platforms.** Down+A on a soft/thin platform drops Nalio through instead of down-tilting, and the drop-through forfeits a grounded jump (2→1). Both diverge from Melee/PM. **[primary for the pycats behavior; parity below]**

---

## What was reproduced (live `Player.update`, nothing mocked)

Script: session scratchpad `downtilt_sim.py` (real `Player.update` = `handle_actions` + `step_physics`).

| Setup | Input | Result |
|---|---|---|
| SOLID ground | Down+A | `current_move.name = "down tilt"`, `on_ground=True`, `jumps=2` — **down-tilt fires, no drop, jump kept** |
| SOLID ground | Right+A | `ftilt` (control — side tilt works) |
| SOLID ground | neutral A | `jab` (distinct from Down+A) |
| THIN platform | Down+A | frame 0: `attack`/`down tilt` but `on_ground=False`, `jumps 2→1` (dropped through, jump forfeited); frame 1+: `dair` (now airborne → down-**air**), keeps falling |
| THIN platform | Down alone | drop-through, no move (baseline) |

So: **solid-ground Down+A is fine**; the two behaviors the human hit are the **thin-platform** cases.

---

## How the pieces fit (pycats code — [primary])

- **Move resolution.** `combat/move_select.py`: `_GROUND_A["down"] = "dtilt"` (line 26). `resolve_move_key(down, on_ground)` prefers `dtilt`; if the cat lacks it, falls back to `"attack"` (line 68). Nalio has no `dtilt` key, so grounded Down+A resolves to `attack`.
- **`attack` IS Nalio's down-tilt.** `characters/nalio_cat.py:44–46` — "Down-tilt (`attack`) — PM3.6 Mario `AttackLw3` … Mapped onto the `attack` move slot, so Nalio is usable via the attack button." Line 602: `"attack": _DOWN_TILT`. `nalio.json`'s `attack` entry: `name="down tilt"`, 3 hitboxes (9/9/8 dmg, angle 80) — the #132 data. So the fallback lands on the down-tilt *by design*; `attack` is not a neutral move for Nalio.
- **Neutral A is separate.** `_GROUND_A["neutral"] = "jab"`; Nalio has a `jab` key (3-box, name "jab"), so neutral-A ≠ Down+A. No collision.
- **Thin-platform drop-through.** `entities/fighter_physics.py:84–98` — `should_prevent_drop_through` covers only ground-spot-dodge, shield+down, and hitstun. It does **not** cover "an attack started this frame." `solve_vertical` reads **held** `down` (line 98) and drops the fighter through. There is no crouch/tap gate — a plain held down from any actionable state drops through.
- **Jump forfeit.** `entities/fighter_physics.py:119` — `_handle_takeoff(was_airborne)` (#473, the "walk-off forfeits the grounded jump" clamp) fires on any ground→air transition, so the drop-through spends a grounded jump (2→1).

---

## Q1 — Is grounded Down+A a "down-tilt"? What's the canonical name?

**Answer: yes — "down tilt" (d-tilt) is the canonical term, and it is the correct move for standing Down+A.**

- SmashWiki, [Down tilt](https://www.ssbwiki.com/Down_tilt): *"A **down tilt** (abbreviated 'd-tilt') … is a tilt attack performed by holding the control stick lightly down and pressing the attack button while on the ground, or pressing the attack button or Z while crouching."* **[primary]**
- It is distinct from the neutral jab (neutral stick) and from the down-smash (a flick, [Tilt attack](https://www.ssbwiki.com/Tilt_attack)). **[primary for tilt-vs-smash; inference for tilt-vs-jab]**
- The internal/animation name **`AttackLw3`** is *not* quotable from SmashWiki. It matches the documented `AttackS3`/`AttackHi3`/`AttackLw3` = f/u/d-tilt scheme and is used that way in #132/#212, but a verbatim primary was not captured this session. **[inference — confirm via the repo's brawllib_rs datamine if a quote is required]**
- Mario (SSBM) d-tilt: "quick spinning leg sweep," hitboxes active frames 5–8 ([Mario (SSBM)/Down tilt](https://www.ssbwiki.com/Mario_(SSBM)/Down_tilt)) — Nalio's active-frame window (5–8) matches. **[primary]**

**So pycats is right to treat Down+A as the down-tilt.** The only issue at Q1 is the **key name**: it is `attack`, not `dtilt`, which obscures the move in any key-based display/probe.

## Q2 — Is Nalio *supposed* to have a `dtilt`? Trace #132 vs the loaded kit.

**Answer: the down-tilt was authored and is present — as the `attack` key, deliberately. Nothing was lost in the #792 JSON flip.**

- #132 (CLOSED) authored "Nalio's real 3-hitbox down-tilt (AttackLw3)" and mapped it onto the `attack` slot (its own body: *"Nalio's `\"attack\"` (down-tilt)"*). This predates the `dtilt` key convention — at the time `attack` was the generic-A fallback and Nalio's single PM-faithful move. **[primary]**
- The #792 flip (`3deed68 feat(combat): flip Nalio to JSON`) carried the data across intact: `nalio.json`'s `attack` = name "down tilt", 3 boxes 9/9/8. Not lost, not renamed away. **[primary]**
- **Divergence across the roster:** Nalio + Birky store their down-tilt under `attack`; Gnok + Narz define a real `dtilt` key (`narz_cat.py:70` `name="dtilt"`, `:304` `"dtilt": _NARZ_DTILT`) and keep `attack` only as a placeholder neutral-A fallback (`narz_cat.py:297`). **[primary]**

**Conclusion:** not a missing move — a **naming-convention inconsistency**. Recommend a downstream *data-cleanliness* DEV ticket to migrate Nalio's (and Birky's) down-tilt to a `dtilt` key so all four cats share one convention and key-based displays read correctly. Low risk (move resolution already prefers `dtilt`); guard with the existing `test_nalio_cat.py` down-tilt assertions.

## Q3 — On a thin platform, should Down+A d-tilt or drop through? What's the correct precedence?

**Answer: it should perform the grounded down-tilt and stay on the platform. pycats' drop-through-on-Down+A is NOT faithful.**

- **Melee engine (meleelight, primary).** Drop-through is the `PASS` action state, entered **only** from crouch (`SQUAT`), shield (`GUARD`/`GUARDON`) — **never** from standing (`WAIT`). From standing, the tilt/smash checks run *before* the crouch transition (`WAIT.js:59–73`), so Down+A → `DOWNTILT`/`DOWNSMASH` and never reaches the drop. The drop condition itself (`SQUAT.js:21–49`) requires ALL of: already crouching, a one-frame window (`timer === 4`), a fresh down **tap** (rising edge — `input[6].lsY > -0.3`, i.e. neutral ~6 frames ago), and being on a platform (`onSurface[0] === 1`). **[primary]**
- **SmashWiki (primary).** [Soft platform](https://www.ssbwiki.com/Soft_platform): a standing character drops through *"by tapping down on the control stick"* — a **tap**, not a hold, and no attack. Down+A registers a grounded attack (the d-tilt) instead. **[primary for the tap; inference that Down+A = d-tilt on the platform]**

**Two parity gaps in pycats:**
1. **Attack does not suppress drop-through.** `should_prevent_drop_through` omits "attacking," so Down+A drops through. Faithful behavior: a same-frame attack input yields the grounded down-tilt and suppresses the drop.
2. **Drop-through triggers on *held* down, from any actionable state, with no tap/crouch/window gate.** Melee requires a crouch state + a fresh down-tap in a one-frame window. pycats' held-down model is coarser.

Fixing #1 alone resolves the human's reported bug (Down+A → down-tilt on a platform). #2 is a deeper drop-through-input fidelity question (tap-vs-hold) that likely deserves its own ticket and depends on the pending Brawl input-model research.

## Q4 — Does dropping through a platform correctly forfeit a grounded jump?

**Answer: no — Melee preserves the midair jump on a platform drop-through. pycats forfeiting it (#473) is a bug.**

- **Melee engine (meleelight, primary).** `PASS.init` (`PASS.js:12–20`) never touches `doubleJumped` or `jumpsUsed`; after a drop the character can still double-jump (`PASS.js:52`). Those flags are set only when a jump state is entered (`JUMPAERIALF/B.js:19`) and reset only on landing/respawn/ledge (`physics.js:399–400`, `REBIRTH.js`, `CLIFFCATCH.js`) — never by dropping through. **[primary]**
- **SmashWiki (corroborating).** [Double jump](https://www.ssbwiki.com/Double_jump)'s restore-list and the multi-jump-block passage treat drop-through as a fall, not a jump; no source says a drop spends a jump. **[inference / gap on a one-sentence quote]**

**Root cause in pycats:** #473 applied the walk-off jump-forfeit clamp to *every* ground→air transition, and a platform drop-through is one. The fix should exempt platform drop-through from `_handle_takeoff` (or the takeoff clamp should distinguish a walk-off/fall from an intentional platform drop). Recommend a downstream DEV ticket; guard with a thin-platform test asserting `jumps_remaining` is unchanged across a drop-through.

## Q_extra — After dropping through, A gives an aerial (d-air), not a d-tilt

Expected. Once the drop puts the fighter airborne, `resolve_move_key` returns the aerial (`dair`), matching Melee's grounded-vs-aerial split ([Aerial attack](https://www.ssbwiki.com/Aerial_attack)). **[inference from primaries]** This is only visible in pycats *because* of the Q3 bug — with drop-through suppressed on Down+A, the fighter never goes airborne and the d-tilt comes out.

---

## Recommended downstream DEV tickets (file one at a time, after this lands — NOT filed now)

1. **Suppress platform drop-through when an attack is input** (fixes the human's reported Down+A-on-a-ledge bug). Add "attack started this frame" to `should_prevent_drop_through`, or gate the held-down drop in `solve_vertical`. Test: Down+A on a thin platform fires `down tilt`, `on_ground` stays True. — *highest value, smallest change.*
2. **Platform drop-through must preserve the grounded jump.** Exempt drop-through from the #473 `_handle_takeoff` clamp. Test: `jumps_remaining` unchanged across a thin-platform drop-through.
3. **Data-cleanliness: migrate Nalio's (and Birky's) down-tilt to a `dtilt` key** so all four cats share the convention and key-based displays read "dtilt." Low risk.
4. **(Deeper, optional) Drop-through input fidelity — tap-vs-hold + crouch gate.** Melee needs a crouch + fresh down-tap in a one-frame window; pycats drops on any held down. Depends on the pending Brawl input-model research (#875). Larger; defer unless prioritized.

## Sources

- **pycats:** `combat/move_select.py:26,63,68` · `characters/nalio_cat.py:44–46,132,602` · `characters/data/nalio.json` · `characters/narz_cat.py:70,297,304` · `entities/fighter_physics.py:84–98,119` · #132 (closed — authored the down-tilt on the `attack` slot) · #473 (takeoff jump-forfeit clamp) · #612 (drop-through hitstun gate) · #792 (`3deed68`, JSON flip).
- **meleelight (Melee engine, primary):** `WAIT.js:59–73` · `SQUAT.js:21–49` · `GUARD.js:60–64` · `GUARDON.js:86–90` · `PASS.js:12–20,52` · `JUMPAERIALF/B.js:19` · `physics.js:399–400,1132` · `actionStateShortcuts.js:373–382,523–525`.
- **SmashWiki:** [Down tilt](https://www.ssbwiki.com/Down_tilt) · [Tilt attack](https://www.ssbwiki.com/Tilt_attack) · [Mario (SSBM)/Down tilt](https://www.ssbwiki.com/Mario_(SSBM)/Down_tilt) · [Soft platform](https://www.ssbwiki.com/Soft_platform) · [Double jump](https://www.ssbwiki.com/Double_jump) · [Aerial attack](https://www.ssbwiki.com/Aerial_attack).
