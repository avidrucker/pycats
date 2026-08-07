# Post-KO respawn timer + on-screen display treatment — findings (#1310)

> **Agent:** FIG · **Authored:** 2026-08-07 · **Ticket:** #1310
>
> Canon = **Project M 3.6** (Brawl lineage; PM restored much Melee behavior). Two prior docs
> already source the *revival-platform invincibility model* deeply — this doc does **not** re-derive
> them; it cites them and adds the two pieces they leave open: **(A)** the KO→re-entry **delay** (how
> many seconds a KO'd fighter is gone), and **(B)** the on-screen **display** treatment as a HUD
> design recommendation.
>
> **One-line answer.** A KO'd fighter is off under player control for roughly **~2.5 s** in the
> Melee-lineage engine (≈61 f blast-off + ≈91 f platform descent), then stands **intangible** on a
> revival platform (up to a **300 f / 5 s** timeout), then leaves with **120 f / 2 s** of descent
> invincibility. pycats today collapses all of this into a single invisible **120 f / 2 s** freeze
> (`RESPAWN_DELAY_FRAMES`) with no platform, no intangibility, and no invincibility. Smash never shows
> a **numeric countdown**; the on-screen convention is the **platform + a blink/flicker on the
> character**, plus a persistent **stock indicator** — the recommended pycats HUD default keeps the
> existing `Lives:` text and adds the already-scoped invincibility **blink**, deferring the platform
> render to its existing epic.

## Read this before citing — prior art + source tiers

Two prior findings docs are the design-of-record for the *invincibility model*; this doc is downstream
of them and does not restate their derivations:

- [`2026-07-03-pm-spawn-respawn-mechanics.md`](./2026-07-03-pm-spawn-respawn-mechanics.md) (#480) —
  reporter-ratified **full-PM revival-platform model**: intangible on platform, platform auto-vanish
  **300 f / 5 s**, post-leave invincibility **120 f / 2 s**, grounded-on-platform jump rule.
  Implementation is epic **#482**.
- [`2026-07-21-respawn-invincibility-validation-findings.md`](./2026-07-21-respawn-invincibility-validation-findings.md)
  (#830) — validated the invincibility: **120 f flat**, acting does **not** truncate the post-drop
  window, and it renders as a **blink/flicker**, not a solid tint (faithful blink deferred to epic
  **#558**).

| Tier | Source | What it gives here |
|---|---|---|
| **Primary reimplementation (Melee)** | **meleelight** — faithful Melee engine reimpl in JS (`~/Documents/Study/JavaScript/meleelight/`, local clone #616), the same primary the #830 doc used | The **DEAD→REBIRTH→REBIRTHWAIT** state machine and its literal frame thresholds — the source of the pre-platform **delay** numbers below. |
| **Secondary — series-universal** | **SmashWiki** — [Revival platform](https://www.ssbwiki.com/Revival_platform), [Invincibility](https://www.ssbwiki.com/Invincibility), [Star KO](https://www.ssbwiki.com/Star_KO), [Respawn](https://www.ssbwiki.com/Respawn) (verified 2026-08-07) | The platform timeout (5 s), the 120 f post-drop window, and the only secondary anchor for the pre-platform delay (Star KO "about 2 seconds"). |
| **pycats as-is** | `pycats/config/stage.py`, `pycats/entities/fighter.py`, `pycats/combat/provenance.py`, `pycats/render/hud.py` | What the code does today (the gap being sized). |

**Tiering caveat (carried from #830).** meleelight is a **Melee** reimplementation, so Melee→PM is an
`[inference]` — PM 3.6 restored much Melee behavior, which makes it strong but not a PM-3.6 primary
quote. SmashWiki's respawn coverage is **series-universal** (Brawl, PM's base, included) and never
names a per-game pre-platform delay. So the **delay** numbers are **FOUND-by-engine** (Melee reimpl),
PM `[inference]`; the platform/invincibility numbers are **FOUND** (SmashWiki + engine agree).

---

## (A) Timing

### A1 — The canonical KO→re-entry timeline (Melee-lineage engine)

The engine runs the post-KO fighter through three states before it is a controllable, vulnerable
fighter again. Frame thresholds are read from meleelight's shared state logic:

| Phase | Engine state | Duration | Player control? | Vulnerable? | Source |
|---|---|---|---|---|---|
| Blast-off / gone | `DEAD{UP,DOWN,LEFT,RIGHT}` | **~61 f (~1.0 s)** | no | n/a (off-stage) | `DEADUP.js` `interrupt()` — **FOUND-by-engine** |
| Platform descent | `REBIRTH` | **~91 f (~1.5 s)** | no | intangible | `REBIRTH.js` `interrupt()` — **FOUND-by-engine** |
| On platform (waiting) | `REBIRTHWAIT` | up to **300 f (5 s)** timeout, or ends on any action | **yes** | **intangible** | `REBIRTHWAIT.js` `interrupt()` — **FOUND** (engine + SmashWiki) |
| Descent after leaving | `FALL`/aerial/etc. | **120 f (2 s)** invincible | yes | **invincible** (not intangible) | `REBIRTHWAIT.js` grants `invincibleTimer = 120` on every leave-path — **FOUND** (#830) |

Verbatim engine evidence (meleelight, shared moves):

- **`DEADUP.js` `interrupt()`:** `if (player[p].timer > 60){ … REBIRTH.init(…) }` — the fighter is in the
  DEAD state for **~61 frames** before moving to the revival platform. (`percent` is zeroed on entry;
  the fighter is off-screen and uncontrollable.)
- **`REBIRTH.js` `init()` / `interrupt()`:** spawns at `respawnPoints[p].y + 135` with `cVel.y = -1.5`
  (descending onto the platform), then `if (player[p].timer > 90){ … REBIRTHWAIT.init(…) }` — the
  descent phase is **~91 frames**.
- **`REBIRTHWAIT.js` `interrupt()`:** `else if (player[p].spawnWaitTime > 300){ … invincibleTimer = 120;
  FALL.init(…) }` — a **300 f / 5 s** inaction timeout; and **every** leave-path (aerial, air-dodge
  `l`/`r`, double-jump, special, a `>0.3` stick tilt, or the timeout) sets `invincibleTimer = 120`.

So **KO → back under control (intangible, on the platform)** is roughly **61 + 91 ≈ 152 f ≈ 2.5 s**;
the fighter then chooses when to leave (immediately, or up to 5 s later), and carries **2 s** of
invincibility down from the platform.

SmashWiki, verbatim, corroborates the platform-and-after numbers (series-universal sections):

- Revival platform: *"If the player does not act, the platform will disappear by itself after 5
  seconds"*; *"The revived character is intangible the entire time they are on the platform"*; *"After
  dropping down from the platform, the character has a further period of invincibility (2 seconds, or
  120 frames)."*
- Invincibility table: respawn invincibility **120 frames** in SSB, Melee, Brawl, and SSB4 (Ultimate
  is the outlier at 60–120, scaled by wait time — **not** adopted, per #480/#830).

**The pre-platform delay (~2.5 s) has no SmashWiki verbatim.** SmashWiki never states a per-game
KO→platform delay; its only adjacent number is [Star KO](https://www.ssbwiki.com/Star_KO) *"often last
about 2 seconds,"* and it notes a Star/Screen KO is **slower** to recover from than an ordinary blast
KO. So treat the ~2.5 s as **FOUND-by-engine** (Melee reimpl; PM `[inference]`), with the Star-KO ~2 s
as a rough, KO-type-dependent secondary anchor — **not** a single canonical constant.

### A2 — pycats today vs the canon

`pycats/config/stage.py`: `RESPAWN_DELAY_FRAMES = int(2 * FPS)` = **120 f / 2 s** — a single invisible
freeze. `pycats/combat/provenance.py` registers it **TUNED**: *"pycats respawn freeze ~2s … ruleset
value, no canon."* On expiry, `Player._handle_death_and_freezes` → `reset_to_spawn` drops the fighter
**airborne** from `START_Y` with **no** platform, **no** intangibility, and **no** invincibility
(`Fighter.reset_to_spawn` even clears `invincible_timer` to 0). The `invincible_timer` machinery (#802)
exists and is honored by tangibility, but **nothing sets it to a nonzero value on respawn** — the
respawn-invincibility grant is unimplemented.

| Aspect | PM / Melee (sourced) | pycats now | Provenance of the target |
|---|---|---|---|
| KO → controllable again | ~152 f / ~2.5 s (DEAD 61 + REBIRTH 91) | 120 f / 2 s single freeze | FOUND-by-engine; PM `[inference]` |
| Structure of the delay | off-screen → **visible platform descent** | one invisible freeze, then airborne drop | FOUND-by-engine |
| On-platform intangibility | yes, until action or 300 f | none | FOUND (#480/#830) |
| Post-leave invincibility | 120 f / 2 s, flat, not truncated by acting | none (cleared to 0) | FOUND (#830) |
| Platform auto-vanish | 300 f / 5 s | n/a (no platform) | FOUND (#480) |
| Numeric on-screen countdown | **none** (not a Smash convention) | none | FOUND (absence — see B) |

**Reading of the gap.** pycats' 2 s freeze is close to the ~2.5 s engine total in *wall-clock*, but it
models the delay as a single hidden pause rather than the two-phase off-screen→platform sequence, and
it omits the intangibility + invincibility windows entirely. Those three gaps are already owned by epic
**#482** (revival-platform model) and its slice **#506** (respawn invincibility) — this doc does not
re-open them. The one **timing** value in scope for a standalone change is whether the bare freeze
should be re-labelled/re-sized against the ~2.5 s engine figure; that is a design call, not a physics
fact, and belongs to #482 when the platform lands (the freeze is subsumed by the DEAD+REBIRTH phases).

**No number is changed by this doc.** Per the repo's "changing a game value needs a basis" rule, the
sourced figures above are recorded as findings (FOUND / FOUND-by-engine); any edit to
`RESPAWN_DELAY_FRAMES` or a new invincibility-duration constant is a downstream DEV change under #482 /
#506, not part of this research.

## (B) Display — how the respawn state should look

Smash's on-screen respawn language is **spatial and animated, not numeric**: a floating platform, a
flashing character, and a persistent stock count. There is **no numeric respawn countdown** anywhere in
the series (the only visualized timer is Smash 4's platform edge fading yellow→red as its 5 s runs out —
still not a number). Options, each with its convention and pycats fit:

| Option | Smash/PM convention | pycats today | Cost to add |
|---|---|---|---|
| **Numeric countdown timer** | **Not a Smash convention** — the series never shows "3… 2… 1". | none | low, but a **divergence** — recommend against |
| **Revival platform** | Canonical: fighter reappears standing on a translucent floating platform, top-centre; player drops off when ready (SmashWiki Revival platform) | none | **high** — a new spawned platform entity + descent/drop-off control; owned by epic **#482** |
| **Invincibility flash (blink/flicker)** | Canonical: the respawning fighter **blinks** during the 120 f window; meleelight toggles body colour on a **~9 f period** (`render.js` `% 9 > 3`), i.e. blink, not solid tint (#830 Q3) | none (`invincible_timer` never set) | **low–medium** — a render tint/blink keyed on `invincible_timer`; faithful flicker already scoped in epic **#558** |
| **Stock / lives indicator** | Canonical: persistent stock icons (head icons) or a count, always on-screen | **present** — HUD draws `Lives: N` text (`pycats/render/hud.py` `_emphasis_lines`) | none (already shipped) |

### Recommended default HUD treatment

**Ranked, with tradeoffs:**

1. **Keep the existing `Lives:` text as the stock indicator (ship as-is).** It already answers "how many
   lives left," which is the information a player checks during a respawn. Head-icon art is a nicety, not
   a requirement, and is out of scope here. *Tradeoff:* text is less glanceable than icons, but zero new
   art/render risk and it is already golden-stable.

2. **Add the invincibility blink as the primary respawn cue — keyed on the existing `invincible_timer`.**
   It is the highest value-per-effort signal: it reuses the #802 tangibility field, maps directly to the
   sourced 120 f window, and tells the player the one thing that changes their decisions (am I still
   protected?). Ship a simple non-blink tint first as an **acknowledged divergence** and defer the
   faithful ~9 f flicker to its existing home, epic **#558** (this is exactly the #830 recommendation).
   *Tradeoff:* a tint is a small divergence from PM's flicker, but it is labelled interim and
   costs little; it is inert until #506 sets `invincible_timer` on respawn, so it lands naturally with
   that slice.

3. **Defer the revival platform to epic #482.** It is the biggest visual change (a spawned platform,
   descent, drop-off jump rules) and is already the ratified, tracked model. Not a HUD element — a world
   entity — so it sits outside a HUD-scoped change. *Tradeoff:* until it lands, respawn stays a plain
   airborne drop, which is the current known #482 gap, not a regression.

4. **Do not add a numeric countdown.** It diverges from every Smash title and would read as a
   non-Smash HUD. *Tradeoff:* a countdown is trivially cheap and arguably "clearer," but clarity here
   is already carried by the flash (protected?) and stock text (lives left?); a number adds noise and
   breaks convention. Recommend against unless a designer explicitly wants a non-PM HUD affordance.

**Net default:** `Lives:` text (already shipped) **+** invincibility blink (interim tint now via #506,
faithful flicker via #558) **+** revival platform (via #482). No countdown. This layers onto the
existing, sourced implementation plan without inventing a new HUD affordance or a new number.

## Provenance summary

| Finding | Value | Provenance | Source |
|---|---|---|---|
| DEAD phase (KO → platform) | ~61 f (~1.0 s) | **FOUND-by-engine**; PM `[inference]` | meleelight `DEADUP.js` `interrupt()` |
| REBIRTH descent phase | ~91 f (~1.5 s) | **FOUND-by-engine**; PM `[inference]` | meleelight `REBIRTH.js` `interrupt()` |
| KO → controllable (sum) | ~152 f (~2.5 s) | **FOUND-by-engine**; PM `[inference]` | meleelight (sum of the two) |
| Star KO duration (secondary anchor) | "about 2 s" | secondary, approximate, KO-type-dependent | SmashWiki Star KO |
| On-platform intangibility | until action / 300 f | **FOUND** | SmashWiki Revival platform + meleelight; #480/#830 |
| Platform auto-vanish | 300 f / 5 s | **FOUND** | SmashWiki + meleelight `REBIRTHWAIT.js` |
| Post-leave invincibility | 120 f / 2 s, flat | **FOUND** | SmashWiki Invincibility + meleelight; #830 |
| Respawn render | blink/flicker, not solid; no numeric countdown | **FOUND-by-engine** (blink) / **FOUND** (no countdown) | meleelight `render.js`; SmashWiki (no countdown in any title) |
| pycats `RESPAWN_DELAY_FRAMES` | 120 f / 2 s | **TUNED** (no canon) | `pycats/combat/provenance.py` |

## Out of scope (downstream tickets)

- Implementing the platform, the intangibility phase, or the invincibility grant — epic **#482** /
  slice **#506**.
- The faithful blink/flicker render — epic **#558**.
- Any change to `RESPAWN_DELAY_FRAMES` or a new duration constant — a DEV change with a basis, filed
  under #482 if wanted.
- Ratifying the HUD recommendation (this is a design recommendation; a decision ticket can ratify if
  sign-off is wanted).

## Sources

- SmashWiki — [Revival platform](https://www.ssbwiki.com/Revival_platform) (verified 2026-08-07)
- SmashWiki — [Invincibility](https://www.ssbwiki.com/Invincibility) (verified 2026-08-07)
- SmashWiki — [Star KO](https://www.ssbwiki.com/Star_KO) (verified 2026-08-07)
- SmashWiki — [Respawn](https://www.ssbwiki.com/Respawn) (verified 2026-08-07)
- meleelight (Melee engine reimplementation, local clone #616) — `src/characters/shared/moves/DEADUP.js`,
  `REBIRTH.js`, `REBIRTHWAIT.js`; `src/main/render.js`
- Prior pycats findings: [`2026-07-03-pm-spawn-respawn-mechanics.md`](./2026-07-03-pm-spawn-respawn-mechanics.md)
  (#480), [`2026-07-21-respawn-invincibility-validation-findings.md`](./2026-07-21-respawn-invincibility-validation-findings.md)
  (#830)
- pycats source: `pycats/config/stage.py`, `pycats/entities/fighter.py`, `pycats/combat/provenance.py`,
  `pycats/render/hud.py`

## Termination

Timing sourced (A1 — full KO→respawn timeline with per-phase provenance; A2 — pycats gap sized without
changing a value), display treatment enumerated + a default HUD recommendation given with tradeoffs (B),
prior art cited not duplicated, downstream tickets named. Findings only — no ruling, no code change.
