# pycats/sim/showcase.py
"""The curated Nalio-vs-Birky feature-showcase demo (#325, epic #308; re-choreographed #398).

A deterministic scripted battle whose nine captioned `DemoSegment`s each demonstrate an
implemented feature **within that caption's own frame window** — so every beat a viewer
reads is actually happening on screen. `tests/test_showcase_demo.py` binds each feature to
its window and fails if a beat drifts out (the #395 audit found the earlier cut narrated
beats the fighters never performed).

The beats, and what each depends on (the #398 re-choreography):
  1. Approach — both walk onto the thick platform, ending ~48px apart with P1 (Nalio) on
     the LEFT (facing Birky), so every offensive beat points the right way.
  2. Jump & double-jump — a VERTICAL air-jump (no direction held) so P1 lands back in range.
  3. Jab — a GROUNDED jab (fired after landing) that connects; Nalio's jab is a disjoint
     that only lands at its ~48px sweet-spot, so P1 must be grounded and adjacent.
  4. Shield — P1 shields while Birky jabs it, so the shield takes (and absorbs) hits
     (a two-sided beat: Birky is given offence via p2 spans).
  5. Jab combo — three grounded jabs in place that rack damage on the adjacent Birky.
     (Since #898 a grounded normal roots the fighter, so the jabs no longer walk Nalio
     forward; both fighters hold position and the beat just racks damage.)
  6. Fireball — Nalio's neutral-B projectile. P1 first steps BACK to open ~130px of
     space (the rooted jabs above leave Birky adjacent), then throws; the projectile
     travels right and connects. The step-back gives it the flight the snapshot needs.
  7. Roll-dodge — P1 rolls RIGHT clean THROUGH Birky (a dodge is intangible and passes
     through the body when it has room; the light combo above preserves that room).
  8. Ledge grab — P1 walks to the right ledge and presses BACK as it slips off, so it
     catches and HANGS (no walk-off).
  9. Ledge recovery — from the hang, P1 presses UP for a neutral getup (#311), climbing
     onto the lip, then walks in off the edge to finish grounded on the stage.

**Shield-break stun and KO are intentionally NOT staged.** A fixed script can't reliably
break a held shield (the jab whiffs on the shield bubble, draining it only passively), and
the default cats are jab-only — with no smash/launcher (combat/charge.py) their jab
knockback can't KO at reasonable percent, so the only KO they could produce is a walk-off
self-destruct (the #395 anti-pattern). The demo ends cleanly on the ledge hang instead.

Play / record it:
    watch.py --demo showcase              # live
    watch.py --demo showcase --video showcase.mp4
"""

from __future__ import annotations

from ..config import FPS
from .captions import BOTTOM_CENTER, TOP_CENTER
from .demo import Demo, DemoSegment
from .input_script import InputSpan

# Beats — each segment carries the InputSpans that drive the beat + a caption. The
# frame windows come from the spans (min start .. max end-1) unless given explicitly.
_SEGMENTS = (
    DemoSegment(
        "Nalio (P1) vs Birky (P2) — approach",
        anchor=TOP_CENTER,
        start=10,
        end=70,
        spans=(
            InputSpan(10, 40, 1, "right"),  # P1 walks in off the left platform
            InputSpan(30, 60, 2, "left"),
        ),  # Birky closes, staying to P1's right
    ),
    DemoSegment(
        # Vertical jump + air jump — no direction held, so P1 lands back in jab range.
        # dwell_at (#412): freeze at f107 while P1 is airborne mid-flight, not the pre-jump f75.
        "Jump & double-jump",
        anchor=BOTTOM_CENTER,
        start=75,
        end=140,
        dwell_at=107,
        spans=(InputSpan(80, 81, 1, "up"), InputSpan(92, 93, 1, "up")),
    ),
    DemoSegment(
        # P1 has landed and is still adjacent — a GROUNDED jab that connects.
        # dwell_at (#412): freeze at f165 as the jab contacts Birky, not the pre-jab f145.
        # end=184, not 185 (#419): windows are inclusive, so ending at the shield beat's
        # start (185) would double-render both captions on that frame (frozen ~2.5s).
        "Jab — a fast disjoint poke",
        anchor=BOTTOM_CENTER,
        start=145,
        end=184,
        dwell_at=165,
        spans=(InputSpan(160, 161, 1, "attack"),),
    ),
    DemoSegment(
        # P1 raises the shield; Birky jabs it, so the shield takes (and absorbs) hits.
        "Shield blocks Birky's jab",
        anchor=BOTTOM_CENTER,
        start=185,
        end=245,
        spans=(InputSpan(190, 235, 1, "shield"), InputSpan(200, 201, 2, "attack"), InputSpan(214, 215, 2, "attack")),
    ),
    DemoSegment(
        # A short jab combo — three GROUNDED jabs in place that rack damage on the
        # adjacent Birky. Since #898 a grounded normal roots the fighter (no walking
        # during startup/active/recovery), so — unlike the pre-#898 cut, which walked
        # Nalio forward between jabs to body-shove Birky downstage — both fighters hold
        # position and the jabs simply rack damage (3% -> 12%). The fireball beat opens
        # its own spacing (below), so this beat no longer needs to advance anyone.
        "Jab combo racks up damage & knockback",
        anchor=BOTTOM_CENTER,
        start=250,
        end=340,
        spans=(
            InputSpan(255, 256, 1, "attack"),
            InputSpan(275, 276, 1, "attack"),
            InputSpan(295, 296, 1, "attack"),
        ),
    ),
    DemoSegment(
        # P1 zones with Nalio's neutral-B fireball (#432). The jab combo (beat 5) now
        # leaves Birky adjacent (~40px) rather than downstage (#898 rooted the advancing
        # jabs), so P1 first takes a short step BACK (walk left, f346-360) to open ~130px
        # of space, then throws a neutral `special` (no direction held ->
        # move_select._SPECIAL["neutral"] = neutral_b). The snapshot is taken AFTER
        # process_hits, so the projectile is only visible while in flight — the step-back
        # gives it that flight (it would otherwise spawn on top of Birky and be consumed
        # before any frame captures it). It travels right and CONNECTS (+~7%). dwell_at
        # (#412/#898): freeze at f388 while the fireball is airborne mid-flight (the
        # projectile is live f379-398 with the new fire frame), not f345.
        "Fireball — Nalio's neutral-B projectile",
        anchor=BOTTOM_CENTER,
        start=345,
        end=420,
        dwell_at=388,
        spans=(InputSpan(346, 360, 1, "left"), InputSpan(365, 366, 1, "special")),
    ),
    DemoSegment(
        # P1 rolls RIGHT clean through Birky (intangible — passes through the body).
        # Frames shifted +80 by the inserted fireball beat (#432).
        "Shield roll-dodge — intangible, right through Birky",
        anchor=BOTTOM_CENTER,
        start=425,
        end=480,
        spans=(InputSpan(430, 465, 1, "shield"), InputSpan(445, 446, 1, "right")),
    ),
    DemoSegment(
        # Walk to the right ledge, then press BACK (left) as P1 slips off so it catches
        # and HANGS on the edge (no walk-off self-destruct). The 1-frame input gap at the
        # lip lets the grab register before the back-press holds the hang.
        # dwell_at (#412): freeze at f542 while P1 hangs on the ledge, not the walking f485.
        # Frames shifted +80 by the inserted fireball beat (#432). The right-walk runs
        # longer (f485-540, was f485-500) because #898 rooted the earlier jabs, so P1
        # enters this beat ~230px further left than the pre-#898 cut and needs the extra
        # steps to reach the lip before the back-press at f542.
        "Ledge grab — hang on the edge",
        anchor=BOTTOM_CENTER,
        start=485,
        end=600,
        dwell_at=542,
        spans=(InputSpan(485, 540, 1, "right"), InputSpan(542, 595, 1, "left")),
    ),
    DemoSegment(
        # From the hang (still holding at ~f585, auto-release not until ~f621), P1 presses
        # UP for a neutral getup (#311): it repositions onto the lip and opens the
        # LEDGE_GETUP_FRAMES climb window (ledge_hang -> ledge_getup -> idle on the stage).
        # Then a short LEFT walk steps P1 in off the edge, so it ends grounded on the
        # platform (not hanging, not KO'd). dwell_at (#412): freeze at f612 mid-climb,
        # while P1 is in `ledge_getup` on the stage lip. New beat 9 — beats 1-8 keep their
        # indices, so the #397/#412/#419 index-keyed tests are unaffected.
        "Ledge recovery — climb back up",
        anchor=BOTTOM_CENTER,
        start=601,
        end=660,
        dwell_at=612,
        spans=(InputSpan(603, 608, 1, "up"), InputSpan(610, 655, 1, "left")),
    ),
)

# default_dwell (#352): freeze ~2.5s on each caption's start so the (fast) beats are
# readable. 2.5s * 60fps = 150 frames. Presenter-level hold — the choreography is
# unchanged (its jab/KO beats are frame-tuned; idle timeline frames would desync them).
_DWELL = round(2.5 * FPS)  # 150
# #898: dress the fighters in high-visibility light skins (P1 ghost / P2 tabby) so a
# viewer can read state at a glance — the archetypes (nalio/birky, and their movesets)
# are unchanged; only the cosmetic palette is overridden.
SHOWCASE = Demo(
    name="showcase",
    segments=_SEGMENTS,
    p1_char="nalio",
    p2_char="birky",
    p1_palette="ghost",
    p2_palette="tabby",
    default_dwell=_DWELL,
)
