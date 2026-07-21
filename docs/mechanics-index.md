# pycats mechanics index (router)

**The front door to "where does mechanic X live, and which doc describes it?"** One row per
pycats-**invented** or PM-**divergent** mechanic, each pointing at its code **landmark**
(*pkg/mod.py::Symbol*) and its **owner** (the one place to read about it). PM-faithful
mechanics live in `docs/pm-reference/` and are out of scope here.

This is a **router, not a reference** — it points, it doesn't re-explain. It's promoted from
the survey in `docs/research/2026-07-07-custom-mechanics-inventory.md` (#605); the prose
reference *custom-pycats-mechanics.md* (#604) will become the owner of the architectural
rows once it lands. The index is **guarded**: `tests/test_doc_landmarks.py` (#737) reds if a
landmark stops resolving, if a registered value-divergence has no row, if a curated
architectural mechanic drops out, or if any cited path goes missing — so this file cannot
silently rot the way unguarded prose does.

**Landmark form:** *pkg/mod.py::Symbol* names a module-scope def / class / constant. A
mechanic that spans several symbols lists them all. The `§` column cites the source section
in the #605 inventory.

---

## A. Architectural / convention mechanics

Invented engine architecture and conventions — the mechanics that aren't a single tuning
number. Owner today is the #605 inventory (the section named in `§`); #604 supersedes it.

| Mechanic | § | Landmark(s) | Owner | Class |
|---|---|---|---|---|
| Declarative status table | §1.1 | `pycats/render_battle.py::StatusSource`, `pycats/render_battle.py::STATUS_SOURCES`, `pycats/render_battle.py::active_tint`, `pycats/render_battle.py::timer_bar_specs` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented render architecture |
| Exclusive-vs-overlay bar precedence | §1.2 | `pycats/render_battle.py::StatusSource`, `pycats/render_battle.py::active_tint`, `pycats/render_battle.py::timer_bar_specs` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented priority model |
| Status-bar / dev-info runtime flags | §1.3 | `pycats/runtime_settings.py::show_status_timer_bars`, `pycats/runtime_settings.py::show_dev_info` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented render toggles |
| Archetype vs cosmetic-skin naming split | §1.4 | `pycats/characters/roster.py::ARCHETYPE_DEFAULT_SKIN`, `pycats/characters/roster.py::ARCHETYPE_PALETTE` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented identity split |
| `"attack"` legacy move-key alias | §3.1 | `pycats/combat/move_select.py::resolve_move_key`, `pycats/combat/move_select.py::select_move_key` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented naming convention |
| `MoveClock` temporal windows | §3.2 | `pycats/combat/move_clock.py::MoveClock`, `pycats/combat/move_clock.py::MoveTick` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented state consolidation |
| up-B / special-recovery hook | §3.3 | `pycats/combat/data.py::MoveData`, `pycats/entities/fighter.py::Fighter` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented move-data extension |
| Statechart flag→state routing | §4.1 | `pycats/charts/fighter_chart.py::build_fighter_chart` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented statechart convention |
| Sim goldens — byte detector + semantic sidecar | §5.1 | `tests/golden_util.py::check_or_update`, `tests/test_golden.py::test_golden_default` | `tests/golden/REGEN_PROTOCOL.md` | invented oracle model |
| Render-parity byte oracle | §5.2 | `tests/test_battle_screen_render.py::test_render_matches_inline_playing_composition` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented divergence guard |
| Screen-flow parity (statechart == frozen golden) | §5.3 | `tests/test_screen_parity.py::test_screen_engine_initial_state` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented equivalence freeze |
| `dev_log` — gated not-yet-implemented breadcrumb | §6.1 | `pycats/dev_log.py::enabled`, `pycats/dev_log.py::reset`, `pycats/dev_log.py::_log_path` | `docs/research/2026-07-07-custom-mechanics-inventory.md` | invented dev tool |

---

## B. Value divergences (config constants)

The invented / departed tuning numbers. Each lives as a plain literal in `pycats/config.py`
and carries a provenance row in `pycats/combat/provenance.py` (owner) with its `source`,
`status`, and derivation. The **status** here (`DIVERGENCE` = intentional departure from a
known canon value; `TUNED` = deliberate design value not seeking canon) is the exact token
in that registry — the value/drift lock-step is guarded by `tests/test_tuning_provenance.py`;
this router's guard only checks that **every** DIVERGENCE/TUNED constant appears below (none
silently dropped) and that its landmark resolves. `FOUND` (PM-sourced) and `GUESS` (unsourced
playtest starts) rows are out of scope — read them straight from the registry.

| Constant | Landmark | Status | Owner | Note |
|---|---|---|---|---|
| `MAX_FALL_SPEED` | `pycats/config.py::MAX_FALL_SPEED` | DIVERGENCE | `pycats/combat/provenance.py` | single global fall speed; no base/fast-fall split |
| `KNOCKBACK_LAUNCH_FACTOR` | `pycats/config.py::KNOCKBACK_LAUNCH_FACTOR` | DIVERGENCE | `pycats/combat/provenance.py` | scaled to the 960px stage |
| `KNOCKBACK_DECAY` | `pycats/config.py::KNOCKBACK_DECAY` | DIVERGENCE | `pycats/combat/provenance.py` | 960px-scaled, preserves 1.7 decay/launch ratio |
| `GETUP_ROLL_FRAMES` | `pycats/config.py::GETUP_ROLL_FRAMES` | DIVERGENCE | `pycats/combat/provenance.py` | shorter roll; duration == intangibility window |
| `DODGE_SPEED` | `pycats/config.py::DODGE_SPEED` | TUNED | `pycats/combat/provenance.py` | ground-roll boost; no single canon |
| `JOSTLE_MIN_VOVERLAP_FRAC` | `pycats/config.py::JOSTLE_MIN_VOVERLAP_FRAC` | TUNED | `pycats/combat/provenance.py` | vertical-overlap gate for X-only push |
| `SHIELD_MAX_HP` | `pycats/config.py::SHIELD_MAX_HP` | TUNED | `pycats/combat/provenance.py` | pycats shield-HP model |
| `SHIELD_DRAIN_PER_FRAME` | `pycats/config.py::SHIELD_DRAIN_PER_FRAME` | TUNED | `pycats/combat/provenance.py` | shield drain/regain rate, no canon |
| `HITSTUN_FLOOR` | `pycats/config.py::HITSTUN_FLOOR` | TUNED | `pycats/combat/provenance.py` | ≥1f floor for any clean hit |
| `SAKURAI_AIRBORNE_DEG` | `pycats/config.py::SAKURAI_AIRBORNE_DEG` | TUNED | `pycats/combat/provenance.py` | keyed to pycats knockback magnitude |
| `SAKURAI_GROUNDED_MAX_DEG` | `pycats/config.py::SAKURAI_GROUNDED_MAX_DEG` | TUNED | `pycats/combat/provenance.py` | grounded max angle at HIGH_KB |
| `SAKURAI_GROUNDED_LOW_KB` | `pycats/config.py::SAKURAI_GROUNDED_LOW_KB` | TUNED | `pycats/combat/provenance.py` | grounded angle flat below this KB |
| `SAKURAI_GROUNDED_HIGH_KB` | `pycats/config.py::SAKURAI_GROUNDED_HIGH_KB` | TUNED | `pycats/combat/provenance.py` | grounded angle maxes at this KB |
| `KNOCKDOWN_VY_THRESHOLD` | `pycats/config.py::KNOCKDOWN_VY_THRESHOLD` | TUNED | `pycats/combat/provenance.py` | auto-knockdown impact-speed gate |
| `KNOCKDOWN_PRONE_FRAMES` | `pycats/config.py::KNOCKDOWN_PRONE_FRAMES` | TUNED | `pycats/combat/provenance.py` | fixed ~0.5s getup window |
| `GETUP_ROLL_SPEED` | `pycats/config.py::GETUP_ROLL_SPEED` | TUNED | `pycats/combat/provenance.py` | getup-roll horizontal speed |
| `LEDGE_GETUP_FRAMES` | `pycats/config.py::LEDGE_GETUP_FRAMES` | TUNED | `pycats/combat/provenance.py` | neutral ledge-getup climb |
| `GROUND_FRICTION` | `pycats/config.py::GROUND_FRICTION` | TUNED | `pycats/combat/provenance.py` | friction knob (1.0=ice); no PM equivalent |
| `AIR_FRICTION` | `pycats/config.py::AIR_FRICTION` | TUNED | `pycats/combat/provenance.py` | air friction knob; no PM equivalent |
| `HURT_TIME` | `pycats/config.py::HURT_TIME` | TUNED | `pycats/combat/provenance.py` | hurt/flinch timer; no PM canon |
| `LEDGE_REGRAB_LOCKOUT_FRAMES` | `pycats/config.py::LEDGE_REGRAB_LOCKOUT_FRAMES` | TUNED | `pycats/combat/provenance.py` | post-release regrab-suppression window |
| `PLAYER_ATTACK_DURATION` | `pycats/config.py::PLAYER_ATTACK_DURATION` | TUNED | `pycats/combat/provenance.py` | default attack duration; no PM canon |
| `INITIAL_LIVES` | `pycats/config.py::INITIAL_LIVES` | TUNED | `pycats/combat/provenance.py` | ruleset stock count, not a physics value |
| `RESPAWN_DELAY_FRAMES` | `pycats/config.py::RESPAWN_DELAY_FRAMES` | TUNED | `pycats/combat/provenance.py` | ~2s respawn freeze; ruleset value |
| `PLAYER_SIZE` | `pycats/config.py::PLAYER_SIZE` | TUNED | `pycats/combat/provenance.py` | default collision box (render→collision, #598) |
| `LEDGE_CATCH_W` | `pycats/config.py::LEDGE_CATCH_W` | TUNED | `pycats/combat/provenance.py` | ledge-grab catch-region width |
| `LEDGE_CATCH_H` | `pycats/config.py::LEDGE_CATCH_H` | TUNED | `pycats/combat/provenance.py` | ledge-grab catch-region height |
| `BLAST_PADDING` | `pycats/config.py::BLAST_PADDING` | TUNED | `pycats/combat/provenance.py` | KO boundary px beyond screen edge (bottom + L/R baseline) |
| `BLAST_PADDING_TOP` | `pycats/config.py::BLAST_PADDING_TOP` | TUNED | `pycats/combat/provenance.py` | top KO line 100px higher than bottom (#823) |

> The GUESS rows (`DODGE_FRAMES`, `DODGE_TIME`, `PROJECTILE_GRAVITY`, `PROJECTILE_RESTITUTION`,
> `PROJECTILE_MAX_BOUNCES`, `DASH_DURATION`, `FSMASH_ANGLE_UP`, `FSMASH_ANGLE_DOWN`) are
> unsourced playtest starts, not divergences — the #319 value-sourcing pass resolves them.
> Read them from `pycats/combat/provenance.py` (status `GUESS`); they are not indexed here.

---

## C. Doc index (which doc owns what)

The primary docs a new agent reaches for, and how to treat each. **Class** legend:
**authoritative** = the single source of truth for its topic (edit here); **derived-pointer**
= points at an authoritative source and must not diverge; **research-archive** = dated
findings, kept for provenance, not a live spec.

| Doc | Role | Class |
|---|---|---|
| `README.md` | run / test / setup; points at the `Makefile` command SSOT (#725) | authoritative |
| `RULES.md` | project conventions, filing/closing discipline | authoritative |
| `CLAUDE.md` | agent front door (auto-loaded), links the critical rules | authoritative |
| `docs/mechanics-index.md` | **this router** — where each invented/divergent mechanic lives | authoritative |
| `pycats/config.py` | the tuning-value SSOT (plain literals, no loader — ADR-0003) | authoritative |
| `pycats/combat/provenance.py` | *why* each value is what it is (source/status/derivation) | authoritative |
| `docs/decisions-ledger.md` | ratified design/decision record | authoritative |
| `docs/glossary.md` | project term definitions | authoritative |
| `docs/mechanics-faq.md` | plain-language mechanics Q&A | derived-pointer |
| `docs/project-m-parity.md` | PM parity tracker (the parity effort's map) | authoritative |
| `docs/parity-status.md` | per-mechanic PM parity status | authoritative |
| `docs/roadmap.md` | forward-looking work map | authoritative |
| `docs/research/2026-07-07-custom-mechanics-inventory.md` | the #605 survey this router promotes | research-archive |
| `docs/research/2026-07-08-ergonomics-ssot-decisions.md` | the #724 SSOT-hygiene decision rationale | research-archive |

PM canon lives under `docs/pm-reference/`; dated investigations under `docs/research/`;
architecture decisions under `docs/adr/`. Full doc-tree classification is a separate pass
(#724 Wave 3 / #7b) — this table is the thin front-door map, not the exhaustive index.

---

## Refs
Parent **#724** (Wave 2). Seed **#605** (`docs/research/2026-07-07-custom-mechanics-inventory.md`).
Prose reference (future owner of section A) **#604**. Guard: `tests/test_doc_landmarks.py`.
Value-layer precedent this mirrors: `pycats/combat/provenance.py` ↔ `tests/test_tuning_provenance.py`.
Rationale: `docs/research/2026-07-08-ergonomics-ssot-decisions.md` (#727). Command SSOT: #725.
