# Fox animation-GIF reference set — manifest (#839)

The **complete** browsable library of Project M 3.6 **Fox** subaction
animations, rendered via the [`tooling-brawllib-rs-gif-recipe.md`](../tooling-brawllib-rs-gif-recipe.md)
(#758) `gif_generator` recipe. It is the visual substrate for comparing pycats'
**Xoff** (pronounced "Zoff" — the Fox archetype: fastest run + fall, blaster,
dies early off the top; the 5th cat in the roster epic #117, name decided by Avi
and recorded in #127 + the naming memory alongside Nalio/Narz/Birky/Gnok)
move-for-move against the PM source. Completes the five-archetype GIF-library set,
mirroring the Mario ([`mario-gif-index.md`](./mario-gif-index.md), #777),
DK ([`dk-gif-index.md`](./dk-gif-index.md), #827), Kirby
([`kirby-gif-index.md`](./kirby-gif-index.md), #828), and Marth
([`marth-gif-index.md`](./marth-gif-index.md), #832) sets.

Each GIF is brawllib_rs's **hurtbox-capsule / skeleton** render (the rukaidata.com
renderer) — it shows *motion*, not the character skin. That is the right thing for
measuring and comparing movement; the capsules track the bones. It is not a sprite sheet.

## ⚠ Copyright — GIFs are not committed

The `.pac` source **and** every derived GIF are copyrighted. The GIFs live **only**
in gitignored `repros/fox-gifs/` (per the repros-dir media policy) and are **never**
committed. This manifest is the only committed artifact — it makes the set
discoverable and reproducible **without** shipping a single frame.

## Reproduce the set

Prerequisites (datamine env, PM 3.6 `.pac` data) are in the recipe doc. Fox's filter is
plain **`-f Fox`**: its `cased_name` and `internal_name` are both `Fox`, and the written
GIF uses the same display name (`output_Fox_<Subaction>.gif`) — no display-vs-internal
split like DK's `Donkey` / `Donkey Kong` (#824). Confirmed once up front via
`high_level_frame_data -f Fox -l subaction` → `Fighter name: Fox`.

**1. Enumerate** every subaction name + frame length (the authoritative list, including the
0-frame empties) with the throwaway `subaction_lengths` helper added to the brawllib_rs clone
(a de-filtered sibling of `wait_lengths`, #753 — no new deps):

```bash
. ~/.cargo/env                          # REQUIRED in non-interactive shells (err #149)
cargo run --release --example subaction_lengths -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \   # vanilla Brawl (DATA/files nesting)
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \                 # PM 3.6 overlay
  -f Fox                                                       # prints "<Subaction>\t<frames.len()>"
```

**2. Render** each subaction with `frames.len() > 0` to a GIF, then move it into the
gitignored library as `fox_<Subaction>.gif`:

```bash
cargo run --release --example gif_generator -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \
  -f Fox -a <Subaction>
# writes output_Fox_<Subaction>.gif -> mv to repros/fox-gifs/fox_<Subaction>.gif
```

For a 383-GIF batch, build the example once (`cargo build --release --example gif_generator`)
and call `target/release/examples/gif_generator` directly in the loop — the per-render
`cargo run` build-check dominates otherwise.

The frame counts below are `subaction.frames.len()` from step 1 — verified equal to the
rendered GIF's `n_frames` (Pillow).

## What's here

- **482** enumerated Fox subactions (the `NONE*` action-table slots are excluded —
  they are unused engine IDs, not animations).
- **383** have real animation frames → one `fox_<Subaction>.gif` each in
  `repros/fox-gifs/`.
- **99** are **empty** (0 frames — Fox's data enumerates the slot but carries no
  animation for it: grab-victim `Capture*` variants for other characters' throws,
  `SmashThrow*` item tosses, the `Special*Bitten` / `*Capture` / `*Egg` / `*Zitabata`
  command-grab-victim poses inherited from the shared subaction table, and unused engine
  slots). These have no motion to reference, so no GIF is saved; they are listed below
  marked **empty** for completeness.

Filename convention: `fox_<Subaction>.gif` (subaction name verbatim). Frame counts are
the subaction's animation length (`frames.len()` = the rendered GIF's frame count).

## Fox special-move key

For the Xoff comparison, the named specials map to these subaction prefixes. (The many
other `Special*` rows in the index — `*Bitten`, `*Capture`, `*Egg`, `*Zitabata`,
`*Stick*` — are engine-generic **command-grab-victim** reaction slots from the shared
subaction table, not Fox's own moves.)

| PM Fox special | Subactions |
|---|---|
| Neutral-B — **Blaster** | `SpecialNStart` / `SpecialNLoop` (fire) / `SpecialNEnd`; `SpecialAirN*` airborne |
| Side-B — **Fox Illusion** | `SpecialSStart` / `SpecialS` (dash) / `SpecialSEnd`; `SpecialAirS*` airborne |
| Up-B — **Fire Fox** | `SpecialHiHold` / `SpecialHiHoldAir` (charge) → `SpecialHi` (launch) → `SpecialHiFall` / `SpecialHiBound` / `SpecialHiLanding` |
| Down-B — **Reflector** | `SpecialLwStart` / `SpecialLwLoop` (hold) / `SpecialLwHit` (reflect) / `SpecialLwEnd`; `SpecialAirLw*` airborne |
| Final Smash — **Landmaster** | `FinalStart` / `FinalEnd` (+ `FinalAirStart` / `FinalAirEnd`) — see Final Smash section |

## Index — by category

### Idle / wait  (3)

| Subaction | GIF | Frames |
|---|---|---|
| `Wait1` | `fox_Wait1.gif` | 121 |
| `Wait2` | `fox_Wait2.gif` | 100 |
| `Wait3` | `fox_Wait3.gif` | 186 |

### Item handling (engine-generic)  (138)

| Subaction | GIF | Frames |
|---|---|---|
| `WaitItem` | `fox_WaitItem.gif` | 121 |
| `ItemHandPickUp` | `fox_ItemHandPickUp.gif` | 2 |
| `ItemHandHave` | `fox_ItemHandHave.gif` | 2 |
| `ItemHandGrip` | `fox_ItemHandGrip.gif` | 2 |
| `ItemHandSmash` | `fox_ItemHandSmash.gif` | 2 |
| `LightGet` | `fox_LightGet.gif` | 8 |
| `LightWalkGet` | `fox_LightWalkGet.gif` | 20 |
| `LightEat` | `fox_LightEat.gif` | 20 |
| `LightWalkEat` | `fox_LightWalkEat.gif` | 20 |
| `HeavyGet` | `fox_HeavyGet.gif` | 38 |
| `HeavyWalk1` | `fox_HeavyWalk1.gif` | 45 |
| `HeavyWalk2` | `fox_HeavyWalk2.gif` | 45 |
| `LightThrowDrop` | `fox_LightThrowDrop.gif` | 24 |
| `LightThrowF` | `fox_LightThrowF.gif` | 29 |
| `LightThrowB` | `fox_LightThrowB.gif` | 29 |
| `LightThrowHi` | `fox_LightThrowHi.gif` | 25 |
| `LightThrowLw` | `fox_LightThrowLw.gif` | 26 |
| `LightThrowF_1` | `fox_LightThrowF_1.gif` | 29 |
| `LightThrowB_1` | `fox_LightThrowB_1.gif` | 29 |
| `LightThrowHi_1` | `fox_LightThrowHi_1.gif` | 25 |
| `LightThrowLw_1` | `fox_LightThrowLw_1.gif` | 26 |
| `LightThrowDash` | `fox_LightThrowDash.gif` | 47 |
| `LightThrowAirF` | `fox_LightThrowAirF.gif` | 29 |
| `LightThrowAirB` | `fox_LightThrowAirB.gif` | 28 |
| `LightThrowAirHi` | `fox_LightThrowAirHi.gif` | 24 |
| `LightThrowAirLw` | `fox_LightThrowAirLw.gif` | 27 |
| `LightThrowAirF_1` | `fox_LightThrowAirF_1.gif` | 29 |
| `LightThrowAirB_1` | `fox_LightThrowAirB_1.gif` | 28 |
| `LightThrowAirHi_1` | `fox_LightThrowAirHi_1.gif` | 24 |
| `LightThrowAirLw_1` | `fox_LightThrowAirLw_1.gif` | 27 |
| `HeavyThrowF` | `fox_HeavyThrowF.gif` | 40 |
| `HeavyThrowB` | `fox_HeavyThrowB.gif` | 40 |
| `HeavyThrowHi` | `fox_HeavyThrowHi.gif` | 30 |
| `HeavyThrowLw` | `fox_HeavyThrowLw.gif` | 30 |
| `HeavyThrowF_1` | `fox_HeavyThrowF_1.gif` | 40 |
| `HeavyThrowB_1` | `fox_HeavyThrowB_1.gif` | 40 |
| `HeavyThrowHi_1` | `fox_HeavyThrowHi_1.gif` | 30 |
| `HeavyThrowLw_1` | `fox_HeavyThrowLw_1.gif` | 30 |
| `SmashThrowF` | — | *empty (0)* |
| `SmashThrowB` | — | *empty (0)* |
| `SmashThrowHi` | — | *empty (0)* |
| `SmashThrowLw` | — | *empty (0)* |
| `SmashThrowDash` | — | *empty (0)* |
| `SmashThrowAirF` | — | *empty (0)* |
| `SmashThrowAirB` | — | *empty (0)* |
| `SmashThrowAirHi` | — | *empty (0)* |
| `SmashThrowAirLw` | — | *empty (0)* |
| `Swing1` | `fox_Swing1.gif` | 24 |
| `Swing3` | `fox_Swing3.gif` | 42 |
| `Swing4Start` | `fox_Swing4Start.gif` | 12 |
| `Swing4` | `fox_Swing4.gif` | 48 |
| `Swing42` | — | *empty (0)* |
| `Swing4Hold` | `fox_Swing4Hold.gif` | 61 |
| `SwingDash` | `fox_SwingDash.gif` | 46 |
| `Swing1_1` | `fox_Swing1_1.gif` | 24 |
| `Swing3_1` | `fox_Swing3_1.gif` | 42 |
| `Swing4Bat` | `fox_Swing4Bat.gif` | 90 |
| `SwingDash_1` | `fox_SwingDash_1.gif` | 46 |
| `Swing1_2` | `fox_Swing1_2.gif` | 24 |
| `Swing3_2` | `fox_Swing3_2.gif` | 42 |
| `Swing4Start_1` | `fox_Swing4Start_1.gif` | 12 |
| `Swing4_1` | `fox_Swing4_1.gif` | 48 |
| `Swing42_1` | — | *empty (0)* |
| `Swing4Hold_1` | `fox_Swing4Hold_1.gif` | 61 |
| `SwingDash_2` | `fox_SwingDash_2.gif` | 46 |
| `Swing1_3` | `fox_Swing1_3.gif` | 24 |
| `Swing3_3` | `fox_Swing3_3.gif` | 42 |
| `Swing4Start_2` | `fox_Swing4Start_2.gif` | 12 |
| `Swing4_2` | `fox_Swing4_2.gif` | 48 |
| `Swing42_2` | — | *empty (0)* |
| `Swing4Hold_2` | `fox_Swing4Hold_2.gif` | 61 |
| `SwingDash_3` | `fox_SwingDash_3.gif` | 46 |
| `Swing1_4` | `fox_Swing1_4.gif` | 24 |
| `Swing3_4` | `fox_Swing3_4.gif` | 42 |
| `Swing4Start_3` | `fox_Swing4Start_3.gif` | 12 |
| `Swing4_3` | `fox_Swing4_3.gif` | 48 |
| `Swing42_3` | — | *empty (0)* |
| `Swing4Hold_3` | `fox_Swing4Hold_3.gif` | 61 |
| `SwingDash_4` | `fox_SwingDash_4.gif` | 46 |
| `ItemHammerWait` | `fox_ItemHammerWait.gif` | 17 |
| `ItemHammerMove` | `fox_ItemHammerMove.gif` | 17 |
| `ItemHammerAir` | `fox_ItemHammerAir.gif` | 17 |
| `ItemHammerWait_1` | `fox_ItemHammerWait_1.gif` | 17 |
| `ItemHammerMove_1` | `fox_ItemHammerMove_1.gif` | 17 |
| `ItemHammerAir_1` | `fox_ItemHammerAir_1.gif` | 17 |
| `ItemDragoonRide` | `fox_ItemDragoonRide.gif` | 41 |
| `ItemScrew` | `fox_ItemScrew.gif` | 41 |
| `ItemScrew_1` | `fox_ItemScrew_1.gif` | 41 |
| `ItemScrewFall` | `fox_ItemScrewFall.gif` | 81 |
| `ItemDragoonGet` | `fox_ItemDragoonGet.gif` | 60 |
| `ItemDragoonRide_1` | `fox_ItemDragoonRide_1.gif` | 41 |
| `ItemBig` | `fox_ItemBig.gif` | 60 |
| `ItemSmall` | `fox_ItemSmall.gif` | 60 |
| `ItemLegsWait` | `fox_ItemLegsWait.gif` | 51 |
| `ItemLegsSlowF` | `fox_ItemLegsSlowF.gif` | 51 |
| `ItemLegsMiddleF` | `fox_ItemLegsMiddleF.gif` | 36 |
| `ItemLegsFastF` | `fox_ItemLegsFastF.gif` | 30 |
| `ItemLegsBrakeF` | `fox_ItemLegsBrakeF.gif` | 2 |
| `ItemLegsDashF` | `fox_ItemLegsDashF.gif` | 27 |
| `ItemLegsSlowB` | `fox_ItemLegsSlowB.gif` | 51 |
| `ItemLegsMiddleB` | `fox_ItemLegsMiddleB.gif` | 36 |
| `ItemLegsFastB` | `fox_ItemLegsFastB.gif` | 29 |
| `ItemLegsBrakeB` | `fox_ItemLegsBrakeB.gif` | 2 |
| `ItemLegsDashB` | `fox_ItemLegsDashB.gif` | 27 |
| `ItemLegsJumpSquat` | `fox_ItemLegsJumpSquat.gif` | 5 |
| `ItemLegsLanding` | `fox_ItemLegsLanding.gif` | 16 |
| `ItemShoot` | `fox_ItemShoot.gif` | 30 |
| `ItemShootAir` | `fox_ItemShootAir.gif` | 25 |
| `ItemShoot_1` | `fox_ItemShoot_1.gif` | 30 |
| `ItemShootAir_1` | `fox_ItemShootAir_1.gif` | 25 |
| `ItemShoot_2` | `fox_ItemShoot_2.gif` | 30 |
| `ItemShootAir_2` | `fox_ItemShootAir_2.gif` | 25 |
| `ItemScopeStart` | `fox_ItemScopeStart.gif` | 16 |
| `ItemScopeRapid` | `fox_ItemScopeRapid.gif` | 9 |
| `ItemScopeFire` | `fox_ItemScopeFire.gif` | 31 |
| `ItemScopeEnd` | `fox_ItemScopeEnd.gif` | 21 |
| `ItemScopeAirStart` | `fox_ItemScopeAirStart.gif` | 16 |
| `ItemScopeAirRapid` | `fox_ItemScopeAirRapid.gif` | 9 |
| `ItemScopeAirFire` | `fox_ItemScopeAirFire.gif` | 31 |
| `ItemScopeAirEnd` | `fox_ItemScopeAirEnd.gif` | 21 |
| `ItemScopeStart_1` | `fox_ItemScopeStart_1.gif` | 16 |
| `ItemScopeRapid_1` | `fox_ItemScopeRapid_1.gif` | 9 |
| `ItemScopeFire_1` | `fox_ItemScopeFire_1.gif` | 31 |
| `ItemScopeEnd_1` | `fox_ItemScopeEnd_1.gif` | 21 |
| `ItemScopeAirStart_1` | `fox_ItemScopeAirStart_1.gif` | 16 |
| `ItemScopeAirRapid_1` | `fox_ItemScopeAirRapid_1.gif` | 9 |
| `ItemScopeAirFire_1` | `fox_ItemScopeAirFire_1.gif` | 31 |
| `ItemScopeAirEnd_1` | `fox_ItemScopeAirEnd_1.gif` | 21 |
| `ItemLauncher` | `fox_ItemLauncher.gif` | 151 |
| `ItemLauncherFire` | `fox_ItemLauncherFire.gif` | 12 |
| `ItemLauncherAirFire` | `fox_ItemLauncherAirFire.gif` | 12 |
| `ItemLauncher_1` | `fox_ItemLauncher_1.gif` | 151 |
| `ItemLauncherFire_1` | `fox_ItemLauncherFire_1.gif` | 12 |
| `ItemLauncherAirFire_1` | `fox_ItemLauncherAirFire_1.gif` | 12 |
| `ItemLauncherFall` | `fox_ItemLauncherFall.gif` | 9 |
| `ItemLauncherAir` | — | *empty (0)* |
| `ItemAssist` | `fox_ItemAssist.gif` | 60 |
| `ItemScrew_2` | `fox_ItemScrew_2.gif` | 41 |

### Ground movement  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `WalkSlow` | `fox_WalkSlow.gif` | 51 |
| `WalkMiddle` | `fox_WalkMiddle.gif` | 36 |
| `WalkFast` | `fox_WalkFast.gif` | 30 |
| `WalkBrake` | `fox_WalkBrake.gif` | 2 |
| `Dash` | `fox_Dash.gif` | 22 |
| `Run` | `fox_Run.gif` | 21 |
| `RunBrake` | `fox_RunBrake.gif` | 18 |
| `Turn` | `fox_Turn.gif` | 12 |
| `TurnRun` | `fox_TurnRun.gif` | 20 |
| `TurnRunBrake` | `fox_TurnRunBrake.gif` | 21 |

### Jump  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `JumpSquat` | `fox_JumpSquat.gif` | 3 |
| `JumpF` | `fox_JumpF.gif` | 41 |
| `JumpF_1` | `fox_JumpF_1.gif` | 41 |
| `JumpB` | `fox_JumpB.gif` | 41 |
| `JumpB_1` | `fox_JumpB_1.gif` | 41 |
| `JumpAerialF` | `fox_JumpAerialF.gif` | 50 |
| `JumpAerialB` | `fox_JumpAerialB.gif` | 50 |
| `StepJump` | `fox_StepJump.gif` | 9 |

### Fall  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `Fall` | `fox_Fall.gif` | 11 |
| `FallF` | `fox_FallF.gif` | 11 |
| `FallB` | `fox_FallB.gif` | 11 |
| `FallAerial` | `fox_FallAerial.gif` | 9 |
| `FallAerialF` | `fox_FallAerialF.gif` | 9 |
| `FallAerialB` | `fox_FallAerialB.gif` | 9 |
| `FallSpecial` | `fox_FallSpecial.gif` | 9 |
| `FallSpecialF` | `fox_FallSpecialF.gif` | 9 |
| `FallSpecialB` | `fox_FallSpecialB.gif` | 9 |
| `DamageFall` | `fox_DamageFall.gif` | 31 |

### Crouch  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `Squat` | `fox_Squat.gif` | 8 |
| `SquatWait` | `fox_SquatWait.gif` | 101 |
| `SquatWait2` | — | *empty (0)* |
| `SquatWaitItem` | `fox_SquatWaitItem.gif` | 101 |
| `SquatRv` | `fox_SquatRv.gif` | 10 |

### Landing  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `LandingLight` | `fox_LandingLight.gif` | 3 |
| `LandingHeavy` | `fox_LandingHeavy.gif` | 3 |
| `LandingFallSpecial` | `fox_LandingFallSpecial.gif` | 31 |
| `LandingAirN` | `fox_LandingAirN.gif` | 15 |
| `LandingAirF` | `fox_LandingAirF.gif` | 22 |
| `LandingAirB` | `fox_LandingAirB.gif` | 20 |
| `LandingAirHi` | `fox_LandingAirHi.gif` | 18 |
| `LandingAirLw` | `fox_LandingAirLw.gif` | 18 |

### Ledge-step (walk-off)  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `StepPose` | `fox_StepPose.gif` | 9 |
| `StepBack` | `fox_StepBack.gif` | 21 |
| `StepAirPose` | `fox_StepAirPose.gif` | 9 |
| `StepFall` | `fox_StepFall.gif` | 41 |
| `Ottotto` | `fox_Ottotto.gif` | 12 |
| `OttottoWait` | `fox_OttottoWait.gif` | 111 |

### Shield  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `GuardOn` | `fox_GuardOn.gif` | 7 |
| `Guard` | `fox_Guard.gif` | 361 |
| `GuardOff` | `fox_GuardOff.gif` | 15 |
| `GuardDamage` | `fox_GuardDamage.gif` | 21 |
| `GuardOn_1` | `fox_GuardOn_1.gif` | 7 |
| `Guard_1` | `fox_Guard_1.gif` | 361 |

### Dodge / roll  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `EscapeN` | `fox_EscapeN.gif` | 26 |
| `EscapeF` | `fox_EscapeF.gif` | 32 |
| `EscapeB` | `fox_EscapeB.gif` | 32 |
| `EscapeAir` | `fox_EscapeAir.gif` | 50 |

### Ground attack — jab / dash  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `Attack11` | `fox_Attack11.gif` | 17 |
| `Attack12` | `fox_Attack12.gif` | 19 |
| `Attack100` | `fox_Attack100.gif` | 37 |
| `AttackDash` | `fox_AttackDash.gif` | 40 |

### Ground attack — tilt  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS3Hi` | `fox_AttackS3Hi.gif` | 37 |
| `AttackS3S` | `fox_AttackS3S.gif` | 37 |
| `AttackS3Lw` | `fox_AttackS3Lw.gif` | 37 |
| `AttackHi3` | `fox_AttackHi3.gif` | 23 |
| `AttackLw3` | `fox_AttackLw3.gif` | 30 |

### Ground attack — smash  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS4Start` | `fox_AttackS4Start.gif` | 4 |
| `AttackS4S` | `fox_AttackS4S.gif` | 42 |
| `AttackS4S_1` | `fox_AttackS4S_1.gif` | 42 |
| `AttackS4S_2` | `fox_AttackS4S_2.gif` | 42 |
| `AttackS4Hold` | `fox_AttackS4Hold.gif` | 61 |
| `AttackHi4Start` | `fox_AttackHi4Start.gif` | 3 |
| `AttackHi4` | `fox_AttackHi4.gif` | 40 |
| `AttackHi4Hold` | `fox_AttackHi4Hold.gif` | 61 |
| `AttackLw4Start` | `fox_AttackLw4Start.gif` | 3 |
| `AttackLw4` | `fox_AttackLw4.gif` | 51 |
| `AttackLw4Hold` | `fox_AttackLw4Hold.gif` | 61 |

### Aerial attack  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackAirN` | `fox_AttackAirN.gif` | 50 |
| `AttackAirF` | `fox_AttackAirF.gif` | 59 |
| `AttackAirB` | `fox_AttackAirB.gif` | 39 |
| `AttackAirHi` | `fox_AttackAirHi.gif` | 39 |
| `AttackAirLw` | `fox_AttackAirLw.gif` | 50 |

### Air-catch grab  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `AirCatch` | — | *empty (0)* |
| `AirCatchPose` | — | *empty (0)* |
| `AirCatchHit` | — | *empty (0)* |
| `AirCatch_1` | — | *empty (0)* |

### Grab  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `Catch` | `fox_Catch.gif` | 31 |
| `CatchDash` | `fox_CatchDash.gif` | 40 |
| `CatchTurn` | `fox_CatchTurn.gif` | 36 |
| `CatchWait` | `fox_CatchWait.gif` | 31 |
| `CatchAttack` | `fox_CatchAttack.gif` | 25 |
| `CatchCut` | `fox_CatchCut.gif` | 30 |

### Throw  (23)

| Subaction | GIF | Frames |
|---|---|---|
| `ThrowB` | `fox_ThrowB.gif` | 39 |
| `ThrowF` | `fox_ThrowF.gif` | 34 |
| `ThrowHi` | `fox_ThrowHi.gif` | 39 |
| `ThrowLw` | `fox_ThrowLw.gif` | 44 |
| `ThrownB` | `fox_ThrownB.gif` | 50 |
| `ThrownF` | `fox_ThrownF.gif` | 34 |
| `ThrownHi` | `fox_ThrownHi.gif` | 50 |
| `ThrownLw` | `fox_ThrownLw.gif` | 55 |
| `ThrownDxB` | `fox_ThrownDxB.gif` | 50 |
| `ThrownDxF` | `fox_ThrownDxF.gif` | 34 |
| `ThrownDxHi` | `fox_ThrownDxHi.gif` | 50 |
| `ThrownDxLw` | `fox_ThrownDxLw.gif` | 55 |
| `ThrownZitabata` | — | *empty (0)* |
| `ThrownDxZitabata` | — | *empty (0)* |
| `ThrownGirlZitabata` | — | *empty (0)* |
| `ThrownFF` | — | *empty (0)* |
| `ThrownFB` | — | *empty (0)* |
| `ThrownFHi` | — | *empty (0)* |
| `ThrownFLw` | — | *empty (0)* |
| `ThrownDxFF` | — | *empty (0)* |
| `ThrownDxFB` | — | *empty (0)* |
| `ThrownDxFHi` | — | *empty (0)* |
| `ThrownDxFLw` | — | *empty (0)* |

### Grabbed / carried (victim)  (27)

| Subaction | GIF | Frames |
|---|---|---|
| `CapturePulledHi` | `fox_CapturePulledHi.gif` | 20 |
| `CaptureWaitHi` | `fox_CaptureWaitHi.gif` | 51 |
| `CaptureDamageHi` | `fox_CaptureDamageHi.gif` | 20 |
| `CapturePulledLw` | `fox_CapturePulledLw.gif` | 20 |
| `CaptureWaitLw` | `fox_CaptureWaitLw.gif` | 81 |
| `CaptureDamageLw` | `fox_CaptureDamageLw.gif` | 20 |
| `CapturePulledSnake` | — | *empty (0)* |
| `CaptureWaitSnake` | — | *empty (0)* |
| `CaptureDamageSnake` | — | *empty (0)* |
| `CapturePulledSnake_1` | — | *empty (0)* |
| `CaptureWaitSnake_1` | — | *empty (0)* |
| `CaptureDamageSnake_1` | — | *empty (0)* |
| `CapturePulledDxSnake` | — | *empty (0)* |
| `CaptureWaitDxSnake` | — | *empty (0)* |
| `CaptureDamageDxSnake` | — | *empty (0)* |
| `CapturePulledDxSnake_1` | — | *empty (0)* |
| `CaptureWaitDxSnake_1` | — | *empty (0)* |
| `CaptureDamageDxSnake_1` | — | *empty (0)* |
| `CapturePulledBigSnake` | — | *empty (0)* |
| `CaptureWaitBigSnake` | — | *empty (0)* |
| `CaptureDamageBigSnake` | — | *empty (0)* |
| `CapturePulledBigSnake_1` | — | *empty (0)* |
| `CaptureWaitBigSnake_1` | — | *empty (0)* |
| `CaptureDamageBigSnake_1` | — | *empty (0)* |
| `CaptureCut` | `fox_CaptureCut.gif` | 31 |
| `CaptureJump` | `fox_CaptureJump.gif` | 51 |
| `Swallowed` | `fox_Swallowed.gif` | 11 |

### Damage / hitstun  (19)

| Subaction | GIF | Frames |
|---|---|---|
| `DamageHi1` | `fox_DamageHi1.gif` | 12 |
| `DamageHi2` | `fox_DamageHi2.gif` | 24 |
| `DamageHi3` | `fox_DamageHi3.gif` | 30 |
| `DamageN1` | `fox_DamageN1.gif` | 12 |
| `DamageN2` | `fox_DamageN2.gif` | 24 |
| `DamageN3` | `fox_DamageN3.gif` | 30 |
| `DamageLw1` | `fox_DamageLw1.gif` | 12 |
| `DamageLw2` | `fox_DamageLw2.gif` | 24 |
| `DamageLw3` | `fox_DamageLw3.gif` | 42 |
| `DamageAir1` | `fox_DamageAir1.gif` | 12 |
| `DamageAir2` | `fox_DamageAir2.gif` | 24 |
| `DamageAir3` | `fox_DamageAir3.gif` | 30 |
| `DamageFlyHi` | `fox_DamageFlyHi.gif` | 37 |
| `DamageFlyN` | `fox_DamageFlyN.gif` | 37 |
| `DamageFlyLw` | `fox_DamageFlyLw.gif` | 37 |
| `DamageFlyTop` | `fox_DamageFlyTop.gif` | 81 |
| `DamageFlyRoll` | `fox_DamageFlyRoll.gif` | 17 |
| `DamageElec` | `fox_DamageElec.gif` | 71 |
| `DamageFace` | — | *empty (0)* |

### Downed / getup  (20)

| Subaction | GIF | Frames |
|---|---|---|
| `DownBoundU` | `fox_DownBoundU.gif` | 27 |
| `DownWaitU` | `fox_DownWaitU.gif` | 71 |
| `DownDamageU` | `fox_DownDamageU.gif` | 14 |
| `DownDamageU3` | — | *empty (0)* |
| `DownEatU` | `fox_DownEatU.gif` | 30 |
| `DownStandU` | `fox_DownStandU.gif` | 30 |
| `DownAttackU` | `fox_DownAttackU.gif` | 50 |
| `DownForwardU` | `fox_DownForwardU.gif` | 36 |
| `DownBackU` | `fox_DownBackU.gif` | 36 |
| `DownBoundD` | `fox_DownBoundD.gif` | 27 |
| `DownWaitD` | `fox_DownWaitD.gif` | 81 |
| `DownDamageD` | `fox_DownDamageD.gif` | 14 |
| `DownDamageD3` | — | *empty (0)* |
| `DownEatD` | `fox_DownEatD.gif` | 30 |
| `DownStandD` | `fox_DownStandD.gif` | 30 |
| `DownAttackD` | `fox_DownAttackD.gif` | 50 |
| `DownForwardD` | `fox_DownForwardD.gif` | 36 |
| `DownBackD` | `fox_DownBackD.gif` | 36 |
| `DownSpotU` | — | *empty (0)* |
| `DownSpotD` | `fox_DownSpotD.gif` | 30 |

### Tech / passive  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `Passive` | `fox_Passive.gif` | 27 |
| `PassiveStandF` | `fox_PassiveStandF.gif` | 41 |
| `PassiveStandB` | `fox_PassiveStandB.gif` | 41 |
| `PassiveWall` | `fox_PassiveWall.gif` | 27 |
| `PassiveWallJump` | `fox_PassiveWallJump.gif` | 41 |
| `PassiveCeil` | `fox_PassiveCeil.gif` | 27 |
| `Pass` | `fox_Pass.gif` | 30 |

### Dizzy / sleep  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `FuraFura` | `fox_FuraFura.gif` | 111 |
| `FuraFuraStartU` | `fox_FuraFuraStartU.gif` | 50 |
| `FuraFuraStartD` | `fox_FuraFuraStartD.gif` | 50 |
| `FuraFuraEnd` | `fox_FuraFuraEnd.gif` | 50 |
| `FuraSleepStart` | `fox_FuraSleepStart.gif` | 30 |
| `FuraSleepLoop` | `fox_FuraSleepLoop.gif` | 111 |
| `FuraSleepEnd` | `fox_FuraSleepEnd.gif` | 60 |

### Ledge (cliff hang / getup)  (12)

| Subaction | GIF | Frames |
|---|---|---|
| `CliffCatch` | `fox_CliffCatch.gif` | 21 |
| `CliffWait` | `fox_CliffWait.gif` | 51 |
| `CliffAttackQuick` | `fox_CliffAttackQuick.gif` | 55 |
| `CliffClimbQuick` | `fox_CliffClimbQuick.gif` | 35 |
| `CliffEscapeQuick` | `fox_CliffEscapeQuick.gif` | 50 |
| `CliffJumpQuick1` | `fox_CliffJumpQuick1.gif` | 15 |
| `CliffJumpQuick2` | `fox_CliffJumpQuick2.gif` | 39 |
| `CliffAttackSlow` | `fox_CliffAttackSlow.gif` | 70 |
| `CliffClimbSlow` | `fox_CliffClimbSlow.gif` | 60 |
| `CliffEscapeSlow` | `fox_CliffEscapeSlow.gif` | 80 |
| `CliffJumpSlow1` | `fox_CliffJumpSlow1.gif` | 20 |
| `CliffJumpSlow2` | `fox_CliffJumpSlow2.gif` | 34 |

### Trip / slip  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SlipDown` | `fox_SlipDown.gif` | 40 |
| `Slip` | `fox_Slip.gif` | 30 |
| `SlipTurn` | `fox_SlipTurn.gif` | 36 |
| `SlipDash` | `fox_SlipDash.gif` | 46 |
| `SlipWait` | `fox_SlipWait.gif` | 61 |
| `SlipStand` | `fox_SlipStand.gif` | 22 |
| `SlipAttack` | `fox_SlipAttack.gif` | 50 |
| `SlipEscapeF` | `fox_SlipEscapeF.gif` | 29 |
| `SlipEscapeB` | `fox_SlipEscapeB.gif` | 29 |

### Swim  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SwimRise` | `fox_SwimRise.gif` | 31 |
| `SwimUp` | `fox_SwimUp.gif` | 17 |
| `SwimUpDamage` | `fox_SwimUpDamage.gif` | 25 |
| `Swim` | `fox_Swim.gif` | 71 |
| `SwimF` | `fox_SwimF.gif` | 51 |
| `SwimEnd` | `fox_SwimEnd.gif` | 20 |
| `SwimTurn` | `fox_SwimTurn.gif` | 20 |
| `SwimDrown` | `fox_SwimDrown.gif` | 61 |
| `SwimDrownOut` | `fox_SwimDrownOut.gif` | 41 |

### Ladder / rope  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `LadderWait` | `fox_LadderWait.gif` | 81 |
| `LadderUp` | `fox_LadderUp.gif` | 17 |
| `LadderDown` | `fox_LadderDown.gif` | 41 |
| `LadderCatchR` | `fox_LadderCatchR.gif` | 25 |
| `LadderCatchL` | `fox_LadderCatchL.gif` | 15 |
| `LadderCatchAirR` | `fox_LadderCatchAirR.gif` | 25 |
| `LadderCatchAirL` | `fox_LadderCatchAirL.gif` | 15 |
| `LadderCatchEndR` | `fox_LadderCatchEndR.gif` | 24 |
| `LadderCatchEndL` | `fox_LadderCatchEndL.gif` | 24 |
| `RopeCatch` | — | *empty (0)* |
| `RopeFishing` | — | *empty (0)* |

### Special move  (63)

| Subaction | GIF | Frames |
|---|---|---|
| `SpecialNBittenStart` | — | *empty (0)* |
| `SpecialNBitten` | — | *empty (0)* |
| `SpecialNBittenEnd` | — | *empty (0)* |
| `SpecialAirNBittenStart` | — | *empty (0)* |
| `SpecialAirNBitten` | — | *empty (0)* |
| `SpecialAirNBittenEnd` | — | *empty (0)* |
| `SpecialNDxBittenStart` | — | *empty (0)* |
| `SpecialNDxBitten` | — | *empty (0)* |
| `SpecialNDxBittenEnd` | — | *empty (0)* |
| `SpecialAirNDxBittenStart` | — | *empty (0)* |
| `SpecialAirNDxBitten` | — | *empty (0)* |
| `SpecialAirNDxBittenEnd` | — | *empty (0)* |
| `SpecialNBigBittenStart` | — | *empty (0)* |
| `SpecialNBigBitten` | — | *empty (0)* |
| `SpecialNBigBittenEnd` | — | *empty (0)* |
| `SpecialAirNBigBittenStart` | — | *empty (0)* |
| `SpecialAirNBigBitten` | — | *empty (0)* |
| `SpecialAirNBigBittenEnd` | — | *empty (0)* |
| `SpecialHiCapture` | — | *empty (0)* |
| `SpecialHiDxCapture` | — | *empty (0)* |
| `SpecialSStickCapture` | — | *empty (0)* |
| `SpecialSStickAttackCapture` | — | *empty (0)* |
| `SpecialSStickJumpCapture` | — | *empty (0)* |
| `SpecialSDxStickCapture` | — | *empty (0)* |
| `SpecialSDxStickAttackCapture` | — | *empty (0)* |
| `SpecialSDxStickJumpCapture` | — | *empty (0)* |
| `SpecialSCapture` | — | *empty (0)* |
| `SpecialAirSCatchCapture` | — | *empty (0)* |
| `SpecialAirSFallCapture` | — | *empty (0)* |
| `SpecialAirSCapture` | — | *empty (0)* |
| `SpecialSDxCapture` | — | *empty (0)* |
| `SpecialAirSDxCatchCapture` | — | *empty (0)* |
| `SpecialAirSDxFallCapture` | — | *empty (0)* |
| `SpecialAirSDxCapture` | — | *empty (0)* |
| `SpecialNEgg` | — | *empty (0)* |
| `SpecialSZitabata` | — | *empty (0)* |
| `SpecialSDxZitabata` | — | *empty (0)* |
| `SpecialNStart` | `fox_SpecialNStart.gif` | 7 |
| `SpecialNLoop` | `fox_SpecialNLoop.gif` | 11 |
| `SpecialNEnd` | `fox_SpecialNEnd.gif` | 35 |
| `SpecialAirNStart` | `fox_SpecialAirNStart.gif` | 5 |
| `SpecialAirNLoop` | `fox_SpecialAirNLoop.gif` | 11 |
| `SpecialAirNEnd` | `fox_SpecialAirNEnd.gif` | 22 |
| `SpecialSStart` | `fox_SpecialSStart.gif` | 20 |
| `SpecialS` | `fox_SpecialS.gif` | 4 |
| `SpecialSEnd` | `fox_SpecialSEnd.gif` | 40 |
| `SpecialAirSStart` | `fox_SpecialAirSStart.gif` | 20 |
| `SpecialAirS` | `fox_SpecialAirS.gif` | 4 |
| `SpecialAirSEnd` | `fox_SpecialAirSEnd.gif` | 40 |
| `SpecialHiHold` | `fox_SpecialHiHold.gif` | 43 |
| `SpecialHiHoldAir` | `fox_SpecialHiHoldAir.gif` | 43 |
| `SpecialHi` | `fox_SpecialHi.gif` | 30 |
| `SpecialHiLanding` | `fox_SpecialHiLanding.gif` | 21 |
| `SpecialHiFall` | `fox_SpecialHiFall.gif` | 21 |
| `SpecialHiBound` | `fox_SpecialHiBound.gif` | 15 |
| `SpecialLwStart` | `fox_SpecialLwStart.gif` | 4 |
| `SpecialLwLoop` | `fox_SpecialLwLoop.gif` | 29 |
| `SpecialLwHit` | `fox_SpecialLwHit.gif` | 20 |
| `SpecialLwEnd` | `fox_SpecialLwEnd.gif` | 18 |
| `SpecialAirLwStart` | `fox_SpecialAirLwStart.gif` | 4 |
| `SpecialAirLwLoop` | `fox_SpecialAirLwLoop.gif` | 29 |
| `SpecialAirLwHit` | `fox_SpecialAirLwHit.gif` | 20 |
| `SpecialAirLwEnd` | `fox_SpecialAirLwEnd.gif` | 18 |

### Taunt / appeal  (12)

| Subaction | GIF | Frames |
|---|---|---|
| `AppealHi` | `fox_AppealHi.gif` | 75 |
| `AppealHi_1` | `fox_AppealHi_1.gif` | 75 |
| `AppealS` | `fox_AppealS.gif` | 86 |
| `AppealS_1` | `fox_AppealS_1.gif` | 86 |
| `AppealLw` | `fox_AppealLw.gif` | 80 |
| `AppealLw_1` | `fox_AppealLw_1.gif` | 80 |
| `AppealSStartL` | `fox_AppealSStartL.gif` | 25 |
| `AppealSStartR` | `fox_AppealSStartR.gif` | 25 |
| `AppealSL` | `fox_AppealSL.gif` | 307 |
| `AppealSR` | `fox_AppealSR.gif` | 307 |
| `AppealSEndL` | `fox_AppealSEndL.gif` | 65 |
| `AppealSEndR` | `fox_AppealSEndR.gif` | 65 |

### Entry / win / lose  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `EntryR` | `fox_EntryR.gif` | 121 |
| `EntryL` | `fox_EntryL.gif` | 121 |
| `Win1` | `fox_Win1.gif` | 201 |
| `Win1Wait` | `fox_Win1Wait.gif` | 81 |
| `Win2` | `fox_Win2.gif` | 121 |
| `Win2Wait` | `fox_Win2Wait.gif` | 81 |
| `Win3` | `fox_Win3.gif` | 121 |
| `Win3Wait` | `fox_Win3Wait.gif` | 81 |
| `Lose` | `fox_Lose.gif` | 121 |

### Final Smash  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `FinalStart` | `fox_FinalStart.gif` | 50 |
| `FinalEnd` | `fox_FinalEnd.gif` | 110 |
| `FinalAirStart` | `fox_FinalAirStart.gif` | 50 |
| `FinalAirEnd` | `fox_FinalAirEnd.gif` | 111 |

### Misc / situational  (17)

| Subaction | GIF | Frames |
|---|---|---|
| `` | — | *empty (0)* |
| `_1` | — | *empty (0)* |
| `_2` | — | *empty (0)* |
| `_3` | — | *empty (0)* |
| `Rebound` | `fox_Rebound.gif` | 31 |
| `Attack100Start` | `fox_Attack100Start.gif` | 7 |
| `AttackEnd` | `fox_AttackEnd.gif` | 18 |
| `WallDamage` | `fox_WallDamage.gif` | 41 |
| `StopCeil` | `fox_StopCeil.gif` | 9 |
| `StopWall` | `fox_StopWall.gif` | 21 |
| `StopCeil_1` | `fox_StopCeil_1.gif` | 9 |
| `MissFoot` | `fox_MissFoot.gif` | 27 |
| `GekikaraWait` | `fox_GekikaraWait.gif` | 61 |
| `GanonSpecialHiCapture` | — | *empty (0)* |
| `GanonSpecialHiDxCapture` | — | *empty (0)* |
| `Dark` | — | *empty (0)* |
| `Spycloak` | — | *empty (0)* |


<!-- rendered=383 empty=99 total=482 -->
