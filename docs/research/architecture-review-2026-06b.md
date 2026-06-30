# pycats architecture review (re-review) — DDD · Hexagonal · BDD (2026-06b)

**Umbrella:** #252 · **This section:** #253 (sub-spike 1/3, DDD) · **Reviewer:** GRAPE · **Date:** 2026-06-30
**Method:** three bounded read-only sub-spikes, one per lens, building on the prior pass [`architecture-review-2026-06.md`](./architecture-review-2026-06.md) (#56). Each section **diffs the prior findings** (resolved / regressed / new) rather than re-deriving from scratch.

> **Status:** DDD lens complete (this doc). Hexagonal (sub-spike 2) and BDD (sub-spike 3) sections are appended later under #252. Follow-ups below are **provisional and not yet filed** — per yegor + the #50 lesson, file one at a time when about to be worked.

---

## Executive summary (provisional — DDD only so far)

The prior review's headline was that all three lenses converged on **one root cause: the 896-line `Player` god-aggregate (D1)**. Since #56, the team executed almost the entire DDD follow-up list. **Every ranked DDD finding (D1–D4) and the dual-backend debt is resolved**, the value-object layer held, and the ubiquitous language is now captured in `CONTEXT.md` + ADRs. The DDD lens moves from **~6/10 → ~8.5/10**.

What remains is no longer structural rot but two *coupling* smells introduced by the decomposition itself: a bidirectional `Fighter`↔`Player` link (domain rules reach back into the adapter) and a `Player.update()` that still ticks domain timers directly. Both are narrow, well-localized, and a natural next refinement — not a god-object.

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

## Process note

This DDD sub-spike was almost entirely a **diff**, and the diff is overwhelmingly green: #56's DDD/structure follow-ups (D1–D4 + dual-backend) were genuinely executed (#69, #70, #71, #178) and the recommended `CONTEXT.md`/ADR seeds landed. That is the system working as designed — a review that produced ranked follow-ups, which were worked, and a re-review that confirms it. The two new findings (N1/N2) are *consequences of the decomposition*, exactly the kind of second-order coupling a re-review is for. The Hexagonal sub-spike (#252 next) should re-check the rendering-port / Sprite-coupling items — `Player` no longer owns a Surface (`player.py:93`), so #56's hexagonal #1 may also be resolved; that needs its own pass. CONTEXT.md's architecture-review link should be repointed to this doc only once all three lenses are complete (final synthesis).
