# Smash charge & hold — PM reference (research #595)

**Question (from #595):** In Project M, once a smash is *fully charged*, can it be **held**
(indefinitely, or up to some max), and does any such cap vary by character? Surfaced while
building the #588 charged-fsmash combat golden, where pycats **auto-fires** a smash the frame
it reaches full charge.

**Verdict in one line:** In PM you **cannot hold** a fully-charged smash — it auto-releases at
the charge cap. Hold-at-full-charge is an **Ultimate-exclusive** feature. pycats' auto-fire is
therefore already faithful on the *hold* question; only two *charge values* diverge from PM.

Citation discipline (per RULES → PM parity): primary quotes below; PM-specific application of
the Ultimate-exclusivity fact is labelled **[inference]** where PM's own page is silent.

---

## Findings

### Q1 — Is a fully-charged smash holdable? → **No, not in PM.**

SmashWiki *Smash attack* (primary), verbatim:
- "A smash attack may be charged for up to 60 frames, or 1 second."
- Ultimate adds the hold: charged smashes "can also be held for an additional 2 seconds after
  that, not increasing their power any further."
- "Melee, Brawl, and SSB4 all use the standard 60-frame charge with **no hold mechanic** — this
  feature is exclusive to Ultimate."

**[inference, strong]** Project M is a **Brawl** mod and predates Ultimate, so it inherits
Brawl's behavior: the smash **auto-releases** at the charge cap; there is no "hold at full
charge" state. SmashWiki's *Project M* page documents PM's charge tweaks (below) but does **not**
mention a hold mechanic — consistent with there being none.

### Q2 — Max hold time? → **N/A for PM** (fires at the cap).

There is no hold window in PM to bound. (For contrast, Ultimate's hold is +2 s after full charge;
Min Min is the outlier at 30 frames. None of this applies to PM.)

### Q3 — Per-character variance? → **None in PM.**

The only per-character charge/hold variance in the series is **Ultimate-only**: Bayonetta,
Mega Man, Ness, Olimar, and Villager use a 1.2× multiplier with a 1-second hold; Min Min holds
for 30 frames. PM has a single global charge rule (below) — no per-character charge/hold data.

### Q4 — Charge ramp (context). → **PM = 59 frames; multiplier 1.3671×.**

SmashWiki *Project M* (primary), verbatim:
> "Though a barely noticeable change, smash attacks are now chargable for **59 frames** as opposed
> to 60, and a fully charged smash deals **x1.3671** of the uncharged amount."

So PM restored **Melee's** full-charge multiplier (1.3671×, vs Brawl-onward's 1.4×) and shaved
the ramp to 59 frames.

### Q5 — pycats gap.

| Aspect | pycats today | PM (sourced) | Faithful? |
|---|---|---|---|
| Hold at full charge | none — auto-fires at cap (`fighter_input.py`, full-charge auto-release) | none (auto-release) | ✅ **yes** |
| Charge ramp | `SMASH_CHARGE_FRAMES = 59` | **59** frames | ✅ **yes** (corrected in #599) |
| Full-charge multiplier | `SMASH_CHARGE_SCALE = 1.3671` | **1.3671** (Melee, restored in PM) | ✅ **yes** (corrected in #599) |

`SMASH_CHARGE_FRAMES` / `SMASH_CHARGE_SCALE` carry `Provenance` rows (`pycats/combat/provenance.py`,
ADR-0003 / #233); **#599** applied both corrections (values + `FOUND` rows re-cited to `SmashWiki:Project_M`)
and regenerated the #588 combat golden.

---

## Recommendation

- **Hold mechanic:** **KEEP** pycats' auto-fire-at-full-charge — it is PM-faithful. Do **not** add
  a "hold at full charge" state; that would import an Ultimate-only mechanic PM never had. No DEV
  ticket for the hold question.
- **Charge values:** two concrete, sourced discrepancies (ramp 60→**59**, multiplier
  1.4→**1.3671**) were corrected in DEV **#599** — both now `FOUND` values (primary-sourced from
  `SmashWiki:Project_M`), superseding #581's base-game/Brawl rows. Not game-feel guesses.

## Sources

- SmashWiki — *Smash attack*: <https://www.ssbwiki.com/Smash_attack>
- SmashWiki — *Charge*: <https://www.ssbwiki.com/Charge> (corroborates the 1.4× / 1.3671×-in-Melee lineage)
- SmashWiki — *Project M*: <https://www.ssbwiki.com/Project_M>
