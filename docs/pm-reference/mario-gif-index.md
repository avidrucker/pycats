# Mario animation-GIF reference set — manifest (#777)

The **complete** browsable library of Project M 3.6 **Mario** subaction animations,
rendered via the [`tooling-brawllib-rs-gif-recipe.md`](../tooling-brawllib-rs-gif-recipe.md)
(#758) `gif_generator` recipe. It is the visual substrate for comparing pycats' **Nalio**
(the Mario archetype) move-for-move against the PM source — the reference-asset
prerequisite for the side-by-side sandbox mode (#778).

Each GIF is brawllib_rs's **hurtbox-capsule / skeleton** render (the rukaidata.com
renderer) — it shows *motion*, not the character skin. That is the right thing for
measuring and comparing movement; the capsules track the bones.

## ⚠ Copyright — GIFs are not committed

The `.pac` source **and** every derived GIF are copyrighted. The GIFs live **only** in
gitignored `repros/mario-gifs/` (per the repros-dir media policy) and are **never**
committed. This manifest is the only committed artifact — it makes the set discoverable
and reproducible **without** shipping a single frame.

## Reproduce the set

Prerequisites (datamine env, PM 3.6 `.pac` data) are in the recipe doc. From the
brawllib_rs clone, render one subaction with:

```bash
. ~/.cargo/env                          # REQUIRED in non-interactive shells (err #149)
cargo run --release --example gif_generator -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \   # vanilla Brawl (DATA/files nesting)
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \                 # PM 3.6 overlay
  -f Mario \                                                  # fighter
  -a <Subaction>                                              # e.g. Wait1
# writes output_Mario_<Subaction>.gif -> copy to repros/mario-gifs/mario_<Subaction>.gif
```

The full set was produced by looping that command over every enumerated subaction
(subaction list from `high_level_frame_data -f Mario -l frame -i 0`). At ~4s/render the
whole set takes ~30 min.

## What's here

- **450** enumerated Mario subactions (the 28 empty `NONE`/`_N` action-table
  slots are excluded — they are unused ID slots, not animations).
- **356** have real animation frames → one `mario_<subaction>.gif` each in
  `repros/mario-gifs/`.
- **94** are **empty** (0 frames — Mario's data enumerates the slot but carries
  no animation for it: Melee air-catch, Snake/Yoshi/Ganon capture-victim variants, smash
  item-throws, struggle/`Zitabata`, etc.). These have no motion to reference, so no GIF is
  saved; they are listed below marked **empty** for completeness.

Filename convention: `mario_<Subaction>.gif` (subaction name verbatim). Frame counts are
the rendered GIF's frame count (= the subaction's animation length).

## Index — by category

### Idle / wait  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `Wait1` | `mario_Wait1.gif` | 51 |
| `Wait2` | `mario_Wait2.gif` | 150 |
| `Wait3` | `mario_Wait3.gif` | 95 |
| `WaitItem` | `mario_WaitItem.gif` | 51 |

### Item handling (engine-generic)  (137)

| Subaction | GIF | Frames |
|---|---|---|
| `ItemHandPickUp` | `mario_ItemHandPickUp.gif` | 2 |
| `ItemHandHave` | `mario_ItemHandHave.gif` | 2 |
| `ItemHandGrip` | `mario_ItemHandGrip.gif` | 2 |
| `ItemHandSmash` | `mario_ItemHandSmash.gif` | 2 |
| `LightGet` | `mario_LightGet.gif` | 8 |
| `LightWalkGet` | `mario_LightWalkGet.gif` | 24 |
| `LightEat` | `mario_LightEat.gif` | 20 |
| `LightWalkEat` | `mario_LightWalkEat.gif` | 24 |
| `HeavyGet` | `mario_HeavyGet.gif` | 25 |
| `HeavyWalk1` | `mario_HeavyWalk1.gif` | 20 |
| `HeavyWalk2` | `mario_HeavyWalk2.gif` | 20 |
| `LightThrowDrop` | `mario_LightThrowDrop.gif` | 24 |
| `LightThrowF` | `mario_LightThrowF.gif` | 33 |
| `LightThrowB` | `mario_LightThrowB.gif` | 30 |
| `LightThrowHi` | `mario_LightThrowHi.gif` | 32 |
| `LightThrowLw` | `mario_LightThrowLw.gif` | 28 |
| `LightThrowF_1` | `mario_LightThrowF_1.gif` | 33 |
| `LightThrowB_1` | `mario_LightThrowB_1.gif` | 30 |
| `LightThrowHi_1` | `mario_LightThrowHi_1.gif` | 32 |
| `LightThrowLw_1` | `mario_LightThrowLw_1.gif` | 28 |
| `LightThrowDash` | `mario_LightThrowDash.gif` | 44 |
| `LightThrowAirF` | `mario_LightThrowAirF.gif` | 31 |
| `LightThrowAirB` | `mario_LightThrowAirB.gif` | 31 |
| `LightThrowAirHi` | `mario_LightThrowAirHi.gif` | 30 |
| `LightThrowAirLw` | `mario_LightThrowAirLw.gif` | 26 |
| `LightThrowAirF_1` | `mario_LightThrowAirF_1.gif` | 31 |
| `LightThrowAirB_1` | `mario_LightThrowAirB_1.gif` | 31 |
| `LightThrowAirHi_1` | `mario_LightThrowAirHi_1.gif` | 30 |
| `LightThrowAirLw_1` | `mario_LightThrowAirLw_1.gif` | 26 |
| `HeavyThrowF` | `mario_HeavyThrowF.gif` | 40 |
| `HeavyThrowB` | `mario_HeavyThrowB.gif` | 40 |
| `HeavyThrowHi` | `mario_HeavyThrowHi.gif` | 30 |
| `HeavyThrowLw` | `mario_HeavyThrowLw.gif` | 30 |
| `HeavyThrowF_1` | `mario_HeavyThrowF_1.gif` | 40 |
| `HeavyThrowB_1` | `mario_HeavyThrowB_1.gif` | 40 |
| `HeavyThrowHi_1` | `mario_HeavyThrowHi_1.gif` | 30 |
| `HeavyThrowLw_1` | `mario_HeavyThrowLw_1.gif` | 30 |
| `SmashThrowF` | — | *empty (0)* |
| `SmashThrowB` | — | *empty (0)* |
| `SmashThrowHi` | — | *empty (0)* |
| `SmashThrowLw` | — | *empty (0)* |
| `SmashThrowDash` | — | *empty (0)* |
| `SmashThrowAirF` | — | *empty (0)* |
| `SmashThrowAirB` | — | *empty (0)* |
| `SmashThrowAirHi` | — | *empty (0)* |
| `SmashThrowAirLw` | — | *empty (0)* |
| `Swing1` | `mario_Swing1.gif` | 24 |
| `Swing3` | `mario_Swing3.gif` | 42 |
| `Swing4Start` | `mario_Swing4Start.gif` | 15 |
| `Swing4` | `mario_Swing4.gif` | 46 |
| `Swing42` | — | *empty (0)* |
| `Swing4Hold` | `mario_Swing4Hold.gif` | 61 |
| `SwingDash` | `mario_SwingDash.gif` | 54 |
| `Swing1_1` | `mario_Swing1_1.gif` | 24 |
| `Swing3_1` | `mario_Swing3_1.gif` | 42 |
| `Swing4Bat` | `mario_Swing4Bat.gif` | 90 |
| `SwingDash_1` | `mario_SwingDash_1.gif` | 54 |
| `Swing1_2` | `mario_Swing1_2.gif` | 24 |
| `Swing3_2` | `mario_Swing3_2.gif` | 42 |
| `Swing4Start_1` | `mario_Swing4Start_1.gif` | 15 |
| `Swing4_1` | `mario_Swing4_1.gif` | 46 |
| `Swing42_1` | — | *empty (0)* |
| `Swing4Hold_1` | `mario_Swing4Hold_1.gif` | 61 |
| `SwingDash_2` | `mario_SwingDash_2.gif` | 54 |
| `Swing1_3` | `mario_Swing1_3.gif` | 24 |
| `Swing3_3` | `mario_Swing3_3.gif` | 42 |
| `Swing4Start_2` | `mario_Swing4Start_2.gif` | 15 |
| `Swing4_2` | `mario_Swing4_2.gif` | 46 |
| `Swing42_2` | — | *empty (0)* |
| `Swing4Hold_2` | `mario_Swing4Hold_2.gif` | 61 |
| `SwingDash_3` | `mario_SwingDash_3.gif` | 54 |
| `Swing1_4` | `mario_Swing1_4.gif` | 24 |
| `Swing3_4` | `mario_Swing3_4.gif` | 42 |
| `Swing4Start_3` | `mario_Swing4Start_3.gif` | 15 |
| `Swing4_3` | `mario_Swing4_3.gif` | 46 |
| `Swing42_3` | — | *empty (0)* |
| `Swing4Hold_3` | `mario_Swing4Hold_3.gif` | 61 |
| `SwingDash_4` | `mario_SwingDash_4.gif` | 54 |
| `ItemHammerWait` | `mario_ItemHammerWait.gif` | 17 |
| `ItemHammerMove` | `mario_ItemHammerMove.gif` | 17 |
| `ItemHammerAir` | `mario_ItemHammerAir.gif` | 17 |
| `ItemHammerWait_1` | `mario_ItemHammerWait_1.gif` | 17 |
| `ItemHammerMove_1` | `mario_ItemHammerMove_1.gif` | 17 |
| `ItemHammerAir_1` | `mario_ItemHammerAir_1.gif` | 17 |
| `ItemDragoonRide` | `mario_ItemDragoonRide.gif` | 61 |
| `ItemScrew` | `mario_ItemScrew.gif` | 41 |
| `ItemScrew_1` | `mario_ItemScrew_1.gif` | 41 |
| `ItemScrewFall` | `mario_ItemScrewFall.gif` | 81 |
| `ItemDragoonGet` | `mario_ItemDragoonGet.gif` | 60 |
| `ItemDragoonRide_1` | `mario_ItemDragoonRide_1.gif` | 61 |
| `ItemBig` | `mario_ItemBig.gif` | 60 |
| `ItemSmall` | `mario_ItemSmall.gif` | 60 |
| `ItemLegsWait` | `mario_ItemLegsWait.gif` | 51 |
| `ItemLegsSlowF` | `mario_ItemLegsSlowF.gif` | 36 |
| `ItemLegsMiddleF` | `mario_ItemLegsMiddleF.gif` | 31 |
| `ItemLegsFastF` | `mario_ItemLegsFastF.gif` | 27 |
| `ItemLegsBrakeF` | `mario_ItemLegsBrakeF.gif` | 2 |
| `ItemLegsDashF` | `mario_ItemLegsDashF.gif` | 24 |
| `ItemLegsSlowB` | `mario_ItemLegsSlowB.gif` | 61 |
| `ItemLegsMiddleB` | `mario_ItemLegsMiddleB.gif` | 41 |
| `ItemLegsFastB` | `mario_ItemLegsFastB.gif` | 26 |
| `ItemLegsBrakeB` | `mario_ItemLegsBrakeB.gif` | 2 |
| `ItemLegsDashB` | `mario_ItemLegsDashB.gif` | 24 |
| `ItemLegsJumpSquat` | `mario_ItemLegsJumpSquat.gif` | 6 |
| `ItemLegsLanding` | `mario_ItemLegsLanding.gif` | 16 |
| `ItemShoot` | `mario_ItemShoot.gif` | 30 |
| `ItemShootAir` | `mario_ItemShootAir.gif` | 30 |
| `ItemShoot_1` | `mario_ItemShoot_1.gif` | 30 |
| `ItemShootAir_1` | `mario_ItemShootAir_1.gif` | 30 |
| `ItemShoot_2` | `mario_ItemShoot_2.gif` | 30 |
| `ItemShootAir_2` | `mario_ItemShootAir_2.gif` | 30 |
| `ItemScopeStart` | `mario_ItemScopeStart.gif` | 16 |
| `ItemScopeRapid` | `mario_ItemScopeRapid.gif` | 9 |
| `ItemScopeFire` | `mario_ItemScopeFire.gif` | 31 |
| `ItemScopeEnd` | `mario_ItemScopeEnd.gif` | 21 |
| `ItemScopeAirStart` | `mario_ItemScopeAirStart.gif` | 16 |
| `ItemScopeAirRapid` | `mario_ItemScopeAirRapid.gif` | 9 |
| `ItemScopeAirFire` | `mario_ItemScopeAirFire.gif` | 31 |
| `ItemScopeAirEnd` | `mario_ItemScopeAirEnd.gif` | 21 |
| `ItemScopeStart_1` | `mario_ItemScopeStart_1.gif` | 16 |
| `ItemScopeRapid_1` | `mario_ItemScopeRapid_1.gif` | 9 |
| `ItemScopeFire_1` | `mario_ItemScopeFire_1.gif` | 31 |
| `ItemScopeEnd_1` | `mario_ItemScopeEnd_1.gif` | 21 |
| `ItemScopeAirStart_1` | `mario_ItemScopeAirStart_1.gif` | 16 |
| `ItemScopeAirRapid_1` | `mario_ItemScopeAirRapid_1.gif` | 9 |
| `ItemScopeAirFire_1` | `mario_ItemScopeAirFire_1.gif` | 31 |
| `ItemScopeAirEnd_1` | `mario_ItemScopeAirEnd_1.gif` | 21 |
| `ItemLauncher` | `mario_ItemLauncher.gif` | 151 |
| `ItemLauncherFire` | `mario_ItemLauncherFire.gif` | 12 |
| `ItemLauncherAirFire` | `mario_ItemLauncherAirFire.gif` | 12 |
| `ItemLauncher_1` | `mario_ItemLauncher_1.gif` | 151 |
| `ItemLauncherFire_1` | `mario_ItemLauncherFire_1.gif` | 12 |
| `ItemLauncherAirFire_1` | `mario_ItemLauncherAirFire_1.gif` | 12 |
| `ItemLauncherFall` | `mario_ItemLauncherFall.gif` | 13 |
| `ItemLauncherAir` | — | *empty (0)* |
| `ItemAssist` | `mario_ItemAssist.gif` | 60 |
| `ItemScrew_2` | `mario_ItemScrew_2.gif` | 41 |

### Ground movement  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `WalkSlow` | `mario_WalkSlow.gif` | 61 |
| `WalkMiddle` | `mario_WalkMiddle.gif` | 41 |
| `WalkFast` | `mario_WalkFast.gif` | 27 |
| `WalkBrake` | `mario_WalkBrake.gif` | 2 |
| `Dash` | `mario_Dash.gif` | 22 |
| `Run` | `mario_Run.gif` | 23 |
| `RunBrake` | `mario_RunBrake.gif` | 23 |
| `Turn` | `mario_Turn.gif` | 12 |
| `TurnRun` | `mario_TurnRun.gif` | 22 |
| `TurnRunBrake` | `mario_TurnRunBrake.gif` | 21 |

### Jump  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `JumpSquat` | `mario_JumpSquat.gif` | 4 |
| `JumpF` | `mario_JumpF.gif` | 56 |
| `JumpF_1` | `mario_JumpF_1.gif` | 56 |
| `JumpB` | `mario_JumpB.gif` | 69 |
| `JumpB_1` | `mario_JumpB_1.gif` | 69 |
| `JumpAerialF` | `mario_JumpAerialF.gif` | 60 |
| `JumpAerialB` | `mario_JumpAerialB.gif` | 90 |

### Fall  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `Fall` | `mario_Fall.gif` | 21 |
| `FallF` | `mario_FallF.gif` | 21 |
| `FallB` | `mario_FallB.gif` | 21 |
| `FallAerial` | `mario_FallAerial.gif` | 11 |
| `FallAerialF` | `mario_FallAerialF.gif` | 11 |
| `FallAerialB` | `mario_FallAerialB.gif` | 11 |
| `FallSpecial` | `mario_FallSpecial.gif` | 7 |
| `FallSpecialF` | `mario_FallSpecialF.gif` | 7 |
| `FallSpecialB` | `mario_FallSpecialB.gif` | 7 |
| `DamageFall` | `mario_DamageFall.gif` | 30 |

### Crouch  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `Squat` | `mario_Squat.gif` | 8 |
| `SquatWait` | `mario_SquatWait.gif` | 131 |
| `SquatWait_1` | `mario_SquatWait_1.gif` | 131 |
| `SquatWaitItem` | `mario_SquatWaitItem.gif` | 131 |
| `SquatRv` | `mario_SquatRv.gif` | 10 |

### Landing  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `LandingLight` | `mario_LandingLight.gif` | 3 |
| `LandingHeavy` | `mario_LandingHeavy.gif` | 3 |
| `LandingFallSpecial` | `mario_LandingFallSpecial.gif` | 21 |
| `LandingAirN` | `mario_LandingAirN.gif` | 15 |
| `LandingAirF` | `mario_LandingAirF.gif` | 21 |
| `LandingAirB` | `mario_LandingAirB.gif` | 15 |
| `LandingAirHi` | `mario_LandingAirHi.gif` | 15 |
| `LandingAirLw` | `mario_LandingAirLw.gif` | 21 |

### Ledge-step (walk-off)  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `StepJump` | `mario_StepJump.gif` | 9 |
| `StepPose` | `mario_StepPose.gif` | 9 |
| `StepBack` | `mario_StepBack.gif` | 21 |
| `StepAirPose` | `mario_StepAirPose.gif` | 9 |
| `StepFall` | `mario_StepFall.gif` | 41 |

### Shield  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `GuardOn` | `mario_GuardOn.gif` | 8 |
| `Guard` | `mario_Guard.gif` | 361 |
| `GuardOff` | `mario_GuardOff.gif` | 16 |
| `GuardDamage` | `mario_GuardDamage.gif` | 21 |
| `Rebound` | `mario_Rebound.gif` | 31 |
| `GuardOn_1` | `mario_GuardOn_1.gif` | 8 |
| `Guard_1` | `mario_Guard_1.gif` | 361 |

### Dodge / roll  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `EscapeN` | `mario_EscapeN.gif` | 26 |
| `EscapeF` | `mario_EscapeF.gif` | 36 |
| `EscapeB` | `mario_EscapeB.gif` | 34 |
| `EscapeAir` | `mario_EscapeAir.gif` | 50 |

### Ground attack — jab / dash  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `Attack11` | `mario_Attack11.gif` | 16 |
| `Attack12` | `mario_Attack12.gif` | 18 |
| `Attack13` | `mario_Attack13.gif` | 40 |
| `AttackDash` | `mario_AttackDash.gif` | 54 |

### Ground attack — tilt  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS3Hi` | `mario_AttackS3Hi.gif` | 33 |
| `AttackS3S` | `mario_AttackS3S.gif` | 33 |
| `AttackS3Lw` | `mario_AttackS3Lw.gif` | 33 |
| `AttackHi3` | `mario_AttackHi3.gif` | 31 |
| `AttackLw3` | `mario_AttackLw3.gif` | 30 |

### Ground attack — smash  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS4Start` | `mario_AttackS4Start.gif` | 6 |
| `AttackS4Hi` | `mario_AttackS4Hi.gif` | 45 |
| `AttackS4S` | `mario_AttackS4S.gif` | 45 |
| `AttackS4Lw` | `mario_AttackS4Lw.gif` | 45 |
| `AttackS4Hold` | `mario_AttackS4Hold.gif` | 61 |
| `AttackHi4Start` | `mario_AttackHi4Start.gif` | 7 |
| `AttackHi4` | `mario_AttackHi4.gif` | 32 |
| `AttackHi4Hold` | `mario_AttackHi4Hold.gif` | 61 |
| `AttackLw4Start` | `mario_AttackLw4Start.gif` | 3 |
| `AttackLw4` | `mario_AttackLw4.gif` | 36 |
| `AttackLw4Hold` | `mario_AttackLw4Hold.gif` | 61 |

### Aerial attack  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackAirN` | `mario_AttackAirN.gif` | 46 |
| `AttackAirF` | `mario_AttackAirF.gif` | 75 |
| `AttackAirB` | `mario_AttackAirB.gif` | 29 |
| `AttackAirHi` | `mario_AttackAirHi.gif` | 34 |
| `AttackAirLw` | `mario_AttackAirLw.gif` | 35 |

### Grab  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `Catch` | `mario_Catch.gif` | 31 |
| `CatchDash` | `mario_CatchDash.gif` | 40 |
| `CatchTurn` | `mario_CatchTurn.gif` | 36 |
| `CatchWait` | `mario_CatchWait.gif` | 31 |
| `CatchAttack` | `mario_CatchAttack.gif` | 24 |
| `CatchCut` | `mario_CatchCut.gif` | 30 |

### Throw  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `ThrowB` | `mario_ThrowB.gif` | 67 |
| `ThrowF` | `mario_ThrowF.gif` | 28 |
| `ThrowHi` | `mario_ThrowHi.gif` | 40 |
| `ThrowLw` | `mario_ThrowLw.gif` | 40 |

### Thrown (victim)  (19)

| Subaction | GIF | Frames |
|---|---|---|
| `ThrownB` | `mario_ThrownB.gif` | 67 |
| `ThrownF` | `mario_ThrownF.gif` | 28 |
| `ThrownHi` | `mario_ThrownHi.gif` | 40 |
| `ThrownLw` | `mario_ThrownLw.gif` | 48 |
| `ThrownDxB` | `mario_ThrownDxB.gif` | 67 |
| `ThrownDxF` | `mario_ThrownDxF.gif` | 28 |
| `ThrownDxHi` | `mario_ThrownDxHi.gif` | 41 |
| `ThrownDxLw` | `mario_ThrownDxLw.gif` | 48 |
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

### Grabbed / carried (victim)  (26)

| Subaction | GIF | Frames |
|---|---|---|
| `CapturePulledHi` | `mario_CapturePulledHi.gif` | 20 |
| `CaptureWaitHi` | `mario_CaptureWaitHi.gif` | 31 |
| `CaptureDamageHi` | `mario_CaptureDamageHi.gif` | 20 |
| `CapturePulledLw` | `mario_CapturePulledLw.gif` | 20 |
| `CaptureWaitLw` | `mario_CaptureWaitLw.gif` | 51 |
| `CaptureDamageLw` | `mario_CaptureDamageLw.gif` | 20 |
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
| `CaptureCut` | `mario_CaptureCut.gif` | 31 |
| `CaptureJump` | `mario_CaptureJump.gif` | 51 |

### Damage / hitstun  (19)

| Subaction | GIF | Frames |
|---|---|---|
| `DamageHi1` | `mario_DamageHi1.gif` | 12 |
| `DamageHi2` | `mario_DamageHi2.gif` | 24 |
| `DamageHi3` | `mario_DamageHi3.gif` | 30 |
| `DamageN1` | `mario_DamageN1.gif` | 12 |
| `DamageN2` | `mario_DamageN2.gif` | 24 |
| `DamageN3` | `mario_DamageN3.gif` | 30 |
| `DamageLw1` | `mario_DamageLw1.gif` | 12 |
| `DamageLw2` | `mario_DamageLw2.gif` | 24 |
| `DamageLw3` | `mario_DamageLw3.gif` | 42 |
| `DamageAir1` | `mario_DamageAir1.gif` | 12 |
| `DamageAir2` | `mario_DamageAir2.gif` | 24 |
| `DamageAir3` | `mario_DamageAir3.gif` | 30 |
| `DamageFlyHi` | `mario_DamageFlyHi.gif` | 37 |
| `DamageFlyN` | `mario_DamageFlyN.gif` | 37 |
| `DamageFlyLw` | `mario_DamageFlyLw.gif` | 37 |
| `DamageFlyTop` | `mario_DamageFlyTop.gif` | 61 |
| `DamageFlyRoll` | `mario_DamageFlyRoll.gif` | 17 |
| `DamageElec` | `mario_DamageElec.gif` | 71 |
| `DamageFace` | — | *empty (0)* |

### Downed / getup  (20)

| Subaction | GIF | Frames |
|---|---|---|
| `DownBoundU` | `mario_DownBoundU.gif` | 27 |
| `DownWaitU` | `mario_DownWaitU.gif` | 71 |
| `DownDamageU` | `mario_DownDamageU.gif` | 14 |
| `DownDamageU3` | — | *empty (0)* |
| `DownEatU` | `mario_DownEatU.gif` | 30 |
| `DownStandU` | `mario_DownStandU.gif` | 30 |
| `DownAttackU` | `mario_DownAttackU.gif` | 50 |
| `DownForwardU` | `mario_DownForwardU.gif` | 36 |
| `DownBackU` | `mario_DownBackU.gif` | 36 |
| `DownBoundD` | `mario_DownBoundD.gif` | 26 |
| `DownWaitD` | `mario_DownWaitD.gif` | 71 |
| `DownDamageD` | `mario_DownDamageD.gif` | 15 |
| `DownDamageD3` | — | *empty (0)* |
| `DownEatD` | `mario_DownEatD.gif` | 30 |
| `DownStandD` | `mario_DownStandD.gif` | 30 |
| `DownAttackD` | `mario_DownAttackD.gif` | 50 |
| `DownForwardD` | `mario_DownForwardD.gif` | 36 |
| `DownBackD` | `mario_DownBackD.gif` | 36 |
| `DownSpotU` | — | *empty (0)* |
| `DownSpotD` | `mario_DownSpotD.gif` | 30 |

### Tech / passive  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `Passive` | `mario_Passive.gif` | 27 |
| `PassiveStandF` | `mario_PassiveStandF.gif` | 41 |
| `PassiveStandB` | `mario_PassiveStandB.gif` | 41 |
| `PassiveWall` | `mario_PassiveWall.gif` | 27 |
| `PassiveWallJump` | `mario_PassiveWallJump.gif` | 41 |
| `PassiveCeil` | `mario_PassiveCeil.gif` | 27 |

### Dizzy / sleep  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `FuraFura` | `mario_FuraFura.gif` | 121 |
| `FuraFuraStartU` | `mario_FuraFuraStartU.gif` | 50 |
| `FuraFuraStartD` | `mario_FuraFuraStartD.gif` | 50 |
| `FuraFuraEnd` | `mario_FuraFuraEnd.gif` | 50 |
| `FuraSleepStart` | `mario_FuraSleepStart.gif` | 30 |
| `FuraSleepLoop` | `mario_FuraSleepLoop.gif` | 111 |
| `FuraSleepEnd` | `mario_FuraSleepEnd.gif` | 60 |

### Misc / situational  (12)

| Subaction | GIF | Frames |
|---|---|---|
| `Swallowed` | `mario_Swallowed.gif` | 11 |
| `Pass` | `mario_Pass.gif` | 30 |
| `Ottotto` | `mario_Ottotto.gif` | 13 |
| `OttottoWait` | `mario_OttottoWait.gif` | 186 |
| `WallDamage` | `mario_WallDamage.gif` | 41 |
| `StopCeil` | `mario_StopCeil.gif` | 9 |
| `StopWall` | `mario_StopWall.gif` | 21 |
| `StopCeil_1` | `mario_StopCeil_1.gif` | 9 |
| `MissFoot` | `mario_MissFoot.gif` | 27 |
| `GekikaraWait` | `mario_GekikaraWait.gif` | 96 |
| `Dark` | — | *empty (0)* |
| `Spycloak` | — | *empty (0)* |

### Ledge (cliff hang / getup)  (12)

| Subaction | GIF | Frames |
|---|---|---|
| `CliffCatch` | `mario_CliffCatch.gif` | 21 |
| `CliffWait` | `mario_CliffWait.gif` | 101 |
| `CliffAttackQuick` | `mario_CliffAttackQuick.gif` | 56 |
| `CliffClimbQuick` | `mario_CliffClimbQuick.gif` | 35 |
| `CliffEscapeQuick` | `mario_CliffEscapeQuick.gif` | 50 |
| `CliffJumpQuick1` | `mario_CliffJumpQuick1.gif` | 16 |
| `CliffJumpQuick2` | `mario_CliffJumpQuick2.gif` | 31 |
| `CliffAttackSlow` | `mario_CliffAttackSlow.gif` | 70 |
| `CliffClimbSlow` | `mario_CliffClimbSlow.gif` | 60 |
| `CliffEscapeSlow` | `mario_CliffEscapeSlow.gif` | 80 |
| `CliffJumpSlow1` | `mario_CliffJumpSlow1.gif` | 20 |
| `CliffJumpSlow2` | `mario_CliffJumpSlow2.gif` | 31 |

### Trip / slip  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SlipDown` | `mario_SlipDown.gif` | 40 |
| `Slip` | `mario_Slip.gif` | 30 |
| `SlipTurn` | `mario_SlipTurn.gif` | 36 |
| `SlipDash` | `mario_SlipDash.gif` | 46 |
| `SlipWait` | `mario_SlipWait.gif` | 111 |
| `SlipStand` | `mario_SlipStand.gif` | 22 |
| `SlipAttack` | `mario_SlipAttack.gif` | 50 |
| `SlipEscapeF` | `mario_SlipEscapeF.gif` | 29 |
| `SlipEscapeB` | `mario_SlipEscapeB.gif` | 29 |

### Air-catch grab (Melee-style)  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `AirCatch` | — | *empty (0)* |
| `AirCatchPose` | — | *empty (0)* |
| `AirCatchHit` | — | *empty (0)* |
| `AirCatch_1` | — | *empty (0)* |

### Swim  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SwimRise` | `mario_SwimRise.gif` | 31 |
| `SwimUp` | `mario_SwimUp.gif` | 16 |
| `SwimUpDamage` | `mario_SwimUpDamage.gif` | 22 |
| `Swim` | `mario_Swim.gif` | 101 |
| `SwimF` | `mario_SwimF.gif` | 31 |
| `SwimEnd` | `mario_SwimEnd.gif` | 20 |
| `SwimTurn` | `mario_SwimTurn.gif` | 20 |
| `SwimDrown` | `mario_SwimDrown.gif` | 61 |
| `SwimDrownOut` | `mario_SwimDrownOut.gif` | 41 |

### Ladder / rope  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `LadderWait` | `mario_LadderWait.gif` | 81 |
| `LadderUp` | `mario_LadderUp.gif` | 9 |
| `LadderDown` | `mario_LadderDown.gif` | 41 |
| `LadderCatchR` | `mario_LadderCatchR.gif` | 15 |
| `LadderCatchL` | `mario_LadderCatchL.gif` | 15 |
| `LadderCatchAirR` | `mario_LadderCatchAirR.gif` | 15 |
| `LadderCatchAirL` | `mario_LadderCatchAirL.gif` | 15 |
| `LadderCatchEndR` | `mario_LadderCatchEndR.gif` | 16 |
| `LadderCatchEndL` | `mario_LadderCatchEndL.gif` | 16 |
| `RopeCatch` | — | *empty (0)* |
| `RopeFishing` | — | *empty (0)* |

### Special grab (victim / other-fighter)  (36)

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
| `SpecialSZitabata` | — | *empty (0)* |
| `SpecialSDxZitabata` | — | *empty (0)* |

### Other-fighter grab (victim)  (2)

| Subaction | GIF | Frames |
|---|---|---|
| `GanonSpecialHiCapture` | — | *empty (0)* |
| `GanonSpecialHiDxCapture` | — | *empty (0)* |

### Special move  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SpecialNEgg` | — | *empty (0)* |
| `SpecialN` | `mario_SpecialN.gif` | 49 |
| `SpecialAirN` | `mario_SpecialAirN.gif` | 49 |
| `SpecialS` | `mario_SpecialS.gif` | 36 |
| `SpecialAirS` | `mario_SpecialAirS.gif` | 36 |
| `SpecialHi` | `mario_SpecialHi.gif` | 38 |
| `SpecialAirHi` | `mario_SpecialAirHi.gif` | 38 |
| `SpecialLw` | `mario_SpecialLw.gif` | 81 |
| `SpecialAirLw` | `mario_SpecialAirLw.gif` | 81 |

### Taunt / appeal  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `AppealHi` | `mario_AppealHi.gif` | 180 |
| `AppealHi_1` | `mario_AppealHi_1.gif` | 180 |
| `AppealS` | `mario_AppealS.gif` | 100 |
| `AppealS_1` | `mario_AppealS_1.gif` | 100 |
| `AppealLw` | `mario_AppealLw.gif` | 85 |
| `AppealLw_1` | `mario_AppealLw_1.gif` | 85 |

### Entry / win / lose  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `EntryR` | `mario_EntryR.gif` | 121 |
| `EntryL` | `mario_EntryL.gif` | 121 |
| `Win1` | `mario_Win1.gif` | 121 |
| `Win1Wait` | `mario_Win1Wait.gif` | 51 |
| `Win2` | `mario_Win2.gif` | 121 |
| `Win2Wait` | `mario_Win2Wait.gif` | 61 |
| `Win3` | `mario_Win3.gif` | 121 |
| `Win3Wait` | `mario_Win3Wait.gif` | 61 |
| `Lose` | `mario_Lose.gif` | 109 |

### Final Smash  (2)

| Subaction | GIF | Frames |
|---|---|---|
| `Final` | `mario_Final.gif` | 180 |
| `FinalAir` | `mario_FinalAir.gif` | 180 |
rendered=356 empty=94 total=450

