# TIL 2026-07-06 — BANANA (session 2)

**Context:** A "process about process" session — hardened a tautological test (#627), then
built and reviewed a chain of tickets studying *decision/value churn*: the churn measurement
(#631 umbrella / #632 Child A), a parent/child label scheme + backfill (#641/#644), the
mitigation thread (#651 Child B), and an escalation-rubric research doc (#653). Lots of
file → review → edit → re-review loops on my own tickets.

---

## 1. Churn's cost is in the tickets, not the git diffs

**What happened:** #632 asked "how many issues/tokens to settle one value?" My first instinct
was to count how often each config constant's *value* changed in git. That ranking put
`DODGE_SPEED` (28→22→14) and `GROUND_FRICTION` (0.2→0.9→0.5) on top. But the value that
actually cost the most — `SMASH_CHARGE_*` — changed in `config.py` **once** (60→59), yet
burned **5 tickets** (#426/#581/#595/#599/#627) because #581 booked the base-game/Brawl number
as `FOUND`, then #595→#599 had to reverse it.

**What I learned:** value-revision count and decision/effort cost rank *oppositely*. The
cheap-to-revise values (ad-hoc 2025 game-feel flips, no tickets) churned most by diff count
and cost nothing; the expensive one changed once but dragged a 5-ticket arc. Counting diffs
would have pointed the mitigation work at exactly the wrong constants.

**The rule:** **Measure decision churn by tickets-to-settle, not by how many times the value changed.**

---

## 2. A naive `git -G` count over-reports churn — whole-file commits are the noise

**What happened:** `git log -G"^NAME ="` over `config.py` flagged **27** constants as ≥2-touch
"churned." After extracting the actual value at each commit and compressing consecutive-equal
values, only **8** were real. The inflation came from two whole-file commits that touched every
assignment line's whitespace/comment without changing a value: the ruff reformat (`a0304b5`,
#505) and the Axis-A annotation pass (`6793673`, #408).

**What I learned:** `-G<regex>` matches any diff that *touches* a matching line, so a reformat
or a comment edit counts as a "change." For value churn you have to read the value at each
commit and drop the no-ops.

**The rule:** **When mining value history, compress on the value itself — a line-touch is not a value change.** (Method recorded in `docs/research/decision-churn-findings.md`.)

---

## 3. Verify the data substrate exists before scoping a sweep off it

**What happened:** I filed #644 to backfill `parent`/`child` labels "driven by their native
parent/sub-issue links." When I went to run it, of **98 open issues exactly 0** had a usable
native sub-issue link (one pointed at a *closed* parent). The repo tracks trees **textually**
("Child A of #631", "split from #21"), not via GitHub's native feature — so the ticket's stated
method (which I wrote) would have tagged nothing.

**What I learned:** I scoped a sweep off a data source I hadn't confirmed had data. The right
move was to stop, surface the mismatch, and switch to a textual/semantic sweep with the mapping
approved first — not to silently produce a vacuous result.

**The rule:** **Confirm the substrate a sweep reads actually contains data before you scope the sweep on it; when the premise breaks, surface it, don't grind out an empty answer.** (Recorded in #644's close comment.)

---

## 4. Same-size config edits defeat `.pyc` invalidation in revert-checks

**What happened (#627):** doing the able-to-fail check, I edited `config.py`
`SMASH_CHARGE_FRAMES = 59` → `60` in place, ran one test (it reddened, good), edited back to
`59`, then ran the full suite — which showed **6 false failures**. Runtime was reading `60`
from a stale `config.pyc`: `"59"` and `"60"` are the same byte size, and both edits landed
within one second, so CPython's (mtime, size) `.pyc` invalidation never fired.

**What I learned:** this is a recurring class (memory `mutation-check-stale-pyc`, error #86).
An in-place same-size numeric edit is the worst case for `.pyc` staleness.

**The rule:** **For a revert-check, monkeypatch the constant or clear `__pycache__` — don't rely on an in-place same-size config edit to invalidate bytecode.**

---

## 5. Before proposing new machinery, survey what the repo already owns

**What happened (#653):** asked to research an escalation rubric, I nearly started from a blank
slate. Reading first, the repo already had **three** of the four pieces: ICE (`pmtools ice`,
spec #199) for priority, RULES "Changing values" for the evidence gate, and the yegor-personas
authority ladder for who-decides. The one genuinely missing axis was **reversibility /
cost-if-wrong** — which is exactly the axis #632's churn turned on. So the rubric became a
two-stage *composition* of existing tools plus one new gate, not a new system.

**What I learned:** the gap is usually one missing dimension, not a greenfield. Surveying prior
art first turned a "design a rubric" task into "add reversibility and wire up what exists" —
lower adoption cost, no new dependency.

**The rule:** **Survey the tools the repo already owns before designing a new one; the real gap is usually a single missing axis.** (Recorded in `docs/research/escalation-rubric-findings.md`.)

---

## What landed

| Artifact | Change |
|---|---|
| `tests/test_status_timer_bar.py` | pinned the charge-bar readout to a concrete literal, killing a tautological assertion (#627) |
| `docs/research/decision-churn-findings.md` | churn measurement — 8/60 constants revised; tickets-to-settle ≠ diff count (#632) |
| `docs/research/escalation-rubric-findings.md` | two-stage escalation rubric composing ICE + RULES + personas + a new reversibility gate (#653) |
| `RULES.md` | `parent`/`child` relationship labels + when-to-apply note (#641) |
| GitHub labels + 15 open issues | created `parent`/`child`; backfilled the open tree (10 parent, 5 child) (#644) |

## Open threads

- The escalation rubric's downstream **WRITER draft** (a one-page working rubric) — scoped in
  #653 §7, deliberately not filed (one-at-a-time).
- #651 (Child B, churn guardrails) is READY and unclaimed.
- Umbrella #631 closes via its own `gh issue close` + `pmtools release` once #651 lands.
- "Verify the substrate before a sweep" (lesson 3) has no `RULES.md` home yet — candidate rule,
  not filed.

## Related artifacts

- Sibling: [TIL 2026-07-06 BANANA (session 1)](./today-i-learned-2026-07-06-banana.md)
- Memories: `mutation-check-stale-pyc`, `python-c-fstring-escaping-footgun` (errors #86/#93/#99)
- Issues #627, #631, #632, #641, #644, #651, #653
