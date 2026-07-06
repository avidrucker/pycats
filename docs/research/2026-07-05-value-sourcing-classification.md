# Classifying "research + update a value" work — DEV, ARCHITECT, research, or a split?

**Ticket:** #530 (research; from #528). **Role:** RESEARCH. **Date:** 2026-07-05. **Agent:** DRAGONFRUIT.
**Method:** a `yegor-personas` council over the standing `yegor-*` skills + pycats' own RULES → "Changing values".

---

## The ruling (TL;DR)

**"Source + pin a value" is not one label — it is a *pipeline*, and the label is decided by one question:
does a faithful, sourceable Project M value already exist, and is it already written down?**

A value-sourcing ticket bundles two acts with two different owners:
- **(a) finding / deciding the number** — a *research* act (look it up) or a *design* act (invent it), and
- **(b) swapping the constant** — a mechanical *courier/DEV* edit.

They are two deliverables with two different "done" definitions (a cited number vs a green proving test),
so by default they are **two tickets**, not one. The exception is when act (a) is *already done* — the number
is already sourced and cited in an in-repo `docs/research/*` finding — in which case only the DEV remains.

### Decision tree — route a "source + pin value X" request

```
Is value X already sourced + cited in an in-repo docs/research/* finding?
├─ YES  → single DEV (enhancement, ≤30m):
│         swap the constant, add the FOUND provenance entry (combat/provenance.py, ADR-0003),
│         cite the finding in the commit + the constant's comment, land a proving test.
│         Basis (1). The finding IS the basis; no new research ticket.
│
└─ NO → is a faithful PM value *sourceable* (PM/Melee has a real number that maps)?
        ├─ YES → research → DEV split:
        │        • research ticket: source + cite X into a docs/research/* finding  (deliverable = the finding)
        │        • DEV child (blocked-by the research): pin it + FOUND provenance + proving test
        │
        └─ NO (PM has no faithful number, or it doesn't map) → decision → DEV split:
                 • decision ticket (human designer picks the surrogate → basis (2), TUNED);
                   label `decision` (+ `humans-only`/`human-decision-required` — a human chooses)
                 • DEV child (blocked-by the decision): apply the ratified choice + TUNED provenance + proving test
                 Never a bare DEV that invents a number — game-feel alone is declined wont-do / vapid (#489).
```

**"ARCHITECT" is a real role here, but pycats has no `architect` label** — and it should not invent one.
The architect *role* maps onto pycats' existing labels: **sourcing the requirement → `research`**; **inventing a
surrogate → `decision` (+ human)**. The Yegor architect "decides *how*; the *what* is owned by the requirements"
(`yegor-architect`) — and for pycats the *what* (the canonical number) is the **PM 3.6 parity spec**, so it is a
requirement to be *sourced or ratified*, never an ARC design deliverable of its own.

---

## The council (`yegor-personas`)

**Fork:** should "research a canonical value, then update the constant" be labeled **DEV**, **ARCHITECT**,
**research**, or a **split** — and specifically, should #528's proposed "DEV to source/pin fall values" stay DEV?

**Standing (4 seated + REQ):** `architect`, `bdd`, `microtasks`, `tickets`, and the **REQ** role-voice
(requirements = PM 3.6 parity). `pm` routes; not seated.

```
REQ (requirements) — The canonical number IS the spec (PM 3.6 parity), not a design choice.
  BECAUSE: pycats' north star is PM parity; a faithful value is a requirement to be *sourced*, and where PM
           has no faithful number the spec is *silent* — which is itself a finding, escalated to the designer.
  STANDING: rung 1 — requirements are the ultimate boss; they settle the "what."

architect — Never mix modes: sourcing/deciding the number (design/what) and swapping it (courier/execute) are
            two sessions, so two tickets. But the *what* is the requirement's, not the architect's own artifact.
  BECAUSE: "The architect decides *how*; the *what* is owned by the requirements" + "never mix modes in one
           session" (yegor-architect). A value looked-up is research; a value invented is a designer decision.
  STANDING: tie-breaker on the residual "one ticket or two" — and it says split.

microtasks — A finding and a code-swap are two commit-worthy deliverables with different done-definitions → split,
             UNLESS the finding already exists (then the swap is one ≤30m DEV citing it — splitting further is
             salami-slicing).
  BECAUSE: one-concern / one-deliverable per ticket; "research + a one-line change" is two deliverables.
  STANDING: objective (≤60m budget + one-deliverable) — decides the sizing.

bdd — "Nalio falls on an unsourced default; should fall on the sourced PM value" is a well-formed complaint
       (have/should) — but it can't be *worked* until the basis exists, and the fix needs a proving test.
  BECAUSE: work is a complaint best expressed as a failing test; "no code change without a proving test" (yegor-bdd);
           RULES → "Changing values": a value change must cite its basis. The finding produces the basis; the
           correction is the bug-shaped DEV.
  STANDING: advisory — shapes the DEV child (proving test), doesn't set the top label.

tickets — Whatever the routing, the *choice of a surrogate* is a decision that must be written down as a ticket
          artifact, not carried in a commit or someone's head.
  BECAUSE: "if it isn't in the tracker, it didn't happen"; picking a surrogate is recorded as a decision ticket.
  STANDING: advisory — governs *where* the decision lives (the decision ticket / provenance entry).
```

### Convergence (authority ladder)

1. **Requirements settle it (rung 1).** PM 3.6 parity is the spec. A faithful PM value is a *requirement to be
   sourced* → **research**; the mechanical apply → **DEV**. Where PM has **no** faithful value, the spec is silent
   → that silence is a finding → the human **designer decides** (a `decision`), never the agent. This already
   splits the work and names who owns each half.
2. **Objective measure confirms the sizing (rung 3).** `microtasks`: finding + swap = two deliverables → two
   tickets, unless the finding already exists in `docs/research/*` (then a single DEV that cites it).
3. **Architect breaks the residual technical tie (rung 5).** "Never mix modes" → don't fuse the source/decide
   step with the execute step in one ticket.

**No dissent** — all four readings + REQ converge on **split, routed by whether a faithful value already exists**.
The reporter owns the final label on any specific ticket (rung 4, `yegor-bdd`); this ruling is the recommended
routing, not an override.

**This ruling is not novel** — it *re-derives* what pycats' RULES → "Changing values" already encodes:
> "**Picking a surrogate is a decision, not a DEV edit.** When no faithful value exists, *choosing* one is a
> `decision:` ticket (e.g. **#491**) … Record which basis applies … as **FOUND** (sourced) or **TUNED**
> (designer-chosen)."

The council's contribution is to make the *research vs decision vs DEV* routing explicit and to bind it to the
`yegor-*` authorities, so value-sourcing tickets get labeled consistently.

---

## Questions answered

**Q1 — Architect vs courier.** *Finding/deciding* the value is **not courier work** and **not an ARC deliverable
of its own** — it is either **research** (the value is looked up → a requirement is *sourced*) or a **designer
decision** (the value is invented → a requirement is *ratified*). *Swapping the constant* is **courier/DEV**
execution. The line for "research + one-line change": the two are separate modes and must not share a session
(`yegor-architect`: "never mix modes"). Cite: `yegor-architect` (modes; "the *what* is owned by the requirements").

**Q2 — Bug vs feature vs decision.** An unsourced/wrong value is a legitimate **complaint** (have/should) — so the
*apply* step is a **bug-shaped DEV with a proving test** (`yegor-bdd`: "no code change without a proving test"; RULES:
"a value change must cite its basis"). But the complaint is **not actionable until the basis exists**: gathering it
is **research**, and inventing it (no faithful source) is a **`decision`** (RULES #489/#491: game-feel alone →
`wont-do`/`vapid`). Cite: `yegor-bdd`, `yegor-tickets`, RULES → "Changing values".

**Q3 — Microtask sizing.** **Two deliverables → two tickets** by default (`yegor-microtasks`: one concern, one
commit-worthy unit, "the finding is one deliverable, the code change another"). **Single ticket only** when the
finding already lives in `docs/research/*` — then the remaining swap is one ≤30m DEV that cites it, and splitting
further would be salami-slicing. Cite: `yegor-microtasks`.

**Q4 — pycats reconciliation.** Labels by branch of the decision tree:
- already-sourced → **`enhancement`** (DEV), cites the finding;
- sourceable-but-not-yet → **`research`** parent → **`enhancement`** (DEV) child, child *blocked-by* the research;
- no-faithful-value → **`decision`** (+ `humans-only`/`human-decision-required`) → **`enhancement`** (DEV) child.
There is **no `architect` label** and none should be minted — the architect role is expressed as `research`
(source) or `decision` (invent). Cite: labels present in-repo (`research`, `decision`, `enhancement`,
`humans-only`, `vapid`, `wont-do`); RULES → "Changing values" (FOUND/TUNED, `combat/provenance.py`, ADR-0003).

---

## Re-classification of #528's proposed follow-up #1

#528's findings doc (`docs/research/2026-07-04-pm-fall-physics.md`) proposes, as follow-up #1:

> "**DEV — source + pin the fall values.** Document Nalio's `gravity`/`max_fall_speed` as the Mario baseline
> (cite Brawl 0.075/1.28 → the pycats scale) and re-pin Birky's with the ratio citation (0.81/0.94) … *(note the
> DEV-vs-ARCHITECT classification question is #530.)*"

**Ruling: do NOT file this as one bare DEV. It bundles two different branches of the decision tree and must split
per `yegor-microtasks` (one concern per ticket):**

- **Nalio (Mario) → single DEV, ready now.** #528's doc already sourced the Mario baseline (Brawl 0.075/1.28 →
  pycats scale) with a citation → the finding exists (basis (1), **FOUND**). This is the "already-sourced → single
  DEV" branch: swap `gravity`/`max_fall_speed`, add the FOUND provenance entry, cite #528's doc in the commit +
  constant comment, land a proving test. Label **`enhancement`**.

- **Birky (Kirby) → decision → DEV, blocked.** #528's doc pins Birky by a *ratio* to Mario **but explicitly leaves
  the PM-vs-Brawl Kirby gravity ⚠ unconfirmed**, punting it to its own follow-up #3 ("**decision — Brawl vs
  PM3.6-exact target** for Kirby"). So Birky's number is **not yet settled** — it depends on a game-designer call.
  This is the "no faithful value settled → decision → DEV" branch: the Brawl-vs-PM3.6 choice is a **`decision`**
  (human), then a DEV applies the ratified number (**FOUND** if PM-sourced, **TUNED** if a surrogate) + proving
  test. The Birky DEV is **blocked-by** that decision.

So #528's three proposed follow-ups, re-labeled under this ruling, are already well-shaped:
1. **split** → (1a) Nalio **DEV** [ready] + (1b) Birky **DEV** [blocked-by #1(3) decision];
2. **ARC → DEV** fast-fall mechanic — correctly a split already (design the model, then wire it);
3. **decision** — Brawl vs PM3.6-exact Kirby — correctly a `decision` already (it *is* the basis Birky's DEV waits on).

---

## Proposed follow-up (NOT filed — out of #530's scope)

- **WRITER — add a "value-sourcing ticket routing" note to RULES → "Changing values"** distilling the decision
  tree above (already-sourced → DEV; sourceable → research→DEV; no-faithful-value → decision→DEV; no `architect`
  label). RULES today states the *basis* rule (FOUND/TUNED) and "picking a surrogate is a decision"; it does not
  yet state the *research/decision/DEV routing + labels*. This ruling warrants that addition — file it as a small
  WRITER ticket, per the ticket's "propose an edit only if the ruling warrants one (a follow-up)".

## Refs

- **Trigger:** #528 (`docs/research/2026-07-04-pm-fall-physics.md`, proposed follow-up #1 + its self-split).
- **RULES → "Changing values"** (basis (1) research/data / (2) designer decision; "picking a surrogate is a
  decision, not a DEV edit"; FOUND/TUNED; `combat/provenance.py`, ADR-0003; precedents #489, #491).
- **`yegor-architect`** (architect vs courier; "never mix modes"; "the *what* is owned by the requirements").
- **`yegor-bdd`** (work is a complaint; "no code change without a proving test").
- **`yegor-microtasks`** (one concern / one deliverable per ticket; the finding and the swap are two deliverables).
- **`yegor-tickets`** (decisions live in the tracker as artifacts).
- **`yegor-personas`** (council + authority ladder: requirements → objective measure → architect tie-break).
- In-repo labels: `research`, `decision`, `enhancement`, `humans-only`, `vapid`, `wont-do` (no `architect` label).
