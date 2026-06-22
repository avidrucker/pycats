"""Hierarchical + parallel fighter statechart (behavior-equivalent to the
flat chart / Player._build_fsm).

Structure (Task 3 of PM Phase 0):

    root  (parallel)
    ├── action  (compound, initial=idle)   <- force_ko / force_idle hoisted here
    │   ├── actionable  (compound, initial=idle)
    │   │   ├── grounded  (compound, initial=idle)
    │   │   │   ├── idle    (leaf)
    │   │   │   ├── run     (leaf)
    │   │   │   └── shield  (leaf)
    │   │   └── airborne  (compound, initial=jump)
    │   │       ├── jump    (leaf)
    │   │       └── fall    (leaf)
    │   ├── attacking  (compound, initial=attack)
    │   │   └── attack   (leaf)            <- SINGLE leaf in Task 3 (split in Task 4)
    │   ├── dodging    (compound, initial=dodge)
    │   │   └── dodge    (leaf)
    │   ├── hitstun    (compound, initial=hurt)
    │   │   ├── hurt    (leaf)
    │   │   └── stun    (leaf)             <- preserved-but-unreachable quirk
    │   └── ko          (leaf)
    └── defensive_status  (compound, initial=vulnerable)
        ├── vulnerable   (leaf)
        └── intangible   (leaf)

LEAF ids equal the flat labels (idle, run, jump, fall, shield, dodge, ko, hurt,
stun, attack) so in_state("idle") etc. keep working. Compound/grouping ids
(action, actionable, grounded, airborne, attacking, dodging, hitstun, root,
defensive_status) are distinct and never collide with leaf labels.

Every tick transition fires on the explicit "tick" event (no eventless
transitions): one send("tick") performs at most one hop, matching the legacy
FSM's break-after-first behavior.

Transition selection note (SCXML / statecharts-py): for each active atomic
state the engine scans the leaf's transitions first (in document order), then
climbs to ancestors only if none matched. So leaf transitions take priority
over hoisted parent transitions. Because the legacy per-leaf transition
ORDERING differs between leaves (e.g. idle/run check attack+dodge first, but
fall checks idle/run/jump/ko before dodge), the tick transitions are kept on
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
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.vel.x != 0 and p.on_ground, "run"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.on_ground and p.vel.y > 0, "fall"),
            _tick(lambda e, d: p.shield_attempting, "shield"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
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
        ),
        state(
            {"id": "shield"},
            _tick(lambda e, d: not p.shield_attempting, "idle"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
        ),
    )

    airborne = state(
        {"id": "airborne", "initial": "jump"},
        state(
            {"id": "jump"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.vel.y >= 0, "fall"),
            _tick(lambda e, d: not p.is_alive, "ko"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
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
        ),
    )

    actionable = state(
        {"id": "actionable", "initial": "idle"},
        grounded,
        airborne,
    )

    attacking = state(
        {"id": "attacking", "initial": "attack"},
        state(
            {"id": "attack"},
            _tick(lambda e, d: p.done_attacking and p.on_ground, "idle"),
            _tick(lambda e, d: p.done_attacking and not p.on_ground, "fall"),
        ),
    )

    dodging = state(
        {"id": "dodging", "initial": "dodge"},
        state(
            {"id": "dodge"},
            _tick(lambda e, d: p.shield_attempting and p.dodge_timer <= 0
                  and p.on_ground, "shield"),
            _tick(lambda e, d: not p.shield_attempting and p.dodge_timer <= 0
                  and p.on_ground and not p.spot_dodge_shield_held, "idle"),
            _tick(lambda e, d: p.dodge_timer <= 0 and not p.on_ground, "fall"),
        ),
    )

    hitstun = state(
        {"id": "hitstun", "initial": "hurt"},
        state(
            {"id": "hurt"},
            _tick(lambda e, d: p.hurt_timer <= 0 and p.on_ground, "idle"),
            _tick(lambda e, d: p.hurt_timer <= 0 and not p.on_ground, "fall"),
        ),
        state(
            {"id": "stun"},
            _tick(lambda e, d: p.stun_timer <= 0 and p.on_ground, "idle"),
            _tick(lambda e, d: p.stun_timer <= 0 and not p.on_ground, "fall"),
        ),
    )

    ko = state(
        {"id": "ko"},
        _tick(lambda e, d: p.is_alive, "idle"),
    )

    action = state(
        {"id": "action", "initial": "idle"},
        # force_ko / force_idle hoisted to the action parent: they fire on
        # distinct events, so they never reorder the per-leaf tick transitions.
        on("force_ko", "ko"),
        on("force_idle", "idle"),
        actionable,
        attacking,
        dodging,
        hitstun,
        ko,
    )

    defensive_status = state(
        {"id": "defensive_status", "initial": "vulnerable"},
        state(
            {"id": "vulnerable"},
            _tick(lambda e, d: p.invulnerable, "intangible"),
        ),
        state(
            {"id": "intangible"},
            _tick(lambda e, d: not p.invulnerable, "vulnerable"),
        ),
    )

    return statechart(
        {"initial": "root"},
        parallel({"id": "root"}, action, defensive_status),
    )
