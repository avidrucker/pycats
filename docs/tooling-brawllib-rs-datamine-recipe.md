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

## ⚠ Gated prerequisites — human-approve at execution (do NOT auto-install)

The clone is on disk, but **running** it is parked behind two human approvals (per RULES →
"Dependencies"):

1. **Rust toolchain** (`cargo` / `rustc`) — not installed on this machine (`which cargo` → nothing).
   The clone pins `rust-toolchain.toml` → channel **1.92** (+ `rustfmt`, `clippy`, and a
   `wasm32-unknown-unknown` target). The native examples below need only the 1.92 host toolchain; the
   **wasm32 target is not required** unless you build the wasm/visualiser examples. Proposed install
   (rustup, user-local, no root): `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
   then let the toolchain file select 1.92. **Propose only — do not run without approval.**
2. **PM 3.6 `.pac` files** — the game build data the parser reads; copyrighted, **not vendored**.
   `BrawlMod::new(brawl_dir, mod_dir)` overlays a **PM 3.6 SD-card build** (`-m`) on top of a
   **vanilla Brawl dump** (`-d`). Both must be obtained separately by the human and their paths
   supplied at run time.

Until both are approved and present, the run steps below are **not executed** — this recipe records
*how*, gated.

## Run recipe (parked behind the gate above)

All commands run from the clone: `cd ~/Documents/Study/Rust/brawllib_rs`.

### 1. Human-readable structured dump (no new deps)

The stock `high_level_frame_data` example already prints the processed tree (Rust `{:#?}` debug):

```bash
# -d vanilla Brawl dump   -m PM 3.6 SD-card overlay   -f fighter   -l data level
cargo run --release --example high_level_frame_data -- \
  -d /path/to/brawl-dump \
  -m /path/to/pm-3.6-sd \
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

### 3. Structured JSON / binary export (small addition — also gated)

The stock examples print debug text, not JSON. The `HighLevelFighter` structs are serde-`Serialize`,
so a machine-readable dump is a ~15-line custom example. Two options:

- **`bincode`** — already a dependency (`Cargo.toml`, serde feature). A binary dump needs **no new
  dep**.
- **`serde_json`** — **not** currently a dep; a JSON emitter would add `serde_json` as a
  dev-dependency to the clone's `Cargo.toml`. That is itself a (small, dev-only, out-of-repo) dep
  addition — treat it as gated with the toolchain approval, don't add it unprompted.

Sketch (`examples/dump_json.rs`, to add once approved):

```rust
use brawllib_rs::brawl_mod::BrawlMod;
use brawllib_rs::high_level_fighter::HighLevelFighter;
use std::path::PathBuf;
// build a BrawlMod(-d, -m), load_fighters(true), filter by fighter,
// let hl = HighLevelFighter::new(&fighter);
// println!("{}", serde_json::to_string_pretty(&hl).unwrap());   // needs serde_json dev-dep
```

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
