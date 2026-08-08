# brawllib_rs — local PM move-data datamining recipe

**Ticket:** #614. **Companion to:** [`research-120-smash-units-and-sources.md`](./research-120-smash-units-and-sources.md)
(rukaidata = ⭐ primary source for *moves / hitboxes*). **Clone:** `~/Documents/Study/Rust/brawllib_rs`
(`rukai/brawllib_rs` @ `e8dc833`, the parsing **crate** — *not* `rukai/rukaidata`, the site generator that
consumes it).

## What this is for

Run `brawllib_rs` locally against **PM 3.6 `.pac` files** to emit structured **per-subaction move
data** — the same data rukaidata.com renders, but as a machine-readable dump we own, instead of
scraping per-subaction HTML. This is our primary path for cat-archetype **hitbox** values
(Nalio / Narz / Birky smash hitboxes, tilts, aerials).

The processed `HighLevelFighter` tree exposes, per subaction frame, a `hit_boxes` list whose structs
(verified serde-`Serialize` in `src/high_level_fighter.rs`) carry exactly the fields we source:

- `damage`, `bkb` (base knockback), `kbg` (knockback growth), angle
- `hitbox_id`, `size`, `x_pos` / `y_pos` (hitbox placement)
- `x_vel_modify` / `y_vel_modify` (scripted self-velocity), `x_vel_temp` / `y_vel_temp`

## ⚠ Scope boundary — moves/hitboxes ONLY, NOT engine globals

brawllib_rs datamines per-character **subaction scripts**. It does **NOT** expose
**engine-hardcoded globals** — smash charge duration/multiplier, air-dodge velocity, etc. live in the
engine / common data, not in subaction scripts (established #215/#222; the `DODGE_AIR_SPEED`
precedent). So this tool is out of scope for #599's charge globals and any engine literal — those
need meleelight / a decomp / the PM codeset (a separate ticket + the sourcing map). Do not attempt to
read a global out of a subaction dump.

## Prerequisites — the env is LIVE (both obtained; #794 §7)

Both prerequisites were obtained by the human and are present on this machine — the run steps below
**execute as written**. (Historically these were the two gated dependencies, per RULES →
"Dependencies"; that gate is cleared. A *new* toolchain/data install still needs approval, but nothing
below installs anything.)

1. **Rust toolchain** — installed via rustup: **cargo 1.97.1 / rustc 1.97.1** at `~/.cargo/bin`
   (not on the non-login `PATH` — source it first with `. ~/.cargo/env`; a bare `which cargo` misses
   it). The clone's `rust-toolchain.toml` pins channel 1.92, but the installed host toolchain builds
   the native examples fine. The `wasm32` target is only needed for the wasm/visualiser examples.
2. **PM 3.6 `.pac` files** — present at **`~/Documents/Study/Rust/pm-data/`**: a vanilla Brawl dump at
   `pm-data/brawl-dump/DATA/files` (`-d`) with the PM 3.6 SD-card build overlaid from `pm-data/pm36-sd`
   (`-m`). Copyrighted, so **still not vendored** into either repo; they live only under `pm-data/`.

## Run recipe (live)

All commands run from the clone: `cd ~/Documents/Study/Rust/brawllib_rs` after `. ~/.cargo/env`.
The `-d`/`-m` paths below are the real on-disk locations.

### 1. Human-readable structured dump (no new deps)

The stock `high_level_frame_data` example already prints the processed tree (Rust `{:#?}` debug) — and,
at `-l fighter`, includes the full `FighterAttributes` block (walk/dash/run, gravity, term/fastfall,
jump velocities, num_jumps, weight — the per-character movement source of record, #1136):

```bash
. ~/.cargo/env
# -d vanilla Brawl dump   -m PM 3.6 SD overlay   -f fighter   -l data level
cargo run --release --example high_level_frame_data -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \
  -f Mario \
  -l subaction \
  -a AttackS4S      # optional: one subaction (here f-smash); omit for all
```

Data levels (`-l`): `fighter` (whole tree), `subaction` (one move's frames), `frame` (with `-i N`).
`dump_fighter` (`-d`/`-m`/`-f`) gives the raw pre-processed `Fighter` tree if you need the low-level view.

### 2. Subaction-name → move map (which subaction holds a move's hitboxes)

From `examples/first_active_frames.rs` (authoritative in-tree list):

| Move | Subaction | Move | Subaction |
|---|---|---|---|
| Jab | `Attack11` | F-smash | `AttackS4Start` / `AttackS4S` |
| U-tilt | `AttackHi3` | D-smash | `AttackLw4Start` / `AttackLw4` |
| D-tilt | `AttackLw3` | U-smash | `AttackHi4Start` / `AttackHi4` |
| F-tilt | `AttackS3S` | Nair/Fair/Bair | `AttackAirN` / `AttackAirF` / `AttackAirB` |
| Dair/Uair | `AttackAirLw` / `AttackAirHi` | Dash attack | `AttackDash` |

(Smash attacks split into a `…Start` charge subaction and the release `…S`/`…4` — read hitboxes from
the release subaction.)

### 3. Structured JSON / binary export (a new-dependency gate, distinct from the now-cleared env gate)

The stock examples print debug text, not JSON. The `HighLevelFighter` structs are serde-`Serialize`,
so a machine-readable dump is a ~15-line custom example. Two options:

- **`bincode`** — already a dependency (`Cargo.toml`, serde feature). A binary dump needs **no new
  dep**.
- **`serde_json`** — **not** currently a dep; a JSON emitter would add `serde_json` as a
  dev-dependency to the clone's `Cargo.toml`. That is a (small, dev-only, out-of-repo) dep addition —
  **still gated** (adding any new dependency needs approval, RULES "Dependencies"), independent of the
  env gate above being cleared. Don't add it unprompted. For a machine-readable roster dump today,
  `scripts/datamine_fighter_attributes.sh` sidesteps this — it greps the stock `{:#?}` output instead
  of adding a JSON emitter, so it needs no new dep.

Sketch (`examples/dump_json.rs`, to add once approved):

```rust
use brawllib_rs::brawl_mod::BrawlMod;
use brawllib_rs::high_level_fighter::HighLevelFighter;
use std::path::PathBuf;
// build a BrawlMod(-d, -m), load_fighters(true), filter by fighter,
// let hl = HighLevelFighter::new(&fighter);
// println!("{}", serde_json::to_string_pretty(&hl).unwrap());   // needs serde_json dev-dep
```

### 4. Per-frame HIT-box JSON table — `hitbox_dump` (#1207, no new dep)

The datamine-grounded hitbox proposer (#1206) needs, per subaction, each hitbox's id / radius /
resolved world position / damage / angle per frame. That dumper exists and is **version-controlled in
pycats** — `scripts/brawllib/hitbox_dump.rs` — with a wrapper that copies it into the clone's
untracked `examples/` and runs it:

```bash
# writes JSON to <out.json> (relative to repo root); omit the 3rd arg to print to stdout
scripts/datamine_hitboxes.sh Mario Attack11 pycats/combat/datamine_data/mario_attack11_hitboxes.json
```

It sidesteps the `serde_json` gate above by **hand-formatting** the JSON (each field is a `u8`/`f32`/
`i32`), so it needs **no new dependency**. Output schema `pycats.datamine.hitboxes/v1`: top-level
`fighter` / `subaction` / `frame_count`, a `summary` (`count` of distinct `hitbox_id`s + per-id active
`windows` as inclusive `[start, end]` frame ranges), and `frames[]` each `{index, boxes[]}` where a
box is `{hitbox_id, size, pos: [x, y, z], damage, angle}`. `pos` is the **resolved WORLD** position
(x=depth, y=vertical up+, z=horizontal), unscaled — the same space `gif_generator_fixed` renders from
(`next_pos = hitbox_position` via `transform_bones`; `src/renderer/draw.rs`). The world→pycats-px
transform + `Circle` synthesis are **out of scope** here (that is I.1b) — this slice extracts only.

The pycats consumer is `pycats.combat.datamine_hitboxes.load_hitbox_table(path)`; a committed one-move
table (`pycats/combat/datamine_data/mario_attack11_hitboxes.json`, packaged since #1314) keeps
downstream slices + tests runnable without this gated env.

## Refs

- [`tooling-brawllib-rs-gif-recipe.md`](./tooling-brawllib-rs-gif-recipe.md) — the **visual** sibling:
  render a subaction to an animated GIF (`gif_generator`) + measure its motion (cycle count / amplitude),
  for when you need to *watch* an animation, not just read its frame count (#758, first used #567/#760).
- `docs/research-120-smash-units-and-sources.md` — sourcing map (rukaidata ⭐ primary for moves).
- Engine-global limit: #215 / #222, the `DODGE_AIR_SPEED` precedent; #599 charge globals are **not**
  sourced here.
- Companion tooling: a **meleelight** clone (sibling ticket) for engine-hardcoded literals.
- Upstream: `github.com/rukai/brawllib_rs` (crate), `github.com/rukai/rukaidata` (site generator).
- Workspace convention: `~/Documents/Study/<Stack>/<repo>/`.
