# PM 3.6 hitlag when an attack connects with an INVINCIBLE defender — findings (#797)

> **Question owner:** #797 (child of epic **#772**). Feeds decision **#784** (Q4a — the
> `INVINCIBLE` combat-branch behavior) and DEV **#506** (respawn invincibility window).
> Canon = **Project M 3.6** (Brawl lineage; PM restored much Melee behavior). Compiled 2026-07-20.
>
> **One-line answer:** when an attack connects with an invincible defender, **the attacker takes
> hitlag; the invincible defender takes none** (nor damage/knockback/hitstun). Attacker-only. The
> premise holds: invincibility (hit *connects*, attacker freezes) is a **mechanically distinct
> engine state** from intangibility (hit *passes through*, nobody freezes) — confirmed not just in
> the definitional wiki but in the **actual state machine of a faithful Melee reimplementation**.

## Source tiering — read this before citing

Two independent lineage sources agree, plus a PM-specific absence-of-override. **None is a PM 3.6
primary quote** — that does not exist at a reachable tier (see "Residual gap") — but the
triangulation is much stronger than a single secondary wiki:

| Tier | Source | What it gives | PM applicability |
|---|---|---|---|
| **Primary reimplementation (Melee)** | **meleelight** — faithful Melee engine reimpl in JS (`~/Documents/Study/JavaScript/meleelight/`, local clone #616) | The **actual engine state machine + hit-resolution code**: distinct intangible/invincible states, the detection gate, attacker-hitlag-on-connect, the precedence order, respawn=invincibility | PM **restored much Melee behavior**; this immunity/hitlag model is a shared-lineage engine mechanic. Melee→PM is an **`[inference]`**, but grounded in the literal code the lineage shares. |
| **Secondary — series-universal** | SmashWiki *Invincibility* / *Hitlag* / *Intangibility* (verified 2026-07-20; the load-bearing sentences sit in **series-universal** sections, no game qualifier, PM never named) | The definitional rule, in words | Series-wide (incl. Brawl, PM's base); PM applicability is `[inference]`. |
| **PM-specific — absence of override** | **Project-M-CC** 3.6 codeset (text, local clone #664) | `grep -ni "invincib\|intangib\|hitlag\|invuln"` over `codes-cc-3_6.txt` → **no hits** | PM added **no Gecko code** touching these mechanics ⇒ consistent with inheriting the lineage engine model unchanged. |

**Why brawllib_rs / rukaidata / OpenSA can't promote this further.** The hitlag-application rule is
an **engine global**, not a per-move subaction script; brawllib_rs / rukaidata expose only scripted
per-move data (#215/#222; `DODGE_AIR_SPEED`; [[rukaidata-engine-hardcoded-limit]]), and OpenSA holds
Brawl *action scripts*, not the global rule. meleelight is the reachable source that actually
implements the engine logic — which is why the local dig paid off where the datamine structurally
could not.

**Residual gap (stated plainly):** no source read here is a **PM-3.6 primary** for this rule. The
strongest is a **Melee reimplementation** (meleelight) plus the PM-restores-Melee inference and the
PM-codeset absence-of-override. A literal PM primary would require the Brawl engine binary or a
Project+ engine-source read of the hit-resolution branch — not attempted (out of the 45m box; the
triangulation above makes it low-value).

---

## Q1 — Does the **attacker** undergo hitlag when hitting an invincible defender? → **YES**

**Engine (meleelight, `executeRegularHit` in `physics/hitDetection.js`):** on any non-phantom,
non-stage hit the attacker's hitlag is set **unconditionally, before** the victim's immunity is
consulted:

```js
player[a].hit.hitlag = Math.floor(damage * (1 / 3) + 3);   // attacker (a) hitlag — set first
...
// if invincible
if (player[v].phys.hurtboxState > 0 && !isThrow) { bluntHit(a, h); return; }   // victim (v) side bails out
```

The attacker's freeze is committed the moment the hit is resolved; the invincible branch only skips
the **victim's** processing. **Secondary corroboration** — SmashWiki *Invincibility* (series-universal):
> "Attacks will connect, but will not deal damage, knockback, or hitstun, though the attacker will
> still experience hitlag."

SmashWiki *Hitlag* (series-universal):
> "Hitlag affects the attacker as long as the attack connects, even if it deals no damage as a
> result of hitting opponents with invincibility."

**Answer: the attacker freezes for the normal hitlag duration.**

## Q2 — Does the **invincible defender** also undergo hitlag? → **NO**

**Engine (meleelight):** in `executeRegularHit`, the victim's hitlag (`player[v].hit.hitlag`),
knockback (`getKnockback` → `player[v].hit.knockback`), and percent are all set **after** the
invincible bail-out — so an invincible victim reaches none of them; only the attacker's hitlag
(set earlier) stands. **Secondary corroboration** — SmashWiki *Hitlag* (series-universal):
> "If an attack deals no knockback, the target does not experience any hitlag."

SmashWiki *Invincibility* (series-universal):
> "If a player attacks an opponent while they are invincible, the player will receive the normal
> amount of hitlag, but the opponent will otherwise be unaffected."

**Answer: the invincible defender does NOT freeze** — knockback is zeroed, and hitlag is gated on
knockback, so "otherwise unaffected."

**Candid caveat on the meleelight reimpl:** its invincible bail-out (`executeRegularHit`) reads
`player[v].phys.hurtboxState` (lowercase *b*), but the canonical field set by the state machine is
`hurtBoxState` (capital *B*) — the lowercase name is defined nowhere, so that early-return is
effectively **dead code in this reimplementation** (a meleelight field-name defect). It does **not**
change the canonical answer: attacker-hitlag is still set first (Q1), the state distinction is still
real (Q4), and SmashWiki + the code's evident intent both give victim-unaffected. It is flagged here
only so the meleelight citation is read with eyes open, not as a claim about PM.

## Q3 — Both, neither, or conditional? → **ATTACKER ONLY**

Q1 + Q2 ⇒ the attacker freezes; the invincible defender does not. Not both, not neither. **`[inference]`**
that pycats' respawn-descent invincibility behaves like any other invincibility source — meleelight
routes every source through the same `hurtBoxState == 2`, and no PM/Brawl source names a per-source
exception.

## Q4 — PREMISE CHECK: is *invincibility* a **distinct** engine state from *intangibility*? → **YES, distinct — confirmed in the state machine**

**Engine (meleelight, `hurtBoxStateUpdate` in `physics/physics.js`):** two separate timers resolve
to **three distinct hurtbox states**, evaluated in order:

```js
// (0 = tangible default; REBIRTH/REBIRTHWAIT forces 1)
if (player[i].phys.invincibleTimer > 0) { player[i].phys.invincibleTimer--; player[i].phys.hurtBoxState = 2; }  // INVINCIBLE
if (player[i].phys.intangibleTimer > 0) { player[i].phys.intangibleTimer--; player[i].phys.hurtBoxState = 1; }  // INTANGIBLE
```

The two are **not collapsed** — they are separate timers producing separate states (`1` vs `2`), and
they diverge at the detection gate. In the hit-detection loop (`physics/hitDetection.js`):

```js
} else if (player[i].phys.hurtBoxState != 1) {   // only NON-intangible victims are tested for a hurtbox hit
    ... hitHurtCollision(...) ... hitQueue.push(...)
```

- **State 1 (intangible):** the hurtbox collision is **never tested** → the attack passes through →
  no hit registers → **no attacker hitlag**. (Matches SmashWiki *Intangibility*: "does not cause
  hitlag to attackers since the intangible character is not physically hit.")
- **State 2 (invincible):** `2 != 1` → the collision **is** tested → the hit queues and
  `executeRegularHit` runs → **attacker hitlag** (Q1), victim zeroed (Q2).

**Answer: distinct states.** The discriminating test (#774 §1.1 — *does the attack connect?*) is
implemented literally: intangible skips detection; invincible connects-then-zeroes.

### Q4 bonus findings (corroborate #784 and #774/#506)

- **Precedence — intangible outranks invincible, confirmed.** In `hurtBoxStateUpdate` the intangible
  check runs **after** the invincible check, so if both timers are live, `hurtBoxState` ends at `1`
  (intangible) — pass-through wins. This is exactly #784's ratified "INTANGIBLE outranks INVINCIBLE,"
  now grounded in engine code rather than inference alone.
- **Respawn = invincibility, confirmed.** `REBIRTHWAIT.js` sets `player[p].phys.invincibleTimer = 120`
  (the post-platform descent → state 2, invincible), while the REBIRTH/REBIRTHWAIT **actionState**
  forces `hurtBoxState = 1` (on the platform → intangible). This matches #774 row 6's *mixed* ruling
  (intangible on-platform, invincible after dropping) and is precisely #506's window — 120 frames,
  invincibility.

## 5. PM 3.6 relevance (the inference bridge)

No PM-3.6 primary states this rule; the bridge is `[inference]`, now triangulated three ways:
(a) **meleelight** implements it in the Melee engine PM restored; (b) **SmashWiki** states it
series-universally (Brawl, PM's base, included); (c) the **PM 3.6 codeset carries no override** of
invincibility/intangibility/hitlag. Chain ⇒ PM 3.6 follows the lineage model — attacker hitlag on
connect, invincible defender unaffected, two distinct states with intangible winning ties.

One **Brawl-specific** detail flagged out-of-scope (SmashWiki *Invincibility*): "In *Super Smash
Bros. Brawl*, it is actually possible to hit an opponent normally out of invincibility… This is only
the case in *Brawl* however." Whether PM kept this hitbox-carryover is **unconfirmed** — it does not
affect the #506/#784 model (which needs only: attacker hitlag yes, victim unaffected, states
distinct), so it is left as an open sub-thread, not a blocker.

## 6. What this means for #784 / #506 (the INVINCIBLE combat branch)

The `INVINCIBLE` branch of the `Tangibility` 3-way combat gate (ratified in #784) should, when an
attack connects with an invincible defender:

1. **Register the hit** (contact is made — unlike the `INTANGIBLE` skip path).
2. **Apply the attacker's hitlag** exactly as a normal hit does — set `atk.owner.fighter.hitlag_timer`
   on the attacker. *(A pycats-code behavior; if implemented it becomes a SHA-pinnable claim per
   #754 — see "Does NOT" in #797.)*
3. **Zero the defender's** damage, knockback, hitstun, **and hitlag** — the invincible defender is
   "otherwise unaffected."

This **confirms #784's premise**: invincibility (register-but-zero, attacker-freezes) is a real,
distinct state from intangibility (skip-the-hit, nobody-freezes) — and the engine even evaluates
them in the same precedence order #784 chose. #784's Q1→A stands; the A-vs-B fork does **not** reopen.
The sole A-vs-B observable at pycats fidelity — "does the attacker freeze for a few hitlag frames
when swinging at a respawning fighter?" — resolves to **A: yes**.

## Acceptance check (against #797)

The ticket asked for a verbatim **primary** quote per question OR an explicit **unknown** mark with
the fallback noted. No PM-primary exists; each answer is grounded in the **meleelight engine
reimplementation** (Melee tier, primary-reimplementation) **+ verbatim series-universal SmashWiki
quotes**, with the **PM-3.6 step labeled `[inference]`** and the residual gap stated. That is the
"explicitly marked, fallback noted" path — over-delivered with engine code rather than a lone wiki.

- ✅ **Q1** attacker hitlag **YES** — meleelight `executeRegularHit` (attacker hitlag set pre-bail) + 2 verbatim quotes.
- ✅ **Q2** defender hitlag **NO** — meleelight ordering (victim path after bail) + 2 verbatim quotes; meleelight casing-bug caveat stated.
- ✅ **Q3** **attacker only** — Q1+Q2; per-source independence `[inference]`.
- ✅ **Q4 premise** **distinct states** — meleelight `hurtBoxStateUpdate` (0/1/2) + detection gate + verbatim contrast quote.
- ➕ **Bonus:** engine-confirmed intangible>invincible precedence (feeds #784) and respawn=invincibility mapping (feeds #774 row 6 / #506).
- ⚠️ **Residual gap stated:** no PM-3.6 primary; strongest is Melee reimpl + series-universal wiki + PM-codeset absence-of-override; PM step is `[inference]`.
- ✅ All inference tagged `[inference]`; Brawl-specific carryover flagged.
- ✅ No claims-ledger entries (external facts live here, not `claims-data/` — #754). No code changes.

## Sources

Verified 2026-07-20. Code cited by named symbol + file path (line numbers drift); local clones per
`docs/pm-reference/where-to-find-source-data.md`.

| Source | Tier | Used for |
|---|---|---|
| meleelight `hurtBoxStateUpdate` — `physics/physics.js` (local clone #616) | primary reimpl (Melee) | Q4 distinct 0/1/2 states; precedence; respawn timers |
| meleelight `executeRegularHit`, detection loop — `physics/hitDetection.js` | primary reimpl (Melee) | Q1 attacker-hitlag-on-connect; Q2 victim path; Q4 detection gate `!= 1`; the casing-bug caveat |
| meleelight `REBIRTHWAIT.js` — `characters/shared/moves/` | primary reimpl (Melee) | respawn = `invincibleTimer = 120` (state 2) |
| Project-M-CC `codes-cc-3_6.txt` (local clone #664) | PM-specific (absence) | no PM Gecko-code override of these mechanics |
| [SmashWiki — Invincibility](https://www.ssbwiki.com/Invincibility) | secondary, series-universal | Q1/Q2 wording; Q4 distinct-states; Brawl-qualified carryover |
| [SmashWiki — Hitlag](https://www.ssbwiki.com/Hitlag) | secondary, series-universal | Q1/Q2 wording |
| [SmashWiki — Intangibility](https://www.ssbwiki.com/Intangibility) | secondary, series-universal | Q4 "does not cause hitlag to attackers" contrast |
| in-repo `docs/research/2026-07-20-intangibility-vs-invulnerability-canon.md` (#774) | — | the discriminating test (§1.1) this builds on |
| in-repo `docs/pm-reference/where-to-find-source-data.md` (#120) | — | source-tiering; the datamine engine-global limit |

## Cross-refs

Epic **#772**; decision **#784** (Q4a / premise — **confirmed**, precedence corroborated); DEV
**#506** (respawn invincibility — window + mixed model corroborated); canon **#774** (row 6 mixed
ruling corroborated); the forthcoming `Tangibility`-enum DEV ticket. Memory:
[[rukaidata-engine-hardcoded-limit]], [[pm36-canonical-reference]], [[brawllib-datamine-env-live]].
