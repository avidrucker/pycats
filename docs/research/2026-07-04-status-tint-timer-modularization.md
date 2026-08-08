# Status tints + above-head timer bars — modularization audit & plan (#513)

> Research findings (#513). Date: 2026-07-04. Agent: FIG. Area: `area:display`.
> **Findings + a concrete refactor plan — no code in this ticket.** Motivating consumer:
> respawn-invuln (#506 / epic #482), which today would need a new branch in *two* ad-hoc
> systems to get its white tint + green timer bar.

## TL;DR / recommendation

Two independent systems in `pycats/render_battle.py` decide a fighter's status feedback:
1. **`active_tint(p)`** (`:313`) — the body-flash overlay, a 3-branch if-chain.
2. **`timer_bar_specs(p)`** (`:521`) + **`_invuln_remaining_max(p)`** (`:498`) — the above-head bars.

They share **no** description of a "status source," so each status is hand-wired in up to two
places, and the two have already **drifted**: the `invulnerable` bool has ~5 sources, but the bar
resolver knows only 3 — so **`ledge_invuln_timer` (#311) is intangible with no bar today**, and
respawn (#506) would be the same. Adding a status = editing both functions, with nothing enforcing
that a timer gets both its tint and its bar.

**Recommendation: yes, unify — build one `STATUS_SOURCES` registry that feeds *both* `active_tint`
and `timer_bar_specs`, as a single identity-preserving refactor DEV** (goldens + render byte-
identical). The full unification (not a bar-only narrow one) is the right scope, because respawn
needs a **tint** *and* a **bar** from one entry — and the tint lives in the *other* system, so a
bar-only registry can't deliver the ticket's goal. After it lands, **registering respawn is one
record** → white tint + green INVULN bar, both driven by the same `respawn_invuln_timer`. The
migration is bounded by three well-understood value-shapes (count-down / resource / fill) and one
carve-out (the dizzy star-halo stays separate).

---

## Audit — every status source × its outputs

`T` = body-flash tint (`active_tint`); `B` = above-head bar (`timer_bar_specs`). Max column is the
constant (or resolver) each bar's ratio divides by.

| Source | timer field | value-shape | max | T (tint) | B (bar / label) | bar class | quirks |
|---|---|---|---|---|---|---|---|
| hurt | `hurt_timer` | count-down | — | **RED** | — | — | **tint-only, no bar** |
| stun / dizzy | `stun_timer` | count-down | `SHIELD_BREAK_STUN_MAX` | **YELLOW** | DIZZY | exclusive | **3 outputs**: tint + bar + **star-halo** (`draw_dizzy_stars`) |
| dodge | `dodge_timer` | count-down | `DODGE_TIME` | **WHITE** | INVULN | overlay | bar routed via `_invuln_remaining_max` (it's an invuln source) |
| shield | `shield_hp` | **resource** | `SHIELD_MAX_HP` | — | SHIELD | exclusive | **not a frame timer** (hp gauge); sorts last (`_SHIELD_RECENCY_KEY`) |
| ledge-hang | `ledge_hang_timer` | count-down | `LEDGE_HANG_FRAMES` | — | HANG | exclusive | suppresses the INVULN bar while hanging |
| prone | `prone_timer` | count-down | `KNOCKDOWN_PRONE_FRAMES` | — | DOWN | exclusive | — |
| regrab lockout | `ledge_regrab_lockout_timer` | count-down | `LEDGE_REGRAB_LOCKOUT_FRAMES` | — | LOCKOUT | overlay | — |
| getup-roll | `getup_roll_timer` | count-down | `GETUP_ROLL_FRAMES` | — | INVULN | overlay | invuln source; **no tint** (only dodge whites) |
| getup-attack | `getup_attack_timer` | count-down | `_GETUP_ATTACK_FRAMES` | — | INVULN | overlay | invuln source; no tint |
| **ledge-invuln** | `ledge_invuln_timer` | count-down | **percent-scaled** (`LEDGE_INVULN_BASE + 0.3/% cap 60`) | — | **none (gap!)** | — | sets `invulnerable=True` but **absent from the bar resolver** — the live drift |
| charge | `smash_charge_timer` | **fill** | `SMASH_CHARGE_FRAMES` | — | CHARGE | overlay | grows 0→100%; recency = up-count; readout `"%·s"` |
| **respawn (future #506)** | `respawn_invuln_timer` | count-down | `RESPAWN_INVULN_FRAMES` | **WANT WHITE** | **WANT INVULN** | overlay | the consumer this refactor unblocks |

### The three problems this exposes
1. **Two systems, no shared source-of-truth.** A source can appear in `active_tint`, in
   `timer_bar_specs`, in both, or (dizzy) also drive a third output — with nothing tying them.
2. **Live drift.** `invulnerable` is set from ~5 places (`player.py:367/417/451/…`) but
   `_invuln_remaining_max` maps only `dodge`/`getup_roll`/`getup_attack`. **`ledge_invuln_timer`
   is intangible with no bar right now** (its own docstring already excuses respawn as another such
   case). New invuln sources silently inherit this gap.
3. **Three value-shapes, hand-computed each time.** count-down (`remaining/max`), resource
   (`shield_hp/max`), fill (`timer/max`, up-count recency). Each bar re-derives ratio/seconds/recency
   inline.

---

## Proposed shape — one `STATUS_SOURCES` registry feeding both systems

An ordered list of declarative records; both render functions *derive* from it:

```
StatusSource(
    name,                       # "respawn", "dodge", "shield", …
    live,                       # (f, p) -> remaining|hp|None  (truthy ⇒ active this frame)
    kind,                       # COUNTDOWN | RESOURCE | FILL   (drives ratio/readout/recency)
    max,                        # constant OR (f, p) -> int     (percent-scaled ledge-invuln)
    tint = None,                # RED/YELLOW/WHITE/… or None
    bar  = None,                # (color, label) or None
    bar_class = None,           # EXCLUSIVE | OVERLAY | None
    precedence = 0,             # tint priority + exclusive-state selection order
    suppress_bar_if = None,     # e.g. p.state == "ledge_hang"
)
```

- **`active_tint(p)`** → first source by `precedence` whose `live` is truthy **and** `tint` is set.
  (Reproduces today's hurt > stun > dodge order.)
- **`timer_bar_specs(p)`** → for sources with a `bar`: at most one `EXCLUSIVE` (highest precedence
  that's live) plus all live `OVERLAY`s; ratio/seconds/recency computed **once per `kind`**.

**Registering respawn becomes one record** — `tint=WHITE, bar=(INVULN_BAR_COLOR,"INVULN"),
kind=COUNTDOWN, max=RESPAWN_INVULN_FRAMES, live=lambda f,p: f.respawn_invuln_timer, bar_class=OVERLAY`
— and it lights the tint *and* the bar off one timer. No new branches. That is the success test.

### Exceptions — modeled, not hand-waved
- **shield** → `kind=RESOURCE` (`live` returns `shield_hp`; seconds from the drain rate); keep the
  sort-last recency sentinel as a `RESOURCE` property. Modeled.
- **charge** → `kind=FILL` (up-count ratio, `"%·s"` readout, recency = the up-count). Modeled.
- **ledge-invuln** → `max` as a resolver `(f,p)->…` for the percent-scaled cap. Modeled.
- **dizzy star-halo** → **exempt.** The registry owns stun's *tint + bar*; the orbiting stars
  (`draw_dizzy_stars`) stay their own render path. Note it, don't fold it.
- **hurt** → `bar=None` (tint-only). Falls out naturally.

### The drift decision (do NOT silently fix in the refactor)
`ledge_invuln_timer` having no bar is a **behavioural** question, not a refactor detail. The refactor
is **identity-preserving**, so it must keep ledge-invuln bar-less (byte-identical). Whether to *give*
it a bar is a separate one-line follow-up decision — flag it, don't fold it in (a "fix" would break
the byte-identity proof and smuggle a behaviour change into a refactor).

---

## Identity-preserving migration plan (the DEV ticket to file next)

1. **Add** the `STATUS_SOURCES` table + two pure derivations (`_tint_from_registry`,
   `_bars_from_registry`) **alongside** the existing functions. No call sites changed yet.
2. **Prove equivalence** headlessly across every state: for a matrix of fighter states/timers,
   assert `_tint_from_registry(p) == active_tint(p)` and
   `_bars_from_registry(p) == timer_bar_specs(p)` (same `TimerBar` list, same order). This is the
   able-to-fail guard (perturb one registry entry → mismatch).
3. **Swap** `active_tint` / `timer_bar_specs` to delegate to the registry; delete the if-chains and
   fold `_invuln_remaining_max` into the table.
4. **Verify byte-identity**: render-hash of `render()` across states unchanged + `test_golden` green
   with **no regen** (this refactor changes nothing observable) + full suite green.
5. Land with the equivalence test as the regression guard.

**Scope call (Q4):** do the **full** unification in this one DEV (all count-down sources + tint
sources + the RESOURCE/FILL kinds; dizzy-halo exempt). A narrow bar-only registry was considered and
rejected: respawn's white tint lives in `active_tint`, so a bar-only registry cannot deliver the
one-entry tint+bar outcome #506 needs. Estimated one focused DEV (~90m) given the equivalence-test
scaffolding; splittable into "registry + tint" then "registry + bars" if the diff balloons, but the
shared table makes one ticket cleaner.

## Follow-ups to file from this finding
- **DEV** (identity refactor): build `STATUS_SOURCES`, migrate `active_tint` + `timer_bar_specs`,
  equivalence test, no golden regen. → unblocks **#506** (respawn registers as one entry).
- **decision** (tiny, non-blocking): should `ledge_invuln_timer` get an INVULN bar (close the drift)?
  Currently no bar; the refactor preserves that pending this call.

## Sources / anchors
`pycats/render_battle.py`: `active_tint:313`, `_blend/tinted/body_tint:332-`, bar colours `:470-476`,
`_invuln_remaining_max:498`, `timer_bar_specs:521`, `draw_timer_bars:603`. Invuln sources in
`pycats/entities/player.py:367/417/451/456/460/464`; `ledge_invuln_timer` `fighter.py:154` (#311).
Systems of record: #109 (tint), #111 → #334 / #340 / #357 / #358 (timer bars), #380 (charge fill).
Consumer: #506 / epic #482. Identity discipline: `tests/golden/REGEN_PROTOCOL.md` + render-hash verify.
