# Findings: PM/Melee smash-attack damage formula + how charge scales it (#426)

> The confirmed source of a smash attack's damage, the full-charge multiplier, and
> — the question this feeds — whether charging scales **damage only** (knockback
> rising through the formula) or **also** scales the knockback stats. Answer:
> **damage only.** Read-only research; feeds the **#423** fix.
>
> Sources (all consulted 2026-07-01):
> SmashWiki [Knockback](https://www.ssbwiki.com/Knockback),
> [Smash attack](https://www.ssbwiki.com/Smash_attack),
> [Charge](https://www.ssbwiki.com/Charge),
> [Forum:Charged Smash Damage Multiplier](https://www.ssbwiki.com/Forum:Charged_Smash_Damage_Multiplier);
> repo companions [`knockback-launch-physics-findings.md`](./knockback-launch-physics-findings.md)
> and [`open-source-smash-implementations.md`](./open-source-smash-implementations.md) (#224).
> Ticket #426; feeds #423; charge engine from #377 (slice 3b of #327); spec spike #328.
> PM canon = Project M 3.6 (Brawl-engine derived).

## TL;DR / recommendation for #423

**Charging scales the hitbox `damage` only.** Knockback rises as a *consequence*
(damage `d` and post-hit percent `p` both feed the KB formula) — the engine does
**not** separately multiply base knockback or knockback growth. Therefore
`combat/charge.py:scale_hitboxes` should scale **`damage` alone** and leave
`base_knockback` / `knockback_growth` untouched. pycats' current triple-scaling
makes a full-charge hit deliver **exactly 1.4× too much knockback** (derivation in
§4). `SMASH_CHARGE_SCALE = 1.4` and `SMASH_CHARGE_FRAMES = 60` are both correct for
PM and stay; only *what they multiply* changes.

## 1. Uncharged smash damage — source of truth

A smash attack's base damage is the per-hitbox `damage` value authored in its
subaction — the number rukaidata lists (e.g. Mario/Nalio f-smash base 17% clean).
There is no separate "smash damage formula": damage is data, knockback is computed
from it (§3). Multi-hit / sour-vs-sweet spots are just multiple hitboxes with their
own `damage`; charging scales each the same way.

- **Confidence: explicit.** SmashWiki Smash attack + Forum test both quote a move's
  authored base damage (Mario f-smash "base 17") and scale from it.

## 2. Charge multiplier + window

| Quantity | Value | pycats | Confidence |
|---|---|---|---|
| Full-charge multiplier (Brawl/PM) | **1.4×** (+40%) | `SMASH_CHARGE_SCALE = 1.4` ✓ | explicit (SmashWiki Charge/Smash attack; Forum empirical: Mario fsmash base 17 → 17×1.4 confirmed via Bowser to 119% over 5 hits) |
| Full-charge multiplier (Melee) | 1.3671× | — (PM is Brawl-era) | explicit; **not** the PM value — noted only to explain why 1.4 (not 1.3671) is right for pycats |
| Charge window | **60 frames = 1 s** | `SMASH_CHARGE_FRAMES = 60` ✓ | explicit (SmashWiki: "may be charged for up to 60 frames, or 1 second," all games) |

**PM uses 1.4×, not Melee's 1.3671×** — Project M is built on the Brawl engine, and
"since Brawl, smash attacks' damage multiplier [was] rounded from 1.3671× to 1.4×"
(SmashWiki Charge). So pycats' `1.4` is the faithful PM value.

## 3. The knockback formula — parity check (pycats is correct)

SmashWiki "Knockback" (Melee-onward, which PM inherits) gives verbatim:

```
KB = ( ( ( ( ( p/10 + p×d/20 ) × 200/(w+100) × 1.4 ) + 18 ) × s ) + b ) × r
```
- `p` = target percent **after** the hit's damage is added
- `d` = move damage · `w` = target weight (100 if weight-independent)
- `s` = knockback scaling ÷ 100 (KBG/100) · `b` = base knockback · `r` = misc (rage/etc., ignore)

pycats `combat/knockback.py:knockback()`:
```python
growth = ((percent/10.0) + (percent*damage/20.0)) * (200.0/(weight+100.0))
growth = (growth * 1.4) + 18.0
return (growth * (knockback_growth/100.0)) + base_knockback
```

**Exact match** — same `p×d/20` term (the #423 ticket's worry that it should be
`p×d/50` was mistaken; `/20` is the SmashWiki value), same `200/(w+100)`, same `×1.4`,
same `+18`, same `KBG/100` and `+BKB`. pycats correctly uses **post-hit** percent
(docstring: "post-hit percent"). No formula discrepancy. **Confidence: explicit.**

## 4. The crux — charge scales damage only (not BKB/KBG)

**Every source frames charge as a _damage_ multiplier**, and describes the knockback
rise as derivative, not a second multiplication:

- SmashWiki Charge: charging "increases their damage up to a maximum of 1.4×, **with a
  corresponding increase in knockback**." The word *corresponding* (vs. "and a 1.4×
  increase in knockback") signals KB rises **through** the damage, not by its own ×1.4.
- SmashWiki Smash attack states the multiplier as a **damage** figure only ("16% → 22.4%
  fully charged in Brawl" = 16×1.4); knockback is never given a separate multiplier.
- Forum:Charged Smash Damage Multiplier — the empirical confirmation is a **damage**
  measurement (Mario f-smash base 17, ×1.4, ×5 hits → 119%). It is titled and reasoned
  entirely as a *damage* multiplier.

Mechanistically this is sufficient: because `d` (and the resulting post-hit `p`) are
inputs to the KB formula (§3), multiplying **damage** already raises knockback — that
*is* the "corresponding increase." A separate ×1.4 on BKB and KBG would be double-counting.

**Why pycats over-scales — exact factor.** With damage scaled the same in both, let
`G = (p/10 + p·d_charged/20)·200/(w+100)·1.4 + 18` (the growth term at charged damage):

- PM-faithful (damage only): `KB_correct = G·(KBG/100) + BKB`
- pycats today (damage + BKB + KBG all ×1.4): `KB_pycats = G·(1.4·KBG/100) + 1.4·BKB = 1.4·(G·KBG/100 + BKB) = 1.4 · KB_correct`

So a full-charge smash in pycats delivers **exactly 1.4× the correct charged
knockback** — a spurious extra ×1.4 layered on top of the legitimate rise from 1.4×
damage. That over-scale is what KOs far too early (#423's symptom). Partial charge
over-scales by the same `charge_factor(c)` applied twice (once legitimately via damage,
once spuriously via BKB/KBG).

- **Confidence: inferred (strong).** No source states a *separate* KB multiplier
  exists; every source describes charge as a damage multiplier and KB as its
  consequence, which is exactly reproducible with the §3 formula. A DOL decompilation
  read (`doldecomp/melee`, the #224-catalogued route for engine-hardcoded behavior)
  would upgrade this to *explicit* if ever wanted, but the damage-only model is the
  community-standard one used by KB calculators and needs no separate-KB term to match
  observed behavior.

## 5. Partial-charge interpolation

pycats `charge_factor(c) = 1 + c·(SMASH_CHARGE_SCALE − 1)` — linear from ×1.0 (c=0)
to ×1.4 (c=1). SmashWiki does not state the interpolation *curve* explicitly, but a
linear per-frame ramp of the damage multiplier over the 60-frame window is the
community-standard model and matches the "builds up while held" description.

- **Confidence: inferred (medium).** Curve not explicitly sourced; linear is the
  standard assumption and is fine to keep. Once §4's fix lands (damage-only), the
  interpolation only affects **damage**, so any future curve refinement is localized.

## 6. Recommended change for #423 (no code here — #423 implements)

In `combat/charge.py:scale_hitboxes`, scale **`damage` only**:

```python
replace(hb, damage=hb.damage * factor)   # drop base_knockback= and knockback_growth=
```

- Leave `base_knockback` and `knockback_growth` untouched; KB rises via §3.
- Keep `charge_factor` / `SMASH_CHARGE_SCALE=1.4` / `SMASH_CHARGE_FRAMES=60` as-is.
- The stale comment at `config.py:86` ("damage/BKB/KBG scale by …") should be corrected
  to "damage scales by …" as part of the fix.
- Regression test (must be able-to-fail): a full-charge smash's KB should equal the
  formula's response to 1.4× damage — i.e. **~1/1.4 of today's** compounded value.
  Red under current triple-scaling, green after damage-only. (The #328 spike's
  "damage/BKB/KBG" line is superseded by this finding.)

## 7. Answers to the ticket's five questions

1. **Uncharged damage source** — per-hitbox authored `damage` (rukaidata value). §1. *explicit*
2. **Full-charge multiplier** — **1.4×** for PM (Brawl-era); 1.3671× is Melee-only. §2. *explicit*
3. **Interpolation** — linear ×1.0→×1.4 over 60 frames; curve not explicitly sourced but standard. §5. *inferred (medium)*
4. **Does charge scale KB independently?** — **No. Damage only; KB rises through the formula.** pycats' extra BKB/KBG scaling makes full-charge KB exactly 1.4× too high. §4. *inferred (strong)*
5. **KB-formula parity** — pycats matches SmashWiki verbatim (incl. `p×d/20`, post-hit `p`); no discrepancy. §3. *explicit*
