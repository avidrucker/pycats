# Kirby animation-GIF reference set — manifest (#828)

The **complete** browsable library of Project M 3.6 **Kirby** subaction animations,
rendered via the [`tooling-brawllib-rs-gif-recipe.md`](../tooling-brawllib-rs-gif-recipe.md)
(#758) `gif_generator` recipe. It is the visual substrate for comparing pycats'
**Birky** (the Kirby archetype — epic #228) move-for-move against the PM source.
Mirrors #777 (the Mario/Nalio set) and #827 (the DK/Gnok set).

Each GIF is brawllib_rs's **hurtbox-capsule / skeleton** render (the rukaidata.com
renderer) — it shows *motion*, not the character skin. That is the right thing for
measuring and comparing movement; the capsules track the bones.

## ⚠ Copyright — GIFs are not committed

The `.pac` source **and** every derived GIF are copyrighted. The GIFs live **only** in
gitignored `repros/kirby-gifs/` (per the repros-dir media policy) and are **never**
committed. This manifest is the only committed artifact — it makes the set discoverable
and reproducible **without** shipping a single frame.

## Reproduce the set

Prerequisites (datamine env, PM 3.6 `.pac` data) are in the recipe doc. Kirby loads as
`-f Kirby` (its `internal_name`; confirmed via `high_level_frame_data` → `Fighter name:
Kirby`). From the brawllib_rs clone, render one subaction with:

```bash
. ~/.cargo/env                          # REQUIRED in non-interactive shells (err #149)
cargo run --release --example gif_generator -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \   # vanilla Brawl (DATA/files nesting)
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \                 # PM 3.6 overlay
  -f Kirby \                                                  # fighter
  -a <Subaction>                                              # e.g. Wait1
# writes output_Kirby_<Subaction>.gif -> copy to repros/kirby-gifs/kirby_<Subaction>.gif
```

The full set was produced by looping that command over every enumerated non-empty
subaction (subaction list from `high_level_frame_data -f Kirby -l subaction`). At
~4s/render the whole set takes ~40 min.

## What's here

- **797** enumerated Kirby subactions (the 14 empty `NONE`/`NONE_N`
  and unnamed action-table slots are excluded — unused ID slots, not animations).
- **543** have real animation frames → one `kirby_<subaction>.gif` each in
  `repros/kirby-gifs/`.
- **240** are **empty** (0 frames — the slot is enumerated but carries no
  animation for Kirby). These have no motion to reference, so no GIF is saved; they are
  listed at the bottom marked **empty** for completeness.

Kirby's set is far larger than Mario's/DK's because of the **copy-ability** system: each
fighter Kirby can Inhale contributes a copied-neutral-special slot (the `SpecialN_<k>`
family), so `Special*` alone is the bulk of the set.

Filename convention: `kirby_<Subaction>.gif` (subaction name verbatim). Frame counts are
the subaction's animation length (= the rendered GIF's frame count).

## Index — by category

### Idle / wait  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `Wait1` | `kirby_Wait1.gif` | 111 |
| `Wait2` | `kirby_Wait2.gif` | 90 |
| `Wait3` | `kirby_Wait3.gif` | 120 |
| `WaitItem` | `kirby_WaitItem.gif` | 111 |

### Ground movement  (15)

| Subaction | GIF | Frames |
|---|---|---|
| `WalkSlow` | `kirby_WalkSlow.gif` | 46 |
| `WalkMiddle` | `kirby_WalkMiddle.gif` | 46 |
| `WalkFast` | `kirby_WalkFast.gif` | 31 |
| `WalkBrake` | `kirby_WalkBrake.gif` | 2 |
| `Dash` | `kirby_Dash.gif` | 24 |
| `Run` | `kirby_Run.gif` | 21 |
| `RunBrake` | `kirby_RunBrake.gif` | 23 |
| `Turn` | `kirby_Turn.gif` | 12 |
| `TurnRun` | `kirby_TurnRun.gif` | 30 |
| `TurnRunBrake` | `kirby_TurnRunBrake.gif` | 21 |
| `Ottotto` | `kirby_Ottotto.gif` | 12 |
| `OttottoWait` | `kirby_OttottoWait.gif` | 64 |
| `StopCeil` | `kirby_StopCeil.gif` | 9 |
| `StopWall` | `kirby_StopWall.gif` | 16 |
| `StopCeil_1` | `kirby_StopCeil_1.gif` | 9 |

### Jump  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `JumpSquat` | `kirby_JumpSquat.gif` | 3 |
| `JumpF` | `kirby_JumpF.gif` | 53 |
| `JumpF_1` | `kirby_JumpF_1.gif` | 53 |
| `JumpB` | `kirby_JumpB.gif` | 53 |
| `JumpB_1` | `kirby_JumpB_1.gif` | 53 |
| `JumpAerialF` | `kirby_JumpAerialF.gif` | 51 |
| `JumpAerialF2` | `kirby_JumpAerialF2.gif` | 51 |
| `JumpAerialF3` | `kirby_JumpAerialF3.gif` | 51 |
| `JumpAerialF4` | `kirby_JumpAerialF4.gif` | 51 |
| `JumpAerialF5` | `kirby_JumpAerialF5.gif` | 51 |

### Fall  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `Fall` | `kirby_Fall.gif` | 9 |
| `FallF` | `kirby_FallF.gif` | 9 |
| `FallB` | `kirby_FallB.gif` | 9 |
| `FallAerial` | `kirby_FallAerial.gif` | 9 |
| `FallAerialF` | `kirby_FallAerialF.gif` | 9 |
| `FallAerialB` | `kirby_FallAerialB.gif` | 9 |
| `FallSpecial` | `kirby_FallSpecial.gif` | 9 |
| `FallSpecialF` | `kirby_FallSpecialF.gif` | 9 |
| `FallSpecialB` | `kirby_FallSpecialB.gif` | 9 |

### Crouch  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `Squat` | `kirby_Squat.gif` | 8 |
| `SquatWait` | `kirby_SquatWait.gif` | 41 |
| `SquatWait2` | `kirby_SquatWait2.gif` | 60 |
| `SquatWaitItem` | `kirby_SquatWaitItem.gif` | 41 |
| `SquatRv` | `kirby_SquatRv.gif` | 10 |

### Landing  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `LandingLight` | `kirby_LandingLight.gif` | 3 |
| `LandingHeavy` | `kirby_LandingHeavy.gif` | 3 |
| `LandingFallSpecial` | `kirby_LandingFallSpecial.gif` | 31 |
| `LandingAirN` | `kirby_LandingAirN.gif` | 15 |
| `LandingAirF` | `kirby_LandingAirF.gif` | 15 |
| `LandingAirB` | `kirby_LandingAirB.gif` | 15 |
| `LandingAirHi` | `kirby_LandingAirHi.gif` | 15 |
| `LandingAirLw` | `kirby_LandingAirLw.gif` | 20 |

### Ledge-step (walk-off)  (12)

| Subaction | GIF | Frames |
|---|---|---|
| `StepJump` | `kirby_StepJump.gif` | 9 |
| `StepPose` | `kirby_StepPose.gif` | 9 |
| `StepBack` | `kirby_StepBack.gif` | 21 |
| `StepAirPose` | `kirby_StepAirPose.gif` | 9 |
| `StepFall` | `kirby_StepFall.gif` | 31 |
| `Passive` | `kirby_Passive.gif` | 27 |
| `PassiveStandF` | `kirby_PassiveStandF.gif` | 41 |
| `PassiveStandB` | `kirby_PassiveStandB.gif` | 41 |
| `PassiveWall` | `kirby_PassiveWall.gif` | 27 |
| `PassiveWallJump` | `kirby_PassiveWallJump.gif` | 41 |
| `PassiveCeil` | `kirby_PassiveCeil.gif` | 26 |
| `Pass` | `kirby_Pass.gif` | 31 |

### Shield / guard  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `GuardOn` | `kirby_GuardOn.gif` | 7 |
| `Guard` | `kirby_Guard.gif` | 361 |
| `GuardOff` | `kirby_GuardOff.gif` | 15 |
| `GuardDamage` | `kirby_GuardDamage.gif` | 21 |
| `GuardOn_1` | `kirby_GuardOn_1.gif` | 7 |
| `Guard_1` | `kirby_Guard_1.gif` | 361 |

### Dodge / roll / escape  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `EscapeN` | `kirby_EscapeN.gif` | 26 |
| `EscapeF` | `kirby_EscapeF.gif` | 52 |
| `EscapeB` | `kirby_EscapeB.gif` | 52 |
| `EscapeAir` | `kirby_EscapeAir.gif` | 50 |

### Aerial attack  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackAirN` | `kirby_AttackAirN.gif` | 56 |
| `AttackAirF` | `kirby_AttackAirF.gif` | 51 |
| `AttackAirB` | `kirby_AttackAirB.gif` | 41 |
| `AttackAirHi` | `kirby_AttackAirHi.gif` | 48 |
| `AttackAirLw` | `kirby_AttackAirLw.gif` | 55 |

### Ground attack — jab / dash  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `Attack11` | `kirby_Attack11.gif` | 18 |
| `Attack12` | `kirby_Attack12.gif` | 21 |
| `Attack100Start` | `kirby_Attack100Start.gif` | 8 |
| `Attack100` | `kirby_Attack100.gif` | 21 |
| `AttackEnd` | `kirby_AttackEnd.gif` | 10 |
| `AttackDash` | `kirby_AttackDash.gif` | 49 |
| `AttackDashAir` | `kirby_AttackDashAir.gif` | 49 |

### Ground attack — tilt  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS3Hi` | `kirby_AttackS3Hi.gif` | 33 |
| `AttackS3S` | `kirby_AttackS3S.gif` | 33 |
| `AttackS3Lw` | `kirby_AttackS3Lw.gif` | 33 |
| `AttackHi3` | `kirby_AttackHi3.gif` | 24 |
| `AttackLw3` | `kirby_AttackLw3.gif` | 30 |

### Ground attack — smash  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS4Start` | `kirby_AttackS4Start.gif` | 5 |
| `AttackS4Hi` | `kirby_AttackS4Hi.gif` | 46 |
| `AttackS4S` | `kirby_AttackS4S.gif` | 46 |
| `AttackS4Lw` | `kirby_AttackS4Lw.gif` | 46 |
| `AttackS4Hold` | `kirby_AttackS4Hold.gif` | 61 |
| `AttackHi4Start` | `kirby_AttackHi4Start.gif` | 6 |
| `AttackHi4` | `kirby_AttackHi4.gif` | 42 |
| `AttackHi4Hold` | `kirby_AttackHi4Hold.gif` | 61 |
| `AttackLw4Start` | `kirby_AttackLw4Start.gif` | 5 |
| `AttackLw4` | `kirby_AttackLw4.gif` | 52 |
| `AttackLw4Hold` | `kirby_AttackLw4Hold.gif` | 61 |

### Grab  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `Catch` | `kirby_Catch.gif` | 31 |
| `CatchDash` | `kirby_CatchDash.gif` | 40 |
| `CatchTurn` | `kirby_CatchTurn.gif` | 36 |
| `CatchWait` | `kirby_CatchWait.gif` | 31 |
| `CatchAttack` | `kirby_CatchAttack.gif` | 30 |
| `CatchCut` | `kirby_CatchCut.gif` | 30 |

### Throw  (14)

| Subaction | GIF | Frames |
|---|---|---|
| `ThrowCutter` | `kirby_ThrowCutter.gif` | 38 |
| `ThrowCutter_1` | `kirby_ThrowCutter_1.gif` | 38 |
| `ThrowB` | `kirby_ThrowB.gif` | 50 |
| `ThrowF` | `kirby_ThrowF.gif` | 62 |
| `ThrowHi` | `kirby_ThrowHi.gif` | 80 |
| `ThrowLw` | `kirby_ThrowLw.gif` | 62 |
| `ThrownB` | `kirby_ThrownB.gif` | 50 |
| `ThrownF` | `kirby_ThrownF.gif` | 62 |
| `ThrownHi` | `kirby_ThrownHi.gif` | 80 |
| `ThrownLw` | `kirby_ThrownLw.gif` | 88 |
| `ThrownDxB` | `kirby_ThrownDxB.gif` | 49 |
| `ThrownDxF` | `kirby_ThrownDxF.gif` | 62 |
| `ThrownDxHi` | `kirby_ThrownDxHi.gif` | 80 |
| `ThrownDxLw` | `kirby_ThrownDxLw.gif` | 95 |

### Grabbed / carried (victim)  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `CapturePulledHi` | `kirby_CapturePulledHi.gif` | 20 |
| `CaptureWaitHi` | `kirby_CaptureWaitHi.gif` | 106 |
| `CaptureDamageHi` | `kirby_CaptureDamageHi.gif` | 20 |
| `CapturePulledLw` | `kirby_CapturePulledLw.gif` | 20 |
| `CaptureWaitLw` | `kirby_CaptureWaitLw.gif` | 131 |
| `CaptureDamageLw` | `kirby_CaptureDamageLw.gif` | 20 |
| `CaptureCut` | `kirby_CaptureCut.gif` | 31 |
| `CaptureJump` | `kirby_CaptureJump.gif` | 51 |
| `Swallowed` | `kirby_Swallowed.gif` | 11 |

### Damage / hitstun  (21)

| Subaction | GIF | Frames |
|---|---|---|
| `DamageFall` | `kirby_DamageFall.gif` | 31 |
| `DamageHi1` | `kirby_DamageHi1.gif` | 12 |
| `DamageHi2` | `kirby_DamageHi2.gif` | 24 |
| `DamageHi3` | `kirby_DamageHi3.gif` | 30 |
| `DamageN1` | `kirby_DamageN1.gif` | 12 |
| `DamageN2` | `kirby_DamageN2.gif` | 24 |
| `DamageN3` | `kirby_DamageN3.gif` | 30 |
| `DamageLw1` | `kirby_DamageLw1.gif` | 12 |
| `DamageLw2` | `kirby_DamageLw2.gif` | 24 |
| `DamageLw3` | `kirby_DamageLw3.gif` | 42 |
| `DamageAir1` | `kirby_DamageAir1.gif` | 12 |
| `DamageAir2` | `kirby_DamageAir2.gif` | 24 |
| `DamageAir3` | `kirby_DamageAir3.gif` | 30 |
| `DamageFlyHi` | `kirby_DamageFlyHi.gif` | 67 |
| `DamageFlyN` | `kirby_DamageFlyN.gif` | 67 |
| `DamageFlyLw` | `kirby_DamageFlyLw.gif` | 67 |
| `DamageFlyTop` | `kirby_DamageFlyTop.gif` | 85 |
| `DamageFlyRoll` | `kirby_DamageFlyRoll.gif` | 17 |
| `DamageElec` | `kirby_DamageElec.gif` | 81 |
| `WallDamage` | `kirby_WallDamage.gif` | 31 |
| `DamageFace` | `kirby_DamageFace.gif` | 2 |

### Downed / getup  (19)

| Subaction | GIF | Frames |
|---|---|---|
| `DownBoundU` | `kirby_DownBoundU.gif` | 27 |
| `DownWaitU` | `kirby_DownWaitU.gif` | 61 |
| `DownDamageU` | `kirby_DownDamageU.gif` | 14 |
| `DownDamageU3` | `kirby_DownDamageU3.gif` | 40 |
| `DownEatU` | `kirby_DownEatU.gif` | 30 |
| `DownStandU` | `kirby_DownStandU.gif` | 30 |
| `DownAttackU` | `kirby_DownAttackU.gif` | 50 |
| `DownForwardU` | `kirby_DownForwardU.gif` | 36 |
| `DownBackU` | `kirby_DownBackU.gif` | 36 |
| `DownBoundD` | `kirby_DownBoundD.gif` | 27 |
| `DownWaitD` | `kirby_DownWaitD.gif` | 76 |
| `DownDamageD` | `kirby_DownDamageD.gif` | 14 |
| `DownDamageD3` | `kirby_DownDamageD3.gif` | 40 |
| `DownEatD` | `kirby_DownEatD.gif` | 30 |
| `DownStandD` | `kirby_DownStandD.gif` | 30 |
| `DownAttackD` | `kirby_DownAttackD.gif` | 50 |
| `DownForwardD` | `kirby_DownForwardD.gif` | 36 |
| `DownBackD` | `kirby_DownBackD.gif` | 36 |
| `DownSpotU` | `kirby_DownSpotU.gif` | 30 |

### Dizzy / sleep  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `FuraFura` | `kirby_FuraFura.gif` | 101 |
| `FuraFuraStartU` | `kirby_FuraFuraStartU.gif` | 50 |
| `FuraFuraStartD` | `kirby_FuraFuraStartD.gif` | 50 |
| `FuraFuraEnd` | `kirby_FuraFuraEnd.gif` | 50 |
| `FuraSleepStart` | `kirby_FuraSleepStart.gif` | 33 |
| `FuraSleepLoop` | `kirby_FuraSleepLoop.gif` | 77 |
| `FuraSleepEnd` | `kirby_FuraSleepEnd.gif` | 76 |

### Ledge (cliff hang / getup)  (12)

| Subaction | GIF | Frames |
|---|---|---|
| `CliffCatch` | `kirby_CliffCatch.gif` | 21 |
| `CliffWait` | `kirby_CliffWait.gif` | 61 |
| `CliffAttackQuick` | `kirby_CliffAttackQuick.gif` | 56 |
| `CliffClimbQuick` | `kirby_CliffClimbQuick.gif` | 34 |
| `CliffEscapeQuick` | `kirby_CliffEscapeQuick.gif` | 60 |
| `CliffJumpQuick1` | `kirby_CliffJumpQuick1.gif` | 15 |
| `CliffJumpQuick2` | `kirby_CliffJumpQuick2.gif` | 25 |
| `CliffAttackSlow` | `kirby_CliffAttackSlow.gif` | 70 |
| `CliffClimbSlow` | `kirby_CliffClimbSlow.gif` | 60 |
| `CliffEscapeSlow` | `kirby_CliffEscapeSlow.gif` | 80 |
| `CliffJumpSlow1` | `kirby_CliffJumpSlow1.gif` | 18 |
| `CliffJumpSlow2` | `kirby_CliffJumpSlow2.gif` | 32 |

### Trip / slip  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `MissFoot` | `kirby_MissFoot.gif` | 27 |
| `SlipDown` | `kirby_SlipDown.gif` | 40 |
| `Slip` | `kirby_Slip.gif` | 30 |
| `SlipTurn` | `kirby_SlipTurn.gif` | 36 |
| `SlipDash` | `kirby_SlipDash.gif` | 46 |
| `SlipWait` | `kirby_SlipWait.gif` | 61 |
| `SlipStand` | `kirby_SlipStand.gif` | 22 |
| `SlipAttack` | `kirby_SlipAttack.gif` | 50 |
| `SlipEscapeF` | `kirby_SlipEscapeF.gif` | 29 |
| `SlipEscapeB` | `kirby_SlipEscapeB.gif` | 29 |

### Swim / drown  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SwimRise` | `kirby_SwimRise.gif` | 31 |
| `SwimUp` | `kirby_SwimUp.gif` | 17 |
| `SwimUpDamage` | `kirby_SwimUpDamage.gif` | 25 |
| `Swim` | `kirby_Swim.gif` | 71 |
| `SwimF` | `kirby_SwimF.gif` | 31 |
| `SwimEnd` | `kirby_SwimEnd.gif` | 20 |
| `SwimTurn` | `kirby_SwimTurn.gif` | 20 |
| `SwimDrown` | `kirby_SwimDrown.gif` | 61 |
| `SwimDrownOut` | `kirby_SwimDrownOut.gif` | 41 |

### Ladder / rope  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `LadderWait` | `kirby_LadderWait.gif` | 77 |
| `LadderUp` | `kirby_LadderUp.gif` | 15 |
| `LadderDown` | `kirby_LadderDown.gif` | 41 |
| `LadderCatchR` | `kirby_LadderCatchR.gif` | 15 |
| `LadderCatchL` | `kirby_LadderCatchL.gif` | 15 |
| `LadderCatchAirR` | `kirby_LadderCatchAirR.gif` | 15 |
| `LadderCatchAirL` | `kirby_LadderCatchAirL.gif` | 15 |
| `LadderCatchEndR` | `kirby_LadderCatchEndR.gif` | 16 |
| `LadderCatchEndL` | `kirby_LadderCatchEndL.gif` | 16 |

### Inhale-hold (mouthful) locomotion (Eat*)  (9)

Kirby holding an inhaled opponent — walk/turn/jump/land while carrying the mouthful before spitting or swallowing.

| Subaction | GIF | Frames |
|---|---|---|
| `EatWait` | `kirby_EatWait.gif` | 81 |
| `EatWalkSlow` | `kirby_EatWalkSlow.gif` | 61 |
| `EatWalkMiddle` | `kirby_EatWalkMiddle.gif` | 46 |
| `EatWalkFast` | `kirby_EatWalkFast.gif` | 46 |
| `EatJump1` | `kirby_EatJump1.gif` | 18 |
| `EatJump2` | `kirby_EatJump2.gif` | 31 |
| `EatWait_1` | `kirby_EatWait_1.gif` | 81 |
| `EatLanding` | `kirby_EatLanding.gif` | 31 |
| `EatTurn` | `kirby_EatTurn.gif` | 15 |

### Item handling (engine-generic)  (120)

Engine-generic item carry/throw/swing subactions shared by every fighter, not Kirby-specific.

| Subaction | GIF | Frames |
|---|---|---|
| `ItemHandSmash` | `kirby_ItemHandSmash.gif` | 2 |
| `LightGet` | `kirby_LightGet.gif` | 8 |
| `LightWalkGet` | `kirby_LightWalkGet.gif` | 24 |
| `LightEat` | `kirby_LightEat.gif` | 20 |
| `LightWalkEat` | `kirby_LightWalkEat.gif` | 24 |
| `HeavyGet` | `kirby_HeavyGet.gif` | 34 |
| `HeavyWalk1` | `kirby_HeavyWalk1.gif` | 45 |
| `HeavyWalk2` | `kirby_HeavyWalk2.gif` | 45 |
| `LightThrowDrop` | `kirby_LightThrowDrop.gif` | 24 |
| `LightThrowF` | `kirby_LightThrowF.gif` | 25 |
| `LightThrowB` | `kirby_LightThrowB.gif` | 25 |
| `LightThrowHi` | `kirby_LightThrowHi.gif` | 24 |
| `LightThrowLw` | `kirby_LightThrowLw.gif` | 24 |
| `LightThrowF_1` | `kirby_LightThrowF_1.gif` | 25 |
| `LightThrowB_1` | `kirby_LightThrowB_1.gif` | 25 |
| `LightThrowHi_1` | `kirby_LightThrowHi_1.gif` | 24 |
| `LightThrowLw_1` | `kirby_LightThrowLw_1.gif` | 24 |
| `LightThrowDash` | `kirby_LightThrowDash.gif` | 40 |
| `LightThrowAirF` | `kirby_LightThrowAirF.gif` | 26 |
| `LightThrowAirB` | `kirby_LightThrowAirB.gif` | 25 |
| `LightThrowAirHi` | `kirby_LightThrowAirHi.gif` | 25 |
| `LightThrowAirLw` | `kirby_LightThrowAirLw.gif` | 24 |
| `LightThrowAirF_1` | `kirby_LightThrowAirF_1.gif` | 26 |
| `LightThrowAirB_1` | `kirby_LightThrowAirB_1.gif` | 25 |
| `LightThrowAirHi_1` | `kirby_LightThrowAirHi_1.gif` | 25 |
| `LightThrowAirLw_1` | `kirby_LightThrowAirLw_1.gif` | 24 |
| `HeavyThrowF` | `kirby_HeavyThrowF.gif` | 45 |
| `HeavyThrowB` | `kirby_HeavyThrowB.gif` | 48 |
| `HeavyThrowHi` | `kirby_HeavyThrowHi.gif` | 40 |
| `HeavyThrowLw` | `kirby_HeavyThrowLw.gif` | 45 |
| `HeavyThrowF_1` | `kirby_HeavyThrowF_1.gif` | 45 |
| `HeavyThrowB_1` | `kirby_HeavyThrowB_1.gif` | 48 |
| `HeavyThrowHi_1` | `kirby_HeavyThrowHi_1.gif` | 40 |
| `HeavyThrowLw_1` | `kirby_HeavyThrowLw_1.gif` | 45 |
| `Swing1` | `kirby_Swing1.gif` | 24 |
| `Swing3` | `kirby_Swing3.gif` | 42 |
| `Swing4Start` | `kirby_Swing4Start.gif` | 7 |
| `Swing4` | `kirby_Swing4.gif` | 54 |
| `Swing4Hold` | `kirby_Swing4Hold.gif` | 61 |
| `SwingDash` | `kirby_SwingDash.gif` | 46 |
| `Swing1_1` | `kirby_Swing1_1.gif` | 24 |
| `Swing3_1` | `kirby_Swing3_1.gif` | 42 |
| `Swing4Bat` | `kirby_Swing4Bat.gif` | 90 |
| `SwingDash_1` | `kirby_SwingDash_1.gif` | 46 |
| `Swing1_2` | `kirby_Swing1_2.gif` | 24 |
| `Swing3_2` | `kirby_Swing3_2.gif` | 42 |
| `Swing4Start_1` | `kirby_Swing4Start_1.gif` | 7 |
| `Swing4_1` | `kirby_Swing4_1.gif` | 54 |
| `Swing4Hold_1` | `kirby_Swing4Hold_1.gif` | 61 |
| `SwingDash_2` | `kirby_SwingDash_2.gif` | 46 |
| `Swing1_3` | `kirby_Swing1_3.gif` | 24 |
| `Swing3_3` | `kirby_Swing3_3.gif` | 42 |
| `Swing4Start_2` | `kirby_Swing4Start_2.gif` | 7 |
| `Swing4_2` | `kirby_Swing4_2.gif` | 54 |
| `Swing4Hold_2` | `kirby_Swing4Hold_2.gif` | 61 |
| `SwingDash_3` | `kirby_SwingDash_3.gif` | 46 |
| `Swing1_4` | `kirby_Swing1_4.gif` | 24 |
| `Swing3_4` | `kirby_Swing3_4.gif` | 42 |
| `Swing4Start_3` | `kirby_Swing4Start_3.gif` | 7 |
| `Swing4_3` | `kirby_Swing4_3.gif` | 54 |
| `Swing4Hold_3` | `kirby_Swing4Hold_3.gif` | 61 |
| `SwingDash_4` | `kirby_SwingDash_4.gif` | 46 |
| `ItemHammerWait` | `kirby_ItemHammerWait.gif` | 17 |
| `ItemHammerMove` | `kirby_ItemHammerMove.gif` | 17 |
| `ItemHammerAir` | `kirby_ItemHammerAir.gif` | 17 |
| `ItemHammerWait_1` | `kirby_ItemHammerWait_1.gif` | 17 |
| `ItemHammerMove_1` | `kirby_ItemHammerMove_1.gif` | 17 |
| `ItemHammerAir_1` | `kirby_ItemHammerAir_1.gif` | 17 |
| `ItemDragoonRide` | `kirby_ItemDragoonRide.gif` | 61 |
| `ItemScrew` | `kirby_ItemScrew.gif` | 41 |
| `ItemScrew_1` | `kirby_ItemScrew_1.gif` | 41 |
| `ItemScrewFall` | `kirby_ItemScrewFall.gif` | 51 |
| `ItemDragoonGet` | `kirby_ItemDragoonGet.gif` | 60 |
| `ItemDragoonRide_1` | `kirby_ItemDragoonRide_1.gif` | 61 |
| `ItemBig` | `kirby_ItemBig.gif` | 60 |
| `ItemSmall` | `kirby_ItemSmall.gif` | 60 |
| `ItemLegsWait` | `kirby_ItemLegsWait.gif` | 51 |
| `ItemLegsSlowF` | `kirby_ItemLegsSlowF.gif` | 31 |
| `ItemLegsMiddleF` | `kirby_ItemLegsMiddleF.gif` | 25 |
| `ItemLegsFastF` | `kirby_ItemLegsFastF.gif` | 21 |
| `ItemLegsBrakeF` | `kirby_ItemLegsBrakeF.gif` | 2 |
| `ItemLegsDashF` | `kirby_ItemLegsDashF.gif` | 24 |
| `ItemLegsSlowB` | `kirby_ItemLegsSlowB.gif` | 41 |
| `ItemLegsMiddleB` | `kirby_ItemLegsMiddleB.gif` | 31 |
| `ItemLegsFastB` | `kirby_ItemLegsFastB.gif` | 25 |
| `ItemLegsBrakeB` | `kirby_ItemLegsBrakeB.gif` | 2 |
| `ItemLegsDashB` | `kirby_ItemLegsDashB.gif` | 24 |
| `ItemLegsJumpSquat` | `kirby_ItemLegsJumpSquat.gif` | 5 |
| `ItemLegsLanding` | `kirby_ItemLegsLanding.gif` | 16 |
| `ItemShoot` | `kirby_ItemShoot.gif` | 30 |
| `ItemShootAir` | `kirby_ItemShootAir.gif` | 30 |
| `ItemShoot_1` | `kirby_ItemShoot_1.gif` | 30 |
| `ItemShootAir_1` | `kirby_ItemShootAir_1.gif` | 30 |
| `ItemShoot_2` | `kirby_ItemShoot_2.gif` | 30 |
| `ItemShootAir_2` | `kirby_ItemShootAir_2.gif` | 30 |
| `ItemScopeStart` | `kirby_ItemScopeStart.gif` | 16 |
| `ItemScopeRapid` | `kirby_ItemScopeRapid.gif` | 9 |
| `ItemScopeFire` | `kirby_ItemScopeFire.gif` | 31 |
| `ItemScopeEnd` | `kirby_ItemScopeEnd.gif` | 21 |
| `ItemScopeAirStart` | `kirby_ItemScopeAirStart.gif` | 16 |
| `ItemScopeAirRapid` | `kirby_ItemScopeAirRapid.gif` | 9 |
| `ItemScopeAirFire` | `kirby_ItemScopeAirFire.gif` | 31 |
| `ItemScopeAirEnd` | `kirby_ItemScopeAirEnd.gif` | 21 |
| `ItemScopeStart_1` | `kirby_ItemScopeStart_1.gif` | 16 |
| `ItemScopeRapid_1` | `kirby_ItemScopeRapid_1.gif` | 9 |
| `ItemScopeFire_1` | `kirby_ItemScopeFire_1.gif` | 31 |
| `ItemScopeEnd_1` | `kirby_ItemScopeEnd_1.gif` | 21 |
| `ItemScopeAirStart_1` | `kirby_ItemScopeAirStart_1.gif` | 16 |
| `ItemScopeAirRapid_1` | `kirby_ItemScopeAirRapid_1.gif` | 9 |
| `ItemScopeAirFire_1` | `kirby_ItemScopeAirFire_1.gif` | 31 |
| `ItemScopeAirEnd_1` | `kirby_ItemScopeAirEnd_1.gif` | 21 |
| `ItemLauncher` | `kirby_ItemLauncher.gif` | 151 |
| `ItemLauncherFire` | `kirby_ItemLauncherFire.gif` | 12 |
| `ItemLauncherAirFire` | `kirby_ItemLauncherAirFire.gif` | 12 |
| `ItemLauncher_1` | `kirby_ItemLauncher_1.gif` | 151 |
| `ItemLauncherFire_1` | `kirby_ItemLauncherFire_1.gif` | 12 |
| `ItemLauncherAirFire_1` | `kirby_ItemLauncherAirFire_1.gif` | 12 |
| `ItemLauncherFall` | `kirby_ItemLauncherFall.gif` | 9 |
| `ItemAssist` | `kirby_ItemAssist.gif` | 60 |
| `ItemScrew_2` | `kirby_ItemScrew_2.gif` | 41 |

### Special moves & copy-ability slots (Special*)  (170)

Kirby's own specials are `SpecialN` (Inhale/Swallow), `SpecialS` (Hammer), `SpecialHi` (Final Cutter) and `SpecialLw` (Stone). The many numbered `SpecialN_<k>` / `SpecialAir*_<k>` variants are the **copy-ability slots** — one Inhale-copied neutral special per fighter Kirby can swallow. The `.pac` action table enumerates them by index, not by source-fighter name, so they are listed here by their raw subaction id.

| Subaction | GIF | Frames |
|---|---|---|
| `SpecialNBittenStart` | `kirby_SpecialNBittenStart.gif` | 8 |
| `SpecialNBitten` | `kirby_SpecialNBitten.gif` | 40 |
| `SpecialNBittenEnd` | `kirby_SpecialNBittenEnd.gif` | 20 |
| `SpecialAirNBittenStart` | `kirby_SpecialAirNBittenStart.gif` | 8 |
| `SpecialAirNBitten` | `kirby_SpecialAirNBitten.gif` | 40 |
| `SpecialAirNBittenEnd` | `kirby_SpecialAirNBittenEnd.gif` | 20 |
| `SpecialNDxBittenStart` | `kirby_SpecialNDxBittenStart.gif` | 8 |
| `SpecialNDxBitten` | `kirby_SpecialNDxBitten.gif` | 40 |
| `SpecialNDxBittenEnd` | `kirby_SpecialNDxBittenEnd.gif` | 20 |
| `SpecialAirNDxBittenStart` | `kirby_SpecialAirNDxBittenStart.gif` | 8 |
| `SpecialAirNDxBitten` | `kirby_SpecialAirNDxBitten.gif` | 40 |
| `SpecialAirNDxBittenEnd` | `kirby_SpecialAirNDxBittenEnd.gif` | 20 |
| `SpecialNBigBittenStart` | `kirby_SpecialNBigBittenStart.gif` | 8 |
| `SpecialNBigBitten` | `kirby_SpecialNBigBitten.gif` | 40 |
| `SpecialNBigBittenEnd` | `kirby_SpecialNBigBittenEnd.gif` | 20 |
| `SpecialAirNBigBittenStart` | `kirby_SpecialAirNBigBittenStart.gif` | 8 |
| `SpecialAirNBigBitten` | `kirby_SpecialAirNBigBitten.gif` | 40 |
| `SpecialAirNBigBittenEnd` | `kirby_SpecialAirNBigBittenEnd.gif` | 20 |
| `SpecialNEgg` | `kirby_SpecialNEgg.gif` | 14 |
| `SpecialNStart` | `kirby_SpecialNStart.gif` | 11 |
| `SpecialNLoop` | `kirby_SpecialNLoop.gif` | 19 |
| `SpecialNEnd` | `kirby_SpecialNEnd.gif` | 20 |
| `SpecialNLoop_1` | `kirby_SpecialNLoop_1.gif` | 19 |
| `SpecialNSwallow` | `kirby_SpecialNSwallow.gif` | 25 |
| `SpecialNFood` | `kirby_SpecialNFood.gif` | 38 |
| `SpecialNBomb` | `kirby_SpecialNBomb.gif` | 72 |
| `SpecialNLarge` | `kirby_SpecialNLarge.gif` | 86 |
| `SpecialNEat` | `kirby_SpecialNEat.gif` | 52 |
| `SpecialNSpit` | `kirby_SpecialNSpit.gif` | 31 |
| `SpecialAirNStart` | `kirby_SpecialAirNStart.gif` | 11 |
| `SpecialAirNLoop` | `kirby_SpecialAirNLoop.gif` | 19 |
| `SpecialAirNEnd` | `kirby_SpecialAirNEnd.gif` | 20 |
| `SpecialAirNLoop_1` | `kirby_SpecialAirNLoop_1.gif` | 19 |
| `SpecialAirNSwallow` | `kirby_SpecialAirNSwallow.gif` | 25 |
| `SpecialAirNFood` | `kirby_SpecialAirNFood.gif` | 38 |
| `SpecialAirNBomb` | `kirby_SpecialAirNBomb.gif` | 72 |
| `SpecialAirNLarge` | `kirby_SpecialAirNLarge.gif` | 86 |
| `SpecialAirNEat` | `kirby_SpecialAirNEat.gif` | 52 |
| `SpecialAirNSpit` | `kirby_SpecialAirNSpit.gif` | 31 |
| `SpecialNDrink` | `kirby_SpecialNDrink.gif` | 31 |
| `SpecialS` | `kirby_SpecialS.gif` | 54 |
| `SpecialAirS` | `kirby_SpecialAirS.gif` | 50 |
| `SpecialAirHi` | `kirby_SpecialAirHi.gif` | 23 |
| `SpecialAirHi2` | `kirby_SpecialAirHi2.gif` | 36 |
| `SpecialAirHi3` | `kirby_SpecialAirHi3.gif` | 6 |
| `SpecialAirHi4` | `kirby_SpecialAirHi4.gif` | 35 |
| `SpecialAirHi_1` | `kirby_SpecialAirHi_1.gif` | 23 |
| `SpecialAirHi2_1` | `kirby_SpecialAirHi2_1.gif` | 36 |
| `SpecialAirHi3_1` | `kirby_SpecialAirHi3_1.gif` | 6 |
| `SpecialAirHi4_1` | `kirby_SpecialAirHi4_1.gif` | 35 |
| `SpecialLw1` | `kirby_SpecialLw1.gif` | 14 |
| `SpecialLw2` | `kirby_SpecialLw2.gif` | 36 |
| `SpecialAirLw1` | `kirby_SpecialAirLw1.gif` | 15 |
| `SpecialAirLw2` | `kirby_SpecialAirLw2.gif` | 36 |
| `SpecialNStart_1` | `kirby_SpecialNStart_1.gif` | 20 |
| `SpecialAirNStart_1` | `kirby_SpecialAirNStart_1.gif` | 20 |
| `SpecialNEnd_1` | `kirby_SpecialNEnd_1.gif` | 27 |
| `SpecialAirNEnd_1` | `kirby_SpecialAirNEnd_1.gif` | 27 |
| `SpecialNStart_2` | `kirby_SpecialNStart_2.gif` | 20 |
| `SpecialAirNStart_2` | `kirby_SpecialAirNStart_2.gif` | 20 |
| `SpecialNStart_3` | `kirby_SpecialNStart_3.gif` | 20 |
| `SpecialNLoop_2` | `kirby_SpecialNLoop_2.gif` | 19 |
| `SpecialNEnd_2` | `kirby_SpecialNEnd_2.gif` | 20 |
| `SpecialAirNStart_3` | `kirby_SpecialAirNStart_3.gif` | 20 |
| `SpecialAirNLoop_2` | `kirby_SpecialAirNLoop_2.gif` | 19 |
| `SpecialAirNEnd_2` | `kirby_SpecialAirNEnd_2.gif` | 20 |
| `SpecialNStart_4` | `kirby_SpecialNStart_4.gif` | 20 |
| `SpecialNLoop_3` | `kirby_SpecialNLoop_3.gif` | 19 |
| `SpecialNEnd_3` | `kirby_SpecialNEnd_3.gif` | 20 |
| `SpecialAirNStart_4` | `kirby_SpecialAirNStart_4.gif` | 20 |
| `SpecialAirNLoop_3` | `kirby_SpecialAirNLoop_3.gif` | 19 |
| `SpecialAirNEnd_3` | `kirby_SpecialAirNEnd_3.gif` | 20 |
| `SpecialNStart_5` | `kirby_SpecialNStart_5.gif` | 20 |
| `SpecialNEnd_4` | `kirby_SpecialNEnd_4.gif` | 20 |
| `SpecialAirNStart_5` | `kirby_SpecialAirNStart_5.gif` | 20 |
| `SpecialAirNEnd_4` | `kirby_SpecialAirNEnd_4.gif` | 20 |
| `SpecialNStart_6` | `kirby_SpecialNStart_6.gif` | 20 |
| `SpecialNEnd_5` | `kirby_SpecialNEnd_5.gif` | 20 |
| `SpecialAirNStart_6` | `kirby_SpecialAirNStart_6.gif` | 20 |
| `SpecialAirNEnd_5` | `kirby_SpecialAirNEnd_5.gif` | 20 |
| `SpecialNStart_7` | `kirby_SpecialNStart_7.gif` | 20 |
| `SpecialAirNStart_7` | `kirby_SpecialAirNStart_7.gif` | 20 |
| `SpecialNEnd_6` | `kirby_SpecialNEnd_6.gif` | 20 |
| `SpecialNFood_1` | `kirby_SpecialNFood_1.gif` | 38 |
| `SpecialNBomb_1` | `kirby_SpecialNBomb_1.gif` | 72 |
| `SpecialNLarge_1` | `kirby_SpecialNLarge_1.gif` | 86 |
| `SpecialNEat_1` | `kirby_SpecialNEat_1.gif` | 52 |
| `SpecialAirNEnd_6` | `kirby_SpecialAirNEnd_6.gif` | 20 |
| `SpecialAirNFood_1` | `kirby_SpecialAirNFood_1.gif` | 38 |
| `SpecialAirNBomb_1` | `kirby_SpecialAirNBomb_1.gif` | 72 |
| `SpecialAirNLarge_1` | `kirby_SpecialAirNLarge_1.gif` | 86 |
| `SpecialAirNEat_1` | `kirby_SpecialAirNEat_1.gif` | 52 |
| `SpecialNStart_8` | `kirby_SpecialNStart_8.gif` | 16 |
| `SpecialAirNStart_8` | `kirby_SpecialAirNStart_8.gif` | 16 |
| `SpecialNStart_9` | `kirby_SpecialNStart_9.gif` | 20 |
| `SpecialNLoop_4` | `kirby_SpecialNLoop_4.gif` | 19 |
| `SpecialNEnd_7` | `kirby_SpecialNEnd_7.gif` | 20 |
| `SpecialAirNStart_9` | `kirby_SpecialAirNStart_9.gif` | 20 |
| `SpecialAirNLoop_4` | `kirby_SpecialAirNLoop_4.gif` | 19 |
| `SpecialAirNEnd_7` | `kirby_SpecialAirNEnd_7.gif` | 20 |
| `SpecialNStart_10` | `kirby_SpecialNStart_10.gif` | 16 |
| `SpecialNEnd_8` | `kirby_SpecialNEnd_8.gif` | 20 |
| `SpecialAirNStart_10` | `kirby_SpecialAirNStart_10.gif` | 16 |
| `SpecialAirNEnd_8` | `kirby_SpecialAirNEnd_8.gif` | 20 |
| `SpecialNStart_11` | `kirby_SpecialNStart_11.gif` | 20 |
| `SpecialNLoop_5` | `kirby_SpecialNLoop_5.gif` | 19 |
| `SpecialAirNStart_11` | `kirby_SpecialAirNStart_11.gif` | 20 |
| `SpecialAirNLoop_5` | `kirby_SpecialAirNLoop_5.gif` | 19 |
| `SpecialNStart_12` | `kirby_SpecialNStart_12.gif` | 20 |
| `SpecialNLoop_6` | `kirby_SpecialNLoop_6.gif` | 19 |
| `SpecialNEnd_9` | `kirby_SpecialNEnd_9.gif` | 20 |
| `SpecialNEnd_10` | `kirby_SpecialNEnd_10.gif` | 20 |
| `SpecialAirNStart_12` | `kirby_SpecialAirNStart_12.gif` | 20 |
| `SpecialAirNLoop_6` | `kirby_SpecialAirNLoop_6.gif` | 19 |
| `SpecialAirNEnd_9` | `kirby_SpecialAirNEnd_9.gif` | 20 |
| `SpecialAirNEnd_10` | `kirby_SpecialAirNEnd_10.gif` | 20 |
| `SpecialNStart_13` | `kirby_SpecialNStart_13.gif` | 20 |
| `SpecialNLoop_7` | `kirby_SpecialNLoop_7.gif` | 19 |
| `SpecialNEnd_11` | `kirby_SpecialNEnd_11.gif` | 20 |
| `SpecialNEnd_12` | `kirby_SpecialNEnd_12.gif` | 20 |
| `SpecialAirNStart_13` | `kirby_SpecialAirNStart_13.gif` | 20 |
| `SpecialAirNLoop_7` | `kirby_SpecialAirNLoop_7.gif` | 19 |
| `SpecialAirNEnd_11` | `kirby_SpecialAirNEnd_11.gif` | 20 |
| `SpecialAirNEnd_12` | `kirby_SpecialAirNEnd_12.gif` | 20 |
| `SpecialNStart_14` | `kirby_SpecialNStart_14.gif` | 20 |
| `SpecialAirNStart_14` | `kirby_SpecialAirNStart_14.gif` | 20 |
| `SpecialNStart_15` | `kirby_SpecialNStart_15.gif` | 20 |
| `SpecialNLoop_8` | `kirby_SpecialNLoop_8.gif` | 19 |
| `SpecialNEnd_13` | `kirby_SpecialNEnd_13.gif` | 20 |
| `SpecialNLoop_9` | `kirby_SpecialNLoop_9.gif` | 19 |
| `SpecialNSwallow_1` | `kirby_SpecialNSwallow_1.gif` | 25 |
| `SpecialNFood_2` | `kirby_SpecialNFood_2.gif` | 38 |
| `SpecialNBomb_2` | `kirby_SpecialNBomb_2.gif` | 72 |
| `SpecialNLarge_2` | `kirby_SpecialNLarge_2.gif` | 86 |
| `SpecialNEat_2` | `kirby_SpecialNEat_2.gif` | 52 |
| `SpecialNSpit_1` | `kirby_SpecialNSpit_1.gif` | 31 |
| `SpecialAirNStart_15` | `kirby_SpecialAirNStart_15.gif` | 20 |
| `SpecialAirNLoop_8` | `kirby_SpecialAirNLoop_8.gif` | 19 |
| `SpecialAirNEnd_13` | `kirby_SpecialAirNEnd_13.gif` | 20 |
| `SpecialAirNLoop_9` | `kirby_SpecialAirNLoop_9.gif` | 19 |
| `SpecialAirNSwallow_1` | `kirby_SpecialAirNSwallow_1.gif` | 25 |
| `SpecialAirNFood_2` | `kirby_SpecialAirNFood_2.gif` | 38 |
| `SpecialAirNBomb_2` | `kirby_SpecialAirNBomb_2.gif` | 72 |
| `SpecialAirNLarge_2` | `kirby_SpecialAirNLarge_2.gif` | 86 |
| `SpecialAirNEat_2` | `kirby_SpecialAirNEat_2.gif` | 52 |
| `SpecialAirNSpit_1` | `kirby_SpecialAirNSpit_1.gif` | 31 |
| `SpecialNStart_16` | `kirby_SpecialNStart_16.gif` | 20 |
| `SpecialNLoop_10` | `kirby_SpecialNLoop_10.gif` | 19 |
| `SpecialNEnd_14` | `kirby_SpecialNEnd_14.gif` | 20 |
| `SpecialAirNStart_16` | `kirby_SpecialAirNStart_16.gif` | 20 |
| `SpecialAirNLoop_10` | `kirby_SpecialAirNLoop_10.gif` | 19 |
| `SpecialAirNEnd_14` | `kirby_SpecialAirNEnd_14.gif` | 20 |
| `SpecialNStart_17` | `kirby_SpecialNStart_17.gif` | 20 |
| `SpecialNLoop_11` | `kirby_SpecialNLoop_11.gif` | 19 |
| `SpecialNEnd_15` | `kirby_SpecialNEnd_15.gif` | 20 |
| `SpecialAirNStart_17` | `kirby_SpecialAirNStart_17.gif` | 20 |
| `SpecialAirNLoop_11` | `kirby_SpecialAirNLoop_11.gif` | 19 |
| `SpecialAirNEnd_15` | `kirby_SpecialAirNEnd_15.gif` | 20 |
| `SpecialNStart_18` | `kirby_SpecialNStart_18.gif` | 20 |
| `SpecialAirNStart_18` | `kirby_SpecialAirNStart_18.gif` | 20 |
| `SpecialNStart_19` | `kirby_SpecialNStart_19.gif` | 20 |
| `SpecialAirNStart_19` | `kirby_SpecialAirNStart_19.gif` | 20 |
| `SpecialNStart_20` | `kirby_SpecialNStart_20.gif` | 20 |
| `SpecialNEnd_16` | `kirby_SpecialNEnd_16.gif` | 20 |
| `SpecialAirNStart_20` | `kirby_SpecialAirNStart_20.gif` | 20 |
| `SpecialAirNEnd_16` | `kirby_SpecialAirNEnd_16.gif` | 20 |
| `SpecialNStart_21` | `kirby_SpecialNStart_21.gif` | 20 |
| `SpecialAirNStart_21` | `kirby_SpecialAirNStart_21.gif` | 20 |
| `SpecialNStart_22` | `kirby_SpecialNStart_22.gif` | 20 |
| `SpecialAirNStart_22` | `kirby_SpecialAirNStart_22.gif` | 20 |

### Taunt / appeal  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `AppealHiR` | `kirby_AppealHiR.gif` | 120 |
| `AppealHiL` | `kirby_AppealHiL.gif` | 120 |
| `AppealSR` | `kirby_AppealSR.gif` | 120 |
| `AppealSL` | `kirby_AppealSL.gif` | 120 |
| `AppealLwR` | `kirby_AppealLwR.gif` | 60 |
| `AppealLwL` | `kirby_AppealLwL.gif` | 60 |

### Final Smash  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `FinalStartR` | `kirby_FinalStartR.gif` | 60 |
| `FinalStartL` | `kirby_FinalStartL.gif` | 60 |
| `FinalCalling` | `kirby_FinalCalling.gif` | 21 |
| `FinalUpNabe` | `kirby_FinalUpNabe.gif` | 21 |
| `Final` | `kirby_Final.gif` | 121 |
| `FinalDownNabe` | `kirby_FinalDownNabe.gif` | 31 |
| `FinalEndR` | `kirby_FinalEndR.gif` | 41 |
| `FinalEndL` | `kirby_FinalEndL.gif` | 41 |
| `FinalAirEndR` | `kirby_FinalAirEndR.gif` | 41 |
| `FinalAirEndL` | `kirby_FinalAirEndL.gif` | 41 |

### Entry / win / lose  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `EntryR` | `kirby_EntryR.gif` | 121 |
| `EntryL` | `kirby_EntryL.gif` | 121 |
| `Win1` | `kirby_Win1.gif` | 176 |
| `Win1Wait` | `kirby_Win1Wait.gif` | 71 |
| `Win2` | `kirby_Win2.gif` | 176 |
| `Win2Wait` | `kirby_Win2Wait.gif` | 71 |
| `Win3` | `kirby_Win3.gif` | 176 |
| `Win3Wait` | `kirby_Win3Wait.gif` | 71 |
| `Lose` | `kirby_Lose.gif` | 161 |

### Misc / situational  (2)

| Subaction | GIF | Frames |
|---|---|---|
| `Rebound` | `kirby_Rebound.gif` | 31 |
| `GekikaraWait` | `kirby_GekikaraWait.gif` | 66 |

## Empty slots (0 frames, no GIF)  (240)

Enumerated in Kirby's action table but carrying no animation frames — no GIF is saved.
(The 14 `NONE`/`NONE_N` and unnamed unused ID slots are excluded entirely.)

`ItemHandPickUp`, `ItemHandHave`, `ItemHandGrip`, `CapturePulledSnake`, `CaptureWaitSnake`, `CaptureDamageSnake`, `CapturePulledSnake_1`, `CaptureWaitSnake_1`, `CaptureDamageSnake_1`, `CapturePulledDxSnake`, `CaptureWaitDxSnake`, `CaptureDamageDxSnake`, `CapturePulledDxSnake_1`, `CaptureWaitDxSnake_1`, `CaptureDamageDxSnake_1`, `CapturePulledBigSnake`, `CaptureWaitBigSnake`, `CaptureDamageBigSnake`, `CapturePulledBigSnake_1`, `CaptureWaitBigSnake_1`, `CaptureDamageBigSnake_1`, `DownSpotD`, `AirCatch`, `AirCatchPose`, `AirCatchHit`, `AirCatch_1`, `SmashThrowF`, `SmashThrowB`, `SmashThrowHi`, `SmashThrowLw`, `SmashThrowDash`, `SmashThrowAirF`, `SmashThrowAirB`, `SmashThrowAirHi`, `SmashThrowAirLw`, `Swing42`, `Swing42_1`, `Swing42_2`, `Swing42_3`, `ItemLauncherAir`, `RopeCatch`, `RopeFishing`, `SpecialHiCapture`, `SpecialHiDxCapture`, `SpecialSStickCapture`, `SpecialSStickAttackCapture`, `SpecialSStickJumpCapture`, `SpecialSDxStickCapture`, `SpecialSDxStickAttackCapture`, `SpecialSDxStickJumpCapture`, `ThrownZitabata`, `ThrownDxZitabata`, `ThrownGirlZitabata`, `ThrownFF`, `ThrownFB`, `ThrownFHi`, `ThrownFLw`, `ThrownDxFF`, `ThrownDxFB`, `ThrownDxFHi`, `ThrownDxFLw`, `GanonSpecialHiCapture`, `GanonSpecialHiDxCapture`, `SpecialSCapture`, `SpecialAirSCatchCapture`, `SpecialAirSFallCapture`, `SpecialAirSCapture`, `SpecialSDxCapture`, `SpecialAirSDxCatchCapture`, `SpecialAirSDxFallCapture`, `SpecialAirSDxCapture`, `SpecialSZitabata`, `SpecialSDxZitabata`, `Dark`, `Spycloak`, `DummySpecialLwToGround`, `DummySpecialLwToAir`, `SpecialN`, `SpecialNTurn`, `SpecialAirN`, `SpecialAirNTurn`, `SpecialN_1`, `SpecialAirN_1`, `SpecialNSpin`, `SpecialNSpin_1`, `SpecialNSpin_2`, `SpecialNCancel`, `SpecialNRebound`, `SpecialNHit`, `SpecialNLanding`, `SpecialN_2`, `SpecialAirN_2`, `SpecialN_3`, `SpecialAirN_3`, `SpecialN_4`, `SpecialAirN_4`, `SpecialNHold`, `SpecialNLight`, `SpecialNHeavy`, `SpecialAirNHold`, `SpecialAirNLight`, `SpecialAirNHeavy`, `SpecialN_5`, `SpecialAirN_5`, `SpecialNOpen`, `SpecialNOpenWait`, `SpecialNBiteStart`, `SpecialNBite`, `SpecialNBiteEnd`, `SpecialNItem`, `SpecialAirNOpen`, `SpecialNOpenWait_1`, `SpecialNBiteStart_1`, `SpecialNBite_1`, `SpecialAirNBiteEnd`, `SpecialAirNItem`, `SpecialN_6`, `SpecialAirN_6`, `SpecialNHit_1`, `SpecialAirNHit`, `SpecialN_7`, `SpecialAirN_7`, `SpecialN1`, `SpecialN1_1`, `SpecialN2`, `SpecialAirN1`, `SpecialAirN1_1`, `SpecialAirN2`, `SpecialNHold_1`, `SpecialNThrowHi`, `SpecialNThrowLw`, `SpecialNThrowM`, `SpecialNClose`, `SpecialAirNHold_1`, `SpecialAirNThrowHi`, `SpecialAirNThrowLw`, `SpecialAirNThrowM`, `SpecialNThrowM_1`, `SpecialAirNThrowM_1`, `SpecialN_8`, `SpecialAirN_8`, `SpecialNCancel_1`, `SpecialAirNCancel`, `SpecialN_9`, `SpecialNHold_2`, `SpecialNFire`, `SpecialN_10`, `SpecialAirN_9`, `SpecialAirNHold_2`, `SpecialAirNFire`, `SpecialAirN_10`, `SpecialNHold_3`, `SpecialNFire_1`, `SpecialAirNHold_3`, `SpecialNAirFire`, `SpecialNCancel_2`, `SpecialN_11`, `SpecialN_12`, `SpecialAirNCancel_1`, `SpecialAirN_11`, `SpecialAirN_12`, `SpecialN_13`, `SpecialAirN_13`, `SpecialNStartL`, `SpecialNStartR`, `SpecialNHold_4`, `SpecialNHold_5`, `SpecialN_14`, `SpecialN_15`, `SpecialN_16`, `SpecialNEndL`, `SpecialNEndR`, `SpecialAirNStartL`, `SpecialAirNStartR`, `SpecialAirNHold_4`, `SpecialAirNHold_5`, `SpecialN_17`, `SpecialN_18`, `SpecialN_19`, `SpecialAirNEndL`, `SpecialAirNEndR`, `SpecialN_20`, `SpecialNCharge`, `SpecialAirNCharge`, `SpecialNShoot`, `SpecialAirNShoot`, `SpecialNDanger`, `SpecialAirNDanger`, `SpecialNBlow`, `SpecialAirNBlow`, `SpecialN_21`, `SpecialAirN_14`, `SpecialNEatWait`, `SpecialNEatWalkSlow`, `SpecialNEatWalkMiddle`, `SpecialNEatWalkFast`, `SpecialAirNEatJump1`, `SpecialAirNEatJump2`, `SpecialNEatFall`, `SpecialNEatLanding`, `SpecialNEatTurn`, `SpecialN_22`, `SpecialAirN_15`, `SpecialN_23`, `SpecialNTurn_1`, `SpecialAirN_16`, `SpecialAirNTurn_1`, `SpecialNHold_6`, `SpecialAirNHold_6`, `SpecialNMax`, `SpecialAirNMax`, `SpecialNShoot_1`, `SpecialAirNShoot_1`, `SpecialN_24`, `SpecialNCancel_3`, `SpecialNHold_7`, `SpecialAirN_17`, `SpecialN_25`, `SpecialAirN_18`, `SpecialNHoldHi`, `SpecialNHoldS`, `SpecialNStoHi`, `SpecialNHitoS`, `SpecialNStoS`, `SpecialNFireS`, `SpecialNFireHi`, `SpecialAirNHoldHi`, `SpecialAirNHoldS`, `SpecialAirNStoHi`, `SpecialAirNHitoS`, `SpecialAirNStoS`, `SpecialAirNFireS`, `SpecialAirNFireHi`, `SpecialN_26`, `SpecialAirN_19`, `SpecialNShoot_2`, `SpecialNShootH`, `SpecialAirNShoot_2`, `SpecialAirNShootH`, `SpecialNLanding_1`

## Refs

#777 (the Mario precedent — mirror its structure) · #827 (the DK sibling) · #758 (the
GIF recipe) · #228 (Birky/Kirby epic) / #261 (Birky remaining-work tracker) · #824
(`-f Donkey` internal_name gotcha — Kirby's is the plain `Kirby`) · #125 (attack
VISUALS epic — the consumer) · #614/#753 (brawllib datamine env).
