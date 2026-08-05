# Magic-number audit — codebase inventory (#1002)

**Role:** RESEARCH · audit-only (no code change) · **as-of 2026-08-02** (branch `br-grape/pycats-1002`)

## What this is

An inventory of unnamed / under-sourced numeric literals across `pycats/` (tests excluded, 116
files scanned), classifying each by **where**, **named?**, **sourced?**, and **bucket**. It reports
current state only — no renaming, no new provenance verdicts. Follow-up extraction is a separate DEV
ticket downstream of this doc.

Priority per #1002: **combat + config tuning values first** (the provenance registry,
`pycats/combat/provenance.py` / ADR-0003, is the existing model and partially covers them).
Per the taking-instruction, this pass **also flags shared consts/globals that look like they should
be per-character values** (`⚠ CHAR-VALUE`) — a fighter silently inheriting a generic default it
should individualise.

## Headline findings

1. **The combat path is the best-covered part of the codebase, with two notable exceptions.**
   `hit_resolution.py` / `movement.py` / `knockback.py` route almost everything through named,
   provenance-registered constants — **except** the `knockback()` formula coefficients (bare inline
   literals in the game's single most-reached equation) and the `GETUP_ATTACK` move (a whole shared
   move of unsourced literals). These two are the top combat-tuning extraction targets.
2. **Three registry-orphans** — live gameplay tuning values that are named but have **no
   `provenance.py` row**, so the drift-guard (`test_tuning_provenance.py`) never sees them:
   `DOUBLE_TAP_WINDOW` (8), `LEDGE_REGRAB_INTANGIBLE_CUTOFF` (5, its basis is already a primary quote
   in-comment), and `VEL_DEADZONE` (0.05, lives in `core/` so the config-scoped guard misses it).
3. **Character-value drift is real and shipping.** Several cats **silently inherit** movement scalars
   they should override: Gnok's `run_speed` inherits the config default (8) so its sustained run is
   *slower than its own dash*; Birky overrides `move_speed` but inherits `dash_speed`/`run_speed`;
   and the global `MAX_FALL_SPEED` (a registered DIVERGENCE — no base/fast-fall split) is one number
   for every fighter. This is the #557 pattern, now visible roster-wide.
4. **Render/UI/menus are mostly named** (the #410 epic + #415/#420/#433/#444/#446 passes did their
   job); the residue is a long tail of layout literals that escaped those passes (chiefly
   `options_menu.py` scaled spacing, `win_screen.py` stats-table/crown geometry, and a repeated
   HUD-hint font size `24`).
5. **Two incidental observations worth a follow-up ticket** (not magic numbers): two likely
   copy-paste `_WAIT` comment labels in the character oracles (Narz cites "Kirby", Birky cites
   "Marth"), and the standing stale-JSON footgun (the `*_cat.py` numbers are drift-guard oracles;
   runtime reads `characters/data/<cat>.json`).

## Classification key

- **Named?** — bare literal vs. a named constant (config module / provenance registry / module const).
- **Sourced?** — carries an accurate basis: a primary citation, a `TUNED`+issue record, or an
  explicit `GUESS`/`⚠` tag. A bare literal with no basis is *unsourced*. (For render/UI, "sourced"
  degrades to "named + documented layout constant" — there is no game-canon to cite.)
- **Bucket** — combat-tuning · physics · timing-frames · render-geometry · ui-layout · ai-threshold ·
  color · incidental (loop bounds / indices / 0-1 identities / epsilons — out of scope).

## Prior art (already-swept modules — #410 epic)

The closed #410 epic + children named constants across render, screens, entities, sim, config,
physics: #415 (render_battle layout), #420 (char_select), #425 (entities consts), #433 (menus),
#444 (controllers AI + presenter fonts), #446 (win_screen cooldowns + physics thresholds), #450
(cross-module dedup). This audit reports what those passes named, what slipped through, and what has
been added since. Several "slipped through" items below are that residue.

---

## Master file checklist (all scanned)

Priority groups (combat, config/core) first.

### combat/ — PRIORITY
- [x] charge.py · collapse.py · data.py · errors.py · geometry.py · knockback.py · move_clock.py · move_select.py · provenance.py · shield.py · tangibility.py · units.py

### config/ + core/ — PRIORITY
- [x] config/{__init__,menu,physics,render,screen,stage}.py · core/{geometry,physics}.py

### characters/ — char-value focus
- [x] birky_cat.py · body_zones.py · default_cat.py · gnok_cat.py · __init__.py · nalio_cat.py · narz_cat.py · og_skins.py · palettes.py · roster.py

### entities/
- [x] attack.py · fighter_input.py · fighter_physics.py · fighter.py · __init__.py · ledge.py · platform.py · player.py · stages.py · tail.py

### render/
- [x] render/battle.py · render_battle.py · render/{body,debug,hud,__init__,status,tint}.py

### screens/ + ui/
- [x] screens/{battle_screen,char_select,__init__,keybind_menu,keybind_sets_menu,main_menu,options_menu,pause_menu,win_screen}.py · ui/{cat_faces,__init__,menu_controller,menu_layout,menu_widgets,stats_print,text_entry,text_utils}.py

### sim/ + systems/
- [x] sim/{battle_log,captions,controllers,demo,__init__,input_script,presenters,runner,showcase}.py · systems/{hit_resolution,__init__,match_engine,movement,screen_engine,state_engine,state_engine_sc,status_model,win_condition}.py

### shell/ + storage/ + loadout/ + charts/ + core-input + game
- [x] shell/{app,display_manager,display,esc_hold,__init__,input_history,input_poll,screen_manager,screen_render}.py · storage/{dev_log,__init__,keybind_store,profile_store,runtime_settings,settings}.py · loadout/{build_fighter,character,__init__,placeholder,player_identity,registry,resolvers,selection,skin_assignment,skin}.py · charts/{fighter_chart,__init__}.py · core/{input,keymap,__init__}.py · game.py · __init__.py

---

# Inventory

## combat/ — PRIORITY

**`provenance.py`** — the value registry (ADR-0003) itself; every number is a sourced `Provenance`
mirror of a config constant. Not magic numbers. Structural note: the registry's docstring scopes it
to *config.py scalars* and explicitly excludes per-character/move data in `characters/*.py` — which is
*why* the per-move literals in `data.py` and the KB coefficients in `knockback.py` are unregistered
(out of scope by construction, hence uncovered by the drift-guard).

**`knockback.py`** — the largest cluster of unregistered combat-tuning literals in the priority set:
- `knockback()` formula coefficients `1.4`, `18.0`, `200.0`, `100`, `10.0`, `20.0` — **bare inline
  literals in the KB equation.** Sourced *by module docstring only* (cites SmashWiki:Knockback, spec
  #39 §2; transcribed verbatim) but unnamed and unregistered. **combat-tuning.** Every hit routes here.
- `set_knockback()` `10.0` — bare; docstring-sourced (WDSK convention p=10). **combat-tuning.**
- `sakurai_angle()`, `hitstun_frames()`, `hitlag_frames()` — all coefficients from registered config
  (`SAKURAI_*`, `HITSTUN_*`, `HITLAG_*`). Clean.

**`data.py`**:
- `GETUP_ATTACK` (module-level `MoveData`) — `startup=4`, `active=3`, `recovery=14`, `damage=8.0`,
  `angle=70`, `base_knockback=40.0`, `knockback_growth=70.0`, circle `dx=28, dy=42, r=24` — **all bare,
  all unsourced** (a prose "⚠ playtest starting points" comment, but no issue-pinned record, no
  registry row). A whole shared wake-up move with no drift-guard coverage. **combat-tuning.**
- `FighterData.weight` default `100` — the Smash "Mario = 100" convention, documented in the field
  docstring; correctly a per-fighter field (not a mis-scoped global). Movement defaults
  (`gravity`/`max_fall_speed`/…) default to registered config globals — see ⚠ CHAR-VALUE.
- `SCHEMA_VERSION=1`, `chr(ord("A")+i)` 26-letter assumption, field defaults — incidental.

**`units.py`** — `vel()`'s `round(..., 2)` precision arg is a bare-but-documented formatting choice
(incidental). The real factor `PX_PER_UNIT ≈ 5.4` is imported + registered (FOUND, #195); this module
is the named seam. Clean by design.

**`charge.py`, `collapse.py`, `errors.py`, `geometry.py`, `move_clock.py`, `move_select.py`,
`shield.py`, `tangibility.py`** — clean. All tuning values (`SMASH_CHARGE_SCALE`, `SHIELD_*`,
`SHIELDSTUN_FACTOR`, …) come from registered config; the `400`/`90`/`0.345`/`361` numbers appear only
in explanatory docstrings, not in code.

## config/ + core/ — PRIORITY

**`config/physics.py`** — the combat/physics home; a header invariant requires every tuning scalar to
have a `provenance.py` row or the drift-guard reds. Most literals here ARE named + sourced (FOUND /
TUNED / GUESS / DIVERGENCE rows: `GRAVITY 0.5`, `MOVE_SPEED 6`, `JUMP_VEL -13`, `HITLAG_* `,
`SHIELDSTUN_FACTOR 0.345`, `SMASH_CHARGE_SCALE 1.3671`, `KNOCKBACK_LAUNCH_FACTOR/DECAY`,
`SAKURAI_* `, `CROUCH_CANCEL_FACTOR 0.67`, `CLANK_PRIORITY_RANGE 9`, `PX_PER_UNIT 5.4`, ledge frames,
etc.). **Registry-orphans (named but NO provenance row → drift-guard-invisible):**
- `DOUBLE_TAP_WINDOW = 8` — live input-timing value, ⚠-flagged as a guess in-comment but absent from
  `TUNING_PROVENANCE`/`TUNING_CONSTANT_NAMES`. **timing-frames. Top registration candidate.**
- `LEDGE_REGRAB_INTANGIBLE_CUTOFF = 5` — comment carries a PMDT 3.5 **primary quote**, yet no registry
  row. **timing-frames.** Basis exists; just not in the machine-checked store (would register FOUND).
- `MAX_SHIELD_RADIUS = 40` / `MIN_SHIELD_RADIUS = 10` — shield-bubble radii; player-visible shield
  feedback, no basis, no row. **render-geometry / combat-tuning.** Confirm render-scope exclusion or
  register.
- Documented gaps (NOT defects, listed so they aren't re-flagged): `LEDGE_POST_CUTOFF_RESIDUAL_FRAMES`
  (`PLACEHOLDER_VALUE_PLS_RESEARCH_ACTUAL`, #656), `ATTACK_SIZE (30,18)` (render, but width doubles as
  a projectile despawn bound — gameplay coupling noted, #584/#598).

**`core/physics.py`** — registry-invisible because it lives in `core/`, not `config/`:
- `VEL_DEADZONE = 0.05` — live friction snap threshold (named #446, unsourced, no row). **physics.**
  Register, or ratify a "core-local, not tracked" carve-out.
- `would_dodge_off_platform()` local `min_overlap = 25` — a **gameplay tuning value hiding as a
  function local** (dodge-off-platform guard). **physics.** Promote to a named/sourced constant.
- `find_current_platform()` local `bottom_tolerance = 2` — platform-standing snap tolerance; local,
  unsourced. **physics.** Minor.
- `JOSTLE_TRIGGER_PX`/`JOSTLE_PUSH_PX` derive via the `u()` units seam from registry-FOUND units —
  correct pattern.

**`config/stage.py`**:
- `BLAST_PADDING_X = 100` — deliberately unregistered "temporary game-feel experiment" (#733), but a
  **live KO boundary with no ratified basis.** **combat-tuning.** Resolve (ratify or source).
- Platform geometry (`THICK/THIN_PLAT_*`, `GLOBAL_Y_OFF`, …) — named, unsourced pycats stage design
  (no canon). `FD_EDGE_GROUND_UNITS 85.5656967163` (Melee FD edge, libmelee, #659) and
  `STARTING_POINT_WIDTH 924` (derived) are sourced. `INITIAL_LIVES 3`, `BLAST_PADDING 50/150`,
  `RESPAWN_DELAY_FRAMES = int(2*FPS)` are TUNED rows. **stage/combat-tuning.**

**`config/screen.py`** — `SCREEN_WIDTH/HEIGHT 960×540` and `FPS 60`: named, effectively the design
baseline; `FPS 60` matches Smash's canonical 60fps but carries no explicit citation (low-risk).

**`config/menu.py`, `config/render.py`** — declared out of registry scope (UI/render). All named;
mostly unsourced-by-design chrome (fonts, paddings, colors, cat-feature geometry, `TAIL_*` feel
knobs). Exceptions that *are* sourced/coupled: `PLAYER_SIZE (40,60)` (registered TUNED #584 — it is
the collision box, not just render); `FIGHTER_OUTLINE_COLOR/WIDTH` (accessibility rationale, #346);
`WIN_SCREEN_STATS_SIZE 26` and `CHAR_SELECT_GRID_COLS 5` (in-line fit rationale).

**`config/__init__.py`, `core/geometry.py`** — clean (re-export shim; structural rect arithmetic).

## characters/ — char-value focus

> **Runtime source is the sibling `characters/data/<cat>.json`** (hydrated by `_fighter_from_json`);
> the `*_cat.py` files are drift-guard oracles kept in sync by hand (R8). Any literal here must match
> its JSON twin — the standing stale-JSON footgun. Combat scalars are largely datamined + per-move
> cited; **positions (dx/dy) are the documented `⚠` "bone-not-modelled" approximation** across all cats.

- **`nalio_cat.py`** (PM3.6 Mario baseline) — best-sourced kit: every move's damage/angle/BKB/KBG/
  radii/frames carries a rukaidata PM3.6 citation; `_WAIT recovery=51` FOUND (brawllib, #753). Binds
  `gravity`/`max_fall_speed` to named globals explicitly "rather than silently inheriting". Gaps:
  `_FIREBALL projectile_speed=10` (⚠🔬 GUESS), `recovery_vx=2.0` (⚠ eyeball), `rehit_rate=4` (⚠
  playtest), `_bair/_uair` flattened averages (`human-designer-temporary-...-v1-only`, #893), and
  bare integer radii in early moves (`round(size×PX_PER_UNIT)` pre-computed, unit only in a comment)
  vs. the `u()` seam in later moves — inconsistent unit provenance.
- **`gnok_cat.py`** (super-heavyweight; the exemplar `vel()`/raw-unit pattern) — geometry MEASURED
  from PM3.6 DK hurtbox extents; moves datamined from brawllib_rs DK dump (#614) + rukaidata FAF
  cross-check; movement scalars via `vel()` with sourced unit rates; `weight=114` sourced;
  `_WAIT 141` FOUND. Best-sourced physics of the group. Positions `⚠🔬 playtest`.
- **`birky_cat.py`** (featherweight; only cat using `zone_dy` body-relative dy + own `stand_size`) —
  stats `weight=70 / gravity=0.42 / max_fall_speed=12 / move_speed=5 / max_jumps=6 / jump_vel=-11`
  from #229 spike (PM Kirby proportional), all `⚠ pin/playtest later`; moves rukaidata-Kirby-cited
  radii, `⚠ playtest` positions; Final Cutter phase-2/3 spike+shockwave `⚠ playtest` (#973/#974/#1110);
  flattened aerials designer-temp (#893/#911). `_CROUCH_SIZE (40,24)` owner-ratified (#589/#565).
- **`narz_cat.py`** (Marth) — **the biggest sourcing gap in the group:** the *entire* moveset
  (damage/angle/BKB/KBG/radii/positions/frames) is bare literals tagged `⚠🔬 playtest /
  rukaidata-confirm LATER` — designer estimates *shaped* like PM Marth but pinned to no primary. Stats
  `weight=87 / gravity=0.45 / jump_vel=-12` from #290 spec, `⚠ playtest`.
- **`default_cat.py`** (P1/P2/testcat seats) — `_ATTACK_HITBOX base_knockback=30.0` (⚠ initial tuning)
  and `knockback_growth=100.0` (**bare, unsourced**); frames/damage sourced to retired config for
  continuity (#70); crouch/prone geometry hand-authored, unsourced ("golden-safe: replay never
  crouches").
- **`body_zones.py`** — `BODY_ZONES {head:0.15, center:0.50, feet:0.85, below_feet:1.10}`: named seam,
  fractions are `⚠ playtest starting points` (faithful-derived deferred to #310). Applied
  inconsistently — only Birky calls `zone_dy`; other cats author raw absolute `dy`.
- **`palettes.py`, `roster.py`, `og_skins.py`, `__init__.py`** — cosmetic RGB (JSON-mirror,
  `_TESTCAT` #672-ratified; `_NEUTRAL` unsourced fallback) + package plumbing. Out of tuning scope.

**Two likely copy-paste `_WAIT` comment-label errors** (audit observation, not a literal defect):
Narz (Marth) comment cites "PM **Kirby** `Wait1`"; Birky (Kirby) comment cites "PM **Marth**
`Wait1`". The `recovery` values (111, 71) may be mislabeled/swapped — worth verifying against the
datamine.

## entities/

- **`fighter_input.py`** — `0.1` horizontal-velocity dead-zone repeated 3× (`can_modify_air_dodge` +
  Priority-2 momentum-dodge), bare, unsourced; decides neutral-vs-momentum air dodge. **physics.**
- **`player.py`** — `vel.y = 1` airborne nudge duplicated in `_evict_from_ledge` and
  `_drive_ledge_hang`, bare, unsourced. **physics.** (`LEDGE_GETUP_FRAMES // 2` halving is documented.)
- **`tail.py`** — `_BASE_TURN_STEP = 0.18` (swing ease) and `_PINNED = 2` (pinned root count): named
  but module-local, unsourced game-feel knobs, contradicting the module's own "feel knobs live in
  config" contract. `_CONSTRAINT_HALF_SPLIT 0.5` (Jakobsen, exact) and `1e-6` epsilon incidental.
- **`attack.py`** — `pad = 2` multi-hitbox bounds padding (bare, render-geometry). `Projectile`
  defaults are named config + ⚠ GUESS-tagged (properly labeled). 
- **`fighter.py`** — clean of bare game values (`_KO_OFFSCREEN_POS` named sentinel; `0.345`/`0.67`/
  `361`/`17.1` appear only in comments, code uses named consts/helpers). Per-fighter stats correctly
  pulled from `fighter_data`.
- **`ledge.py`** — no bare literals; `LEDGE_POST_CUTOFF_RESIDUAL_FRAMES` referenced is a self-declared
  unsourced PLACEHOLDER with no Provenance entry (flagged for sourcing).
- **`fighter_physics.py`, `platform.py`, `stages.py`, `__init__.py`** — clean (physics via named
  `core.physics` primitives; geometry from config platform dicts).

## render/

The #415/#900 passes left this layer in good shape — most literals are named module/config constants
with rationale comments. Substantive findings:
- **`body.py`** — ⚠ CHAR-VALUE: `IDLE_BREATH_BOB_PX = 3` / `IDLE_BREATH_SQUASH_PX = 1` — absolute px
  baked from **Nalio's 60px body** (#760) and applied to every archetype **unscaled**, while the
  *period* is already per-cat (`_IDLE_BREATH_PERIOD_FRAMES`). Should become a fraction-of-body-height
  or per-archetype value. Also `_BODY_PAD_X/TOP/BOT = 48/56/12` — named + role-documented, but the
  magnitudes themselves have no derivation.
- **`hud.py`** — bare `HUD_SPACING * 3` / `* 2` bottom-anchor multipliers coupling `emphasis_row_y`,
  `draw_pause_hint`, `draw_shell_chrome` by a raw literal (a pause-hint row change won't propagate to
  the emphasis baseline); plus a bare held-bar line width `2`.
- **`status.py`** — ⚠ CHAR-VALUE (minor): `STATUS_BAR_WIDTH = int(1.5 * PLAYER_SIZE[0])` keys off the
  *global* `PLAYER_SIZE`, not the fighter's real `stand_size`, so a differently-sized cat gets a
  mis-sized bar. Small in-expression bare gaps: `STATUS_BAR_STACK_STRIDE`'s `+4`, timer readout `-2`.
- **`battle.py`, `debug.py`, `tint.py`, `body`-consts, `render/__init__.py`, `render_battle.py`** —
  clean (named + sourced colors/geometry; `render_battle.py` is a re-export shim).

## screens/ + ui/

Post-#420/#433/#446, most menus are named. Residue (all ui-layout unless noted):
- **`options_menu.py`** — **highest-volume offender:** the `round(N * scale)` spacing family
  (`10`/`8`/`6`/`4`/`30`/`80`/`90`/`12`/`40`) recurs across `_layout`/`_render_keybind`/`_render_sets`
  with the same numbers meaning different things; none extracted.
- **`win_screen.py`** — stats-table `180`/`100`/`20` col widths, `0.5`/`0.75`/`0.8` line-spacing
  fractions, `_draw_crown` `8`/`22`/`0.7`/`3`, `_SEAT_CENTER_X 135` (#446 was cooldown-only, so these
  visual literals were never named; several are as-of tunables per #738/#746).
- **`char_select.py`** — residual text-offset literals (title `50`, instructions `90 + i*20`, tag
  offsets `15`/`12`, bottom strip `-40`, name gap `10`) left bare by #420's grid/tile pass.
- **`text_entry.py`** — `draw_text_entry` grid dims `cell_w=56`/`cell_h=40`/`top=160`, title `40`,
  buffer `95` (local, bare). **`cat_faces.py`** — luma threshold `110` (bare game-feel cutoff).
  **`menu_layout.py`** — `gutter=24` (named param; could align to a shared spacing const).
- Clean: `battle_screen.py`, `keybind_menu.py`, `keybind_sets_menu.py`, `main_menu.py`,
  `pause_menu.py`, `menu_controller.py`, `menu_widgets.py`, `stats_print.py`, `text_utils.py`,
  package markers.

## sim/ + systems/

**Combat-path files are clean:** `hit_resolution.py` (`CLANK_PRIORITY_RANGE`, FOUND #38) and
`movement.py` (`MOVE_SPEED`, FOUND #384, per-fighter-overridable #126) use named registry constants
only. `match_engine.py`, `screen_engine.py`, `state_engine*.py`, `win_condition.py`,
`status_model.py` (named spec-referenced bar colors), `runner.py`, `battle_log.py`, `input_script.py`,
`showcase.py`, `demo.py` — clean (choreography frame numbers are documented content, not game values).

Findings concentrate in the AI file **`controllers.py`** — most knobs are named (#444) and disclosed
as `⚠ GUESS`/`⚠ tuning`/`PLACEHOLDER`/`DIVERGENCE #970`, i.e. honestly tagged. The real gaps:
- inline `± 8` standoff deadband in `_decide_engage` (level-less path) and both `FollowerController`
  branches — bare, even though #970 already named `SPACING_STOP = 8` for the leveled path.
- `AttackerController.__init__` **untagged** default args `attack_period=12`, `standoff=30`,
  `attack_range=45`, `drop_threshold=20` — bare, no `⚠` basis (unlike their `⚠ GUESS`-tagged
  `shield_threat_*`/`fireball_range` neighbours).
- **`presenters.py`** — #444 miss: `ScreenshotPresenter._draw_overlay` still inlines `22` twice,
  duplicating the named `OVERLAY_STAT_FONT_SIZE`/`OVERLAY_STAT_LINE_SPACING`.

## shell/ + storage/ + loadout/ + charts/ + core-input + game

Mostly plumbing; the game-feel literals are in the input/present layer:
- **The 2-second / 120-frame hold threshold is declared three times** — `EscHoldTimer(hold_frames=120)`
  (esc_hold.py) + `back_hold_frames=120` + `esc_quit_hold_frames=120` (screen_manager.py). Each is
  individually sourced ("2s @ 60fps", #905/#453/#113), but there is no single SSOT. **timing-frames.**
- **HUD-hint font size `24` is a bare repeated literal** — `display_manager.present()` (toast) and
  `screen_render.render_active_screen` (×2), sitting right next to the *named* `HUD_PADDING`/
  `HUD_SPACING`. **ui-layout.**
- **`esc_hold.draw_esc_hold_arc`** — `radius=28`, `width=6`, outline `2`, and `SCREEN_HEIGHT - 155`
  are bare + unsourced (the `155` is the most opaque). The one cluster that is both bare *and*
  undocumented. **ui-layout.**
- `settings._DEFAULTS["show_hitbox_overlay"] = True` — a flagged temporary default (revert to OFF
  before release, #239→#241); tracked so it isn't shipped on.
- Clean/sourced: `display.py` (`TOAST_DURATION_FRAMES = 3*FPS`, exemplary), `input_history.py`
  (`INPUT_HISTORY_FRAMES = 16`), `app.py`/`game.py` `--speed 1.0`, all of storage/loadout/charts,
  `core/{input,keymap}.py` (input.py notes a *future* key-buffer window TODO — timing-frame tuning
  when implemented). `placeholder.py`/`roster.py` grays are #672-ratified.

---

# Priority extraction candidates (for the follow-up DEV ticket)

Combat/config-tuning subset first (the #1002 priority), then the rest. Registry-orphans rank high
because they are live values invisible to the drift-guard.

## Tier 1 — combat / physics (do first)

1. **`knockback.py` `knockback()` formula coefficients** (`1.4`, `18.0`, `200.0`, `100`, `10`, `20`) —
   bare inline literals in the game's most-reached equation; docstring-cited but unnamed + unregistered.
2. **`data.py` `GETUP_ATTACK` move literals** (`4/3/14`, `damage 8.0`, `angle 70`, `bkb 40`, `kbg 70`,
   circle `28/42/24`) — an entire shared move self-labeled "playtest" with no issue-pinned record / row.
3. **`DOUBLE_TAP_WINDOW = 8`** (config/physics.py) — registry-orphan input-timing value; register GUESS.
4. **`LEDGE_REGRAB_INTANGIBLE_CUTOFF = 5`** (config/physics.py) — registry-orphan whose basis is
   already a primary quote in-comment; register FOUND.
5. **`VEL_DEADZONE = 0.05`** (core/physics.py) — live friction snap threshold, registry-invisible
   (in `core/`); register or ratify a carve-out.
6. **`would_dodge_off_platform()` `min_overlap = 25`** (core/physics.py) — gameplay tuning value hiding
   as a function local; promote to a named constant.
7. **`default_cat.py` `knockback_growth = 100.0` / `base_knockback = 30.0`** — bare/under-sourced KB on
   the P1/P2/testcat default jab.
8. **`BLAST_PADDING_X = 100` / `MAX/MIN_SHIELD_RADIUS`** (config) — live gameplay values deliberately
   unregistered; resolve (ratify or source) rather than a fresh extraction.

## Tier 2 — AI / input / feel

9. **`controllers.py` inline `± 8` deadband** (level-less + follower paths) — reuse the named
   `SPACING_STOP = 8` the file already defines.
10. **`controllers.py` untagged Attacker defaults** (`attack_period 12`, `standoff 30`, `attack_range
    45`, `drop_threshold 20`) — add a basis tag or promote to named constants.
11. **The 120-frame hold threshold (×3 sites)** — extract one `ESC_HOLD_FRAMES` / `HOLD_TO_BACK_FRAMES`.
12. **`fighter_input.py` `0.1` air-dodge dead-zone (×3)** and **`player.py` `vel.y = 1` ledge nudge
    (×2)** — extract one named epsilon / one `LEDGE_DROP_NUDGE_VY` each.
13. **`tail.py` `_BASE_TURN_STEP 0.18` / `_PINNED 2`** — relocate to config with the other `TAIL_*`.

## Tier 3 — render / UI layout (large but low-risk)

14. **`options_menu.py` scaled-spacing family** (`10/8/6/4/30/80/90/12/40`) — highest-volume dedup.
15. **`win_screen.py` stats-table + crown geometry** (`180/100/20`, `0.5/0.75/0.8`, `8/22/0.7/3`, `135`).
16. **`hud.py` bottom-anchor `HUD_SPACING * 3/2` coupling** — name a bottom-row-slot constant.
17. **`body.py` `IDLE_BREATH_BOB_PX/SQUASH_PX`** (also a CHAR-VALUE item — see below).
18. **`char_select.py` / `text_entry.py` residual offsets**, **`presenters.py` bare `22` ×2**,
    **`esc_hold.draw_esc_hold_arc` geometry**, **`cat_faces.py` luma `110`** — small mechanical lifts.

---

# ⚠ Character-value candidates (shared consts that should be per-fighter)

The engine already threads most fighter stats as per-`FighterData` fields; the risk is a cat
**silently inheriting** a shared global for a value real fighters differ on. Ranked by how live the
drift is:

1. **Gnok `run_speed` (strong, shipping)** — Gnok sets `dash_speed = vel(1.8) = 9.72` but inherits
   `run_speed = DASH_SPEED = 8` (a config px global, *not* vel-scaled). Its sustained run (8) is
   **slower than its dash burst (9.72)** and off the faithful scale — the "fastest-mobility"
   super-heavyweight runs at the generic default. `gnok_cat.py → GNOK_FIGHTER_DATA`.
2. **Birky `dash_speed` / `run_speed` (strong, shipping)** — overrides `move_speed = 5` for the
   slow-featherweight identity but inherits `dash_speed = 8` / `run_speed = 8`; a slow-walk Kirby that
   dashes/runs at the generic 8 contradicts its stated identity. `birky_cat.py → BIRKY_FIGHTER_DATA`.
3. **Global `MAX_FALL_SPEED = 13` (the #557 case)** — a registered **DIVERGENCE**: one global fall
   speed for every cat, no Melee/PM base-vs-fast-fall split. Fall speed differs sharply per fighter
   (Fox/Falco ≫ Jigglypuff/Peach). Also **`GRAVITY 0.5` / `JUMP_VEL -13` / `MOVE_SPEED 6` /
   `DASH_SPEED 8` / `MAX_JUMPS 2`** are all PM-Mario-calibrated globals that shipped cats ride via the
   default. The per-fighter plumbing exists (`apply_gravity` takes a `gravity` arg, #126); the shipped
   cats just don't all set it. `config/physics.py` + each `*_cat.py`.
4. **Nalio `move_speed`/`dash_speed`/`jump_vel`/`max_jumps` (consistency)** — Nalio binds
   `gravity`/`max_fall_speed` explicitly "rather than silently inheriting," yet leaves these four to
   inherit. Intended (Nalio == baseline), but the same silent-inherit its own comment argues against;
   bind explicitly for parity. `nalio_cat.py → NALIO_FIGHTER_DATA`. (Narz `dash_speed` — mild, same.)
5. **`body.py` `IDLE_BREATH_BOB_PX = 3` / `SQUASH_PX = 1` (render, shipping)** — absolute breathing
   amplitude baked from Nalio's 60px body, applied to every archetype unscaled (period is already
   per-cat). A real per-character render value hardcoded shared.
6. **`config.FSMASH_ANGLE_UP = 50` / `FSMASH_ANGLE_DOWN = 330`** — the held-up/down f-smash launch
   angle is one global applied to *every* cat's `fsmash` (comment: "no per-character angle field").
   Currently deliberate; makes the angled f-smash identical across archetypes.
7. **`controllers.py` AI ranges** (`attack_range = 45`, `fireball_range = 450`, `shield_threat_range
   = 160`/`_dy = 80`, per-level `standoff`) — flat AI bands for every fighter; a long-reach vs
   short-reach cat should differ. `attack_range = 45` is exactly what `reach_aware` (#335) exists to
   supersede, but remains the reach-unaware fallback.
8. **`status.py` `STATUS_BAR_WIDTH` keyed to global `PLAYER_SIZE` (render, minor)** — above-head bar
   width won't track a differently-sized cat's real `stand_size` (cosmetic).
9. **`tail.py` + `TAIL_*` config (weak)** — the tail feel/structure system (`_PINNED`,
   `_BASE_TURN_STEP`, `TAIL_GRAVITY`, `TAIL_SEGMENT_LENGTH`, …) is one shared global profile; the audit
   brief lists "tail stiffness" as a per-fighter stat. Every other physics stat is already per-fighter
   — the tail is the one visible-feel system still hardwired for all cats.
10. **`body_zones.BODY_ZONES` (weak)** — one shared body-relative-placement table, but only Birky uses
    `zone_dy`; other cats author raw absolute `dy`, so the guarantee is applied inconsistently.

**Correctly global (not char-value):** `weight` (already per-`FighterData`, not a config global),
match-rule globals (`INITIAL_LIVES`, `BLAST_PADDING*`, `RESPAWN_DELAY_FRAMES`), and engine-global
scalars (`HITLAG_*`, `SHIELDSTUN_FACTOR`, `CLANK_PRIORITY_RANGE`, `PX_PER_UNIT`).

---

# Follow-up tickets (filed under tracker #1134)

Filed as an umbrella + 4 children downstream of this doc (audit itself is closed via #1002):

- **Tracker #1134** — magic-number + char-value cleanup epic.
  1. **#1135 — DEV: extract + register Tier-1 combat/physics values** (knockback coefficients,
     GETUP_ATTACK, the 3 registry-orphans, `min_overlap`, default-cat KB).
  2. **#1136 — RESEARCH: character-value drift** (Gnok `run_speed`, Birky `dash/run_speed`, and
     whether shipped cats should stop inheriting the Mario movement globals). A basis-required change
     per RULES "Changing a game value" — sourcing or a designer decision, not a bare DEV.
  3. **#1137 — verify + fix two `_WAIT` comment-label errors** (Narz↔Birky "Kirby/Marth" mislabels;
     confirm the 111/71 values aren't swapped — escalates to a data bug if they are).
  4. **#1138 — DEV: Tier-2/3 render + UI layout extraction** (options_menu spacing, win_screen
     geometry, the ×3 hold-frame SSOT, HUD-hint `24`). Lower risk, batchable.
