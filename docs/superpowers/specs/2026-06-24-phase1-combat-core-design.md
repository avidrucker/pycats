# Phase 1 (foundation) — authentic knockback + hitstun-from-knockback

> Design/spec for the first slice of **#38 — Phase 1 Combat core**. Replaces the
> placeholder linear knockback with the authentic Brawl/Project-M formula and
> derives hitstun from knockback. Implementation is a separate, later-filed child
> of #38; this doc is the contract that child builds to.
>
> Roadmap: [`docs/research/pm-mechanics-implementation-analysis.md`](../../research/pm-mechanics-implementation-analysis.md) §8 (Phase 1) / §9.
> Date: 2026-06-24. Spec ticket: #39. Umbrella: #38.

## 1. Problem

Today knockback is a placeholder: in `Player.receive_hit`,

```python
kb = atk.base_kb + atk.kb_scale * self.percent      # linear; KNOCKBACK_BASE=5, KNOCKBACK_SCALE=0.5
```

and hitstun is a fixed `HURT_TIME = 12` frames regardless of the hit. That means:

- knockback ignores **damage of the move**, **target weight**, and the real
  percent-scaling curve, so heavy hits at high percent feel the same as light ones;
- hitstun is constant, so there is no combo structure (hitstun should grow with
  knockback) and no relationship between how hard you are hit and how long you are
  stunned.

This slice makes both faithful to the Brawl/PM model, using only well-documented
formulas (no research-gated mechanics — see §7).

## 2. The formula (authentic)

### 2.1 Knockback

The Brawl/Project-M knockback value (SmashWiki, "Knockback"):

```
KB = (((((p / 10) + (p * d / 20)) * (200 / (w + 100)) * 1.4) + 18) * (KBG / 100)) + BKB
```

| Symbol | Meaning | Source in pycats |
|---|---|---|
| `p` | target damage percent **after** this hit is applied | `self.percent` (post-`+= damage`) |
| `d` | damage dealt by the hit | `hitbox.damage` |
| `w` | target weight | new `Player.weight` (default 100) |
| `BKB` | base knockback (per-hitbox) | new `Hitbox.base_knockback` |
| `KBG` | knockback growth (per-hitbox) | new `Hitbox.knockback_growth` |

Notes / decisions:
- **Weight default = 100.** Brawl's reference weight is 100; at `w = 100` the
  `200/(w+100)` term is `1.0`, so a neutral fighter is the natural baseline. The
  existing `weight` config TODO is satisfied by this field.
- `p` is the **post-hit** percent (the hit's damage is added before computing KB),
  matching Smash. The current code already does `self.percent += atk.damage`
  before computing kb — keep that order.
- Output `KB` is a unitless knockback magnitude that feeds the launch velocity the
  same way today's `kb` does (`vel += KB·cos(angle)·dir`, `vel.y = KB·-sin(angle)`),
  preserving #8's **combine-horizontal / override-vertical** behaviour.

### 2.2 Hitstun

```
hitstun_frames = max(HITSTUN_FLOOR, floor(KB * HITSTUN_MULTIPLIER))
```

| Constant | Value | Confidence |
|---|---|---|
| `HITSTUN_MULTIPLIER` | `0.4` | **⚠ verify** — Brawl/PM hitstun ≈ `KB × 0.4`; PM removed hitstun-cancelling but kept the proportional model. Pin at 0.4; revisit if combo feel is off. |
| `HITSTUN_FLOOR` | `1` | **⚠ verify** — a small floor so any clean hit yields ≥1 frame of hurt; exact PM minimum not pinned. Chosen, not sourced. |

These two constants are the only sourced-but-uncertain numbers in the slice; both
are isolated in `config.py` so tuning is a one-line change.

## 3. Architecture (decomplect the math out of `Player`)

New pure module **`pycats/combat/knockback.py`** — no pygame, no `Player`, no state:

```python
def knockback(percent: float, damage: float, weight: int,
              base_knockback: float, knockback_growth: float) -> float:
    """Brawl/PM knockback magnitude. `percent` is the post-hit percent."""

def hitstun_frames(kb: float) -> int:
    """Frames of hitstun for a given knockback magnitude."""
```

`Player.receive_hit` becomes a thin caller:

```python
# `atk` is the Attack, which carries the active hitbox's damage/angle and
# (Phase 1) base_knockback/knockback_growth through from MoveData.Hitbox.
self.percent += atk.damage
kb = knockback(self.percent, atk.damage, self.weight,
               atk.base_knockback, atk.knockback_growth)
self.hurt_timer = hitstun_frames(kb)
self._start_hurt()                      # visual flash only; caller set the timer
# launch (unchanged from #8): combine X, override Y
self.vel.x += kb * math.cos(rad) * direction
self.vel.y  = kb * -math.sin(rad)
```

Why a separate module: the formula is pure arithmetic with known reference values,
so it is unit-testable in isolation against a Smash knockback calculator — which is
exactly the can-fail regression test the new [RULES.md → Fixing bugs](../../../RULES.md)
rule (#35) requires. Keeping it inline in `receive_hit` would force every test to
build a pygame `Player` and a hit, hiding the math behind I/O.

## 4. Data changes

| File | Change |
|---|---|
| `pycats/combat/data.py` | `Hitbox` gains `base_knockback: float` and `knockback_growth: float` (the fields its own docstring reserves as "Phase 1 fields"). |
| `pycats/characters/default_cat.py` | the one `"attack"` move's hitbox gets concrete `base_knockback` / `knockback_growth` chosen to keep the jab's feel close to today's (tuned so a mid-percent hit lands near the current launch — documented in the move comment). |
| `pycats/entities/attack.py` | carry `base_knockback`/`knockback_growth` from the hitbox; **retire** `base_kb`/`kb_scale` (and the `KNOCKBACK_BASE`/`KNOCKBACK_SCALE` defaults they read). |
| `pycats/entities/player.py` | add `weight: int = 100` (constructor arg + stored); `receive_hit` uses the new module; `_start_hurt` no longer hard-codes the timer (caller sets `hurt_timer`). |
| `pycats/config.py` | remove `KNOCKBACK_BASE`/`KNOCKBACK_SCALE`; add `HITSTUN_MULTIPLIER = 0.4`, `HITSTUN_FLOOR = 1`; retire the `weight` TODO comment. `HURT_TIME` stays only if still used elsewhere (audit; likely removable). |

Weight is a single scalar on the fighter for now; per-character weight values
(heavy/medium/light) are a later concern (config TODO / future moveset work), not
this slice — default 100 for all.

## 5. Testing

1. **Unit — `tests/test_knockback.py` (pure, no pygame):**
   - Reference values: feed inputs whose expected `KB` is computed by hand / a
     known calculator and assert equality (within float tolerance). At least:
     low-percent light hit, high-percent heavy hit, and a `weight` sweep
     (lighter → more KB, heavier → less).
   - `hitstun_frames` monotonic in `KB`; floor honoured at `KB → 0`.
   - **Can-fail check (per #35):** confirm a deliberately-wrong coefficient makes
     the test red before committing.
2. **Integration — extend respawn/combat tests:** a hit applies computed hitstun
   (not 12); a **moving** defender still combines horizontal momentum (#8 guard
   must stay green).
3. **Golden:** `tests/golden/combat.json` **will churn** — launch velocities and
   hitstun change. Regenerate with `PYCATS_UPDATE_GOLDENS=1`, then **verify the
   diff semantically** (only velocity / hurt_timer / percent-derived fields move,
   in the expected direction) before committing — the #31 discipline. Document the
   verification in the implementation PR/commit.
4. **Parity:** legacy↔statechart parity may legitimately end for combat math (the
   roadmap §6 flags this); knockback lives in `receive_hit` (shared by both
   backends), so parity should hold here — confirm, and if it diverges, treat
   golden self-regression as the oracle.

## 6. Out of scope (later, separately-filed children of #38)

Multi-hitbox priority/clank · hitlag/freeze frames · ground vs air attack split ·
shieldstun + shield-break→stun · stale-move negation · DI/SDI · tumble/knockdown
threshold · Sakurai angle (361) special-casing · per-character weights.

## 7. Research gating

None for this slice. The knockback/hitstun formulas are well-documented
(SmashWiki). The refuted/under-documented mechanics (shield **pushback** magnitudes
— thread b; powershield/parry, wavedash, L-cancel — thread c) are **not** in this
slice; see #24 / `docs/research/BACKLOG.md`. The two flagged constants (§2.2) are
tuning values, not research blockers.

## 8. Definition of done (this spec ticket #39)

- This doc committed and self-reviewed (no TBDs, internally consistent).
- Human reviewer approves.
- writing-plans produces the implementation plan; the **implementation** child of
  #38 is then filed (and claimed) as the next step.

## Sources

- SmashWiki — Knockback (formula): https://www.ssbwiki.com/Knockback
- SmashWiki — Hitstun: https://www.ssbwiki.com/Hitstun
- `docs/research/brawl-projectm-fighter-states.md`, `pm-framerate-fidelity.md`
  (integer-frame timing), `pm-mechanics-implementation-analysis.md` (§3–4 gap, §8 roadmap).
