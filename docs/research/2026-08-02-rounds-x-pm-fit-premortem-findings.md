# Mixing PM/Brawl/Melee fighter mechanics with ROUNDS' card-draft — fit, risks, opportunities (premortem)

**Ticket:** #1076 (RESEARCH · brainstorm + premortem · `area:combat`) · **Date:** 2026-08-02 · **Agent:** FIG
**Parent:** #347 (Rounds Mode epic, deferred). **Sibling dependency:** the ROUNDS core-mechanics findings (#1075/#1085, `docs/research/2026-08-02-rounds-game-mechanics-findings.md`) — every ROUNDS-side fact here is taken from that doc, not re-derived.
**Deliverable:** this doc. **Findings + option space only — no mode design, no pycats card catalog, no ratified format choice.** This is analysis to inform a future design/architect child; it surfaces consequences, it does not rule them.

> **What this ticket is.** ROUNDS' escalating-power draft was built on a *ROUNDS-style shooter* — a ranged, HP-attrition game. pycats is a *melee platform-fighter* modelling PM 3.6 / Brawl / Melee (knockback %, hitstun, stocks, ledges, disjoints, recovery, shields). Bolting one onto the other is **not obviously a clean fit**. Below: a structured "what composes / what clashes / what breaks, and why," a premortem of the most probable ways it flops, and the opportunities the fighter base opens that a shooter can't.

---

## 0. How to read the evidence grades

Two provenance streams meet in this doc, so each claim carries the grade of *its* stream:

| Grade | Meaning | Trust |
|---|---|---|
| **[pycats]** | Grounded in pycats source — `pkg/mod.py::Symbol` | Highest for the pycats side |
| **[PM]** | Project M / Brawl / Melee canon (SmashWiki formula, cited where pinned) | Canon for the fighter side |
| **[ROUNDS §N]** | A fact carried over from the #1075/#1085 ROUNDS findings, that doc's section N | As graded there |
| **[Inference]** | My reasoning from the above — a hypothesis, not a stated fact | Treat as analysis |

**Evidence sufficiency is Avi's call** (per the ticket). This doc flags what is analysis vs. grounded fact; it does not gate the epic on my own judgment.

---

## 1. TL;DR — the two-axis mismatch, and the one thing to preserve

**ROUNDS and pycats disagree on two independent axes, and the disagreement is the whole story:**

1. **Ranged vs. melee.** ROUNDS is a *bullet* game — roughly **half its 67-card catalog** is projectile physics (bounces, homing, ammo, reload, spread, drill, steer; [ROUNDS §8.4]). pycats cats are **melee** — a move is `nair`/`bair`/`utilt`, resolved by hitbox-circle overlap (`systems/hit_resolution.py`) [pycats]. **The projectile half of the catalog has no surface in pycats at all.** A literal port is impossible; the catalog must be redesigned melee-native.

2. **HP-attrition vs. knockback.** ROUNDS damage is a **subtractive HP pool** — linear: a "+30% damage" card linearly shortens time-to-kill [ROUNDS §8.1]. pycats has **no HP bar**; you accumulate **percent**, and a KO happens when a hit's **knockback** launches you past a blast zone (`config/stage.py::BLAST_PADDING`) [pycats]. Knockback is **super-linear** in both percent and damage (`combat/knockback.py::knockback`, formula below) [PM]. So the *same* "+damage" card is **far swingier** in pycats than in ROUNDS — it converts to early KOs nonlinearly, and the rubber-band can over-correct.

**The one thing worth preserving verbatim:** the **meta-loop** — *only the loser drafts, cards are permanent and stack, the offer is random* ([ROUNDS §5]). That loop is **orthogonal to the combat model** — it works over any win condition — and it **maps onto stocks natively** (concede a stock → draft). It's the crown jewel and it ports cleanly.

**Slogan for the eventual designer:** *keep the loop, throw away the catalog, and respect the knockback curve.* [Inference]

---

## 2. The two combat models, precisely — the mismatch everything hinges on

### 2.1 ROUNDS: a subtractive HP pool

A ROUNDS fighter has an HP number. Bullets subtract from it; a duel ends at 0. Cards add HP, bullets, damage, DoT, lifesteal — all **additive or simple-percentage on a linear pool** [ROUNDS §8.4]. "+30% damage" means each bullet subtracts 30% more; time-to-kill drops ~linearly. This linearity is *why ROUNDS can hand out dozens of stacking buffs and stay balanced* — the designer can reason additively.

### 2.2 pycats/PM: percent → knockback → blast-zone KO

pycats has **no HP**. The chain is [pycats]/[PM]:

```
hit lands → percent += damage → knockback(percent, damage, weight, BKB, KBG) → launch
          → if launch crosses a blast zone (config/stage.py) → KO (lose a stock)
```

The knockback magnitude (`combat/knockback.py::knockback`, SmashWiki-sourced) is:

```
KB = ((((p/10) + (p·d/20)) · (200/(w+100)) · 1.4) + 18) · (KBG/100) + BKB
     where p = post-hit percent, d = damage, w = weight
```

Three consequences that ROUNDS' model does **not** have [Inference from the formula]:

- **Super-linear in percent.** The `p·d/20` term means KB grows faster than linearly as percent climbs — the essence of the Smash "you get lighter as you get hurt" feel. A buff that raises damage raises *both* the immediate KB and the rate percent accumulates, compounding.
- **Super-linear in damage.** `d` appears inside the `p·d` product *and* additively — so "+damage" is not a linear knob.
- **Weight is in the denominator.** `200/(w+100)` — a "+HP" analog (see §3) that maps to weight is *also* nonlinear, and inversely so.

**This is the central fact of the whole premortem:** every ROUNDS card that touches damage, HP, or "survivability" lands on a **nonlinear** surface in pycats. ROUNDS' additive-balance reasoning does not transfer. [Inference]

---

## 3. Mechanic-by-mechanic fit matrix

ROUNDS card **families** ([ROUNDS §4]) × pycats/PM **subsystems**. Verdict: **Composes** (ports with a clean analog) · **Clashes** (portable but fights a tuned system) · **Breaks** (no surface, or reopens an unratified mechanic).

| ROUNDS card family | pycats/PM subsystem it lands on | Verdict | Why |
|---|---|---|---|
| **Bullet physics** — bounce, homing, ammo, reload, spread, drill, steer (Barrage, Ricochet, Homing, Quick Reload, Spray, Drill Ammo, Remote…) | *none* — cats are melee (`hit_resolution.py` circle overlap) [pycats] | **Breaks** | pycats has no projectile system. ~half the 67-card catalog [ROUNDS §8.4] has zero surface. Not portable; must be replaced by melee-native cards. |
| **Raw damage** — Glass Cannon, Careful Planning, Wind Up, Combine | `knockback()` percent/damage terms; per-move `MoveData.damage` [pycats] | **Clashes** | Ports as a per-move damage patch, but the knockback curve (§2.2) makes it **swingy/nonlinear** — the #1 balance hazard. |
| **HP / survivability** — Huge, Tank, Pristine Perseverance, Decay | weight (`200/(w+100)` term) or a shield-health analog [pycats]/[PM] | **Clashes** | No HP bar. Cleanest map is **weight** — but weight is nonlinear and inverse; "+HP" over-survives at low percent, barely helps at high. |
| **Extra life** — Phoenix (respawn once) | stocks (`systems/win_condition.py`, `match_engine.py`) [pycats] | **Composes** | "+1 stock" is a clean, native analog — stocks *are* ROUNDS pips. |
| **Lifesteal / regen** — Leech, Lifestealer, Parasite | percent-heal (reduce your own %) — a novel seam [Inference] | **Composes** | "heal % on hit" is coherent and melee-native; no existing system but no clash either. |
| **Movement / tempo** — Chase, Taste of Blood, Scavenger | dash/run/air speed (grounded speeds, #813) [pycats] | **Composes** | pycats has real movement stats; +movespeed cards port directly. |
| **Recovery / vertical** (the fighter analog: +jump, +recovery distance) | up-B / recovery hook (**#578**), ledge-getup (**#754**) [pycats] | **Breaks** | Touches the **edgeguard game** — a core PM depth axis. "+1 jump" / "2× up-B" trivializes edgeguarding. Highest blast-radius on the most PM-specific system. |
| **Bigger hitbox / disjoint** (the melee analog of "Big Bullets") | hitbox size + clank/priority + multi-hitbox (`hit_resolution.py`, #130) [pycats] | **Clashes** | Growing a move's hitbox flips priority trades and **reopens the same-frame multi-hit questions #829/#843 are still researching** — unratified mechanics underneath. |
| **On-block triggers** — the whole "block-triggered" family (Bombs Away, Echo, Shockwave, Teleport…) [ROUNDS §4.5] | shield (`combat/shield.py`: shieldstun, shield-break) [pycats] | **Clashes** | pycats *has* a block analog (**shield**), so on-block cards have a surface — but PM shields (deplete, poke, drop, break) are a very different action from ROUNDS' cooldown-gated block. Rich but semantically clashy. |
| **DoT / on-hit AoE** — Poison, Explosive Bullet, Toxic Cloud | percent-over-time on a hurtbox [Inference]; no AoE system [pycats] | **Clashes** | A "% over N frames" DoT is portable onto the percent model; the AoE/explosion half needs a system that doesn't exist. |
| **Downside cards** — Glass Cannon −HP, Demonic Pact −HP/shot | −weight / −stock / self-percent [Inference] | **Clashes** | The trade-off backbone [ROUNDS §5] ports, but every downside is nonlinear too (−weight = float away earlier, compounding). |
| **Draft meta-loop** — loser-drafts, permanent, stacking, random offer | win-condition + a new draft state; seeded RNG (**#166**) [pycats] | **Composes** | The loop is combat-model-agnostic and maps onto stocks. Determinism is **already solved** (#166 seam). The crown jewel. |

**Reading the matrix:** exactly **one row Composes cleanly on the combat side** (movement, lifesteal, +stock) plus the meta-loop; the damage/HP/hitbox/block rows all **Clash** (portable but fight a tuned nonlinear system); and two families **Break** outright (bullet physics has no surface; recovery cards wreck edgeguarding). [Inference]

---

## 4. What's likely to work WELL, and why

1. **The catch-up loop is orthogonal to the combat model and maps onto stocks.** *Only the loser drafts* [ROUNDS §5] needs a win condition and a draft state — nothing about HP vs. knockback. **Concede a stock → draft** is a native pip analog (`win_condition.py`). The single most valuable ROUNDS mechanic ports with zero combat-model friction. [Inference]
2. **A fighter kit is a far richer modifier surface than a shooter.** ROUNDS modifies *one gun* (damage, bullets, reload). pycats exposes **per-move damage, hitbox size/position, KBG/BKB, angle, jump count, recovery distance, dash/air speed, weight, shield health** — and `MoveData` is already **declarative JSON per cat** (#792 flip) [pycats]. **A card is literally a `MoveData` patch.** The card design space is strictly larger than ROUNDS'. This is the ticket's own hypothesis, and the source bears it out. [Inference from `combat/data.py::MoveData` + the #792 JSON flip]
3. **Determinism is already solved — a de-risk ROUNDS never needed.** The draft is random, and pycats' golden oracle (`test_golden`) needs reproducible matches. **#166 shipped a seeded-RNG seam** (fixed seed for sims/goldens, clocktime for live) [pycats, #166 CLOSED]. The draft can reuse it → seedable → goldens survive. ROUNDS had no such constraint; pycats *already built the tool*. [Inference]
4. **Synergies get deeper with movesets.** ROUNDS sells 11.2M combinations [ROUNDS §1]. A fighter multiplies the surface: a "+KBG on smashes" × "+disjoint reach" × "smaller blast zone" build is an edgeguard engine with no shooter analog. The combinatorial-novelty selling point *scales up* on a richer kit. [Inference]
5. **Value drift is auditable.** A card bumps a tuning constant, and pycats already tracks tuning provenance (`combat/provenance.py`, guarded by `test_tuning_provenance`) [pycats]. A card system is *sanctioned* runtime drift — the registry gives a ready vocabulary to describe "this card set KBG from X to Y." (Also a tension — see §5.5.)

---

## 5. What's likely to work POORLY, and why — the clash list, ticket-tagged

1. **Knockback nonlinearity → swingy buffs → the rubber band can invert.** `combat/knockback.py::knockback` is super-linear in percent *and* damage (§2.2) [PM]. ROUNDS' most common card is "+30% damage" [ROUNDS §8.4]; in pycats that converts to early KOs **nonlinearly**. The catch-up loop hands buffs to the *loser* — but a nonlinear buff can **over-correct**, flipping the trailing player into a runaway. Balancing is materially harder than ROUNDS' additive HP. **Touches:** `knockback.py`, `config/stage.py` (blast zones).
2. **~Half the catalog has no surface.** Bounce/homing/ammo/reload/spread/drill/steer — the projectile-physics families [ROUNDS §8.4] — reference a bullet system pycats doesn't have. A naive port yields **dead, nonsensical cards** ("+2 bounces" on a melee `bair`). The catalog must be re-authored melee-native, not transcribed. **Touches:** `hit_resolution.py` (melee-only).
3. **Recovery/ledge cards break edgeguarding.** The fighter analog of ROUNDS' mobility cards is "+jump / +recovery." Those land on the recovery hook (**#578**) and ledge-getup facts (**#754**) [pycats] — the **edgeguard game**, one of PM's deepest axes. A card that adds a jump or doubles up-B distance trivializes it. Highest blast-radius on the most PM-specific system.
4. **Bigger-hitbox / disjoint cards reopen unratified mechanics.** A "+hitbox size" card interacts with clank/priority and the multi-hitbox machinery (`hit_resolution.py`, #130) [pycats]. The one-connect guarantee was audited (#943 CLOSED), but **how canon resolves multiple same-frame hitboxes (#829) and multi-target hits (#843) is still OPEN research.** A hitbox-resizing card sits directly on top of two unratified questions. **Touches:** #829, #843.
5. **Permanent stacking vs. PM's tuned frame data — and vs. the drift guardrail.** PM frame data is carefully balanced; ROUNDS' whole appeal is escalation *past* any fixed tuning [ROUNDS §5]. pycats' `provenance.py` + `test_tuning_provenance` exist specifically to **stop undocumented value drift** [pycats]. A card system is *deliberate* runtime drift — it fights the guardrail's intent. Resolvable (cards get their own provenance vocabulary — see §4.5) but a real tension to design around.
6. **Draft-replay determinism vs. a live match.** #166's seam is built [pycats], but its live/goldens split (clocktime vs. fixed seed) means the **draft-replay story for goldens must be wired through it deliberately** — an unseeded draft makes every match-running golden nondeterministic (see premortem #5). pycats is currently local-only (no netcode), so there's no rollback problem *yet* — but replay determinism for the oracle is non-optional. **Touches:** #166, `test_golden`.
7. **CPU can't play around a random loadout.** The CPU controller (`sim/controllers.py`; epic **#231**, decision-making research **#915** — both OPEN) [pycats] has no notion of "I now hold Glass Cannon, so I die to one hit." A CPU handed a random build plays it blind. CPU competence with drafted loadouts is **unsolved and out of #231/#915's current scope.** **Touches:** #231, #915.

---

## 6. Premortem (Murphyjitsu) — assume it shipped and flopped

For each: the failure, *why* it's probable given the systems above, and the **early signal** that would predict it in playtest/telemetry.

| # | Failure mode | Why probable | Early signal (watch for this first) |
|---|---|---|---|
| 1 | **Degenerate dominant card** | KB nonlinearity (§2.2) rewards one knob (e.g. "+KBG on all moves") strictly above others; every loser picks it | A card's **pick-rate ≫ its draft-frequency**; win-rate correlates with holding it |
| 2 | **Runaway leader (no catch-up)** | If cards are too weak vs. a stock lead, or the leader still 2-touches, the rubber band fails | **Point-differential *widens* after the first draft** instead of narrowing; comeback rate below ROUNDS' baseline |
| 3 | **Swingy over-correction (opposite of #2)** | Nonlinear buffs over-correct → trailing player *becomes* the runaway → matches oscillate | **Lead changes every point**; match length bimodal (blowouts in both directions) |
| 4 | **Draft screen kills the tempo** | ROUNDS' magic is *instant* restart [ROUNDS §5.4]; a modal draft between stocks breaks the "needle swinging" — and adds a statechart state (`screen_parity`) [pycats] | Playtesters **rush/skip the draft**; session length drops; the fast pick→counterpick feel is gone |
| 5 | **Unseedable draft reds the goldens** | If the draft isn't wired through #166's seam, every match-running golden goes nondeterministic | **`test_golden` flakes the instant the mode is enabled** (mitigation exists — #166 — but must be *used*) |
| 6 | **Catalog feels bolted-on** | A literal ROUNDS port keeps bullet/reload cards with no melee meaning (§5.2) | Playtesters **can't tell what a card does**; card-comprehension fails; "why is there a reload card in a fighter?" |

**The two failures most worth designing against up front:** #1/#3 (both are the **knockback curve** biting — the thing ROUNDS' additive model never had to fear) and #4 (the **tempo** — the thing ROUNDS' instant-restart got for free). [Inference]

---

## 7. Opportunities unique to the fighter base (option space — not a plan)

Things ROUNDS *can't* do that a Smash-like enables. Surfaced as a space for the downstream design child, **not** proposed for build.

- **Stage / camera cards.** "Smaller blast zones," "moving platform," "windbox stage," "lower ceiling." A platform fighter has stage geometry to draft against (`config/stage.py`) [pycats]; a shooter arena doesn't. — but note the KB-nonlinearity interaction (smaller blast zone × +damage compounds).
- **Recovery / ledge cards.** "+1 jump," "tether recovery," "ledge-snap intangibility" — a whole family with no shooter analog (double-edged; see §5.3).
- **Per-move disjoint tuning.** Cards that reshape a *single* move's hitbox/angle/KBG — far more expressive than "+damage on your one gun," and `MoveData` already supports per-move patches (#792) [pycats].
- **Weight / fall-speed cards.** Trade survivability (weight) for combo weight / tech-chase pressure — a knockback-native axis a shooter has no room for.
- **Taunt / meter mechanics.** Draft a resource that builds on taunt or on landing a smash — a fighter-native economy ROUNDS has no verb for.
- **Stock-count as the pip, natively.** The catch-up loop needs no invented score — **the stock count *is* the ROUNDS pip** (`win_condition.py`) [pycats].

---

## 8. Open questions handed downstream (Avi's call — surfaced, not ruled)

Per the scope guard, these are *consequences to weigh in the design/architect child*, not decisions this doc makes:

1. **What does "HP" map to?** Weight (nonlinear, inverse), a shield-health pool, a percent-heal, or +stock — the §3 "HP/survivability" row has no single clean analog. The choice sets the whole balance character.
2. **How is the swinginess (§5.1) tamed?** Cap KBG/damage buffs? Diminishing returns on stacks (ROUNDS has *no* global cap [ROUNDS §7 gap])? Weaker cards than ROUNDS? A decision that trades away ROUNDS' escalation feel for pycats' KB reality.
3. **Melee-native catalog scope.** How many of the 67 cards have *any* melee analog, and how many are net-new? (Rough read from §3: the ~half that are bullet physics don't; movement/HP/lifesteal/on-block/DoT do, with clashes.)
4. **Does the draft break the tempo, and can a fast/non-modal draft UI preserve the "needle swinging"?** (Premortem #4 — a screens-epic #18 / #818 concern too.)
5. **CPU-with-loadout competence** — is it in scope for v1, or does the mode ship human-only until #231/#915 extend the CPU? (Premortem — §5.7.)
6. **Seeding contract** — confirm the draft rides #166's seam for goldens before any match-running test depends on it. (The one item with a *known* answer: yes, and it's mandatory.)

---

## 9. Scope guard

Per repo rules, this doc **reports findings + option space only.** It contains **no** ROUNDS→pycats mode design, **no** pycats card catalog, **no** modifier-layer or draft-screen spec, and **does not rule** #347's format / catalog / who-drafts questions — it surfaces their consequences. ROUNDS-side facts are cited to the #1075/#1085 findings, not re-derived. Fighter-side claims are grounded in pycats source or PM canon and labelled `[Inference]` where they are my analysis. Determinism (#166) is noted as a constraint the eventual draft must satisfy, not designed here. The mode design belongs to a downstream architect/decision child, filed one-at-a-time after #347 is un-deferred (research never produces a spec).

---

## Sources

**pycats source (this repo, worktree `wt-fig-pycats-1076` @ branch base):**
- `pycats/combat/knockback.py::knockback` / `::hitstun_frames` / `::hitlag_frames` — the Brawl/PM knockback + hitstun formula (SmashWiki-sourced in its docstring)
- `pycats/config/stage.py::BLAST_PADDING` / `::BLAST_PADDING_TOP` — KO boundaries
- `pycats/systems/win_condition.py`, `pycats/systems/match_engine.py` — stocks / win condition
- `pycats/combat/shield.py` — shield / shieldstun / shield-break (the "block" analog)
- `pycats/systems/hit_resolution.py` — hit detection, clank/priority, multi-hitbox (#130)
- `pycats/combat/data.py::MoveData` + the #792 per-cat JSON flip — the declarative move surface a card would patch
- `pycats/combat/provenance.py` + `tests/test_tuning_provenance.py` — the tuning-drift guardrail

**Referenced tickets (state as of 2026-08-02):**
- #347 (OPEN, deferred) — Rounds Mode epic (parent)
- #166 (CLOSED) — seeded-RNG seam for deterministic sims/goldens (the determinism de-risk)
- #578 (CLOSED) — up-B / special-recovery engine hook; #754 (CLOSED) — ledge-getup frame facts
- #943 (CLOSED) — one-connect guarantee audit; **#829 (OPEN)** — same-frame multi-hitbox resolution; **#843 (OPEN)** — multi-target hits
- #231 (OPEN) — CPU difficulty epic; #915 (OPEN) — CPU decision-making research

**ROUNDS-side facts:** all from `docs/research/2026-08-02-rounds-game-mechanics-findings.md` (#1075/#1085) — cited inline as `[ROUNDS §N]`.

*This is a premortem analysis, not a measurement: the `[Inference]` claims (buff swinginess, catalog fit percentages, failure-mode probabilities) are reasoned from the cited formula and systems, not observed in a built mode. They are the hypotheses a design child should carry in with eyes open.*
