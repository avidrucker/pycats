# TIL 2026-06-24 — CHERRY

**Context:** A fleet session that started as a `/fruit-agent-orchestrate` triage and
turned into a run of combat/physics bug fixes — #6 (spot-dodge input order), #8
(knockback zeroed when moving), #9 (respawn leaves a fighter damaged) — plus a
cleanup-close of two already-merged-but-still-open tickets (#1, #5). Two of the
fixes traced back to the **same engine-ordering quirk**, which is the throughline
below.

---

## 1. A merged fix is not a closed ticket — and the orchestrator believes GitHub

**What happened:** `/fruit-agent-orchestrate` ranked #1 and #5 as the top medium
bugs. Both were already fixed and merged to `main` (`4240ec1`, `4c95b65`) with
green regression tests. They showed OPEN only because their commit subjects said
`(#1)`/`(#5)` but the **bodies lacked `Closes #N`** — GitHub auto-closes on the
keyword in the body, not a bare `(#N)` in the subject. The triage skill trusts
GitHub's open/closed state, so it cheerfully assigned dead work.

**What I learned:** This is the concrete mechanism behind the 2026-06-23 CHERRY
lesson "committed ≠ merged+pushed" — here it's "merged ≠ closed." The orchestrator
snapshot is only as truthful as the issue tracker, and the tracker is only as
truthful as the last commit's body. A quick `git log --grep` sweep across the open
queue caught two stale-open tickets in seconds.

**The rule:** **Put `Closes #N` in the commit _body_, never rely on `(#N)` in the
subject; and before trusting the open-issue queue, sweep git history for merged-
but-open tickets.** (Authority: already in `RULES.md` → "Closing work"; tracked by
the close-discipline epic #29.)

---

## 2. The one-frame FSM-label lag (the throughline)

**What happened:** #8 — knockback looked "100% cancelled" when the defender was
moving. The repro showed the post-hit horizontal velocity collapsing to exactly
`MOVE_SPEED`. Root cause: `game.py` runs `combat.process_hits` (→ `receive_hit`,
which sets `hurt_timer`) **after** `player.update` has already run that frame's
`engine.tick`. So `hurt_timer > 0` is true a full frame **before** the FSM label
flips to `"hurt"`. The input gate read the lagging **state label**
(`if self.state not in ("hurt", ...)`), so for that one frame `handle_move` still
ran and `step_horizontal` overwrote the knockback with walk speed.

**What I learned:** When a value is set by a system that runs *after* the state
machine ticks, the state *label* trails the underlying *timer* by one frame. Gating
behaviour on the label is a latent bug; gating on the timer (the source of truth)
is correct. The fix was `in_hitstun = hurt_timer > 0 or stun_timer > 0` added to
the gate.

**The rule:** **Gate behaviour on the source-of-truth timer, not the FSM label it
will (eventually) produce — the label lags any state set after `engine.tick`.**
(Authority: documented in-code at `player.py` `update()`, commit of #8.)

---

## 3. Parallel reset paths drift apart

**What happened:** #9 — a new life could start in the "damaged" state. `reset_game()`
(full-match reset) zeroes `hurt_timer`/`stun_timer`; `_respawn()` (per-life reset)
did **not**. Because `_ko()` early-returns from `update()`, those timers never tick
down during death — they freeze, and `_respawn()` only fixed the image colour. So
the respawned fighter re-entered the `hurt` FSM state and sat frozen (`in_hitstun`,
the very gate from lesson 2) for several frames. The fix made `_respawn()` clear the
same timers `reset_game()` does.

**What I learned:** Two functions that both "reset the player" are a standing
invariant: *they must clear the same fields.* The drift was wider than #9's hurt/stun
timers — `_respawn()` still skips `dodge_timer`/`attack_timer`/`invulnerable_timer`,
so a player KO'd mid-dodge carries those too. That's the same bug class, filed as
**#31** rather than scope-creeping the #9 fix.

**The rule:** **When two code paths reset the same object, treat their field lists
as one contract — diff them; a field cleared in one and not the other is a latent
bug.** (Authority: follow-up ticket #31.)

---

## 4. Golden snapshots legitimately move on a physics fix — but emergent assertions don't

**What happened:** Both #8 and #9 shifted `tests/golden/combat.json` (and #8 also
`full_match.json`): effective knockback resolved the scripted match faster
(717→690 frames), and a respawning P2's stale `hurt_timer` now reads 0. My first
instinct — "a golden diff means I broke something" — was wrong.

**What I learned:** `test_golden.py` carries two kinds of check: frozen snapshot
values (which *should* move when behaviour intentionally changes) and **emergent
assertions** that run *before* `check_or_update` — `"hurt"`/`"ko"` reached, P1 keeps
3 stocks, P2 drains `[3,2,1,0]`, `phase == "match_over"`. Those encode *scenario
validity* independent of exact numbers. The safe move: confirm the emergent
assertions are green, *then* regenerate with `PYCATS_UPDATE_GOLDENS=1`, then re-run
clean. Legacy↔statechart **parity** also stayed byte-identical throughout, because
the change lives in shared `player.py` (both backends inherit it).

**The rule:** **Regenerate goldens only after the emergent assertions pass — a value
diff is expected on a behaviour fix; an emergent-assertion failure is a real
regression. Never blind-accept a regenerated snapshot.**

---

## 5. The repro corrects the ticket's surface wording

**What happened:** #9's title says "rects show the **red** damaged state." My
`repros/repro_issue_9.py` (gitignored, exit-code verdict) showed the respawned P2's
image was its normal grey — `P2_COLOR == (90, 90, 90)` — *not* red. The real defect
was the **damaged state itself** (stale `hurt_timer`, frozen hitstun), which only
*renders* red on characters whose tint contrasts. Had I coded to the literal word
"red," I'd have hunted the renderer and missed the timer.

**What I learned:** A bug title describes a *symptom as one reporter saw it on one
character*. The reproduce-first discipline (already a pycats norm — see 2026-06-23
BANANA) isn't just about proving the bug; it's about letting ground truth overwrite
the assumptions baked into the ticket's wording.

**The rule:** **Reproduce to ground truth before trusting a ticket's surface
description — fix the state, not the adjective.**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/entities/player.py` | `_handle_dodge` accepts held-down for spot dodge (#6); `receive_hit` combines horizontal momentum + gate on hitstun timers (#8); `_respawn` clears hurt/stun timers (#9) |
| `tests/test_spot_dodge_input_order.py`, `test_knockback_momentum.py`, `test_respawn_clears_damaged_state.py` | New regression tests for #6/#8/#9 |
| `tests/golden/{combat,full_match}.json` | Regenerated for the #8/#9 behaviour fixes |
| Issues | Closed #1, #5 (cleanup), #6, #8, #9; filed #31 (reset-path drift) |

## Open threads

- **#31** — finish the reset-path drift audit (`dodge_timer`/`attack_timer`/
  `invulnerable_timer` in `_respawn`).
- **#7** (respawn doesn't reset facing) lives in the *same* `_respawn()` I just
  touched, which already sets `facing_right = original_facing_right` — so #7 is
  subtler than it reads and wants a careful look (possibly the same lag/ordering
  family as #8).
- Pre-existing noise unrelated to these fixes: active `print()` debug lines in the
  air-dodge path (`player.py` ~506) and legacy `tests/*` debug scripts that
  reference the removed `.fsm` attribute (the README already flags the latter).

## Related artifacts

- [TIL 2026-06-23 CHERRY](./today-i-learned-2026-06-23-cherry.md) — "committed ≠ merged+pushed" (lesson 1 is its sequel)
- [TIL 2026-06-23 BANANA](./today-i-learned-2026-06-23-banana.md) — reproduce-first sims, golden/parity oracle
- [TIL 2026-06-23 DRAGONFRUIT](./today-i-learned-2026-06-23-dragonfruit.md) — already notes `pmtools close` exits 1 after success (hit it again this session)
- Issues #6, #8, #9, #29, #31
