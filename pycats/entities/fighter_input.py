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

from ..combat.move_select import resolve_move_key
from ..config import DODGE_SPEED, DOUBLE_TAP_WINDOW, SMASH_CHARGE_FRAMES
from ..systems.movement import step_horizontal


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
            ),  # no walking while shielding/crouching (#124), helpless (#184), or charging a smash (#327/3a)
            # #388 (slice 2a): during the initial-dash burst, held movement is at
            # `dash_speed`, not walk speed. dash_timer is 0 in the default path, so
            # this is walk speed everywhere until slice 2b's double-tap starts a dash.
            move_speed=(p.fighter.dash_speed if p.fighter.dash_timer > 0 else p.fighter.move_speed),
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
        if (
            jump_pressed
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
            and abs(p.fighter.vel.x) < 0.1  # Currently has no horizontal velocity
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
                elif abs(p.fighter.vel.x) > 0.1:
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
        atk_pressed = self._pressed(pressed, "attack")
        sp_pressed = self._pressed(pressed, "special")
        # Smash (#331, slice 1 of #327): a dedicated input, ground-only. Takes
        # precedence over attack/special the frame it's pressed; smash-in-air alone
        # is a no-op this slice (no air-smash). `_pressed` is binding-tolerant, so
        # control maps without "smash" (the sim keymaps) simply never smash.
        ground_smash = self._pressed(pressed, "smash") and p.fighter.on_ground
        if (atk_pressed or sp_pressed or ground_smash) and p.state not in ("shield", "dodge", "helpless"):
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
        #### TODO: implement grab from shield state or combo press of attack + shield from idle/walk state

        # e.g. disappearing ranged attack (vanish immediately on hit) like fireballs
        # attack_group.add(Attack(self, disappear_on_hit=True))

        return False  # No dodge initiated
