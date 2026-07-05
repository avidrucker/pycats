# Pass B provenance-coverage audit — what the #233 registry doesn't yet cover

**Ticket:** #580 (research; Pass B slice 1 of umbrella #451). **Role:** RESEARCH. **Date:** 2026-07-05. **Agent:** BANANA.
**Method:** three parallel read-only catalogues (per-character move data · config-constant delta · render/collision geometry), each value then confirmed against the code; sourcing/classification per RULES → "Changing values" and the #530 value-sourcing routing.

---

## TL;DR — the recommendation

Pass B ("extend the #233 registry beyond the ~34 config scalars") should extend it to the **config gameplay scalars and the two mis-shelved collision constants — NOT to the ~900 per-character move-data values.**

- **Config scalars (30 in play): the registry's natural home.** They are bare literals with no inline context, exactly what a keyed sidecar + drift-guard is for. 20 are gameplay-tuning; ~10 are ambiguous (need a human scope call). This is the tractable, high-ROI extension.
- **Per-character move data (~900 values across 4 cats / 38 moves / 117 hitboxes): keep inline.** It is **already densely sourced inline** (PM3.6 move names + rukaidata citations + issue refs on nearly every move; positions `⚠`-approximated by design). Mirroring it into a machine registry would be ~900 rows of noise plus a drift-guard nightmare (117 hitboxes re-checked against live `FighterData`) — the exact "marker soup / provenance noise" the registry design warns against. Its provenance layer already exists (Axis A markers + the char-spec docs). Recommend **structure/greppability**, not duplication.
- **Render: mostly excluded (correct). Two exceptions.** Hit/whiff runs on resolved circles, not render rects, so colors/pads/HUD/tail are genuinely cosmetic. But `PLAYER_SIZE` is a **collision** constant mis-labelled render, and `ATTACK_SIZE` quietly sets the projectile despawn margin.

This keeps the registry's "no provenance noise" invariant intact while closing the real gaps. Follow-up DEV/decision slices are routed per #530 in the last section.

---

## Category 2 (config) — the registry's natural extension

The registry covers 38 `config.py` scalars. Of the **137 uncovered** UPPER_CASE constants: **20 gameplay-tuning**, **10 ambiguous**, **107 excluded-by-design** (platform geometry, colors, fonts, HUD/menu layout, tail-physics, cat-feature render — the registry docstring already scopes these out).

### 2a — gameplay-tuning candidates (registry-ready), with candidate status

| constant | value | candidate status | basis / note |
|---|---|---|---|
| `PX_PER_UNIT` | 5.4 | **FOUND-derivation / anchor** | **strongest miss.** The ADR-0003 derivation-guard re-evaluates `round(units*PX_PER_UNIT)` against config, and `DODGE_AIR_SPEED`'s registered derivation depends on it — yet the base itself is unregistered. (#120/#195) |
| `SMASH_CHARGE_FRAMES` | 60 | **FOUND** | "PM/Melee 60 frames = 1s (confirmed #426, SmashWiki)" — cited in-comment. |
| `SMASH_CHARGE_SCALE` | 1.4 | **FOUND** | "PM (Brawl-era) 1.4 (Melee 1.3671; confirmed #426)." |
| `DASH_SPEED` | 8 | **FOUND-derivation** | "≈Mario dash 1.5u ×5.4 ≈ 8.1px." |
| `MAX_JUMPS` | 2 | **FOUND** | single + double = Mario/PM default jump count. |
| `GROUND_FRICTION` | 0.5 | GUESS/TUNED | "1.0=ice; 0.0=instant stop" — no cited canon. |
| `AIR_FRICTION` | 0.85 | GUESS/TUNED | physics knob, uncited. |
| `PROJECTILE_GRAVITY` | 0.5 | **GUESS** (⚠) | block flagged "⚠ GUESS tuning starting points" (#266/#425). |
| `PROJECTILE_RESTITUTION` | 0.6 | **GUESS** (⚠) | same block. |
| `PROJECTILE_MAX_BOUNCES` | 3 | **GUESS** (⚠) | same block (mirrors `attack.py:185` `⚠ GUESS`). |
| `DASH_DURATION` | 12 | GUESS (⚠) | "⚠ tuning start." |
| `DOUBLE_TAP_WINDOW` | 8 | **decision-pending** | already a live decision **#491** (from #407/#489) — do not re-litigate here. |
| `SMASH` angles `FSMASH_ANGLE_UP`/`_DOWN` | 50 / 330 | TUNED | pycats smash-angle design. |
| `HURT_TIME` | 12 | GUESS/TUNED | hitstun-adjacent timer, uncited. |
| `LEDGE_HANG_FRAMES` | 120 | TUNED | "~2s auto-release timeout" — pycats rule. |
| `LEDGE_REGRAB_LOCKOUT_FRAMES` | 30 | TUNED | pycats regrab suppression. |
| `PLAYER_ATTACK_DURATION` | 12 | TUNED | default attack window. |
| `INITIAL_LIVES` | 3 | TUNED (ruleset) | stock count — a match rule, not a PM physics value. |
| `RESPAWN_DELAY_FRAMES` | 2·FPS | TUNED (ruleset) | "2s freeze before respawn." |

> Confirm-as-touched: `PX_PER_UNIT` absence verified against `TUNING_CONSTANT_NAMES` (38-name set); `SMASH_CHARGE_*` #426 citations present in-comment; `PROJECTILE_*` `⚠ GUESS` markers present.

### 2b — ambiguous (need a human scope ruling before registering)

`SCREEN_WIDTH` 960 · `SCREEN_HEIGHT` 540 · `FPS` 60 · `MAX_SHIELD_RADIUS` 40 · `MIN_SHIELD_RADIUS` 10 · `LEDGE_CATCH_W` 24 · `LEDGE_CATCH_H` 64 · `ATTACK_SIZE` (30,18) · `PLAYER_SIZE` (40,60) · `BLAST_PADDING` 50.

These sit on the fence: `SCREEN_WIDTH`/`FPS` are *sourcing context* the registry's own derivations cite ("scaled to the 960px stage"; "60 FPS maps 1:1") rather than tuning values themselves; `PLAYER_SIZE`/`ATTACK_SIZE`/shield/ledge-catch are collision/region sizes (see Category 3). Recommend a single `decision` ruling on which of these the registry should own.

---

## Category 3 (render) — resolving the "render in-scope" tension

The umbrella lists "render" under Pass B, but the registry excludes render as noise. **Hit/whiff detection runs on resolved circles (`combat/geometry.resolve_circle` + `circles_overlap`), not on any render rect** (`attack.py:124`, `render_battle.py:863` both say "combat uses `a.resolved`, not this"). So the drawn attack rect governs nothing a fighter can hit. Verdict: **the exclusion is correct for the bulk; two constants are genuinely collision, not render:**

| constant | value | reality | recommendation |
|---|---|---|---|
| `PLAYER_SIZE` | (40,60) | the **default collision box** (`fighter.py:96` `stand_size or PLAYER_SIZE`); height feeds jostle vertical-overlap | **reclassify as a collision constant → registry candidate** (it is not render) |
| `ATTACK_SIZE` | (30,18) | comment says "render-only," but `attack.py:153,217` uses its width as the **projectile despawn bound** | document the coupling as a note; minor — despawn only |
| everything else | — | colors, `_BODY_PAD_*`, shield bubble, dizzy stars, eyes/ears/whiskers/tail, HUD/menu fonts | **keep excluded** (purely visual; verified not shared with collision) |

> Confirm-as-touched: `PLAYER_SIZE` collision default verified at `fighter.py:96`; `ATTACK_SIZE` despawn use verified at `attack.py:153,217`; also found `attack.py:185 max_bounces` carrying `⚠ GUESS`.

---

## Category 1 (per-character move data) — why it stays inline

Catalogued across `default_cat.py`, `nalio_cat.py` (Mario), `birky_cat.py` (Kirby), `narz_cat.py` (Marth), `body_zones.py`:

- **38 moves · 117 hitboxes · ~900 individual authored values**: per-hitbox `damage/angle/BKB/KBG` (~468) + positions `dx/dy` (234, **all `⚠`-approximated**) + timing (114 move-level + ~64 per-hitbox windows) + character-level scalars (~30: weights 100/70/87, gravities, jump/fall/move, jump counts, hurtbox/crouch/prone geometry) + optional `WDSK`/`rehit_rate`/`projectile_*`/`chargeable`.
- **Provenance already lives inline and is greppable:** verbatim `Source: Project M 3.6 <Mario|Kirby|Marth>`; rukaidata move names (`Attack11`, `AttackLw3`, `AttackAirF`, `AttackS4S`, `SpecialN`, …); dense issue refs; and Axis-A `⚠`/`🔬` markers where a value is a guess. Positions are `⚠`-approximated **by design** (rukaidata offsets are bone-relative; pycats models no skeleton — the #120 convention, marked once per file).
- **Explicitly-flagged guesses** (not sourced): Nalio fireball `projectile_speed=10` (`⚠🔬` GUESS, #192/#195 pending); Nalio/Birky dair `rehit_rate` (`⚠` playtest); Nalio `usmash recovery=33` + late angle 259 (`⚠` playtest, community frame data off-script); Nalio `nair angle 45` (literal placeholder for the 361 sentinel); **all Narz moves** (`⚠🔬` playtest / rukaidata-confirm-later, #290 v1); Default `attack` base_knockback + reach dx=46 (`⚠`); Birky dy zones (`⚠` ADR-0003).

**Scope boundary (candid):** this audit confirms each cited source *exists, is correct-shaped, and is greppable* — it does **not** independently re-derive all ~900 values from primary sources (that is a separate, per-value research act under #530, and unnecessary while the inline citation stands). Per the PM-parity primary-citation rule, nothing here is upgraded from "cited inline" to "independently primary-verified."

**Why not mirror into the registry:** the registry's worth is turning a *bare literal* into a sourced row. Character values are the opposite — already annotated. ~900 mirror-rows + a drift-guard over 117 live hitboxes would be pure noise against the registry's stated "no provenance noise" invariant. If machine-tracking of character data is wanted later, it is its own design ticket (a `MoveData`-keyed guard), **not** part of this registry extension.

---

## Coverage-strategy decision (the design question this audit answers)

**Recommended: option (c) hybrid, scoped tight.**
- **Registry (Pass B DEV):** extend `combat/provenance.py` + `TUNING_CONSTANT_NAMES` + the drift-guard to the **config gameplay scalars** (2a) and the reclassified **collision** constant `PLAYER_SIZE`. This is bounded (~20–30 rows), high-value, and matches the registry's design intent.
- **Inline (no registry work):** per-character move data keeps its existing inline citations + Axis-A markers as its provenance home.
- **Human ruling (decision):** the 10 ambiguous constants (2b) — which belong in the registry vs stay excluded.

Rejected: (a) full parallel `MoveData` registry — ~900 rows, drift-guard nightmare, violates "no provenance noise"; (b) inline-only for everything — leaves the bare config literals unsourced, the exact gap #233 exists to close.

---

## Follow-up slices (filed one at a time, per research-epic discipline; routed per #530)

1. **DEV — register the already-sourced config scalars (basis (1), FOUND).** `PX_PER_UNIT`, `SMASH_CHARGE_FRAMES`, `SMASH_CHARGE_SCALE`, `DASH_SPEED`, `MAX_JUMPS` — rows + `TUNING_CONSTANT_NAMES` + drift-guard + citation in each comment. Ready now (findings exist). ≤30–60m.
2. **DEV — register the tuning/guessed config scalars (GUESS/TUNED).** `PROJECTILE_*`, `DASH_DURATION`, `GROUND_FRICTION`, `AIR_FRICTION`, `HURT_TIME`, `FSMASH_ANGLE_*`, `LEDGE_HANG_FRAMES`, `LEDGE_REGRAB_LOCKOUT_FRAMES`, `PLAYER_ATTACK_DURATION`, `INITIAL_LIVES`, `RESPAWN_DELAY_FRAMES` — candid GUESS/TUNED status, no fabricated sourcing.
3. **decision (humans-only) — the 10 ambiguous constants (2b) + `PLAYER_SIZE`/`ATTACK_SIZE` collision reclassification.** Which does the registry own? (`DOUBLE_TAP_WINDOW` is already #491 — excluded from this decision.)
4. *(optional, out of Pass B)* **design ticket — machine-tracked per-move provenance**, only if the inline layer proves insufficient. Not recommended now.

Pass C (parity-light generator) then renders `🟢/🟡/🔴` from whatever B ends up covering. Umbrella #451's Pass B box stays open until slices 1–2 (at least) land.

## Refs
Umbrella **#451** (Pass B). Registry **#233** / ADR-0003 (`combat/provenance.py`). Value-sourcing routing **#530** (`docs/research/2026-07-05-value-sourcing-classification.md`). Pass A audit precedent **#454**. Legend **#452** (`docs/parity-labeling-legend.md`). Unit convention #120/#195/#384. Char specs: #119 (Mario→Nalio), #229 (Kirby→Birky), #290 (Marth→Narz). PM canon = Project M 3.6.
