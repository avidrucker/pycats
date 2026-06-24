# Learnings (TIL)

Per-session "Today I Learned" retrospectives. Each row links a dated entry; newest
at the bottom (chronological).

| Doc | Date | Agent | Themes |
|---|---|---|---|
| [TIL 2026-06-23 BANANA](./today-i-learned-2026-06-23-banana.md) | 2026-06-23 | BANANA | Reproduce-first viewable sims; physics-layer (not statechart) collision fixes; golden/parity as oracle; Project M fidelity (#5 solid sides, #1 jostle); sequencing same-file tickets; verifying subagent output. |
| [TIL 2026-06-23 CHERRY](./today-i-learned-2026-06-23-cherry.md) | 2026-06-23 | CHERRY | Re-derive git state live (session-start snapshot is stale); inspect a doc before deleting it; "committed" ≠ "merged+pushed"; committed plan indexes vs issues-as-source-of-truth. |
| [TIL 2026-06-23 DRAGONFRUIT](./today-i-learned-2026-06-23-dragonfruit.md) | 2026-06-23 | DRAGONFRUIT | A non-reproducing bug is a missing regression test (#7); surface contradictions before an outward-facing close; decrement-then-check cooldowns are off-by-one, seed N+1 (#10); prove a guard by reverting the fix; `pmtools close` exits 1 after success (read the banner); file-level (not just area-level) collision guard in orchestration. |
| [TIL 2026-06-24 CHERRY](./today-i-learned-2026-06-24-cherry.md) | 2026-06-24 | CHERRY | Merged ≠ closed (`Closes #N` in body, sweep git before trusting the open queue); the one-frame FSM-label lag — gate on the timer not the lagging state label (#8); parallel reset paths must clear the same fields (#9, follow-up #31); goldens move on behaviour fixes but emergent assertions don't — regenerate only after they pass; reproduce to ground truth, fix the state not the adjective (#9 "red"). |
