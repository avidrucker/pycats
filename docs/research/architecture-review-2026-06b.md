# pycats architecture review (re-review) — DDD · Hexagonal · BDD (2026-06b)

**Umbrella:** #252 · **Sub-spikes:** #253 (DDD) · #257 (Hexagonal) · #262 (BDD) · **Reviewer:** GRAPE · **Date:** 2026-06-30
**Method:** three bounded read-only sub-spikes, one per lens, building on the prior pass [`architecture-review-2026-06.md`](./architecture-review-2026-06.md) (#56). Each section **diffs the prior findings** (resolved / regressed / new) rather than re-deriving from scratch.

> **Status: COMPLETE** — all three lenses reviewed; Final synthesis below. Follow-ups are **provisional and not yet filed** — per yegor + the #50 lesson, file one at a time when about to be worked.

---

## Executive summary

| Lens | #56 | Now | One-line |
|---|---|---|---|
| DDD (domain model) | ~6/10 | **~8.5/10** | God-object decomposed; D1–D4 + dual-backend all resolved; remaining = two coupling smells |
| Hexagonal (ports & adapters) | ~6/10 | **~7/10** | Player rendering extracted; 3 entities + input port + value-types still leak |
| BDD (spec quality & tests) | ~6/10 | **~8.5/10** | Suite green/guarded, invariants enforced, golden de-risked; only tuning provenance lags |

**Headline:** #56 found all three lenses converging on **one root cause — the 896-line `Player` god-aggregate** — and scored ~6/10 across the board. A year-equivalent of focused work later, **almost every ranked #56 follow-up was genuinely executed** (D1/#69, D2/#71, D3/#70, S1+S2/#59, S3/#54/#81, dual-backend/#178, golden de-risk/S4), and the codebase is now demonstrably healthier on all three lenses. What remains is **refinement, not rot**: hexagonal polish (finish the rendering port, split the input port), DDD coupling cleanup (`Fighter`↔`Player` one-way), and tuning-provenance follow-through (ADR-0003 + drift-guard). This re-review is strong evidence the review→follow-up→re-review loop works.

The prior review's headline was that all three lenses converged on **one root cause: the 896-line `Player` god-aggregate (D1)**. Since #56, the team executed almost the entire DDD follow-up list. **Every ranked DDD finding (D1–D4) and the dual-backend debt is resolved**, the value-object layer held, and the ubiquitous language is now captured in `CONTEXT.md` + ADRs. The DDD lens moves from **~6/10 → ~8.5/10**.

What remains on DDD is no longer structural rot but two *coupling* smells introduced by the decomposition itself: a bidirectional `Fighter`↔`Player` link (domain rules reach back into the adapter) and a `Player.update()` that still ticks domain timers directly. Both are narrow, well-localized, and a natural next refinement — not a god-object.

**Hexagonal (~6/10 → ~7/10):** the same #69 decomposition that fixed D1 also extracted **Player's** rendering into the adapter (`render_battle`), the largest of #56's "entity owns a Surface" leaks. But the extraction is **partial** — `Attack`, `Platform`, and `Tail` still own their rendering (Surface/`image.fill`/self-draw), and `Tail` even imports the adapter (`from ..render_battle import tinted`), a layering inversion. The two prior architect decisions — **#9 split the input port** and **#10 sanction `pygame.math` value types** — remain open; `core/input.py` still binds the pure `InputFrame` port to the `poll()` pygame adapter in one module, leaking pygame into otherwise-pure consumers. The rules core itself (Fighter/combat/statecharts) is clean.

---

## Lens 1 (re-review) — DDD (domain model)

### Diff vs #56 — prior findings

| # | #56 finding | Status now | Evidence |
|---|---|---|---|
| **D1** | `Player` god-aggregate (896 lines, ≥7 concerns, inline FSM tables) | ✅ **Resolved** (#69, #178) | `Fighter` is now a Sprite-free rich aggregate (453 ln) owning combat state + rules + KO/lives + `receive_hit` (`fighter.py:62-156`, `:204-273`); `Player` is a thin sprite adapter (436 ln, "no longer owns a Surface" `player.py:93`); FSM tables left `player.py` for a declarative statechart `charts/fighter_chart.py:63` — the whole FSM step is one line `self.engine.tick(None)` (`player.py:381`). |
| **D2** | Triple move-progress (`move_frame` + `attack_timer` + `done_attacking`) hand-synced | ✅ **Resolved** (#71) | Single `MoveClock` owns progress (`move_clock.py:4-11`, `player.py:114`); former trackers are now derived read-only properties (`player.py:154-166`). Residual: `done_attacking` survives as a hand-latched *move-exit* flag (not progress state) — minor (see N3). |
| **D3** | Dead legacy `Attack(hitbox=None)` fallback + `ATTACK_SIZE/LIFETIME/HIT_DAMAGE` | ✅ **Resolved** (#70) | `ATTACK_LIFETIME`/`HIT_DAMAGE` retired (`config.py:77-79`); `Attack(hitbox=None)` now raises, not falls back (`attack.py:78-81`); only live construction passes `hitboxes=` (`player.py:369-372`). `ATTACK_SIZE` kept deliberately — render-only, real use (`attack.py:114`), not dead. |
| **D4** | Win-condition duplicated (`match_engine` mirrors `game.check_win_condition`) | ✅ **Resolved** | Single rule in `win_condition.winner_index` (`win_condition.py:11-22`); `match_engine` consumes it (`match_engine.py:9,21,34`); `game.check_win_condition` → `battle.winner()` → `winner_loser` (`game.py:204-207`, `battle_screen.py:92-94`). No second copy. |
| **Dual backends** | Two fighter FSMs (`state_engine` + `_sc`) and two match engines (Legacy/Statechart) to maintain | ✅ **Resolved** (#178, ADR-0002) | Legacy fighter, match, **and** screen engines deleted; statechart is sole backend (`state_engine.py:4-36`, `match_engine.py:4-42`); `--backend`/env-var selection gone (zero grep hits). Parity oracle converted to statechart-vs-frozen-golden. |

### Strengths that held (protect these)

- **Value objects intact and richer.** `Circle`/`Hitbox`/`MoveData`/`Hurtbox`/`FighterData` all still `@dataclass(frozen=True)` and now self-validating (`combat/data.py:38-212`, `__post_init__` window checks `:83-96`, `:132-155`). `load_fighter_data()` remains the repository/factory seam, evolved to per-archetype dispatch (`data.py:219-242`).
- **Authentic ubiquitous language, now documented.** `CONTEXT.md` captures the dialect (hurtbox/hitbox/BKB/KBG/startup-active-recovery/percent/hitstun) and explicitly names the new model: *fighter = pure domain, player = thin sprite adapter, MoveClock = single move-progress source*. Code, tests, tracker, and docs speak one language.
- **Invariants now enforced at the aggregate (was #56 Spec finding S3).** `Fighter` enforces `percent ≥ 0`, `0 ≤ shield_hp ≤ MAX`, `lives ≥ 0` at the setters (`fighter.py:165,176,184`) — the "enforce once at the mutation site" pattern #56 asked for, at least for these three. (Full S3 audit belongs to the BDD sub-spike.)

### New DDD findings (this re-review)

- **N1 — Aggregate boundary leak: `Fighter` ↔ `Player` is bidirectional.** `Fighter` keeps an `owner` back-reference (`fighter.py:67`) through which **domain rules reach back into the adapter**: `self.owner.engine.force("ko")` (`:329`), `self.owner.force_prone(...)` (`:301`), `self.owner._clock`, `self.owner.tail`, and notably `self.owner.state == "crouch"` (`:243`) — domain hit-resolution reading the *FSM/presentation state label*. The decomposition cleanly extracted the data but left the control coupling pointing both ways. Direction of dependency should be one-way (Player → Fighter).
- **N2 — `Player.update()` is a thick timer-ticking coordinator.** `update()` (`player.py:189-385`) reaches into `self.fighter.*` to advance domain timers (hurt/stun/prone/getup/landing-lag/shieldstun/dodge, `:287-333`) and spawn `Attack` hitboxes off the clock. Per-frame timer progression is *domain behaviour* living in the adapter; the aggregate should advance its own timers (e.g. `Fighter.tick()`), with `Player.update()` orchestrating, not reaching in. N1 and N2 are two faces of the same coupling and likely one structural pass.
- **N3 (minor) — `done_attacking` hand-latched in 3 sites.** Set False on attack start (`fighter_input.py:206`), latched True when the clock drains (`player.py:374-375`), reset on respawn (`fighter.py:139,372`). It's a move-exit signal, not redundant progress state, but it could be *derived* off the clock/state rather than manually maintained. Small decomplect.
- **(Not a defect) Functional-core knockback/hitstun.** `combat/knockback.py` etc. remain free functions over primitives — mildly anemic but pure/deterministic/testable; a defensible functional core, same verdict as #56.

### Score

**DDD: ~8.5/10** (was ~6/10). The structural debt that dominated #56 is gone; what remains is localized coupling polish.

### Provisional follow-ups (NOT filed — file when worked)

| Item | Finding | Size | Note |
|---|---|---|---|
| **F1** | N1 — make `Fighter`↔`Player` one-way: remove/narrow the `owner` back-ref; pass state-label/clock/engine effects in as params or via return-of-intent, so domain rules don't reach into the adapter | M | Highest-leverage remaining DDD item; touches `fighter.py` hot paths → needs its own scoping. |
| **F2** | N2 — move per-frame timer advancement into `Fighter` (`tick()`/`advance_timers()`); `Player.update()` orchestrates only | M | Pairs with F1 (same coupling). Do as one structural spike or sequence F1→F2. |
| **F3** | N3 — derive/encapsulate `done_attacking` as a move-exit signal off `MoveClock`/state | S | Cheap decomplect; easy after F1/F2. |

---

## Lens 2 (re-review) — Hexagonal (ports & adapters)

### Diff vs #56 — prior findings

| Concern | #56 | Status now | Evidence |
|---|---|---|---|
| **Rules core purity** | ✅ pure interior | ✅ **held** | `Fighter` is Sprite-free (`fighter.py` no `Sprite`/`Surface`); `combat/`, `statecharts/`, `sim/controllers` import no pygame (`controllers.py` fully pure — `InputFrame` + injected seeded RNG only). |
| **Input port** | ✅ port, ⚠ wart: port+adapter share `core/input.py` | ◐ **unchanged — decision #9 open** | `InputFrame` + `merge_frames` (pure, `core/input.py:9-39`) still share the module with the `poll()` pygame adapter (`:45-65`) and a module-level `import pygame` (`:3`) — so even the pure `controllers.py` transitively imports pygame. |
| **Rendering port** | ❌ absent (Player/Attack/Platform/Tail own `Surface`/`image.fill`) | ◐ **partial — Player done, 3 entities lag** | **Player ✅** rendering extracted to `render_battle` (`_cat_body_surface` `:435-460`; "no longer owns a Surface" `player.py:93`). **Attack ❌** still owns `self.image`/`image.fill`/`draw.circle` (`attack.py:114-132`, render-only; combat uses circles). **Platform ❌** still `image.fill(color)` state-as-colour (`platform.py:25-27`). **Tail ❌** draws itself in `Tail.draw` (`tail.py:240-266`). |
| **Sprite coupling** | ❌ entities inherit `Sprite` | ◐ **domain freed; adapters still Sprite** | Domain `Fighter` is Sprite-free ✅. `Player` (`player.py:64`), `Attack` (`attack.py:25`), `Platform` (`platform.py:15`) still subclass `pygame.sprite.Sprite`; `Tail` is a plain class. Acceptable for an adapter layer, but Attack/Platform are domain-ish entities still bound to the framework. |
| **Geometry value types** | ◐ `Vector2`/`Rect` in `physics`(13)/`movement`/`player` | ◐ **unchanged — decision #10 open** | `core/physics.py` (`Rect`/`Vector2`, value-type-only), `systems/movement.py` (`Vector2` only), `fighter.py` (`Rect`/`Vector2`). Pure geometry — deterministic, display-free — but literally `import pygame`. |
| **Time / RNG** | ✅ n/a | ✅ **held** | Frame-counter timing, no `pygame.time`; RNG only as an injected seeded seam in `controllers.py`. |

### New / refined hexagonal findings

- **H1 — Rendering port is half-built.** The #69 pattern (entity holds no Surface; `render_battle` composites it) was applied to `Player` but **not** to `Attack`, `Platform`, `Tail`. Those three still own presentation Surfaces / self-draw, so #56's "entity owns a Surface, state via `image.fill`" smell persists for them. Finishing the extraction would *complete* the rendering port and let `Attack`/`Platform` drop the `Sprite` base.
- **H2 — Layering inversion in `Tail`.** `tail.py:247` does `from ..render_battle import tinted` — a domain/entity module importing the **adapter** (render) layer. This is a direct dependency-direction violation (the hexagon's interior reaching out to an adapter) and the sharpest single hexagonal defect found. Should invert (pass the tint in, or move `Tail.draw` into `render_battle`).
- **H3 — Input port still not split (decision #9).** Because `core/input.py` does module-level `import pygame`, the pure port (`InputFrame`/`merge_frames`) cannot be imported without dragging pygame in — defeating part of the point of a port. Splitting the pure port into its own pygame-free module is small and unblocks a truly headless input contract.
- **H4 (doc accuracy) — `CONTEXT.md` "pygame-free `systems/`" is slightly off.** The determinism contract lists `systems/` as importing no pygame, but `systems/movement.py:3` imports `pygame as pg` (for `Vector2`). The *spirit* holds (deterministic, display-free), but the wording should be "Sprite-free + display-free" rather than "import no pygame", pending decision #10.

### Score

**Hexagonal: ~7/10** (was ~6/10). The biggest leak (Player rendering) is gone; the core is clean and the input/sim seams work. Held back by the half-finished rendering port (H1), the `Tail`→adapter inversion (H2), and the two still-open architect decisions (#9 input split, #10 `pygame.math`).

### Provisional follow-ups (NOT filed — file when worked)

| Item | Finding | Size | Note |
|---|---|---|---|
| **H-a** | H2 — fix the `Tail` → `render_battle` upward import (invert: pass tint in, or move `Tail.draw` to the renderer) | S | Sharpest defect; cheap; do first. |
| **H-b** | H1 — finish the rendering port: extract `Attack`/`Platform`/`Tail` Surfaces into `render_battle` (mirror the #69 Player pattern); drop their `Sprite` base where possible | M | Completes #56's rendering-port item; subsumes H-a if done together. |
| **H-c** | H3 / decision #9 — split `core/input.py` into a pygame-free port module + a `poll()` adapter module | S | Makes the pure path importable without pygame. |
| **H-d** | decision #10 — rule on `pygame.math` (`Vector2`/`Rect`) as sanctioned value types vs pure `Vec2`/`Rect`; then correct the `CONTEXT.md` wording (H4) | dec | Architect call; don't churn geometry until decided. |

---

## Lens 3 (re-review) — BDD (spec quality, able-to-fail tests, invariants)

### Diff vs #56 — prior findings (Lens 3 "Spec quality & robustness")

| # | #56 finding | Status now | Evidence |
|---|---|---|---|
| **S1** | Bare `pytest` unguarded — errored on legacy debug scripts; zero-byte stub collisions; sanctioned runner a hand-curated README list | ✅ **Resolved** (#59) | `pytest.ini` sets `testpaths = tests` + markers and notes legacy debug scripts moved to `scripts/`; bare `pytest -q` runs the whole suite green (573 passed, 1 xfailed). No zero-byte stubs. |
| **S2** | Non-test artifacts in `tests/` (`debug_*`, `comprehensive_*`, `minimal_*`, `run_test.py`, `*_SUMMARY.md`) | ✅ **Resolved** (#59) | Dev scripts relocated to `scripts/`; `*_SUMMARY.md` → `docs/`. `tests/` now holds only test modules + `conftest.py`/`golden_util.py`/`golden/`. |
| **S3** | Contracts emergent, not enforced — only **3 asserts/raises** in all source | ✅ **Resolved** | **12** real asserts/raises now. `Fighter` setters enforce `percent ≥ 0` / `0 ≤ shield_hp ≤ MAX` / `lives ≥ 0` (`fighter.py:166,179,184`); value objects validate in `__post_init__` (`combat/data.py:86-150`); `Attack` requires a hitbox (`attack.py:80`). **#54** (lives ≥ 0) now a setter clamp (#81), not emergent. |
| **S4** | Golden rubber-stamp risk — 1.18 MB opaque `full_match.json`, trivial `PYCATS_UPDATE_GOLDENS=1` regen | ✅ **Resolved** | Segmented into `combat`/`default`/`two_npc`/`full_match` (~125 KB) each paired with a ~0.6 KB reviewable `*.summary.json` semantic digest; `golden_util.summarize` asserts the summary **first** (`golden_util.py:162-164`); `REGEN_PROTOCOL.md` documents the threat + a reviewer checklist for spotting laundered regressions; `summarize` is itself unit-tested. Parity converted to statechart-vs-frozen-golden (`test_screen_parity.py:156-167`). |
| **S5** | Unsourced `⚠` tuning constants = no correctness spec (#51) | ◐ **Partial** | ~20 `⚠`/GUESS markers still inline across 7 files; **but** provenance is now governed — `ADR-0003` (tuning provenance + drift-guard, **Proposed**, gated on #226), `GUESSED_VALUES_TO_RESEARCH.md`, and a large `docs/research`/`docs/pm-reference` corpus. #51 still open/blocked. Drift-guard not yet implemented. |

### BDD-specific quality (the sharpened lens)

The test suite is **high quality** — among the more disciplined Python suites: **94 test modules / ~549 test functions**, broad and well-partitioned (combat/physics, entities/movement, render, golden/parity, data, settings, meta-guards).

- **Behavioral naming + Given/When/Then docstrings, zero vague names.** e.g. `test_crouch_lowers_hurtbox_high_attack_whiffs` (`test_crouch.py:126`), `test_hitstun_never_below_floor` (`test_knockback.py:36`), `test_airborne_361_launches_up_not_flat` (`test_sakurai_angle.py:112`). Docstrings frame expected behaviour + issue links.
- **Real assertions on boundaries & invariants, not happy-path-only.** Knockback monotonicity/floor + a 100-iteration sign-preservation invariant (`test_knockback.py:36-67`); shield sub-threshold edge (`test_shieldstun.py:48`); KO arcs reach `hurt→ko` and stocks drop (`test_golden.py:43-45`). Names match assertions (no "Liar"); no Giant/Free-Ride tests; healthy assert density.
- **Clean isolation** via `conftest.py` — `render_isolation` (#63) + an autouse `runtime_settings` reset (#121) defend against global-state leakage.
- **Exceptional able-to-fail / traceability discipline.** 82/94 files cite issue numbers; ~50 explicit "able-to-fail" annotations (e.g. `test_per_character_movement.py:98`, `test_controller_rng.py:47`); the `#112` strict-`xfail` self-completing guard is the canonical example — and the **only** suppression in the suite (no skip/xfail sprawl).
- **Minor nits (non-structural):** a few tests are positionally coupled to snapshot tuple layout (`p[1]`/`[9]`), mitigated by centralizing that in `golden_util.summarize`; one signature-introspection guard (`test_screen_parity.py:93`) is structural by design (guards against re-adding deleted plumbing).

### Score

**BDD: ~8.5/10** (was ~6/10). Suite is green/guarded, invariants are enforced, and the golden oracle is genuinely de-risked. Held back only by S5 (tuning provenance: ADR-0003 still *Proposed*, drift-guard unbuilt) and the minor tuple-coupling nit.

### Provisional follow-ups (NOT filed — file when worked)

| Item | Finding | Size | Note |
|---|---|---|---|
| **B-a** | S5 — accept ADR-0003 (gated on #226) and implement the tuning drift-guard; source the ~20 `⚠` constants (broadens #51) | M/dec | Only materially-open Lens-3 item; decision-gated. |
| **B-b** | Decouple goldens from snapshot tuple layout — assert via named accessors, not `p[1]`/`[9]` | S | Cheap robustness; shrinks blast radius of a layout change. |

---

## Final synthesis (cross-lens)

### Overall: the #56 follow-ups were executed, and it shows

pycats moved from "**~6/10 on all three lenses, one dominating root cause**" to **DDD ~8.5 · Hexagonal ~7 · BDD ~8.5**. The single highest-leverage #56 item — **decompose `Player` (D1)** — was done (#69) and, exactly as #56 predicted, *subsumed* the top hexagonal items (Player's rendering left the entity). The rest of the ranked list followed: test infra (S1/S2 → #59), invariants (S3 → #54/#81), the golden oracle (S4), the dual-backend endgame (#178/ADR-0002), and dead-code/duplication (D2/#71, D3/#70, D4). The protect-list strengths (pure rules core, frozen value objects, authentic language) all held and are now documented in `CONTEXT.md` + ADRs.

### What's left — ranked, cross-lens (provisional, file when worked)

| Rank | Item | Lens | Size | Why here |
|---|---|---|---|---|
| **1** | **H-a** — fix `Tail` → `render_battle` upward import (layering inversion) | Hex | S | Sharpest single defect; cheap; the only hard dependency-direction violation. |
| **2** | **F1+F2** — make `Fighter`↔`Player` one-way (drop `owner` back-ref; move per-frame timer ticking into `Fighter`) | DDD | M | Top DDD remainder; the decomposition's residual coupling. One structural spike. |
| **3** | **H-b** — finish the rendering port (extract `Attack`/`Platform`/`Tail` Surfaces; drop their `Sprite` base) | Hex | M | Completes #56's rendering-port item; subsumes H-a if done together. |
| **4** | **H-c / decision #9** — split `core/input.py` into a pygame-free port module + `poll()` adapter | Hex | S | Makes the pure path importable without pygame. |
| **5** | **B-a / S5** — accept ADR-0003 (#226) + build the drift-guard; source `⚠` constants (#51) | BDD | M/dec | Only materially-open spec item; decision-gated. |
| **6** | **decision #10** — rule on `pygame.math` value types; then fix `CONTEXT.md` "systems/ pygame-free" wording (H4) | Hex | dec | Architect call; don't churn geometry until decided. |
| **7** | **F3** — derive `done_attacking` off `MoveClock`/state | DDD | S | Cheap decomplect; after F1/F2. |
| **8** | **B-b** — decouple goldens from tuple-index layout | BDD | S | Robustness; low urgency. |

**Suggested next step:** the two architect decisions (#9, #10) and ADR-0003 (#226) are written-ruling-first, no-code items — settle them in `docs/adr/` so #4/#5/#6 unblock. The cheap structural wins (H-a, then F1+F2) pay for themselves first.

### Process note

All three sub-spikes were almost entirely **diffs**, and the diff is overwhelmingly green — the system working as designed: a review (#56) produced ranked follow-ups, the follow-ups were worked, and this re-review confirms it. The new findings (DDD N1/N2, Hex H1–H4, BDD's S5 remainder) are mostly *consequences of, or remainders after,* the big decomposition — second-order coupling and finishing touches — which is precisely what a re-review surfaces. Method note worth carrying forward: gathering each lens's evidence via parallel read-only investigations kept every claim file:line-cited and the spikes bounded.

---

## Appendix — F1+F2 slice plan (scoping spike #270)

Scope-first slicing of #264 item 2 (findings **N1** `Fighter`→`Player` back-reference + **N2** `Player.update()` ticks domain timers). Read-only enumeration; each slice below is single-deliverable, ≤60min, and ordered to keep the suite green at every step.

### Enumeration

**N1 — `self.owner.*` reaches in `fighter.py`:**

| Reach | file:line | Kind |
|---|---|---|
| `self.owner.state == "crouch"` | `:247` (in `receive_hit`) | state-label read (FSM/adapter) |
| `self.owner.force_prone(...)` | `:305` (in `receive_hit`) | transition (→ engine) |
| `self.owner.engine.force("ko")` | `:333` (in `_ko`) | transition (→ engine) |
| `self.owner._clock.reset()` | `:382` (in `reset_to_spawn`) | data reach (clock) |
| `self.owner.tail.reset()` | `:389` (in `reset_to_spawn`) | data reach (presentation) |
| `owner.SIZE` | `:83, :96` (`__init__`) | construction read |

*(`atk.owner.fighter.*` in `receive_hit` — `:223,232,252,277` — is the attacker↔defender link via the `Attack` object, legitimate domain↔domain; out of scope.)*

**N2 — timers in `player.update()`:**

- **Pure decrement** (`if t>0: t-=1`, no transition): `hitlag_timer` `:212`, `hurt_timer` `:340`, `stun_timer` `:342`, `landing_lag_timer` `:374`, `ledge_regrab_lockout_timer` `:376`, `shieldstun_timer` `:378`.
- **Decrement + transition** (reads `self.state` / calls `engine.force` / starts a clock): `respawn_timer` `:200`, `prone_timer→getup` `:344-361`, `getup_roll_timer` `:366`, `getup_attack_timer` `:370`, `ledge_hang_timer` `:292-303`, `dodge_timer` `:380-382`.

### Inversion shape (Q3 — resolved)

A **hybrid**, applied per-kind:
- **Pure timers** → a `Fighter.tick_timers()` the aggregate owns (no owner needed).
- **Coupled timers** → `Fighter` advances them and **returns expiration events**; `Player.update()` maps events → `engine.force`/`_clock.start` (transitions stay in the adapter layer, which is correct — the Fighter reports *what expired*, the Player decides *what that means for the FSM*).
- **`receive_hit`/`_ko` transitions** → same **return-intent** pattern (`receive_hit`/`_ko` return e.g. `("force","ko")`/`("force","prone")`; `combat.process_hits` / the caller applies it).
- **state-label read** → pass the defender's crouch state in (or a `Fighter.is_crouching` flag) instead of reading `owner.state`.
- **reset/construction reaches** → `Player` owns `_clock`/`tail` reset and passes `size` into `Fighter(...)`.

Rejected: a pure injected-engine-port on `Fighter` (keeps a control dependency on the engine inside the domain; return-intents keep `Fighter` free of the engine entirely).

### Ranked DEV slices (file one at a time under #264; not pre-filed)

| # | Slice | N | Size | Covering oracles (behaviour-neutral net) |
|---|---|---|---|---|
| **S1** | `Fighter.tick_timers()` owns the 6 **pure** decrements; `Player.update()` calls it | N2 | S | `tests/golden/*` (combat/two_npc/full_match), `test_shieldstun.py`, `test_hitlag.py`, `test_knockback.py` (hitstun floor) + new unit: each pure timer −1, floors at 0 |
| **S2** | crouch state-label: pass defender crouch-state into `receive_hit` (drop `owner.state`) | N1 | S | `test_crouch.py` (crouch-cancel whiff) |
| **S3** | `Player` owns `_clock`/`tail` reset + pass `size` into `Fighter()` (drop those `owner` reaches) | N1 | S | respawn/reset tests, `tests/golden/*` |
| **S4** | `Fighter.tick()` advances **coupled** timers, returns expiration events; `Player` maps → transitions | N2 | M | `test_prone*`, `test_getup_roll`/`#146`, `test_getup_attack`/`#225`, `test_dodge_mechanics.py`, `test_ledge*`, goldens |
| **S5** | return-intent for `receive_hit`/`_ko` transitions (`force_prone`, `engine.force("ko")`); caller applies | N1 | M | `test_combat.py`, knockback/KO + blast-zone tests, goldens — **hardest; do after the pattern is proven** |
| **S6** | drop the `owner` back-ref entirely + AST guard (Fighter has no `self.owner.` except `atk.owner`) | N1 | S | new able-to-fail structural guard (mirrors the #265 tail guard) |

**Order rationale:** S1–S3 are isolated, low-risk confidence-builders; S4 establishes the event-return pattern; S5 (the high-blast-radius `process_hits` change) lands once that pattern is proven; S6 is the enforcing capstone. The suite stays green at every step.
