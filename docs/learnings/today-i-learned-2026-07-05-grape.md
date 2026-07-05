# TIL 2026-07-05 — GRAPE

**Context:** A long research + governance session. Started as a spike on #520 (is pycats'
invulnerability/timer model composed correctly, and how does Project M do it?), which produced a
findings doc and follow-ups (#527 design, #535 register, #536 ledge audit). Reporter pushback on
my PM citations then turned into two primary-source research rounds, a two-layer correction
(#537), and — because I'd filed two tickets concurrently and swapped their numbers — an error-log
entry, a fix ticket (#542), and a ratified new RULES clause (#541). Closed by running
`guide-human-decision` to ratify #541 and this `write-til-doc`.

---

## 1. Don't rule "refuted" on external mechanics from a chain of inference

**What happened:** #520 asked whether Project M "composes" multiple intangibility sources. I
answered **"refuted — PM uses a single body-state, nothing composes,"** built by joining two
sourced facts ("one action-state enum" + "one debug colour") with my own reasoning. The reporter
pushed back twice — *"show me your citations"* — and each round the verdict eroded. A proper
primary-source pass (`brawllib_rs` `HurtBoxState` enum with `=` overwrite semantics, the PMDT 3.5
ledge blogpost via Wayback, OpenSA's `06050100` Body-Collision event) showed the truth was a
**two-layer** model: Layer 1 (dodge/ledge/getup) *is* a single mutually-exclusive body-state — my
instinct was right there — but Layer 2 (respawn/Star timed invincibility) is a **separate overlay
that composes**. So the hypothesis was *partly correct*, not refuted.

**What I learned:** The dangerous move wasn't being wrong — it was stating a **verdict at a
confidence the sources didn't support**, then propagating it into a committed doc and a downstream
design ticket (#527). Inference dressed as a citation is worse than an admitted gap. My interim
*over*-correction was the same failure in reverse: I grabbed a sloppy `fighter.h` fetch summary
and called Metal/Loupe "composing invuln flags" — both wrong (Metal = knockback resistance;
Loupe = off-screen chip *damage*), which a 30-second SmashWiki check refuted.

**The rule:** **For a PM/parity mechanics claim, pull a verbatim quote from a primary source and
label anything else as inference — never issue "refuted/confirmed" from reasoning alone.** Filed
as a RULES proposal in **#562**.

---

## 2. Concurrent `gh issue create` races the ticket numbers

**What happened:** I filed the register and the ledge-audit tickets in one shell line —
`gh issue create … & gh issue create … ; wait`. GitHub minted their numbers in **completion
order**, which didn't match my command order, so #535/#536 landed **swapped** from what I told the
reporter — and I'd already baked the wrong numbers into the committed #537 doc (4 refs) and two
comments. Cleanup: `pmtools error log` (id=51), a fix ticket (#542, closed), API-patching the two
comments, and re-verifying every number by lookup.

**What I learned:** Two independent root causes, not one: (A) I **stated numbers before verifying
them**, and (B) I **filed concurrently**, making the numbering a race. Fixing only one leaves the
other live. The tell was the reporter catching it during an `issue-review` — the swap is invisible
inside each ticket body (they reference each other by description), so it only surfaces in
cross-links.

**The rule:** **Verify a ticket's number/title from a real `gh` lookup before stating it, and
mint IDs/refs (`gh issue create`, `pmtools claim`) one at a time — never concurrently.** Ratified
and now live in `RULES.md` → "Filing work" (**#541**), with a `CLAUDE.md` echo. I filed #562 and
the TIL issue sequentially under the new rule.

---

## 3. Backticks inside a double-quoted `gh --body` execute as shell

**What happened:** `gh issue create --body "… \`RULES.md\` …"` failed with
`RULES.md: command not found` — the backticks in the double-quoted string triggered bash command
substitution, so the create aborted (logged as error id=55).

**What I learned:** Any prose destined for `--body` with Markdown code spans (backticks) can't ride
in a double-quoted argument. This bit me twice in one session before I internalised it.

**The rule:** **Write ticket/comment bodies to a file and use `--body-file` (or `--input -` for
`gh api`) — never inline backticked prose in a double-quoted `--body`.**

---

## 4. A self-proposed rule still goes through the human-decision gate

**What happened:** After the misnumbering, I *proposed* a fix rule (#541) but did **not** edit
`RULES.md` — governance changes need human sign-off (the #472 precedent, where an unapproved RULES
edit was itself the mistake). I ran `guide-human-decision` to split the proposal into its
independent clauses (A verify-before-state, B sequential-filing), presented each with a
recommendation + tradeoff, collected a per-clause ruling, and only then applied the ratified text
in the claimed worktree.

**What I learned:** The right shape for "I found a process gap" is **propose → ratify → apply**,
even when I'm confident and it's my own mistake being fixed. The decision ticket and its
implementation can share one worktree once ratified; the gate is the *ratification*, not a
separate ticket.

**The rule:** **Never edit `RULES.md` (or any shared governance doc) without an explicit human
ratification — propose it, walk the decision, then apply.** (Already in force; reinforced.)

---

## What landed

| Artifact | Change |
|---|---|
| `docs/research/2026-07-04-invuln-timer-state-model.md` | #520 findings + a 2026-07-05 two-layer Correction (#537) |
| `RULES.md` + `CLAUDE.md` | Ticket-filing hygiene clauses A + B (#541) |
| `docs/research/2026-07-04-invuln-timer-state-model.md` | Fixed 4 transposed #535/#536 refs (#542) |
| `pmtools` errors store | id=51 (misnumber), id=55 (bash backtick) |

## Open threads

- **#527** — two-layer invuln design; gated on ratification before DEV.
- **#535 / #536** — PM-rules register + ledge percent-scaling audit; #536 gates #535's ledge row;
  home-of-record pinned to `docs/research/2026-07-05-pm-ledge-intangibility-basis.md`.
- **#562** — the "cite primary, label inference" rule, awaiting ratification.

## Related artifacts

- Issues #520, #527, #535, #536, #537, #541, #542, #562
- Prior TIL: [TIL 2026-07-05 CHERRY](./today-i-learned-2026-07-05-cherry.md)
