# PM-mechanics grounding — a consult-before-assert mechanism (research #571)

**Role:** RESEARCH · no code. **Ticket:** [#571](https://github.com/avidrucker/pycats/issues/571).
**Question:** what most reliably forces an agent to ground in **real, evidence-backed PM 3.6**
mechanics — and cite them — *before* asserting or classifying PM behavior, so we stop
"reasoning from a proxy instead of the evidence."

This is the **proactive** half. The **detective** half (a gate that catches un-sourced /
registry-contradicting PM claims after the fact) is [#575](https://github.com/avidrucker/pycats/issues/575) —
not restated here.

---

## TL;DR recommendation

Build a **layered** mechanism, cheapest-first, reusing infra that already exists — not a single silver bullet:

1. **A `pm-mechanics` trigger-skill** (primary) — a thin skill whose *description* fires whenever
   an agent is about to assert/classify a PM/Melee/Brawl mechanic, and whose *body* force-loads the
   map (`00-overview.md` + `project-m-rules-by-category.md` + the relevant category doc) and the
   **provenance registry**, then demands a primary cite or an explicit `inference` label. This mirrors
   the live `author-vet-this-source` skill (description-triggered, force-reads shared core docs first).
2. **A short always-on RULES line** (backstop reflex) — folded into the pending
   [#562](https://github.com/avidrucker/pycats/issues/562) decision, generalized one notch to cover
   **proxy-reasoning beyond PM** (read the *body* not the title, *primary* not memory, *registry* not
   prose). This is the reflex that fires the skill.
3. **A `UserPromptSubmit` hook** (deterministic backstop) — *only if* skill+rule still miss. Net-new
   infra (this repo has **no hooks** today); defer until the cheaper layers are shown insufficient.

Skill = content loader · rule = reflex · hook = deterministic catch. Ship **1 + 2 first** (both reuse
existing docs and the existing #562 track); hold **3** in reserve.

---

## What already exists (the gap is consultation, not content)

The two-layer knowledge the human asked for is **already built**:

| Layer | Artifact | Role |
|---|---|---|
| Core primer | `docs/pm-reference/00-overview.md` | broad PM 3.6 model, conventions, source list |
| Sub-domain (12) | `docs/pm-reference/*.md` (`ledge-mechanics`, `defense-shield-dodge`, …) | detailed per-domain reference |
| Greppable map | `docs/project-m-rules-by-category.md` | one-line-per-mechanic index → doc + primary source + **status** |
| Status registry | `pycats/combat/provenance.py` + `tests/test_tuning_provenance.py` | FOUND/GUESS/TUNED/DIVERGENCE per constant (ADR-0003) |

**The gap is not content — it is the reflex to consult it.** Nothing today makes an agent *load and
cite* these before making a PM claim. The ledge divergence (#538→#543) and the #363 title-reasoning
error (#59) both happened with the correct evidence sitting one file away, unconsulted.

## Q1 — Mechanism: skill vs rule vs hook

| Mechanism | Reliability | Token cost | False-trigger | Verdict |
|---|---|---|---|---|
| **Trigger-skill** (`pm-mechanics`) | Medium — relies on the model recognizing its description matches the task; **no hard enforcement** | Cheap — body loads **only when triggered**; idle cost = one description line | Low if the description is tight | **Primary.** Best content-load-on-demand fit; proven pattern in-repo |
| **CLAUDE.md / RULES line** | Medium — always in context, but passive prose competing with ~15 other critical rules; easy to skim past | Always-on, small | Zero (no trigger) | **Backstop reflex.** Cheap, and #562 is already opening this track |
| **Hook** (`UserPromptSubmit`/`PreToolUse`) | **High — deterministic**, fires regardless of model attention | Fires on every matching prompt | Pattern-match false positives (any prompt naming "Melee"/"Brawl") | **Reserve.** Only *hard* option, but net-new infra; and a hook can inject a reminder, it still **cannot force the model to actually cite** |

**Precedent (live, in this environment):** `author-vet-this-source` — its frontmatter carries explicit
`Triggers —` phrases, and step 1 of its body is *"Read before vetting: [core docs]."* That is exactly
the shape a `pm-mechanics` skill needs: description-matched trigger → force-read the map + registry →
then act. (Note: the `claude-api` skill the ticket cited as precedent is **not installed here** — it was
a remembered example; `author-vet-this-source` is the locatable equivalent and confirms the pattern works.)

**Why layered, not one-of:** the skill loads the *right content* but can misfire on recognition; the
rule is the *always-on reflex* that reminds the agent the skill exists but has no teeth; the hook is
*deterministic* but coarse and can't compel a citation. Each covers the others' failure mode. No single
one is sufficient, so lead with the two cheapest that reuse existing infra.

## Q2 — Two-layer mapping

The human's (1) core primer / (2) sub-domain-on-demand maps **almost** cleanly onto `00-overview.md` +
the category docs — with one gap: `00-overview.md` is a *descriptive* overview, **not** a
"core mechanics you must never get wrong, and here's how each is sourced" primer. It does not foreground
the FOUND/TUNED/DIVERGENCE status or the shortlist of values pycats commits to.

**Recommendation:** do **not** author a whole new primer doc (content already exists). Instead the
`pm-mechanics` skill body should:
- point at `00-overview.md` + `project-m-rules-by-category.md` as **the map** (core layer),
- name a short **"must-never-get-wrong" shortlist** (60 Hz timing, the knockback formula lineage,
  ledge = *fixed* intangibility burst not percent-scaled, PM canon = 3.6),
- hard-link `combat/provenance.py` so the agent grounds in **status-tagged values**, not prose.

## Q3 — Trust the source (confidence-tag)

The ledge case proves `pm-reference/` **prose can itself be un-sourced or contradict the registry**
(the registry said `TUNED`; the doc implied PM-canon). So the mechanism must **route through the
status-tagged artifacts first** — the by-category index and the provenance registry both carry
FOUND/GUESS/TUNED/DIVERGENCE — and treat **un-tagged prose as unverified**.

A full confidence-tag *pass over all prose* is **out of scope here** — that content work belongs to
[#535](https://github.com/avidrucker/pycats/issues/535) (canonical register w/ verbatim citations) and
the [#575](https://github.com/avidrucker/pycats/issues/575) coverage gate. This ticket only wires the
*consultation order*: **registry/index (tagged) before prose (untagged).**

## Q4 — Both failure modes, and the general rule

- **(a) source-less mechanic claim** → the skill forces a primary cite or an explicit `inference` label
  (reconciles with #562's "label inference, never rule refuted/confirmed from reasoning").
- **(b) proxy-reasoning** (asserting from a title/memory, not the evidence) → this is **broader than PM**;
  #363 was a v1-classification from a ticket *title* without reading the *body*.

**Open sub-question, answered: yes** — (b) warrants a **general RULES line**, not a PM-only one:

> **Read the source before asserting.** Ground a claim in the primary artifact — the ticket **body**
> over its title, the **code** over memory, the status **registry** over prose. If you asserted from a
> proxy, say so and go read the source.

This is one notch broader than #562 (which is PM/parity-specific). Recommend #562 stays the PM-citation
rule; this general line is its parent principle and could land in the same RULES edit.

## Reconciliation (don't duplicate)

- **#562** — the PM-citation *rule*. This ticket's skill *operationalizes* it (loads + demands the cite);
  the proposed general line is its broader parent. No overlap.
- **#535** — the canonical citation *register* (content). The skill *consumes* it; doesn't rebuild it.
- **#536** — the ledge content audit. Owns the ledge instance; this ticket touches no PM content.
- **#575** — the *detective* gate. This is the *proactive* consult; they are complementary halves.

## Recommended follow-ups (seeds — no code here)

1. **DEV: author the `pm-mechanics` skill** — thin `SKILL.md`: description-trigger on
   "assert/classify a PM/Melee/Brawl mechanic or value"; body = force-load the map + provenance registry,
   the must-never-get-wrong shortlist, and the cite-or-label-inference demand. Use `skill-creator` /
   `write-a-skill`. (Blocked-by nothing; content already exists.)
2. **Fold into #562** — add the general **"read the source before asserting"** RULES line alongside the
   PM-citation rule, for human ratification.
3. **Reserve (do not build yet):** a `UserPromptSubmit` hook that injects the primer pointer when a
   prompt names PM/Melee/Brawl — only if #1+#2 still miss in practice.

## Out of scope

Implementing any mechanism (seeds a DEV). Re-auditing `pm-reference/` prose (#536 owns ledge; #535 owns
the register). The detective gate (#575).
