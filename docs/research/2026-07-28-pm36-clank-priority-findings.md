# Research findings — Project M 3.6 clank / priority mechanics (window, transcendent priority, rebound, projectiles) vs pycats

- **Ticket:** #869 (RESEARCH · area:combat) — spun out of #807 / ledger claim `PYC-C-006-GRAPE`; feeds scoping of `PYC-C-007-GRAPE` (the no-rebound gap).
- **Agent:** banana
- **Date:** 2026-07-28
- **Canon:** Project M 3.6 (a Brawl mod). Brawl is the labeled fallback baseline where no PM-3.6-specific primary exists.
- **Primary sources (accessed 2026-07-28):** SmashWiki [*Priority*](https://www.ssbwiki.com/Priority), [*Rebound*](https://www.ssbwiki.com/Rebound).

## TL;DR

pycats' clank rule (opposing **ground** hitboxes, **9%** damage window, aerials exempt, loser negated with no rebound) **matches the documented canon model** — with three labeled caveats:

1. **The 9% window is not PM-sourced.** SmashWiki documents **9% for Melee**, **10% for SSB64**, and a **formula for Smash 4** — and **never names Project M** and gives **Brawl no separate number**. PM 3.6 inheriting 9% is a **Brawl-baseline inheritance inference** (Brawl inherits Melee's 9%; PM is a Brawl mod; no PMDT changelog entry alters clank/priority), *not* a PM-3.6 primary. pycats' provenance record currently tags it flat **`FOUND`** citing "9% across the Melee/Brawl/PM family" — that **over-claims** the citation (see [Finding A](#finding-a--provenance-over-claims-the-9-citation)).
2. **The comparison is per-attack, not per-hitbox.** pycats compares each attack's **strongest box damage**; canon calculates "based on **individual hitboxes**." A minor divergence, benign for single-box moves ([Finding C](#finding-c--per-attack-max-box-vs-per-hitbox-comparison)).
3. **No rebound state / freeze frames** in pycats (the loser is just negated) — canon gives freeze frames equal to the stronger attack's hitlag, then a rebound animation. This is exactly the `PYC-C-007` gap ([Finding D](#finding-d--rebound-state--freeze-frames-absent-pyc-c-007)).

Everything else pycats models is faithful. Projectile-clank and transcendent-priority are **absent-but-correct-by-construction** (no projectiles/specials authored yet).

---

## Verbatim canon (the primary quotes this doc rests on)

All from SmashWiki, accessed 2026-07-28. **Game-of-record labeled per quote** — this is the crux of the ticket.

### Clank event & the 9% priority range

> "When two ground attack hitboxes overlap, they will clank. This collision is signified by a white 'bubble'."
> — *Priority* (general).

> "If the stronger hitbox (by %) deals more than 9% (the 'priority range') more than the weaker hitbox, the stronger move will continue as normal…"
> — *Priority*. **Game-of-record: Melee.** The 9% figure is stated in the ground-attacks section anchored to Melee; the article does **not** restate a separate number for Brawl.

> "(note that in the original Super Smash Bros., the priority range is instead 10%)"
> — *Priority*. **SSB64 = 10%** (the one explicitly-differing value).

> "If both hitboxes deal within 9% of each other, both moves will end and both characters will go into rebound."
> — *Rebound* (general statement of the window).

**On PM / Brawl specifically:** *Project M is not named in either article.* Brawl is given **no** priority-range number of its own — i.e. the article treats Brawl as sharing the 9% (only SSB64's 10% and Smash 4's rebound-length formula are called out as different).

### Ground vs aerial

> "Different rules apply to the hitboxes of normal aerial attacks. When a normal aerial attack hitbox overlaps that of a normal ground attack or another normal aerial, the attacks do not clank."
> — *Priority*.

> "However, the hitboxes of aerial attacks can clank with projectiles."
> — *Priority*.

> Aerial attacks "cannot rebound at all."
> — *Rebound*.

### What "strength" is compared

> "While the effects of priority are calculated based on individual hitboxes, the results are applied to the attacker as a whole."
> — *Priority*. Comparison is by **damage %** ("the stronger hitbox (by %)"), computed **per hitbox** (not per whole-attack).

### Clank outcome — freeze frames + rebound animation

> "First, a rebounding character will suffer freeze frames equal to the hitlag of the **stronger** attack (by %)."
> — *Rebound*.

> "After the freeze frames are over, characters go through a unique rebound animation."
> — *Rebound*. **Rebound-animation length, Melee:** `R = Roundup(0.559 * (d + 10))`; **Smash 4:** `R = Floor((d + 4) * 15 / 8)`. (Brawl not given a formula in the quotes pulled — treat as Melee-family; **not** needed by pycats until rebound state exists.)

### Multi-hitbox / >2 boxes

> "While the effects of priority are calculated based on individual hitboxes, the results are applied to the attacker as a whole."
> — *Priority*. The article **does not** address three-or-more simultaneously-overlapping opposing hitboxes — **canon is silent** on the >2 case.

### Projectile vs melee

> "Similar rules apply when ground attack hitboxes overlap normal projectile hitboxes. If the ground move deals more than 9% more than the projectile, the projectile is destroyed and the ground move continues…"
> — *Priority*. Projectiles use the **same 9% window** vs ground moves; and (above) **aerials can clank projectiles** even though aerials never clank melee.

### Transcendent priority

> "Transcendent priority (also known as transcending priority) refers to hitboxes that cannot clank with other hitboxes, meaning they won't cancel out, or be cancelled out by, other hitboxes."
> — *Priority*. It is a **per-hitbox flag**, not a damage comparison. Named examples: **Fox's Blaster**, **Meta Knight's forward smash (Brawl)**, **Ganondorf's down aerial (Melee/Brawl/Smash 4)**.

---

## The exact PM 3.6 model (assembled, with each figure's basis labeled)

| Rule | Value / behavior | Game-of-record in the primary | PM 3.6 basis |
|---|---|---|---|
| Priority (clank) window | **9%** damage difference | Melee (stated); SSB64=10%; Smash 4 = rebound-length formula | **[inference — Brawl-baseline]** Brawl inherits Melee's 9%; PM is a Brawl mod; no PMDT change → PM retains 9% |
| Resolution basis | deterministic, from **damage %** — no RNG | general | inherited |
| Within window (incl. equal) | **both** moves end → **both** rebound | general | inherited |
| Outside window | **stronger continues, weaker ends** → weaker rebounds | general | inherited |
| Ground vs aerial | ground clanks ground/aerial; **aerials never clank melee**; **aerials CAN clank projectiles** | general | inherited |
| Comparison granularity | **per individual hitbox**, result applied to attacker as a whole | general | inherited |
| Clank outcome | **freeze frames = stronger attack's hitlag**, then a unique **rebound animation**; aerials cannot rebound | general (Melee/Brawl family) | inherited |
| Projectile vs ground | same 9% window; ground >9% stronger destroys projectile & continues | general | inherited |
| Transcendent priority | per-hitbox flag; those hitboxes never clank | general (examples Melee/Brawl/Smash 4) | inherited |
| >2 opposing hitboxes | **not documented** | — | canon silent |

**Bottom line on the ticket's headline question ("is it 9%? same across PM 3.6 / Brawl?"):**
Yes, 9% — but the **9% is Melee-documented and Brawl-inherited; PM 3.6 is not named in any primary**. It firms to a PM-3.6 `FOUND` only on a PM-3.6-specific primary (an in-engine hit-collision dump or a PMDT statement quoting the priority range). This is the **same fallback-ladder situation** as the #874 tap-jump toggle: a firmly-pinned Brawl baseline + a labeled Brawl-inheritance inference, not a bare guess.

---

## pycats coverage table (match / diverge / absent — pinned)

Code as of this worktree (`br-banana/pycats-869…`, base `main` @ `00b4a8d`). Landmarks are function/file, not line numbers.

| Canon rule | pycats | Verdict | Where |
|---|---|---|---|
| Clank = opposing **ground** hitboxes overlap | pairwise over active, `not in_air`, different-owner, overlapping | **MATCH** | `systems/combat.py::_resolve_clanks` |
| 9% window: within → both end; outside → stronger survives | `abs(da-db) <= CLANK_PRIORITY_RANGE(9)` both `_negate`; else weaker `_negate` | **MATCH** (boundary faithful: diff *exactly* 9 clanks, matching "more than 9% … continue") | `_resolve_clanks`; `config.CLANK_PRIORITY_RANGE` |
| 9% is PM 3.6 canon | provenance tags it `FOUND`, "across the Melee/Brawl/PM family" | **DIVERGE (citation)** — see Finding A | `combat/provenance.py::CLANK_PRIORITY_RANGE` |
| Aerials don't clank melee | `in_air` hitboxes excluded from the clank pass | **MATCH** | `_resolve_clanks` (`live = … not in_air`) |
| Aerials **can** clank projectiles | no projectiles authored; rule is "aerials never clank" | **ABSENT** (correct-by-construction until projectiles exist) | — |
| Comparison per **individual hitbox** | representative = attack's **max box damage** | **DIVERGE (minor)** — see Finding C | `_clank_strength` |
| Freeze frames + rebound animation on clank | loser just `_negate`d (active=False / kill); no rebound state, no freeze | **ABSENT** = `PYC-C-007` gap — see Finding D | `_negate` |
| Projectile vs ground (same 9% window) | no projectiles authored | **ABSENT** (correct-by-construction) | — |
| Transcendent priority (per-hitbox no-clank flag) | no flag modelled | **ABSENT** | — |
| >2 opposing hitboxes | pairwise negation as encountered | **canon-silent** → pycats' pairwise pass is a defensible extrapolation, not a known divergence | `_resolve_clanks` nested loop |

---

## Findings (each is a downstream follow-up candidate — filed one-at-a-time, not in this doc)

### Finding A — provenance over-claims the 9% citation
`combat/provenance.py` records `CLANK_PRIORITY_RANGE = Provenance(9, "%", "SmashWiki:Priority — 9% across the Melee/Brawl/PM family", "FOUND", 38)`. The primary **does not** say "across the … PM family" — SmashWiki names the 9% for **Melee**, gives Brawl no number, and never names PM. Per the grounded-claim discipline this should read as **Brawl-baseline inheritance inference** (the value is right; the *basis label* is inflated), not a flat PM `FOUND`. **Directly informs `PYC-C-006-GRAPE` verification (#872):** the claim that pycats' 9% window matches PM 3.6 is TRUE-with-caveat (Brawl-inherited, PM not primary-named), not a clean canon `FOUND`. *No edit made here — value change/re-tag needs its own downstream ticket + basis, per RULES "Changing values".*

### Finding B — pm-reference wording "9% across Melee → Brawl → PM"
`docs/pm-reference/combat-hitboxes-priority.md` ("Brawl / Melee deltas") states "Priority range: 9% across Melee → Brawl → PM". The Melee→Brawl half is supported; the **→ PM** half is inheritance-inference (PM not named). Candidate doc-label tightening (same fallback-ladder framing as #874).

### Finding C — per-attack (max-box) vs per-hitbox comparison
Canon compares **individual hitboxes**; pycats compares each attack's **strongest box** (`_clank_strength`). Benign for single-box moves and for moves whose strongest box is the one overlapping; can differ for a multi-box move where a **weaker** box is the one actually overlapping the opponent's hitbox. Low-priority fidelity item; note in any future multi-box clank work.

### Finding D — rebound state & freeze frames absent (`PYC-C-007`)
Canon: on a clank both fighters take **freeze frames = stronger attack's hitlag**, then a **rebound animation** (aerials can't rebound). pycats `_negate`s the losing hitbox with **no** rebound state and **no** freeze frames. This is exactly the `PYC-C-007-GRAPE` no-rebound gap — this doc confirms it and pins the canon target (freeze = stronger hitlag; then rebound anim; Melee length `Roundup(0.559*(d+10))`). Scoping a rebound state is a downstream DEV/DESIGN slice, gated behind the hitlag work (#825 area).

### Finding E — projectile & transcendent-priority absent-by-construction
No projectiles or transcendent-priority flag exist yet. The **aerials-never-clank** rule as coded will be **wrong once projectiles exist** (canon: aerials *can* clank projectiles). Flag for whenever projectiles are authored — the `in_air` exemption needs a projectile carve-out then.

---

## Out of scope (per ticket)

No implementation, no value re-tag, no provenance/pm-reference edits in this pass. Each finding above is a candidate follow-up filed **one at a time** downstream of this doc, on an explicit go-ahead.

## Sources

- SmashWiki — [*Priority*](https://www.ssbwiki.com/Priority) (clank, 9% window, ground/aerial, transcendent priority, projectile-vs-ground), accessed 2026-07-28.
- SmashWiki — [*Rebound*](https://www.ssbwiki.com/Rebound) (within-9% → both rebound; freeze frames = stronger hitlag; Melee/Smash 4 rebound-length formulas; aerials can't rebound), accessed 2026-07-28.
- PMDT changelog survey (Project M 3.x): no entry altering clank/priority/rebound located ([PM 3.0 changelog thread](https://smashboards.com/threads/project-m-3-0-released-changelog-in-post.343401/), [pmunofficial.com](https://pmunofficial.com/en/)) — supports "PM retains Brawl's clank model" as inheritance, not modification.
- Prior in-repo: [`docs/research-findings-141-clank-priority-simultaneous-trade-dragonfruit-2026-06-26.md`](../research-findings-141-clank-priority-simultaneous-trade-dragonfruit-2026-06-26.md), [`docs/pm-reference/combat-hitboxes-priority.md`](../pm-reference/combat-hitboxes-priority.md).
