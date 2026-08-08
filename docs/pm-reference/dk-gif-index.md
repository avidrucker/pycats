# Donkey Kong animation-GIF reference set — manifest (#827)

The **complete** browsable library of Project M 3.6 **Donkey Kong** subaction
animations, rendered via the [`tooling-brawllib-rs-gif-recipe.md`](../tooling-brawllib-rs-gif-recipe.md)
(#758) `gif_generator` recipe. It is the visual substrate for comparing pycats'
**Gnok** (the DK archetype, epic #779 / spec #794) move-for-move against the PM
source. Mirrors the Mario set ([`mario-gif-index.md`](./mario-gif-index.md), #777).

Each GIF is brawllib_rs's **hurtbox-capsule / skeleton** render (the rukaidata.com
renderer) — it shows *motion*, not the character skin. That is the right thing for
measuring and comparing movement; the capsules track the bones.

## ⚠ Copyright — GIFs are not committed

The `.pac` source **and** every derived GIF are copyrighted. The GIFs live **only**
in gitignored `repros/dk-gifs/` (per the repros-dir media policy) and are **never**
committed. This manifest is the only committed artifact — it makes the set
discoverable and reproducible **without** shipping a single frame.

## Reproduce the set

Prerequisites (datamine env, PM 3.6 `.pac` data) are in the recipe doc. Note the
**`-f Donkey`** filter: `gif_generator` matches the fighter's `cased_name` (which is
`Donkey`, not `Donkey Kong`), and `high_level_frame_data` matches its `internal_name`
(also `Donkey`) — so **both** examples take `-f Donkey`, while the written GIF uses the
display name (`output_Donkey Kong_<Subaction>.gif`). From the brawllib_rs clone:

```bash
. ~/.cargo/env                          # REQUIRED in non-interactive shells (err #149)
cargo run --release --example gif_generator -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \   # vanilla Brawl (DATA/files nesting)
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \                 # PM 3.6 overlay
  -f Donkey \                                                 # fighter (cased_name)
  -a <Subaction>                                              # e.g. Wait1
# writes output_Donkey Kong_<Subaction>.gif -> copy to repros/dk-gifs/dk_<Subaction>.gif
```

The full set was produced by looping that command over every enumerated subaction
(subaction list from `high_level_frame_data -f Donkey -l frame -i 0`; frame counts read
back from each rendered GIF with Pillow). At ~1.4s/render the whole set takes ~12 min.

## What's here

- **500** enumerated DK subactions (the `NONE*` action-table slots are excluded —
  they are unused engine IDs, not animations).
- **411** have real animation frames → one `dk_<subaction>.gif` each in
  `repros/dk-gifs/`.
- **89** are **empty** (0 frames — DK's data enumerates the slot but carries
  no animation for it: capture-victim variants for grab-characters, item throws DK
  can't perform, etc.). These have no motion to reference, so no GIF is saved; they are
  listed below marked **empty** for completeness.

Filename convention: `dk_<Subaction>.gif` (subaction name verbatim). Frame counts are
the rendered GIF's frame count (= the subaction's animation length).

## Index — by category

### Idle / wait  (3)

| Subaction | GIF | Frames |
|---|---|---|
| `Wait1` | `dk_Wait1.gif` | 141 |
| `Wait2` | `dk_Wait2.gif` | 140 |
| `Wait3` | `dk_Wait3.gif` | 100 |

### Item handling (engine-generic)  (138)

| Subaction | GIF | Frames |
|---|---|---|
| `WaitItem` | `dk_WaitItem.gif` | 141 |
| `ItemHandPickUp` | `dk_ItemHandPickUp.gif` | 2 |
| `ItemHandHave` | `dk_ItemHandHave.gif` | 2 |
| `ItemHandGrip` | `dk_ItemHandGrip.gif` | 2 |
| `ItemHandSmash` | `dk_ItemHandSmash.gif` | 2 |
| `LightGet` | `dk_LightGet.gif` | 8 |
| `LightWalkGet` | `dk_LightWalkGet.gif` | 20 |
| `LightEat` | `dk_LightEat.gif` | 20 |
| `LightWalkEat` | `dk_LightWalkEat.gif` | 20 |
| `HeavyGet` | `dk_HeavyGet.gif` | 20 |
| `HeavyWalk1` | — | *empty (0)* |
| `HeavyWalk2` | — | *empty (0)* |
| `LightThrowDrop` | `dk_LightThrowDrop.gif` | 28 |
| `LightThrowF` | `dk_LightThrowF.gif` | 39 |
| `LightThrowB` | `dk_LightThrowB.gif` | 30 |
| `LightThrowHi` | `dk_LightThrowHi.gif` | 32 |
| `LightThrowLw` | `dk_LightThrowLw.gif` | 29 |
| `LightThrowF_1` | `dk_LightThrowF_1.gif` | 39 |
| `LightThrowB_1` | `dk_LightThrowB_1.gif` | 30 |
| `LightThrowHi_1` | `dk_LightThrowHi_1.gif` | 32 |
| `LightThrowLw_1` | `dk_LightThrowLw_1.gif` | 29 |
| `LightThrowDash` | `dk_LightThrowDash.gif` | 40 |
| `LightThrowAirF` | `dk_LightThrowAirF.gif` | 32 |
| `LightThrowAirB` | `dk_LightThrowAirB.gif` | 27 |
| `LightThrowAirHi` | `dk_LightThrowAirHi.gif` | 29 |
| `LightThrowAirLw` | `dk_LightThrowAirLw.gif` | 28 |
| `LightThrowAirF_1` | `dk_LightThrowAirF_1.gif` | 32 |
| `LightThrowAirB_1` | `dk_LightThrowAirB_1.gif` | 27 |
| `LightThrowAirHi_1` | `dk_LightThrowAirHi_1.gif` | 29 |
| `LightThrowAirLw_1` | `dk_LightThrowAirLw_1.gif` | 28 |
| `HeavyThrowF` | `dk_HeavyThrowF.gif` | 40 |
| `HeavyThrowB` | `dk_HeavyThrowB.gif` | 40 |
| `HeavyThrowHi` | `dk_HeavyThrowHi.gif` | 30 |
| `HeavyThrowLw` | `dk_HeavyThrowLw.gif` | 35 |
| `HeavyThrowF_1` | `dk_HeavyThrowF_1.gif` | 40 |
| `HeavyThrowB_1` | `dk_HeavyThrowB_1.gif` | 40 |
| `HeavyThrowHi_1` | `dk_HeavyThrowHi_1.gif` | 30 |
| `HeavyThrowLw_1` | `dk_HeavyThrowLw_1.gif` | 35 |
| `SmashThrowF` | — | *empty (0)* |
| `SmashThrowB` | — | *empty (0)* |
| `SmashThrowHi` | — | *empty (0)* |
| `SmashThrowLw` | — | *empty (0)* |
| `SmashThrowDash` | — | *empty (0)* |
| `SmashThrowAirF` | — | *empty (0)* |
| `SmashThrowAirB` | — | *empty (0)* |
| `SmashThrowAirHi` | — | *empty (0)* |
| `SmashThrowAirLw` | — | *empty (0)* |
| `Swing1` | `dk_Swing1.gif` | 28 |
| `Swing3` | `dk_Swing3.gif` | 42 |
| `Swing4Start` | `dk_Swing4Start.gif` | 9 |
| `Swing4` | `dk_Swing4.gif` | 52 |
| `Swing42` | — | *empty (0)* |
| `Swing4Hold` | `dk_Swing4Hold.gif` | 61 |
| `SwingDash` | `dk_SwingDash.gif` | 46 |
| `Swing1_1` | `dk_Swing1_1.gif` | 28 |
| `Swing3_1` | `dk_Swing3_1.gif` | 42 |
| `Swing4Bat` | `dk_Swing4Bat.gif` | 90 |
| `SwingDash_1` | `dk_SwingDash_1.gif` | 46 |
| `Swing1_2` | `dk_Swing1_2.gif` | 28 |
| `Swing3_2` | `dk_Swing3_2.gif` | 42 |
| `Swing4Start_1` | `dk_Swing4Start_1.gif` | 9 |
| `Swing4_1` | `dk_Swing4_1.gif` | 52 |
| `Swing42_1` | — | *empty (0)* |
| `Swing4Hold_1` | `dk_Swing4Hold_1.gif` | 61 |
| `SwingDash_2` | `dk_SwingDash_2.gif` | 46 |
| `Swing1_3` | `dk_Swing1_3.gif` | 28 |
| `Swing3_3` | `dk_Swing3_3.gif` | 42 |
| `Swing4Start_2` | `dk_Swing4Start_2.gif` | 9 |
| `Swing4_2` | `dk_Swing4_2.gif` | 52 |
| `Swing42_2` | — | *empty (0)* |
| `Swing4Hold_2` | `dk_Swing4Hold_2.gif` | 61 |
| `SwingDash_3` | `dk_SwingDash_3.gif` | 46 |
| `Swing1_4` | `dk_Swing1_4.gif` | 28 |
| `Swing3_4` | `dk_Swing3_4.gif` | 42 |
| `Swing4Start_3` | `dk_Swing4Start_3.gif` | 9 |
| `Swing4_3` | `dk_Swing4_3.gif` | 52 |
| `Swing42_3` | — | *empty (0)* |
| `Swing4Hold_3` | `dk_Swing4Hold_3.gif` | 61 |
| `SwingDash_4` | `dk_SwingDash_4.gif` | 46 |
| `ItemHammerWait` | `dk_ItemHammerWait.gif` | 17 |
| `ItemHammerMove` | `dk_ItemHammerMove.gif` | 17 |
| `ItemHammerAir` | `dk_ItemHammerAir.gif` | 17 |
| `ItemHammerWait_1` | `dk_ItemHammerWait_1.gif` | 17 |
| `ItemHammerMove_1` | `dk_ItemHammerMove_1.gif` | 17 |
| `ItemHammerAir_1` | `dk_ItemHammerAir_1.gif` | 17 |
| `ItemDragoonRide` | `dk_ItemDragoonRide.gif` | 41 |
| `ItemScrew` | `dk_ItemScrew.gif` | 41 |
| `ItemScrew_1` | `dk_ItemScrew_1.gif` | 41 |
| `ItemScrewFall` | `dk_ItemScrewFall.gif` | 81 |
| `ItemDragoonGet` | `dk_ItemDragoonGet.gif` | 60 |
| `ItemDragoonRide_1` | `dk_ItemDragoonRide_1.gif` | 41 |
| `ItemBig` | `dk_ItemBig.gif` | 60 |
| `ItemSmall` | `dk_ItemSmall.gif` | 60 |
| `ItemLegsWait` | `dk_ItemLegsWait.gif` | 101 |
| `ItemLegsSlowF` | `dk_ItemLegsSlowF.gif` | 51 |
| `ItemLegsMiddleF` | `dk_ItemLegsMiddleF.gif` | 41 |
| `ItemLegsFastF` | `dk_ItemLegsFastF.gif` | 35 |
| `ItemLegsBrakeF` | `dk_ItemLegsBrakeF.gif` | 2 |
| `ItemLegsDashF` | `dk_ItemLegsDashF.gif` | 26 |
| `ItemLegsSlowB` | `dk_ItemLegsSlowB.gif` | 66 |
| `ItemLegsMiddleB` | `dk_ItemLegsMiddleB.gif` | 55 |
| `ItemLegsFastB` | `dk_ItemLegsFastB.gif` | 44 |
| `ItemLegsBrakeB` | `dk_ItemLegsBrakeB.gif` | 2 |
| `ItemLegsDashB` | `dk_ItemLegsDashB.gif` | 26 |
| `ItemLegsJumpSquat` | `dk_ItemLegsJumpSquat.gif` | 7 |
| `ItemLegsLanding` | `dk_ItemLegsLanding.gif` | 16 |
| `ItemShoot` | `dk_ItemShoot.gif` | 25 |
| `ItemShootAir` | `dk_ItemShootAir.gif` | 25 |
| `ItemShoot_1` | `dk_ItemShoot_1.gif` | 25 |
| `ItemShootAir_1` | `dk_ItemShootAir_1.gif` | 25 |
| `ItemShoot_2` | `dk_ItemShoot_2.gif` | 25 |
| `ItemShootAir_2` | `dk_ItemShootAir_2.gif` | 25 |
| `ItemScopeStart` | `dk_ItemScopeStart.gif` | 16 |
| `ItemScopeRapid` | `dk_ItemScopeRapid.gif` | 9 |
| `ItemScopeFire` | `dk_ItemScopeFire.gif` | 31 |
| `ItemScopeEnd` | `dk_ItemScopeEnd.gif` | 21 |
| `ItemScopeAirStart` | `dk_ItemScopeAirStart.gif` | 16 |
| `ItemScopeAirRapid` | `dk_ItemScopeAirRapid.gif` | 9 |
| `ItemScopeAirFire` | `dk_ItemScopeAirFire.gif` | 31 |
| `ItemScopeAirEnd` | `dk_ItemScopeAirEnd.gif` | 21 |
| `ItemScopeStart_1` | `dk_ItemScopeStart_1.gif` | 16 |
| `ItemScopeRapid_1` | `dk_ItemScopeRapid_1.gif` | 9 |
| `ItemScopeFire_1` | `dk_ItemScopeFire_1.gif` | 31 |
| `ItemScopeEnd_1` | `dk_ItemScopeEnd_1.gif` | 21 |
| `ItemScopeAirStart_1` | `dk_ItemScopeAirStart_1.gif` | 16 |
| `ItemScopeAirRapid_1` | `dk_ItemScopeAirRapid_1.gif` | 9 |
| `ItemScopeAirFire_1` | `dk_ItemScopeAirFire_1.gif` | 31 |
| `ItemScopeAirEnd_1` | `dk_ItemScopeAirEnd_1.gif` | 21 |
| `ItemLauncher` | `dk_ItemLauncher.gif` | 151 |
| `ItemLauncherFire` | `dk_ItemLauncherFire.gif` | 12 |
| `ItemLauncherAirFire` | `dk_ItemLauncherAirFire.gif` | 12 |
| `ItemLauncher_1` | `dk_ItemLauncher_1.gif` | 151 |
| `ItemLauncherFire_1` | `dk_ItemLauncherFire_1.gif` | 12 |
| `ItemLauncherAirFire_1` | `dk_ItemLauncherAirFire_1.gif` | 12 |
| `ItemLauncherFall` | `dk_ItemLauncherFall.gif` | 17 |
| `ItemLauncherAir` | — | *empty (0)* |
| `ItemAssist` | `dk_ItemAssist.gif` | 60 |
| `ItemScrew_2` | `dk_ItemScrew_2.gif` | 41 |

### Ground movement  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `WalkSlow` | `dk_WalkSlow.gif` | 46 |
| `WalkMiddle` | `dk_WalkMiddle.gif` | 31 |
| `WalkFast` | `dk_WalkFast.gif` | 23 |
| `WalkBrake` | `dk_WalkBrake.gif` | 2 |
| `Dash` | `dk_Dash.gif` | 31 |
| `Run` | `dk_Run.gif` | 36 |
| `RunBrake` | `dk_RunBrake.gif` | 30 |
| `Turn` | `dk_Turn.gif` | 12 |
| `TurnRun` | `dk_TurnRun.gif` | 34 |
| `TurnRunBrake` | `dk_TurnRunBrake.gif` | 21 |

### Jump  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `JumpSquat` | `dk_JumpSquat.gif` | 5 |
| `JumpF` | `dk_JumpF.gif` | 36 |
| `JumpF_1` | `dk_JumpF_1.gif` | 36 |
| `JumpB` | `dk_JumpB.gif` | 46 |
| `JumpB_1` | `dk_JumpB_1.gif` | 46 |
| `JumpAerialF` | `dk_JumpAerialF.gif` | 35 |
| `JumpAerialB` | `dk_JumpAerialB.gif` | 60 |
| `StepJump` | `dk_StepJump.gif` | 9 |

### Fall  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `Fall` | `dk_Fall.gif` | 17 |
| `FallF` | `dk_FallF.gif` | 17 |
| `FallB` | `dk_FallB.gif` | 17 |
| `FallAerial` | `dk_FallAerial.gif` | 17 |
| `FallAerialF` | `dk_FallAerialF.gif` | 17 |
| `FallAerialB` | `dk_FallAerialB.gif` | 17 |
| `FallSpecial` | `dk_FallSpecial.gif` | 39 |
| `FallSpecialF` | `dk_FallSpecialF.gif` | 39 |
| `FallSpecialB` | `dk_FallSpecialB.gif` | 39 |
| `DamageFall` | `dk_DamageFall.gif` | 61 |

### Crouch  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `Squat` | `dk_Squat.gif` | 8 |
| `SquatWait` | `dk_SquatWait.gif` | 161 |
| `SquatWait_1` | `dk_SquatWait_1.gif` | 161 |
| `SquatWaitItem` | `dk_SquatWaitItem.gif` | 161 |
| `SquatRv` | `dk_SquatRv.gif` | 8 |

### Landing  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `LandingLight` | `dk_LandingLight.gif` | 4 |
| `LandingHeavy` | `dk_LandingHeavy.gif` | 4 |
| `LandingFallSpecial` | `dk_LandingFallSpecial.gif` | 31 |
| `LandingAirN` | `dk_LandingAirN.gif` | 17 |
| `LandingAirF` | `dk_LandingAirF.gif` | 27 |
| `LandingAirB` | `dk_LandingAirB.gif` | 15 |
| `LandingAirHi` | `dk_LandingAirHi.gif` | 25 |
| `LandingAirLw` | `dk_LandingAirLw.gif` | 29 |

### Ledge-step (walk-off)  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `StepPose` | `dk_StepPose.gif` | 9 |
| `StepBack` | `dk_StepBack.gif` | 21 |
| `StepAirPose` | `dk_StepAirPose.gif` | 9 |
| `StepFall` | `dk_StepFall.gif` | 41 |
| `Ottotto` | `dk_Ottotto.gif` | 10 |
| `OttottoWait` | `dk_OttottoWait.gif` | 91 |

### Shield  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `GuardOn` | `dk_GuardOn.gif` | 8 |
| `Guard` | `dk_Guard.gif` | 361 |
| `GuardOff` | `dk_GuardOff.gif` | 23 |
| `GuardDamage` | `dk_GuardDamage.gif` | 21 |
| `GuardOn_1` | `dk_GuardOn_1.gif` | 8 |
| `Guard_1` | `dk_Guard_1.gif` | 361 |

### Dodge / roll  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `EscapeN` | `dk_EscapeN.gif` | 31 |
| `EscapeF` | `dk_EscapeF.gif` | 32 |
| `EscapeB` | `dk_EscapeB.gif` | 32 |
| `EscapeAir` | `dk_EscapeAir.gif` | 50 |

### Ground attack — jab / dash  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `Attack11` | `dk_Attack11.gif` | 29 |
| `Attack12` | `dk_Attack12.gif` | 45 |
| `AttackDash` | `dk_AttackDash.gif` | 43 |
| `AttackDashAir` | `dk_AttackDashAir.gif` | 30 |

### Ground attack — tilt  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS3Hi` | `dk_AttackS3Hi.gif` | 38 |
| `AttackS3S` | `dk_AttackS3S.gif` | 38 |
| `AttackS3Lw` | `dk_AttackS3Lw.gif` | 38 |
| `AttackHi3` | `dk_AttackHi3.gif` | 40 |
| `AttackLw3` | `dk_AttackLw3.gif` | 28 |

### Ground attack — smash  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS4Start` | `dk_AttackS4Start.gif` | 15 |
| `AttackS4S` | `dk_AttackS4S.gif` | 41 |
| `AttackS4S_1` | `dk_AttackS4S_1.gif` | 41 |
| `AttackS4S_2` | `dk_AttackS4S_2.gif` | 41 |
| `AttackS4Hold` | `dk_AttackS4Hold.gif` | 61 |
| `AttackHi4Start` | `dk_AttackHi4Start.gif` | 7 |
| `AttackHi4` | `dk_AttackHi4.gif` | 54 |
| `AttackHi4Hold` | `dk_AttackHi4Hold.gif` | 61 |
| `AttackLw4Start` | `dk_AttackLw4Start.gif` | 3 |
| `AttackLw4` | `dk_AttackLw4.gif` | 54 |
| `AttackLw4Hold` | `dk_AttackLw4Hold.gif` | 61 |

### Aerial attack  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackAirN` | `dk_AttackAirN.gif` | 42 |
| `AttackAirF` | `dk_AttackAirF.gif` | 51 |
| `AttackAirB` | `dk_AttackAirB.gif` | 39 |
| `AttackAirHi` | `dk_AttackAirHi.gif` | 45 |
| `AttackAirLw` | `dk_AttackAirLw.gif` | 51 |

### Air-catch grab (Melee-style)  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `AirCatch` | — | *empty (0)* |
| `AirCatchPose` | — | *empty (0)* |
| `AirCatchHit` | — | *empty (0)* |
| `AirCatch_1` | — | *empty (0)* |

### Grab  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `Catch` | `dk_Catch.gif` | 31 |
| `CatchDash` | `dk_CatchDash.gif` | 50 |
| `CatchTurn` | `dk_CatchTurn.gif` | 36 |
| `CatchWait` | `dk_CatchWait.gif` | 31 |
| `CatchAttack` | `dk_CatchAttack.gif` | 24 |
| `CatchCut` | `dk_CatchCut.gif` | 30 |

### Throw  (45)

| Subaction | GIF | Frames |
|---|---|---|
| `ThrowB` | `dk_ThrowB.gif` | 40 |
| `ThrowF` | `dk_ThrowF.gif` | 20 |
| `ThrowHi` | `dk_ThrowHi.gif` | 44 |
| `ThrowLw` | `dk_ThrowLw.gif` | 60 |
| `ThrownB` | `dk_ThrownB.gif` | 40 |
| `ThrownF` | `dk_ThrownF.gif` | 20 |
| `ThrownHi` | `dk_ThrownHi.gif` | 44 |
| `ThrownLw` | `dk_ThrownLw.gif` | 60 |
| `ThrownDxB` | `dk_ThrownDxB.gif` | 48 |
| `ThrownDxF` | `dk_ThrownDxF.gif` | 20 |
| `ThrownDxHi` | `dk_ThrownDxHi.gif` | 54 |
| `ThrownDxLw` | `dk_ThrownDxLw.gif` | 68 |
| `ThrownZitabata` | `dk_ThrownZitabata.gif` | 51 |
| `ThrownDxZitabata` | `dk_ThrownDxZitabata.gif` | 51 |
| `ThrownGirlZitabata` | `dk_ThrownGirlZitabata.gif` | 51 |
| `ThrownFF` | `dk_ThrownFF.gif` | 40 |
| `ThrownFB` | `dk_ThrownFB.gif` | 40 |
| `ThrownFHi` | `dk_ThrownFHi.gif` | 30 |
| `ThrownFLw` | `dk_ThrownFLw.gif` | 40 |
| `ThrownDxFF` | `dk_ThrownDxFF.gif` | 40 |
| `ThrownDxFB` | `dk_ThrownDxFB.gif` | 40 |
| `ThrownDxFHi` | `dk_ThrownDxFHi.gif` | 35 |
| `ThrownDxFLw` | `dk_ThrownDxFLw.gif` | 40 |
| `ThrowFWait` | `dk_ThrowFWait.gif` | 51 |
| `ThrowFWalkSlow` | `dk_ThrowFWalkSlow.gif` | 71 |
| `ThrowFWalkMiddle` | `dk_ThrowFWalkMiddle.gif` | 36 |
| `ThrowFWalkFast` | `dk_ThrowFWalkFast.gif` | 36 |
| `ThrowFTurn` | `dk_ThrowFTurn.gif` | 12 |
| `ThrowFJumpSquat` | `dk_ThrowFJumpSquat.gif` | 6 |
| `ThrowFJump` | `dk_ThrowFJump.gif` | 26 |
| `ThrowFFall` | `dk_ThrowFFall.gif` | 15 |
| `ThrowFLanding` | `dk_ThrowFLanding.gif` | 18 |
| `ThrowFWait_1` | `dk_ThrowFWait_1.gif` | 51 |
| `ThrowFWalkSlow_1` | `dk_ThrowFWalkSlow_1.gif` | 71 |
| `ThrowFWalkMiddle_1` | `dk_ThrowFWalkMiddle_1.gif` | 36 |
| `ThrowFWalkFast_1` | `dk_ThrowFWalkFast_1.gif` | 36 |
| `ThrowFTurn_1` | `dk_ThrowFTurn_1.gif` | 12 |
| `ThrowFJumpSquat_1` | `dk_ThrowFJumpSquat_1.gif` | 6 |
| `ThrowFJump_1` | `dk_ThrowFJump_1.gif` | 26 |
| `ThrowFFall_1` | `dk_ThrowFFall_1.gif` | 15 |
| `ThrowFLanding_1` | `dk_ThrowFLanding_1.gif` | 18 |
| `ThrowFF` | `dk_ThrowFF.gif` | 30 |
| `ThrowFB` | `dk_ThrowFB.gif` | 30 |
| `ThrowFHi` | `dk_ThrowFHi.gif` | 32 |
| `ThrowFLw` | `dk_ThrowFLw.gif` | 40 |

### Grabbed / carried (victim)  (27)

| Subaction | GIF | Frames |
|---|---|---|
| `CapturePulledHi` | `dk_CapturePulledHi.gif` | 20 |
| `CaptureWaitHi` | `dk_CaptureWaitHi.gif` | 41 |
| `CaptureDamageHi` | `dk_CaptureDamageHi.gif` | 20 |
| `CapturePulledLw` | `dk_CapturePulledLw.gif` | 20 |
| `CaptureWaitLw` | `dk_CaptureWaitLw.gif` | 41 |
| `CaptureDamageLw` | `dk_CaptureDamageLw.gif` | 20 |
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
| `CaptureCut` | `dk_CaptureCut.gif` | 21 |
| `CaptureJump` | `dk_CaptureJump.gif` | 51 |
| `Swallowed` | `dk_Swallowed.gif` | 11 |

### Damage / hitstun  (19)

| Subaction | GIF | Frames |
|---|---|---|
| `DamageHi1` | `dk_DamageHi1.gif` | 12 |
| `DamageHi2` | `dk_DamageHi2.gif` | 24 |
| `DamageHi3` | `dk_DamageHi3.gif` | 30 |
| `DamageN1` | `dk_DamageN1.gif` | 12 |
| `DamageN2` | `dk_DamageN2.gif` | 24 |
| `DamageN3` | `dk_DamageN3.gif` | 30 |
| `DamageLw1` | `dk_DamageLw1.gif` | 12 |
| `DamageLw2` | `dk_DamageLw2.gif` | 24 |
| `DamageLw3` | `dk_DamageLw3.gif` | 42 |
| `DamageAir1` | `dk_DamageAir1.gif` | 12 |
| `DamageAir2` | `dk_DamageAir2.gif` | 24 |
| `DamageAir3` | `dk_DamageAir3.gif` | 30 |
| `DamageFlyHi` | `dk_DamageFlyHi.gif` | 37 |
| `DamageFlyN` | `dk_DamageFlyN.gif` | 37 |
| `DamageFlyLw` | `dk_DamageFlyLw.gif` | 37 |
| `DamageFlyTop` | `dk_DamageFlyTop.gif` | 81 |
| `DamageFlyRoll` | `dk_DamageFlyRoll.gif` | 17 |
| `DamageElec` | `dk_DamageElec.gif` | 71 |
| `DamageFace` | — | *empty (0)* |

### Downed / getup  (20)

| Subaction | GIF | Frames |
|---|---|---|
| `DownBoundU` | `dk_DownBoundU.gif` | 27 |
| `DownWaitU` | `dk_DownWaitU.gif` | 61 |
| `DownDamageU` | `dk_DownDamageU.gif` | 14 |
| `DownDamageU3` | — | *empty (0)* |
| `DownEatU` | `dk_DownEatU.gif` | 30 |
| `DownStandU` | `dk_DownStandU.gif` | 30 |
| `DownAttackU` | `dk_DownAttackU.gif` | 52 |
| `DownForwardU` | `dk_DownForwardU.gif` | 36 |
| `DownBackU` | `dk_DownBackU.gif` | 36 |
| `DownBoundD` | `dk_DownBoundD.gif` | 27 |
| `DownWaitD` | `dk_DownWaitD.gif` | 81 |
| `DownDamageD` | `dk_DownDamageD.gif` | 14 |
| `DownDamageD3` | — | *empty (0)* |
| `DownEatD` | `dk_DownEatD.gif` | 30 |
| `DownStandD` | `dk_DownStandD.gif` | 30 |
| `DownAttackD` | `dk_DownAttackD.gif` | 50 |
| `DownForwardD` | `dk_DownForwardD.gif` | 36 |
| `DownBackD` | `dk_DownBackD.gif` | 36 |
| `DownSpotU` | `dk_DownSpotU.gif` | 30 |
| `DownSpotD` | — | *empty (0)* |

### Tech / passive  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `Passive` | `dk_Passive.gif` | 27 |
| `PassiveStandF` | `dk_PassiveStandF.gif` | 41 |
| `PassiveStandB` | `dk_PassiveStandB.gif` | 41 |
| `PassiveWall` | `dk_PassiveWall.gif` | 26 |
| `PassiveWallJump` | `dk_PassiveWallJump.gif` | 41 |
| `PassiveCeil` | `dk_PassiveCeil.gif` | 26 |
| `Pass` | `dk_Pass.gif` | 26 |

### Dizzy / sleep  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `FuraFura` | `dk_FuraFura.gif` | 161 |
| `FuraFuraStartU` | `dk_FuraFuraStartU.gif` | 50 |
| `FuraFuraStartD` | `dk_FuraFuraStartD.gif` | 50 |
| `FuraFuraEnd` | `dk_FuraFuraEnd.gif` | 50 |
| `FuraSleepStart` | `dk_FuraSleepStart.gif` | 30 |
| `FuraSleepLoop` | `dk_FuraSleepLoop.gif` | 81 |
| `FuraSleepEnd` | `dk_FuraSleepEnd.gif` | 60 |

### Ledge (cliff hang / getup)  (12)

| Subaction | GIF | Frames |
|---|---|---|
| `CliffCatch` | `dk_CliffCatch.gif` | 21 |
| `CliffWait` | `dk_CliffWait.gif` | 81 |
| `CliffAttackQuick` | `dk_CliffAttackQuick.gif` | 55 |
| `CliffClimbQuick` | `dk_CliffClimbQuick.gif` | 35 |
| `CliffEscapeQuick` | `dk_CliffEscapeQuick.gif` | 50 |
| `CliffJumpQuick1` | `dk_CliffJumpQuick1.gif` | 12 |
| `CliffJumpQuick2` | `dk_CliffJumpQuick2.gif` | 18 |
| `CliffAttackSlow` | `dk_CliffAttackSlow.gif` | 70 |
| `CliffClimbSlow` | `dk_CliffClimbSlow.gif` | 60 |
| `CliffEscapeSlow` | `dk_CliffEscapeSlow.gif` | 80 |
| `CliffJumpSlow1` | `dk_CliffJumpSlow1.gif` | 23 |
| `CliffJumpSlow2` | `dk_CliffJumpSlow2.gif` | 17 |

### Trip / slip  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SlipDown` | `dk_SlipDown.gif` | 40 |
| `Slip` | `dk_Slip.gif` | 30 |
| `SlipTurn` | `dk_SlipTurn.gif` | 36 |
| `SlipDash` | `dk_SlipDash.gif` | 46 |
| `SlipWait` | `dk_SlipWait.gif` | 61 |
| `SlipStand` | `dk_SlipStand.gif` | 22 |
| `SlipAttack` | `dk_SlipAttack.gif` | 50 |
| `SlipEscapeF` | `dk_SlipEscapeF.gif` | 29 |
| `SlipEscapeB` | `dk_SlipEscapeB.gif` | 29 |

### Swim  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SwimRise` | `dk_SwimRise.gif` | 46 |
| `SwimUp` | `dk_SwimUp.gif` | 17 |
| `SwimUpDamage` | `dk_SwimUpDamage.gif` | 25 |
| `Swim` | `dk_Swim.gif` | 101 |
| `SwimF` | `dk_SwimF.gif` | 66 |
| `SwimEnd` | `dk_SwimEnd.gif` | 30 |
| `SwimTurn` | `dk_SwimTurn.gif` | 20 |
| `SwimDrown` | `dk_SwimDrown.gif` | 71 |
| `SwimDrownOut` | `dk_SwimDrownOut.gif` | 41 |

### Ladder / rope  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `LadderWait` | `dk_LadderWait.gif` | 81 |
| `LadderUp` | `dk_LadderUp.gif` | 19 |
| `LadderDown` | `dk_LadderDown.gif` | 26 |
| `LadderCatchR` | `dk_LadderCatchR.gif` | 15 |
| `LadderCatchL` | `dk_LadderCatchL.gif` | 15 |
| `LadderCatchAirR` | `dk_LadderCatchAirR.gif` | 15 |
| `LadderCatchAirL` | `dk_LadderCatchAirL.gif` | 15 |
| `LadderCatchEndR` | `dk_LadderCatchEndR.gif` | 25 |
| `LadderCatchEndL` | `dk_LadderCatchEndL.gif` | 25 |
| `RopeCatch` | — | *empty (0)* |
| `RopeFishing` | — | *empty (0)* |

### Special move  (54)

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
| `SpecialNStart` | `dk_SpecialNStart.gif` | 8 |
| `SpecialNLoop` | `dk_SpecialNLoop.gif` | 13 |
| `SpecialNCancel` | `dk_SpecialNCancel.gif` | 9 |
| `SpecialN` | `dk_SpecialN.gif` | 52 |
| `SpecialN_1` | `dk_SpecialN_1.gif` | 52 |
| `SpecialAirNStart` | `dk_SpecialAirNStart.gif` | 8 |
| `SpecialAirNLoop` | `dk_SpecialAirNLoop.gif` | 13 |
| `SpecialAirNCancel` | `dk_SpecialAirNCancel.gif` | 9 |
| `SpecialAirN` | `dk_SpecialAirN.gif` | 45 |
| `SpecialAirN_1` | `dk_SpecialAirN_1.gif` | 45 |
| `SpecialS` | `dk_SpecialS.gif` | 60 |
| `SpecialAirS` | `dk_SpecialAirS.gif` | 60 |
| `SpecialHi` | `dk_SpecialHi.gif` | 85 |
| `SpecialAirHi` | `dk_SpecialAirHi.gif` | 85 |
| `SpecialLwStart` | `dk_SpecialLwStart.gif` | 14 |
| `SpecialLwLoop` | `dk_SpecialLwLoop.gif` | 28 |
| `SpecialLwEnd` | `dk_SpecialLwEnd.gif` | 18 |

### Taunt / appeal  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `DKTauntR` | `dk_DKTauntR.gif` | 256 |
| `DKTauntL` | `dk_DKTauntL.gif` | 256 |
| `AppealHiR` | `dk_AppealHiR.gif` | 100 |
| `AppealHiL` | `dk_AppealHiL.gif` | 100 |
| `AppealS` | `dk_AppealS.gif` | 90 |
| `AppealS_1` | `dk_AppealS_1.gif` | 90 |
| `AppealLwR` | `dk_AppealLwR.gif` | 60 |
| `AppealLwL` | `dk_AppealLwL.gif` | 60 |

### Entry / win / lose  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `EntryR` | `dk_EntryR.gif` | 121 |
| `EntryL` | `dk_EntryL.gif` | 121 |
| `Win1` | `dk_Win1.gif` | 121 |
| `Win1Wait` | `dk_Win1Wait.gif` | 101 |
| `Win2` | `dk_Win2.gif` | 121 |
| `Win2Wait` | `dk_Win2Wait.gif` | 101 |
| `Win3` | `dk_Win3.gif` | 121 |
| `Win3Wait` | `dk_Win3Wait.gif` | 101 |
| `Lose` | `dk_Lose.gif` | 31 |

### Final Smash  (15)

| Subaction | GIF | Frames |
|---|---|---|
| `FinalStartL` | `dk_FinalStartL.gif` | 46 |
| `FinalStartR` | `dk_FinalStartR.gif` | 46 |
| `FinalStartAirL` | `dk_FinalStartAirL.gif` | 46 |
| `FinalStartAirR` | `dk_FinalStartAirR.gif` | 46 |
| `FinalBody` | `dk_FinalBody.gif` | 111 |
| `FinalArm` | `dk_FinalArm.gif` | 61 |
| `FinalHandCrap` | `dk_FinalHandCrap.gif` | 30 |
| `FinalEndL` | `dk_FinalEndL.gif` | 80 |
| `FinalEndR` | `dk_FinalEndR.gif` | 80 |
| `FinalEndAirL` | `dk_FinalEndAirL.gif` | 80 |
| `FinalEndAirR` | `dk_FinalEndAirR.gif` | 80 |
| `FinalEndL_1` | `dk_FinalEndL_1.gif` | 80 |
| `FinalEndR_1` | `dk_FinalEndR_1.gif` | 80 |
| `FinalEndAirL_1` | `dk_FinalEndAirL_1.gif` | 80 |
| `FinalEndAirR_1` | `dk_FinalEndAirR_1.gif` | 80 |

### Misc / situational  (15)

| Subaction | GIF | Frames |
|---|---|---|
| `_1` | — | *empty (0)* |
| `_2` | — | *empty (0)* |
| `Rebound` | `dk_Rebound.gif` | 31 |
| `_3` | — | *empty (0)* |
| `_4` | — | *empty (0)* |
| `WallDamage` | `dk_WallDamage.gif` | 51 |
| `StopCeil` | `dk_StopCeil.gif` | 9 |
| `StopWall` | `dk_StopWall.gif` | 18 |
| `StopCeil_1` | `dk_StopCeil_1.gif` | 9 |
| `MissFoot` | `dk_MissFoot.gif` | 26 |
| `GekikaraWait` | `dk_GekikaraWait.gif` | 31 |
| `GanonSpecialHiCapture` | — | *empty (0)* |
| `GanonSpecialHiDxCapture` | — | *empty (0)* |
| `Dark` | — | *empty (0)* |
| `Spycloak` | — | *empty (0)* |

## Refs

- #777 (the Mario precedent this mirrors) · #758 (the GIF recipe) · #779 / #794 (Gnok
  epic + spec — the consumer) · #824 (Gnok jab — first per-move DK datamine) · #614 /
  #753 (brawllib datamine env) · #778 (the Nalio-vs-Mario sandbox — the Gnok-vs-DK
  equivalent this feeds).

<!-- rendered=411 empty=89 total=500 -->
