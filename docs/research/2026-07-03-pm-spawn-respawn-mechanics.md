# PM spawn / respawn model — parity spec (#480)

> Research + reporter-ratified design of record for the spawn/respawn work.
> Decision (2026-07-03, avidrucker): **adopt the full-PM model** — implementation epic
> **#482**. Date: 2026-07-03. Agent: FIG. PM canon: Project M 3.6 (Melee-based).

## 1. PM / Melee model (cited)

**Match start.** Fighters begin **grounded** at fixed start positions on the stage — not
airborne. *(Standard Melee/PM; SmashWiki's respawn coverage is post-KO, so this is
medium-high confidence, not a quoted frame value.)*

**Post-KO respawn — the revival platform.**
- The fighter reappears on a **revival platform floating above the centre of the stage**,
  **intangible** the whole time it is on the platform.
- The platform **disappears as soon as the player moves or attacks** (any action leaves
  it), or **auto-disappears after 5 seconds** of inaction.
- **After leaving, ~2 s / 120 frames** of further invincibility aids the descent
  (Melee/Brawl; Ultimate scales it down by time-spent-waiting — not adopted).
- The revival platform is a **standable, pass-through platform**: on it the fighter is
  **grounded** (walk / jump / shield / drop-through via down / attack), so it has its
  **full jump count**; leaving (drop / walk / jump off) forfeits the grounded jump →
  **midair jump(s) only** (the #466/#473 rule).

Sources: SmashWiki [Respawn](https://www.ssbwiki.com/Respawn),
[Revival platform](https://www.ssbwiki.com/Revival_platform),
[Invincibility](https://www.ssbwiki.com/Invincibility).

> **Validated 2026-07-21 (#830)** — see
> [research/2026-07-21-respawn-invincibility-validation-findings.md](./2026-07-21-respawn-invincibility-validation-findings.md):
> duration **120 f** confirmed (flat; Ultimate's scaling not adopted); **acting does not truncate** the
> post-drop 120 f window (it runs in full regardless of actions — meleelight engine; PM `[inference]`);
> the window renders as a **blink/flicker**, not a solid tint (PM `[inference]`; SmashWiki silent on the
> respawn model's appearance). The on-platform *intangibility* still ends on any action.

## 2. pycats now (as-is, verified 2026-07-03)

Both match-start and every post-KO respawn go through
`Player.reset_to_spawn → Fighter.reset_to_spawn`:
- **Spawns AIRBORNE** — `on_ground=False` at `PLAYER{1,2}_START_{X,Y}` → falls to the stage.
- **Full jumps** at spawn.
- **No respawn invincibility** — `reset_to_spawn` even clears leaked `invulnerable`.
- **No revival platform.**
- **Input live immediately** — can drift / jump / air-dodge / attack while falling.
- **2 s KO freeze** (`RESPAWN_DELAY_FRAMES`) before the drop.

## 3. Comparison

| Aspect | PM / Melee | pycats now | Match? |
|---|---|---|---|
| Match-start position | grounded on stage | airborne, falls in | ✗ |
| Post-KO location | revival platform (top-centre) | dropped at `START_Y`, falls | ✗ |
| On-respawn intangibility | intangible on platform | none | ✗ |
| Post-leave invincibility | ~120 f / 2 s | none | ✗ |
| Platform auto-vanish | 5 s (~300 f) | n/a | ✗ |
| Invincibility ends on | move **or** attack | n/a | — |
| Jump count at spawn | full (grounded on platform) | full (but airborne) | ~ (right count, wrong basis) |
| Leaving forfeits grounded jump | yes | no (→ #473) | ✗ |
| Control during spawn | full | full (while falling) | ✓ |

## 4. Ratified decision — **full-PM**

Adopt the revival-platform model, respawn intangibility + 120 f post-leave window, and a
grounded match-start. Implementation is epic **#482** (ordered slices there). Frame values:
pycats runs at 60 FPS, so **adopt Melee's counts directly** — post-leave invincibility
**120 f**, platform auto-vanish **300 f**; revival platform is a **thin (drop-through)**
platform, top-centre, above the thin stage platforms (exact rect pinned at slice pickup).

## 5. Rulings that feed #473 (the takeoff jump clamp)

- **Drop-through (down-press through a thin platform)** is a no-jump takeoff → forfeits the
  grounded jump (midair only). **#473's clamp should fire on drop-through** — confirmed
  PM-faithful. → add to #473 acceptance.
- **Respawn jump count** is resolved *by the platform model*, not by special-casing: a
  fighter spawns **grounded on the revival platform** (slice 2 of #482) → keeps full
  `max_jumps`; when it leaves the platform, #473's ordinary clamp forfeits the grounded
  jump. So #473 needs **no** respawn-specific branch — it just must not misfire on spawn.
  (With today's airborne-drop model it already doesn't, because spawn is already airborne
  — no ground→air transition; once #482 slice 2 lands the platform, spawn-on-platform is
  grounded and the clamp fires correctly on leaving.)

## 6. Termination

PM model cited (§1), pycats gap recorded (§2–3), full-PM ruling ratified (§4), #473
refinements settled (§5), implementation tracked on epic **#482**. Done.
