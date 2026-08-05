# TIL 2026-06-23 — DRAGONFRUIT

**Context:** Three pieces of work in one session: fixed the win-screen early-click
bug (#10), ran `/fruit-agent-orchestrate` to assign CHERRY and myself, and
investigated the "respawn doesn't reset facing" bug (#7) — which turned out to be
already fixed. The throughline was *reproduce-first*: two of the three tickets
hinged on what the reproduction actually showed rather than what the ticket said.

---

## 1. A bug that won't reproduce is a missing test, not a missing fix

**What happened:** #7 said "respawn keeps the prior facing." I tried to reproduce
it before touching anything — wrote a script that KO'd a player (driven out the
bottom blast zone through the real `Player.update()` loop) and ticked through the
respawn delay, on both the `legacy` and `statechart` backends. Facing reset
correctly every time. `git log -S original_facing_right` showed why: commit
**b480ae0** ("fix bug where respawned chars don't face their original
orientation", Jul 2025) already fixed it, and it's on `main`. #7 was filed
2026-06-22 during the `TODOS.md`→issues migration — a stale carryover of a TODO
that predated its own fix.

**What I learned:** The honest deliverable for an already-fixed ticket isn't a
fabricated fix and it isn't a silent close. b480ae0 shipped with **no dedicated
regression test** (`test_parity` only checks backend-to-backend byte-parity, so a
facing bug present in *both* backends would slip through). So the real gap was
test coverage. I wrote `tests/test_respawn_facing.py` — the reproduction the
assignment asked for, which simply happens to pass — and that became the thing
that closes the ticket.

**The rule:** When a reported bug doesn't reproduce on current `main`, find the
commit that fixed it, then ship the regression test that was missing — that is the
work, not a no-op close.

---

## 2. Surface the contradiction; don't decide it silently

**What happened:** My finding (already fixed) directly contradicted #7's premise
(bug present). Rather than just closing it, I stopped and asked the human whether
to close-with-test, leave-open, or hold for a repro I might have missed —
recommending close-with-test and giving the evidence. They chose close.

**What I learned:** Closing a GitHub issue is outward-facing. When what I find
contradicts how the ticket describes reality, that's a moment to surface, not to
proceed on my own read — the reporter may know a repro path (a char-select/skin
or round-edge scenario) my reproduction didn't cover.

**The rule:** If the evidence contradicts the ticket's premise, present the finding
and let the human confirm disposition before an outward-facing close.

---

## 3. Decrement-then-check cooldowns are off-by-one — seed N+1 for an N-frame window

**What happened:** #10's fix gates win-screen confirm input behind a ~2s grace
window. The existing `update()` does *decrement-then-check*:

```python
if self.p1_input_cooldown > 0:
    self.p1_input_cooldown -= 1
if self.p1_input_cooldown == 0:   # processes input on the SAME tick it hits 0
    ...
```

I first seeded the cooldown with `INITIAL_INPUT_GRACE_FRAMES` (= `2 * FPS` = 120).
My "mash for the whole window" test still confirmed on the final frame: seeding
`N` only blocks `N-1` ticks, because the tick that brings the counter to `0` also
runs the input check. Seeding `N + 1` blocks the full window.

**What I learned:** With a decrement-then-check counter, the value you seed is one
larger than the number of frames actually blocked. A boundary test (mash for the
*entire* window, assert nothing happens) is what exposes this — a "frame 0" test
alone would have passed and hidden the off-by-one.

**The rule:** For a decrement-then-check timer, seed `windowFrames + 1` to block a
full N-frame window, and prove it with a test that exercises the last frame of the
window, not just the first.

---

## 4. A green regression test isn't proven until you watch it fail

**What happened:** For #7, the new test passed immediately (the fix is already in).
Green-on-current proves nothing about whether the test actually *guards* the
behavior. So I temporarily reverted b480ae0's two lines in `_respawn`, re-ran:
all 4 cases failed. Restored the fix: all 4 passed again.

**What I learned:** A regression test written against already-fixed code can
trivially pass for the wrong reason (asserting on the wrong field, never reaching
the branch). The only way to know it bites is to break the thing it guards and see
red.

**The rule:** When adding a regression test for already-fixed behavior, revert the
fix once to confirm the test goes red, then restore — a test that's never been red
is unproven.

---

## 5. `pmtools close` exits 1 *after* succeeding — read the banner, not the code

**What happened:** Both `pmtools close #10` and `pmtools close #7` returned exit
code 1, with a trailing `getcwd: cannot access parent directories` error. The
close had actually fully succeeded: the output showed `CLOSE OK`, the commit
confirmed on `origin/main`, the issue CLOSED, and the worktree removed. The
non-zero exit is just the shell's working directory being deleted out from under
it (the tool tears down the worktree I was `cd`'d into).

**What I learned:** The exit code is a false negative here. The authoritative
signal is the `CLOSE OK issue=N … sha=…` banner and the `#N is CLOSED` line, not
`$?`. After a close, I `cd` back to the main checkout and post the closing comment
from there.

**The rule:** Treat `pmtools close`'s `CLOSE OK` banner (not its exit code) as the
success signal; the exit-1 + `getcwd` error is the expected cost of the tool
deleting the worktree you were standing in. (Authority: tracked under #29, the
ticket-closing-discipline tracker.)

---

## 6. The orchestration collision guard is necessary at the *file* level, not just the area level

**What happened:** Running `/fruit-agent-orchestrate` for CHERRY and me, the three
top tickets were all medium bugs: #7 (respawn facing), #8 (knockback), #9 (new
round leaves rects damaged). #7 and #9 share no area label, but both edit the
round/respawn reset path in `pycats/sim/`. The 5a-bis same-file guard held #9 so
two agents wouldn't land in the same file; #8 (combat physics, a different file)
paired cleanly with #7.

**What I learned:** "Different sub-theme" or "no shared area label" does not imply
"different file." The collision guard reads ticket bodies for file targets and
*refuses* to co-schedule plausible overlaps — it never tells two agents to
coordinate, because that would push a concurrency-safety decision onto runtime.

**The rule:** Each emitted assignment must be executable in isolation; when two
tickets plausibly touch the same file, hold one — don't ask the agents to
coordinate.

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/win_screen.py` | Seed input cooldowns with a `2*FPS + 1` grace window on win-screen entry (#10) |
| `tests/test_win_screen_input.py` | Frame-0 / full-window / after-window confirm-gating tests (#10) |
| `tests/test_respawn_facing.py` | Regression guard: respawn restores initial facing, both backends × both directions (#7) |

## Open threads

- `reset_game()` in `game.py` hardcodes `player1.facing_right = True` /
  `player2.facing_right = False` instead of using each player's
  `original_facing_right`. Correct today only because P1/P2 happen to match the
  literals — a latent smell if skins/sides ever become configurable (cf. #16
  character skin selection). Not filed; noting here.

## Related artifacts

- [TIL 2026-06-23 CHERRY](./today-i-learned-2026-06-23-cherry.md) — overlapping
  "committed ≠ merged+pushed" and "inspect before deleting" themes.
- Issues #10, #7, #30; collision-held #9; orchestration partner #8; close-tracker #29.
