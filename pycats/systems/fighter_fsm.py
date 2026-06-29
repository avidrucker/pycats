"""Legacy flat fighter FSM table (behavior-equivalent to the hierarchical
statechart in charts/fighter_chart.py).

This is the data/closure twin of `build_fighter_chart(p)`: the same per-state
transition guards, expressed as the hand-rolled `FSM`/`Transition` table the
`LegacyEngine` consumes. Extracted from `Player._build_fsm` (D1 slice 5, #79) so
the table lives in `systems/` alongside the engine that runs it, mirroring how
the statechart already lives outside the entity.

Guards are closures over the owning `player`; they read its live attributes each
tick. Transition ORDER within a state is significant — it encodes priority
(first matching transition wins, break-after-first) and is kept verbatim to
guarantee byte-identical parity with the statechart (see fighter_chart.py's
"Transition selection note").
"""
from __future__ import annotations

from .fsm import FSM, Transition


def build_fighter_fsm(player) -> FSM:
    """player is the owning Player; guards read its live attributes."""
    return FSM(
        state="idle",
        table={
            "idle": [
                Transition("attack", lambda f, ctx: player.attack_timer > 0),
                Transition(
                    "dodge", lambda f, ctx: player.fighter.dodge_timer > 0
                ),  # Dodge should take priority
                Transition(
                    "crouch",
                    lambda f, ctx: player.fighter.crouch_attempting and player.fighter.on_ground,
                ),
                Transition(
                    "run", lambda f, ctx: player.fighter.vel.x != 0 and player.fighter.on_ground
                ),
                Transition("jump", lambda f, ctx: player.fighter.vel.y < 0),
                Transition(
                    "fall", lambda f, ctx: not player.fighter.on_ground and player.fighter.vel.y > 0
                ),
                Transition("shield", lambda f, ctx: player.fighter.shield_attempting),
                Transition("hurt", lambda f, ctx: player.fighter.hurt_timer > 0),
            ],
            "run": [
                Transition("attack", lambda f, ctx: player.attack_timer > 0),
                Transition(
                    "dodge", lambda f, ctx: player.fighter.dodge_timer > 0
                ),  # Dodge should take priority
                Transition(
                    "crouch",
                    lambda f, ctx: player.fighter.crouch_attempting and player.fighter.on_ground,
                ),
                Transition("idle", lambda f, ctx: player.fighter.vel.x == 0),
                Transition("jump", lambda f, ctx: player.fighter.vel.y < 0),
                Transition(
                    "fall", lambda f, ctx: not player.fighter.on_ground and player.fighter.vel.y > 0
                ),
                Transition("hurt", lambda f, ctx: player.fighter.hurt_timer > 0),
                Transition(
                    "shield",
                    lambda f, ctx: player.fighter.shield_attempting and player.fighter.on_ground,
                ),  # can enter shield state while running on the ground
            ],
            # Crouch (#124): hold down on solid ground; mirrors the statechart
            # crouch leaf transition order exactly (parity).
            "crouch": [
                Transition("attack", lambda f, ctx: player.attack_timer > 0),
                Transition("dodge", lambda f, ctx: player.fighter.dodge_timer > 0),
                Transition("jump", lambda f, ctx: player.fighter.vel.y < 0),
                Transition("hurt", lambda f, ctx: player.fighter.hurt_timer > 0),
                Transition("fall", lambda f, ctx: not player.fighter.on_ground),
                Transition("idle", lambda f, ctx: not player.fighter.crouch_attempting),
            ],
            "jump": [
                Transition("attack", lambda f, ctx: player.attack_timer > 0),
                Transition("fall", lambda f, ctx: player.fighter.vel.y >= 0),
                Transition("ko", lambda f, ctx: not player.fighter.is_alive),
                Transition("dodge", lambda f, ctx: player.fighter.dodge_timer > 0),
                Transition("hurt", lambda f, ctx: player.fighter.hurt_timer > 0),
            ],
            "fall": [
                Transition("attack", lambda f, ctx: player.attack_timer > 0),
                Transition(
                    "idle", lambda f, ctx: player.fighter.on_ground and player.fighter.vel.x == 0
                ),
                Transition(
                    "run", lambda f, ctx: player.fighter.on_ground and player.fighter.vel.x != 0
                ),
                Transition("jump", lambda f, ctx: player.fighter.vel.y < 0),
                Transition("ko", lambda f, ctx: not player.fighter.is_alive),
                Transition("dodge", lambda f, ctx: player.fighter.dodge_timer > 0),
                Transition("hurt", lambda f, ctx: player.fighter.hurt_timer > 0),
            ],
            "shield": [
                # Shield-break stun (#12) takes priority: a depleted shield calls
                # _start_stun (stun_timer > 0) and the fighter is dizzy regardless
                # of whether shield is still held.
                Transition("stun", lambda f, ctx: player.fighter.stun_timer > 0),
                Transition("idle", lambda f, ctx: not player.fighter.shield_attempting),
                Transition("dodge", lambda f, ctx: player.fighter.dodge_timer > 0),
                Transition("jump", lambda f, ctx: player.fighter.vel.y < 0),
                #### TODO: grab: attacking while shielding leads to grabbing state
                #### TODO: held: being grabbed by an opponent leads to held state
            ],
            "ko": [Transition("idle", lambda f, ctx: player.fighter.is_alive)],
            "dodge": [
                Transition(
                    "shield",
                    lambda f, ctx: player.fighter.shield_attempting
                    and player.fighter.dodge_timer <= 0
                    and player.fighter.on_ground,
                ),  # can re-enter shield state after dodging on the ground
                Transition(
                    "idle",
                    lambda f, ctx: not player.fighter.shield_attempting
                    and player.fighter.dodge_timer <= 0
                    and player.fighter.on_ground
                    and not player.fighter.spot_dodge_shield_held,  # Don't go to idle if spot dodge shield is held
                ),  #  and player.fighter.vel.x == 0
                Transition(
                    "fall",
                    lambda f, ctx: player.fighter.dodge_timer <= 0 and not player.fighter.on_ground,
                ),  # and player.fighter.vel.y > 0
            ],
            #### hurt: hit by an attack, unable to move or attack for a short time
            "hurt": [
                Transition(
                    "idle", lambda f, ctx: player.fighter.hurt_timer <= 0 and player.fighter.on_ground
                ),
                Transition(
                    "fall",
                    lambda f, ctx: player.fighter.hurt_timer <= 0 and not player.fighter.on_ground,
                ),
                #### TODO: implement shield holding to transition from hurt to shield state
            ],
            "stun": [
                Transition(
                    "idle", lambda f, ctx: player.fighter.stun_timer <= 0 and player.fighter.on_ground
                ),
                Transition(
                    "fall",
                    lambda f, ctx: player.fighter.stun_timer <= 0 and not player.fighter.on_ground,
                ),
            ],
            # Prone / knockdown (#13): force-entry only (no natural trigger yet;
            # landing-velocity is #145). The only self-initiated action is standing
            # up, expressed as the getup window: prone_timer counts to 0 -> stand.
            # Mirrors the statechart prone leaf transition order exactly (parity).
            "prone": [
                Transition(
                    "idle", lambda f, ctx: player.fighter.prone_timer <= 0 and player.fighter.on_ground
                ),
                Transition(
                    "fall",
                    lambda f, ctx: player.fighter.prone_timer <= 0 and not player.fighter.on_ground,
                ),
            ],
            "attack": [
                Transition(
                    "idle", lambda f, ctx: player.fighter.done_attacking and player.fighter.on_ground
                ),
                Transition(
                    "fall",
                    lambda f, ctx: player.fighter.done_attacking and not player.fighter.on_ground,
                ),
            ],
            #### TODO: hang: hanging on the ledge
        },
    )
