# Smash charge ramp — primary-source provenance (research #626)

**Question (from #626, spun out of the #599 caveat):** confirm or refute Project M's
smash-attack **charge ramp of 59 frames** (vs the base-game 60) against a *primary* source,
and route the outcome — upgrade the provenance, revert to 60, or mark `⚠ undocumented`.

**Verdict in one line:** the **×1.3671 full-charge multiplier is now primary-confirmed**
(meleelight, a Melee engine reimplementation); the **59-frame ramp is neither confirmed nor
refuted by any accessible primary** — it rests on a single secondary (SmashWiki *Project M*)
that *contradicts SmashWiki's own general article* (which states 60 frames for every game
Melee→Ultimate). Recommendation: **keep 59** as the PM-specific value but **downgrade its
provenance note to `⚠ primary-unconfirmed`**, and **upgrade the multiplier's note** to cite the
meleelight primary.

Citation discipline (per RULES → PM parity, and memory `pm-parity-cite-primary-not-inference`):
primary quotes are labelled **[primary]**; secondary/wiki claims **[secondary]**; reasoning
**[inference]**. Note this corrects a mislabel in `smash-charge-hold.md` (#595), which called
SmashWiki *Project M* a "primary" — a wiki is a **citable secondary**, not primary.

---

## What each source actually says

### Multiplier — ×1.3671 at full charge → **[primary] confirmed**

`~/Documents/Study/JavaScript/meleelight/` (clone from #616 — schmooblidon/meleelight, a
faithful **Melee** engine reimplementation in JS). Every forward/down/up-smash hardcodes the
same ramp, e.g. `src/characters/marth/moves/FORWARDSMASH.js`:

```js
player[p].phys.chargeFrames++;
if (player[p].phys.chargeFrames === 60) { /* fire at cap */ }
// damage scaling elsewhere: damage *= 1 + chargeFrames * (0.3671 / 60)
```

At full charge (`chargeFrames = 60`): `1 + 60*(0.3671/60) = 1.3671`. This is a **[primary]**
engine literal for **Melee**, and PM restored Melee's multiplier — so `SMASH_CHARGE_SCALE =
1.3671` is corroborated by a primary (Melee lineage) **and** two secondaries (SmashWiki *Smash
attack*: "1.3671× damage in Melee"; SmashWiki *Project M*: "x1.3671"). Well-sourced.

### Ramp — 59 vs 60 frames → **neither confirmed nor refuted by a primary**

| Source | Tier | Says | On which game |
|---|---|---|---|
| meleelight (`chargeFrames === 60`) | **[primary]** engine literal | **60** | Melee |
| SmashWiki *Smash attack* | [secondary] | "may be charged for up to **60 frames**, or 1 second" — stated for **all** games Melee→Ultimate | Melee/Brawl/4/Ult |
| SmashWiki *Project M* | [secondary] | "chargable for **59 frames** as opposed to 60" | PM |
| brawllib_rs (`~/Documents/Study/Rust/`, #614) | — | **no charge-cap constant** — only `ShieldCharge` (unrelated) and the `SmashSwingItemCharge` action *name* | — |

The 59 comes from **one** secondary, the SmashWiki *Project M* page, and it **contradicts
SmashWiki's own general *Smash attack* article**, which puts every game at 60. No primary was
found either way for PM specifically.

### Why no PM primary is reachable

The smash charge **cap is an engine-hardcoded global**, not per-move subaction script data — so
it is **out of brawllib_rs / rukaidata scope** (confirmed here: brawllib_rs exposes no such
constant; consistent with memory `rukaidata-engine-hardcoded-limit` and the #215/#222
air-dodge-velocity precedent). PM itself was never open-sourced (Nintendo C&D, 2015). The
Sammi-Husky *Project-Smash-Attacks* PSA changelog is **silent** on charge duration. Project+
(the open continuation) ships its engine changes as a build/codeset, not grep-able source with
this literal. **The only path to a PM primary is a DOL / live-memory dump of a PM ISO** — outside
this spike's box.

---

## Routing the outcome

Per the ticket's three options — upgrade provenance / revert to 60 / mark `⚠ undocumented` —
the two config values route differently:

| Value | Now (#599) | Finding | Recommended route |
|---|---|---|---|
| `SMASH_CHARGE_SCALE` | `1.3671` | **primary-confirmed** (meleelight, Melee lineage) | **Upgrade** the provenance note — add the meleelight primary citation alongside SmashWiki. Value unchanged. |
| `SMASH_CHARGE_FRAMES` | `59` | single-secondary, **primary-unconfirmed**, contradicted by SmashWiki's general article | **Keep 59, downgrade the note** to `⚠ primary-unconfirmed` (see rationale). Value unchanged. |

**Why keep 59 rather than revert to 60.** #599 established the reconciliation rule that a
**PM-specific** source outranks a **general** Melee/Brawl value applied to PM. This spike does
not overturn that rule — it only shows the PM-specific claim lacks a *primary* and disagrees with
a *general* (non-PM) article. Reverting to 60 would substitute a general value for the
PM-specific one — the exact move #599 corrected away from — and would cost another #588 combat
golden regen for a **1-frame, sub-1%-damage** difference. Lowest-churn, most internally
consistent route: **keep the value, mark the weak sourcing honestly.**

**Escalation note (parity vs. sourcing).** Whether a PM-faithful game should hold a
PM-specific-but-primary-unconfirmed 59 over a better-sourced 60 is ultimately a
**parity-vs-provenance design judgment**, not a pure research finding. This doc recommends keep-59;
if the maintainer prefers the better-sourced 60, that is a defensible `decision:`/designer call
(record as `TUNED`, not `FOUND`). Either way it is a **value-neutral provenance edit or a
1-line config change**, not new mechanics.

---

## Recommendation & follow-up

- **No config value changes in this ticket** (research only; both numbers stay as #599 set them).
- **Recommended follow-up (one DEV ticket, filed downstream on go-ahead):** in
  `pycats/combat/provenance.py`, (a) add the meleelight primary citation to the
  `SMASH_CHARGE_SCALE` row, and (b) annotate the `SMASH_CHARGE_FRAMES` row `⚠ primary-unconfirmed
  — single secondary (SmashWiki:Project_M), contradicted by SmashWiki:Smash_attack (60, all
  games); primary needs a PM DOL/memory dump`. Value-neutral; `test_tuning_provenance.py` stays
  green (no number changes).
- Update `smash-charge-hold.md` Q4's "primary" mislabel → "secondary" (fold into the same
  follow-up or #625's doc pass).

## Sources

- meleelight (Melee engine reimpl, **[primary]** literal) — `~/Documents/Study/JavaScript/meleelight/src/characters/*/moves/*SMASH.js` (clone #616)
- brawllib_rs (no charge-cap constant) — `~/Documents/Study/Rust/brawllib_rs/src/` (clone #614)
- SmashWiki — *Smash attack*: <https://www.ssbwiki.com/Smash_attack> (60 frames, all games; 1.3671× Melee / 1.4× Brawl+)
- SmashWiki — *Project M*: <https://www.ssbwiki.com/Project_M> (the sole "59 frames / x1.3671" source)
- Sammi-Husky *Project-Smash-Attacks* PSA changelog (silent on charge duration): <https://github.com/Sammi-Husky/Project-Smash-Attacks/blob/master/PSA/Changelog.txt>

## Refs

Spun out of #599 (charge-value corrections) via the #588 charged-fsmash golden. Companion:
`docs/pm-reference/smash-charge-hold.md` (#595), `docs/research-120-smash-units-and-sources.md`,
`docs/pm-reference/where-to-find-source-data.md` (#617/#625). Sourcing discipline: memories
`pm-parity-cite-primary-not-inference`, `rukaidata-engine-hardcoded-limit`.
