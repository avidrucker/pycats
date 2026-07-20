# brawllib_rs — subaction → animated-GIF render recipe (visual reference)

**Ticket:** #758. **Sibling of:** [`tooling-brawllib-rs-datamine-recipe.md`](./tooling-brawllib-rs-datamine-recipe.md)
(the *numbers* recipe — hitbox values + `subaction.frames.len()` animation lengths). **Clone:**
`~/Documents/Study/Rust/brawllib_rs`. **First used:** #567/#760 (idle-breathing bob/squash).

## What this is for

The datamine recipe reads *numbers* out of a subaction (`subaction.frames.len()` = animation length,
hitbox sizes/positions). That answers "how many frames long is this animation?" but **not** "what does
the motion actually look like?" — e.g. a 51-frame `Wait1` loop tells you nothing about whether it
contains one visual breath or two.

This recipe renders a subaction to an **animated GIF** so you can *watch* the motion and measure it
frame-by-frame. It is how #567 found that Mario's `Wait1` loop holds **2** breaths (not one), and how
#760 measured the bob/squash **amplitude** (±5.3% / ±2.4% of body height). The render is brawllib_rs's
own hurtbox-capsule visualiser — the same renderer behind rukaidata.com's move GIFs — so it shows the
**skeleton/hurtbox motion**, not the character skin. That is exactly what you want for measuring
*motion*; the capsules track the bones.

> Note: rukaidata.com publishes GIFs mostly for **attack** subactions. `Wait*`/idle animations aren't
> reliably on the site, so rendering locally from our own extracted data is the dependable path.

## Prerequisites — the datamine env must be live

Same two inputs as the datamine recipe, and they are **already stood up** (#614 → #753; see the
`brawllib-datamine-env-live` agent memory):

- **Rust toolchain** — `install.sh rust` (dotfiles) installs rustup; the clone's `rust-toolchain.toml`
  pins 1.92 and auto-selects. In a **non-interactive / background shell** you must `source` cargo
  first or `cargo` is not on PATH (error #149):
  ```bash
  . ~/.cargo/env
  ```
- **PM 3.6 `.pac` data** — copyrighted, **never vendored**. Lives under `~/Documents/Study/Rust/pm-data/`:
  - `-d` = vanilla Brawl dump — the dir that **directly** contains `fighter/`
    (note the extracted-ISO nesting: `…/brawl-dump/DATA/files`);
  - `-m` = PM 3.6 overlay — a dir whose **child** has `pf/fighter` (so it's `…/pm36-sd/projectm`,
    a symlink into `repros/pm36-codeset/extracted/projectm`, #640).

A working **wgpu** backend is also needed (the GIF renderer runs on the GPU, or on a software fallback
like `llvmpipe`). On this machine it renders without extra setup.

## Render recipe

Run from the clone: `cd ~/Documents/Study/Rust/brawllib_rs`.

The stock `gif_generator` example renders one fighter+subaction to a GIF — **no new dependencies**
(it uses `renderer::render_gif_blocking` + `WgpuState::new_for_gif`, both in the crate):

```bash
. ~/.cargo/env                          # REQUIRED in non-interactive/background shells (err #149)
cargo run --release --example gif_generator -- \
  -d ~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files \   # vanilla Brawl (note DATA/files nesting)
  -m ~/Documents/Study/Rust/pm-data/pm36-sd \                 # PM 3.6 overlay (contains projectm/)
  -f Mario \                                                  # fighter (cased name; case-insensitive)
  -a Wait1                                                     # subaction (idle breathing loop)
```

It writes **`output_<Fighter>_<Subaction>.gif`** into the clone dir (e.g. `output_Mario_Wait1.gif`).
Copy it into the pycats repo's gitignored media dir for inspection (per the repros policy):

```bash
mkdir -p ~/Documents/Study/Python/pycats/repros/idle-breathing
cp output_Mario_Wait1.gif ~/Documents/Study/Python/pycats/repros/idle-breathing/mario_wait1.gif
```

For **subaction names** (which `-a` to pass), use the move→subaction map in the datamine recipe
(§"Subaction-name → move map"), or run the `high_level_frame_data` example with `-l fighter` to list
them. Idle: `Wait1` = the base breathing loop; `Wait2`/`Wait3` = the random fidget variants.

### Benign log spam — not failures

The run prints error-level lines that are **expected** and do not affect the GIF:

- `ERROR brawllib_rs::fighter] Can't load: Zako* / ZakoBall …` — known-unfixable NPC/enemy fighters in
  the dump; your target fighter still loads.
- `ERROR brawllib_rs::script_runner] Avoided Goto infinite loop` (repeated) — the script interpreter's
  loop guard firing on idle-wait scripts; harmless.

A successful run ends with `Finished` + the written `output_*.gif`; exit code 0.

## Measuring the motion (cycle count + amplitude)

A single frame can't tell you the number of visual cycles or the amplitude — analyse all frames. Open
the GIF with Pillow (already a pycats dep) and track the body's vertical extent per frame. This is the
exact method #567/#760 used:

```python
from PIL import Image
im = Image.open("repros/idle-breathing/mario_wait1.gif")
W, H = im.size
rows = []
for i in range(im.n_frames):
    im.seek(i); px = im.convert("RGB").load()
    top = bot = None
    for y in range(H):
        if any(sum(px[x, y]) > 60 for x in range(0, W, 2)):  # non-black = body
            if top is None: top = y
            bot = y
    rows.append((top, bot, bot - top))                       # head-top, feet-bottom, height
# center = (top+bot)/2 per frame; count its rise/fall cycles across the loop.
```

Reading it:

- **Fixed-camera check first.** brawllib renders the whole subaction with one camera. Confirm the
  **silhouette height stays ~constant** across frames while its *position* swings (and the extremes
  touch the canvas edges) — that proves the motion is real, not per-frame reframing. If height is
  ~constant, trust the position series.
- **Cycle count:** count the rise/fall cycles of the body **center** over the loop. Mario `Wait1` (51
  frames): center peaks at frames ~4 & ~26, troughs at ~13 & ~38 → **2 breaths per loop** → sin period
  = 51/2 = 25.5 f/breath.
- **Amplitude, scale-invariantly:** the GIF is in arbitrary render-units, so transfer the motion as a
  **fraction of body height**, not absolute px. Mario `Wait1`: body-center bob ±5.3%, squash (height
  change) ±2.4% of the ~270px body. Multiply by the pycats fighter's body-box height to get px (Nalio
  60px → ±3px bob, ±1px squash). Watch for **clipping** — if the head touches row 0 at the peak, the
  true amplitude is a hair larger.

## Refs

- [`tooling-brawllib-rs-datamine-recipe.md`](./tooling-brawllib-rs-datamine-recipe.md) — the numbers
  sibling (hitboxes, `frames.len()`, subaction→move map).
- `docs/research/2026-07-15-idle-breathing-cycle.md` — worked example: the #753 length dump + the
  #567/#760 GIF cycle-count and amplitude measurement.
- Example output: `repros/idle-breathing/mario_wait1.gif` (gitignored).
- Upstream: `github.com/rukai/brawllib_rs` (`examples/gif_generator.rs`).
- `brawllib-datamine-env-live` agent memory — the operational env + re-run command.
