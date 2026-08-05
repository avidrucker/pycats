# Dash-attack IASA + per-frame velocity-curve datamine — findings (#963)

**Ticket:** #963 (RESEARCH · area:combat) — "5a" of the #948 dash-attack research epic. Datamines, per
archetype, the PM `AttackDash` **IASA / interrupt frame** (true recovery, vs #866's animation-tail
bound) and its **per-frame forward-velocity curve** (the #939 Q5 gap). Feeds **#930** (Fork 4 = Option B,
per-move movement field) and its DEV **5b** (persist the values).

**Scope:** findings + primary datamine only — **no ratified spec**, no data authored into pycats
(memory `research-never-produces-spec`; that's 5b / #930). Numbers are tagged primary / inference / gap
(memory `pm-parity-cite-primary-not-inference`).

**Archetype → PM fighter** (from each cat's module header): **nalio→Mario, birky→Kirby, gnok→Donkey
Kong, narz→Marth.** No cat has a `dash_attack` move key authored yet (expected — #930 Fork 3 sequences
that with the mechanic DEV).

---

## Method (primary — brawllib_rs PM datamine)

Datamine env is live (memory `brawllib-datamine-env-live`): brawllib_rs over vanilla Brawl (`-d`) +
the PM 3.6 overlay (`-m ~/…/pm36-sd`). A throwaway helper `examples/dash_attack_movement.rs` (left in
the clone, not committed to pycats — same pattern as the #866 `dash_attack_frames.rs`) reads each
fighter's `AttackDash` subaction and prints, per frame:

- **`iasa`** (`HighLevelSubaction.iasa`) — the first interruptible frame = the true recovery point.
- **`x_vel_modify`** (`VelModify::Set/Add`) — explicit **Self-Velocity script commands** (the carrying
  self-velocity, persists across frames).
- **`x_vel_temp`** — the **animation velocity** for that frame (the TransN translation baked into the
  animation; applies that frame only). brawllib composes displacement as `x_pos += x_vel + x_vel_temp`
  (`high_level_fighter.rs`), so a fighter's forward slide = carrying self-velocity **plus** animation
  velocity.

Units are Brawl/Melee **units/frame** (forward = +, `face`-signed at runtime). pycats scales spatial
units→px by `PX_PER_UNIT ≈ 5.4` (`config/physics.py`); a units→px conversion is **5b's** job, not done
here.

---

## Finding 1 — IASA / interrupt frames (true recovery)

*(primary — brawllib_rs PM)*

| Archetype (fighter) | Anim length | **IASA (interrupt)** | Active window | #866 tail bound | Correction |
|---|---|---|---|---|---|
| nalio (Mario) | 54 | **37** | 6–25 | 54 | tail was **17 f** too long |
| birky (Kirby) | 49 | **46** | 8–31 | 49 | tail was 3 f too long |
| gnok (Donkey Kong) | 43 | **38** | 9–20 | 43 | tail was 5 f too long |
| narz (Marth) | 50 | **40** | 12–15 | 50 | tail was 10 f too long |

- **IASA is the frame the dash attack becomes interruptible** (jump/tilt/smash/grab/dash/etc.). Recovery
  = IASA-1 through the interrupt; the animation may keep playing past IASA but the fighter is actionable.
- **Cross-validation (strong):** marth IASA = **40** exactly matches meleelight's marth `ATTACKDASH.interrupt`,
  which only opens actions at `timer > 39` (i.e. frame 40). Independent tool + independent codebase agree.
- **Active window** = frames with any hitbox present (`active_count`). Mario (6–25) and Kirby (8–31) hold
  a hitbox for a long span; whether that's a lingering single hit or a multi-hit is **out of scope**
  (#943 one-connect audit / #944 multi-hit parity), not decided here.

## Finding 2 — the forward slide is the **animation velocity** (`x_vel_temp`), except DK also scripts Self-Velocity

*(primary — brawllib_rs PM)*

Three of four fighters have **no** `x_vel_modify` command on any frame — their entire dash-attack slide
is the **animation velocity** `x_vel_temp`. **Donkey Kong is the exception**: it layers three explicit
`SetVelocity` commands (f1 `Set 0.75`, f5 `Set 3.75`, f20 `Set 1.10`) on top of its animation velocity —
a deliberate scripted lunge. So the per-move model #930 Option B must carry **both** channels for full
fidelity (an authored per-frame curve **plus** optional set-velocity events), though a single per-frame
effective-velocity array is a reasonable V1 simplification.

**Decisive Melee→PM confirmation:** brawllib's PM marth `x_vel_temp` matches meleelight's Melee
`ATTACKDASH.setVelocities` to ~3 decimals (below). #939 flagged Melee→PM as *inference*; this datamine
**confirms** PM inherited Melee's dash-attack velocity unchanged for marth (and, by the same pipeline,
the other three are read directly from PM data — no inference needed).

```
frame:              1       2       3       4       5       6       7       8      9      10     11
brawllib PM marth:  0.7554  1.9624  2.7136  3.0090  2.8486  2.2324  1.1836  0.5422 0.7045 1.3250 1.4874
meleelight Melee:   0.755   1.962   2.714   3.010   2.849   2.232   1.184   0.542  0.704  1.325  1.487
```

## Finding 3 — per-archetype forward-velocity curves

*(primary — brawllib_rs PM; `x_vel_temp` unless noted)*

Peak and shape per fighter (full arrays in the appendix). Peak in units/frame, and ×5.4 as an
illustrative px/f (5b owns the real conversion + rounding):

| Archetype | Curve shape | Peak (units/f) | ≈ px/f (×5.4) | Notes |
|---|---|---|---|---|
| narz (Marth) | ramp→peak f4, dip f8, 2nd hump f11, long taper | **3.009 @ f4** | ~16 | == meleelight; braking tail near 0 |
| nalio (Mario) | plateau ~1.84 f2–5, steady decay, small f27–29 bump | **1.893 @ f5** | ~10 | lower, sustained shove |
| gnok (Donkey Kong) | anim ramps to **3.47 @ f12**, plus `Set 3.75 @ f5` | **3.47 @ f12** (+Set 3.75) | ~19–20 | strongest lunge; scripted + animated |
| birky (Kirby) | slow build to **3.694 @ f11**, then long decay | **3.694 @ f11** | ~20 | late peak, gliding slide |

---

## Direct answers to the ticket

- **IASA / interrupt frame per archetype** → Finding 1 table (Mario 37, Kirby 46, DK 38, Marth 40).
  Supersedes #866's animation-tail recovery bound (which over-counted by 3–17 f).
- **Per-frame forward-velocity curve per archetype** → Findings 2–3 + appendix arrays. Source-of-truth
  is the animation velocity `x_vel_temp` (+ DK's three `SetVelocity` events).
- **Melee→PM inference (from #939)** → **confirmed** for marth by direct PM datamine match; the other
  three are read straight from PM data.

## Gaps / handoffs (not decided here)

1. **How pycats represents/consumes the curve** (single effective-velocity array vs animation-curve +
   set-velocity events; units→px rounding; whether to store full 40–54-frame arrays or a compressed
   model) — that is **5b (DEV)** + the #930 Option-B field design, not this research.
2. **DK's two-channel composition** — pycats' Option-B field must decide whether to fold DK's
   `Set` events into one effective curve or model both channels. Flagged for 5b.
3. **Active-window hit semantics** (lingering vs multi-hit for the long Mario/Kirby windows) — belongs
   to **#943 / #944**, out of scope here.

## Appendix — full per-frame `x_vel_temp` arrays (units/frame, PM)

**Marth** (len 50, IASA 40): 0.7554, 1.9624, 2.7136, 3.0090, 2.8486, 2.2324, 1.1836, 0.5422, 0.7045,
1.3250, 1.4874, 1.0789, 0.6353, 0.6418, 0.6164, 0.5504, 0.5503, 0.5077, 0.4818, 0.4580, 0.4360, 0.4065,
0.4065, 0.3704, 0.3247, 0.2963, 0.2720, 0.2518, 0.2270, 0.2018, 0.1874, 0.1836, 0.1742, 0.1669, 0.1481,
0.1269, 0.1148, 0.0835, 0.0674, 0.0674, 0.0321, 0.0108, then ~0 to end.

**Mario** (len 54, IASA 37): −0.0034, 1.8443, 1.8443, 1.8443, 1.8929, 1.7696, 1.7755, 1.7636, 1.7338,
1.7336, 1.5966, 1.4333, 1.4122, 1.3765, 1.3263, 1.2614, 1.1820, 1.0879, 0.9793, 0.8560, 0.7008, 0.5440,
0.4186, 0.3246, 0.2619, 0.2305, 0.2305, 0.2619, 0.3246, 0.0089, 0.1380×7, 0.1627, then ~−0.012 to end.

**Kirby** (len 49, IASA 46): 0, 0.8733, 0.6706, 0.5896, 0.6301, 0.7922, 1.0760, 1.4814, 2.0084, 3.5250,
3.6942, 2.5913, 2.4758, 2.3653, 2.2600, 2.1597, 2.0645, 1.9745, 1.8895, 1.8096, 1.7348, 1.6650, 1.6004,
1.5409, 1.4864, 1.4371, 1.3928, 1.3537, 1.3196, 1.2906, 1.2667, 1.2479, 1.2342, 1.2256, 1.2221, 1.1149,
0.9238, 0.7671, 0.6449, 0.5572, 0.5039, 0.4271, 0.3202, 0.2379, 0.1804, 0.1475, 0.1392, 0.1557, 0.1968.

**Donkey Kong** (len 43, IASA 38) — animation `x_vel_temp`, **plus** `SetVelocity`: f1 `Set 0.75`,
f5 `Set 3.75`, f20 `Set 1.10`: temp = 0.0034, 0.7000, 0.2247, 0.2011, 0.6294, 1.5095, 2.3412, 2.7592,
3.0806, 3.3054, 3.4337, 3.4655, 3.4008, 3.2395, 2.9816, 2.7891, 2.2691, 1.4451, 0.9460, 0.7049, 0.6327,
0.5611, 0.4949, 0.4339, 0.3783, 0.3280, 0.2830, 0.2433, 0.2090, 0.1800, 0.1563, 0.1379, 0.1248, 0.1171,
0.1146, 0.1175, 0.1257, 0.1393, 0.1581, 0.1823, 0.2118, 0.2466, 0.2867.

## Provenance

- **primary (PM 3.6 datamine):** brawllib_rs `examples/dash_attack_movement.rs` (this session) over
  `~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files` + `pm36-sd` overlay; fields
  `HighLevelSubaction.iasa`, `HighLevelFrame.x_vel_modify` (`VelModify::Set/Add`), `.x_vel_temp`
  (`src/high_level_fighter.rs`). Env per memory `brawllib-datamine-env-live`.
- **primary-reimpl (Melee, cross-check):** meleelight `src/characters/marth/moves/ATTACKDASH.js`
  (`setVelocities`, `interrupt` at `timer > 39`) — matches the PM datamine, confirming #939's inference.
- **superseded:** #866 animation-tail recovery bound (`docs/research/2026-07-31-dash-attack-mechanic-spec.md`);
  brawllib_rs `examples/dash_attack_frames.rs` (#866 helper — length/active only, no IASA/velocity).

## Cross-refs

#948 (epic) · #930 (architect; Fork 4 = Option B) · #939 (per-action movement model; Q5 gap now filled) ·
#866 (animation-tail bound, superseded for recovery) · 5b (DEV: persist IASA + velocity, downstream) ·
#943 / #944 (hit semantics of the active window) · #388 (walk/dash/run epic).
