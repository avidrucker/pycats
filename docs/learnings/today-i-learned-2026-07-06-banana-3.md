# TIL 2026-07-06 — BANANA (session 3)

**Context:** A stage + queue-hygiene session. Researched Project M Final Destination
measurements (#659), built the flat "Starting Point" stage from them (#660), ran a
fleet orchestration pass, then reviewed + ICE-ranked + area-labelled all 94 open issues
(#679, via 8 parallel subagents), and closed with a RULES carve-out for human-authorized
direct pushes (#600).

---

## 1. When the primary source won't yield the number, cite the quotable anchor and label the rest ⚠ — don't fabricate to fill the gap

**What happened:** #659 asked for PM 3.6 Final Destination measurements (stage width,
ledge x, blast zones). SmashWiki and the PM-official site turned out to carry **only
qualitative descriptors** ("Large, Medium ceiling, Medium blast zones") — the real floats
live in the stage `.pac` (`Dead0N`/`Dead1N` + camera bones), reachable only by a datamining
dump. The one *quotable* numeric anchor was **Melee** FD, datamined into libmelee's source
(`BLASTZONES … (-246,246,188,-140)`, edge `±85.57`). PM restored Melee physics, so I used
Melee FD as the proportional basis but marked every derived pixel value **⚠ best-guess**,
not "sourced PM."

**What I learned:** the disciplined move when the primary is unquotable isn't to guess a
plausible number and book it `FOUND` — it's to (a) cite whatever *is* quotable, (b) name the
exact source of truth I couldn't reach (the `.pac`), and (c) label the derived values as
best-guess with the reasoning. That's the same failure #536/#581 hit from the other side
(booking Brawl numbers as PM `FOUND`).

**The rule:** **No quotable primary → cite the nearest quotable anchor, name the unreachable
source of truth, and label the derived value ⚠ best-guess — never launder a guess into a
sourced value.** (Authority: RULES → "Read the source before asserting" / #562 already owns this.)

---

## 2. A fixed camera can't honor faithful proportions *and* on-screen framing at once — surface the tension as a decision, don't pick a number

**What happened:** the crux of #659 was the unit→px mapping. At pycats' fighter scale
(`PX_PER_UNIT ≈ 5.4`) the FD **ground** fits the 960×540 screen (~924 px), but the **blast
zones** land ~848 px *beyond* each screen edge (and ~1015 up / ~756 down). pycats has a
fixed, non-scrolling camera and models KO at `BLAST_PADDING = 50 px` — ~17× tighter than a
faithful FD. There is no scale that satisfies both "ground fills the screen" and "faithful
blast distance."

**What I learned:** this isn't a value to source — it's a game-feel/camera-model tradeoff
with no canonical answer. The right output was to **surface it as a `decision:`** (with the
options costed) and build only the part that *was* buildable (the flat ground + ledges),
leaving `BLAST_PADDING` untouched. Trying to pick "the right" blast scale would have been
exactly the sourced-when-guessed trap.

**The rule:** **When faithfulness and a hard engine constraint (fixed camera) genuinely
conflict, escalate the tradeoff as a `decision:` and ship the unblocked remainder — don't
resolve it with a guessed number.** (Authority: RULES → "Changing values".)

---

## 3. Route through the seam that already exists before reaching for new config

**What happened:** #660 asked for a flat FD stage, and the human wanted **players** on it
while **demos/sims** stayed on the old Battlefield arena. I braced for a stage-selection
config layer — but `platforms` was **already a caller-provided argument** everywhere
(`BattleScreen.step(frame_input, platforms)`; `game.py` owns the live list; `sim/runner.py`
builds its own; the render tests build `platforms=[]`). So switching *only* `game.py`'s list
to the new named stage gave "players get FD, sims keep Battlefield" — with **zero** golden /
render-parity churn, because the sim path never changed.

**What I learned:** the "update the affected goldens intentionally" acceptance criterion
became *moot* once I found the existing injection point. The routing the human wanted fell
out of a seam that was already there; the named-stage abstraction was small precisely because
I didn't add a parallel config path.

**The rule:** **Before building new configuration, find the injection seam the code already
has — routing behaviour through an existing caller-provided argument often beats a new config
layer and avoids collateral churn.** (Candidate rule — not filed.)

---

## 4. Parse subagent output programmatically; never hand-retype it into a committed artifact

**What happened:** #679 (review + ICE + correct area for all 94 open issues) fanned out to
**8 parallel read-only subagents**, each returning a JSON array. I started transcribing their
results into scratchpad `b*.json` files by hand — and mis-typed #493's area call (wrote
`change:docs→tracker`; the agent actually said `keep:docs`). I caught it only because I then
wrote a Python extractor that pulled each subagent's JSON **straight from its `.output`
transcript** — canonical data — and the discrepancy showed up. The committed CSV + Artifact
used the extracted data, so the error never shipped.

**What I learned:** with N subagents feeding a committed artifact, hand-copying their output
is a silent-corruption surface. The `.output` transcript files are the source of truth; a
small parser (walk the JSONL, unescape the string leaves, `json.loads` the array) is both
faster and error-free. Extract, don't retype.

**The rule:** **When subagent output feeds a committed artifact, extract it programmatically
from the transcript files — hand-transcription is an unbounded error surface.** (Extends the
"verify subagent output" note in [TIL 2026-06-23 BANANA](./today-i-learned-2026-06-23-banana.md);
candidate for RULES.)

---

## 5. ICE rewards trivial-broad wins, so it floats human-decisions to the top — read the rank with the composition in mind

**What happened:** after the #679 refresh, the top of the ICE ranking was **#600** (20.0) and
**#491** (15.0) — a RULES-wording edit and a `decision:` ticket. ICE = I×C×E with Ease
multiplying, and "author a one-line human ruling" scores E=10 (trivial). So `decision`-type
tickets that need *the human*, not an agent, outrank real build work on the raw ICE sort.

**What I learned:** ICE is the **slot-3** key under bug → blocker → ICE, and human-routing is
a separate partition — so the composition catches this. But the raw single-column ICE sort
misleads if read alone. I flagged it back to the human (offer: score decisions separately)
rather than silently letting the board imply "do #491 first."

**The rule:** **ICE ranks by quick-win, not by who does the work — always read it through the
bug → blocker → ICE composition and the human-routing partition, and surface the caveat when
presenting a raw ICE board.** (Candidate observation — not filed.)

---

## 6. Verify a prose edit line-agnostically — a word-wrapped phrase defeats a single-line grep

**What happened:** closing #600 (the RULES carve-out), my acceptance check
`grep -l "explicitly authorizes a direct merge + push" CLAUDE.md RULES.md` matched **only
RULES.md**. The phrase *was* in CLAUDE.md — but word-wrapped across a line break
("explicitly\n  authorizes…"), so the single-line grep couldn't see it. A false negative on a
correct edit.

**What I learned:** prose in wrapped Markdown can't be verified with a naive line-oriented
grep; collapse newlines first (`tr '\n' ' ' | grep -o …`) or match a short unbroken fragment.
I nearly mis-read a done edit as incomplete.

**The rule:** **To confirm a phrase landed in wrapped prose, collapse newlines before grepping
(or match a short single-line fragment) — a line-oriented grep gives false negatives on
word-wrapped text.** (Candidate rule — not filed.)

---

## What landed

| Artifact | Change |
|---|---|
| `docs/research/2026-07-06-pm-final-destination-measurements.md` | FD measurements; Melee anchor + ⚠ best-guess PM px; blast-zone/camera decision surfaced (#659) |
| `pycats/entities/stages.py` + `config.py` + `game.py` | "Starting Point" flat FD stage; players-only, sims keep Battlefield (#660) |
| `stats/ice-scores.csv` | full-queue ICE refresh (95 rows; 65 ranked, 30 containers) + a review Artifact + 5 area-label fixes (#679) |
| `CLAUDE.md` + `RULES.md` | explicit-human-authorization carve-out for direct merge+push to `main` (#600) |

## Open threads

- **11 area-label suggestions from #679 flagged, not applied** — mostly "add a 2nd area to an
  epic"; left for a human ruling (marked ⚠ on the triage Artifact).
- **Score `decision:` tickets separately in ICE?** — raised to the human (lesson 5); no ticket yet.
- Lessons 3, 4, 6 have **no `RULES.md` home** — candidate rules, unfiled (authority path pending).

## Related artifacts

- Siblings: [TIL 2026-07-06 BANANA (s1)](./today-i-learned-2026-07-06-banana.md),
  [(s2)](./today-i-learned-2026-07-06-banana-2.md)
- Issues #659, #660, #679, #600, #685
