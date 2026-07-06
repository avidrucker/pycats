# TIL 2026-07-06 — CHERRY

**Context:** A shield/stun-mechanics session. Shipped a shield-recharge HUD bar
(#597), researched stun actionability vs Project M (#610), split the findings into
fixes + a study (#612/#613/#615), implemented the drop-through gate (#612), reframed
one fix to research after a wrong premise (#613), and wrote a mechanics FAQ (#602).
The through-line: how a parity claim gets over-stated, and how review catches it.

---

## 1. A verbatim primary quote is not confirmation if it's ambiguous about an observable

**What happened:** In research #610 I "confirmed" that shield-break dizzy cancels
the instant a fighter becomes airborne, quoting SmashWiki verbatim: *"any airborne
state induced upon a stunned character will cancel the stunned state immediately."*
I filed a bug (#613) to make pycats match. The user pushed back with one question —
*"can't you be both dizzy and falling?"* — and they were right. The word **"induced"**
almost certainly means *hit/knockback*, not passive falling; a fighter is dizzy **and**
airborne during the shield-break pop-up/juggle. I had a real quote and still drew the
wrong conclusion, because the quote was ambiguous about the exact frame-to-frame
behaviour I was claiming.

**What I learned:** The project's PM-parity rule ("cite primary, don't infer") kept me
disciplined about *having a source* but not about *over-reading it*. A quote pins wording;
it does not pin an **observable behaviour** unless it's unambiguous about that behaviour.
Pulling the quote felt like it discharged the burden of proof. It didn't.

**The rule:** **For a claim about what a state *does* frame-to-frame, a face-value wiki
sentence is weak evidence — confirm with a replay / frame check / the actual
state-machine data before writing "confirmed."** (Sharpens the existing PM-parity
cite-primary discipline; logged as error #81, correction posted on #610.)

---

## 2. Issue-review your own filings — self-authorship is not a quality exemption

**What happened:** I ran `/issue-review-skill` on #612 and #613, both of which I had
filed hours earlier. #612 scored a clean READY. But reviewing #613 against the code, I
caught that its acceptance criterion said "when a dizzy fighter goes airborne, send them
to **fall**" — when the most common way a dizzy fighter goes airborne is **being hit**,
which should land them in **hitstun**, not neutral falling. Building the ticket verbatim
would have shipped a new bug. (This was *before* the user's deeper challenge that
retired the premise entirely — but the review had already flagged the ticket as
NEEDS WORK.)

**What I learned:** The tickets I write get the least scrutiny precisely because I wrote
them — I trust my own recent framing. Running the same adversarial rubric I'd apply to
someone else's ticket surfaced a target-state error I'd been blind to while drafting.

**The rule:** **Before taking a ticket you filed yourself, review it as if a stranger
wrote it — a self-filed ticket earns no trust discount.**

---

## 3. Reframe a bug to research when its premise is unverified — don't code on an unconfirmed parity claim

**What happened:** Once the "dizzy cancels on airborne" premise cracked (#1), the right
move for #613 was **not** to fix the acceptance criteria and implement — it was to strip
the ticket back to a `research` question ("can a fighter be dizzy while airborne in PM,
and what actually cancels dizzy?"), drop the `bug`/`severity:low` labels, and confirm the
real behaviour before any code. Meanwhile #612 (the held-`down` drop-through gate) was
**unaffected** — it rested on independent quotes ("unable to act", drop-through needs the
standing state) — so it shipped.

**What I learned:** A shaky premise doesn't invalidate the whole thread; it invalidates
the part that depends on it. Isolating which fix leans on the unconfirmed claim (#613)
from the one that doesn't (#612) let me ship the safe half and de-risk the rest.

**The rule:** **When a fix's premise is unverified, downgrade that ticket to research
before writing code — and check which sibling tickets are independent enough to proceed.**

---

## 4. A declarative registry turns a parity feature into a one-record add

**What happened:** #597 (shield-recharge HUD bar) was a single `StatusSource` record in
the `STATUS_SOURCES` table (`render_battle.py`) — `active`/`ratio`/`readout`/colour, no
new branches in `timer_bar_specs`. #612 (drop-through gate) was one clause added to
`should_prevent_drop_through`. Both features were mostly *test*, not *code*.

**What I learned:** When a system is already a declarative table (the #522 registry) or a
single well-named predicate, adding faithful behaviour is a data edit, and the review load
shifts entirely onto the test. That's where the effort belonged anyway.

**The rule:** **In a declarative-registry codebase, spend the budget on the able-to-fail
test, not the one-line record.**

---

## 5. Scope the formatter to the files you're committing

**What happened:** Carried forward a prior lesson (error #76, last session): running
`ruff format pycats/` reformats *pre-existing drift* in files you never touched. This
session I ran `ruff format pycats/entities/fighter_physics.py tests/...` — only my two
files — and the commit stayed clean with no collateral reformat.

**What I learned:** The habit fix stuck because I named the exact command, not the intent.
"Format before committing" is ambiguous about scope; "format the files in the diff" isn't.

**The rule:** **`ruff format <the files you changed>`, never `ruff format pycats/` — a
whole-package format sweeps unrelated drift into your diff.**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/render_battle.py` | `RECHARGE` shield-regen `StatusSource` (#597) |
| `pycats/entities/fighter_physics.py` | drop-through gated off during hitstun/dizzy (#612) |
| `docs/research/stun-actionability-findings.md` | stun actionability vs PM (#610) |
| `docs/research/hitstun-vs-dizzy-findings.md` | hitstun≠dizzy comparison (#615) |
| `docs/mechanics-faq.md` | human-facing PM mechanics FAQ (#602) |
| #613 | reframed `bug` → `research` (premise unverified) |

## Open threads

- #613 — confirm real PM dizzy-while-airborne behaviour before any code.

## Related artifacts

- Prior CHERRY TIL: [2026-07-05 session 2](./today-i-learned-2026-07-05-cherry-2.md) (review-your-own-ticket, prove installs in a clean venv)
- Issues #597 #602 #610 #612 #613 #615 · error rows #76 #81
