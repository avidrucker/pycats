"""
pycats/entities/fighter_input.py

FighterInput — translates an InputFrame into a fighter's actions (jump, dodge,
shield, attack, horizontal move). The input-decode/handling concern lifted out
of the Player god-object (#73 / D1 slice 3). It holds a reference to its owning
Player and mutates it; Player delegates handle_actions/handle_move/_pressed here.

This is the designated home for #67's B/special move routing (the attack branch
in handle_actions). Behaviour is verbatim the old Player methods, minus three
shipped DEBUG print() calls.
"""

from __future__ import annotations

from ..combat.move_select import resolve_move_key, select_move_key
from ..config import DODGE_SPEED, DOUBLE_TAP_WINDOW, SMASH_CHARGE_FRAMES
from ..storage import dev_log
from ..systems.movement import step_horizontal

# Horizontal-velocity threshold (px/frame) below which an air dodge counts as having
# "no horizontal velocity" — the seam between a neutral air dodge (redirectable) and a
# momentum air dodge. Distinct from config.VEL_DEADZONE (0.05, the friction dead-zone).
_AIRDODGE_VEL_DEADZONE = 0.1


class FighterInput:
    """Reads the owning Player's controls + state and applies input actions."""

    def __init__(self, player) -> None:
        self._p = player

    def _pressed(self, key_set: set[int], name):
        """key_set is usually input_frame.held or .pressed. An action with no
        binding in this fighter's control map is simply unpressable (#143: the
        move-selection seam reads "special", which some minimal control maps omit)
        — read defensively rather than KeyError."""
        code = self._p.controls.get(name)
        return code is not None and code in key_set

    # horizontal input movement
    def handle_move(self, keys):
        p = self._p
        # #967 slice 3: expose "the dash direction is still held" to the chart. True
        # while a horizontal press TOWARD current facing is held — the direction the
        # dash burst launched (facing == dash direction after `_start_dash`). The chart
        # cannot read the keyboard (it reads fighter STATE), so this is the input-derived
        # seam its dash->run / run-release transitions test. Computed before the speed
        # select below so the chart tick (later in Player.update) sees this frame's value.
        p.fighter.run_input_held = self._pressed(keys, "right" if p.fighter.facing_right else "left")
        # #967: while in the sustained `run` state, held movement is at `run_speed`;
        # otherwise #388's dash-burst speed (dash_timer > 0) or the walk speed.
        if p.state == "run":
            move_speed = p.fighter.run_speed
        elif p.fighter.dash_timer > 0:
            move_speed = p.fighter.dash_speed
        else:
            move_speed = p.fighter.move_speed
        p.fighter.vel, p.fighter.facing_right = step_horizontal(
            p.fighter.vel,
            p.fighter.facing_right,
            p.fighter.on_ground,
            self._pressed(keys, "left"),
            self._pressed(keys, "right"),
            locked=p.state
            in (
                "shield",
                "crouch",
                "helpless",
                "smash_charge",
            )  # no walking while shielding/crouching (#124), helpless (#184), or charging a smash (#327/3a)
            # A grounded normal roots the fighter (#898): `handle_actions` starts
            # the move, then this runs the SAME frame — held left/right must not
            # apply walk speed, or a forward-tilt slides ~10px instead of staying
            # planted. Friction still runs (step 1 of step_horizontal), so any
            # prior momentum bleeds off. Read `attack_timer` (set synchronously
            # when the clock starts) rather than the "attacking" state label,
            # which lags a frame and would miss the trigger frame. `on_ground`-
            # gated so airborne attacks keep their air drift.
            or (p.attack_timer > 0 and p.fighter.on_ground),
            move_speed=move_speed,  # walk / dash-burst / run, selected above (#388, #967)
        )

    def _maybe_start_dash(self, held, pressed):
        """Double-tap edge-detection (#388 slice 2b, #403).

        On a fresh single-direction press: a second same-direction press while
        `dash_input_window > 0` is a double-tap → `_start_dash`; otherwise the
        window is (re)armed to `DOUBLE_TAP_WINDOW` (it counts down in
        `Fighter.tick_timers`). Only an actionable, grounded idle/walk fighter
        dashes.

        Gated on the hitstun TIMERS, not just the `state` label (#370): the FSM
        label lags the hurt/stun timer by a frame, so a stale window must not
        dash the frame a hit lands. (The caller — `Player.update` — already skips
        `handle_actions` during hitstun; this guard keeps the seam correct if the
        detector is ever driven directly.) A held shield makes a directional
        press a dodge, not a dash, so shield-held taps are excluded."""
        p, f = self._p, self._p.fighter
        left = self._pressed(pressed, "left")
        right = self._pressed(pressed, "right")
        if left == right:  # neither pressed, or both: no directional edge
            return
        direction = 1 if right else -1
        if not (
            f.on_ground
            and f.dash_timer == 0
            and f.hurt_timer == 0
            and f.stun_timer == 0
            and not self._pressed(held, "shield")
            and p.state in ("idle", "walk")
        ):
            return
        if f.dash_input_window > 0 and f.dash_input_dir == direction:
            f._start_dash(direction)  # double-tap → burst
            f.dash_input_window = 0
            f.dash_input_dir = 0
        else:  # first tap (or a new direction): arm
            f.dash_input_window = DOUBLE_TAP_WINDOW
            f.dash_input_dir = direction

    def _smash_direction_and_angle(self, held):
        """Direction + f-smash angle for a smash (#327 slice 4). Unlike the normal
        token, the HORIZONTAL component wins over the vertical, so up/down is an
        f-smash ANGLE modifier rather than a u/d-smash: a forward/back smash with
        up/down held aims the swing. Pure vertical (no left/right) stays u/d-smash.
        Returns (direction, angle_dir) with angle_dir in {"up","down",None}."""
        p = self._p
        right = self._pressed(held, "right")
        left = self._pressed(held, "left")
        horiz = (right and not left) or (left and not right)
        if horiz:
            toward_facing = right if p.fighter.facing_right else left
            direction = "forward" if toward_facing else "back"
            angle_dir = "up" if self._pressed(held, "up") else "down" if self._pressed(held, "down") else None
            return direction, angle_dir
        # no horizontal -> pure vertical / neutral -> u/d-smash via the normal token
        return self._move_direction(held), None

    def _move_direction(self, held):
        """Direction token for move selection (#143) from held input + facing:
        neutral / up / down / forward (toward facing) / back (away). Precedence
        down > up > horizontal so down/up tilts+aerials win over f-tilt/f-air."""
        p = self._p
        if self._pressed(held, "down"):
            return "down"
        if self._pressed(held, "up"):
            return "up"
        right = self._pressed(held, "right")
        left = self._pressed(held, "left")
        if right and not left:
            return "forward" if p.fighter.facing_right else "back"
        if left and not right:
            return "back" if p.fighter.facing_right else "forward"
        return "neutral"

    # actions
    def handle_actions(self, input_frame, attack_group):
        p = self._p
        held = input_frame.held
        pressed = input_frame.pressed  # formerly prev_keys, refers to keys just freshly pressed this frame

        # ------- Smash charge (#327 slice 3a): hold to charge, release to fire ---
        # While a chargeable smash is being charged (pending_smash_key set, the
        # `smash_charge` state), accumulate the timer (capped) and fire on release
        # or at max. The fighter is rooted this frame (early return + handle_move
        # locks on the state). A mid-charge hit clears the charge via receive_hit
        # (input is gated during hitstun), so this block only runs while charging.
        f = p.fighter
        if f.pending_smash_key is not None:
            if f.smash_charge_timer < SMASH_CHARGE_FRAMES:
                f.smash_charge_timer += 1
            smash_held = self._pressed(held, "smash")
            if (not smash_held) or f.smash_charge_timer >= SMASH_CHARGE_FRAMES:
                # Capture the charge fraction for the slice-3b output scaling, then
                # start the swing on the move clock and drop the charge.
                f.smash_charge_fraction = f.smash_charge_timer / SMASH_CHARGE_FRAMES
                p._clock.start(p.fighter_data.moves[f.pending_smash_key])
                f.record_attack_made()
                f.cancel_smash_charge()
            return False  # rooted while charging; no other action this frame

        # ------- Double-tap dash (#388 slice 2b, #403) ------------
        # A fast double-tap of one direction fires the dash burst (_start_dash,
        # slice 2a). Reads `pressed` (fresh down-frames) — a held key is fresh
        # only once, so holding never double-taps and plain-hold stays walk
        # (golden-safe). Placed before the movement/attack branches; it only
        # (re)arms or starts a dash and never consumes the frame.
        self._maybe_start_dash(held, pressed)

        # ------- Jump ---------------------------------------------
        # Walking/falling off the ground forfeits the grounded jump — enforced by
        # the symmetric takeoff clamp in fighter_physics (Fighter._handle_takeoff),
        # not here (resolved #466 → #473). This branch only spends a jump on a press.
        jump_pressed = self._pressed(pressed, "up")
        atk_pressed = self._pressed(pressed, "attack")
        # up + special + a real `up_b` move = an up-special / recovery, not a jump —
        # divert the up press to the special block below (#578, B1 of #566). Fighters
        # without an `up_b` defined (e.g. the default cat) still jump on up+special, so
        # existing behavior / goldens are unchanged.
        wants_up_special = (
            self._pressed(pressed, "special") and self._move_direction(held) == "up" and "up_b" in p.fighter_data.moves
        )
        # A fresh Up + A resolves the ATTACK, not a jump (#878 / #865 Option D): let the
        # frame fall through to the Attack/Special seam below, where up + A becomes the
        # up-tilt (grounded) / up-air (airborne). One guard fixes both the grounded and
        # airborne cases because this branch is not `on_ground`-gated. Bare Up (no A)
        # still jumps / double-jumps. Scope is A (`attack`) only — Up + B (`wants_up_special`)
        # is unchanged. Shield is excluded so the frame keeps jumping out of shield: the
        # attack seam does not fire in shield, so yielding the jump there would drop the
        # frame instead of producing an attack.
        attack_wins_over_jump = atk_pressed and p.state not in ("shield", "dodge", "helpless")
        if (
            jump_pressed
            and not wants_up_special
            and not attack_wins_over_jump
            and p.fighter.jumps_remaining
            and p.state not in ("dodge", "hurt", "stun", "helpless")  # helpless locks jump (#184)
        ):
            p.fighter.vel.y = p.fighter.jump_vel
            p.fighter.jumps_remaining -= 1
            p.fighter.shield_attempting = False
            return False  # No dodge initiated

        # ------- Dodge Logic (check first to prevent shield conflicts) -------
        #### DONE: implement dodge as a combo press of directional + shield
        #### DONE: reset air_dodge_ok when landing
        #### TODO: implement directional flipping when ground dodging/rolling
        #### TODO: prevent repeated dodges by holding down shield and a directional, what
        # happens instead is that the player will enter a shield state, and then can press
        # a direction to dodge again
        #### DONE: make player rect flash semi-transparent white while in dodge state
        # Shield-plus-direction = dodge
        # "crouch" is dodge-able (#124): shield+down from a crouch spot-dodges,
        # preserving the #6 down-then-shield ordering now that down first crouches.
        can_dodge_state = p.state in ("idle", "jump", "fall", "shield", "crouch")
        # Special case: allow adding direction to neutral air dodges
        can_modify_air_dodge = (
            p.state == "dodge"
            and not p.fighter.on_ground
            and abs(p.fighter.vel.x) < _AIRDODGE_VEL_DEADZONE  # Currently has no horizontal velocity
            and p.fighter.dodge_timer > 0  # Still dodging
        )

        shield_down = self._pressed(held, "shield")
        shield_pressed = self._pressed(pressed, "shield")
        dodge_initiated = False

        if (can_dodge_state and p.fighter.dodge_timer == 0) or can_modify_air_dodge:
            dir_x = None
            dir_y = 0
            airborne = not p.fighter.on_ground
            down_input = self._pressed(pressed, "down") or self._pressed(held, "down")

            # Priority 1: Check for simultaneous shield + direction press (including spot dodge)
            # Issue #6: the spot-dodge direction may be *held* from an earlier
            # frame, not only freshly pressed — so pressing shield while down is
            # already held still spot-dodges (symmetric with the shield-held-then-
            # down path handled by Priority 3). Held left/right stay momentum/air
            # dodges via Priority 2; only the neutral spot dodge reads held-down.
            # Wavedash (#202): in the AIR, shield+down WITH a horizontal direction is
            # not a spot dodge but a diagonal-down air dodge — fall through to the
            # L/R branches (which set dir_y below). The ground spot dodge is unchanged.
            if (
                shield_pressed
                and down_input
                and not (airborne and (self._pressed(pressed, "left") or self._pressed(pressed, "right")))
            ):
                dir_x = 0  # spot dodge
            elif shield_pressed and self._pressed(pressed, "left"):
                dir_x = -1  # left dodge
            elif shield_pressed and self._pressed(pressed, "right"):
                dir_x = 1  # right dodge
            # Priority 2: Check if shield is *just* pressed for air dodge or momentum dodge
            elif shield_pressed and not can_modify_air_dodge:  # Don't allow shield-only during air dodge modification
                if not p.fighter.on_ground:
                    dir_x = 0  # air dodge without direction pressed
                elif abs(p.fighter.vel.x) > _AIRDODGE_VEL_DEADZONE:
                    dir_x = 1 if p.fighter.vel.x > 0 else -1
            # Priority 3: Check if a direction is freshly pressed while shield is held (ground dodge)
            # OR if direction is pressed during neutral air dodge
            elif shield_down or can_modify_air_dodge:
                if self._pressed(pressed, "down"):
                    dir_x = 0
                elif self._pressed(pressed, "left"):
                    dir_x = -1
                elif self._pressed(pressed, "right"):
                    dir_x = 1

            # Wavedash (#202): a directional air dodge with down also input bursts
            # diagonally DOWN (dir_y=1) instead of flat — drives into the ground for a
            # waveland. Only meaningful for a fresh airborne directional dodge.
            if dir_x is not None and dir_x != 0 and airborne and down_input:
                dir_y = 1

            if dir_x is not None:
                if can_modify_air_dodge:
                    # Special case: modifying existing air dodge
                    if dir_x != 0:  # Only allow directional modification, not neutral
                        p.fighter.vel.x = (dir_x * DODGE_SPEED) + p.fighter.vel.x
                        dodge_initiated = True
                elif p.fighter.on_ground or p.fighter.air_dodge_ok:
                    p.fighter._start_dodge(dir_x, dir_y)
                    dodge_initiated = True
                    if not p.fighter.on_ground:
                        p.fighter.air_dodge_ok = False
                return True  # Dodge initiated, no further actions needed

        # ------- Shield -------------------------------------------
        # 2.  Shield can **only** be (re)started while on ground and not airborne
        # Don't enter shield state if we just initiated a dodge
        grounded_can_shield = (
            p.fighter.on_ground
            and p.state in ("idle", "shield", "dodge", "walk")
            and p.fighter.dodge_timer == 0
            and not dodge_initiated  # Don't shield if we just started dodging
        )

        if self._pressed(held, "shield") and grounded_can_shield:
            #### TODO: prevent entering of shield state when falling/jumping, when in hurt state, etc.
            p.fighter.shield_attempting = True
        else:
            # Don't reset shield_attempting if we just initiated a dodge or are currently dodging
            if not dodge_initiated and p.state != "dodge":
                p.fighter.shield_attempting = False

        # ------- Attack / Special (move-selection seam #143) ------
        #### TODO: implement attack buffering, that attacks can be chained
        # `atk_pressed` was computed above (jump-branch guard, #878).
        sp_pressed = self._pressed(pressed, "special")
        # Smash (#331, slice 1 of #327): a dedicated input, ground-only. Takes
        # precedence over attack/special the frame it's pressed; smash-in-air alone
        # is a no-op this slice (no air-smash). `_pressed` is binding-tolerant, so
        # control maps without "smash" (the sim keymaps) simply never smash.
        ground_smash = self._pressed(pressed, "smash") and p.fighter.on_ground
        # Hard-drop a mid-move re-press (#1087, ruling #1079 Q2): while a move is
        # already running (`current_move is not None`), ignore Attack/Special/ground-
        # smash — no `MoveClock.start()`, so the running move is NOT restarted to
        # frame 0. No early-out/IASA window in V1: pycats keeps its no-IASA commitment
        # model, and PM 3.6 is faithful to the drop (no default input buffer — a
        # mid-move press is dropped, not buffered to IASA; research #1093,
        # docs/research/pm-input-buffer-findings.md). IASA-aware interrupt is post-V1
        # (#1089). The `smash_charge` fire path returns above and never reaches here,
        # and during a charge no move clock is active, so charging is unaffected.
        if (
            (atk_pressed or sp_pressed or ground_smash)
            and p.state not in ("shield", "dodge", "helpless")
            and p.current_move is None
        ):
            # Map (direction × ground/air × A-vs-B-vs-smash) -> a move key, falling
            # back to whatever the character defines (#143). Data-driven (Task 4 /
            # #71): start the move clock; the hitbox spawns later in update() when
            # the active window opens. Partial kits (default cat = {"attack"}, Nalio
            # = full normals) resolve to the same moves as before, so the golden sims
            # are unchanged; B with no special is a no-op, and a smash with no
            # smash-key falls back to the tilt (move_select).
            is_smash = ground_smash
            is_special = sp_pressed and not atk_pressed and not ground_smash
            # Smashes use horizontal-wins direction + an f-smash angle (#327/4);
            # attacks/specials use the normal token.
            if is_smash:
                direction, angle_dir = self._smash_direction_and_angle(held)
            else:
                direction, angle_dir = self._move_direction(held), None
            key = resolve_move_key(p.fighter_data.moves, direction, p.fighter.on_ground, is_special, is_smash)
            if key is not None:
                move = p.fighter_data.moves[key]
                # Capture the aimed angle only when the smash resolves to a real
                # fsmash (a u/d-smash or a tilt fallback clears it).
                p.fighter.smash_angle_dir = angle_dir if key == "fsmash" else None
                if is_smash and move.chargeable:
                    # Chargeable smash (#327/3a): begin charging instead of firing —
                    # the swing starts on release/max (the charge block above). A
                    # smash that fell back to a tilt (not chargeable) fires normally.
                    p.fighter.smash_charge_timer = 0
                    p.fighter.pending_smash_key = key
                    p.engine.force("smash_charge")
                else:
                    p._clock.start(move)
                    p.fighter.record_attack_made()  # Track attack statistics
                    # (#321/F3: done_attacking is derived (attack_timer == 0); starting
                    #  the clock above makes it False — no flag to set.)
                    # Special-recovery / up-B (#578, B1 of #566): a recovery move SETS
                    # an upward burst on start and arms `recovery_active`, so the move's
                    # airborne exit routes to `helpless` (#184). Set the flag on EVERY
                    # start (False for a normal move) so it never goes stale.
                    p.fighter.recovery_active = move.grants_recovery
                    if move.grants_recovery:
                        facing = 1 if p.fighter.facing_right else -1
                        p.fighter.vel.y = move.recovery_vy
                        p.fighter.vel.x = move.recovery_vx * facing
                    # Landing shockwave (#974, B-cluster of #566): a move that declares
                    # a `landing_spawn` (Final Cutter's ground beam) stashes its
                    # descriptor now — the spawn fires on the eventual touchdown, by
                    # which point the move has ended (current_move is None). Stashed on
                    # EVERY start (None for a normal move) so it never goes stale.
                    p._pending_landing_spawn = move.landing_spawn
            elif is_special:
                # Not-yet-implemented: an input mapped to a move the fighter does not
                # define (an undefined special resolves to None — specials have no
                # fallback). Silent no-op in play; leave a dev breadcrumb (#587). The
                # logger is OFF unless PYCATS_DEV_LOG is set, so the sim/golden path
                # does zero file I/O and stays byte-identical.
                dev_log.log_unimplemented(
                    p.char_name,
                    select_move_key(direction, p.fighter.on_ground, is_special=True),
                    f"{direction}+special",
                    [
                        "combat/move_select.py",
                        "entities/fighter_input.py",
                        f"characters/{p.char_name.lower()}_cat.py",
                    ],
                )
        #### TODO: implement grab from shield state or combo press of attack + shield from idle/walk state

        # e.g. disappearing ranged attack (vanish immediately on hit) like fireballs
        # attack_group.add(Attack(self, disappear_on_hit=True))

        return False  # No dodge initiated
