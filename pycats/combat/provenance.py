"""Tuning-data provenance registry + drift-guard anchor (ADR-0003, #233).

The combat/physics tuning constants live as plain Python literals in
`pycats.config` (byte-stable, no loader — ADR-0003 constraint C1). *Why* each
value is what it is — its source, unit, status, and any derivation — lives here,
in a typed sidecar keyed by the constant's name. The two are kept in lock-step by
`tests/test_tuning_provenance.py`:

  1. no drift        — every `Provenance.value` equals the live `config.<name>`;
  2. no orphans      — the registry keyset equals `TUNING_CONSTANT_NAMES`;
  3. derivation integrity — every `derivation` re-evaluates to its `value`.

This module is **data only** — it deliberately does NOT import `config` for
values. Each value is stated twice (here and in `config`) on purpose: the
drift-guard exists to police the pair, so editing one without the other reds the
suite (ADR-0003 constraint C4).

Scope (v1): the sourced combat/physics **scalars** in `config.py`. Render/UI,
cat-feature, tail-physics, platform, and menu constants are excluded by
construction (no provenance noise on `BG_COLOR`). Per-character/move data in
`characters/*.py` is a later slice.

`status` values: FOUND (traced to a cited canon value), GUESS (unsourced /
playtest starting point — the #319 value-sourcing pass resolves these),
TUNED (deliberate design value, not seeking canon), DIVERGENCE (intentional
departure from a known canon value).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Provenance:
    value: int | float           # MUST equal the live config constant (C4 anchor)
    unit: str                    # "px/frame" | "frames" | "deg" | "factor" | "%" | ...
    source: str                  # citation: repo/path, SmashWiki page, or "unsourced …"
    status: str                  # "FOUND" | "GUESS" | "TUNED" | "DIVERGENCE"
    issue: int | None            # GH issue that sourced/introduced it
    derivation: str | None = None  # e.g. "round(3.1 * PX_PER_UNIT)"; None = direct literal


# One row per in-scope constant. Keyed by the exact `config` attribute name.
TUNING_PROVENANCE: dict[str, Provenance] = {
    # ---- base movement / physics (unsourced defaults; #319 to source) ----
    "GRAVITY": Provenance(0.5, "px/frame^2", "pycats base-physics default; not yet traced to canon", "GUESS", None),
    "MAX_FALL_SPEED": Provenance(13, "px/frame", "pycats base-physics default; not yet traced to canon", "GUESS", None),
    "MOVE_SPEED": Provenance(6, "px/frame", "pycats base-physics default; not yet traced to canon", "GUESS", None),
    "JUMP_VEL": Provenance(-13, "px/frame", "pycats base-physics default; not yet traced to canon", "GUESS", None),

    # ---- dodges / rolls ----
    "DODGE_FRAMES": Provenance(15, "frames", "roll intangibility window; playtest starting point", "GUESS", None),
    "DODGE_TIME": Provenance(14, "frames", "roll duration; playtest starting point", "GUESS", None),
    "DODGE_SPEED": Provenance(14, "px/frame", "roll horizontal boost; playtest starting point", "GUESS", None),
    # FOUND (#215): Melee escapeair_force = 3.1 units/frame (doldecomp/melee, meleelight
    # ESCAPEAIR.js); px/frame = round(3.1 * PX_PER_UNIT). PM restored Melee's air dodge.
    "DODGE_AIR_SPEED": Provenance(17, "px/frame", "doldecomp/melee escapeair_force=3.1u/f; meleelight ESCAPEAIR.js; SmashWiki:Air_dodge", "FOUND", 215, "round(3.1 * PX_PER_UNIT)"),

    # ---- wavedash (#202/#184) ----
    "WAVEDASH_ANGLE_DEG": Provenance(17.1, "deg", "SmashWiki:Wavedash — optimal angle 17.1 deg below horizontal (Melee/PM)", "FOUND", 202),
    "WAVEDASH_LANDING_LAG": Provenance(10, "frames", "SmashWiki:Wavedash — Melee/PM landing lag ~10 frames (60 FPS maps 1:1)", "FOUND", 202),

    # ---- fighter-vs-fighter jostle (#1/#68) ----
    "JOSTLE_MIN_VOVERLAP_FRAC": Provenance(0.8, "factor", "deliberate vertical-overlap gate for the PM X-only push heuristic", "TUNED", 68),

    # ---- shield / shieldstun / shield-break (#12/#140/#111) ----
    "SHIELD_BREAK_STUN_MAX": Provenance(490, "frames", "Melee/PM shield-break stun = (400 - percent) + 90; max at 0%", "FOUND", 12),
    "SHIELD_BREAK_STUN_MIN": Provenance(90, "frames", "Melee/PM shield-break stun = (400 - percent) + 90; min at >=400%", "FOUND", 12),
    "SHIELDSTUN_FACTOR": Provenance(0.345, "factor", "SmashWiki:Shieldstun — Brawl/PM factor 0.345", "FOUND", 140),
    "SHIELD_MAX_HP": Provenance(50, "hp", "fresh shield-bubble HP; pycats tuning, not sourced", "GUESS", None),
    "SHIELD_DRAIN_PER_FRAME": Provenance(0.2, "hp/frame", "shield HP drain/regain per frame; pycats tuning, not sourced", "GUESS", 111),

    # ---- hitstun (#43/#44) ----
    "HITSTUN_MULTIPLIER": Provenance(0.4, "factor", "hitstun_frames = floor(KB * this); approx Brawl/PM ~0.4, unverified", "GUESS", None),
    "HITSTUN_FLOOR": Provenance(1, "frames", "minimum hitstun for any clean hit; tuning, not sourced", "GUESS", None),

    # ---- hitlag / freeze frames (#138) ----
    "HITLAG_DAMAGE_FACTOR": Provenance(0.3846154, "factor", "SmashWiki:Hitlag (Brawl onward) — d-term coefficient 1/2.6", "FOUND", 138),
    "HITLAG_BASE": Provenance(5, "frames", "SmashWiki:Hitlag (Brawl onward) — base term", "FOUND", 138),
    "HITLAG_CAP": Provenance(30, "frames", "SmashWiki:Hitlag — Brawl-onward cap (Melee was 20)", "FOUND", 138),

    # ---- knockback decay model (#44 from #43) ----
    "KNOCKBACK_LAUNCH_FACTOR": Provenance(0.085, "factor", "launch_speed = KB * this; scaled from Smash KB*0.03 to the 960px stage; tuning", "GUESS", 44),
    "KNOCKBACK_DECAY": Provenance(0.145, "px/frame", "hitstun velocity bleed/frame; scaled from Smash 0.051 keeping the 1.7 decay/launch ratio; tuning", "GUESS", 44),

    # ---- Sakurai angle (#203, a #142 gate) ----
    "SAKURAI_ANGLE_CODE": Provenance(361, "code", "SmashWiki:Sakurai_angle — the 361 sentinel (not a literal degree)", "FOUND", 203),
    "SAKURAI_AIRBORNE_DEG": Provenance(40.0, "deg", "Brawl/PM-derived airborne launch angle; playtest starting point", "GUESS", 203),
    "SAKURAI_GROUNDED_MAX_DEG": Provenance(40.0, "deg", "Brawl/PM-derived grounded max angle at HIGH_KB; playtest starting point", "GUESS", 203),
    "SAKURAI_GROUNDED_LOW_KB": Provenance(60.0, "kb", "grounded angle stays flat below this KB; playtest starting point", "GUESS", 203),
    "SAKURAI_GROUNDED_HIGH_KB": Provenance(88.0, "kb", "grounded angle reaches max at this KB; playtest starting point", "GUESS", 203),

    # ---- crouch-cancel (#135) ----
    "CROUCH_CANCEL_FACTOR": Provenance(0.67, "factor", "Melee/PM crouch-cancel knockback scale (0.67x); value cited, still a tuning starting point", "FOUND", 135),

    # ---- auto landing-velocity knockdown (#145) ----
    "KNOCKDOWN_VY_THRESHOLD": Provenance(8.0, "px/frame", "downward impact speed that forces prone while in hitstun; not sourced", "GUESS", 145),
    "KNOCKDOWN_PRONE_FRAMES": Provenance(30, "frames", "getup window the auto-knockdown sets (~0.5s @60 FPS); not sourced", "GUESS", 145),

    # ---- getup-roll (#146) ----
    "GETUP_ROLL_FRAMES": Provenance(16, "frames", "getup-roll duration = its intangibility window; playtest starting point", "GUESS", 146),
    "GETUP_ROLL_SPEED": Provenance(12.0, "px/frame", "initial getup-roll horizontal speed (decays under friction); playtest starting point", "GUESS", 146),

    # ---- clank / priority (#38 4c) ----
    "CLANK_PRIORITY_RANGE": Provenance(9, "%", "SmashWiki:Priority — 9% across the Melee/Brawl/PM family", "FOUND", 38),
}

# The curated combat/physics set (excludes render/UI/tail/platform/menu constants).
# This is an INDEPENDENT hand-maintained list — NOT derived from TUNING_PROVENANCE —
# so the "no orphans" drift-guard can actually fail: add a constant to config + this
# set but forget the registry row (or vice versa) and the test reds. Adding a tuning
# constant to config forces both a name here and a row above.
TUNING_CONSTANT_NAMES: frozenset[str] = frozenset({
    "GRAVITY", "MAX_FALL_SPEED", "MOVE_SPEED", "JUMP_VEL",
    "DODGE_FRAMES", "DODGE_TIME", "DODGE_SPEED", "DODGE_AIR_SPEED",
    "WAVEDASH_ANGLE_DEG", "WAVEDASH_LANDING_LAG",
    "JOSTLE_MIN_VOVERLAP_FRAC",
    "SHIELD_BREAK_STUN_MAX", "SHIELD_BREAK_STUN_MIN", "SHIELDSTUN_FACTOR",
    "SHIELD_MAX_HP", "SHIELD_DRAIN_PER_FRAME",
    "HITSTUN_MULTIPLIER", "HITSTUN_FLOOR",
    "HITLAG_DAMAGE_FACTOR", "HITLAG_BASE", "HITLAG_CAP",
    "KNOCKBACK_LAUNCH_FACTOR", "KNOCKBACK_DECAY",
    "SAKURAI_ANGLE_CODE", "SAKURAI_AIRBORNE_DEG", "SAKURAI_GROUNDED_MAX_DEG",
    "SAKURAI_GROUNDED_LOW_KB", "SAKURAI_GROUNDED_HIGH_KB",
    "CROUCH_CANCEL_FACTOR",
    "KNOCKDOWN_VY_THRESHOLD", "KNOCKDOWN_PRONE_FRAMES",
    "GETUP_ROLL_FRAMES", "GETUP_ROLL_SPEED",
    "CLANK_PRIORITY_RANGE",
})
