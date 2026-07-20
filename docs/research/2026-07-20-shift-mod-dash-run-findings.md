# Hold-Shift dash/run modifier — mechanism, coexistence toggle, golden-safety (#800)

> Research findings for **#800** (child of umbrella **#799**, hold-Shift dash/run
> modifier). Scopes the mechanism + risks of a hold-Shift (LShift=P1, RShift=P2)
> dash/run trigger before the **(ii) DECISION** child of #799 is filed. Design/spec
> reconnaissance only — **no code changes, no design decision** (that is (ii)).
> Date: 2026-07-20. Agent: APPLE.

## TL;DR

- **A mod-key run route is already RATIFIED** — `docs/research/2026-07-01-walk-run-dash-pycats-design.md`
  (#374) **D2-C**: "**Mod-key + direction → Run (direct)** — the modifier route straight
  into sustained run, skipping the dash burst." It is slice **4** of that doc's ordered
  implementation tracker ("Mod-key → run (the D2-C direct-run input)"). #799's hold-Shift
  proposal **is** that route. The research question is therefore not *"should pycats have a
  mod-key dash/run?"* (answered: yes, ratified) but *"does #799 supersede the shape #374
  ratified, and how?"*
- **#799 diverges from #374 in model, not in existence.** #374 makes double-tap and mod-key
  **complementary and both permanently on, no flag** (double-tap → dash-burst → run; mod-key
  → run directly). #799 wants shift-mod as the **default** with double-tap **demoted to an
  options toggle** and a runtime-selectable **dash-trigger-mode** setting for A/B — an
  *either/or* framing. The (ii) decision must consciously pick: honour #374's both-on additive
  model, or supersede D2 with the toggle/A-B model.
- **"Run" does not exist yet.** Source confirms only the **initial-dash burst** is
  implemented (`Fighter._start_dash`); the sustained `run` state is #374 slice 3, **not
  built**. So "dash/run" today = a 12-frame burst at `dash_speed`, then decay back to walk.
- **The default flip is golden-safe by construction**, and #374 already argued why: the
  faster states are reached **only** through inputs the scripted goldens + default controller
  never emit. Source-verified: the sim keymaps (`sim/runner.py`) bind no Shift, no controller
  emits Shift or a double-tap, and `runtime_settings` is present-layer only (the sim never
  reads it). The one real trap is **where the mode setting is read** (see Q4).

---

## Q1 — Comparable-game mapping of a hold-modifier walk↔run

Grounded in the #373 primary-source doc (`docs/research/2026-07-01-pm-walk-run-dash-mechanics.md`)
and its #407 addendum:

- **Project M / Melee use an *analog* split, not a modifier.** Walk = partial stick tilt;
  initial-dash = a hard tap past a magnitude threshold; run = holding past the dash window.
  The chain is **tilt→walk** / **tap→dash→(hold)→run** (#373 Q2). There is no "run button" in
  PM — the modifier is a *keyboard invention* to stand in for the missing analog axis.
- **A keyboard has no tilt magnitude**, so every digital port must choose a proxy. #373's
  handoff explicitly lists the candidates for #374: *"hold-to-walk/tap-to-dash, a modifier, a
  double-tap, or a reduced model."* A **hold-modifier + direction** is one of those named
  proxies — legitimate, not ad-hoc.
- **Feel/ergonomics tradeoffs for a held modifier (from the analog-vs-digital gap):**
  - *Discoverability & reliability:* a modifier is unambiguous and repeatable (no timing
    window), where a double-tap depends on a tuned window (`DOUBLE_TAP_WINDOW = 8`, itself a
    placeholder tuned to human double-tap ergonomics, **not** a PM value — #407). Shift-mod
    removes the fat-finger/timing failure mode.
  - *Momentum/reversal:* PM's run cannot instantly flip direction (needs skid/pivot, #373 Q2).
    A held modifier makes direction changes trivial (just move the other arrow), which is
    *less* PM-faithful than the tap route's dash-dance/skid feel — a reason #374 gave the
    modifier the **direct-run** semantics (skip the agile dash-burst layer) rather than
    routing it through dash.
  - *Release behaviour:* the open sub-question — does releasing Shift mid-run drop straight to
    walk, or decay through a skid? PM has no modifier to copy, so this is a pycats design call
    (feeds (ii)). Direction change while held (Shift + flip arrow) similarly needs a defined
    rule (instant reverse-run vs skid).

## Q2 — Interaction with the existing model (burst-then-decay)

Source: `pycats/entities/fighter_input.py::_maybe_start_dash` (double-tap edge-detect) →
`pycats/entities/fighter.py::_start_dash` (the burst).

- **Today's live model is burst-only.** `_maybe_start_dash` arms `dash_input_window` on a
  fresh directional press; a second same-direction press inside the window calls `_start_dash`,
  which sets `dash_timer = DASH_DURATION` (12) and `vel.x = direction * dash_speed` (8). While
  `dash_timer > 0`, held movement is at `dash_speed` (see `handle_move`: `move_speed =
  dash_speed if dash_timer > 0 else move_speed`); after it, movement decays back to walk. There
  is **no sustained run** — the "run" in `_start_dash`'s docstring is explicitly *"slice 3"* and
  unbuilt.
- **#374 already specified how a mod-key should feed this:** route the modifier **directly to
  `run`** (the committed sustained state), *skipping* the dash burst (D2-C). That means the
  Shift path is **not** just "call `_start_dash` on Shift+dir" — it wants a `run` state that
  does not exist yet. So implementing #799 the #374 way **has `run` (slice 3) as a
  prerequisite**; implementing it as "Shift = the burst" is a *reduced* interpretation that
  diverges from D2-C. This fork is a decision input for (ii).
- **Gating already in place** (`_maybe_start_dash` guard) that a Shift route must mirror: only
  when `on_ground and dash_timer == 0 and hurt_timer == 0 and stun_timer == 0 and not shield-held
  and state in ("idle","walk")`. A held Shield turns a directional press into a **dodge**, not a
  dash (the shield branch), so Shift+direction+Shield precedence must be defined.

## Q3 — Run status (source-cited)

**Confirmed: pycats has only the initial-dash burst; no sustained `run` state exists.**

- `pycats/entities/fighter.py::_start_dash` docstring (verbatim): *"`run` (the sustained state
  after the burst) is slice 3. Grounded only for now."* The method sets only `dash_timer`,
  `vel.x`, and `facing_right`.
- `pycats/config.py` (walk/dash/run comment): *"DASH_DURATION = the initial-dash burst window
  in frames … run — the sustained state after the burst — is slice 3 of #388."*
- #374's ordered tracker lists "Dash→run transition + `run` state + `run_speed`" as slice **3**
  and "Mod-key → run" as slice **4** — neither is built (grep: no `run_speed`, no `run` FSM leaf;
  the historical `run` leaf is the *mislabelled walk* #374 slice 1 planned to rename).

**Implication for #799:** "dash/**run**" is aspirational under the current engine. The umbrella
should decide whether it targets *run* (needs slice 3 first) or ships a Shift-**burst** as an
interim (a reduced model vs #374 D2-C).

## Q4 — Coexistence + where the dash-trigger-mode setting lives

**The load-bearing constraint: the dash trigger is decided inside `fighter_input`, which the
deterministic sim executes.** `Player.update → handle_actions → _maybe_start_dash` runs in the
golden/sim path. Therefore:

- **A dash-trigger-mode read from `runtime_settings` inside `fighter_input` would couple the sim
  to the present layer and break the byte-identical golden guarantee.** `runtime_settings.py` and
  `settings.py` are documented **present-layer only** — *"the deterministic sim and golden tests
  never read it."* Putting the mode there and reading it in the input decoder violates that
  boundary. So `runtime_settings` is the **wrong home** for a value the sim's input path must
  honour, even though it is the precedent for *render* toggles (`show_status_timer_bars`,
  `show_dev_info`).
- **The control/keybind layer is the right home**, because the sim already takes the control
  scheme as an **explicit, passed-in input**, not a global: `compile_timeline(spans, keymaps)`
  and controllers read `a.controls`. Two clean shapes for the mode:
  1. **Make Shift a real binding and keep both triggers permanently live (the #374 model).**
     Add a `dash`/`run` modifier action to the `Keymap` (P1 `LSHIFT`, P2 `RSHIFT`, in
     `pycats/app.py` `P1_KEYS`/`P2_KEYS`). `_maybe_start_dash` (or a sibling) checks
     `_pressed(held, "run")`. The sim keymaps (`sim/runner.py`) simply **don't bind it**, so the
     modifier is inert in sim → golden-safe with **no mode flag at all**. Double-tap stays live
     too. This is the *least code / most golden-safe* path and matches D2's "no flag" claim —
     but it does **not** give the user the "double-tap OFF" option, only "both on."
  2. **A per-scheme dash-trigger-mode ride-along** for the true A/B (double-tap on/off). Carry a
     `dash_trigger_mode` alongside each player's control map (e.g. a field on `Keymap`, or a
     parallel per-player control-scheme value), so it is an explicit sim input like the keymap.
     The live game defaults it to `shift-mod`; the Options menu flips the double-tap half; the
     **sim/golden keymaps pin it to whatever keeps the burst path unreachable** (they emit
     neither Shift nor double-tap, so either value is byte-identical). The options-menu double-tap
     toggle then lives in `options_menu.py` and writes a **persisted pref** (`settings.py` schema
     + `runtime_settings`) that seeds the *live-game* control scheme at startup — the pref feeds
     the control layer, it is **not** read inside `fighter_input`.
- **Tradeoff summary for (ii):** shape (1) is simplest and needs no new setting, but can't
  express "double-tap disabled." Shape (2) delivers the user's exact ask (default shift-mod +
  double-tap as a toggle) but introduces a per-scheme mode primitive and must keep the
  present-layer/sim boundary intact by threading the mode through the *control scheme*, never
  through a `runtime_settings` read in the input decoder.

## Q5 — Golden-safety of the default flip (source-verified)

**Shipping shift-mod as default + a double-tap options toggle does not move the sim goldens,**
provided the mode is threaded per Q4 (never read from `runtime_settings` inside `fighter_input`).
Evidence:

- **No Shift anywhere in the sim inputs.** `pycats/sim/runner.py` `P1_KEYS`/`P2_KEYS` bind only
  `left/right/up/down/attack/special/shield/smash` — **no Shift, no run/dash modifier**. Adding
  LShift/RShift to the *live-game* `app.py` keymaps leaves these untouched.
- **Scripted inputs cannot emit a modifier and cannot double-tap.** `sim/input_script.py`
  `ACTIONS = ("left","right","up","down","attack","shield","smash")` — no modifier action;
  timelines are *held spans*, and a held key is `pressed` only on its down-frame, so a held
  direction never double-taps. (Confirmed by the `DEFAULT_SCRIPT`/`COMBAT_SCRIPT` spans.)
- **No controller emits Shift or a double-tap.** Every `decide()` in `sim/controllers.py`
  returns a set of held keys drawn from `a.controls[...]` (`left/right/up/down/attack/shield/
  special`); none references a modifier, and movement is *held*, not tapped — so the
  double-tap/burst path is never reached. This is the same invariant #374 D3 relied on.
- **`runtime_settings` is not on the sim path** (documented present-layer only), so a persisted
  default of `shift-mod` cannot reach the golden run — *as long as the input decoder does not
  read it* (the Q4 boundary).

**What the (iii) implementation must assert** (able-to-fail regression tests):
1. With no modifier and no double-tap, a plain-held direction produces **walk** (`MOVE_SPEED`)
   under *either* default mode — the golden byte-identity guard (extend the existing
   golden/render-parity suites; they must stay green after the default flip).
2. The sim keymaps/controllers still emit no modifier (a census/guard that `sim/runner.py`
   keymaps and `ACTIONS` contain no run/dash-modifier action — de-censused per the
   `question-brittle-tests` lesson, i.e. assert the *behaviour* stays walk, not a frozen exact
   key set).
3. A live-game control scheme with `dash_trigger_mode = shift-mod` + Shift-held + direction
   produces the dash/run response; with the double-tap toggle off, a double-tap does **not**.

## Q6 — Edge cases (feed the decision)

Enumerated from the `fighter_input.handle_actions` branch structure and existing state gates:

- **Shift + Shield held:** Shield already converts a directional press into a **dodge/roll**
  (Priority-1/3 in `handle_actions`), and `_maybe_start_dash` explicitly excludes shield-held
  taps. Rule needed: Shift is inert while Shield is held (dodge wins), or a defined precedence.
- **Shift during crouch:** movement is *locked* in `crouch` (`handle_move` `locked=` set includes
  "crouch"), and `_maybe_start_dash` gates on `state in ("idle","walk")`. Shift+dir from crouch
  should be a no-op (or defined) — must not bypass the crouch lock.
- **Shift in the air:** dash/run are grounded-only (`on_ground` gate). Shift airborne should not
  produce a ground burst; interaction with air-speed is out of scope (#229).
- **Shift during dodge / smash_charge / helpless / hitstun:** all movement-locked or input-gated
  states. `_maybe_start_dash` gates on `hurt_timer == 0 and stun_timer == 0`; `Player.update`
  skips `handle_actions` during hitstun. Shift must respect the same gates (no dash out of
  hitstun/charge).
- **Both players simultaneously:** LShift (P1) and RShift (P2) are disjoint physical keys, mapped
  per-player like every other action — no shared-key contention. (Confirmed: `app.py` keymaps are
  fully disjoint P1/P2 sets.)
- **Remapping LShift/RShift in the keybind UI:** the keybind system stores bindings by
  `pygame.key.name` (`keybind_store.py`) and rebinds live via the shared `Keymap` instance
  (#439/#447). A new modifier action participates automatically *if added as a standard action*;
  the keybind menu/sets UI (`keybind_menu.py`, `keybind_sets_menu.py`) and the conflict check must
  treat it like any other bindable action (a modifier bound to the same key as another action is a
  conflict to surface).
- **Wavedash interaction:** wavedash is a Shield+down(+direction) **air dodge** (`#202`, the
  dodge branch) — a different modifier (Shield), grounded vs air, so no direct collision. But if
  Shift is ever considered as a general modifier, confirm it does not shadow the Shield-based
  wavedash/spot-dodge inputs.
- **Dash-dependent moves:** none exist yet (no dash-attack / dash-grab in the kit); flagged so the
  decision notes dash-attack is downstream (#374 non-goals / advanced tech).

---

## Deliverable status & handoff to (ii)

This doc answers Q1–Q6 with source citations for Q3/Q5 (and surfaces the #374 ratification the
umbrella did not account for). **The single most important input to the (ii) DECISION:** #799's
"shift-mod default + double-tap as an options toggle, A/B-selectable" is a **different model** from
the already-ratified #374 D2 ("both triggers permanently on, complementary semantics, no flag").
(ii) must decide whether to:

- **(a) Honour #374 D2** — both on, no toggle, Shift → direct-run (needs slice 3 `run` first);
  simplest, already golden-safe, but no "double-tap off."
- **(b) Supersede #374 D2** with the toggle/A-B model — delivers the user's exact ask, adds a
  per-scheme `dash_trigger_mode` primitive (homed in the control/keybind layer per Q4, **not**
  `runtime_settings`), and an Options double-tap toggle.

Either way: run (`slice 3`) is a prerequisite for a faithful "dash/**run**"; a Shift-**burst** is
the reduced interim. No tuning-value changes are implied by this research.

## Cross-refs

- PM facts: `docs/research/2026-07-01-pm-walk-run-dash-mechanics.md` (#373) + #407 addendum.
- Ratified design this reopens: `docs/research/2026-07-01-walk-run-dash-pycats-design.md` (#374, D2-C + slice 4).
- Code: `pycats/entities/fighter_input.py::_maybe_start_dash`, `pycats/entities/fighter.py::_start_dash`,
  `pycats/config.py` (`DASH_SPEED`/`DASH_DURATION`/`DOUBLE_TAP_WINDOW`/`MOVE_SPEED`),
  `pycats/app.py` (`P1_KEYS`/`P2_KEYS` live keymaps), `pycats/sim/runner.py` (sim keymaps),
  `pycats/sim/input_script.py` (`ACTIONS`), `pycats/sim/controllers.py` (no modifier emitted),
  `pycats/runtime_settings.py` + `pycats/settings.py` (present-layer boundary),
  `pycats/keybind_store.py` / `keybind_menu.py` / `keybind_sets_menu.py` (rebind path),
  `pycats/options_menu.py` (toggle home).
- Umbrella: #799. This child: #800. Design lineage: #388 (design #374).
