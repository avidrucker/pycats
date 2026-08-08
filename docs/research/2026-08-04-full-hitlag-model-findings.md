# Full hitlag model across scenarios — PM 3.6 canon vs pycats coverage (findings)

- **Ticket:** #825 (RESEARCH · area:combat · combat:engine) — spun out of #807 (auditing the
  "handles timing" claim). Feeds the eventual verification of ledger claim `PYC-C-002-GRAPE`
  (battle-mechanics topic) and scopes the downstream h/e/c-multiplier, shield-hitlag-parity,
  and clank-freeze slices (each filed one-at-a-time **after** this doc).
- **Agent:** cherry
- **Date:** 2026-08-04
- **Canon:** **Project M 3.6** (a Brawl mod; PM restored much Melee behavior). **Brawl is the
  labeled fallback baseline** where no PM-3.6-specific primary exists.
- **Primary sources (accessed 2026-08-04):** SmashWiki [*Hitlag*](https://www.ssbwiki.com/Hitlag)
  (formula, multipliers, cap, electric, crouch-cancel, shield). Reuses two in-repo primary digs:
  [invincible-hitlag #797](2026-07-20-pm-invincible-hitlag-findings.md) (meleelight engine +
  SmashWiki) and [clank #869](2026-07-28-pm36-clank-priority-findings.md) (SmashWiki *Priority* /
  *Rebound*).

## TL;DR

The **base damage formula** pycats ships — `min(30, floor(d·0.3846154 + 5))` — is the canon
Brawl/Smash-4 formula with **all three multipliers (h, e, c) pinned to 1** (#138). Canon is the
fuller expression `⌊⌊(d·0.3846154 + 5)·h·e⌋·c⌋`. Against the ticket's scenario list:

| Scenario | Verdict |
|---|---|
| **Damage-based base formula** (factor / base / cap) | **MATCH** — exact, incl. the 30-frame Brawl-onward cap. |
| **Clean / sour** (early/late-hit damage) | **MATCH by construction** — hitlag reads the *connecting box's* damage, so a weaker sour box gives less hitlag with no special handling. |
| **h — per-move hitlag multiplier** | **PARTIAL** — a `hitlag_mult` field is authored/serialized (ADR-0018 #1161, ADR-0021 #1150) but **not consumed**; `hitlag_frames` never multiplies by it. |
| **e — electric** | **ABSENT** — no electric attribute exists anywhere; the ×1.5 (floored, stacks with h) is unmodelled. |
| **c — crouch-cancel (hitlag)** | **ABSENT (hitlag side)** — crouch-cancel scales *knockback* ×0.67 (#135) but **not** hitlag; canon's 0.67× victim-only hitlag and the **victim-only 20-frame cap** are unmodelled. |
| **Shielding** — normal shield | **MATCH** — a held-shield hit freezes **both** fighters for the normal `hitlag_frames(dmg)`, then shieldstun ticks. |
| **Shielding** — perfect shield (powershield) | **ABSENT** — no powershield window exists; canon's attacker-only / defender-zero hitlag is unmodelled. |
| **Invincible defender** | **MATCH** — hit connects, **attacker-only** hitlag, defender zeroed (#797/#784, `Tangibility.INVINCIBLE`). |
| **Intangible defender** | **MATCH** — pass-through, **nobody** freezes (#797/#784, `INTANGIBLE` skip). |
| **Clank** | **ABSENT** — `_negate` ends the losing hitbox with **no** freeze; canon gives freeze = stronger attack's hitlag, then rebound (the `PYC-C-007` gap, #869 Finding D). |
| **Projectiles / disjoint / absorbed / transcendent** | **ABSENT-by-construction** — none authored in V1; disjoint hitlag is damage-driven (no special rule). |
| **Attacker-only vs both / SDI window** | both-freeze **MATCH**; **SDI/ASDI absent** (out of scope per ticket — scope note only). |

Two small **boundary divergences** in the base formula (both benign today, both a wiring note for
the h/e/c consumer): pycats returns **5 frames at d=0** where canon is **0** ("if the attack deals
no damage, hitlag is always zero"), and pycats gives the target hitlag regardless of knockback where
canon gates target hitlag on non-zero knockback.

---

## Verbatim canon (the primary quotes this doc rests on)

All from SmashWiki [*Hitlag*](https://www.ssbwiki.com/Hitlag), accessed 2026-08-04. **Game-of-record
labeled per quote.**

### The formula

> "In *Super Smash Bros. Brawl* and *Super Smash Bros. 4*, it is `⌊⌊(d * 0.3846154 + 5) * h * e⌋ * c⌋`."
> — **Game-of-record: Brawl & Smash 4.** This is the formula pycats' family belongs to.

> "In *Super Smash Bros. Melee*, it is `⌊⌊⌊d/3 + 3⌋ * e⌋ * c⌋`"
> — **Melee** (comparison only; note the different coefficients d/3 + 3 — this is what the
> meleelight quote in #797 shows, `Math.floor(damage * (1/3) + 3)`, and is **not** pycats' formula).

> "both the attacker and target are frozen in place for a certain number of frames"
> — universal. **Both sides freeze.**

### The three multipliers

> "**h**, hitlag multiplier; defined by every hitbox and defaults to 1×"

> "Attacks with the *electric* effect uniquely increase the amount of hitlag, multiplying its
> duration in frames by 1.5 (rounded down), which stacks with the hitlag multiplier that the move
> otherwise has." — the **e** term, ×1.5 floored, **stacks with h**.

> "**c**, crouch canceling; 0.666667× in *Melee* and 0.67× in *Brawl* onward (for the victim only
> in every game except *Ultimate*, where it is applied to both the attacker and victim)"
> — the **c** term: **0.67× Brawl-onward, victim-only.**

### The cap

> "Hitlag has a cap of 20 frames in *Melee*, and 30 frames (20 for the victim if crouch cancelling)
> from *Brawl* onward." — **30-frame cap Brawl-onward**, but **20 for the victim when crouch-cancelling**.

### Shield

> "Hitlag is also exaggerated if two attacks clash, or if an attack is *perfect shielded*; in the
> latter case, the attacker suffers from hitlag while the defender receives none."
> — **perfect shield (powershield)**: attacker-only hitlag, defender none. (Normal-shield hitlag is
> not given a separate rule on this page — it is the ordinary both-sides freeze; only the *perfect*
> shield is the attacker-only exception.)

### No-damage / no-knockback edges

> "If an attack deals no knockback, the target does not experience any hitlag."

> "If the attack deals no damage, hitlag is always zero."

### Reused from prior in-repo digs

- **Invincible / intangible** ([#797 doc](2026-07-20-pm-invincible-hitlag-findings.md)): SmashWiki
  *Invincibility* — "the attacker will still experience hitlag … the opponent will otherwise be
  unaffected"; SmashWiki *Intangibility* — intangible "does not cause hitlag to attackers since the
  intangible character is not physically hit." Corroborated in the meleelight engine state machine
  (attacker hitlag set before the invincible bail-out; intangible skips detection entirely).
- **Clank** ([#869 doc](2026-07-28-pm36-clank-priority-findings.md)): SmashWiki *Rebound* — "a
  rebounding character will suffer freeze frames equal to the hitlag of the **stronger** attack (by
  %)."

---

## Source tiering — read before citing

| Tier | Source | Gives | PM applicability |
|---|---|---|---|
| **Secondary, series-universal / Brawl-labeled** | SmashWiki *Hitlag* | the formula, h/e/c multipliers, cap, electric, crouch-cancel, perfect-shield rule | The formula block is **Brawl-labeled** (names Brawl explicitly); PM is a Brawl mod → **[inference — Brawl-baseline]**. PM never named. |
| **Primary reimplementation (Melee)** | meleelight (local #616, via #797) | the engine hit-resolution ordering: attacker-hitlag-on-connect, invincible bail, intangible detection-skip | Melee→PM `[inference]`; used only for the invuln/intangible scenario, where SmashWiki agrees. |
| **PM-specific (absence of override)** | Project-M-CC 3.6 codeset (local #664, via #797) | no Gecko code touches hitlag/invincibility | consistent with PM inheriting the lineage formula unchanged. |

**Why the datamine can't promote this to a PM `FOUND`.** The hitlag duration rule is an **engine
global**, not a per-move subaction script; brawllib_rs / rukaidata / OpenSA expose only scripted
per-move data (the `hitlag_mult` per-box value is authored data, *not* the global formula). No
PM-3.6 primary for the formula was reachable; the value pycats ships is Brawl-labeled on SmashWiki
and PM-inherited by inference — the **same fallback-ladder** as the #869 clank 9% window and the
#874 tap-jump baseline.

---

## The PM 3.6 hitlag model, assembled (each figure basis-labeled)

Canon duration (per connecting hitbox): **`H = ⌊⌊(d · 0.3846154 + 5) · h · e⌋ · c⌋`**, then capped.

| Term / rule | Canon value | Game-of-record | PM 3.6 basis |
|---|---|---|---|
| damage coefficient | 0.3846154 (= 1/2.6) | Brawl / Smash 4 (labeled) | **[inference — Brawl-baseline]** |
| base | +5 | Brawl / Smash 4 | Brawl-baseline |
| **h** per-hitbox multiplier | default 1×, per hitbox | Brawl / Smash 4 | Brawl-baseline |
| **e** electric | ×1.5 (floored), **stacks with h** | universal (Brawl formula) | Brawl-baseline |
| **c** crouch-cancel | ×0.67, **victim only** | Brawl onward | Brawl-baseline |
| cap | 30 frames | Brawl onward | Brawl-baseline |
| cap — crouch-cancelling victim | **20 frames** (victim side) | Brawl onward | Brawl-baseline |
| both sides freeze | attacker + target | universal | inherited |
| d = 0 → hitlag | **0** ("always zero") | universal | inherited |
| no knockback → target hitlag | **0** for the target | universal | inherited |
| perfect shield (powershield) | **attacker-only** hitlag, defender none | universal | inherited |
| clank / clash | freeze = **stronger** attack's hitlag, both rebound in-window | Melee-family (via #869) | Brawl-baseline |
| invincible defender | hit connects, **attacker-only** hitlag, defender zeroed | universal + meleelight (via #797) | Brawl-baseline / `[inference]` |
| intangible defender | pass-through, **nobody** freezes | universal + meleelight (via #797) | Brawl-baseline / `[inference]` |

**Nested-floor note (matters once h/e/c are wired).** Canon floors **twice**: an inner floor after
`·h·e`, then an outer floor after `·c`. pycats' single `floor(d·f + 5)` is byte-identical **only
while h=e=c=1** (the inner and outer floors collapse onto the already-integer base). The downstream
consumer must reproduce the double floor, not `floor(base · h · e · c)`.

---

## pycats coverage table (match / partial / absent — pinned)

Code as of this worktree (`br-cherry/pycats-825…`, base `main`). Landmarks are function/file, not
line numbers.

| Canon rule | pycats behavior | Verdict | Where |
|---|---|---|---|
| Base formula `d·0.3846154 + 5`, cap 30 | `min(30, floor(d·0.3846154 + 5))` | **MATCH** | `combat/knockback.py::hitlag_frames`; consts `config/physics.py` `HITLAG_DAMAGE_FACTOR/BASE/CAP`; pins `combat/provenance.py` (#138, `FOUND`) |
| Clean/sour = different % per box → different hitlag | hitlag reads `atk.damage` = the connecting box's damage (`hit_resolution` sets `atk.damage = hit_box.damage` before `receive_hit`) | **MATCH (by construction)** | `systems/hit_resolution.py::process_hits` → `fighter.receive_hit` |
| **h** per-hitbox hitlag multiplier | `Hitbox.hitlag_mult` authored + serialized, defaults 1.0; **never read** by `hitlag_frames` | **PARTIAL** (slot exists, no consumer) | `combat/data.py::Hitbox.hitlag_mult` (ADR-0018 #1161 / ADR-0021 #1150); consumer wiring is an explicit downstream DEV |
| **e** electric ×1.5 (floored, stacks) | no electric attribute anywhere; no ×1.5 path | **ABSENT** | — (only a docstring mention in `hitlag_frames`) |
| **c** crouch-cancel hitlag ×0.67, victim-only, victim cap 20 | crouch scales **knockback** ×`CROUCH_CANCEL_FACTOR`=0.67; hitlag untouched, both sides get full `hitlag_frames(dmg)`, cap 30 both | **ABSENT (hitlag side)** — KB side present (#135) | `fighter.receive_hit` (`if is_crouching: kb *= CROUCH_CANCEL_FACTOR`, comment: "Hitlag scaling (the 'c' multiplier) stays deferred") |
| Both attacker + target freeze | on a clean hit both `self.hitlag_timer` and `atk.owner.fighter.hitlag_timer` set to `hl` | **MATCH** | `fighter.receive_hit` |
| Normal shield → hitlag both sides + shieldstun | held-shield branch sets `hitlag_frames(dmg)` on both, then `shieldstun_frames(dmg)` (floor(dmg·0.345)) | **MATCH** | `fighter.receive_hit` (shield branch); `combat/shield.py::shieldstun_frames` (#140) |
| Perfect shield (powershield) → attacker-only hitlag | no powershield/parry window exists | **ABSENT** | — |
| Invincible defender → attacker-only hitlag, defender zeroed | `receive_hit_invincible` sets only `atk.owner.fighter.hitlag_timer` | **MATCH** | `fighter.receive_hit_invincible`; `combat/tangibility.py` `INVINCIBLE` (#797/#784/#506) |
| Intangible defender → pass-through, nobody freezes | `INTANGIBLE` → detection skipped, no `receive_hit` | **MATCH** | `hit_resolution.process_hits` tangibility gate; `combat/tangibility.py` `INTANGIBLE` (#797/#784) |
| Clank → freeze = stronger attack's hitlag | `_negate` ends the losing hitbox; no freeze, no rebound | **ABSENT** = `PYC-C-007` gap | `systems/hit_resolution.py::_negate` / `_resolve_clanks` (#38; #869 Finding D) |
| d = 0 → hitlag 0 | `hitlag_frames(0)` = **5** | **DIVERGENCE (boundary)** — benign; no 0-damage box authored | `hitlag_frames` |
| no knockback → target no hitlag | target always gets `hl` regardless of KB | **DIVERGENCE (boundary)** — benign; every authored hit has KB | `fighter.receive_hit` |
| Projectile / disjoint / absorbed / transcendent hitlag | no projectiles/specials/absorb/transcendent authored; disjoint hitlag is damage-driven (no special rule) | **ABSENT-by-construction** | — |
| SDI / ASDI during victim hitlag | `Player.update` returns early while `hitlag_timer > 0` (position held, hitstun paused, move clock paused); no directional-input read in that window | **ABSENT** (out of scope per ticket) | `entities/player.py` update early-return (#138) |

---

## Findings (downstream follow-up candidates — filed one-at-a-time, not in this doc)

Ordered roughly by the ticket's own downstream sequencing. **No implementation, no value change,
and no provenance edit in this pass** (RULES "Changing values" / "Suggest, don't act").

### Finding A — `h` (per-hitbox hitlag multiplier): field authored, consumer unwired
`Hitbox.hitlag_mult` (default 1.0) is stored + serialized but `hitlag_frames` ignores it. Wiring it
is the natural first h/e/c slice: multiply inside the **inner** floor (`floor((d·f+5)·h)`), keep the
cap. Golden-safe until a move authors a non-1.0 value. This is the DEV the `data.py` docstring
already forward-references ("Consumer wiring (→ hitlag_frames) is a downstream DEV").

### Finding B — `e` (electric): attribute + ×1.5 unmodelled
No electric concept exists. A downstream slice needs (i) an `electric` per-hitbox flag on `Hitbox`,
(ii) the ×1.5 floored term **stacking with h** inside the inner floor. Gated behind Finding A (same
inner-floor seam). No authored move is electric yet, so this is additive/golden-safe.

### Finding C — `c` (crouch-cancel hitlag): hitlag side + victim-only asymmetry + 20-cap
pycats crouch-cancel scales only knockback. Canon also scales the **victim's** hitlag ×0.67 and caps
the **victim** at 20 frames (attacker keeps full hitlag + 30 cap) — an attacker/victim asymmetry
pycats' symmetric `hl` for both sides does not currently express. A crouch-cancel-hitlag slice must
split the two sides' hitlag, not reuse one `hl`.

### Finding D — perfect shield (powershield): attacker-only hitlag path absent
No powershield window exists (normal shield is modelled and correct). Whenever powershield is
scoped, its hitlag rule is **attacker-only, defender none** — structurally the same shape as the
`INVINCIBLE` branch (`receive_hit_invincible`), which is a ready template.

### Finding E — clank freeze frames (`PYC-C-007`, from #869 Finding D)
`_negate` gives the clank no freeze. Canon: both fighters freeze for the **stronger** attack's
hitlag, then rebound (aerials can't rebound). This doc pins the freeze target (`= hitlag_frames` of
the stronger box's damage); the rebound *animation* is a separate DESIGN slice. #869 explicitly
gated this "behind the hitlag work (#825 area)" — this doc is that gate.

### Finding F — base-formula boundary divergences (d=0, no-knockback)
`hitlag_frames(0)` returns 5 (canon 0), and the target always freezes even on a zero-knockback hit
(canon: no KB → no target hitlag). Both are unreachable by any authored move today. Worth a guard
(and a regression test) *if and when* a 0-damage or pure-set-0-KB box is authored — otherwise a
labeled note on `hitlag_frames`. Lowest priority.

### Finding G — `PYC-C-002-GRAPE` verification input
This doc supplies the canon side the ledger claim's verification needs: the claim pins pycats'
current single-slice hitlag (h=e=c=1). Verdict for that claim is **TRUE-with-scope** — pycats
matches the canon **base** formula exactly, but the full canon model has three multipliers + a
perfect-shield/clank freeze that pycats does not yet apply. The claim is accurate about *what pycats
does*; this doc enumerates *what canon adds on top*.

---

## Out of scope (per ticket)

No implementation; no `provenance.py` / `pm-reference` edits; no value re-tag; SDI/ASDI is a scope
note only. Each finding above is a candidate follow-up filed **one at a time** downstream of this
doc, on an explicit go-ahead.

## Sources

Verified 2026-08-04. Code cited by named symbol + file path (line numbers drift); local clones per
`docs/pm-reference/where-to-find-source-data.md`.

| Source | Tier | Used for |
|---|---|---|
| SmashWiki — [*Hitlag*](https://www.ssbwiki.com/Hitlag) | secondary, Brawl-labeled / universal | formula, h/e/c, cap (30; victim-20 CC), electric ×1.5-stacks, perfect-shield attacker-only, d=0 / no-KB edges, both-freeze |
| in-repo [invincible-hitlag #797](2026-07-20-pm-invincible-hitlag-findings.md) | primary reimpl (meleelight) + secondary | invincible attacker-only / intangible nobody-freezes; engine ordering + precedence |
| in-repo [clank #869](2026-07-28-pm36-clank-priority-findings.md) | secondary (SmashWiki *Priority*/*Rebound*) | clank freeze = stronger attack's hitlag; the `PYC-C-007` gap |
| pycats `combat/knockback.py`, `combat/shield.py`, `combat/tangibility.py`, `combat/data.py`, `systems/hit_resolution.py`, `entities/fighter.py`, `config/physics.py`, `combat/provenance.py` | in-repo (audited) | the "what pycats does" column |

## Cross-refs

Parent audit #807 (the "handles timing" claim); ledger claim `PYC-C-002-GRAPE` (this doc feeds its
verification). Downstream candidates (file one-at-a-time on go-ahead): h-wiring (Finding A),
electric (B), crouch-cancel hitlag (C), powershield (D), clank freeze `PYC-C-007` (E), boundary
guards (F). Related canon: #797 (invuln/intangible hitlag), #869 (clank), #138 (hitlag base slice),
#135 (crouch-cancel knockback), #140 (shieldstun). Memory:
[[pm-parity-cite-primary-not-inference]], [[grounded-speeds-projectplus-not-pm36]],
[[pm36-canonical-reference]].
