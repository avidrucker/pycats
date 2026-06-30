# pycats — current Project M parity progress report

> A living implementation-completeness snapshot: mechanic by mechanic, **what is at
> full Project M parity, what is partial/diverged, and what is absent** — each row
> grounded in the live code (`file:func`) and measured against the documented PM
> target in `docs/research/*` and `docs/pm-reference/*`. This is the *status*
> companion to #99 (`docs/project-m-parity.md`), which records the *rationale* for
> intentional divergences.
>
> **Last combed at commit `b9a71ad`.** Method: six parallel subsystem auditors
> (combat core · moveset/hitboxes · movement/states · fighters/archetypes ·
> AI-CPU/determinism · screens/match-flow), each reading the working tree and the
> matching PM-oracle doc. Date: 2026-06-29. Agent: DRAGONFRUIT. Ticket #189.
> **Perishable** — re-comb (re-run the audit) rather than trusting an old report;
> the codebase moves fast (the main branch advanced mid-audit).

## Legend

- ✅ **Full parity** — implemented and behaviorally matches the documented PM target.
- 🟡 **Partial / diverged** — present but incomplete, simplified, or deliberately
  different (intentional divergences are tagged *(intentional)* and link #99).
- ⬜ **Absent** — not implemented; the tracking issue is linked where one exists.
- **Confidence** = how well the code was confirmed to match the PM target (high/med/low).

## Headline

pycats has a **solid, correct combat-math core and a real per-character data spine**,
but it is **early on content and movement tech**, and most *systems* that exist are
**one-fighter-deep**. Rough tally across ~95 audited mechanics: **~25 ✅ full**,
**~28 🟡 partial/diverged**, **~42 ⬜ absent** (the denominator is judgment-dependent;
the per-subsystem tables are authoritative). The split by subsystem:

| Subsystem | Shape of parity |
| --- | --- |
| **Combat core** | ✅ the hard math is done & faithful (knockback formula, hitstun, hitlag, shieldstun, shield-break). 🟡 tuning constants & shield model simplified. ⬜ a whole coherent **defense cluster** (DI/SDI/ASDI/tech) + shield pushback are unbuilt. |
| **Moveset** | ✅ the **engine/seam** is real (frame data, multi-hitbox, ground/air move-selection). ⬜ the **content** is ~3 moves on one cat; tilts/smashes/dash/aerials/specials/stale-negation/Sakurai-angle absent. |
| **Movement/states** | ✅ jumps, dodges (spot/roll), crouch, drop-through. 🟡 air dodge is a **Brawl-style hybrid, not PM Melee-style** (no helpless). ⬜ short-hop/fast-fall/DJC/dash-dance/pivot/**ledge**/**wavedash**/**L-cancel** — most PM movement tech. |
| **Fighters** | ✅ the per-character **infrastructure** (weight + 5 movement constants + crouch geometry, proven able-to-fail). 🟡/⬜ the **content**: only **2 distinct fighters** (default + partial Nalio); 4 of 5 archetypes are names-in-comments; the 6 selectable "cats" are recolor skins. |
| **AI / CPU** | ✅ seeded-RNG seam (#166); determinism (intentional divergence). 🟡 three demo/benchmark controller archetypes. ⬜ **no player-facing CPU opponent at all**, no 1–9 difficulty ladder (research-only). |
| **Screens/flow** | ✅ pause, win/results screen. 🟡 minimal main-menu/CSS/options + intentional rematch divergence; the statechart screen engine is wired behind the `PYCATS_SCREEN_BACKEND` toggle (legacy default). ⬜ **battle isn't a real game-state** yet (#100 port mid-flight), stage/time/match settings absent. |

**The three biggest structural gaps:** (1) PM **movement tech** (ledge + wavedash +
L-cancel + dash/fast-fall), (2) **moveset content** beyond one cat's 3 moves, and
(3) the **statecharts screen-flow port** (battle-as-a-state, #100). The biggest
*latent* strength: the combat-math core and the data-driven character spine are
correct and tested, so the missing pieces are mostly **content + new states on a
sound engine**, not rewrites.

---

## 1. Combat core — knockback / hitstun / hitlag / shield / clank / defense

| Mechanic | Status | Evidence | PM source / issue# | Conf |
|---|---|---|---|---|
| Real Brawl/PM knockback formula | ✅ | `combat/knockback.py:knockback()` — exact `((p/10+p·d/20)·(200/(w+100))·1.4+18)·(KBG/100)+BKB`, fed per-fighter weight + per-hitbox BKB/KBG | SmashWiki Knockback; #40 | high |
| Hitstun-from-knockback | 🟡 | `knockback.py:hitstun_frames()` = `floor(KB·0.4)` → `hurt_timer`; `HITSTUN_FLOOR=1` self-flagged "not sourced"; no hitstun-cancel modeling | #40 | high |
| Knockback decay / launch trajectory | 🟡 | `decay_velocity()` + `player.py` bleed `vel.x` by `KNOCKBACK_DECAY`; launch=`KB·LAUNCH_FACTOR`. Pixel-scaled tuning constants (0.085/0.145), self-flagged ⚠ | knockback-launch-physics-findings.md; #43/#44 | high |
| Hitlag / freeze frames | ✅ | `knockback.py:hitlag_frames()`=`min(30,floor(d·0.3846+5))`; both fighters frozen via `hitlag_timer`; h/e/c=1 (documented deferral) | SmashWiki Hitlag; #138 | high |
| Shieldstun | ✅ | `shield.py:shieldstun_frames()`=`floor(d·0.345)`; locks defender via `shieldstun_timer` | SmashWiki Shieldstun; #140 | high |
| Shield HP / deplete / regen | 🟡 *(intentional)* | `player.py` 0.2/0.2 symmetric, `SHIELD_MAX_HP=50`; PM is 0.28/0.07 asymmetric + 0.7× mult — simplification logged | brawl-projectm-fighter-states.md; #99 | high |
| Shield-break → dizzy stun | ✅ | `shield.py:shield_break_stun_frames()`=`(400−p)+90` clamp [90,490]; `_start_stun()`; inputs locked (mash-out omitted, documented) | SmashWiki Stun; #12 | high |
| Shield pushback | ⬜ | absent — no pushback on block; prior PM formula was refuted in research | research (refuted); #24 | high |
| Shield poke (geometry) | 🟡 | `geometry.py` circle-overlap hit/hurt tests, but shield is a **flag** (`shield_attempting`), not a shrinking bubble — no true poke-through-exposed-hurtbox | brawl-projectm-fighter-states.md; #12 | med |
| Clank / trade / priority | 🟡 | `combat.py:_resolve_clanks` — ground-only 9% `CLANK_PRIORITY_RANGE`, pure negation; **no rebound state / bounce / rebound freeze-frames** | pm-reference/combat-hitboxes-priority.md; #38/#133 | high |
| DI | ⬜ | absent — spec only ("Phase 3") | combat-knockback-hitstun.md | high |
| SDI | ⬜ | absent — hitlag early-return reads no input (natural future seam) | combat-knockback-hitstun.md | high |
| ASDI | ⬜ | absent | combat-knockback-hitstun.md | high |
| Teching | ⬜ | absent — `force_prone()` exists but no tech window / tech-roll / missed-tech | fighter-states.md; #13/#145 | high |
| Crouch-cancel | 🟡 | `fighter.py:receive_hit` `kb*=CROUCH_CANCEL_FACTOR` (0.67) when `state=="crouch"` — **knockback only**, hitlag "c" deferred; 0.67 ⚠ tuning | Melee/PM; #135 | high |

**Notes:** the **defense cluster (DI/SDI/ASDI/tech)** is a coherent unbuilt "Phase 3"
— present in `docs/pm-reference/` specs, zero implementation; hitlag's frozen
early-return is the seam SDI/ASDI will hook. Shield is HP-and-flag, not geometric, so
shield-poke and shield-priority-by-geometry are simplified. Shield drain/regen
(0.2/0.2) and absent shield-pushback are **ratified divergences** (#99/#24), not bugs.

## 2. Moveset & hitbox system

| Mechanic | Status | Evidence | PM source / issue# | Conf |
|---|---|---|---|---|
| Per-move frame data (startup/active/recovery) | ✅ | `combat/data.py:MoveData`; `move_clock.py:MoveClock.tick` opens active `startup<f≤startup+active`, ends `+recovery` | analysis §2.1; #70/#71 | high |
| Ground vs air variant split | ✅ | `MoveData.in_air`; `move_select.select_move_key` branches `_GROUND_A`/`_AIR_A` on `on_ground` | #143/#133 | high |
| Move-selection seam (dir × ground/air × A/B) | ✅ | `combat/move_select.py:select_move_key`/`resolve_move_key`; `fighter_input._move_direction`; `test_move_select.py` | #143 | high |
| Multiple hitboxes per move | ✅ | `MoveData.hitboxes: tuple`; `move_clock.tick` spawns all; `combat.process_hits` walks boxes; `test_multi_hitbox.py` | #130 | high |
| Per-hitbox damage/angle/BKB/KBG | ✅ | `data.py:Hitbox` fields; `combat.process_hits` applies connecting box | #130/#117 | high |
| Jab | 🟡 | Nalio only (`nalio_cat.py:_JAB`, PM Attack11, 3 boxes); default cat has only generic `"attack"` | spec-119; #154 | high |
| D-tilt | 🟡 | Nalio `_DOWN_TILT` (3 boxes) sits in the generic `"attack"` alias slot, not its canonical `"dtilt"` key (deliberate bootstrap, `nalio_cat.py:41-43`). down+A *does* play it via the `"attack"` fallback (`move_select.py:58`) — but so do up/forward+A, since none of ftilt/utilt/dtilt are defined. Re-key under #142 when ground normals land | spec-119; #132/#142 | high |
| Aerials (n/f/b/u/d-air) | 🟡 | only `nair` (Nalio); `move_select._AIR_A` maps all five but fair/bair/uair/dair undefined | spec-119; #136 | high |
| F-tilt / U-tilt | ⬜ | keys reserved in `move_select.py`, no MoveData | analysis §2.1; #142 | high |
| Smashes (chargeable) | ⬜ | no charge state, no smash keys, no charge field | analysis §8; #142 | high |
| Dash attack | ⬜ | absent (needs a dash state) | analysis §2.1; #142 | high |
| Specials (neutral/side/up/down-B) | ⬜ | `move_select._SPECIAL` maps 4 keys; `resolve_move_key` no-ops (no character defines any) | #67/#142 | high |
| Sequential multi-hit (jab1-2-3) | 🟡 | engine supports it: per-hitbox temporal windows (`Hitbox.active_start/end`, `MoveClock` fires each window on its start frame) land in #204; no real move authored with them yet (n-air late hit etc. is Phase D) | #204; analysis §2.2; #142 | high |
| Sakurai angle (361) handling | ✅ | `fighter.receive_hit` resolves 361 via `knockback.sakurai_angle` (airborne-fixed, grounded scales flat→max with KB); thresholds are ⚠ playtest starting points | #203 | high |
| Stale-move negation | ⬜ | no staleness queue/table; `knockback()` takes no stale multiplier | analysis §8; #142 | high |

**Notes:** the moveset **engine is real**; the **content is one cat, ~3 moves**
(jab, d-tilt mis-keyed to `"attack"`, n-air), default cat has a single generic
attack. Two engine gaps block faithful authoring even where data exists: a **single
active window** per move (no sequential multi-hit) and **no Sakurai-angle resolution**.
Clank exists but is move-vs-move negation, *not* stale-move negation.

## 3. Movement & fighter states

| Mechanic | Status | Evidence | PM source / issue# | Conf |
|---|---|---|---|---|
| Double jump / multi-jump | ✅ | `fighter_input.handle_actions` jump branch gated by `jumps_remaining`; `FighterData.max_jumps`; reset on land | analysis §Jumps | high |
| Spot dodge | ✅ | `_start_dodge` (`dir_x==0 & on_ground` → `vel=0`); `dodge` leaf; intangible | #6; SmashWiki | high |
| Roll (directional ground dodge) | ✅ | `_start_dodge` grounded branch (`DODGE_SPEED`, faces opposite travel per #2); edge-aware clamp | #2; SmashWiki Roll | high |
| Crouch | ✅ | `fighter_chart.py` `crouch` leaf; body/hurtbox resize from `FighterData.crouch_*`; movement locked | #124; test_crouch.py | high |
| Platform drop-through | ✅ | `core.physics.solve_vertical` (thin + down → drop); spot-dodge/shield+down guard | #5 family | high |
| Air dodge (neutral) | 🟡 *(diverged)* | Brawl-style: `_start_dodge` doesn't touch `vel.y`, gravity continues; PM should halt momentum + go helpless | #23/#184; air-dodge-vertical-momentum-findings.md | high |
| Air dodge (directional) | 🟡 *(diverged)* | additive nudge `vel.x += dir_x·DODGE_SPEED` (PM *sets* a fixed burst); no helpless after | #184 | high |
| Prone/knockdown + getup | 🟡 | `prone` leaf + `Player.force_prone()` (force-entry only); getup = timer→idle. No auto landing trigger (#145), no getup-roll/attack (#146) | #13/#145/#146; test_prone.py | high |
| Helpless / special-fall | ⬜ | no `helpless`/`freefall` leaf; dodge → `fall` directly | #184; findings §3 | high |
| Short hop vs full hop | ⬜ | jump always `vel.y=jump_vel` (fixed); no tap-vs-hold | analysis §6 | high |
| Fast-fall | ⬜ | `apply_gravity` clamps to `max_fall_speed`, no down-held boost (TODO only) | analysis §6 | high |
| Double-jump-cancel | ⬜ | absent | analysis §6 | high |
| Tech | ⬜ | no tech window / tech-roll / tech-in-place | #13/#146 | high |
| Dash vs run | ⬜ | single `run` leaf, one `move_speed`, no initial-dash burst | analysis §6 | high |
| Dash-dance | ⬜ | absent (no dash state) | analysis §6 | high |
| Pivot | ⬜ | facing flips instantly; no turnaround state | analysis §6 | high |
| Ledge grab / hang / getup / roll / jump / drop / intangibility | ⬜ | no ledge detection or state anywhere (TODO + unused comments only) | #14 | high |
| Wavedash | ⬜ | needs PM air-dodge physics + traction model | #184; analysis §6 | high |
| L-cancel | ⬜ | no landing-lag system at all (Nalio docstring confirms deferral) | analysis §6 | high |

**Notes:** the reachable, tested states (jumps, dodges, crouch, drop-through) are
solid. **Air dodge is the headline divergence** — a non-canonical Brawl/Melee hybrid
(momentum preserved, additive nudge, no helpless), which is *why* wavedash and
L-cancel are ⬜ (gated on fixing it, #184). Prone exists structurally but **nothing in
normal play enters it** (force-entry only; #145 auto-trigger deferred). Essentially
all **PM movement tech** is unbuilt.

## 4. Fighters & archetypes

| Item | Status | Evidence | PM source / issue# | Conf |
|---|---|---|---|---|
| Per-character `weight` | ✅ | `data.py:FighterData.weight`; threaded to `fighter.py` | #117/#123 | high |
| Per-character movement (run/air speed, gravity, fall speed, jump vel, jump count) | ✅ | `FighterData.move_speed/gravity/max_fall_speed/jump_vel/max_jumps`; read by `movement`/`physics`; able-to-fail tests | #126 | high |
| Per-character crouch geometry | ✅ | `crouch_size`/`crouch_hurtbox`; Nalio 40×40 + lowered hurtbox; default too | #124 | high |
| Constants actually read per-fighter (not just stored) | ✅ | physics/movement take params; `test_per_character_movement.py` revert-able | #126 | high |
| `load_fighter_data()` per-archetype seam | 🟡 | only `"nalio"` branches; everything else (incl. live `"P1"/"P2"`) → default | #117 | high |
| # of mechanically-distinct fighters | 🟡 | **2**: `DEFAULT_FIGHTER_DATA` + `NALIO_FIGHTER_DATA` (of 5 planned) | #117 | high |
| Nalio = Mario archetype | 🟡 | weight + hurtbox + 3 moves + crouch; specials/smashes/full kit absent; movement = baseline by design (PM Mario) | #119; research-spec-119 | high |
| Per-character hurtbox geometry | 🟡 | `FighterData.hurtbox` is per-fighter; Nalio reuses default 2-circle stack (stated approximation) | #119 §3 | high |
| Multi-jump used (Kirby 5–6) | 🟡 | engine supports `max_jumps>2` (tested) but **no fighter sets it**; default 2 | #117/#126 | high |
| Narz/Marth · Gnok/DK · Birky/Kirby · Xoff/Fox | ⬜ | names in `og_skins.py` comments only — no files/data | #117 | high |
| Disjoint hitboxes (Marth tipper) | ⬜ | `Hitbox` has no disjoint/sweetspot | #117 | high |
| Projectile / special (Fox blaster) | ⬜ | no projectile system | #117 | high |
| Fast-fall speed field | ⬜ | no fast-fall field/constant | #126/#120 | high |
| Archetypes selectable in live game | ⬜ | `char_select` lists `CAT_CHARACTERS` = 6 recolor skins; `game.py` hardwires `char_name="P1"/"P2"` → default cat; **Nalio is unreachable in-game** | #117 | high |

**Notes:** the per-character **infrastructure is real and proven** (weight + 5
movement constants + crouch geometry flow `FighterData → Fighter → physics`). What's
missing is **content** (4 archetypes are names only) and **distinguishing mechanics**
(disjoint hitboxes, used multi-jump, projectiles, fast-fall). The 6 selectable "cats"
are **pure recolor skins** (`og_skins.py`: `{name,color,stripe,eye}`), and even the
one real archetype (Nalio) is reachable only via the loader seam + tests, never in the
live game.

## 5. AI / CPU controllers & determinism

| Item | Status | Evidence | PM source / issue# | Conf |
|---|---|---|---|---|
| Seeded-RNG seam | ✅ | `controllers.py:BaseController` `self.rng=random.Random(DEFAULT_CONTROLLER_SEED=0)`; edge-only; `watch.py` injects `--seed`/clocktime; `test_controller_rng.py` | #166 | high |
| Sim determinism (golden oracle) | ✅ *(intentional divergence)* | `run_battle` + `test_golden.py` (4 byte-identical goldens); **no PRNG in core sim** (only the #166 controller edge) — stricter route to PM's seeded determinism | #144; #176 | high |
| Omits random tripping | ✅ *(intentional, aligned)* | absent — PM itself removed Brawl tripping | #144 §G | high |
| Omits move-intrinsic RNG (Judge/turnips/misfire) | ✅ *(intentional)* | none authored; #144 prescribes a single seeded stream if ever added | #144 §B | high |
| Omits items / hazards | ✅ *(intentional)* | single neutral stage, no items (PM competitive config) | #144 §C/D | high |
| Archetype controllers (attacker/follower/idler) | 🟡 | real tested demo policies (`controllers.py`, `test_archetypes.py`, goldens) — but RNG-free, not difficulty-graded, **not in-game** | #48 | high |
| `watch.py` flags (`--seed`/`--vs`/`--match`) | 🟡 | archetype-select for *demos*; no `--cpu-level N` | #61; #148 step 5 | high |
| In-game (player-facing) CPU opponent | ⬜ | `game.py` feeds one keyboard frame to all players; no controller wired into the live loop; menus expose no CPU/difficulty | #148; #48 | high |
| Difficulty levels 1–9 ladder | ⬜ | **research-only** — the `level→knob` table + 5-step DEV decomposition live in `docs/research/2026-06-29-pm-cpu-difficulty-levels-1-9.md`; no code | #148 (proposal) | high |

**Notes:** **no player-facing CPU exists** — every "controller" is a scripted,
headless demo/benchmark/golden-generation policy invoked only from `watch.py`/
`sim.runner`. The archetypes are real *as policies* but ⬜ *as opponent AI*. The 1–9
ladder is fully researched (#148) but unbuilt. Determinism is an **intentional
divergence** (a strength, not a gap): pycats core has *no* PRNG, with #166's edge seam
reserved for future golden-safe stochastic difficulty.

## 6. Screens / match flow / menus

| Item | Status | Evidence | PM source / issue# | Conf |
|---|---|---|---|---|
| Pause | ✅ | `pause_menu.py:PauseMenuManager` (Resume/End Match/Return); P-key guard; frozen-bg overlay | project-m-menu-architecture.md §6 | high |
| Win / results screen | ✅ | `win_screen.py:WinScreenManager.render` + `_render_stats_table` (winner, stocks, per-player stats) | PM results | high |
| Main menu | 🟡 | `main_menu.py` — Play/Options/Quit only (no Solo/Group/Vault tree) | menu-architecture §1 | high |
| Character select (roster + flow) | 🟡 | `char_select.py` — 6 cats, 3×2 grid, 2 players, confirm/cancel + both-confirm START; no port colours/tags/CSS-settings | menu-architecture §3 | high |
| Rematch / play-again | 🟡 *(intentional)* | `win_screen.py` **both players confirm** + 30f delay → char_select; diverges from PM single-press | #10/#11 | high |
| Stock match setting | 🟡 | `INITIAL_LIVES=3` hardcoded, applied in `reset_game`; no in-menu selector | PM Rules | high |
| Options / settings menu | 🟡 *(intentional)* | `options_menu.py` (status bars/scale/fullscreen/hold-ESC); consolidated+persisted vs PM distributed/ephemeral | #116/#121/#122 | high |
| Statechart screen engine wiring (#100/#181) | 🟡 | `StatechartScreenEngine`/`make_screen_engine` (slice 1, #181) IS wired into the live game — `screen_manager.py:97-101` builds the engine with `backend=os.environ.get("PYCATS_SCREEN_BACKEND","legacy")` (used by `game.py:439,530`), so `PYCATS_SCREEN_BACKEND=statechart` runs the whole live flow on it. **Legacy is just the default**; flipping it = #100 slice 4 (after parity proven) | #100/#181 | high |
| Match/battle as a real game-state | ⬜ | `game.py` `if current_state=="playing":` inline ladder; battle state module-global; FSM `playing` empty | screen-flow-statecharts-port-findings.md; #100 | high |
| Screen flow on statecharts vs hand-rolled | ⬜ | live flow on hand-rolled `systems/fsm.py` (6-state guard table); statecharts only in fighter + match_engine | #100 | high |
| Stage select | ⬜ | single hardcoded stage; `game.py` TODO "NOT YET" | menu-architecture §4 | high |
| Time match / items / teams / Rules menu | ⬜ | absent | menu-architecture §5 | high |
| Changelog screen | ⬜ | absent | #134 | high |

**Notes:** pycats is intentionally a **minimal 1v1 trainer**, so most absent menu
features (stage select, large roster, time mode, items/teams) are scope decisions, not
regressions. Two divergences are **ratified** (#99): both-confirm rematch (#10/#11) and
the consolidated/persisted options menu (#116/#121/#122). The **statecharts screen-flow
port (#100) is the largest real screens gap** — the `StatechartScreenEngine` seam +
parity guard exist (#181) but the live flow and battle-as-a-state refactor are not done.

---

## What's closest to "done" vs the biggest gaps

**Closest to full parity (build on these):**
- Combat math: knockback formula, hitstun, hitlag, shieldstun, shield-break stun.
- Move *engine*: frame data, multi-hitbox, per-hitbox data, ground/air move-selection.
- Per-character data spine: weight + movement constants + crouch geometry (proven able-to-fail).
- Determinism + the seeded-RNG seam (#166).

**Biggest gaps (ranked by structural weight):**
1. **PM movement tech** — ledge (#14), wavedash + L-cancel (gated on PM air dodge #184), dash/dash-dance/pivot, fast-fall/short-hop. Mostly ⬜.
2. **Moveset content** — tilts/smashes/dash/aerials/specials beyond Nalio's ~3 moves; plus the two engine gates (sequential multi-hit, Sakurai-angle) — #142 Phase 2.
3. **Battle-as-a-state / statecharts screen-flow port** — #100 (engine wired behind the `PYCATS_SCREEN_BACKEND` toggle #181; battle-as-a-state + flipping the default to statechart remain — slices 2 & 4).
4. **Defense cluster** — DI/SDI/ASDI/tech (Phase 3); shield geometry/poke + shield pushback.
5. **Roster content** — 4 of 5 archetypes absent; the one real archetype isn't live-selectable (#117).
6. **Player-facing CPU** — no in-game opponent or difficulty ladder (research-ready, #148).

## Intentional divergences (see #99 for rationale)

Not gaps — deliberate design choices, recorded here so they aren't re-investigated as
bugs: **deterministic sim / no core PRNG** (#144); **both-players-confirm rematch**
(#10/#11); **consolidated + persisted Options menu** (#116/#121/#122); **simplified
shield drain/regen 0.2/0.2** and **deferred shield pushback** (#99/#24); **status-timer
bars** (a PM-absent UI aid, #111). The #99 doc is the canonical rationale list; this
report only links it.

## Caveats & how to refresh

- **Freshness / sha drift:** combed at `b9a71ad`; the main branch advanced *during*
  the audit (sibling merges), so a few line numbers may have shifted. The mechanic
  inventory holds, but re-comb before trusting specifics. This report is a snapshot,
  not a maintained ledger — **re-run the six-auditor pass** rather than hand-patching.
- **Denominator is judgmental:** the ~25/28/42 tally depends on how mechanics are
  split; treat the per-row tables as authoritative, the headline as directional.
- **PM target is secondary-tier:** the oracle is SmashWiki + community docs +
  `docs/pm-reference/*` + the repo's research docs, not PM decompilation — provenance
  caveats from umbrella #24 apply.
- **Follow-ups:** several ⬜/🟡 rows already have tracking issues (linked inline).
  Two near-misses flagged during this audit were verified to be **already tracked**,
  not new bugs: the Nalio d-tilt alias re-key (annotated on #142) and flipping the
  screen-engine default to statechart (annotated on #100, slice 4). Genuinely
  untracked rows are candidates to file one at a time, on go-ahead.

## Sources (PM oracle)

`docs/research/`: pm-mechanics-implementation-analysis.md (roadmap), knockback-launch-physics-findings.md,
brawl-projectm-fighter-states.md, air-dodge-vertical-momentum-findings.md,
2026-06-29-pm-cpu-difficulty-levels-1-9.md, 2026-06-25-npc-behaviors-and-dual-controller.md,
research-findings-144-pm-randomness-survey, research-spec-119-mario-cat-pm.md,
screen-flow-statecharts-port-findings.md, project-m-menu-architecture.md ·
`docs/pm-reference/`: combat-hitboxes-priority.md, combat-knockback-hitstun.md, defense-shield-dodge.md ·
`docs/project-m-parity.md` (#99, intentional divergences) · the pycats source at `b9a71ad`.
