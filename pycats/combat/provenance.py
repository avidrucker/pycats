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
    value: int | float  # MUST equal the live config constant (C4 anchor)
    unit: str  # "px/frame" | "frames" | "deg" | "factor" | "%" | ...
    source: str  # citation: repo/path, SmashWiki page, or "unsourced …"
    status: str  # "FOUND" | "GUESS" | "TUNED" | "DIVERGENCE"
    issue: int | None  # GH issue that sourced/introduced it
    derivation: str | None = None  # e.g. "round(3.1 * PX_PER_UNIT)"; None = direct literal


# One row per in-scope constant. Keyed by the exact `config` attribute name.
TUNING_PROVENANCE: dict[str, Provenance] = {
    # ---- base movement / physics (calibrated to PM Mario via PX_PER_UNIT, #120/#384) ----
    "GRAVITY": Provenance(
        0.5,
        "px/frame^2",
        "PM Mario gravity 0.095 u/f^2 (SmashWiki:Mario_(PM); #120)",
        "FOUND",
        384,
        "round(0.095 * PX_PER_UNIT, 1)",
    ),
    "MAX_FALL_SPEED": Provenance(
        13,
        "px/frame",
        "DIVERGENCE: pycats uses a single global fall speed ~= PM Mario fast-fall 2.3 u/f; the Melee/PM base 1.7 / fast-fall 2.3 split is not modelled (SmashWiki:Mario_(PM); #120)",  # noqa: E501
        "DIVERGENCE",
        384,
    ),
    "MOVE_SPEED": Provenance(
        6, "px/frame", "PM Mario walk 1.1 u/f (SmashWiki:Mario_(PM); #120)", "FOUND", 384, "round(1.1 * PX_PER_UNIT)"
    ),
    "JUMP_VEL": Provenance(
        -13,
        "px/frame",
        "calibrated to PM Mario full-hop 30.19 u (SmashWiki:Mario_(PM); #120) via height = JUMP_VEL^2/(2*GRAVITY) = 169 px ~= 31 u @ PX_PER_UNIT",  # noqa: E501
        "FOUND",
        384,
    ),
    # ---- authoring scale + walk/dash/jump (#195/#388, sourced-scalars slice #581) ----
    "PX_PER_UNIT": Provenance(
        5.4,
        "px/unit",
        "data-authoring units->px calibration ~=5.4 (docs/research-120-smash-units-and-sources.md; #120/#195); the base every spatial derivation in this registry references",  # noqa: E501
        "FOUND",
        195,
    ),
    "DASH_SPEED": Provenance(
        8,
        "px/frame",
        "PM Mario dash ~1.5 u/f (config #388 comment; docs/research-120) -> round(1.5 * PX_PER_UNIT) = round(8.1)",
        "FOUND",
        388,
        "round(1.5 * PX_PER_UNIT)",
    ),
    "MAX_JUMPS": Provenance(
        2,
        "jumps",
        "Mario/PM jump count: 1 ground + 1 midair = 2 (standard 2-jump character; SmashWiki:Mario_(PM))",
        "FOUND",
        None,
    ),
    # ---- smash charge (#327 slice 3 / #426) ----
    "SMASH_CHARGE_FRAMES": Provenance(
        60,
        "frames",
        "PM/Melee full smash charge = 60 frames = 1s (confirmed #426, SmashWiki:Smash_attack)",
        "FOUND",
        426,
    ),
    "SMASH_CHARGE_SCALE": Provenance(
        1.4,
        "factor",
        "PM (Brawl-era) full-charge damage multiplier 1.4 (Melee 1.3671; confirmed #426, SmashWiki:Smash_attack)",
        "FOUND",
        426,
    ),
    # ---- dodges / rolls ----
    "DODGE_FRAMES": Provenance(15, "frames", "roll intangibility window; playtest starting point", "GUESS", None),
    "DODGE_TIME": Provenance(14, "frames", "roll duration; playtest starting point", "GUESS", None),
    "DODGE_SPEED": Provenance(
        14,
        "px/frame",
        "pycats ground-roll horizontal boost; Melee rolls are animation-driven per-character, no single canon speed to derive",  # noqa: E501
        "TUNED",
        None,
    ),
    # FOUND (#215): Melee escapeair_force = 3.1 units/frame (doldecomp/melee, meleelight
    # ESCAPEAIR.js); px/frame = round(3.1 * PX_PER_UNIT). PM restored Melee's air dodge.
    "DODGE_AIR_SPEED": Provenance(
        17,
        "px/frame",
        "doldecomp/melee escapeair_force=3.1u/f; meleelight ESCAPEAIR.js; SmashWiki:Air_dodge",
        "FOUND",
        215,
        "round(3.1 * PX_PER_UNIT)",
    ),
    # ---- wavedash (#202/#184) ----
    "WAVEDASH_ANGLE_DEG": Provenance(
        17.1, "deg", "SmashWiki:Wavedash — optimal angle 17.1 deg below horizontal (Melee/PM)", "FOUND", 202
    ),
    "WAVEDASH_LANDING_LAG": Provenance(
        10, "frames", "SmashWiki:Wavedash — Melee/PM landing lag ~10 frames (60 FPS maps 1:1)", "FOUND", 202
    ),
    # ---- fighter-vs-fighter jostle (#1/#68) ----
    "JOSTLE_MIN_VOVERLAP_FRAC": Provenance(
        0.8, "factor", "deliberate vertical-overlap gate for the PM X-only push heuristic", "TUNED", 68
    ),
    # ---- shield / shieldstun / shield-break (#12/#140/#111) ----
    "SHIELD_BREAK_STUN_MAX": Provenance(
        490, "frames", "Melee/PM shield-break stun = (400 - percent) + 90; max at 0%", "FOUND", 12
    ),
    "SHIELD_BREAK_STUN_MIN": Provenance(
        90, "frames", "Melee/PM shield-break stun = (400 - percent) + 90; min at >=400%", "FOUND", 12
    ),
    "SHIELDSTUN_FACTOR": Provenance(0.345, "factor", "SmashWiki:Shieldstun — Brawl/PM factor 0.345", "FOUND", 140),
    "SHIELD_MAX_HP": Provenance(
        50,
        "hp",
        "pycats shield-HP model; no verified 1:1 canon value (Melee uses a different shield-health/decay model)",
        "TUNED",
        12,
    ),
    "SHIELD_DRAIN_PER_FRAME": Provenance(
        0.2, "hp/frame", "pycats shield-HP model; deliberate drain/regain rate, no canon equivalent", "TUNED", 111
    ),
    # ---- hitstun (#43/#44) ----
    "HITSTUN_MULTIPLIER": Provenance(
        0.4,
        "factor",
        "SmashWiki:Hitstun — 0.4 frames per unit of knockback (Melee; Brawl same; PM = Melee model)",
        "FOUND",
        378,
    ),
    "HITSTUN_FLOOR": Provenance(
        1,
        "frames",
        "pycats floor: >=1 frame for any clean hit; SmashWiki:Hitstun documents no canon minimum",
        "TUNED",
        138,
    ),
    # ---- hitlag / freeze frames (#138) ----
    "HITLAG_DAMAGE_FACTOR": Provenance(
        0.3846154, "factor", "SmashWiki:Hitlag (Brawl onward) — d-term coefficient 1/2.6", "FOUND", 138
    ),
    "HITLAG_BASE": Provenance(5, "frames", "SmashWiki:Hitlag (Brawl onward) — base term", "FOUND", 138),
    "HITLAG_CAP": Provenance(30, "frames", "SmashWiki:Hitlag — Brawl-onward cap (Melee was 20)", "FOUND", 138),
    # ---- knockback decay model (#44 from #43) ----
    "KNOCKBACK_LAUNCH_FACTOR": Provenance(
        0.085,
        "factor",
        "DIVERGENCE from Smash launch_speed = KB*0.03 (docs/research/knockback-launch-physics-findings.md, #43): deliberately scaled to the 960px stage",  # noqa: E501
        "DIVERGENCE",
        44,
    ),
    "KNOCKBACK_DECAY": Provenance(
        0.145,
        "px/frame",
        "DIVERGENCE from Smash decay 0.051/frame (#43): deliberately scaled to the 960px stage, preserving the 1.7 decay/launch ratio",  # noqa: E501
        "DIVERGENCE",
        44,
    ),
    # ---- Sakurai angle (#203, a #142 gate) ----
    "SAKURAI_ANGLE_CODE": Provenance(
        361, "code", "SmashWiki:Sakurai_angle — the 361 sentinel (not a literal degree)", "FOUND", 203
    ),
    "SAKURAI_AIRBORNE_DEG": Provenance(
        40.0,
        "deg",
        "pycats airborne launch angle; keyed to pycats knockback() magnitude, not Smash units — no canon value",
        "TUNED",
        203,
    ),
    "SAKURAI_GROUNDED_MAX_DEG": Provenance(
        40.0,
        "deg",
        "pycats grounded max angle at HIGH_KB; keyed to pycats knockback() magnitude, not Smash units — no canon value",
        "TUNED",
        203,
    ),
    "SAKURAI_GROUNDED_LOW_KB": Provenance(
        60.0,
        "kb",
        "pycats threshold — grounded angle stays flat below this pycats KB magnitude; no canon value",
        "TUNED",
        203,
    ),
    "SAKURAI_GROUNDED_HIGH_KB": Provenance(
        88.0,
        "kb",
        "pycats threshold — grounded angle reaches max at this pycats KB magnitude; no canon value",
        "TUNED",
        203,
    ),
    # ---- crouch-cancel (#135) ----
    "CROUCH_CANCEL_FACTOR": Provenance(
        0.67,
        "factor",
        "Melee/PM crouch-cancel knockback scale (0.67x); value cited, still a tuning starting point",
        "FOUND",
        135,
    ),
    # ---- auto landing-velocity knockdown (#145) ----
    "KNOCKDOWN_VY_THRESHOLD": Provenance(
        8.0,
        "px/frame",
        "pycats auto-knockdown impact-speed gate (#145); pycats-specific mechanic, no canon equivalent",
        "TUNED",
        145,
    ),
    "KNOCKDOWN_PRONE_FRAMES": Provenance(
        30,
        "frames",
        "pycats fixed getup window (~0.5s @60 FPS); Melee knockdown/getup is variable + per-character, no single canon value (SmashWiki:Floor_getup)",  # noqa: E501
        "TUNED",
        145,
    ),
    # ---- getup-roll (#146) ----
    "GETUP_ROLL_FRAMES": Provenance(
        16,
        "frames",
        "pycats getup-roll duration = its intangibility window; DIVERGENCE from Melee (getup roll 35f, intangible frames 1-14..1-24 per Smashboards frame data) — pycats runs a shorter roll on its own scale",  # noqa: E501
        "DIVERGENCE",
        146,
    ),
    "GETUP_ROLL_SPEED": Provenance(
        12.0,
        "px/frame",
        "pycats getup-roll horizontal speed (decays under friction); no canon single value (animation-driven)",
        "TUNED",
        146,
    ),
    # ---- clank / priority (#38 4c) ----
    "CLANK_PRIORITY_RANGE": Provenance(9, "%", "SmashWiki:Priority — 9% across the Melee/Brawl/PM family", "FOUND", 38),
    # ---- ledge edge-hog (#311, grounded by #297) ----
    "LEDGE_INVULN_BASE_FRAMES": Provenance(
        23, "frames", "Brawl ledge-grab intangibility baseline 23f (SmashWiki:Ledge; #297)", "FOUND", 311
    ),
    "LEDGE_INVULN_PER_PERCENT": Provenance(
        0.3,
        "frames/%",
        "pycats percent-scaling of ledge invincibility; PM is per-character, no single canon curve",
        "TUNED",
        311,
    ),
    "LEDGE_INVULN_MAX_FRAMES": Provenance(
        60, "frames", "pycats cap on the ledge-invincibility burst (~1s); no canon value", "TUNED", 311
    ),
    "LEDGE_GETUP_FRAMES": Provenance(
        16,
        "frames",
        "pycats neutral ledge-getup climb window (edge frees at half); PM getup frames are per-character",
        "TUNED",
        311,
    ),
}

# The curated combat/physics set (excludes render/UI/tail/platform/menu constants).
# This is an INDEPENDENT hand-maintained list — NOT derived from TUNING_PROVENANCE —
# so the "no orphans" drift-guard can actually fail: add a constant to config + this
# set but forget the registry row (or vice versa) and the test reds. Adding a tuning
# constant to config forces both a name here and a row above.
TUNING_CONSTANT_NAMES: frozenset[str] = frozenset(
    {
        "GRAVITY",
        "MAX_FALL_SPEED",
        "MOVE_SPEED",
        "JUMP_VEL",
        "PX_PER_UNIT",
        "DASH_SPEED",
        "MAX_JUMPS",
        "SMASH_CHARGE_FRAMES",
        "SMASH_CHARGE_SCALE",
        "DODGE_FRAMES",
        "DODGE_TIME",
        "DODGE_SPEED",
        "DODGE_AIR_SPEED",
        "WAVEDASH_ANGLE_DEG",
        "WAVEDASH_LANDING_LAG",
        "JOSTLE_MIN_VOVERLAP_FRAC",
        "SHIELD_BREAK_STUN_MAX",
        "SHIELD_BREAK_STUN_MIN",
        "SHIELDSTUN_FACTOR",
        "SHIELD_MAX_HP",
        "SHIELD_DRAIN_PER_FRAME",
        "HITSTUN_MULTIPLIER",
        "HITSTUN_FLOOR",
        "HITLAG_DAMAGE_FACTOR",
        "HITLAG_BASE",
        "HITLAG_CAP",
        "KNOCKBACK_LAUNCH_FACTOR",
        "KNOCKBACK_DECAY",
        "SAKURAI_ANGLE_CODE",
        "SAKURAI_AIRBORNE_DEG",
        "SAKURAI_GROUNDED_MAX_DEG",
        "SAKURAI_GROUNDED_LOW_KB",
        "SAKURAI_GROUNDED_HIGH_KB",
        "CROUCH_CANCEL_FACTOR",
        "KNOCKDOWN_VY_THRESHOLD",
        "KNOCKDOWN_PRONE_FRAMES",
        "GETUP_ROLL_FRAMES",
        "GETUP_ROLL_SPEED",
        "CLANK_PRIORITY_RANGE",
        "LEDGE_INVULN_BASE_FRAMES",
        "LEDGE_INVULN_PER_PERCENT",
        "LEDGE_INVULN_MAX_FRAMES",
        "LEDGE_GETUP_FRAMES",
    }
)
