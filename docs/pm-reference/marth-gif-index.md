# Marth animation-GIF reference set — manifest (#832)

The **complete** browsable library of Project M 3.6 **Marth** subaction
animations, rendered via the [`tooling-brawllib-rs-gif-recipe.md`](../tooling-brawllib-rs-gif-recipe.md)
(#758) `gif_generator` recipe. It is the visual substrate for comparing pycats'
**Narz** (the Marth archetype — the disjointed spacer, epic #294 / spec #290
[`research-spec-290-narz-marth-pm.md`](../research-spec-290-narz-marth-pm.md)) move-for-move
against the PM source. Mirrors the Mario set ([`mario-gif-index.md`](./mario-gif-index.md),
#777) and the DK set ([`dk-gif-index.md`](./dk-gif-index.md), #827).

Each GIF is brawllib_rs's **hurtbox-capsule / skeleton** render (the rukaidata.com
renderer) — it shows *motion*, not the character skin. That is the right thing for
measuring and comparing movement; the capsules track the bones. For Marth the sword is a
**disjoint** — a hurtbox on the weapon bone reaching past the body — so the tipper/spacing
that defines the archetype is visible in the capsule set.

## ⚠ Copyright — GIFs are not committed

The `.pac` source **and** every derived GIF are copyrighted. The GIFs live **only**
in gitignored `repros/marth-gifs/` (per the repros-dir media policy) and are **never**
committed. This manifest is the only committed artifact — it makes the set
discoverable and reproducible **without** shipping a single frame.

## Reproduce the set

Prerequisites (datamine env, PM 3.6 `.pac` data) are in the recipe doc. Marth's filter is
plain **`-f Marth`**: its `cased_name` and `internal_name` are both `Marth`, and the written
GIF uses the same display name (`output_Marth_<Subaction>.gif`) — no display-vs-internal
split like DK's `Donkey` / `Donkey Kong`.

**1. Enumerate** every subaction name + frame length (the authoritative list, including the
0-frame empties) with the throwaway `subaction_lengths` helper added to the brawllib_rs clone
(a de-filtered sibling of `wait_lengths`, #753 — no new deps):

```bash
. ~/.cargo/env                          # REQUIRED in non-interactive shells (err #149)
cargo run --release --example subaction_lengths -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \   # vanilla Brawl (DATA/files nesting)
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \                 # PM 3.6 overlay
  -f Marth                                                    # prints "<Subaction>\t<frames.len()>"
```

**2. Render** each subaction with `frames.len() > 0` to a GIF, then move it into the
gitignored library as `marth_<Subaction>.gif`:

```bash
cargo run --release --example gif_generator -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \
  -f Marth -a <Subaction>
# writes output_Marth_<Subaction>.gif -> mv to repros/marth-gifs/marth_<Subaction>.gif
```

The frame counts below are `subaction.frames.len()` from step 1 — verified equal to the
rendered GIF's `n_frames` (Pillow) on a sample. At ~1.4 s/render the 383-GIF set takes
~10–15 min.

## What's here

- **486** enumerated Marth subactions (the `NONE*` action-table slots are excluded —
  they are unused engine IDs, not animations).
- **383** have real animation frames → one `marth_<Subaction>.gif` each in
  `repros/marth-gifs/`.
- **103** are **empty** (0 frames — Marth's data enumerates the slot but carries no
  animation for it: grab-victim `Capture*Snake`/`*BigSnake` variants for other characters'
  throws, `SmashThrow*` item tosses, the `Special*Bitten`/`*Capture` command-grab-victim
  poses, and unused engine slots like `Dark` / `Spycloak` / the numbered `_N`). These have
  no motion to reference, so no GIF is saved; they are listed below marked **empty** for
  completeness.

Filename convention: `marth_<Subaction>.gif` (subaction name verbatim). Frame counts are
the subaction's animation length (`frames.len()` = the rendered GIF's frame count).

## Marth special-move key

For the Narz comparison, the named specials map to these subaction prefixes:

| PM Marth special | Subactions |
|---|---|
| Neutral-B — **Shield Breaker** | `SpecialNStart` / `SpecialNLoop` (charge) / `SpecialNEnd` (release); `SpecialAirN*` airborne |
| Side-B — **Dancing Blade** (4-hit, per-hit up/side/down branches) | `SpecialS1`, then `SpecialS2{Hi,Lw}`, `SpecialS3{Hi,S,Lw}`, `SpecialS4{Hi,S,Lw}`; `SpecialAirS*` airborne |
| Up-B — **Dolphin Slash** | `SpecialHi` / `SpecialAirHi` |
| Down-B — **Counter** | `SpecialLw` (stance) / `SpecialLwHit` (riposte); `SpecialAirLw` / `SpecialAirLwHit` airborne |
| Final Smash — **Critical Hit** | `FinalStart` / `FinalDash` / `FinalDashEnd` / `FinalEnd` (+ `FinalAir*`) — see Final Smash section |

## Index — by category

### Idle / wait  (3)

| Subaction | GIF | Frames |
|---|---|---|
| `Wait1` | `marth_Wait1.gif` | 71 |
| `Wait2` | `marth_Wait2.gif` | 95 |
| `Wait3` | `marth_Wait3.gif` | 120 |

### Item handling (engine-generic)  (138)

| Subaction | GIF | Frames |
|---|---|---|
| `WaitItem` | `marth_WaitItem.gif` | 71 |
| `ItemHandPickUp` | `marth_ItemHandPickUp.gif` | 2 |
| `ItemHandHave` | `marth_ItemHandHave.gif` | 2 |
| `ItemHandGrip` | `marth_ItemHandGrip.gif` | 2 |
| `ItemHandSmash` | `marth_ItemHandSmash.gif` | 2 |
| `LightGet` | `marth_LightGet.gif` | 8 |
| `LightWalkGet` | `marth_LightWalkGet.gif` | 20 |
| `LightEat` | `marth_LightEat.gif` | 20 |
| `LightWalkEat` | `marth_LightWalkEat.gif` | 20 |
| `HeavyGet` | `marth_HeavyGet.gif` | 44 |
| `HeavyWalk1` | `marth_HeavyWalk1.gif` | 45 |
| `HeavyWalk2` | `marth_HeavyWalk2.gif` | 45 |
| `LightThrowDrop` | `marth_LightThrowDrop.gif` | 24 |
| `LightThrowF` | `marth_LightThrowF.gif` | 33 |
| `LightThrowB` | `marth_LightThrowB.gif` | 30 |
| `LightThrowHi` | `marth_LightThrowHi.gif` | 34 |
| `LightThrowLw` | `marth_LightThrowLw.gif` | 27 |
| `LightThrowF_1` | `marth_LightThrowF_1.gif` | 33 |
| `LightThrowB_1` | `marth_LightThrowB_1.gif` | 30 |
| `LightThrowHi_1` | `marth_LightThrowHi_1.gif` | 34 |
| `LightThrowLw_1` | `marth_LightThrowLw_1.gif` | 27 |
| `LightThrowDash` | `marth_LightThrowDash.gif` | 40 |
| `LightThrowAirF` | `marth_LightThrowAirF.gif` | 33 |
| `LightThrowAirB` | `marth_LightThrowAirB.gif` | 30 |
| `LightThrowAirHi` | `marth_LightThrowAirHi.gif` | 30 |
| `LightThrowAirLw` | `marth_LightThrowAirLw.gif` | 27 |
| `LightThrowAirF_1` | `marth_LightThrowAirF_1.gif` | 33 |
| `LightThrowAirB_1` | `marth_LightThrowAirB_1.gif` | 30 |
| `LightThrowAirHi_1` | `marth_LightThrowAirHi_1.gif` | 30 |
| `LightThrowAirLw_1` | `marth_LightThrowAirLw_1.gif` | 27 |
| `HeavyThrowF` | `marth_HeavyThrowF.gif` | 45 |
| `HeavyThrowB` | `marth_HeavyThrowB.gif` | 45 |
| `HeavyThrowHi` | `marth_HeavyThrowHi.gif` | 35 |
| `HeavyThrowLw` | `marth_HeavyThrowLw.gif` | 35 |
| `HeavyThrowF_1` | `marth_HeavyThrowF_1.gif` | 45 |
| `HeavyThrowB_1` | `marth_HeavyThrowB_1.gif` | 45 |
| `HeavyThrowHi_1` | `marth_HeavyThrowHi_1.gif` | 35 |
| `HeavyThrowLw_1` | `marth_HeavyThrowLw_1.gif` | 35 |
| `SmashThrowF` | — | *empty (0)* |
| `SmashThrowB` | — | *empty (0)* |
| `SmashThrowHi` | — | *empty (0)* |
| `SmashThrowLw` | — | *empty (0)* |
| `SmashThrowDash` | — | *empty (0)* |
| `SmashThrowAirF` | — | *empty (0)* |
| `SmashThrowAirB` | — | *empty (0)* |
| `SmashThrowAirHi` | — | *empty (0)* |
| `SmashThrowAirLw` | — | *empty (0)* |
| `Swing1` | `marth_Swing1.gif` | 28 |
| `Swing3` | `marth_Swing3.gif` | 42 |
| `Swing4Start` | `marth_Swing4Start.gif` | 6 |
| `Swing4` | `marth_Swing4.gif` | 54 |
| `Swing42` | — | *empty (0)* |
| `Swing4Hold` | `marth_Swing4Hold.gif` | 61 |
| `SwingDash` | `marth_SwingDash.gif` | 46 |
| `Swing1_1` | `marth_Swing1_1.gif` | 28 |
| `Swing3_1` | `marth_Swing3_1.gif` | 42 |
| `Swing4Bat` | `marth_Swing4Bat.gif` | 90 |
| `SwingDash_1` | `marth_SwingDash_1.gif` | 46 |
| `Swing1_2` | `marth_Swing1_2.gif` | 28 |
| `Swing3_2` | `marth_Swing3_2.gif` | 42 |
| `Swing4Start_1` | `marth_Swing4Start_1.gif` | 6 |
| `Swing4_1` | `marth_Swing4_1.gif` | 54 |
| `Swing42_1` | — | *empty (0)* |
| `Swing4Hold_1` | `marth_Swing4Hold_1.gif` | 61 |
| `SwingDash_2` | `marth_SwingDash_2.gif` | 46 |
| `Swing1_3` | `marth_Swing1_3.gif` | 28 |
| `Swing3_3` | `marth_Swing3_3.gif` | 42 |
| `Swing4Start_2` | `marth_Swing4Start_2.gif` | 6 |
| `Swing4_2` | `marth_Swing4_2.gif` | 54 |
| `Swing42_2` | — | *empty (0)* |
| `Swing4Hold_2` | `marth_Swing4Hold_2.gif` | 61 |
| `SwingDash_3` | `marth_SwingDash_3.gif` | 46 |
| `Swing1_4` | `marth_Swing1_4.gif` | 28 |
| `Swing3_4` | `marth_Swing3_4.gif` | 42 |
| `Swing4Start_3` | `marth_Swing4Start_3.gif` | 6 |
| `Swing4_3` | `marth_Swing4_3.gif` | 54 |
| `Swing42_3` | — | *empty (0)* |
| `Swing4Hold_3` | `marth_Swing4Hold_3.gif` | 61 |
| `SwingDash_4` | `marth_SwingDash_4.gif` | 46 |
| `ItemHammerWait` | `marth_ItemHammerWait.gif` | 17 |
| `ItemHammerMove` | `marth_ItemHammerMove.gif` | 17 |
| `ItemHammerAir` | `marth_ItemHammerAir.gif` | 17 |
| `ItemHammerWait_1` | `marth_ItemHammerWait_1.gif` | 17 |
| `ItemHammerMove_1` | `marth_ItemHammerMove_1.gif` | 17 |
| `ItemHammerAir_1` | `marth_ItemHammerAir_1.gif` | 17 |
| `ItemDragoonRide` | `marth_ItemDragoonRide.gif` | 33 |
| `ItemScrew` | `marth_ItemScrew.gif` | 41 |
| `ItemScrew_1` | `marth_ItemScrew_1.gif` | 41 |
| `ItemScrewFall` | `marth_ItemScrewFall.gif` | 81 |
| `ItemDragoonGet` | `marth_ItemDragoonGet.gif` | 60 |
| `ItemDragoonRide_1` | `marth_ItemDragoonRide_1.gif` | 33 |
| `ItemBig` | `marth_ItemBig.gif` | 60 |
| `ItemSmall` | `marth_ItemSmall.gif` | 60 |
| `ItemLegsWait` | `marth_ItemLegsWait.gif` | 51 |
| `ItemLegsSlowF` | `marth_ItemLegsSlowF.gif` | 51 |
| `ItemLegsMiddleF` | `marth_ItemLegsMiddleF.gif` | 31 |
| `ItemLegsFastF` | `marth_ItemLegsFastF.gif` | 26 |
| `ItemLegsBrakeF` | `marth_ItemLegsBrakeF.gif` | 2 |
| `ItemLegsDashF` | `marth_ItemLegsDashF.gif` | 27 |
| `ItemLegsSlowB` | `marth_ItemLegsSlowB.gif` | 51 |
| `ItemLegsMiddleB` | `marth_ItemLegsMiddleB.gif` | 31 |
| `ItemLegsFastB` | `marth_ItemLegsFastB.gif` | 26 |
| `ItemLegsBrakeB` | `marth_ItemLegsBrakeB.gif` | 2 |
| `ItemLegsDashB` | `marth_ItemLegsDashB.gif` | 27 |
| `ItemLegsJumpSquat` | `marth_ItemLegsJumpSquat.gif` | 6 |
| `ItemLegsLanding` | `marth_ItemLegsLanding.gif` | 16 |
| `ItemShoot` | `marth_ItemShoot.gif` | 25 |
| `ItemShootAir` | `marth_ItemShootAir.gif` | 25 |
| `ItemShoot_1` | `marth_ItemShoot_1.gif` | 25 |
| `ItemShootAir_1` | `marth_ItemShootAir_1.gif` | 25 |
| `ItemShoot_2` | `marth_ItemShoot_2.gif` | 25 |
| `ItemShootAir_2` | `marth_ItemShootAir_2.gif` | 25 |
| `ItemScopeStart` | `marth_ItemScopeStart.gif` | 16 |
| `ItemScopeRapid` | `marth_ItemScopeRapid.gif` | 9 |
| `ItemScopeFire` | `marth_ItemScopeFire.gif` | 31 |
| `ItemScopeEnd` | `marth_ItemScopeEnd.gif` | 21 |
| `ItemScopeAirStart` | `marth_ItemScopeAirStart.gif` | 16 |
| `ItemScopeAirRapid` | `marth_ItemScopeAirRapid.gif` | 9 |
| `ItemScopeAirFire` | `marth_ItemScopeAirFire.gif` | 31 |
| `ItemScopeAirEnd` | `marth_ItemScopeAirEnd.gif` | 21 |
| `ItemScopeStart_1` | `marth_ItemScopeStart_1.gif` | 16 |
| `ItemScopeRapid_1` | `marth_ItemScopeRapid_1.gif` | 9 |
| `ItemScopeFire_1` | `marth_ItemScopeFire_1.gif` | 31 |
| `ItemScopeEnd_1` | `marth_ItemScopeEnd_1.gif` | 21 |
| `ItemScopeAirStart_1` | `marth_ItemScopeAirStart_1.gif` | 16 |
| `ItemScopeAirRapid_1` | `marth_ItemScopeAirRapid_1.gif` | 9 |
| `ItemScopeAirFire_1` | `marth_ItemScopeAirFire_1.gif` | 31 |
| `ItemScopeAirEnd_1` | `marth_ItemScopeAirEnd_1.gif` | 21 |
| `ItemLauncher` | `marth_ItemLauncher.gif` | 151 |
| `ItemLauncherFire` | `marth_ItemLauncherFire.gif` | 12 |
| `ItemLauncherAirFire` | `marth_ItemLauncherAirFire.gif` | 12 |
| `ItemLauncher_1` | `marth_ItemLauncher_1.gif` | 151 |
| `ItemLauncherFire_1` | `marth_ItemLauncherFire_1.gif` | 12 |
| `ItemLauncherAirFire_1` | `marth_ItemLauncherAirFire_1.gif` | 12 |
| `ItemLauncherFall` | `marth_ItemLauncherFall.gif` | 13 |
| `ItemLauncherAir` | — | *empty (0)* |
| `ItemAssist` | `marth_ItemAssist.gif` | 60 |
| `ItemScrew_2` | `marth_ItemScrew_2.gif` | 41 |

### Ground movement  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `WalkSlow` | `marth_WalkSlow.gif` | 61 |
| `WalkMiddle` | `marth_WalkMiddle.gif` | 46 |
| `WalkFast` | `marth_WalkFast.gif` | 25 |
| `WalkBrake` | `marth_WalkBrake.gif` | 2 |
| `Dash` | `marth_Dash.gif` | 28 |
| `Run` | `marth_Run.gif` | 17 |
| `RunBrake` | `marth_RunBrake.gif` | 26 |
| `Turn` | `marth_Turn.gif` | 12 |
| `TurnRun` | `marth_TurnRun.gif` | 30 |
| `TurnRunBrake` | `marth_TurnRunBrake.gif` | 21 |

### Jump  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `JumpSquat` | `marth_JumpSquat.gif` | 4 |
| `JumpF` | `marth_JumpF.gif` | 45 |
| `JumpF_1` | `marth_JumpF_1.gif` | 45 |
| `JumpB` | `marth_JumpB.gif` | 56 |
| `JumpB_1` | `marth_JumpB_1.gif` | 56 |
| `JumpAerialF` | `marth_JumpAerialF.gif` | 50 |
| `JumpAerialB` | `marth_JumpAerialB.gif` | 55 |
| `StepJump` | `marth_StepJump.gif` | 9 |

### Fall  (10)

| Subaction | GIF | Frames |
|---|---|---|
| `Fall` | `marth_Fall.gif` | 11 |
| `FallF` | `marth_FallF.gif` | 11 |
| `FallB` | `marth_FallB.gif` | 11 |
| `FallAerial` | `marth_FallAerial.gif` | 11 |
| `FallAerialF` | `marth_FallAerialF.gif` | 11 |
| `FallAerialB` | `marth_FallAerialB.gif` | 11 |
| `FallSpecial` | `marth_FallSpecial.gif` | 11 |
| `FallSpecialF` | `marth_FallSpecialF.gif` | 11 |
| `FallSpecialB` | `marth_FallSpecialB.gif` | 11 |
| `DamageFall` | `marth_DamageFall.gif` | 33 |

### Crouch  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `Squat` | `marth_Squat.gif` | 8 |
| `SquatWait` | `marth_SquatWait.gif` | 81 |
| `SquatWait2` | — | *empty (0)* |
| `SquatWaitItem` | `marth_SquatWaitItem.gif` | 81 |
| `SquatRv` | `marth_SquatRv.gif` | 8 |

### Landing  (8)

| Subaction | GIF | Frames |
|---|---|---|
| `LandingLight` | `marth_LandingLight.gif` | 3 |
| `LandingHeavy` | `marth_LandingHeavy.gif` | 3 |
| `LandingFallSpecial` | `marth_LandingFallSpecial.gif` | 31 |
| `LandingAirN` | `marth_LandingAirN.gif` | 15 |
| `LandingAirF` | `marth_LandingAirF.gif` | 15 |
| `LandingAirB` | `marth_LandingAirB.gif` | 24 |
| `LandingAirHi` | `marth_LandingAirHi.gif` | 15 |
| `LandingAirLw` | `marth_LandingAirLw.gif` | 25 |

### Ledge-step (walk-off)  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `StepPose` | `marth_StepPose.gif` | 9 |
| `StepBack` | `marth_StepBack.gif` | 21 |
| `StepAirPose` | `marth_StepAirPose.gif` | 9 |
| `StepFall` | `marth_StepFall.gif` | 41 |
| `Ottotto` | `marth_Ottotto.gif` | 6 |
| `OttottoWait` | `marth_OttottoWait.gif` | 101 |

### Shield  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `GuardOn` | `marth_GuardOn.gif` | 8 |
| `Guard` | `marth_Guard.gif` | 361 |
| `GuardOff` | `marth_GuardOff.gif` | 16 |
| `GuardDamage` | `marth_GuardDamage.gif` | 21 |
| `GuardOn_1` | `marth_GuardOn_1.gif` | 8 |
| `Guard_1` | `marth_Guard_1.gif` | 361 |

### Dodge / roll  (4)

| Subaction | GIF | Frames |
|---|---|---|
| `EscapeN` | `marth_EscapeN.gif` | 28 |
| `EscapeF` | `marth_EscapeF.gif` | 32 |
| `EscapeB` | `marth_EscapeB.gif` | 36 |
| `EscapeAir` | `marth_EscapeAir.gif` | 50 |

### Ground attack — jab / dash  (3)

| Subaction | GIF | Frames |
|---|---|---|
| `Attack11` | `marth_Attack11.gif` | 38 |
| `Attack12` | `marth_Attack12.gif` | 30 |
| `AttackDash` | `marth_AttackDash.gif` | 50 |

### Ground attack — tilt  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS3S` | `marth_AttackS3S.gif` | 44 |
| `AttackS3S_1` | `marth_AttackS3S_1.gif` | 44 |
| `AttackS3S_2` | `marth_AttackS3S_2.gif` | 44 |
| `AttackHi3` | `marth_AttackHi3.gif` | 40 |
| `AttackLw3` | `marth_AttackLw3.gif` | 50 |

### Ground attack — smash  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackS4Start` | `marth_AttackS4Start.gif` | 3 |
| `AttackS4S` | `marth_AttackS4S.gif` | 48 |
| `AttackS4S_1` | `marth_AttackS4S_1.gif` | 48 |
| `AttackS4S_2` | `marth_AttackS4S_2.gif` | 48 |
| `AttackS4Hold` | `marth_AttackS4Hold.gif` | 61 |
| `AttackHi4Start` | `marth_AttackHi4Start.gif` | 5 |
| `AttackHi4` | `marth_AttackHi4.gif` | 51 |
| `AttackHi4Hold` | `marth_AttackHi4Hold.gif` | 61 |
| `AttackLw4Start` | `marth_AttackLw4Start.gif` | 4 |
| `AttackLw4` | `marth_AttackLw4.gif` | 67 |
| `AttackLw4Hold` | `marth_AttackLw4Hold.gif` | 61 |

### Aerial attack  (5)

| Subaction | GIF | Frames |
|---|---|---|
| `AttackAirN` | `marth_AttackAirN.gif` | 50 |
| `AttackAirF` | `marth_AttackAirF.gif` | 34 |
| `AttackAirB` | `marth_AttackAirB.gif` | 40 |
| `AttackAirHi` | `marth_AttackAirHi.gif` | 46 |
| `AttackAirLw` | `marth_AttackAirLw.gif` | 60 |

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
| `Catch` | `marth_Catch.gif` | 31 |
| `CatchDash` | `marth_CatchDash.gif` | 40 |
| `CatchTurn` | `marth_CatchTurn.gif` | 40 |
| `CatchWait` | `marth_CatchWait.gif` | 61 |
| `CatchAttack` | `marth_CatchAttack.gif` | 24 |
| `CatchCut` | `marth_CatchCut.gif` | 30 |

### Throw  (23)

| Subaction | GIF | Frames |
|---|---|---|
| `ThrowB` | `marth_ThrowB.gif` | 40 |
| `ThrowF` | `marth_ThrowF.gif` | 32 |
| `ThrowHi` | `marth_ThrowHi.gif` | 45 |
| `ThrowLw` | `marth_ThrowLw.gif` | 43 |
| `ThrownB` | `marth_ThrownB.gif` | 50 |
| `ThrownF` | `marth_ThrownF.gif` | 40 |
| `ThrownHi` | `marth_ThrownHi.gif` | 45 |
| `ThrownLw` | `marth_ThrownLw.gif` | 40 |
| `ThrownDxB` | `marth_ThrownDxB.gif` | 50 |
| `ThrownDxF` | `marth_ThrownDxF.gif` | 40 |
| `ThrownDxHi` | `marth_ThrownDxHi.gif` | 45 |
| `ThrownDxLw` | `marth_ThrownDxLw.gif` | 43 |
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
| `CapturePulledHi` | `marth_CapturePulledHi.gif` | 20 |
| `CaptureWaitHi` | `marth_CaptureWaitHi.gif` | 61 |
| `CaptureDamageHi` | `marth_CaptureDamageHi.gif` | 20 |
| `CapturePulledLw` | `marth_CapturePulledLw.gif` | 20 |
| `CaptureWaitLw` | `marth_CaptureWaitLw.gif` | 61 |
| `CaptureDamageLw` | `marth_CaptureDamageLw.gif` | 20 |
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
| `CaptureCut` | `marth_CaptureCut.gif` | 31 |
| `CaptureJump` | `marth_CaptureJump.gif` | 51 |
| `Swallowed` | `marth_Swallowed.gif` | 11 |

### Damage / hitstun  (19)

| Subaction | GIF | Frames |
|---|---|---|
| `DamageHi1` | `marth_DamageHi1.gif` | 12 |
| `DamageHi2` | `marth_DamageHi2.gif` | 24 |
| `DamageHi3` | `marth_DamageHi3.gif` | 30 |
| `DamageN1` | `marth_DamageN1.gif` | 12 |
| `DamageN2` | `marth_DamageN2.gif` | 24 |
| `DamageN3` | `marth_DamageN3.gif` | 30 |
| `DamageLw1` | `marth_DamageLw1.gif` | 12 |
| `DamageLw2` | `marth_DamageLw2.gif` | 24 |
| `DamageLw3` | `marth_DamageLw3.gif` | 42 |
| `DamageAir1` | `marth_DamageAir1.gif` | 12 |
| `DamageAir2` | `marth_DamageAir2.gif` | 24 |
| `DamageAir3` | `marth_DamageAir3.gif` | 30 |
| `DamageFlyHi` | `marth_DamageFlyHi.gif` | 37 |
| `DamageFlyN` | `marth_DamageFlyN.gif` | 37 |
| `DamageFlyLw` | `marth_DamageFlyLw.gif` | 37 |
| `DamageFlyTop` | `marth_DamageFlyTop.gif` | 81 |
| `DamageFlyRoll` | `marth_DamageFlyRoll.gif` | 17 |
| `DamageElec` | `marth_DamageElec.gif` | 71 |
| `DamageFace` | — | *empty (0)* |

### Downed / getup  (20)

| Subaction | GIF | Frames |
|---|---|---|
| `DownBoundU` | `marth_DownBoundU.gif` | 27 |
| `DownWaitU` | `marth_DownWaitU.gif` | 71 |
| `DownDamageU` | `marth_DownDamageU.gif` | 14 |
| `DownDamageU3` | — | *empty (0)* |
| `DownEatU` | `marth_DownEatU.gif` | 30 |
| `DownStandU` | `marth_DownStandU.gif` | 30 |
| `DownAttackU` | `marth_DownAttackU.gif` | 55 |
| `DownForwardU` | `marth_DownForwardU.gif` | 40 |
| `DownBackU` | `marth_DownBackU.gif` | 40 |
| `DownBoundD` | `marth_DownBoundD.gif` | 27 |
| `DownWaitD` | `marth_DownWaitD.gif` | 71 |
| `DownDamageD` | `marth_DownDamageD.gif` | 14 |
| `DownDamageD3` | — | *empty (0)* |
| `DownEatD` | `marth_DownEatD.gif` | 30 |
| `DownStandD` | `marth_DownStandD.gif` | 30 |
| `DownAttackD` | `marth_DownAttackD.gif` | 55 |
| `DownForwardD` | `marth_DownForwardD.gif` | 44 |
| `DownBackD` | `marth_DownBackD.gif` | 44 |
| `DownSpotU` | `marth_DownSpotU.gif` | 30 |
| `DownSpotD` | — | *empty (0)* |

### Tech / passive  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `Passive` | `marth_Passive.gif` | 27 |
| `PassiveStandF` | `marth_PassiveStandF.gif` | 41 |
| `PassiveStandB` | `marth_PassiveStandB.gif` | 41 |
| `PassiveWall` | `marth_PassiveWall.gif` | 27 |
| `PassiveWallJump` | `marth_PassiveWallJump.gif` | 43 |
| `PassiveCeil` | `marth_PassiveCeil.gif` | 27 |
| `Pass` | `marth_Pass.gif` | 31 |

### Dizzy / sleep  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `FuraFura` | `marth_FuraFura.gif` | 101 |
| `FuraFuraStartU` | `marth_FuraFuraStartU.gif` | 50 |
| `FuraFuraStartD` | `marth_FuraFuraStartD.gif` | 50 |
| `FuraFuraEnd` | `marth_FuraFuraEnd.gif` | 50 |
| `FuraSleepStart` | `marth_FuraSleepStart.gif` | 30 |
| `FuraSleepLoop` | `marth_FuraSleepLoop.gif` | 81 |
| `FuraSleepEnd` | `marth_FuraSleepEnd.gif` | 60 |

### Ledge (cliff hang / getup)  (12)

| Subaction | GIF | Frames |
|---|---|---|
| `CliffCatch` | `marth_CliffCatch.gif` | 21 |
| `CliffWait` | `marth_CliffWait.gif` | 101 |
| `CliffAttackQuick` | `marth_CliffAttackQuick.gif` | 55 |
| `CliffClimbQuick` | `marth_CliffClimbQuick.gif` | 38 |
| `CliffEscapeQuick` | `marth_CliffEscapeQuick.gif` | 50 |
| `CliffJumpQuick1` | `marth_CliffJumpQuick1.gif` | 12 |
| `CliffJumpQuick2` | `marth_CliffJumpQuick2.gif` | 41 |
| `CliffAttackSlow` | `marth_CliffAttackSlow.gif` | 75 |
| `CliffClimbSlow` | `marth_CliffClimbSlow.gif` | 65 |
| `CliffEscapeSlow` | `marth_CliffEscapeSlow.gif` | 85 |
| `CliffJumpSlow1` | `marth_CliffJumpSlow1.gif` | 22 |
| `CliffJumpSlow2` | `marth_CliffJumpSlow2.gif` | 38 |

### Trip / slip  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SlipDown` | `marth_SlipDown.gif` | 41 |
| `Slip` | `marth_Slip.gif` | 30 |
| `SlipTurn` | `marth_SlipTurn.gif` | 36 |
| `SlipDash` | `marth_SlipDash.gif` | 46 |
| `SlipWait` | `marth_SlipWait.gif` | 71 |
| `SlipStand` | `marth_SlipStand.gif` | 22 |
| `SlipAttack` | `marth_SlipAttack.gif` | 55 |
| `SlipEscapeF` | `marth_SlipEscapeF.gif` | 36 |
| `SlipEscapeB` | `marth_SlipEscapeB.gif` | 36 |

### Swim  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `SwimRise` | `marth_SwimRise.gif` | 31 |
| `SwimUp` | `marth_SwimUp.gif` | 17 |
| `SwimUpDamage` | `marth_SwimUpDamage.gif` | 25 |
| `Swim` | `marth_Swim.gif` | 71 |
| `SwimF` | `marth_SwimF.gif` | 51 |
| `SwimEnd` | `marth_SwimEnd.gif` | 50 |
| `SwimTurn` | `marth_SwimTurn.gif` | 20 |
| `SwimDrown` | `marth_SwimDrown.gif` | 61 |
| `SwimDrownOut` | `marth_SwimDrownOut.gif` | 41 |

### Ladder / rope  (11)

| Subaction | GIF | Frames |
|---|---|---|
| `LadderWait` | `marth_LadderWait.gif` | 81 |
| `LadderUp` | `marth_LadderUp.gif` | 13 |
| `LadderDown` | `marth_LadderDown.gif` | 41 |
| `LadderCatchR` | `marth_LadderCatchR.gif` | 15 |
| `LadderCatchL` | `marth_LadderCatchL.gif` | 15 |
| `LadderCatchAirR` | `marth_LadderCatchAirR.gif` | 15 |
| `LadderCatchAirL` | `marth_LadderCatchAirL.gif` | 15 |
| `LadderCatchEndR` | `marth_LadderCatchEndR.gif` | 16 |
| `LadderCatchEndL` | `marth_LadderCatchEndL.gif` | 16 |
| `RopeCatch` | — | *empty (0)* |
| `RopeFishing` | — | *empty (0)* |

### Special move  (69)

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
| `SpecialNStart` | `marth_SpecialNStart.gif` | 12 |
| `SpecialNLoop` | `marth_SpecialNLoop.gif` | 31 |
| `SpecialNEnd` | `marth_SpecialNEnd.gif` | 33 |
| `SpecialNEnd_1` | `marth_SpecialNEnd_1.gif` | 33 |
| `SpecialAirNStart` | `marth_SpecialAirNStart.gif` | 12 |
| `SpecialAirNLoop` | `marth_SpecialAirNLoop.gif` | 31 |
| `SpecialAirNEnd` | `marth_SpecialAirNEnd.gif` | 33 |
| `SpecialAirNEnd_1` | `marth_SpecialAirNEnd_1.gif` | 33 |
| `SpecialS1` | `marth_SpecialS1.gif` | 30 |
| `SpecialS2Hi` | `marth_SpecialS2Hi.gif` | 45 |
| `SpecialS2Lw` | `marth_SpecialS2Lw.gif` | 45 |
| `SpecialS3Hi` | `marth_SpecialS3Hi.gif` | 52 |
| `SpecialS3S` | `marth_SpecialS3S.gif` | 51 |
| `SpecialS3Lw` | `marth_SpecialS3Lw.gif` | 45 |
| `SpecialS4Hi` | `marth_SpecialS4Hi.gif` | 51 |
| `SpecialS4S` | `marth_SpecialS4S.gif` | 66 |
| `SpecialS4Lw` | `marth_SpecialS4Lw.gif` | 61 |
| `SpecialAirS1` | `marth_SpecialAirS1.gif` | 30 |
| `SpecialAirS2Hi` | `marth_SpecialAirS2Hi.gif` | 45 |
| `SpecialAirS2Lw` | `marth_SpecialAirS2Lw.gif` | 45 |
| `SpecialAirS3Hi` | `marth_SpecialAirS3Hi.gif` | 52 |
| `SpecialAirS3S` | `marth_SpecialAirS3S.gif` | 51 |
| `SpecialAirS3Lw` | `marth_SpecialAirS3Lw.gif` | 55 |
| `SpecialAirS4Hi` | `marth_SpecialAirS4Hi.gif` | 51 |
| `SpecialAirS4S` | `marth_SpecialAirS4S.gif` | 66 |
| `SpecialAirS4Lw` | `marth_SpecialAirS4Lw.gif` | 61 |
| `SpecialHi` | `marth_SpecialHi.gif` | 40 |
| `SpecialAirHi` | `marth_SpecialAirHi.gif` | 40 |
| `SpecialLw` | `marth_SpecialLw.gif` | 60 |
| `SpecialLwHit` | `marth_SpecialLwHit.gif` | 37 |
| `SpecialAirLw` | `marth_SpecialAirLw.gif` | 60 |
| `SpecialAirLwHit` | `marth_SpecialAirLwHit.gif` | 37 |

### Taunt / appeal  (6)

| Subaction | GIF | Frames |
|---|---|---|
| `AppealHi` | `marth_AppealHi.gif` | 90 |
| `AppealHi_1` | `marth_AppealHi_1.gif` | 90 |
| `AppealS` | `marth_AppealS.gif` | 130 |
| `AppealS_1` | `marth_AppealS_1.gif` | 130 |
| `AppealLw` | `marth_AppealLw.gif` | 93 |
| `AppealLw_1` | `marth_AppealLw_1.gif` | 93 |

### Entry / win / lose  (9)

| Subaction | GIF | Frames |
|---|---|---|
| `EntryR` | `marth_EntryR.gif` | 121 |
| `EntryL` | `marth_EntryL.gif` | 121 |
| `Win1` | `marth_Win1.gif` | 206 |
| `Win1Wait` | `marth_Win1Wait.gif` | 86 |
| `Win2` | `marth_Win2.gif` | 251 |
| `Win2Wait` | `marth_Win2Wait.gif` | 86 |
| `Win3` | `marth_Win3.gif` | 241 |
| `Win3Wait` | `marth_Win3Wait.gif` | 81 |
| `Lose` | `marth_Lose.gif` | 113 |

### Final Smash  (7)

| Subaction | GIF | Frames |
|---|---|---|
| `FinalStart` | `marth_FinalStart.gif` | 50 |
| `FinalDash` | `marth_FinalDash.gif` | 7 |
| `FinalDashEnd` | `marth_FinalDashEnd.gif` | 91 |
| `FinalEnd` | `marth_FinalEnd.gif` | 71 |
| `FinalAirStart` | `marth_FinalAirStart.gif` | 50 |
| `FinalAirDashEnd` | `marth_FinalAirDashEnd.gif` | 91 |
| `FinalAirEnd` | `marth_FinalAirEnd.gif` | 71 |

### Misc / situational  (19)

| Subaction | GIF | Frames |
|---|---|---|
| *(unnamed slot)* | — | *empty (0)* |
| `_1` | — | *empty (0)* |
| `_2` | — | *empty (0)* |
| `_3` | — | *empty (0)* |
| `_4` | — | *empty (0)* |
| `_5` | — | *empty (0)* |
| `_6` | — | *empty (0)* |
| `Rebound` | `marth_Rebound.gif` | 31 |
| `_7` | — | *empty (0)* |
| `WallDamage` | `marth_WallDamage.gif` | 51 |
| `StopCeil` | `marth_StopCeil.gif` | 9 |
| `StopWall` | `marth_StopWall.gif` | 21 |
| `StopCeil_1` | `marth_StopCeil_1.gif` | 9 |
| `MissFoot` | `marth_MissFoot.gif` | 27 |
| `GekikaraWait` | `marth_GekikaraWait.gif` | 96 |
| `GanonSpecialHiCapture` | — | *empty (0)* |
| `GanonSpecialHiDxCapture` | — | *empty (0)* |
| `Dark` | — | *empty (0)* |
| `Spycloak` | — | *empty (0)* |

## Refs

- #777 (the Mario precedent) · #827 (the DK precedent this mirrors) · #758 (the GIF
  recipe) · #294 (Narz epic) / #290 (Narz spec — the consumer) · #614 / #753 (brawllib
  datamine env; `subaction_lengths` is a de-filtered `wait_lengths`) · #778 (the
  Nalio-vs-Mario sandbox — the Narz-vs-Marth equivalent this feeds).

<!-- rendered=383 empty=103 total=486 -->
