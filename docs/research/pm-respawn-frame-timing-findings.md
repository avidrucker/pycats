# PM 3.6 post-KO respawn frame timing — DEAD / REBIRTH split (re-source)

> **Agent:** FIG · **Authored:** 2026-08-08 · **Ticket:** #1336

Re-sources the exact **DEAD** (off-screen blast) and **REBIRTH** (platform-descent) phase
frame durations for a normal (non-star) KO respawn, the one input #1334 (the child-3 DEV
slice) is gated on. #1327's disposition ruled the two-phase structure **V1** but blocked
hard-coding the frame split until it was re-sourced (`spawn-respawn-disposition.md`, B3 note):
the ~61 f / ~91 f figures #1317 carried were **engine-only Melee `[inference]`** with no
PM-3.6 primary.

**Outcome:** no PM-3.6 or Brawl **primary** for the DEAD/REBIRTH phase frame counts exists in
the accessible sources. After the documented search below, this doc records the meleelight
engine values as the **sourced-best `[inference]`**, with the platform-side numbers they share
independently corroborated for Brawl on SmashWiki. #1334 may hard-code the split as an
`[inference]`-tagged value citing this doc — it is a written basis, not a bare guess.

**Scope:** the DEAD and REBIRTH phase *durations* only. The platform's existence / location /
pass-through / 300 f vanish and the 120 f post-drop invincibility are already sourced (#1317
B5–B13) and are re-confirmed here only where they corroborate the timing. No ruling, no code,
no value change.

## Provenance tiers

| Marker | Meaning |
|---|---|
| **FOUND** | A primary/secondary quote (SmashWiki, PM/Brawl docs) pins the value. |
| **FOUND-by-engine** | A meleelight code line pins it. meleelight is a **Melee** reimplementation → Melee→PM is `[inference]`; and since PM is **Brawl**-based, it is a doubled Melee→Brawl→PM inference. |
| **`[inference]`** | Carried from an engine line with no PM/Brawl primary to confirm it. |

## The question

For a normal (non-star) KO in Project M 3.6, how many frames is the fighter:
1. **DEAD** — off-screen / gone after the blast, before the revival platform appears, and
2. **REBIRTH** — riding the platform down as it descends into place,

sourced to a PM-3.6 / Brawl primary rather than the Melee-engine inference?

## Inheritance chain (why a PM primary is a Brawl primary)

pycats needs a **PM 3.6** value. PM 3.6 is built on **Brawl**, and the PM 3.6 codeset applies
**no** override to normal-versus respawn timing — so PM inherits Brawl's respawn timing
unmodified, and a Brawl primary is the target.

**Project-M-CC 3.61 codeset (#664) — re-checked.** Grepping the codeset
(`~/Documents/Study/reference/Project-M-CC`) for `respawn|rebirth|revive|dead|blastzone`
returns exactly three respawn-related codes, none of which touch the normal-versus DEAD/REBIRTH
phase durations:

| Code | What it is | Touches DEAD/REBIRTH frames? |
|---|---|---|
| `All star VS: proper respawn 1.0d [wiiztec, Magus]` | All-Star-mode respawn fix | No — All-Star mode, not versus |
| `Respawn Camera Zoom Refocus [ds22]` | camera framing on respawn | No — camera only |
| `CPU falls from respawn plane when Turbo [Bero]` | Turbo-mode CPU behaviour | No — Turbo mode, CPU only |

So PM 3.6's normal-versus respawn timing **is** Brawl's, unchanged. (Same conclusion #1321
reached for match-start spawn: PM 3.6 ships no override there either.)

## Sources worked (documented search)

1. **meleelight** (`~/Documents/Study/JavaScript/meleelight/`, #616) — the shared DEAD/REBIRTH
   action states; the only source with an exact per-frame count (Melee):
   - `src/characters/shared/moves/DEADUP.js` (and `DEADDOWN` / `DEADLEFT` / `DEADRIGHT`, identical
     logic): `init` sets `timer = 0`; `main` runs `timer++` each frame; `interrupt` transitions
     to `REBIRTH` (if `stocks > 0`) once **`timer > 60`**. → DEAD ≈ **61 frames**.
   - `src/characters/shared/moves/REBIRTH.js`: `init` sets `timer = 1`, places the fighter at
     `respawnPoints[p].y + 135` with `cVel.y = -1.5`; `main` runs `timer += 1`; `interrupt`
     transitions to `REBIRTHWAIT` once **`timer > 90`**. → REBIRTH ≈ **90 frames**.
   - `src/characters/shared/moves/REBIRTHWAIT.js`: on the platform; `interrupt` sends the fighter
     to `FALL` once **`spawnWaitTime > 300`** (the 300 f auto-vanish), and every exit path sets
     **`invincibleTimer = 120`** (the post-drop invincibility). Full intangibility while waiting.
2. **SmashWiki** — [Revival platform](https://www.ssbwiki.com/Revival_platform),
   [Invincibility](https://www.ssbwiki.com/Invincibility): secondary corroboration for the
   platform-side numbers (below). Confirms the *existence* of the DEAD/descent phases and that
   KO type changes how fast the fighter reaches the platform, but gives **no** frame count for
   the DEAD or REBIRTH phase.
3. **Smashboards frame-data directories** (Complete Frame Data Directory; Brawl frame-data
   spreadsheets) — character move frame data only; no respawn/DEAD/REBIRTH phase durations.
4. **Project-M-CC** 3.61 codeset (#664) — no normal-versus respawn-timing override (table above).

## Findings

| Phase | Value (sourced-best) | Marker | Basis |
|---|---|---|---|
| **DEAD** (off-screen blast → platform appears) | **~61 f** | **FOUND-by-engine** → **`[inference]`** | meleelight `DEAD*.js` `interrupt` at `timer > 60`; no Brawl/PM primary |
| **REBIRTH** (descent on the platform) | **~90 f** | **FOUND-by-engine** → **`[inference]`** | meleelight `REBIRTH.js` `interrupt` at `timer > 90`; descent of 135 units at 1.5 u/f = 90 f (internally consistent); no Brawl/PM primary |
| **DEAD + REBIRTH total** | **~151 f (~2.5 s)** | derived `[inference]` | 61 + 90; matches #1317 B3's ~152 f / ~2.5 s |
| Platform auto-vanish | **300 f (~5 s)** | **FOUND** | SmashWiki "disappear by itself after 5 seconds"; meleelight `spawnWaitTime > 300` |
| Post-drop invincibility | **120 f (~2 s)** | **FOUND** | SmashWiki "invincibility (2 seconds, or 120 frames)"; meleelight `invincibleTimer = 120` |
| On-platform intangibility | full while waiting | **FOUND** | SmashWiki "intangible the entire time they are on the platform" |

### Confidence note — why the `[inference]` is trustworthy here despite no primary

The two engine numbers that **do** have an independent Brawl primary — the **300 f** auto-vanish
and the **120 f** post-drop invincibility — match SmashWiki's Brawl figures exactly. meleelight's
respawn model therefore tracks Brawl on every respawn value that is independently checkable. That
does not *prove* the DEAD (61 f) and REBIRTH (90 f) phase durations are identical between Melee
and Brawl — Melee and Brawl are distinct engines and this remains `[inference]` — but it raises
confidence that meleelight's respawn timing carries to the Brawl/PM target rather than diverging.
The REBIRTH figure has a second internal check: the platform sits 135 units above the respawn
point and descends at 1.5 units/frame, so 90 frames is exactly the descent-complete frame, not a
free parameter.

## Recommendation for #1334 (the DEV slice)

- Hard-code **DEAD = 61 f** and **REBIRTH = 90 f** (total ~151 f, ~2.5 s), replacing the single
  `RESPAWN_DELAY_FRAMES = 120 f` (2 s) freeze — this is the two-phase ~2.5 s the disposition
  ruled V1.
- Register the two new constants in `pycats/combat/provenance.py` as **`[inference]`** (a
  `GUESSED`-tier / inference marker citing this doc + meleelight), **not** `FOUND` and **not**
  `TUNED` — the value is engine-inferred, and the marker must say so.
- Keep the 300 f auto-vanish and 120 f invincibility as **FOUND** (they have a Brawl primary).
- If a frame-exact PM-3.6 capture ever surfaces, the two `[inference]` constants are the single
  place to re-source; the marker makes them findable.

## Gap / open item

- **No PM-3.6 or Brawl primary for the DEAD/REBIRTH phase frame counts was located.** The only
  route to a primary would be a frame-count from a PM-3.6 gameplay capture (a clip counted
  frame-by-frame) or a Brawl decomp exposing the `Dead`/`Rebirth` action-state lengths — neither
  is in the accessible source set. This is recorded as `[inference]`, not closed as FOUND.

## Out of scope (unchanged from the ticket)

- Star-KO variant duration (#1317 B4, ruled **neither**).
- Implementing the DEAD/REBIRTH state machine or the revival platform (#1334).
- Re-deciding any disposition (#1327).
- Match-start entrance timing (A3, ruled **neither**).

## Refs

Precondition for **#1334** (#1316 child-3, slice 1); basis **#1327**
(`docs/design/spawn-respawn-disposition.md`, B3 note). Prior findings **#1317** (B1–B3, B5–B13),
**#1321**; consolidated **#1310** / **#830**. Engine: meleelight (#616). PM codeset:
Project-M-CC (#664, no normal-versus override).
