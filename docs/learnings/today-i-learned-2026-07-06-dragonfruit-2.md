# TIL 2026-07-06 — DRAGONFRUIT (session 2)

**Context:** A triage session, not a build. I ran `/fruit-agent-orchestrate` for 7 agents,
then was handed an older ticket (#535, "create a canonical PM rules-by-category register") with
a twist: *is this still relevant?* Verifying that turned into cross-validating our newly-cloned
data sources locally, and the answer re-shaped what #535 should even be. No code shipped — the
output was a re-scoped ticket + a clarifying comment.

---

## 1. A "create X" ticket goes stale when X already exists — grep the target path before taking it

**What happened:** #535 (filed 2026-07-05) asked me to *create*
`docs/project-m-rules-by-category.md`. Before claiming, I ran `ls` on the target and
`git log` on it. The file **already existed** — built incrementally by #538 → #543 → #635 — and
was under a test gate (`tests/test_tuning_provenance.py`, #635, keeping each keyed row's `Status`
in sync with `combat/provenance.py`). The categorized register the ticket envisioned had also
materialized separately as `docs/pm-reference/` (19 files). The ticket's whole premise ("PM
evidence is scattered, we have no register") had quietly gone false in the day since filing.

**What I learned:** A ticket that says *create* is an assertion about the world at filing time,
and in a fast fleet that assertion decays. The single cheapest check — `ls`/`git log` on the
exact deliverable path — catches it before you burn a claim re-building something tested.

**The rule:** **Before claiming a "create `<path>`" ticket, `ls` the path and `git log` it — the
deliverable may already exist under a different ticket.** (Sharpens the existing "surface the
artifact, don't duplicate" principle in RULES → "Filing work".)

---

## 2. Know what a local clone actually *is* before you trust a value from it

**What happened:** The user asked me to cross-validate #535's citations against the sources we'd
"downloaded locally." Three clones exist. Probing each:

- `~/Documents/Study/JavaScript/meleelight` — a **Melee** reimplementation (schmooblidon fork,
  2018). Grepping it: Marth's smash moves cap at `chargeFrames === 60` (Melee), `airdodgeIntangible: 25`,
  `REBIRTHWAIT.js: invincibleTimer = 120`. All **Melee-tier** values.
- `~/Documents/Study/Rust/brawllib_rs` — rukai's **parser library**, source only. It reads `.pac`
  fighter files; without the game files it yields schema/enums, **not per-move numbers**.
- `~/Documents/Study/Rust/pm-data` — an **empty placeholder directory** (not even a git repo).

So of three "data sources," one is the wrong game, one is a parser with no data fed in, and one
is empty. What I *could* corroborate: the register's respawn "120f invincibility" row matched
meleelight's `invincibleTimer = 120` (a Melee-model value PM inherited). What I *couldn't*: any
PM-*specific* value — meleelight's charge cap is Melee's 60, not pycats/PM's 59 (#599), so it
confirms the divergence exists but not PM's number; the `1.3671` smash multiplier isn't in
meleelight at all. This is the same limit already recorded in
`docs/pm-reference/where-to-find-source-data.md` and the `rukaidata-engine-hardcoded-limit`
memory — a clone doesn't change which *tier* a value is.

**What I learned:** "We cloned it locally" is not "we can now verify it." A source's tier is a
property of what the source *is*, not of where it lives. A Melee reimpl gives Melee-tier
literals no matter how local it is; a parser gives nothing without inputs; an empty dir gives
nothing at all.

**The rule:** **Before citing a local clone, classify it — which game, source-or-data,
populated-or-empty — and label every lifted value by that tier; a local copy of a Melee source
still yields a Melee-tier value, never a PM confirmation.**

---

## 3. When a ticket's acceptance is only partly met, re-scope to the delta — don't fake-close, don't rebuild

**What happened:** #535's deliverable existed, but its acceptance ("≥ invuln + ledge + respawn
categories populated") was only **1/3 met**: the register's table was **Ledge-only** (confirmed
by `grep`). That put me between two wrong moves — *close it "done/superseded"* (false: invuln and
respawn rows genuinely aren't there) or *take it as written and "create the doc"* (duplicates a
tested file). I convened a strict yegor council; it converged cleanly: REQ (acceptance
partially-unmet → not closable-as-done), review (no fake-green, no busywork), microtasks (the
residual is ~20m of copy-in from already-verified findings, not a 90m build), bdd (the reporter
owns the trigger). The truthful third option is the **delta**: re-scope #535 from "create the
doc" to "backfill the invuln + respawn rows into the existing table," and post a comment saying
what happened and why. Which is what I did — body + title rewritten, comment pinned, ticket left
open and unclaimed.

**What I learned:** "Done" and "not started" aren't the only states a stale ticket can be in.
A partially-satisfied ticket has a real, smaller remainder, and both closing it and restarting
it misreport the world. Re-scoping to exactly the unmet slice is the only framing that's neither
a lie nor duplication.

**The rule:** **A ticket whose acceptance is partly met gets re-scoped to the unmet delta —
closing-as-done overstates, building-fresh duplicates; edit the body to the remainder and
comment the why.**

---

## 4. Two "ELI5 that" asks in a row means the recommendation isn't landing — re-explain, don't re-argue

**What happened:** After I gave the #535 verdict, the user asked `/eli5` — twice — and the second
time explicitly: "stop repeating 'the choice is yours,' I know that already." My first plain
rewrite still leaned on process framing (council, tiers, "your call"). The fix wasn't more
evidence or a different recommendation; it was stripping jargon and a reflexive hedge and stating
the shape plainly: *the document exists but is one-third filled, so the job is "finish it," not
"build it."* Once that landed, the go-ahead came immediately.

**What I learned:** A repeated request to simplify is a signal that the *packaging*, not the
*content*, is the blocker — and that a hedge I'd added for safety ("you decide") was read as
noise, not deference. The user had already granted me the opinion; restating who-decides was
friction.

**The rule:** **When asked to simplify twice, the content is fine and the framing isn't — cut
jargon and reflexive hedges and name the plain shape of the recommendation; don't re-litigate or
re-hedge.** (Mirrors BANANA's #584 "give the opinion, the gate is on the commit" — over-hedging
is the same miss as over-deferring.)

---

## What I did (no code shipped)

| Artifact | Change |
|---|---|
| #535 (title + body) | Re-scoped "create the register" → "backfill invuln + respawn rows (ledge done)"; ~90m → ~20m |
| #535 (comment) | Pinned what-happened/why: deliverable materialized via #538/#543/#635; acceptance 1/3 met |
| `/fruit-agent-orchestrate` | Assigned 7 agents (one ticket per `area:*` lane; busy agents got next-assignments, in-flight tickets excluded) |

## Open threads (not filed — candidate RULES codifications)

- Lesson 1 ("grep the target path before a create-ticket") and lesson 3 ("re-scope to the delta")
  both sharpen "Filing work" / "Suggest, don't act"; a one-line RULES pointer for each is a
  candidate if a human wants it codified. Flagged, not filed (no unprompted ticket creation).

## Related artifacts

- Issue #535 (re-scoped this session), #538 / #543 / #635 (built the register + its test gate)
- `docs/pm-reference/where-to-find-source-data.md`; memory `rukaidata-engine-hardcoded-limit`
- Sibling TIL today: [DRAGONFRUIT session 1](./today-i-learned-2026-07-06-dragonfruit.md)
