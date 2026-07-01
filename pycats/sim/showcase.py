# pycats/sim/showcase.py
"""The curated Nalio-vs-Birky feature-showcase demo (#325, final child of #308).

A deterministic scripted battle whose captioned `DemoSegment`s each demonstrate an
implemented feature. Built on the `DEFAULT_SCRIPT`/`COMBAT_SCRIPT` choreography template
(input_script.py): the opening movement + jabs + the knockback hit-chain come from that
proven positioning (nalio's jab is a disjoint that only connects at its ~48px sweet-spot,
which those scripts are tuned to), then two authored beats add the roll-dodge and the
ledge-grab-into-blast-zone finish.

Coverage is asserted by `tests/test_showcase_demo.py` via the derived event-log + the
visited fighter-state set. **Shield-break stun is intentionally NOT covered here** — see
that ticket's finding: a fixed script can't reliably break a held shield (the opponent's
jab whiffs on the shield bubble, so it only drains passively, which does not trigger the
hit-driven break).

Play / record it:
    watch.py --demo showcase              # live
    watch.py --demo showcase --video showcase.mp4
"""
from __future__ import annotations

from .captions import TOP_CENTER, BOTTOM_CENTER
from .demo import Demo, DemoSegment
from .input_script import InputSpan

# Beats — each segment carries the InputSpans that drive the beat + a caption. The
# frame windows come from the spans (min start .. max end-1) unless given explicitly.
_SEGMENTS = (
    DemoSegment(
        "Nalio (P1) vs Birky (P2) — approach",
        anchor=TOP_CENTER, start=10, end=60,
        spans=(InputSpan(10, 40, 1, "right"),   # P1 walks in
               InputSpan(30, 60, 2, "left")),   # Birky closes the gap
    ),
    DemoSegment(
        "Jump & double-jump",
        anchor=BOTTOM_CENTER,
        spans=(InputSpan(50, 51, 1, "up"), InputSpan(60, 61, 1, "up")),
    ),
    DemoSegment(
        "Jabs — a fast disjoint poke",
        anchor=BOTTOM_CENTER,
        spans=(InputSpan(90, 91, 1, "attack"), InputSpan(95, 96, 2, "attack")),
    ),
    DemoSegment(
        "Shield up",
        anchor=BOTTOM_CENTER,
        spans=(InputSpan(110, 140, 1, "shield"),),
    ),
    DemoSegment(
        "Jab combo racks up damage & knockback",
        anchor=BOTTOM_CENTER, start=141, end=245,
        spans=(InputSpan(141, 142, 1, "attack"), InputSpan(142, 165, 1, "right"),
               InputSpan(165, 166, 1, "attack"), InputSpan(166, 185, 1, "right"),
               InputSpan(185, 186, 1, "attack"), InputSpan(186, 210, 1, "right"),
               InputSpan(210, 211, 1, "attack"), InputSpan(211, 240, 1, "right"),
               InputSpan(240, 241, 1, "attack"),
               InputSpan(150, 151, 2, "up")),     # Birky jumps mid-combo
    ),
    DemoSegment(
        "Shield roll-dodge (intangible)",
        anchor=BOTTOM_CENTER,
        spans=(InputSpan(250, 285, 1, "shield"), InputSpan(268, 269, 1, "left")),
    ),
    DemoSegment(
        "Edge-grab, then off the blast zone (KO)",
        anchor=BOTTOM_CENTER, start=310, end=480,
        spans=(InputSpan(310, 480, 1, "left"),),   # walk to the ledge, grab, then off
    ),
)

SHOWCASE = Demo(name="showcase", segments=_SEGMENTS, p1_char="nalio", p2_char="birky")
