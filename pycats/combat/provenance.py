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

Scope: the combat/physics **tuning scalars** in `config.py`. A tuning scalar that
lives elsewhere is RELOCATED into `config.py` to bring it under this drift-guard,
not left unguarded for living in the wrong module — e.g. #1135 moved the friction
dead-zone (`VEL_DEADZONE`) and the dodge edge-safety margin
(`DODGE_MIN_PLATFORM_OVERLAP_PX`) here from `core/physics.py`. Excluded by
construction (they are not tuning scalars, and location is not why): render/UI,
cat-feature, tail-physics, platform, and menu constants (no provenance noise on
`BG_COLOR`), and incidental implementation slop such as float-comparison tolerances
(`core.physics.PLATFORM_STAND_TOLERANCE_PX`). Per-character/per-move data in
`characters/*.py` has its OWN parallel registry — the #1133 value-status seam
(`FieldStatus`/`Status` maps in `combat/data.py`), carried into `characters/data/*.json`.

`status` values: FOUND (traced to a cited canon value), GUESS (unsourced /
playtest starting point — the #319 value-sourcing pass resolves these),
TUNED (deliberate design value, not seeking canon), DIVERGENCE (intentional
departure from a known canon value).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Provenance:
    value: (
        int | float | tuple[int, int]
    )  # MUST equal the live config constant (C4 anchor); tuple for size pairs e.g. PLAYER_SIZE (#598)
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
    "MAX_JUMPS": Provenance(
        2,
        "jumps",
        "Mario/PM jump count: 1 ground + 1 midair = 2 (standard 2-jump character; SmashWiki:Mario_(PM))",
        "FOUND",
        None,
    ),
    # ---- smash charge (#327 slice 3 / #599, PM-specific; supersedes #581/#426) ----
    "SMASH_CHARGE_FRAMES": Provenance(
        59,
        "frames",
        'PM smash charge ramp = 59 frames. ⚠ primary-unconfirmed: single secondary (SmashWiki:Project_M "59 frames as opposed to 60"), contradicted by SmashWiki:Smash_attack (60, all games); cap is engine-hardcoded so brawllib_rs has none — a PM DOL/RAM dump is the only primary (see #626). Supersedes the base-game 60 #581 registered.',  # noqa: E501
        "FOUND",
        599,
    ),
    "SMASH_CHARGE_SCALE": Provenance(
        1.3671,
        "factor",
        'PM full-charge damage multiplier = 1.3671, Melee value restored in PM. [primary] meleelight (Melee reimpl, clone #616) hardcodes 1 + chargeFrames*(0.3671/60) → 1.3671 at cap; [secondary] SmashWiki:Project_M "deals x1.3671". Supersedes #581 Brawl-era 1.4.',  # noqa: E501
        "FOUND",
        599,
    ),
    # ---- dodges / rolls ----
    "DODGE_FRAMES": Provenance(
        15, "frames", "roll intangibility window; playtest starting point (tracked #65)", "GUESS", 65
    ),
    "DODGE_TIME": Provenance(14, "frames", "roll duration; playtest starting point (tracked #65)", "GUESS", 65),
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
    # ---- fighter-vs-fighter ground jostle (#1/#1020, ADR-0012) ----
    # Raw Smash units (config holds the unit; core/physics.py derives px via units.u()).
    # SECONDARY proxy: meleelight is a faithful reimplementation, NOT the retail ROM; the
    # exact retail Melee/Brawl/PM 3.6 magnitude is ⚠ UNDOCUMENTED (engine global, not
    # per-move script data). Direct source literals → no derivation.
    "JOSTLE_TRIGGER_UNITS": Provenance(
        6.5,
        "unit",
        "meleelight @27af171 src/physics/physics.js `if (diff < 6.5 && diff > 0)` (SECONDARY proxy; retail PM 3.6 magnitude UNDOCUMENTED)",  # noqa: E501
        "FOUND",
        1020,
    ),
    "JOSTLE_PUSH_UNITS": Provenance(
        0.3,
        "unit",
        "meleelight @27af171 src/physics/physics.js `pos.x += sign(...) * -0.3` (SECONDARY proxy; retail PM 3.6 magnitude UNDOCUMENTED)",  # noqa: E501
        "FOUND",
        1020,
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
    # ---- knockback formula coefficients (#39 §2 / #1135) ----
    # Fixed terms of the canonical Brawl/PM knockback equation
    # (SmashWiki:Knockback; the formula lives in combat/knockback.py). FOUND — these
    # are the formula, not tuning knobs; changing one departs from Smash canon.
    "KB_PERCENT_DIVISOR": Provenance(
        10.0, "factor", "SmashWiki:Knockback — the p/10 percent term (spec #39 §2)", "FOUND", 1135
    ),
    "KB_PERCENT_DAMAGE_DIVISOR": Provenance(
        20.0, "factor", "SmashWiki:Knockback — the p*d/20 percent-damage term (spec #39 §2)", "FOUND", 1135
    ),
    "KB_WEIGHT_NUMERATOR": Provenance(
        200.0, "factor", "SmashWiki:Knockback — the 200/(w+100) weight-ratio numerator (spec #39 §2)", "FOUND", 1135
    ),
    "KB_WEIGHT_OFFSET": Provenance(
        100.0, "factor", "SmashWiki:Knockback — the w+100 weight offset (spec #39 §2)", "FOUND", 1135
    ),
    "KB_GROWTH_SCALE": Provenance(
        1.4, "factor", "SmashWiki:Knockback — the ×1.4 growth scale (spec #39 §2)", "FOUND", 1135
    ),
    "KB_GROWTH_BASE": Provenance(
        18.0, "factor", "SmashWiki:Knockback — the +18 base term (spec #39 §2)", "FOUND", 1135
    ),
    "KB_KBG_DIVISOR": Provenance(
        100.0, "factor", "SmashWiki:Knockback — the KBG/100 growth-percent→factor divisor (spec #39 §2)", "FOUND", 1135
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
    "LEDGE_INTANGIBLE_BASE_FRAMES": Provenance(
        21, "frames", "PM 3.6 CliffCatch intangibility 1-21, flat across characters (rukaidata; #671)", "FOUND", 683
    ),
    "LEDGE_REGRAB_INTANGIBLE_CUTOFF": Provenance(
        5,
        "grabs",
        'PMDT 3.5 primary: "After a character regrabs the ledge five times without touching the ground, that character no longer receives intangibility for grabbing the ledge again" — grabs 1..5 grant the full burst, grab 6+ only the residual (#656, ratified #670). The COUNT is primary-sourced; the post-cutoff residual (LEDGE_POST_CUTOFF_RESIDUAL_FRAMES) is a separate acknowledged gap, deliberately unregistered.',  # noqa: E501
        "FOUND",
        670,
    ),
    "LEDGE_GETUP_FRAMES": Provenance(
        16,
        "frames",
        "pycats neutral ledge-getup climb window (edge frees at half); PM getup frames are per-character",
        "TUNED",
        311,
    ),
    # ---- Pass B: guessed/tuned scalars (#582, from the #580 audit) — candid GUESS/TUNED, no fabricated sourcing ----
    # projectile physics (#266/#425) — flagged ⚠ GUESS tuning starting points in config
    "PROJECTILE_GRAVITY": Provenance(
        0.5,
        "px/frame^2",
        "pycats projectile fall accel; GUESS tuning start (config ⚠, #266/#425), no PM source",
        "GUESS",
        266,
    ),
    "PROJECTILE_RESTITUTION": Provenance(
        0.6,
        "factor",
        "pycats projectile bounce energy kept (<1); GUESS tuning start (config ⚠, #266/#425)",
        "GUESS",
        266,
    ),
    "PROJECTILE_MAX_BOUNCES": Provenance(
        3, "bounces", "pycats projectile bounces before despawn; GUESS (config ⚠, #266/#425)", "GUESS", 266
    ),
    # walk/dash burst (#388) — DASH_SPEED is FOUND (#581); the burst window is a guess
    "DASH_DURATION": Provenance(
        12,
        "frames",
        "pycats initial-dash burst window; GUESS tuning start (config ⚠, #388), no canon single value",
        "GUESS",
        388,
    ),
    "DOUBLE_TAP_WINDOW": Provenance(
        8,
        "frames",
        "pycats double-tap dash window: frames after a fresh directional press in which a second same-direction press fires the dash (#388 slice 2b / #403); GUESS tuning start (config ⚠, ~8-10f), no canon single value",  # noqa: E501
        "GUESS",
        403,
    ),
    # angled f-smash literals (#327 slice 4) — flagged ⚠ playtest in config
    "FSMASH_ANGLE_UP": Provenance(
        50,
        "deg",
        "pycats angled-fsmash up-forward launch angle; GUESS (config ⚠ playtest, #327), no canon value",
        "GUESS",
        327,
    ),
    "FSMASH_ANGLE_DOWN": Provenance(
        330,
        "deg",
        "pycats angled-fsmash down-forward launch angle (-30deg); GUESS (config ⚠ playtest, #327)",
        "GUESS",
        327,
    ),
    # friction model — pycats-specific design knobs, no PM canon number
    "GROUND_FRICTION": Provenance(
        0.5,
        "factor",
        "pycats ground friction (1.0=ice, 0.0=instant stop); deliberate design knob, no PM equivalent",
        "TUNED",
        None,
    ),
    "AIR_FRICTION": Provenance(
        0.85, "factor", "pycats air friction; deliberate design knob, no PM equivalent", "TUNED", None
    ),
    # friction dead-zone + dodge edge-safety — relocated from core/physics.py to config
    # so this registry covers them (#1135); both pycats-specific, no PM canon.
    "VEL_DEADZONE": Provenance(
        0.05,
        "px/frame",
        "pycats horizontal-velocity dead-zone: |vel.x| below this snaps to 0 after friction so a fighter stops instead of creeping; pycats implementation threshold, no PM equivalent",  # noqa: E501
        "TUNED",
        1135,
    ),
    "DODGE_MIN_PLATFORM_OVERLAP_PX": Provenance(
        25,
        "px",
        "pycats dodge-off-ledge safety margin: a roll/dodge is cancelled if it would leave less than this body-overlap on the platform; pycats edge-safety rule, no PM equivalent",  # noqa: E501
        "TUNED",
        1135,
    ),
    # misc timers / match rules — pycats design, no canon
    "HURT_TIME": Provenance(
        12, "frames", "pycats hurt/flinch timer; deliberate design value, no PM canon equivalent", "TUNED", None
    ),
    "LEDGE_REGRAB_LOCKOUT_FRAMES": Provenance(
        30,
        "frames",
        "pycats post-release regrab-suppression window; pycats ledge rule (#14), no canon single value",
        "TUNED",
        14,
    ),
    "PLAYER_ATTACK_DURATION": Provenance(
        12, "frames", "pycats default attack duration; deliberate design value, no PM canon", "TUNED", None
    ),
    "INITIAL_LIVES": Provenance(
        3, "stocks", "pycats default stock count; a match ruleset setting, not a PM physics value", "TUNED", None
    ),
    "RESPAWN_DELAY_FRAMES": Provenance(
        120, "frames", "pycats respawn freeze ~2s (config computes int(2*FPS)); ruleset value, no canon", "TUNED", None
    ),
    # ---- Pass B: #584-ratified collision/rule constants (#598) — TUNED, no PM canon ----
    "PLAYER_SIZE": Provenance(
        (40, 60),
        "px",
        "pycats default fighter collision box (Fighter.__init__ reads stand_size or PLAYER_SIZE); reclassified render->collision per #584, no PM-mapped dimension",  # noqa: E501
        "TUNED",
        584,
    ),
    "LEDGE_CATCH_W": Provenance(
        24, "px", "pycats ledge-grab catch-region width off the edge corner; pycats geometry, no canon", "TUNED", 584
    ),
    "LEDGE_CATCH_H": Provenance(
        64, "px", "pycats ledge-grab catch-region height below the lip; pycats geometry, no canon", "TUNED", 584
    ),
    "BLAST_PADDING": Provenance(
        50, "px", "pycats KO boundary = px beyond the screen edge; pycats stage rule, no canon", "TUNED", 584
    ),
    "BLAST_PADDING_TOP": Provenance(
        150,
        "px",
        "pycats TOP KO boundary = BLAST_PADDING + 100; owner design decision (Avi 2026-07-20) raising the top blast line 100px above the bottom, no canon",  # noqa: E501
        "TUNED",
        823,
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
        "JUMP_VEL",
        "PX_PER_UNIT",
        "MAX_JUMPS",
        "SMASH_CHARGE_FRAMES",
        "SMASH_CHARGE_SCALE",
        "DODGE_FRAMES",
        "DODGE_TIME",
        "DODGE_SPEED",
        "DODGE_AIR_SPEED",
        "WAVEDASH_ANGLE_DEG",
        "WAVEDASH_LANDING_LAG",
        "JOSTLE_TRIGGER_UNITS",
        "JOSTLE_PUSH_UNITS",
        "SHIELD_BREAK_STUN_MAX",
        "SHIELD_BREAK_STUN_MIN",
        "SHIELDSTUN_FACTOR",
        "SHIELD_MAX_HP",
        "SHIELD_DRAIN_PER_FRAME",
        # knockback-formula coefficients (#39 §2 / #1135)
        "KB_PERCENT_DIVISOR",
        "KB_PERCENT_DAMAGE_DIVISOR",
        "KB_WEIGHT_NUMERATOR",
        "KB_WEIGHT_OFFSET",
        "KB_GROWTH_SCALE",
        "KB_GROWTH_BASE",
        "KB_KBG_DIVISOR",
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
        "LEDGE_INTANGIBLE_BASE_FRAMES",
        "LEDGE_REGRAB_INTANGIBLE_CUTOFF",
        "LEDGE_GETUP_FRAMES",
        # Pass B guessed/tuned scalars (#582)
        "PROJECTILE_GRAVITY",
        "PROJECTILE_RESTITUTION",
        "PROJECTILE_MAX_BOUNCES",
        "DASH_DURATION",
        "DOUBLE_TAP_WINDOW",
        "FSMASH_ANGLE_UP",
        "FSMASH_ANGLE_DOWN",
        "GROUND_FRICTION",
        "AIR_FRICTION",
        "VEL_DEADZONE",
        "DODGE_MIN_PLATFORM_OVERLAP_PX",
        "HURT_TIME",
        "LEDGE_REGRAB_LOCKOUT_FRAMES",
        "PLAYER_ATTACK_DURATION",
        "INITIAL_LIVES",
        "RESPAWN_DELAY_FRAMES",
        # Pass B #584-ratified collision/rule constants (#598)
        "PLAYER_SIZE",
        "LEDGE_CATCH_W",
        "LEDGE_CATCH_H",
        "BLAST_PADDING",
        "BLAST_PADDING_TOP",
    }
)


# --- status views (#643) ------------------------------------------------------
# The registry is the single source of truth for value status; these are filters
# over it, not a second store. "what do we knowingly diverge on / haven't sourced?"
# is a query:  divergences()  (knowing canon departures),  debt()  (unsourced GUESS).
# TUNED is a settled design choice — deliberately not a "divergence".


def by_status(*statuses: str) -> dict[str, Provenance]:
    """Registry rows whose `status` is one of `statuses`
    (e.g. ``by_status("DIVERGENCE", "GUESS")``)."""
    wanted = set(statuses)
    return {name: prov for name, prov in TUNING_PROVENANCE.items() if prov.status in wanted}


def divergences() -> dict[str, Provenance]:
    """Values that knowingly depart from a canon value (DIVERGENCE) — the audit-risk list."""
    return by_status("DIVERGENCE")


def debt() -> dict[str, Provenance]:
    """Unsourced values (GUESS) awaiting a sourcing pass (#319) — the grounding-debt list."""
    return by_status("GUESS")
