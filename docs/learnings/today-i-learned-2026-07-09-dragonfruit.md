# TIL 2026-07-09 — DRAGONFRUIT

**Context:** A long session anchored on CPU difficulty (#702 research → #703 interpolation →
#704 decision → #705 decision-ledger + ADR-0007 → #708 sim-duration → #710 cpu-ai reference),
plus a stage-default revert (#715) and win-screen player colors (#726). The throughline was
*filing and convention discipline*: what not to file, how a new convention collides with old
ones, and grounding decisions in the docs that already exist.

---

## 1. The cheapest ticket is the one you don't file

**What happened:** Two "please add X" requests — show both players' stock counts on the sims,
then the same for the win screen — were **already implemented**. `sim/presenters.py ::
_draw_overlay` already draws `"{name}: {lives} stocks  {%}  [{state}]"`; the live battle HUD
already draws `"Lives: N"` (always on); the win screen already had `P1_UI_COLOR`/`P2_UI_COLOR`
confirmation boxes. I grepped the render path before filing and surfaced the finding instead of
filing a no-op ticket.

**What I learned:** A "make it do X" request is a *lead, not a fact* — the feature may already
exist under a different name (the game HUD calls stocks **"Lives"**). Filing first would have
produced a ticket that closes as "already done."

**The rule:** **Before filing a "make it do X" ticket, grep the impl/render path to confirm X
isn't already there — surface it, don't file it.** (Already RULES → *Filing work*: "verify a
user-reported symptom in the code before filing.")

---

## 2. A new convention silently reclassifies the tickets it touches

**What happened:** I built the append-only **Decision Log** ledger (#705 / ADR-0007). The ticket
spec said a `decision:` ticket "appends its ledger row before close, *alongside the existing
`gh issue close` + `pmtools release` no-code path*." But appending a row **is a committed
artifact** — so a decision ticket is no longer commit-less and must close via `Closes #N` +
`pmtools close`, not the no-code path. I caught the contradiction while wiring RULES and fixed the
clause + ADR to say so.

**What I learned:** Bolting an artifact-producing step onto a class of "no-code" tickets
*reclassifies them*. The convention's own framing was subtly self-contradictory, and only surfaced
when I tried to write the exact close instructions.

**The rule:** **When a new convention adds a committed artifact to a ticket type, re-derive its
close path — an artifact means it is no longer "no-code."** (Encoded in RULES → *Closing work*
via #705.)

---

## 3. Read the repo's storage conventions before proposing where something "should live"

**What happened:** Reviewing #704 ("where is this decision recorded?"), my first suggestion was to
invent a `docs/decisions/` folder. Running **grill-with-docs** sent me to read RULES +
`combat/provenance.py` + `docs/adr/` *first* — which showed the conventions already existed (a
ratified `decision:` ticket is itself the citation; values land as `TUNED` in `provenance.py`;
architecture goes in ADRs) and that `docs/decisions/` **did not exist**. The user's instinct ("we
already have conventions for this") was right; my invented location was off-convention.

**What I learned:** I proposed a home from memory instead of reading the repo's actual
decision-recording machinery. The docs answered the question before I did.

**The rule:** **Before proposing where something should live, read the existing storage
conventions (RULES / ADRs / provenance) — don't mint a location that may already exist under
another name.** (RULES → *Read the source before asserting*.)

---

## 4. A closed ticket's wrong words outlive the work

**What happened:** #726 asked to paint win-screen text "in each player's color." My own ticket
wording leaned "skin/palette color," but the screen already used `P1_UI_COLOR`/`P2_UI_COLOR` slot
accents (red/blue). I shipped with the **slot** colors, stated that interpretation in the commit +
closing comment, and the user confirmed — *then* asked me to **redline the closed ticket** so a
future agent re-reading it wouldn't be pulled toward skin/palette. I struck the misleading phrases
(`~~…~~`) and added a top correction note.

**What I learned:** Shipping the right thing isn't enough if the ticket still *says* the wrong
thing. A closed ticket is a durable artifact future agents read as authoritative.

**The rule:** **When you resolve an ambiguous ticket by choosing an interpretation, record it in
the commit AND redline the source ticket — the words outlive the work.**

---

## 5. An advertised range can lie about the behavioral range

**What happened:** #703. The CPU ladder advertised difficulty 1–9, but reading
`sim/controllers.py :: level_params` showed it snapped to 5 anchors (1/3/5/7/9) with ties rounding
**up** — so Lv2≡Lv3, Lv4≡Lv5, Lv6≡Lv7, Lv8≡Lv9. Only **5 of 9** levels were behaviorally distinct.
The table looked like a full ladder; the *resolver* was a step function. Fixed with piecewise-linear
interpolation (half-up via `Decimal`, so the one `.5` case `standoff` Lv2 = 42.5 pins to 43).

**What I learned:** "supports 1–9" was true at the API and false in behavior; the gap was visible
only by reading the resolver, not the anchor table.

**The rule:** **A parameter's advertised range can hide collapsed values — read the resolver, not
just the table, to see which inputs are actually distinct.**

---

## What landed

| Artifact | Change |
|---|---|
| `sim/controllers.py :: level_params` | Interpolate the CPU curve 1–9 so every level is distinct (#703) |
| `docs/decisions-ledger.md` + `docs/adr/0007-*` + RULES | Append-only Decision Log convention (#705) |
| `docs/pm-reference/cpu-ai.md` | Brawl/PM CPU behavior + parity-vs-custom map (#710) |
| `entities/stages.py` | Revert v1 player default to Battlefield — Starting Point felt cramped (#715) |
| `win_screen.py` | Paint stats columns + winner banner in each player's slot color (#726) |
| #704 (decision) | Approved near-miss + accidental-press + per-character CPU tuning as pycats-custom |

## Open threads

- #702 follow-up DEV chain (special-usage ramp → `spacing_accuracy` → near-miss → accidental-press)
  — filed one-at-a-time downstream, none filed yet; unblocked by the #704 ruling.
- #708 (sim-duration research) and #726's possible skin-color follow-up (deliberately not filed) —
  both available.
- Suggested DRY refactor: `sim.runner.build_stage` could delegate to `BATTLEFIELD.build()` (one
  builder for the same arena) — not filed.

## Related artifacts

- Prior session TIL: [2026-07-06 DRAGONFRUIT (session 3)](./today-i-learned-2026-07-06-dragonfruit-3.md)
- Issues: #702, #703, #704, #705, #708, #710, #715, #726
