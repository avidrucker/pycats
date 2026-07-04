"""Hierarchical + parallel fighter statechart. This is the sole fighter-FSM
(ADR-0002: the behavior-equivalent flat FSM, systems.fighter_fsm, was removed
in #178).

Structure (Task 3 of PM Phase 0):

    root  (parallel)
    ├── action  (compound, initial=idle)   <- force_ko / force_idle hoisted here
    │   ├── actionable  (compound, initial=idle)
    │   │   ├── grounded  (compound, initial=idle)
    │   │   │   ├── idle    (leaf)
    │   │   │   ├── walk     (leaf)
    │   │   │   └── shield  (leaf)
    │   │   └── airborne  (compound, initial=jump)
    │   │       ├── jump    (leaf)
    │   │       └── fall    (leaf)
    │   ├── attacking  (compound, initial=startup)   <- split in Task 4
    │   │   ├── startup  (leaf)
    │   │   ├── active   (leaf)
    │   │   └── recovery (leaf)            <- all map to flat label "attack"
    │   ├── dodging    (compound, initial=dodge)
    │   │   └── dodge    (leaf)
    │   ├── hitstun    (compound, initial=hurt)
    │   │   ├── hurt    (leaf)
    │   │   └── stun    (leaf)             <- preserved-but-unreachable quirk
    │   └── ko          (leaf)
    └── defensive_status  (compound, initial=vulnerable)
        ├── vulnerable   (leaf)
        └── intangible   (leaf)

LEAF ids equal the flat labels (idle, walk, jump, fall, shield, dodge, ko, hurt,
stun) so in_state("idle") etc. keep working. The attacking sub-phase leaves
(startup, active, recovery) do NOT match a flat label individually; instead
StatechartEngine.state maps in_state("attacking") -> "attack", so the flat
label stays "attack" across all three sub-phases. Compound/grouping ids
(action, actionable, grounded, airborne, attacking, dodging, hitstun, root,
defensive_status) are distinct and never collide with leaf labels.

Every tick transition fires on the explicit "tick" event (no eventless
transitions): one send("tick") performs at most one hop, matching the legacy
FSM's break-after-first behavior.

Transition selection note (SCXML / statecharts-py): for each active atomic
state the engine scans the leaf's transitions first (in document order), then
climbs to ancestors only if none matched. So leaf transitions take priority
over hoisted parent transitions. Because the legacy per-leaf transition
ORDERING differs between leaves (e.g. idle/walk check attack+dodge first, but
fall checks idle/walk/jump/ko before dodge), the tick transitions are kept on
their leaves verbatim to guarantee byte-identical priority/parity. Only the
force_ko / force_idle transitions — which fire on distinct events and therefore
never conflict with the per-leaf tick ordering — are hoisted to the `action`
compound parent so every action leaf inherits them in one place.
"""

from __future__ import annotations

from statecharts import on, parallel, state, statechart, transition


def _tick(cond, target):
    return transition({"event": "tick", "cond": cond, "target": target})


def build_fighter_chart(p):
    """p is the owning Player; guards read its live attributes."""

    grounded = state(
        {"id": "grounded", "initial": "idle"},
        state(
            {"id": "idle"},
            _tick(lambda e, d: p.attack_timer > 0, "attacking"),
            _tick(lambda e, d: p.fighter.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.fighter.dash_timer > 0, "dash"),
            _tick(lambda e, d: p.fighter.crouch_attempting and p.fighter.on_ground, "crouch"),
            _tick(lambda e, d: p.fighter.vel.x != 0 and p.fighter.on_ground, "walk"),
            _tick(lambda e, d: p.fighter.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.fighter.on_ground and p.fighter.vel.y > 0, "fall"),
            _tick(lambda e, d: p.fighter.shield_attempting, "shield"),
            _tick(lambda e, d: p.fighter.hurt_timer > 0, "hurt"),
        ),
        state(
            {"id": "walk"},
            _tick(lambda e, d: p.attack_timer > 0, "attacking"),
            _tick(lambda e, d: p.fighter.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.fighter.dash_timer > 0, "dash"),
            _tick(lambda e, d: p.fighter.crouch_attempting and p.fighter.on_ground, "crouch"),
            _tick(lambda e, d: p.fighter.vel.x == 0, "idle"),
            _tick(lambda e, d: p.fighter.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.fighter.on_ground and p.fighter.vel.y > 0, "fall"),
            _tick(lambda e, d: p.fighter.hurt_timer > 0, "hurt"),
            _tick(lambda e, d: p.fighter.shield_attempting and p.fighter.on_ground, "shield"),
        ),
        # Dash (#388, slice 2a): the initial-dash burst, entered while dash_timer > 0
        # (started via Fighter._start_dash — slice 2b's double-tap is the caller).
        # Exits to walk/idle when the burst window expires; run (the sustained state
        # after the burst) is slice 3. Grounded burst; standard interrupts apply.
        state(
            {"id": "dash"},
            _tick(lambda e, d: p.attack_timer > 0, "attacking"),
            _tick(lambda e, d: p.fighter.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.fighter.hurt_timer > 0, "hurt"),
            _tick(lambda e, d: p.fighter.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.fighter.on_ground and p.fighter.vel.y > 0, "fall"),
            _tick(lambda e, d: p.fighter.dash_timer == 0 and p.fighter.vel.x != 0, "walk"),
            _tick(lambda e, d: p.fighter.dash_timer == 0 and p.fighter.vel.x == 0, "idle"),
        ),
        # Crouch (#124): hold down on solid ground. Movement is locked (see
        # fighter_input), the body Rect resizes + the hurtbox lowers (Player).
        state(
            {"id": "crouch"},
            _tick(lambda e, d: p.attack_timer > 0, "attacking"),
            _tick(lambda e, d: p.fighter.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.fighter.vel.y < 0, "jump"),
            _tick(lambda e, d: p.fighter.hurt_timer > 0, "hurt"),
            _tick(lambda e, d: not p.fighter.on_ground, "fall"),
            _tick(lambda e, d: not p.fighter.crouch_attempting, "idle"),
        ),
        state(
            {"id": "shield"},
            # Shield-break stun (#12) takes priority: a depleted shield calls
            # _start_stun (stun_timer > 0) and the fighter is dizzy regardless of
            # whether shield is still held.
            _tick(lambda e, d: p.fighter.stun_timer > 0, "stun"),
            _tick(lambda e, d: not p.fighter.shield_attempting, "idle"),
            _tick(lambda e, d: p.fighter.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.fighter.vel.y < 0, "jump"),
        ),
    )

    airborne = state(
        {"id": "airborne", "initial": "jump"},
        state(
            {"id": "jump"},
            _tick(lambda e, d: p.attack_timer > 0, "attacking"),
            _tick(lambda e, d: p.fighter.vel.y >= 0, "fall"),
            _tick(lambda e, d: not p.fighter.is_alive, "ko"),
            _tick(lambda e, d: p.fighter.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.fighter.hurt_timer > 0, "hurt"),
        ),
        state(
            {"id": "fall"},
            _tick(lambda e, d: p.attack_timer > 0, "attacking"),
            _tick(lambda e, d: p.fighter.on_ground and p.fighter.vel.x == 0, "idle"),
            _tick(lambda e, d: p.fighter.on_ground and p.fighter.vel.x != 0, "walk"),
            _tick(lambda e, d: p.fighter.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.fighter.is_alive, "ko"),
            _tick(lambda e, d: p.fighter.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.fighter.hurt_timer > 0, "hurt"),
        ),
    )

    actionable = state(
        {"id": "actionable", "initial": "idle"},
        grounded,
        airborne,
    )

    # Task 4: the single `attack` leaf is split into startup/active/recovery
    # sub-phases. The flat label "attack" is recovered in StatechartEngine.state
    # via in_state("attacking"), so player.state reads "attack" throughout.
    #
    # Phase progression mirrors the player's move clock (post-increment, so the
    # first update after the press is move_frame == 1):
    #   startup  -> active   when move_frame > current_move.startup
    #   active   -> recovery when move_frame > startup + active
    # The active window is therefore startup < move_frame <= startup+active,
    # identical to where the player spawns the hitbox.
    #
    # The EXIT (-> idle / -> fall) reads p.done_attacking (derived, #321). It is placed
    # on each phase leaf (first, so it has priority and can fire from whichever
    # phase is active when attack_timer hits 0). Because the total move duration
    # == startup+active+recovery == attack_timer, the exit fires on the frame
    # attack_timer hits 0, preserving the golden.
    #
    # Each guard reading current_move first checks for None to avoid
    # AttributeError when no move is live.
    def _mf_gt(thresh):
        return lambda e, d: p.current_move is not None and p.move_frame > thresh(p.current_move)

    attacking = state(
        {"id": "attacking", "initial": "startup"},
        state(
            {"id": "startup"},
            _tick(lambda e, d: p.done_attacking and p.fighter.on_ground, "idle"),
            _tick(lambda e, d: p.done_attacking and not p.fighter.on_ground, "fall"),
            _tick(_mf_gt(lambda m: m.startup), "active"),
        ),
        state(
            {"id": "active"},
            _tick(lambda e, d: p.done_attacking and p.fighter.on_ground, "idle"),
            _tick(lambda e, d: p.done_attacking and not p.fighter.on_ground, "fall"),
            _tick(_mf_gt(lambda m: m.startup + m.active), "recovery"),
        ),
        state(
            {"id": "recovery"},
            _tick(lambda e, d: p.done_attacking and p.fighter.on_ground, "idle"),
            _tick(lambda e, d: p.done_attacking and not p.fighter.on_ground, "fall"),
        ),
    )

    dodging = state(
        {"id": "dodging", "initial": "dodge"},
        state(
            {"id": "dodge"},
            # Waveland (#202): a diagonal-down air dodge that lands cancels into a
            # grounded slide + landing lag (landing_lag_timer set in _handle_landing).
            # Highest priority so it wins over the shield/idle ground exits.
            _tick(
                lambda e, d: p.fighter.dodge_timer <= 0 and p.fighter.on_ground and p.fighter.landing_lag_timer > 0,
                "landing_lag",
            ),
            _tick(
                lambda e, d: p.fighter.shield_attempting and p.fighter.dodge_timer <= 0 and p.fighter.on_ground,
                "shield",
            ),
            _tick(
                lambda e, d: (
                    not p.fighter.shield_attempting
                    and p.fighter.dodge_timer <= 0
                    and p.fighter.on_ground
                    and not p.fighter.spot_dodge_shield_held
                ),
                "idle",
            ),
            # PM air dodge (#184): an air dodge exits into `helpless` (special-fall),
            # not straight to `fall` — locked out of actions until landing. A
            # non-air (ground) dodge that somehow ends airborne still falls.
            _tick(
                lambda e, d: p.fighter.dodge_timer <= 0 and not p.fighter.on_ground and p.fighter.air_dodge_active,
                "helpless",
            ),
            _tick(
                lambda e, d: p.fighter.dodge_timer <= 0 and not p.fighter.on_ground and not p.fighter.air_dodge_active,
                "fall",
            ),
        ),
    )

    hitstun = state(
        {"id": "hitstun", "initial": "hurt"},
        state(
            {"id": "hurt"},
            _tick(lambda e, d: p.fighter.hurt_timer <= 0 and p.fighter.on_ground, "idle"),
            _tick(lambda e, d: p.fighter.hurt_timer <= 0 and not p.fighter.on_ground, "fall"),
        ),
        state(
            {"id": "stun"},
            _tick(lambda e, d: p.fighter.stun_timer <= 0 and p.fighter.on_ground, "idle"),
            _tick(lambda e, d: p.fighter.stun_timer <= 0 and not p.fighter.on_ground, "fall"),
        ),
    )

    ko = state(
        {"id": "ko"},
        _tick(lambda e, d: p.fighter.is_alive, "idle"),
    )

    # Prone / knockdown (#13): force-entry only (entered via force_prone, hoisted
    # below; the landing-velocity trigger is #145). The only self-initiated action
    # is standing up — the getup window is prone_timer counting to 0 -> idle (on
    # ground) / fall (airborne). Mirrors the flat FSM "prone" order (parity).
    prone = state(
        {"id": "prone"},
        # Getup-roll (#146): if a direction was held as the getup window closed,
        # player.update has started the roll (getup_roll_timer > 0) before this tick
        # — route to the roll instead of the neutral stand. Highest priority so it
        # wins over the plain idle/fall getup exits below.
        _tick(lambda e, d: p.fighter.prone_timer <= 0 and p.fighter.getup_roll_timer > 0, "getup_roll"),
        # Getup-attack (#225): if attack was held at getup, player.update started the
        # wake-up move on the clock (getup_attack_active) — swing instead of standing.
        _tick(lambda e, d: p.fighter.prone_timer <= 0 and p.fighter.getup_attack_timer > 0, "getup_attack"),
        _tick(lambda e, d: p.fighter.prone_timer <= 0 and p.fighter.on_ground, "idle"),
        _tick(lambda e, d: p.fighter.prone_timer <= 0 and not p.fighter.on_ground, "fall"),
    )

    # Getup-roll (#146): a directional, intangible getup out of prone. The roll's
    # velocity (set in start_getup_roll) decays under friction; input stays locked
    # until the roll window closes -> idle. Intangibility (invulnerable) is dropped
    # by player.update when getup_roll_timer hits 0.
    getup_roll = state(
        {"id": "getup_roll"},
        _tick(lambda e, d: p.fighter.getup_roll_timer <= 0 and p.fighter.on_ground, "idle"),
        _tick(lambda e, d: p.fighter.getup_roll_timer <= 0 and not p.fighter.on_ground, "fall"),
    )

    # Getup-attack (#225): the wake-up attack out of prone. Its hitbox spawns via
    # the move clock (started in player.update); the state ends when the move
    # completes (attack_timer hits 0), recovering to idle. Intangibility is dropped
    # by player.update at the same point.
    getup_attack = state(
        {"id": "getup_attack"},
        _tick(lambda e, d: p.fighter.getup_attack_timer <= 0 and p.fighter.on_ground, "idle"),
        _tick(lambda e, d: p.fighter.getup_attack_timer <= 0 and not p.fighter.on_ground, "fall"),
    )

    # Helpless / special-fall (#184): entered after an air dodge's timer expires
    # (air_dodge_active). No self-initiated transitions — normal actions are locked
    # out here (also gated in fighter_input); the fighter falls under normal gravity
    # and only recovers on landing -> idle. Wavedash (air dodge into the ground) is
    # deferred to #184b.
    helpless = state(
        {"id": "helpless"},
        # Waveland from special-fall (#202): if the air dodge's helpless fall ends on
        # the ground while a landing-lag window is armed, route through landing_lag;
        # otherwise a plain helpless landing recovers straight to idle (#184).
        _tick(lambda e, d: p.fighter.on_ground and p.fighter.landing_lag_timer > 0, "landing_lag"),
        _tick(lambda e, d: p.fighter.on_ground, "idle"),
    )

    # Waveland landing lag (#202): grounded action-lock after a wavedash. No
    # self-initiated transitions — input is gated in player.update while the timer
    # runs (the slide decays under GROUND_FRICTION meanwhile); recovers to idle when
    # the lag window closes.
    landing_lag = state(
        {"id": "landing_lag"},
        _tick(lambda e, d: p.fighter.landing_lag_timer <= 0, "idle"),
    )

    # Ledge-hang (#14): force-entry via force_ledge_grab (player.update detects the
    # grab and sends it, mirroring force_prone). The hang holds while grabbed_ledge
    # is set; player.update releases it — neutral getup repositions onto the stage
    # (-> idle), while drop/timeout leaves the fighter airborne (-> fall).
    # Intangibility reuses `invulnerable`, so the defensive_status region flips to
    # intangible for free.
    ledge_hang = state(
        {"id": "ledge_hang"},
        # Neutral getup started (#311): a climb window (ledge_getup_timer) opens; the
        # edge frees to others at half and the fighter finishes onto the stage.
        _tick(lambda e, d: p.fighter.grabbed_ledge is not None and p.fighter.ledge_getup_timer > 0, "ledge_getup"),
        _tick(lambda e, d: p.fighter.grabbed_ledge is None and p.fighter.on_ground, "idle"),
        _tick(lambda e, d: p.fighter.grabbed_ledge is None and not p.fighter.on_ground, "fall"),
    )

    # Ledge neutral getup climb (#311): a short action-lock on the stage after a
    # getup input. player.update ticks ledge_getup_timer, frees the edge at ~half,
    # and clears grabbed_ledge when the window closes -> idle (on the stage).
    ledge_getup = state(
        {"id": "ledge_getup"},
        _tick(lambda e, d: p.fighter.grabbed_ledge is None and p.fighter.on_ground, "idle"),
        _tick(lambda e, d: p.fighter.grabbed_ledge is None and not p.fighter.on_ground, "fall"),
    )

    # Smash charge (#327 slice 3a): a pre-swing HOLD, force-entered on a chargeable
    # smash press (fighter_input sends force_smash_charge). The charge accumulates
    # in fighter_input (smash_charge_timer, capped); on release/max it starts the
    # move clock (attack_timer > 0) and this state routes into `attacking` for the
    # actual swing. A mid-charge hit sets hurt_timer (and cancel_smash_charge clears
    # the pending key) -> exit to hurt. Charge happens BEFORE the move clock, so the
    # move-clock invariant (#71) is untouched.
    smash_charge = state(
        {"id": "smash_charge"},
        _tick(lambda e, d: p.attack_timer > 0, "attacking"),  # released/maxed -> swing
        _tick(lambda e, d: p.fighter.hurt_timer > 0, "hurt"),  # hit mid-charge
        _tick(lambda e, d: p.fighter.stun_timer > 0, "stun"),
        _tick(lambda e, d: not p.fighter.is_alive, "ko"),
        # Charge abandoned without firing (pending cleared, no swing started).
        _tick(lambda e, d: p.fighter.pending_smash_key is None and p.attack_timer == 0 and p.fighter.on_ground, "idle"),
        _tick(
            lambda e, d: p.fighter.pending_smash_key is None and p.attack_timer == 0 and not p.fighter.on_ground, "fall"
        ),
    )

    action = state(
        {"id": "action", "initial": "idle"},
        # force_ko / force_idle / force_prone / force_ledge_grab / force_smash_charge
        # hoisted to the action parent: they fire on distinct events, so they never
        # reorder the per-leaf tick transitions.
        on("force_ko", "ko"),
        on("force_idle", "idle"),
        on("force_prone", "prone"),
        on("force_ledge_grab", "ledge_hang"),
        on("force_smash_charge", "smash_charge"),
        actionable,
        attacking,
        dodging,
        hitstun,
        ko,
        prone,
        getup_roll,
        getup_attack,
        helpless,
        landing_lag,
        ledge_hang,
        ledge_getup,
        smash_charge,
    )

    defensive_status = state(
        {"id": "defensive_status", "initial": "vulnerable"},
        state(
            {"id": "vulnerable"},
            _tick(lambda e, d: p.fighter.invulnerable, "intangible"),
        ),
        state(
            {"id": "intangible"},
            _tick(lambda e, d: not p.fighter.invulnerable, "vulnerable"),
        ),
    )

    return statechart(
        {"initial": "root"},
        parallel({"id": "root"}, action, defensive_status),
    )
