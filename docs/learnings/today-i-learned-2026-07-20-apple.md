# TIL 2026-07-20 — APPLE

**Context:** I claimed #808 (add PM's sustained `run` state + `RUN_SPEED`, slice 3 of the #388 walk/dash/run epic) to *implement* it. I never wrote a line of `run` code. Chasing the one value the state needed — `RUN_SPEED` — turned into provenance archaeology that ended with the value blocked, the ticket parked, and two research tickets filed (#813 umbrella, #814 child). The lessons are all about that pivot: from courier to researcher, mid-claim.

---

## 1. "Sourced" is not "pinned to a primary" — and the source can be the wrong game

**What happened:** #808 needed a number for `RUN_SPEED`. The value was already "cited": PM Mario run = 1.55 u/f, carried by #373's findings doc, which attributes it to #119 (the Mario spec), which attributes it to #120 (the units-and-sources doc), which says "sourced from SmashWiki / rukaidata." Four hops, each pointing at the next, all looking respectable. I fetched the actual SmashWiki *Mario (PM)* page to pull a verbatim quote for the ADR-0003/#233 provenance row — and the attribute table is labeled **"Stats (Project+)"**. Verbatim: *"Dash speed: 1.5 – Initial dash, 1.55 – Run."* Project+, not Project M 3.6. pycats' canonical reference is **PM 3.6, explicitly not Project+/Melee**. The same softness infects `MOVE_SPEED = 6` (= round(1.1 × 5.4), PM Mario walk) — same table, same wrong game.

**What I learned:** A citation chain gives the *feeling* of provenance without the substance. Every hop I trusted was real, but none of them had ever put eyes on a PM 3.6 primary — #120 itself admits the movement values were "long-established community knowledge," never run through the derivation guard. The rot was at the bottom of the stack, invisible from any single doc. You only see it by walking the chain to its leaf and reading the source's own label.

**The rule:** **A value is only as sourced as its leaf citation — walk the chain to the primary and read that source's own version/label before you trust the number.** (RULES → "Changing values" + "cite primary, not inference"; the concrete follow-up is #813/#814.)

---

## 2. A blocking value-basis decision is a signal to go get the value, not to guess it

**What happened:** I first framed `RUN_SPEED` as a design fork and asked the user to pick (8px = sourced-but-same-as-dash, 9px = faster-but-unsourced, or defer). They picked none — instead: *"where did we get 1.55 from originally? We need explicit citations for every value."* That reframed the whole thing. The blocker wasn't a design preference; it was missing provenance. The right move wasn't to pick a number, it was to **stop implementing and file research** — an umbrella (#813) plus its first child (#814, the per-character survey), one at a time.

**What I learned:** When implementation stalls on "what number goes here," the instinct is to resolve it as a judgement call (pick the game-feel value) so the code can move. But if the number is supposed to be *sourced*, a judgement call is exactly the wrong tool — it launders a guess as a decision. The stall is the process working: it caught an un-pinned value before it shipped.

**The rule:** **If code is blocked on a value that's meant to be sourced, the fix is a research ticket that pins it, not a game-feel guess.** (RULES → "Changing a game value needs a basis"; "repro/spec-first.")

---

## 3. `pmtools file --role` adds no semantic label — `--dry-run` is how you catch it

**What happened:** I filed #813 with `pmtools file --role RESEARCH --area entities --label parent`, expecting the RESEARCH role to stamp a `research` label. The `--dry-run` output showed the exact `gh issue create` line it would run: `--label parent --label area:entities` — **no `research`**. I added `--label research` explicitly and re-ran.

**What I learned:** The role gates validation (WRITER/DEV/RESEARCH/PM are valid; ARCHITECT/DECISION/DESIGN are not) and `--area X` expands to `--label area:X`, but the role itself does not attach a semantic label. I'd been carrying the opposite assumption from a prior session. `--dry-run` prints the literal command, so the missing label is right there to see before anything is created.

**The rule:** **Always `pmtools file --dry-run` first and read the printed `gh` line; add the semantic label (`--label research`/`enhancement`) explicitly — the role won't.**

---

## 4. Release a claim on now-blocked work — don't park a dangling claim

**What happened:** Once `RUN_SPEED` was blocked on #813, #808 couldn't proceed. I'd written zero code in its worktree. I added the `blocked` label + an explanation comment, then `ExitWorktree keep` → `pmtools release 808`, which tore down the worktree and branch and left the issue OPEN. No re-claim cost later, because there was nothing to lose.

**What I learned:** A claim is a signal to the fleet that work is in flight. Holding one on a ticket that literally cannot advance is a false signal that also squats a worktree. When the blocker is external (another ticket's output) and nothing is committed, releasing is strictly cleaner than parking — the ticket goes back to OPEN+blocked, visible and grabbable the moment it unblocks.

**The rule:** **When a claimed ticket becomes blocked with no committed work, mark it `blocked` and release the claim — a parked claim on dead work is a lie to the fleet.** (RULES → "Closing/Claiming.")

---

## What landed

| Artifact | Change |
|---|---|
| #813 | Filed — umbrella: PM 3.6 grounded-movement speed provenance (parent) |
| #814 | Filed — child 1: do PM 3.6 walk/dash/run speeds vary per character? (roster survey) |
| #808 | Marked `blocked` on #813; claim released (no code written) |

## Open threads

- **Child 2 of #813** (re-pin Mario's walk/dash/run to a PM 3.6 primary — unblocks #808) is deferred, filed after #814's findings land, one-at-a-time.
- The Project+-vs-PM-3.6 gap may extend beyond speeds to other "community-knowledge" movement values (gravity/fall/jump) — flagged out-of-scope on #813, not yet ticketed.

## Related artifacts

- Issues #808, #813, #814
- `docs/research/2026-07-01-pm-walk-run-dash-mechanics.md` (#373), `docs/research-120-smash-units-and-sources.md` (#120)
