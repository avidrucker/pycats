# pycats architecture review — DDD · Hexagonal · Spec quality (2026-06)

**Ticket:** #56 (research umbrella) · **Reviewer:** CHERRY · **Date:** 2026-06-25
**Method:** three bounded read-only sub-spikes, one per lens, findings logged on #56 as they completed. This doc consolidates them and produces the cross-lens ranked follow-up list.

> **Status of the follow-ups below:** *provisional and not yet filed as tickets.* Per yegor (and the #50 lesson), they are filed one at a time, scoped to ≤60min, when about to be worked — not mass-created here. This doc is the architect-mode output; execution is courier-mode, later.

---

## Executive summary

pycats is a **pure, well-modelled rules core wrapped in a leaky entity/presentation shell.** All three lenses independently scored **~6/10** and converged on the **same root cause**: an 896-line `Player` god-object that braids domain state, rules, input, physics, presentation, and animation — sitting on top of a genuinely good value-object/data layer and a deterministic, pygame-free systems core.

| Lens | Score | One-line |
|---|---|---|
| Hexagonal (ports & adapters) | ~6/10 | Pure core + clean input port; **no rendering port**, entities are `Sprite`s holding `Surface`s |
| DDD (domain model) | ~6/10 | Exemplary value objects + authentic language; **`Player` god aggregate** + dual-model migration debt |
| Spec quality & robustness | ~6/10 | Strong bug-driven test net; **contracts unenforced** (3 asserts in all source) + fragile test infra |

**The convergence is the headline:** the single biggest follow-up — **decompose `Player`** — absorbs the top finding of every lens. That is strong evidence the priority is real, not an artifact of one viewpoint.

---

## What is genuinely good (protect this)

- **A pure domain core.** `combat/` (knockback, data, geometry), `statecharts/`, `systems/` (combat, match_engine, state_engine, state_engine_sc, fsm), `sim/controllers`, `characters/`, `config`, `stats_print` import no pygame and are **RNG-free and wall-clock-free** (frame-counter timing). The rules engine runs headless and deterministic.
- **Exemplary value objects.** `combat/data.py` — frozen `Circle`/`Hitbox`/`MoveData`/`Hurtbox`/`FighterData`, with `load_fighter_data()` as a repository/factory seam.
- **Authentic ubiquitous language.** hurtbox, hitbox, BKB/KBG, startup/active/recovery, percent, hitstun — matching the #39/#40 specs and SSBWiki. Code and tracker speak the same dialect.
- **A real input port.** `InputFrame` + `merge_frames` + pure `controllers.py`; controls injected as a dict (no `K_*` keycode coupling in entities).
- **Layered test oracles.** parity (legacy ≡ statechart, byte-identical) + golden snapshots + semantic state-reachability assertions; 196 bug-driven tests.

---

## Lens 1 — Hexagonal (ports & adapters)

**Map:** pure core (above) is the hexagon's interior. Ports/adapters status:

| Concern | Port? | Note |
|---|---|---|
| Input | ✅ good | `InputFrame` port + `poll()` (pygame) / `controllers` (scripted) adapters. Wart: port + pygame adapter share `core/input.py`. |
| Rendering | ❌ absent | `Player`/`Attack`/`Platform`/`Tail` own `self.image = Surface(...)` and encode state as `image.fill(RED/…)` (player.py:418–427, 720, 725, 731, 896). State→tint is domain logic expressed as an adapter mutation. |
| Sprite framework | ❌ | Entities inherit `pygame.sprite.Sprite`; physics passes `sprite.Group`. |
| Geometry types | ◐ | `Vector2`/`Rect` as domain value types in `player`/`physics`(densest, 13)/`movement`. |
| Time / RNG | ✅ n/a | No coupling; frame counters, no `pygame.time`/`random`. No port needed. |

**"Headless works" caveat:** the `SDL_VIDEODRIVER=dummy` path proves the seam exists, but rendering isn't ported *out* — the `Surface` calls are *satisfied by the dummy driver*, not removed.

---

## Lens 2 — DDD (domain model)

**Good:** the value-object layer and language (above). The new model is wired in, not aspirational — `Player.fighter_data` drives moves via `MoveData`; `systems/combat.process_hits` does circle-vs-`hurtbox.circles` collision.

**Bad:**
- **`Player` is a god aggregate (896 lines)** complecting ≥7 concerns, including the **FSM transition tables embedded inline** (player.py:783–878).
- **Triple move-progress representation** — `move_frame` (new) + `attack_timer` (legacy) + `done_attacking` (legacy) all track "where in the move are we" and must stay in sync (player.py:617–628).
- **Dead legacy model present** — `Attack(hitbox=None)` rect fallback is unreachable (only live call passes `hitbox=`); `ATTACK_SIZE/ATTACK_LIFETIME/HIT_DAMAGE` linger in `config`/`attack`/`sim`.
- **Duplicated win-condition** — `systems/match_engine` "Mirrors `game.check_win_condition`": same rule, two homes.
- **Dual backends ×2** — fighter FSM (`state_engine` + `state_engine_sc`) and match (`Legacy`/`Statechart` engines). Deliberate, parity-tested migration scaffolding — but two models to maintain until the migration *finishes*.
- *(Minor)* knockback/hitstun are free functions over primitives — mildly anemic, but pure/testable; defensible functional-core. Not a defect.

---

## Lens 3 — Spec quality & robustness

**Good:** 196 bug-driven tests with real assertions (parity byte-identical + semantic reachability; knockback boundary tests), headless-by-design (`conftest.py`), honest `⚠` tuning markers.

**Risks:**
1. **Contracts emergent, not enforced** — only **3 asserts/raises in all source**. `lives ≥ 0` (now #54), `shield_hp` bounds, `percent ≥ 0`, transition legality hold only because the loop happens not to violate them; verified only in tests. #54 was one instance of a systemic shape.
2. **Test collection unguarded** — `pytest.ini` adds no `--ignore`/`norecursedirs`, so bare `pytest` errors on legacy debug scripts (+ "4 zero-byte root stubs share basenames"). Sanctioned runner is a hand-curated ~20-file README list → new tests added manually (silent gaps); CI/agents can't just run `pytest`.
3. **Non-test artifacts in `tests/`** — `debug_*`, `comprehensive_*`, `minimal_*`, `run_test.py`, two `*_SUMMARY.md`.
4. **Golden rubber-stamp risk** — 1.18 MB opaque `full_match.json`; `PYCATS_UPDATE_GOLDENS=1` regen is trivial, so a regression can be re-recorded without scrutiny. Mitigated (not removed) by semantic assertions.
5. **Unsourced tuning = no correctness spec** — `⚠` constants (cf #51); no spec for "correct" combat feel.

---

## Cross-lens ranked follow-up list

Ranked by leverage and dependency, not severity. **Rationale for the order:** S1 unblocks all refactor work (you cannot safely decompose `Player` without a trustworthy green suite); the decomposition (D1) is the high-value structural fix and *subsumes* two hexagonal items; cheap cleanups and enforced-invariant work follow; pure decisions go last (architect-mode, no code until decided).

| Rank | Item | Lens(es) | Size | Why here |
|---|---|---|---|---|
| **1** | **S1 — make bare `pytest` green** (ignore/relocate legacy scripts, kill zero-byte stub collisions) | Spec | S/M | **Enabler.** No safe refactor without one trustworthy runnable suite. |
| **2** | **D1 — decompose the `Player` god aggregate** (extract `Fighter` domain from presentation/input/physics/tail/inline-FSM) | DDD + Hex | **L** | Top finding of all three lenses. **Subsumes hexagonal #1 (rendering port) + #2 (Sprite decouple).** Likely its own spike to slice into ≤60min units. |
| **3** | D3 — remove dead `Attack(hitbox=None)` fallback + retire `ATTACK_SIZE/LIFETIME/HIT_DAMAGE` once confirmed unused | DDD | S | Cheap; shrinks the surface D1 must move. |
| **4** | D4 — de-duplicate win-condition (`match_engine` vs `game.check_win_condition`) | DDD | S/M | Cheap correctness win; single source. |
| **5** | S2 — relocate non-test artifacts out of `tests/` | Spec | S | Overlaps S1; do together. |
| **6** | D2 — unify move-progress (`move_frame`/`attack_timer`/`done_attacking` → one source) | DDD | M | Decomplect; easier post-D1. |
| **7** | S3 — enforce key invariants at mutation sites (`shield_hp`, `percent`, transitions), per the #54 pattern | Spec | M | Easier on smaller units (post-D1); splits into small tickets. |
| **8** | S4 — de-risk the golden oracle (segment/shrink `full_match.json`; regen-review protocol) | Spec | M | Reduces rubber-stamp risk. |
| **9** | **Decision** — input port split (`InputFrame` vs `poll()` into separate modules) | Hex | S | Small but waits for D1's shape. |
| **10** | **Decision** — `pygame.math` (`Vector2`/`Rect`) sanctioned vs pure `Vec2`/`Rect` | Hex | dec | Architect call; don't churn until decided. |
| **11** | **Decision** — dual-backend endgame: finish statechart migration (delete legacy) or keep both forever | DDD | dec | Governs fighter FSM + match engine maintenance. |
| **12** | S5 / #51 — source & validate the `⚠` combat tuning constants | Spec | M | Broaden #51 from one symptom to a tuning/spec pass; link, don't dup. |

### Suggested immediate next steps (after #56 closes)
1. File **S1** as the next child ticket and land it — it pays for itself immediately (green `pytest`, CI-able, agent-runnable).
2. Run a **D1 scoping spike** (yegor-spikes) to slice the `Player` decomposition into ≤60min units before adding any `@todo`/tickets.
3. Treat #9–#11 as **architect-mode decision tickets** (write the ruling first; no code until decided).

### Process note
Sub-spike 1 surfaced "extract a rendering port" as an independent follow-up. Sub-spike 2 then showed it is one slice of the larger `Player` decomposition (D1). Had we executed it immediately, we'd have built a partial abstraction needing rework — concrete, in-review evidence for finishing the investigation before acting (logged on #56). Also worth seeding from this review: a first `CONTEXT.md` (ubiquitous language is strong enough to capture) and `docs/adr/` for decisions #9–#11.
