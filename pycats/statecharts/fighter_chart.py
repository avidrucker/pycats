"""Flat statechart mirroring Player._build_fsm() exactly.

Every transition fires on the explicit "tick" event (no eventless transitions),
so one send("tick") performs at most one hop — matching the legacy FSM's
break-after-first behavior. Guards close over the live Player. Each state also
carries force_ko / force_idle transitions for imperative jumps (Player._ko and
reset_game).
"""
from __future__ import annotations

from statecharts import on, state, statechart, transition


def _tick(cond, target):
    return transition({"event": "tick", "cond": cond, "target": target})


def build_fighter_chart(p):
    """p is the owning Player; guards read its live attributes."""
    forces = (on("force_ko", "ko"), on("force_idle", "idle"))

    return statechart(
        {"initial": "idle"},
        state(
            {"id": "idle"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.vel.x != 0 and p.on_ground, "run"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.on_ground and p.vel.y > 0, "fall"),
            _tick(lambda e, d: p.shield_attempting, "shield"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
            *forces,
        ),
        state(
            {"id": "run"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.vel.x == 0, "idle"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.on_ground and p.vel.y > 0, "fall"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
            _tick(lambda e, d: p.shield_attempting and p.on_ground, "shield"),
            *forces,
        ),
        state(
            {"id": "jump"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.vel.y >= 0, "fall"),
            _tick(lambda e, d: not p.is_alive, "ko"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
            *forces,
        ),
        state(
            {"id": "fall"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.on_ground and p.vel.x == 0, "idle"),
            _tick(lambda e, d: p.on_ground and p.vel.x != 0, "run"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.is_alive, "ko"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
            *forces,
        ),
        state(
            {"id": "shield"},
            _tick(lambda e, d: not p.shield_attempting, "idle"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            *forces,
        ),
        state(
            {"id": "ko"},
            _tick(lambda e, d: p.is_alive, "idle"),
            *forces,
        ),
        state(
            {"id": "dodge"},
            _tick(lambda e, d: p.shield_attempting and p.dodge_timer <= 0
                  and p.on_ground, "shield"),
            _tick(lambda e, d: not p.shield_attempting and p.dodge_timer <= 0
                  and p.on_ground and not p.spot_dodge_shield_held, "idle"),
            _tick(lambda e, d: p.dodge_timer <= 0 and not p.on_ground, "fall"),
            *forces,
        ),
        state(
            {"id": "hurt"},
            _tick(lambda e, d: p.hurt_timer <= 0 and p.on_ground, "idle"),
            _tick(lambda e, d: p.hurt_timer <= 0 and not p.on_ground, "fall"),
            *forces,
        ),
        state(
            {"id": "stun"},
            _tick(lambda e, d: p.stun_timer <= 0 and p.on_ground, "idle"),
            _tick(lambda e, d: p.stun_timer <= 0 and not p.on_ground, "fall"),
            *forces,
        ),
        state(
            {"id": "attack"},
            _tick(lambda e, d: p.done_attacking and p.on_ground, "idle"),
            _tick(lambda e, d: p.done_attacking and not p.on_ground, "fall"),
            *forces,
        ),
    )
