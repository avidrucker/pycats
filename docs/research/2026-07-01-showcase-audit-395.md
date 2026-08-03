# Research #395 — showcase demo audit: captions vs. actual behaviour

**Agent:** ELDERBERRY · **Date:** 2026-07-01 · **Parent:** #308 · Validates #325. **No production code — findings + recommended children.**

## Method
Ran `showcase` headless (`run_battle(demo_timeline(...))`, 480 frames, main @ `704f34b`) and inspected the per-frame snapshots (fighter state / on_ground / jumps_remaining / vel_y / percent / shield_hp / x) against each caption's frame window (from `demo_captions`). Harness: `scratchpad/audit_showcase.py` (not committed).

## Verdict: only **1 of 7** beats legibly demonstrates its caption.

| # | Caption | Window (dwell@start) | What actually happens | Class |
|---|---|---|---|---|
| 1 | approach | 10–60 | P1 walks x260→460, P2 x660→505 — they do approach. Minor: P1 walks off a platform edge and falls/re-lands (f25–45). | OK-ish |
| 2 | Jump & double-jump | 50–60 | **Double-jump is REAL** — airborne jump at f60 (`jumps 1→0`, on_ground-before=0, vel_y re-boosts −8→−12.5). But dwell freezes on **f50** (first jump); the double-jump is a brief blip at the window's tail. | (a) timing |
| 3 | Jabs — a fast disjoint poke | 90–95 | P1 is in `attack` at 90–95 but **airborne** (falling, og=0) — an aerial, not a grounded jab; it does **not** connect (P2 undamaged until f142). | (a)/(b) |
| 4 | Shield up | 110–139 | P1 **can't shield in the air** — it's in `attack`/`fall` until it lands, so it shields only **f136–139** (4 frames). P2 is `idle` at x476 the whole window and **never attacks**. P1's `shield_hp` only drains passively (49.8→49.4) then regens — **no attack ever contacts the shield.** "Hit while shielding" is entirely absent. | (a) major + (c) |
| 5 | Jab combo racks up damage & knockback | 141–245 | **Works.** 5 HITs (f142/166/186/211/241), P2 0→15%, knocked x476→870. | **OK ✓** |
| 6 | Shield roll-dodge (intangible) | 250–284 | Roll fires (`dodge` f268–280) — but in **open space**: Birky is far right (~700+), P1 rolls **left, away**. Not a dodge *past/through* an opponent. | (a) reposition |
| 7 | Edge-grab, then off the blast zone (KO) | 310–480 | P1 walks left, catches the ledge for **exactly 1 frame** (`ledge_hang` @f409), then held-`left` releases it → falls → **self-destruct KO** (f433, lives 3→2). The dwell freezes on **f310** (mid-walk), nowhere near the grab. The KO shown is the *showcased* fighter killing **itself**. | (a) major |

## Root causes (why this shipped green)

1. **The coverage test is a "feature-touched-somewhere" gate.** `tests/test_showcase_demo.py:36-43` asserts `{ATTACK,JUMP,HIT,KO}` events and `{shield,dodge,ledge_hang}` states each occur *anywhere* in the 480-frame run — never that they coincide with, and are legible during, the caption that narrates them. A lone airborne jump satisfies "double-jump"; a 1-frame `ledge_hang` satisfies "edge-grab"; a `HIT` (on P2) and a `shield` state (on P1) independently satisfy the set, so "hit while shielding" passes without any hit ever touching a shield.

2. **The #352 dwell freezes each caption's START frame, but several payoffs land at the END of the window.** Double-jump fires at f60 for a window starting f50; the ledge touch is at f409 for a window starting f310. So even correct mechanics are emphasized at the wrong instant.

3. **Combat is one-sided.** P1 never takes damage (percent stays 0 all run); P2 only ever gets hit, never attacks. So every "defensive" beat (shield-block, hit-while-shielding) has nothing to defend against.

4. **Shield/ledge inputs fight the fighter's state.** Holding `shield` while airborne is a no-op (beat 4); holding `left` through a ledge grabs then immediately releases it (beat 7). The script issues the input but not the *precondition* (grounded / stop-at-ledge) the mechanic needs.

## Recommendation — decompose into children of #308 (pending go-ahead)

1. **DEV: re-choreograph the showcase so each beat demonstrates its feature in its dwelled window.** Concretely: (2) dwell on the double-jump apex, not the first jump; (3) land a grounded jab that connects, or relabel; (4) ground P1 before shielding **and make P2 attack the raised shield** so a block is visible (two-sided combat); (6) position Birky so the roll passes through/past it; (7) stop the `left` input at the ledge so P1 **hangs** (held `ledge_hang`) and dwell there, and end on a real combat KO rather than a self-destruct. Requires making the fight two-sided (give Birky offence via a second input track / controller).
2. **DEV: strengthen the coverage test to bind each feature to its caption's frame window** — the regression guard so beats can't silently drift again. Assert: the JUMP satisfying "double-jump" is airborne **inside seg-2's window**; a HIT lands on P1's shield (shield_hp step-drop) **inside seg-4's window**; `ledge_hang` is held ≥N frames **inside seg-7's window**; the `dodge` x-range overlaps P2's. Pairs with #1 (lands red→green).
3. **(optional) enhancement to #352: dwell-on-payoff-frame** — let a segment freeze on a chosen frame (e.g. its window end / a `dwell_at`) instead of always its start, so a beat whose climax is late is emphasized correctly. Would simplify #1's beats 2 and 7.
4. **(optional) research/mechanics:** whether a deterministic fixed script can reliably land an attack **on a held shield** (the docstring notes jabs whiff on the shield bubble) — feeds beat 4. May reveal a real mechanics limitation to document or a move that does connect.

## Key code sites
- `pycats/sim/showcase.py` — the 7 `DemoSegment`s to re-choreograph.
- `tests/test_showcase_demo.py:36-43` — the "touched-somewhere" gate to strengthen.
- `pycats/sim/captions.py:51-59` — `caption_hold_frames` (freezes `frames[0]`; the dwell-on-payoff enhancement).
- `pycats/sim/runner.py` — `run_battle(controllers=…)` already supports a second controller → the seam for Birky's offence.

Refs #325 #308 #352 #356
