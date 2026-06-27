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

from ..config import DODGE_SPEED
from ..systems.movement import step_horizontal


class FighterInput:
    """Reads the owning Player's controls + state and applies input actions."""

    def __init__(self, player) -> None:
        self._p = player

    def _pressed(self, key_set: set[int], name):
        """key_set is usually input_frame.held or .pressed."""
        return self._p.controls[name] in key_set

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
            == "shield",  # prevents moving while shielding, this may need to change when dodging is implemented
            move_speed=p.fighter.move_speed,
        )

    # actions
    def handle_actions(self, input_frame, attack_group):
        p = self._p
        held = input_frame.held
        pressed = (
            input_frame.pressed
        )  # formerly prev_keys, refers to keys just freshly pressed this frame

        # ------- Jump ---------------------------------------------
        jump_pressed = self._pressed(pressed, "up")
        #### TODO: determine whether walking off of a ledge "consumes" a jump
        if (
            jump_pressed
            and p.fighter.jumps_remaining
            and p.state not in ("dodge", "hurt", "stun")
        ):
            p.fighter.vel.y = p.fighter.jump_vel
            p.fighter.jumps_remaining -= 1
            p.fighter.shield_attempting = False
            return False  # No dodge initiated

        # ------- Dodge Logic (check first to prevent shield conflicts) -------
        #### DONE: implement dodge as a combo press of directional + shield
        #### DONE: reset air_dodge_ok when landing
        #### TODO: implement directional flipping when ground dodging/rolling
        #### TODO: prevent repeated dodges by holding down shield and a directional, what happens instead is that the player will enter a shield state, and then can press a direction to dodge again
        #### DONE: make player rect flash semi-transparent white while in dodge state
        # Shield-plus-direction = dodge
        can_dodge_state = p.state in ("idle", "jump", "fall", "shield")
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

            # Priority 1: Check for simultaneous shield + direction press (including spot dodge)
            # Issue #6: the spot-dodge direction may be *held* from an earlier
            # frame, not only freshly pressed — so pressing shield while down is
            # already held still spot-dodges (symmetric with the shield-held-then-
            # down path handled by Priority 3). Held left/right stay momentum/air
            # dodges via Priority 2; only the neutral spot dodge reads held-down.
            if shield_pressed and (self._pressed(pressed, "down")
                                   or self._pressed(held, "down")):
                dir_x = 0  # spot dodge
            elif shield_pressed and self._pressed(pressed, "left"):
                dir_x = -1  # left dodge
            elif shield_pressed and self._pressed(pressed, "right"):
                dir_x = 1  # right dodge
            # Priority 2: Check if shield is *just* pressed for air dodge or momentum dodge
            elif (
                shield_pressed and not can_modify_air_dodge
            ):  # Don't allow shield-only during air dodge modification
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

            if dir_x is not None:
                if can_modify_air_dodge:
                    # Special case: modifying existing air dodge
                    if dir_x != 0:  # Only allow directional modification, not neutral
                        p.fighter.vel.x = (dir_x * DODGE_SPEED) + p.fighter.vel.x
                        dodge_initiated = True
                elif p.fighter.on_ground or p.fighter.air_dodge_ok:
                    p.fighter._start_dodge(dir_x)
                    dodge_initiated = True
                    if not p.fighter.on_ground:
                        p.fighter.air_dodge_ok = False
                return True  # Dodge initiated, no further actions needed

        # ------- Shield -------------------------------------------
        # 2.  Shield can **only** be (re)started while on ground and not airborne
        # Don't enter shield state if we just initiated a dodge
        grounded_can_shield = (
            p.fighter.on_ground
            and p.state in ("idle", "shield", "dodge", "run")
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

        # ------- Attack -------------------------------------------
        #### TODO: implement attack buffering, that attacks can be chained
        atk_pressed = self._pressed(pressed, "attack")
        if atk_pressed and p.state not in ("shield", "dodge"):
            # Data-driven attack (Task 4 / #71): start the move clock instead of
            # spawning the hitbox immediately. The hitbox is spawned later, in
            # update(), once the active window opens. done_attacking is kept so
            # the legacy FSM and the chart's attack-exit guard classify/exit at
            # the same total frame (attack_timer is now p._clock.remaining).
            p._clock.start(p.fighter_data.moves["attack"])
            p.fighter.record_attack_made()  # Track attack statistics
            p.fighter.done_attacking = False  # set to false when attack starts, set true when done
            #### TODO: implement unique custom attacks for each player w/ variable damage, knockback, and angle, attack activation time, attack duration, etc.
        #### TODO: implement grab from shield state or combo press of attack + shield from idle/run state

        # e.g. disappearing ranged attack (vanish immediately on hit) like fireballs
        # attack_group.add(Attack(self, disappear_on_hit=True))

        return False  # No dodge initiated
