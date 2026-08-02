# pycats/systems/status_model.py
"""The pure (pygame-free) status-feedback model: the single `STATUS_SOURCES`
table plus the functions that derive above-head timer bars and the grabs-left
count from live fighter state.

Moved out of the render adapter (#900, child 3 of #833): `timer_bar_specs` and
`grabs_left_dots` are pure functions of fighter state — no pygame — so they live
in `systems/` and are unit-testable without a display. The render layer draws
them (`render.status.draw_timer_bars` / `draw_grabs_left_dots`) and derives the
body flash from the same table (`render.tint.active_tint`). Byte-identical to the
pre-#900 `render_battle` definitions; only the module home changed.
"""

import math
from typing import NamedTuple

from ..combat.data import GETUP_ATTACK
from ..config import (
    DODGE_TIME,
    FPS,
    GETUP_ROLL_FRAMES,
    KNOCKDOWN_PRONE_FRAMES,
    LEDGE_REGRAB_INTANGIBLE_CUTOFF,
    LEDGE_REGRAB_LOCKOUT_FRAMES,
    RED,
    SHIELD_BREAK_STUN_MAX,
    SHIELD_DRAIN_PER_FRAME,
    SHIELD_MAX_HP,
    SMASH_CHARGE_FRAMES,
    WHITE,
    YELLOW,
)
from ..storage import runtime_settings

# Per-timer bar colours (#334 spec). These are the BAR hues only — distinct from
# the shared SHIELD_COLOR (shield bubble) / YELLOW (dizzy stars + body flash),
# which are left untouched so only the above-head bars recolour.
SHIELD_BAR_COLOR = (70, 130, 255)  # blue — shield resource (#364)
DIZZY_BAR_COLOR = (210, 90, 220)  # magenta — shield-break stun (#364)
# (HANG_BAR_COLOR removed with the ledge-hang timeout — #475)
DOWN_BAR_COLOR = (255, 140, 45)  # orange — knockdown/getup window (#350)
LOCKOUT_BAR_COLOR = (230, 70, 70)  # red — post-drop regrab lockout (#357)
INTANGIBLE_BAR_COLOR = (95, 225, 120)  # green — intangibility window (#358)
CHARGE_BAR_COLOR = (255, 205, 40)  # gold — smash charge, the one FILL bar (#380)
RECHARGE_BAR_COLOR = (60, 200, 140)  # teal — shield HP regen after release (#597)

# The getup-attack (#225) intangibility window = the whole swing, so its bar's
# max is the move's total frames (kept in sync with the move data, not hardcoded).
_GETUP_ATTACK_FRAMES = GETUP_ATTACK.startup + GETUP_ATTACK.active + GETUP_ATTACK.recovery

# Recency sentinel: the shield bar is a *resource* gauge (shield_hp), not a frame
# counter, so it has no comparable "frames elapsed since start". Give it a key
# that sorts it LAST (a held shield reads as background; action count-downs stack
# newest-on-top above it). See timer_bar_specs' recency ordering (#357).
_SHIELD_RECENCY_KEY = float("inf")


class TimerBar(NamedTuple):
    """One above-head bar: a coloured 0..1 fill, a text readout, and an optional
    label. `label=None` renders no label (byte-identical to the #111 bar)."""

    ratio: float  # 0..1 fill fraction (drawer clamps)
    readout: str  # e.g. "3s" (count-down) or "60% · 1.2s" (fill)
    color: tuple  # bar fill + label colour
    label: str | None = None


def _intangible_remaining_max(p):
    """The active intangibility window as `(remaining, max)` frames, or None.

    Per-source resolve (#358, option 1): `fighter.intangible` is a bool driven
    by several actions, each with its own timer and constant max — dodge
    (DODGE_TIME), getup-roll (GETUP_ROLL_FRAMES), getup-attack (the whole swing).
    Gated on the `intangible` bool so the bar shows only while actually
    intangible, and **suppressed while ledge-hanging** — the ledge-grab burst gets
    its own dedicated bar in #531; until then the hang shows no intangibility bar
    (the HANG timeout bar it used to defer to is gone, #475). Returns None when not
    intangible or the source has no tracked frame window (e.g. respawn grants none).
    """
    f = p.fighter
    if not f.intangible or p.state == "ledge_hang":
        return None
    if f.dodge_timer > 0:
        return (f.dodge_timer, DODGE_TIME)
    if f.getup_roll_timer > 0:
        return (f.getup_roll_timer, GETUP_ROLL_FRAMES)
    if f.getup_attack_timer > 0:
        return (f.getup_attack_timer, _GETUP_ATTACK_FRAMES)
    return None


def _secs(frames):
    """The `"Ns"` count-down readout shared by every COUNTDOWN bar (#111)."""
    return f"{math.ceil(frames / FPS)}s"


class StatusSource(NamedTuple):
    """One declarative status feedback source (#522) — the single description that
    both `active_tint` and `timer_bar_specs` derive from, so a status is defined in
    ONE place and adding one (e.g. #531 ledge-intangible, #506 respawn) is a single record
    with no new branches. Callables take `(f, p)` (fighter, player).

    `kind` documents the value-shape (COUNTDOWN / RESOURCE / FILL); the per-source
    `ratio`/`readout`/`recency` callables encode it (kept explicit so the migration is
    byte-identical to the pre-#522 inline logic)."""

    name: str
    precedence: int  # tint order + exclusive-bar selection order (low first)
    active: object  # (f, p) -> bool: is this source live?
    kind: object = None  # "COUNTDOWN" | "RESOURCE" | "FILL" (documentation)
    tint: object = None  # body-flash overlay colour, or None
    bar_color: object = None  # timer-bar colour, or None
    bar_label: object = None
    bar_class: object = None  # "exclusive" | "overlay"
    ratio: object = None  # (f, p) -> float  (0..1 fill; drawer clamps)
    readout: object = None  # (f, p) -> str
    recency: object = None  # (f, p) -> float  (sort key; lower = nearer head)


# The single source of truth for status tints + above-head bars (#522). Order here is
# precedence order; `active_tint` returns the first live source with a `tint`, and
# `timer_bar_specs` takes the first live EXCLUSIVE bar + all live OVERLAY bars. Byte-
# identical to the pre-#522 `active_tint` if-chain and `timer_bar_specs` branches.
# The dizzy star-halo (draw_dizzy_stars) is a separate render path, not modelled here.
STATUS_SOURCES = [
    StatusSource("hurt", 0, kind="COUNTDOWN", tint=RED, active=lambda f, p: f.hurt_timer > 0),
    StatusSource(
        "shield",
        1,
        kind="RESOURCE",
        active=lambda f, p: p.state == "shield",
        bar_color=SHIELD_BAR_COLOR,
        bar_label="SHIELD",
        bar_class="exclusive",
        ratio=lambda f, p: f.shield_hp / SHIELD_MAX_HP,
        readout=lambda f, p: f"{math.ceil(f.shield_hp / (SHIELD_DRAIN_PER_FRAME * FPS))}s",
        recency=lambda f, p: _SHIELD_RECENCY_KEY,
    ),
    StatusSource(
        "stun",
        2,
        kind="COUNTDOWN",
        tint=YELLOW,
        active=lambda f, p: f.stun_timer > 0,
        bar_color=DIZZY_BAR_COLOR,
        bar_label="DIZZY",
        bar_class="exclusive",
        ratio=lambda f, p: f.stun_timer / SHIELD_BREAK_STUN_MAX,
        readout=lambda f, p: _secs(f.stun_timer),
        recency=lambda f, p: SHIELD_BREAK_STUN_MAX - f.stun_timer,
    ),
    StatusSource("dodge", 3, kind="COUNTDOWN", tint=WHITE, active=lambda f, p: f.dodge_timer > 0),
    # LEDGE-INTANG (#531, revived #658) — the fixed ledge-grab intangibility burst
    # (21f full for grabs 1-5, 5f residual for grab 6+ past the cutoff; #656/#683). Its
    # own INTANG overlay bar. #531 suppressed it while `state == "ledge_hang"` — the ONE
    # state in which the timer is ever live — so the bar never rendered (the #531
    # dead-render defect). #658 drops that gate so it shows DURING the hang, stacked
    # above the grabs-left dots (#657; the #720 stack). Ratio is against the *granted*
    # length stored at grab (#538), so a 5f residual grab drains a truthful 5/5->0
    # (normalized per-grant — #720 chose this over a proportional stub). No body tint.
    # The reversal is scoped to THIS bar only: _intangible_remaining_max KEEPS its ledge-hang
    # suppression for the dodge/getup/respawn INTANG bar, so the two never double up
    # during a hang. Spec: docs/pm-reference/ledge-regrab-intangible-and-display.md.
    StatusSource(
        "ledge_intangible",
        4,
        kind="COUNTDOWN",
        active=lambda f, p: f.ledge_intangible_timer > 0,
        bar_color=INTANGIBLE_BAR_COLOR,
        bar_label="INTANG",
        bar_class="overlay",
        ratio=lambda f, p: f.ledge_intangible_timer / max(1, f.ledge_intangible_granted),
        readout=lambda f, p: _secs(f.ledge_intangible_timer),
        recency=lambda f, p: f.ledge_intangible_granted - f.ledge_intangible_timer,
    ),
    StatusSource(
        "prone",
        5,
        kind="COUNTDOWN",
        active=lambda f, p: p.state == "prone" and f.prone_timer > 0,
        bar_color=DOWN_BAR_COLOR,
        bar_label="DOWN",
        bar_class="exclusive",
        ratio=lambda f, p: f.prone_timer / KNOCKDOWN_PRONE_FRAMES,
        readout=lambda f, p: _secs(f.prone_timer),
        recency=lambda f, p: KNOCKDOWN_PRONE_FRAMES - f.prone_timer,
    ),
    StatusSource(
        "lockout",
        6,
        kind="COUNTDOWN",
        active=lambda f, p: f.ledge_regrab_lockout_timer > 0,
        bar_color=LOCKOUT_BAR_COLOR,
        bar_label="LOCKOUT",
        bar_class="overlay",
        ratio=lambda f, p: f.ledge_regrab_lockout_timer / LEDGE_REGRAB_LOCKOUT_FRAMES,
        readout=lambda f, p: _secs(f.ledge_regrab_lockout_timer),
        recency=lambda f, p: LEDGE_REGRAB_LOCKOUT_FRAMES - f.ledge_regrab_lockout_timer,
    ),
    # INTANG — the dodge / getup-roll / getup-attack intangibility window, resolved
    # (with its `intangible`-bool gate + ledge-hang suppression) by
    # _intangible_remaining_max. One overlay bar; #531 (ledge-intangible) and #506 (respawn)
    # each add their OWN separate source rather than extend this resolver.
    StatusSource(
        "intangible",
        7,
        kind="COUNTDOWN",
        active=lambda f, p: _intangible_remaining_max(p) is not None,
        bar_color=INTANGIBLE_BAR_COLOR,
        bar_label="INTANG",
        bar_class="overlay",
        ratio=lambda f, p: _intangible_remaining_max(p)[0] / _intangible_remaining_max(p)[1],
        readout=lambda f, p: _secs(_intangible_remaining_max(p)[0]),
        recency=lambda f, p: _intangible_remaining_max(p)[1] - _intangible_remaining_max(p)[0],
    ),
    # CHARGE (#380) — the one FILL bar: grows 0->100% as smash_charge_timer accumulates
    # rather than draining; recency = the up-count (frames elapsed since charge began).
    StatusSource(
        "charge",
        8,
        kind="FILL",
        active=lambda f, p: f.smash_charge_timer > 0,
        bar_color=CHARGE_BAR_COLOR,
        bar_label="CHARGE",
        bar_class="overlay",
        ratio=lambda f, p: min(1.0, f.smash_charge_timer / SMASH_CHARGE_FRAMES),
        readout=lambda f, p: (
            f"{round(min(1.0, f.smash_charge_timer / SMASH_CHARGE_FRAMES) * 100)}%·"
            f"{math.ceil((SMASH_CHARGE_FRAMES - f.smash_charge_timer) / FPS)}s"
        ),
        recency=lambda f, p: f.smash_charge_timer,
    ),
    # RECHARGE (#597) — shield HP regenerating back to full after release. A FILL bar
    # (fills 0->100% as shield_hp climbs), shown ONLY while regenerating and never
    # during shield-break dizzy: the `stun_timer == 0` clause makes it provably never
    # co-live with the "stun"/DIZZY source (active on stun_timer > 0). Overlay so it
    # composes with a concurrent action bar (e.g. DOWN/LOCKOUT while HP climbs); as a
    # background resource gauge it reuses _SHIELD_RECENCY_KEY to sort last, so action
    # count-downs stack above it (mirrors the SHIELD drain gauge, with which it is
    # state-exclusive: that needs state == "shield", this needs state != "shield").
    StatusSource(
        "recharge",
        9,
        kind="FILL",
        active=lambda f, p: p.state != "shield" and f.shield_hp < SHIELD_MAX_HP and f.stun_timer == 0,
        bar_color=RECHARGE_BAR_COLOR,
        bar_label="RECHARGE",
        bar_class="overlay",
        ratio=lambda f, p: f.shield_hp / SHIELD_MAX_HP,
        readout=lambda f, p: _secs((SHIELD_MAX_HP - f.shield_hp) / SHIELD_DRAIN_PER_FRAME),
        recency=lambda f, p: _SHIELD_RECENCY_KEY,
    ),
]


def _bar_for(s, f, p):
    """Build the `(recency, TimerBar)` pair for a live bar source `s`."""
    return (s.recency(f, p), TimerBar(s.ratio(f, p), s.readout(f, p), s.bar_color, s.bar_label))


def timer_bar_specs(p):
    """The active above-head timer bars for fighter `p`, ordered newest-on-top.

    Pure function of live state (#111): each fill is the remaining value over the
    *known constant max* — shield -> shield_hp/SHIELD_MAX_HP, stun ->
    stun_timer/SHIELD_BREAK_STUN_MAX, etc. — so no per-instance start value is
    stored and a bar tracks mid-effect changes (e.g. a blocked hit chipping
    shield). Honours the live status-bars toggle (runtime_settings, #111/#121).

    Two kinds of bar (#357):
    - **Exclusive-state** bars (shield / stun / hang / prone) — mutually exclusive
      states, so at most one is added (shield takes precedence, via the elif
      chain: a shielding fighter is never simultaneously stunned).
    - **Overlay** timers — state-independent, so they co-activate with the above:
      LOCKOUT (post-drop regrab suppression, #357) and INTANG (intangibility
      window, #358; per-source resolve via _intangible_remaining_max).

    Bars are returned **newest-on-top**: sorted by recency = frames elapsed since
    the timer started (`max - remaining`), ascending, so the most recently started
    bar is `specs[0]` (drawn nearest the head by draw_timer_bars). The shield
    resource gauge has no frame elapsed and sorts last (`_SHIELD_RECENCY_KEY`).
    Ordering is stable, so equal-recency bars keep insertion order. Single-bar
    cases return the same one bar as before this slice (byte-identity preserved).
    """
    if not runtime_settings.show_status_timer_bars():
        return []
    f = p.fighter
    ordered = sorted(STATUS_SOURCES, key=lambda s: s.precedence)
    bars = []  # (recency_key, TimerBar); lower key = more recent = nearer head

    # --- exclusive-state bar (at most one): first live one, by precedence ---
    for s in ordered:
        if s.bar_class == "exclusive" and s.bar_color is not None and s.active(f, p):
            bars.append(_bar_for(s, f, p))
            break

    # --- overlay bars (state-independent; co-activate with the exclusive) ---
    for s in ordered:
        if s.bar_class == "overlay" and s.bar_color is not None and s.active(f, p):
            bars.append(_bar_for(s, f, p))

    bars.sort(key=lambda kb: kb[0])  # newest-on-top (least elapsed first)
    return [bar for _, bar in bars]


def grabs_left_dots(p):
    """How many grabs-left dots to show above fighter `p` — 0 for none (#657).

    Each dot is one remaining ledge grab (of `LEDGE_REGRAB_INTANGIBLE_CUTOFF`) that still
    grants the full intangibility burst before PM's anti-plank cutoff. Pinned to the
    shipped #656 counter, which is **1 on the first grab**:
    `dots = LEDGE_REGRAB_INTANGIBLE_CUTOFF + 1 - ledge_regrab_count`, shown only while the
    fighter is in an active regrab chain (count in `1..CUTOFF`). At count 0 (no chain /
    just reset) or past the cutoff (6+), no dots — so the first grab shows 5, the fifth
    shows 1, and the sixth shows none. Honours the shared status-bars toggle. Spec:
    docs/pm-reference/ledge-regrab-intangible-and-display.md.
    """
    if not runtime_settings.show_status_timer_bars():
        return 0
    count = p.fighter.ledge_regrab_count
    if count < 1 or count > LEDGE_REGRAB_INTANGIBLE_CUTOFF:
        return 0
    return LEDGE_REGRAB_INTANGIBLE_CUTOFF + 1 - count
