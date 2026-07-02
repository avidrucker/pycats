# Nalio fireball trajectory + spawn height + hurtbox — findings (#263)

> Research findings (#263). Investigates why Nalio's fireball appears to "sail over"
> grounded foes (surfaced during #254 threat-aware shielding). **Findings only — no
> code.** Spec-first: root-causes the symptom in code + sources the *correct* PM model,
> so a follow-up DEV can implement with a clear target.
>
> Code grounded against `pycats/entities/attack.py`, `pycats/entities/player.py`,
> `pycats/combat/geometry.py`, `pycats/characters/nalio_cat.py`, `pycats/config.py` at
> HEAD. Date: 2026-06-30. Agent: FIG. Area: `area:combat`.

## TL;DR — the premise was wrong; it's a *trajectory-model* gap, not a height bug

The #263 parent observation guessed a **spawn-height bug** (and tied it to the
guessed-values trackers #192/#195). **That is disproven.** Three findings, all
grounded in a real loop:

1. **No spawn-height bug.** The fireball spawns at the **thrower's body-centre**.
   `Circle(dx=50, dy=30, r=19)` resolves via `resolve_circle` to `cy = rect.top + 30`;
   `PLAYER_SIZE = (40, 60)` → `rect.top = centre − 30`, so `cy = centre`. Correct.
2. **Hurtbox / `process_hits` is correct.** A **same-elevation** fireball **connects** —
   verified: p2 took **7% damage** (the fireball's authored `damage`) from a flat shot
   at equal height. The circle-vs-hurtbox detection works.
3. **The "whiff" is a cross-elevation artifact of *flat* travel.** Both fighters
   **spawn on the thin platforms** (`Rect(205,290,…)` / `Rect(605,290,…)` → grounded
   centre **cy≈260**); during combat one drops to the **main platform**
   (`Rect(80,410,800,80)` → grounded centre **cy≈380**). A **flat** projectile fired
   at cy≈260 from the higher thrower then flies ~120px **over** a target standing on
   the lower platform. Geometrically expected for a flat projectile — not a bug in
   spawn or hit detection.

**The real gap:** pycats shipped the fireball as **flat travel** (#223, explicitly
"minimal moving projectile (flat travel)"). But Nalio is the **PM *Mario* archetype**
([[cat-archetype-naming]] / [[pm36-canonical-reference]]), and **Mario's fireball is
gravity-affected and bounces along the ground** — it descends to lower terrain and
follows slopes. Flat travel is **Luigi's** fireball, not Mario's. So Nalio's projectile
currently behaves like the wrong character, and that mismatch is what makes it sail
over lower foes. The fix is a **trajectory model** (gravity + ground-bounce), not a
spawn-height or PX_PER_UNIT tweak.

## Root-cause walkthrough (grounded)

**Spawn position.** `player.py` spawns the projectile `Attack(self, hitboxes=tick.spawn,
velocity=(facing*projectile_speed, 0), …)`. `Attack.__init__` resolves each circle once
from `owner.rect.(x,y)` top-left via `resolve_circle` (`combat/geometry.py`):
`cy = origin_y + dy`. With `dy=30` and a 60px-tall body, that's the owner's vertical
centre — correct. `velocity=(±10, 0)` → **purely horizontal**, no vertical component.

**Flight.** `Attack.update` advances the resolved circles + `hit_cx/hit_cy` by
`velocity` each frame; `cy` never changes (vy=0). So the fireball holds the **thrower's
launch height for its whole life**, regardless of the target's elevation or the terrain.

**Measured (real loop, `process_hits` active):**
- Both idle at default spawn → both grounded at **cy=260** (thin platforms).
- Same-platform throw at equal height → **hit, +7% on the target** (hurtbox OK).
- Thrower on thin plat (cy 260) vs target dropped to main plat (cy 380) → fireball
  flies at cy=260 across the whole stage, `|Δy|≈120` > the body half-height (30) +
  radius (19) → **never overlaps** the lower hurtbox → clean whiff. Correct for a flat
  projectile; wrong for a Mario fireball, which would arc/bounce down to it.

So: **spawn height ✅, hit detection ✅, trajectory model ❌ (flat, should arc+bounce).**

## How a Mario fireball *should* move (sourced)

SmashWiki (*Fireball*), Mario:
- **Gravity + bounce:** *"The fireballs fall down until they hit the ground, which will
  cause them to bounce off of the ground"*; they *"bounce a few times before
  disappearing completely,"* **losing momentum** each bounce.
- **Terrain-following:** *"The fireball's trajectory changes according to the stage's
  surface angle upon contact"*; firing *"from higher locations and toward downward
  slopes"* makes them travel further; *"firing at a wall or upward slope, the balls
  will bounce backward."*
- **Contrast — Luigi (= today's pycats model):** *"they travel in a straight line,
  being unaffected by gravity"* rather than *"rolling and bouncing along the ground
  like Mario's."*

So the PM-faithful Nalio fireball is a **gravity-affected, ground-bouncing** projectile
that descends toward and along lower terrain — which would naturally reach a foe on the
main platform below the thin platforms. No source gives Mario's exact gravity / bounce
count / momentum-loss / per-bounce-speed numbers → those are **tuning guesses** (flag
them, per #148 discipline). **Provenance:** SmashWiki only; **no PM-specific source**
(PM is Brawl-derived for this, consistent with #48/#148/#24).

## Recommended DEV decomposition (file one at a time, per RULES)

1. **DEV: gravity + ground-bounce projectile (PM-faithful).** *(recommended; the
   substantive fix.)* Give the projectile `Attack` a vertical model: a downward
   `gravity` accel on its velocity, and a **bounce** off platform tops (reflect vy,
   scale by a restitution < 1 so it loses momentum), bounded to a few bounces /
   `projectile_lifetime`. This needs **projectile-vs-platform collision** (the
   projectile currently ignores platforms — `Attack.update` only integrates velocity).
   Numbers (gravity, restitution, launch vy, max bounces) are `⚠ GUESS` starting
   points to playtest. Makes Nalio's fireball reach lower targets and behave like
   Mario.
2. **DEV (optional, smaller): minimal downward arc.** If full bounce is too big a
   slice, ship a constant downward `vy` (gravity only, no bounce) so the fireball
   descends toward lower platforms — partial faithfulness, cheaper. Treat as an
   interim, not the end state.
3. **No-op alternative — keep flat travel.** Only correct if Nalio's fireball is
   *intended* to be the Luigi (flat) model. Given Nalio = PM Mario, this is wrong
   long-term; if chosen, **document it** so the cross-elevation whiff isn't re-reported
   as a bug.

**AI follow-on (not part of this ticket):** once the projectile arcs/bounces, the
threat-aware shield's vertical band (`shield_threat_dy`, #254) should track the
projectile's *actual* y-trajectory rather than assume a flat threat — a small refine
under #250 when the trajectory lands.

## Golden-safety & test impact

- The **default (level-less) controller has no `specials`** → never throws a fireball,
  so the `full_match` golden has **no projectile** and a trajectory change is
  **golden-safe** for it. (Verify with the suite + `git status tests/golden/` when the
  DEV lands.)
- `tests/test_cpu_difficulty.py::test_lv9_nalio_throws_fireball_in_battle…` asserts a
  fireball **spawns**, not its path → unaffected by a trajectory change.
- A bounce/gravity model wants its **own** regression tests (descends over a frame
  window; bounces off a platform top; hits a lower-platform target; loses momentum;
  expires after N bounces / lifetime). All expressible in the existing headless
  `attacks.update()` + `process_hits` loop (this doc's repro pattern).

## Caveats & gaps

- **No PM-specific fireball source** — Brawl/SmashWiki-derived only; PM-exactness
  confidence low by provenance.
- **No numeric trajectory data** (gravity, bounce count, momentum loss, per-bounce
  speed) in any source — all DEV numbers are tuning guesses, not measured PM values.
- The current `projectile_speed=10` / `projectile_lifetime=73` remain GUESSES
  ([[rukaidata-engine-hardcoded-limit]]; nalio_cat.py comment) — orthogonal to the
  trajectory model but worth deriving alongside (relates to PX_PER_UNIT #195, distinct
  from this ticket).
- This investigation **disproves** the #263-parent guess that the symptom is a
  spawn-height bug tied to #192/#195 — it's the flat-vs-bounce trajectory model.

## Sources

| Source | Quality | Gives |
|---|---|---|
| [SmashWiki — Fireball](https://www.ssbwiki.com/Fireball) | secondary (authoritative community) | Mario fireball = gravity + ground-bounce + terrain-follow; bounces a few times losing momentum; Luigi = flat/straight contrast |
| `pycats/entities/attack.py` (`resolve`, `update`) | primary (repo) | spawn at owner top-left + `dy`; velocity-only integration (vy=0 → flat) |
| `pycats/combat/geometry.py` (`resolve_circle`) | primary (repo) | `cy = origin_y + dy` → fireball at body centre (no height bug) |
| `pycats/entities/player.py` (projectile spawn) | primary (repo) | `velocity=(facing*speed, 0)`; horizontal-only |
| `pycats/config.py` (`PLAYER_SIZE`, platforms via `build_stage`) | primary (repo) | 60px body; thin plats cy≈260 vs main plat cy≈380 (the cross-elevation source) |
| Real headless repro (`attacks.update` + `process_hits`) | primary (this session) | same-level hit = +7%; cross-elevation flat whiff at Δy≈120 |
| #223 (closed) / `docs/research/nalio-fireball-scoping-findings.md` | primary (repo) | the deliberate flat-travel simplification this revisits |
