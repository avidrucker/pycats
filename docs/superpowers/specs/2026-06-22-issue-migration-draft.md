# pycats issue-migration draft — REVIEW BEFORE CREATION

Source: `TODOS.md` (checked items excluded — already done) + `docs/research/BACKLOG.md`.
Each item is shaped as a yegor-bdd complaint. **Nothing is created until you approve this
list.** Edit/strike/relabel freely, then I run `gh issue create` per approved block.

**Label conventions used here:**
- `bug` + `severity:*` for defects (severity = impact of the defect).
- `enhancement` + `severity:*` for features, where severity is used as a **priority proxy**
  (high = core/blocking-feel, low = nice-to-have) so the solo queue ranks sensibly.
- `research` for open investigation threads.

## Summary table

| # | Proposed title | Type | Severity |
|---|---|---|---|
| 1 | Players landing on each other should push apart in X, not block | bug | medium |
| 2 | Character faces opposite the ground-dodge-roll direction | bug | low |
| 3 | Tail physics snaps wrong when cats turn left/right | bug | low |
| 4 | Tail physics ignores gravity and thick-platform collisions | bug | low |
| 5 | Jumping over a flush-adjacent character misbehaves | bug | medium |
| 6 | Add win/loss screen with end-of-match stats + play-again | enhancement | medium |
| 7 | Add shield-break stun ("dizzy") state that locks inputs | enhancement | medium |
| 8 | Players can jump into the sides of thick platforms | bug | medium |
| 9 | Down-hold + shield doesn't trigger spot dodge | bug | medium |
| 10 | Add prone status (only stand-up action allowed) | enhancement | low |
| 11 | Add ledge-hanging status | enhancement | medium |
| 12 | Air dodge cancels vertical momentum (confirm intended first) | bug | low |
| 13 | Respawn facing direction not reset to initial | bug | medium |
| 14 | Attack-knockback momentum zeroed when defender is moving | bug | medium |
| 15 | Add fullscreen display mode | enhancement | low |
| 16 | New round leaves player rects in red damaged state | bug | medium |
| 17 | Win screen accepts clicks too early (accidental restart) | bug | medium |
| 18 | Add character skin selection | enhancement | low |
| 19 | Apply working title "Cat Fight" to start screen | enhancement | low |
| 20 | Add screen manager (menu / select / match / win transitions) | enhancement | high |
| 21 | Add Esc-to-quit-match with yes/no confirmation | enhancement | medium |
| 22 | Add hold-B-to-menu circular progress indicator | enhancement | low |
| 23 | Add visual/auditory button-press feedback | enhancement | low |
| 24 | Research: Brawl/PM fighter-state mechanics (4 threads) | research | — |

---

## Issue bodies

### 1 — Players landing on each other should push apart in X, not block  · `bug` `severity:medium`
**Have:** when player A's center-X ≥ player B's center-X on landing, players block/remove on contact.
**Should:** players get pushed apart along X until both land; player-to-player collision is ignored on the Y axis.
**Repro:** have two players land on the same spot; observe blocking instead of separation.

### 2 — Character faces opposite the ground-dodge-roll direction · `bug` `severity:low`
**Have:** facing direction during/after a ground dodge roll does not invert relative to roll direction.
**Should:** character faces the opposite direction to the roll travel.
**Repro:** ground dodge roll left; observe facing.

### 3 — Tail physics snaps wrong when cats turn left/right · `bug` `severity:low`
**Have:** tail does not snap nicely on a left/right turn.
**Should:** tail snaps cleanly to the new facing.
**Repro:** rapidly turn left/right; watch the tail.

### 4 — Tail physics ignores gravity and thick-platform collisions · `bug` `severity:low`
**Have:** tail is unaffected by gravity and clips through thick platforms.
**Should:** tail responds to gravity and collides with thick platforms.

### 5 — Jumping over a flush-adjacent character misbehaves · `bug` `severity:medium`
**Have:** jumping over another character while starting flush against them causes a glitch (original note truncated — confirm exact symptom).
**Should:** the jump-over resolves cleanly.
**Repro:** stand flush against another character and jump over them.

### 6 — Add win/loss screen with end-of-match stats + play-again · `enhancement` `severity:medium`
**Have:** no end-of-match screen.
**Should:** a win/loss screen showing basic game stats with a single-press "play again" that returns to initial setup.

### 7 — Add shield-break stun ("dizzy") state that locks inputs · `enhancement` `severity:medium`
**Have:** no shield-break consequence.
**Should:** a stun state with a "dizzy" animation above the cat's head that disables all inputs for the stunned character while stunned.

### 8 — Players can jump into the sides of thick platforms · `bug` `severity:medium`
**Have:** players can enter the sides of thick platforms.
**Should:** side entry is blocked.
**Repro:** jump into the side face of a thick platform.

### 9 — Down-hold + shield doesn't trigger spot dodge · `bug` `severity:medium`
**Have:** holding down then pressing shield fails to trigger a spot dodge.
**Should:** it triggers a spot dodge — without regressing the default long-press shield/down → other-key behavior where dodge-end returns to shield automatically.
**Repro:** hold down, press shield.

### 10 — Add prone status (only stand-up allowed) · `enhancement` `severity:low`
**Should:** a prone state where the only self-initiated action available is stand-up.

### 11 — Add ledge-hanging status · `enhancement` `severity:medium`
**Should:** a ledge-hang state when grabbing a ledge.

### 12 — Air dodge cancels vertical momentum (confirm intended first) · `bug` `severity:low`
**Have:** air dodging zeroes vertical momentum.
**Should:** TBD — **research whether this is intended** before fixing.

### 13 — Respawn facing direction not reset to initial · `bug` `severity:medium`
**Have:** character respawn does not reset facing to the correct initial direction.
**Should:** respawn resets facing to the initial per-player direction.

### 14 — Attack-knockback momentum zeroed when defender is moving · `bug` `severity:medium`
**Have:** knockback momentum appears 100% cancelled when the defender is moving left/right, but not when stationary.
**Should:** both the defender's existing momentum and the knockback are factored in, in both cases.

### 15 — Add fullscreen display mode · `enhancement` `severity:low`
**Should:** a fullscreen display option.

### 16 — New round leaves player rects in red damaged state · `bug` `severity:medium`
**Have:** at new-round start, player rects can still show the red damaged state.
**Should:** rects reset to normal at round start.

### 17 — Win screen accepts clicks too early (accidental restart) · `bug` `severity:medium`
**Have:** the win screen responds to clicks immediately, causing accidental round starts.
**Should:** ignore clicks for ~2s initially, or require a specific Space-key press to proceed.

### 18 — Add character skin selection · `enhancement` `severity:low`
**Should:** skin changing (white ghost, orange tabby, gray tabby, black void, orange/black tiger, bengal white/black tiger).

### 19 — Apply working title "Cat Fight" to start screen · `enhancement` `severity:low`
**Should:** the start screen shows the working title "Cat Fight".

### 20 — Add screen manager (menu / select / match / win transitions) · `enhancement` `severity:high`
**Have:** screens are ad hoc.
**Should:** a dedicated screen manager handling the current screen and transitions (character select, win screen, match, main menu). *(Likely unblocks #6, #17, #19, #21, #23.)*

### 21 — Add Esc-to-quit-match with yes/no confirmation · `enhancement` `severity:medium`
**Should:** Esc quits the match back to main menu, gated by a yes/no confirmation.

### 22 — Add hold-B-to-menu circular progress indicator · `enhancement` `severity:low`
**Should:** an upper-left circular indicator that fills to show how long B must be held to return to the main menu.

### 23 — Add visual/auditory button-press feedback · `enhancement` `severity:low`
**Should:** button highlights and sounds on press.

### 24 — Research: Brawl/PM fighter-state mechanics · `research`
Four open threads from `docs/research/BACKLOG.md` (could be one issue with a checklist, or four):
- **(a)** authoritative state-to-state transition graph — published, or extractable from doldecomp/brawl / BrawlHeaders?
- **(b)** correct shield-pushback formulas for defender AND attacker (prior formula was refuted) — in the decompilation or only datamined?
- **(c)** how Project M / Project+ deviates from base Brawl (action states, shield, powershield/parry)?
- **(d)** concrete collision-resolution algorithm (order shield/hitbox/hurtbox/grab are tested per frame) — exposed yet?

---

## ✅ FINAL PLAN (decisions applied 2026-06-22)

Supersedes the table above. **24 issues created now**; the 4 Brawl research threads are deferred (lazy, one-at-a-time under an umbrella).

**Bugs — `bug` + `severity:*` (10):** #1 push-apart (med), #2 dodge-roll facing (low), #3 tail snap (low), #4 tail gravity/collision (low), #8 jump-into-platform-sides (med), #9 down+shield spot-dodge (med), #13 respawn facing reset (med), #14 knockback momentum zeroed (med), #16 new-round red state (med), #17 win-screen clicks-too-early (med; depends on win-screen #6).

**Features — `enhancement`, NO severity (11):** #6 win screen, #7 shield-break dizzy, #10 prone, #11 ledge-hang, #15 fullscreen, #18 skins, #19 title, **#20 screen manager (spine)**, #21 esc-to-menu, #22 hold-B indicator, #23 button feedback. #20's body lists candidate dependents (#6/#21/#23) to confirm at implementation; hard `blocked` labels deferred (avoid asserting unverified code deps + over-serializing fleet work).

**Research — `research` (3 now):**
- **#5 → research:** reproduce & spec the jump-over-flush-adjacent-character bug, *then* file the DEV bug. (Was an under-specified bug.)
- **#12 → research:** determine whether air-dodge cancelling vertical momentum is intended; then file a bug or close `wontfix`.
- **Umbrella research tracker — "Brawl/PM fighter-state mechanics"** listing the 4 threads (a: state-graph, b: shield formulas, c: PM deviations, d: collision algorithm). Children filed **one at a time**, each finished before the next (lazy decomposition).

**TODOS.md:** deleted after creation (preserved in git history). **BACKLOG.md:** its 4 threads move into the umbrella issue body; replace BACKLOG.md's thread list with a pointer to the umbrella issue (keep `brawl-projectm-fighter-states.md` as reference).

**Conventions encoded** (so this isn't a one-off): `RULES.md`, `CLAUDE.md`, `scripts/create-standard-labels.sh` header, and the skill's `orchestrate-config.md`.

## ~~Open questions for you~~ (resolved — see Final Plan)
1. **Severity-as-priority on features** — OK, or keep features severity-less (they'd rank as ⚪ untriaged)?
2. **Research item** — one issue with a 4-item checklist, or four separate `research` issues?
3. **Item #5** — the original TODO line was truncated ("jumping over other characters while starting flush against cause"); confirm the intended symptom.
4. **TODOS.md after migration** — annotate each line with its new `#N`, or move migrated items to a "migrated to issues" section?
