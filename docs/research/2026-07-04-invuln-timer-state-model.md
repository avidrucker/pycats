# Invulnerability / timer-state model — is it composed? should it unify? how does PM do it? (#520)

> Research findings (#520). Date: 2026-07-04. Agent: GRAPE. Area: `area:entities` /
> `area:combat`. **Findings + a recommendation — no code, no enum/refactor, no tuning.**
> Any unify work is a follow-up DEV/ARCHITECT ticket, filed only on an explicit go-ahead.
>
> Companion finding: **#513** (`2026-07-04-status-tint-timer-modularization.md`) maps the
> **render-side** drift of the same source list (tint + above-head bar). This doc is the
> **game-logic** half: how intangibility composes and gets checked at hit time.

## TL;DR

- Intangibility in pycats is **one shared boolean** — `Fighter.invulnerable` — written from
  **14 sites** and read at hit time by **exactly one** conditional (`combat.py:113`). There is
  **no** per-source flag, no `any(sources)` derivation, no refcount, no enum grouping.
- The composition model is **last-writer-wins**, made safe *only* by two external
  conventions: (a) the fighter statechart keeps action-states **mutually exclusive** (you are
  dodging OR ledge-hanging OR getting up, never two at once), and (b) each `invulnerable =
  False` exit is **string-guarded** on `self.state == "<that state>"`. Nothing in the
  intangibility model itself enforces this.
- **No live clobber bug today** — exclusivity + the guards hold. But there is a **latent rot
  hazard**: `invulnerable_timer` (`fighter.py:171`) is **vestigial** — set once, **never
  decremented, never read as a gate** — so the bool and the timer can silently disagree. And
  adding a **new overlapping source** (respawn-invuln #506 is exactly this, already
  half-documented) would break last-writer-wins unless every `= False` exit becomes
  source-aware.
- **Project M does NOT "compose" multiple simultaneous intangibility sources** — the claim to
  test is **refuted as a description of PM's engine**. PM/Brawl runs a single **action state
  machine** (`Fighter::Status::Kind`, one exclusive state per frame); intangibility is a
  per-frame **body-state** (normal / intangible / invincible) emitted by the *current* action's
  script and checked at collision. There is no N-source stack to compose because there is only
  ever one action state. pycats' single-bool model is actually **closer to PM** than an
  `any(sources)` refcount would be — PM's single source of truth is *the current state itself*.
- **Recommendation: yes, unify — but toward PM's shape, not toward a refcount.** Make
  intangibility **derived** (`is_intangible = any(live source-timers)` or, better, a property of
  the current action-state) instead of a separately-written flag; delete the vestigial
  `invulnerable_timer`; and align the source list with **#513's `STATUS_SOURCES` registry**
  (one list feeds hit-nullification + tint + bar). This is a robustness/maintainability
  investment (today's behaviour is correct), so it is a **follow-up**, not urgent — and it is
  the natural unblock for respawn-invuln (#506).

---

## Q1 — Inventory: every intangibility source + every timer

**Owner of `invulnerable`:** `Fighter` (`pycats/entities/fighter.py:174`). `Player` reaches
through `self.fighter.invulnerable`; it owns no copy.

### The 14 write sites of `fighter.invulnerable`

| # | file:line | → | State / trigger |
|---|---|---|---|
| W1 | `fighter.py:174` | `False` | init default |
| W2 | `fighter.py:392` | `False` | `_handle_landing` waveland — diagonal-down air dodge touching ground ends the dodge, drops intangibility (keeps the slide) |
| W3 | `fighter.py:494` | `False` | `reset_to_spawn` — clears leaked intangibility on KO / respawn / new-match |
| W4 | `fighter.py:548` | `True` | `start_getup_roll` — getup-roll out of prone (#146) |
| W5 | `fighter.py:564` | `True` | `_start_dodge` — **all** dodges (spot / air / roll / wavedash) (#184/#202) |
| W6 | `player.py:172` | `False` | `_evict_from_ledge` — a mistimed edge-hog occupant is knocked off (#311) |
| W7 | `player.py:367` | `=(ledge_invuln_timer>0)` | ledge-hang, per-frame: intangible iff the percent-scaled burst still runs (#311) |
| W8 | `player.py:374` | `False` | neutral ledge getup (up) begins the climb → hang intangibility ends |
| W9 | `player.py:378` | `False` | ledge drop (down / away / timeout) → hang intangibility ends |
| W10 | `player.py:417` | `True` | ledge-grab moment (#14/#311) |
| W11 | `player.py:451` | `True` | getup-attack (#225) — held for the **whole** swing (⚠ flagged for playtest tightening) |
| W12 | `player.py:456` | `False` | `getup_roll_timer==0 && state=="getup_roll"` → intangibility ends with the roll |
| W13 | `player.py:460` | `False` | `getup_attack_timer==0 && state=="getup_attack"` → ends with the swing |
| W14 | `player.py:464` | `False` | `dodge_timer==0 && state=="dodge"` → ends after the dodge |

### The timer fields (all on `Fighter`, `fighter.py:134-171`; constants in `config.py`)

**Intangibility sources** — they set / drive `invulnerable = True`:

| Timer | Max | Drives invuln via |
|---|---|---|
| `dodge_timer` | `DODGE_TIME`=14 | `_start_dodge` W5; ends at W14 |
| `getup_roll_timer` | `GETUP_ROLL_FRAMES`=16 | `start_getup_roll` W4; ends at W12 |
| `getup_attack_timer` | swing length | W11; ends at W13 |
| `ledge_invuln_timer` | `ledge_invuln_frames(pct)` (base 23, +0.3/%, cap 60) | grab W10, per-frame W7; ends W8/W9 |

**Plain action-locks — NOT intangible** (restrict input/actions, still hittable):
`hurt_timer` (hitstun), `stun_timer` (shield-break dizzy), `prone_timer` (knockdown — only
*lowers* the hurtbox, `combat.py:127-134`), `landing_lag_timer` (waveland lock),
`ledge_hang_timer` (hang *timeout*; intangibility is the separate `ledge_invuln_timer`),
`ledge_getup_timer` (climb lock — W8 sets `invulnerable=False` when it starts),
`ledge_regrab_lockout_timer`, `shieldstun_timer`, `hitlag_timer` (freeze for *both* fighters),
`dash_timer` / `dash_input_window`, `smash_charge_timer` (counts up), `attack_timer` (derived
on `Player` over `MoveClock`). **Shield** is a *resource* (`shield_hp`), blocked in a separate
`receive_hit` branch (`fighter.py:302`), independent of `invulnerable`.

**`respawn`** intangibility is **mentioned but unimplemented** — the init comment
(`fighter.py:174`) and `_invuln_remaining_max` docstring (`render_battle.py:507`) name it, but
no code grants it; `reset_to_spawn` sets `invulnerable=False`. It is the future consumer
(#506 / epic #482) and the **exact new-overlapping-source risk** below.

---

## Q2 — Current composition model: independent boolean writes, last-writer-wins

**How the sources interact today: they don't — they take turns.** Each source hard-assigns the
one shared bool. This is **not** stacking, not additive, not a refcount, not `any(...)`. It is
**last-writer-wins within a frame**, plus **per-frame overwrite** (W7 reassigns every hang
frame). The hit path reads that single bool:

```python
# pycats/systems/combat.py:110-115  — the sole hit-nullification guard
for defender in players:
    if (
        defender.fighter.invulnerable or not defender.fighter.is_alive or defender is atk.owner
    ):  # no self-hit
        continue
```

**Why it's correct today — two conventions outside the model:**

1. **State exclusivity.** The statechart (`charts/fighter_chart.py`) `action` region holds one
   leaf at a time (`dodge` / `prone` / `getup_roll` / `getup_attack` / `ledge_hang` / …), so two
   intangibility sources are essentially never live together. The separate `defensive_status`
   orthogonal region (`fighter_chart.py:377-387`) is a **mirror** — leaves `vulnerable` /
   `intangible` are driven *off* the bool (`_tick(lambda …: p.fighter.invulnerable)`), it does
   not *decide* intangibility.
2. **String-guarded exits.** W12/W13/W14 only set `False` when `self.state ==` the matching
   state, so a dodge that ends the same frame a ledge-grab begins can't clear the grab's
   intangibility (state is `ledge_hang` by then). **These string compares are the only thing
   preventing cross-source clobber.**

**The overlap / clobber question, answered directly:**

- *Two intangibility windows overlapping* — cannot arise under normal play because states are
  exclusive. The model has **no defined behaviour** for it; whichever site runs last in
  `update()` wins. There is no OR.
- *One source ends and sets `invulnerable=False` while another is still live* — **guarded, not
  modelled.** W12/W13/W14 dodge the clobber via the `state ==` string guard. W2 (waveland) and
  W7 (ledge per-frame `=`) are **unconditional** assignments — they *would* clobber a
  co-active source, and are safe only because none co-occurs today.
- **Latent rot — the clearest hazard:** `invulnerable_timer` (`fighter.py:171`) is **dead**.
  It's set to `GETUP_ROLL_FRAMES` in `start_getup_roll` (`fighter.py:549`) and zeroed in
  init/`reset_to_spawn`, but **never decremented and never read to gate a hit** (only the
  `runner.py:97` snapshot + a `test_respawn_timers.py` assert touch it). So the bool and the
  timer can silently disagree; any future code trusting `invulnerable_timer` as authoritative
  would be **wrong**. This is the one thing here that already smells.
- **The new-source trap:** respawn-invuln (#506) is a source that *can* overlap the descent
  (fighter falls off the revival platform still intangible, could dodge). Bolting it onto
  last-writer-wins means every `= False` exit must learn about respawn, or a dodge-end will
  cancel respawn intangibility early. This is the concrete motivation to unify **before** #506.

**Verdict:** the model is **independent / last-writer-wins**, *not* composed/stacking/combo.
It is correct today by convention (state exclusivity + string guards), carries one dead field
(`invulnerable_timer`), and does not scale to a genuinely overlapping source without rework.

---

## Q3 — Should we unify? Yes, scoped — and toward PM's shape

**Recommendation (not a mandate): derive intangibility instead of writing it.** Replace the
14-site written bool with a single **derived** predicate:

```
is_intangible = any(t > 0 for t in (dodge_timer, getup_roll_timer,
                                    getup_attack_timer, ledge_invuln_timer, respawn_invuln_timer))
```

— or, cleaner and more PM-like, make it a **property of the current action-state** (the state
owns whether it is intangible; the hit path asks the state). Either kills last-writer-wins:
sources become **additive by construction** (any live window ⇒ intangible), no `= False` exit
can clobber a co-active source, and the vestigial `invulnerable_timer` is deleted.

**Trade-offs (candid):**

| | Unify (derive) | Keep (written bool) |
|---|---|---|
| Correctness today | same (identity-preserving) | correct |
| New overlapping source (#506 respawn) | **one entry, no clobber** | every `=False` exit must be edited to be source-aware |
| Clobber class | structurally impossible | prevented by string-guards + exclusivity (fragile) |
| Dead `invulnerable_timer` | deleted | lingers, can desync |
| Cost | refactor across `combat.py` + `player.py` + `fighter.py` + `fighter_chart` + tests; must stay golden/byte-identical | zero |
| Alignment with #513 | **shares one source list** (hit + tint + bar) | two/three drifting lists |

**Why it's a follow-up, not urgent:** today's behaviour is *right*, so this buys robustness +
maintainability, not a bugfix. But it has **two pulls** making it worth doing soon: (1) #506
respawn-invuln is the first real overlapping source and is blocked-by-design on this; (2) #513
already proposes a `STATUS_SOURCES` registry for the render side off the **same** source list —
unifying the logic-side predicate and the render-side registry against one list is the
convergence that stops all three (hit / tint / bar) from drifting. **The natural scope is: one
source list → `is_intangible` (logic) + `active_tint` + `timer_bar_specs` (render).**

**Don't over-build:** a full `DefensiveState` enum / statechart rewrite is **not** needed — the
statechart already exists and already exposes exclusive action-states. The minimal unify is (a)
derive the predicate, (b) drop `invulnerable_timer`, (c) point it at the #513 registry. Bigger
state-machine work is a separate call.

---

## Q4 — How Project M handles it (the claim, tested)

> ⚠️ **SUPERSEDED — see [`## Correction (2026-07-05)`](#correction-2026-07-05) at the end.**
> This section'’s "**Refuted / single body-state / nothing composes**" verdict was **over-stated**.
> A PM-specific research pass with primary sources (`brawllib_rs`, OpenSA, PMDT changelog) found a
> **two-layer** model: action intangibility *is* a single mutually-exclusive body-state (this part
> was right), **but** timed invincibility (respawn, Star) is a **separate overlay that composes**
> with it. The compose hypothesis is therefore **partly correct**, not refuted. Read the
> Correction for the adjudicated evidence; the text below is kept as the original reasoning.

**The claim under test** (from another agent, treated as hypothesis):
> "invulnerable composes with dodge/ledge/getup" … "a hit during the window while also
> mid-dodge stays nullified".

**Refuted as a description of PM's engine.** PM (a **Brawl** mod; PM 3.6 canon,
[[pm36-canonical-reference]]) does not maintain multiple simultaneous intangibility sources and
OR them. It runs a single **action state machine**: each fighter is in exactly **one**
`Fighter::Status::Kind` action state per frame (`Wait=0x0`, `Guard=0x1B`, … `Dead=0xBD` — the
enumerated list is in `BrawlHeaders/fighter.h` and rukaidata's per-character dumps; see
`docs/research/brawl-projectm-fighter-states.md`). Intangibility is a per-frame **body-state**
— *normal / intangible / invincible* — set by **body-state events in the currently-active
action's PSA script**, and checked when a hitbox tests a hurtbubble at collision time. Melee's
debug view makes the single-body-state nature visible: a fighter's hurtboxes turn **blue
(intangible)** or **green (invincible)** as one unit, not per-source
([SmashWiki — Intangibility](https://www.ssbwiki.com/Intangibility),
[Invincibility](https://www.ssbwiki.com/Invincibility)).

**So there is nothing to "compose"** — dodge, ledge-grab, and getup are **different action
states**, mutually exclusive, and each *owns* the body-state while it is the active state. A
fighter is never "mid-dodge **and** on the ledge"; entering the ledge-grab state *is* leaving
the dodge state. The "hit stays nullified while any source is active" phrasing describes an
`any(...)` refcount model that PM **does not** use.

**The correct pycats takeaway (the inversion):** pycats' single `invulnerable` bool is
*already* the PM-shaped thing — one body-state, one collision check. PM's robustness comes from
that body-state being **derived from the single active action-state**, so it *cannot* desync.
pycats' fragility is the opposite: its states are exclusive only by **convention** (string
guards), and its body-state is a **separately-written** flag (plus a dead parallel timer). The
unify in Q3 — derive intangibility from the active state / live windows rather than writing a
flag — is precisely **moving pycats toward PM's model**, not away from it. The right fix is
*not* to add an `any(sources)` stack (that is neither PM nor needed); it is to make the one bool
**derived** so it can't drift.

**Sourcing + limits (rukaidata caveat, [[rukaidata-engine-hardcoded-limit]]):** rukaidata gives
the **per-move scripted** body-state windows (which frames of which move are intangible) and the
action-ID list — but **not** the engine's collision-resolution predicate, which is
engine-hardcoded and lives in the **~1%-complete `doldecomp/brawl`** decomp (`gap`). So "one
body-state checked per frame" is established from the fighter.h observer architecture + the
single-colour debug display (primary-partial + secondary), while the *exact* collision
predicate line is not quotable from a primary source. The **single-exclusive-action-state**
model, however, is well-corroborated and is the load-bearing fact that refutes the compose
claim.

---

## Follow-ups (proposed, NOT filed — file on go-ahead only)

1. **ARCHITECT/DEV (identity-preserving):** derive `is_intangible` from live source-timers /
   active state; delete the vestigial `invulnerable_timer`; align the source list with #513's
   `STATUS_SOURCES` registry (one list → hit-nullification + tint + bar). Golden/byte-identical;
   able-to-fail equivalence test (`derived == old bool` across a state matrix, perturb one entry
   → mismatch). **Unblocks #506** (respawn registers as one source, no clobber).
2. **Note on #513:** its render-side `STATUS_SOURCES` proposal and this logic-side predicate
   should be **one** source list, not two. If #513's DEV lands first, this reuses it; if this
   lands first, #513 derives its tint/bar from the same list. Flag the ordering so they don't
   build two lists.
3. **Tiny cleanup (independent):** `invulnerable_timer` can be removed on its own — it is dead
   today regardless of the larger unify. (Would touch the `runner.py` snapshot + one test.)

## Sources

| Source | Quality | Gives |
|---|---|---|
| `pycats/entities/fighter.py`, `player.py`, `systems/combat.py:110-115`, `charts/fighter_chart.py:377-387`, `render_battle.py:498-518` | primary (repo) | the 14 writes, single-bool hit check, vestigial `invulnerable_timer`, `defensive_status` mirror |
| `docs/research/2026-07-04-status-tint-timer-modularization.md` (#513) | primary (repo) | the render-side `STATUS_SOURCES` proposal off the same source list |
| `docs/research/brawl-projectm-fighter-states.md` | primary (repo, deep-research) | PM/Brawl single action-state machine, `Fighter::Status::Kind`, fighter.h observers, decomp %-complete |
| [SmashWiki — Intangibility](https://www.ssbwiki.com/Intangibility) / [Invincibility](https://www.ssbwiki.com/Invincibility) | secondary | body-state = normal/intangible/invincible; blue/green debug colours = one body-state per fighter |
| [BrawlHeaders `fighter.h`](https://github.com/Sammi-Husky/BrawlHeaders), [rukaidata](https://rukaidata.com/Brawl/) | primary / primary-partial | action-ID enum, per-move body-state windows (not the collision predicate — engine-hardcoded, decomp gap) |

## Caveats & gaps

- PM's **exact** collision-resolution predicate (the line that reads the body-state) is in the
  ~1%-complete `doldecomp/brawl` — **not quotable**; the single-body-state model is inferred
  from architecture + debug display (`gap`, flagged).
- This doc makes **no** ruling on whether to unify — it **recommends** and lays out trade-offs.
  The unify/refactor is a follow-up ARCHITECT/DEV, filed only on an explicit go-ahead per
  RULES.md "Filing work".
- 60-minute spike box respected: PM internals sourced to the corroborated
  single-action-state model; the un-sourceable collision line is recorded as a gap rather than
  guessed ([[rukaidata-engine-hardcoded-limit]]).

---

## Correction (2026-07-05)

> Corrects **Q4** above (filed as #537). A PM-specific research pass — driven by reporter
> pushback on the strength of the original citations — pulled **primary sources** that were not
> consulted in the 60-minute spike. The Q4 verdict "**refuted / single body-state / nothing
> composes**" was **over-stated**. The corrected model is **two layers**. Two *interim*
> over-corrections were also made and are themselves withdrawn here (Metal / Loupe — see below).
> Consumers: **#527** (design reframed to the two-layer model); **#535** (canonical PM register
> will hold these citations). This is the load-bearing version; Q4 is kept only as history.

### The corrected model — PM intangibility is TWO layers

- **Layer 1 — action-driven intangibility (dodge / roll / spot-dodge / air-dodge / ledge-grab /
  getup) is a single, mutually-exclusive body-state, set by the current move's script (overwrite,
  not additive).** *This half of the original Q4 was right* — pycats' single `invulnerable` bool
  is genuinely PM-shaped for these sources; they never co-occur.
- **Layer 2 — timed invincibility (respawn ~120f; Starman) is a separate frame-counted overlay
  that COMPOSES with Layer 1.** Respawn's window is keyed to *when the fighter dismounts the
  revival platform*, runs on its own timer, and the fighter acts freely (dodge / jump / attack)
  while it stays live. This is real composition — but it happens **between the two layers**,
  **never** among multiple action-states.
- **Net PM hit-nullification ≈ `body_state != Normal` OR `any timed-invuln window active`.**
  So the original "**nothing composes**" was wrong for the timed-overlay layer, and the compose
  hypothesis is **partly correct** — precisely for the case pycats' #506 respawn-invuln needs.

### Per-claim verdict table (adjudicated 2026-07-05)

| # | Claim | Verdict | Key citation (tier) |
|---|---|---|---|
| A | Action intangibility (dodge/ledge/getup) = single mutually-exclusive body-state, not ORed flags | ✅ **Confirmed** (high) | `brawllib_rs` `HurtBoxState` enum + `hurtbox_state_all = state` overwrite (**T1 verbatim**); OpenSA `06050100` "Body Collision" (T1, summary); SmashWiki one-colour debug (T2) |
| B | "Metal" (`Flag_Metal`) is invincibility | ❌ **Refuted** — withdrawn interim claim | SmashWiki *Metal Box*: *"does not make fighters invincible"*, *"can still be hit and damaged"*; it's −30 knockback + weight + fall speed (T2) |
| C | "Loupe" (`Flag_Loupe_Damage`) is damage immunity | ❌ **Refuted (it's the opposite)** — withdrawn | SmashWiki *Magnifying glass*: *"damage applied … at a rate of 1% per second"* (off-screen chip damage) (T2) |
| D | "Star" = invincibility composing with acting | ✅ Confirmed but **irrelevant** (item pycats lacks) | SmashWiki: *"invulnerable to all attacks"*, *"you can still attack without fear"* (T2) |
| E | Respawn invincibility composes with actions (overlaps a dodge, not tied to a respawn action-state) | ✅ **Confirmed** (medium-high) | SmashWiki *Revival platform*: on-platform *"intangible … disappears as soon as the player moves or attacks"* vs post-drop *"a further period of invincibility (2 seconds, or 120 frames)"* keyed to dismount (T2). Gap: no verbatim "attacking doesn't truncate the 120f" |
| F | PM ledge intangibility is percent-scaled (as pycats' `ledge_invuln_frames` + #297 claim) | ❌ **Refuted for PM** → audit #536 | PMDT *"3.5 Blogpost #6: Ledge Invincibility"* (**T1 primary**, Wayback): PM uses a flat **5-regrab COUNT** cutoff; per-grab/percent decay is Smash 4/Ultimate, not PM |

### Verbatim anchors (Layer 1, primary)

`brawllib_rs` (rukai's datamined Brawl subaction-script interpreter — powers rukaidata):
```rust
// script_ast/mod.rs — one field holds ONE of these, selected by a single integer
pub enum HurtBoxState { Normal, Invincible, IntangibleFlashing,
                        IntangibleNoFlashing, IntangibleQuickFlashing, Unknown(i32) }
// script_runner.rs — the event OVERWRITES (=), does not accumulate
EventAst::ChangeHurtBoxStateAll { state } => { self.hurtbox_state_all = state.clone(); }
```
Opcode `06 05` = whole-body "Body Collision"; `06 08` = per-bone (each bone still one state).
(`https://raw.githubusercontent.com/rukai/brawllib_rs/master/src/script_ast/mod.rs`,
`.../src/script_runner.rs`.)

### What this changes downstream

- **Q3 recommendation stands and is strengthened:** derive intangibility, retire the vestigial
  `invulnerable_timer`, converge with #513 — unchanged. But the derivation is now explicitly
  **two-layer**: `is_intangible = (action body-state intangible) OR any(live timed overlays like
  respawn)`. The earlier "**don't add an `any(sources)` stack**" line in Q3/Q4 is **withdrawn** —
  the `OR` over timed overlays is exactly PM-faithful and is what #506 respawn needs. #527 is
  reframed accordingly.
- **New ticket #536** — the ledge percent-scaling mis-attribution (claim F) is a separate audit
  against `ledge_invuln_frames` / #297.

### Confidence + remaining gaps (not hidden)

- Layer 1 rests on `brawllib_rs`, a faithful **reimplementation**, not the retail Brawl DOL; no
  `doldecomp/brawl` line confirms the shipped binary's field. OpenSA is held as a fetch **summary**,
  not a byte-exact quote (site HTTP-only / unreachable). → high confidence on "single state value",
  medium-high that retail matches.
- Layer 2 respawn act-persistence (E) is **inferred** from the dismount-keyed timer + universal
  practice; no single verbatim sentence states "attacking does not truncate the 120f".
- Sources tiered: **T1** = PMDT changelog, `brawllib_rs`/rukaidata, OpenSA/dantarion, doldecomp;
  **T2** = SmashWiki/Liquipedia/Smashboards.

### Sources added by this correction

| Source | Tier | Gives |
|---|---|---|
| [`brawllib_rs` `script_ast/mod.rs`](https://raw.githubusercontent.com/rukai/brawllib_rs/master/src/script_ast/mod.rs) + [`script_runner.rs`](https://raw.githubusercontent.com/rukai/brawllib_rs/master/src/script_runner.rs) | T1 primary (reimpl.) | `HurtBoxState` enum, `ChangeHurtBoxStateAll` overwrite, opcodes 06 05 / 06 08 |
| OpenSA `Events (Brawl)` — "Body Collision" `06050100` | T1 primary (summary only) | the script event that sets the single body-state |
| [SmashWiki — Revival platform](https://www.ssbwiki.com/Revival_platform) | T2 | on-platform intangibility vs post-drop 120f invincibility |
| [SmashWiki — Metal Box](https://www.ssbwiki.com/Metal_Box) / [Magnifying glass](https://www.ssbwiki.com/Magnifying_glass) / [Starman](https://www.ssbwiki.com/Starman_(item)) | T2 | refute Metal/Loupe as invuln; Star = item invincibility |
| PMDT — "3.5 Blogpost #6: Ledge Invincibility" ([Wayback](https://web.archive.org/web/20150809045045/https://projectmgame.com/en/news/dev-blogpost-6-ledge-invincibility)) | T1 primary | PM ledge anti-stall = 5-regrab count cutoff (feeds #536) |
