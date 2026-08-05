"""
Time-driven self-heal system — ROUNDS v1 Health Regen consumer (#1218).

The Health Regen card (ADR-0019 §3) heals its owner a fixed chunk every N frames.
Unlike Vampire's on-hit lifesteal (event-driven, `hit_resolution.process_hits`,
DEV 5), Health Regen is *time*-driven: it triggers on elapsed frames, not on a hit
event — so it gets its own per-frame hook, a sibling of `systems/win_condition.py`.

Reads the #1208 knob-fields only (`FighterData.regen_rate` / `regen_interval`) and
heals by LOWERING the owner's `percent` (the `entities/fighter.py` setter floors it
at 0). A fighter with `regen_interval == 0` is off — skipped with no divide/modulo,
so every existing cat and the default sim are byte-identical (no cat carries a regen
card). Magnitudes (interval N + heal chunk) stay tunable (#1156), not fixed here.

Tick slot: called in the runner's per-fighter `p.update` pass, BEFORE `process_hits`
and before `snapshot` (#1173 Q4 Option A — engine-faithful, meleelight-confirmed
order). The per-fighter frame counter is transient runtime state on the Fighter
(`fighter.regen_counter`), like the other per-fighter timers.
"""

from __future__ import annotations


def tick(players) -> None:
    """Advance each fighter's regen counter; heal the owner every `regen_interval` frames.

    For each player whose `fighter_data.regen_interval > 0`, increment the fighter's
    `regen_counter`; when it reaches the interval, reset it and heal the owner by
    `regen_rate` (percent), i.e. `percent -= regen_rate` — the percent setter floors
    the result at 0. A fighter with `regen_interval == 0` is off and is skipped (no
    modulo/divide, no heal). Owner-only: a fighter's regen only touches its own percent.
    """
    for p in players:
        interval = p.fighter_data.regen_interval
        if interval <= 0:
            continue  # off — no regen card (default), no divide/modulo, no heal
        fighter = p.fighter
        fighter.regen_counter += 1
        if fighter.regen_counter >= interval:
            fighter.regen_counter = 0
            fighter.percent = fighter.percent - p.fighter_data.regen_rate
