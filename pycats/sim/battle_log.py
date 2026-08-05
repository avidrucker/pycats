# pycats/sim/battle_log.py
"""Battle event-log — a 'git-diff for the fight' derived from snapshots (#302/#300).

Pure post-processing of the per-frame `snapshot()` list `run_battle` returns: diff
consecutive snapshots and emit a chronological event whenever something significant
changes (jumps, attacks, hits, KOs, notable state transitions, match end). It touches
nothing in the sim, so it is golden-safe by construction and works on any recorded or
replayed (seeded, #166) run.

snapshot() shapes (see runner.snapshot):
    part   = (name, state, x, y, vx, vy, on_ground, percent, shield_hp, lives,
              is_alive, jumps_remaining, ...)            # indices below
    attack = (x, y, frames_left, owner_name, active, hit_cx, hit_cy, hit_r)
    snap   = (parts, attacks, phase, winner)
"""

from __future__ import annotations

from collections import Counter, namedtuple

BattleEvent = namedtuple("BattleEvent", ["frame", "actor", "type", "detail"])

# Event-type constants.
JUMP = "JUMP"
ATTACK = "ATTACK"
HIT = "HIT"
KO = "KO"
STATE = "STATE"
MATCH_END = "MATCH_END"

# Part-tuple indices we read.
_NAME, _STATE, _PERCENT, _LIVES, _JUMPS = 0, 1, 7, 9, 11
# Attack-tuple indices.
_ATK_OWNER, _ATK_ACTIVE = 3, 4

# State transitions worth logging (into these); transitions into run/idle/etc. are not.
NOTABLE_STATES = frozenset({"ko", "hurt", "helpless", "dizzy", "shield", "dodge"})


def _active_owner_counts(snap) -> Counter:
    return Counter(a[_ATK_OWNER] for a in snap[1] if a[_ATK_ACTIVE])


def events_from_snaps(snaps) -> list[BattleEvent]:
    """Diff consecutive snapshots into a chronological list of BattleEvents.

    Per frame the events are emitted in a stable order: ATTACK(s) (by owner), then
    each fighter in index order with sub-order JUMP -> HIT -> KO -> STATE, then
    MATCH_END. That ordering is part of the contract."""
    events: list[BattleEvent] = []
    for f in range(1, len(snaps)):
        cur, prev = snaps[f], snaps[f - 1]

        # ATTACK: an owner's count of *active* attacks increased this frame.
        cur_owners = _active_owner_counts(cur)
        prev_owners = _active_owner_counts(prev)
        for owner in sorted(cur_owners):
            if cur_owners[owner] > prev_owners.get(owner, 0):
                events.append(BattleEvent(f, owner, ATTACK, {}))
        active_owners = list(cur_owners)  # for HIT attribution

        # Per-fighter diffs, in index order.
        for i in range(len(cur[0])):
            a, b = cur[0][i], prev[0][i]
            name = a[_NAME]
            if a[_JUMPS] < b[_JUMPS]:
                events.append(BattleEvent(f, name, JUMP, {"remaining": a[_JUMPS]}))
            if a[_PERCENT] > b[_PERCENT] + 1e-9:
                by = next((o for o in active_owners if o != name), None)
                events.append(
                    BattleEvent(
                        f,
                        name,
                        HIT,
                        {
                            "damage": round(a[_PERCENT] - b[_PERCENT], 6),
                            "from": b[_PERCENT],
                            "to": a[_PERCENT],
                            "by": by,
                        },
                    )
                )
            if a[_LIVES] < b[_LIVES]:
                events.append(
                    BattleEvent(
                        f,
                        name,
                        KO,
                        {
                            "stock_from": b[_LIVES],
                            "stock_to": a[_LIVES],
                            "percent": b[_PERCENT],
                        },
                    )
                )
            if a[_STATE] != b[_STATE] and a[_STATE] in NOTABLE_STATES:
                events.append(BattleEvent(f, name, STATE, {"from": b[_STATE], "to": a[_STATE]}))

        # MATCH_END: the winner resolved this frame.
        if cur[3] is not None and prev[3] is None:
            events.append(BattleEvent(f, "MATCH", MATCH_END, {"winner": cur[3]}))
    return events


def _detail_text(e: BattleEvent) -> str:
    d = e.detail
    if e.type == JUMP:
        return f"({d['remaining']} left)"
    if e.type == HIT:
        base = f"+{d['damage']:.0f}% ({d['from']:.0f}->{d['to']:.0f})"
        return base + (f" by {d['by']}" if d.get("by") else "")
    if e.type == KO:
        return f"stock {d['stock_from']}->{d['stock_to']} @{d['percent']:.0f}%"
    if e.type == STATE:
        return f"-> {d['to']}"
    if e.type == MATCH_END:
        return f"winner={d['winner']}"
    return ""  # ATTACK


def render(events) -> str:
    """One readable 'diff' line per event."""
    lines = []
    for e in events:
        lines.append(f"{e.frame:>6}  {e.actor:<6} {e.type:<9} {_detail_text(e)}".rstrip())
    return "\n".join(lines)
