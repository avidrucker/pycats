# PM 3.6 initial-spawn (match-start) — re-sourced Part A

> **Agent:** FIG · **Authored:** 2026-08-07 · **Ticket:** #1321

Re-sources the six **initial match-start spawn** rules (Part A) that
[`spawn-respawn-catalog-findings.md`](./spawn-respawn-catalog-findings.md) (#1317)
recorded as **all GUESSED** — no quoted value on any of them. This doc replaces those
GUESSED markers with **FOUND-by-engine** wherever a meleelight line pins the behaviour,
adds a SmashWiki secondary tier and a Project-M-CC codeset cross-check, and keeps the
pycats current-state column + match verdict so the decision child (#1316 child 2) has a
sourced Part A gap table.

**Scope:** initial match-start spawn only. Post-KO respawn (Part B of #1317) is already
sourced and is not re-derived here. No ruling, no code, no value change.

## Provenance tiers

| Marker | Meaning |
|---|---|
| **FOUND** | A primary/secondary quote (SmashWiki, PM/Brawl docs) pins the value. |
| **FOUND-by-engine** | A meleelight code line pins it. meleelight is a **Melee** reimplementation → Melee→PM is `[inference]` (carried from #830/#1310/#1317). |
| **GUESSED** | No quote and no engine line — convention-level, flagged soft. |

**Melee→PM inheritance note.** The **Project-M-CC** 3.61 codeset
(`~/Documents/Study/reference/Project-M-CC`, #664) was searched for any match-start /
entrance / initial-spawn override: **none exists** — every spawn-related code targets
*post-KO* respawn (`All star VS: proper respawn`, `Respawn Camera Zoom Refocus`, `CPU
falls from respawn plane`) or ledge invincibility, not the match-start entrance. So PM 3.6
inherits **Brawl's** default match-start entrance unmodified, and Brawl's entrance is the
same drop-in-from-above shape Melee uses (the engine below). That reinforces the
`[inference]` tier for these rows rather than weakening it: the parity target did not touch
match-start spawn, so the Melee/engine behaviour carries.

## Sources worked (in the ticket's order)

1. **meleelight** (`~/Documents/Study/JavaScript/meleelight/`, #616) — the match-start init
   path, primary evidence for every row below:
   - `src/main/main.js` — `startingPoint = [[-50,50],[50,50],[-25,5],[25,5]]`,
     `startingFace = [1,-1,1,-1]`, `ground = [[-68.4,0],[68.4,0]]`; `startGame()` sets
     `startTimer = 1.5` and `starting = true`.
   - `src/main/player.js` — `playerObject` ctor sets `this.actionState = "ENTRANCE"`;
     `physicsObject` ctor sets `grounded = false`, `doubleJumped = false`,
     `jumpsUsed = 0`, `invincibleTimer = 0`, `intangibleTimer = 0`.
   - `src/characters/shared/moves/ENTRANCE.js` — the entrance action state:
     `canBeGrabbed : false`, `phys.grounded = false`, and `interrupt` transitions to
     `FALL` once `timer > 60`.
2. **SmashWiki** — [On-screen appearance](https://www.ssbwiki.com/On-screen_appearance),
   [Invincibility](https://www.ssbwiki.com/Invincibility) (secondary corroboration).
3. **Project-M-CC** 3.61 codeset (#664) — cross-check for a PM-specific match-start
   override (result: none, see note above).

## pycats current state (read from source)

All spawn state is set by `Fighter.reset_to_spawn` (`pycats/entities/fighter.py`), which
both match-start (`battle_screen` → `Player.reset_to_spawn`) and post-KO respawn route
through:

- Position — `rect.with_midbottom(self.spawn_point)`; `spawn_point` is midbottom at
  `PLAYER{1,2}_START_{X,Y}` (`pycats/config/render.py`), fixed points symmetric about
  screen centre near the thin-platform surface.
- `on_ground = False`; `vel.update(0, 0)` — **airborne**, drops from `START_Y`.
- `facing_right = self.original_facing_right` — P1 (left slot) `True`, P2 (right slot)
  `False` (`pycats/sim/runner.py` construction), i.e. inward.
- `jumps_remaining = self.max_jumps` — full jump count.
- `invincible_timer = 0`, `intangible = False` — no spawn protection.
- Control is live immediately — the fighter falls under player control from frame 1;
  pycats has **no** entrance / ready lockout state.

## Part A — re-sourced gap table (supersedes #1317's all-GUESSED Part A)

| # | Rule | Parity target (sourced) | Marker | pycats current state | Match |
|---|------|-------------------------|--------|----------------------|-------|
| A1 | **Spawn position** | Fixed per-slot start points, symmetric about centre, above the stage surface — `startingPoint = [[-50,50],[50,50],…]` (x = ±50 symmetric; y = 50, above `ground` y = 0) | **FOUND-by-engine** (`main.js`) | Fixed `PLAYER{1,2}_START_{X,Y}`, symmetric about centre near the thin-platform surface | ✓ |
| A2 | **Grounded vs airborne** | **Airborne** — spawns above the surface and drops in: `physicsObject.grounded = false`, `ENTRANCE.init` re-asserts `phys.grounded = false`, start y = 50 sits above `ground` y = 0 | **FOUND-by-engine** (`player.js`, `ENTRANCE.js`) — **reverses #1317's GUESSED "grounded"** | **Airborne** — `on_ground = False`; drops from `START_Y` | ✓ **(was ✗ in #1317)** |
| A3 | **Control at spawn** | **Not immediate** — a non-controllable entrance precedes control: a ~90-frame `startTimer` (1.5 s) freeze, then a 60-frame `ENTRANCE` state whose `main` only ticks a timer (no movement/jump/attack input) before `interrupt` hands off to `FALL`. SmashWiki: on-screen appearance is "a short animation that shows each character entering a stage before the beginning of a match" | **FOUND-by-engine** (`main.js`, `ENTRANCE.js`) + **FOUND** (SmashWiki) — **reverses #1317's GUESSED "full control from start"** | Full control from frame 1 — no entrance/lockout state | ✗ **(was ✓ in #1317)** |
| A4 | **Jump count at spawn** | Full — `doubleJumped = false`, `jumpsUsed = 0`; airborne, so the grounded jump is unusable until landing (midair jumps only, same basis as A2) | **FOUND-by-engine** (`player.js`) | Full — `jumps_remaining = max_jumps`; also airborne | ✓ (the #1317 "right-count-wrong-basis" caveat dissolves — the target is airborne too, so both have midair jumps only until landing) |
| A5 | **Match-start invulnerability** | **None** — `invincibleTimer = 0`, `intangibleTimer = 0` at construction and nothing sets a match-start invuln window (SmashWiki ties invincibility to *respawn*, not match start). Nuance: `ENTRANCE` is `canBeGrabbed : false`, so the fighter is *ungrabbable during the entrance* — a grab-immunity, not a damage-invulnerability | **FOUND-by-engine** (`player.js`, `ENTRANCE.js`) + **FOUND** (SmashWiki) | **None** — `invincible_timer = 0`, `intangible = False` | ✓ (damage-invuln match; pycats does not model the entrance ungrabbable window, but that rides on A3's missing entrance state) |
| A6 | **Facing** | **Inward** — `startingFace = [1,-1,1,-1]`: P1 faces +1 (right, toward centre from the left slot), P2 faces −1 (left, toward centre) | **FOUND-by-engine** (`main.js`) | Inward — P1 `facing_right=True`, P2 `facing_right=False`, restored from `original_facing_right` | ✓ |

## What changed vs #1317

#1317 marked **all six Part A rows GUESSED** and read the one divergence as **A2
(grounded target vs airborne pycats)**. Re-sourcing against the engine **reverses two
verdicts**:

- **A2 flips ✗ → ✓.** The parity target starts **airborne** (drops in from y = 50 above
  the y = 0 surface, `grounded = false`), not grounded. #1317's "grounded" was the
  convention guess; the engine contradicts it. pycats' airborne start now **matches** the
  target — it was never the divergence.
- **A3 flips ✓ → ✗.** The target has a **non-controllable entrance** (~90-frame start
  freeze + 60-frame `ENTRANCE` lockout) before control; pycats gives control from frame 1
  with no entrance state. This — not A2 — is **the one clear Part A divergence**.
- **A4's caveat dissolves.** #1317 flagged A4 "right count, wrong basis" *because* it
  believed the target was grounded. With the target airborne (A2), both sides have midair
  jumps only until landing — same basis, clean match.
- **A1, A5, A6 stay ✓**, now sourced (FOUND-by-engine ± SmashWiki) instead of GUESSED.
  A5 gains a nuance: the target's `ENTRANCE` is ungrabbable, a grab-immunity distinct from
  damage-invuln, which pycats doesn't model — but that rides on the missing A3 entrance
  state, not a separate divergence.

## Gap summary for the decision child (#1316 child 2)

- **The one Part A divergence is A3 (entrance control lockout), not A2.** pycats spawns
  the fighter directly into player-controlled airborne fall; the parity target holds a
  ~90 f start freeze then a 60 f ungrabbable `ENTRANCE` drop before control. Whether to
  model an entrance state is the open Part A design question — **not** grounded-vs-airborne
  (which matches).
- **A1/A2/A4/A6 match** and are now sourced; no action needed beyond recording them FOUND.
- **A5 damage-invuln matches** (neither has match-start invincibility); the only sub-gap is
  the entrance ungrabbable window, which is downstream of the A3 decision.
- **Tier:** every row is `[inference]` (Melee engine → PM), reinforced by the PM-CC
  finding that PM 3.6 ships **no** match-start spawn override, so Brawl/Melee entrance
  behaviour carries. A frame-exact PM-3.6 primary for the entrance timing (90 f + 60 f) was
  not located outside the engine; SmashWiki confirms the *existence* of the entrance
  animation but not its frame length.

## Out of scope (unchanged from the ticket)

- Post-KO respawn (Part B of #1317) — already sourced.
- Ruling any rule V1/post-V1/neither — #1316's ARC/decision child.
- DEV implementation of an entrance state.
- The general intangibility/invulnerability model (#527/#772).
