// pycats #1207 (I.1a of #1206): dump a fighter subaction's HIT boxes per frame as JSON,
// so the datamine-grounded hitbox proposer (#1206) has a sourced input.
//
// For each animation frame, each active hitbox is emitted with its:
//   - hitbox_id   (u8; a move's distinct hitboxes share an id across the frames they're live)
//   - size        (f32 radius, world units)
//   - pos         ([x, y, z] resolved WORLD position — next_pos = hitbox_position via
//                  transform_bones; the same world space gif_generator_fixed renders from,
//                  see src/renderer/draw.rs. NOT a bone-relative offset.)
//   - damage      (f32) and angle (i32 trajectory, degrees) from next_values Hit variant;
//                  null for a Grab-box variant.
// Plus a per-move summary: distinct-hitbox count + per-id active-frame windows.
//
// Axis convention matches examples/hurtbox_dump.rs: x = depth (into screen),
// y = vertical (up +), z = horizontal. pycats 2D consumes (z, y); the world->px transform
// is I.1b's job (this slice extracts only — no scaling, no Circle synthesis, no editor).
//
// JSON is hand-formatted (no serde_json) so this adds NO new dependency to the clone
// (recipe docs/tooling-brawllib-rs-datamine-recipe.md §3 flags serde_json as a gated dep).
// The clone keeps pycats examples untracked; the version-controlled SSOT is
// pycats scripts/brawllib/hitbox_dump.rs, copied in by scripts/datamine_hitboxes.sh.
//
// Usage (from the clone, after `. ~/.cargo/env`):
//   cargo run --release --example hitbox_dump -- -d <brawl> -m <mod> -f Mario -a Attack11

use brawllib_rs::brawl_mod::BrawlMod;
use brawllib_rs::high_level_fighter::{CollisionBoxValues, HighLevelFighter};

use getopts::Options;
use std::collections::BTreeMap;
use std::env;
use std::path::PathBuf;

/// Format an f32 as a JSON number, or `null` when non-finite (defensive — hitbox
/// values are finite in practice, and the pycats loader test asserts finiteness).
fn num(x: f32) -> String {
    if x.is_finite() {
        format!("{}", x)
    } else {
        "null".to_string()
    }
}

/// Collapse a sorted, de-duplicated frame-index list into inclusive `[start, end]` ranges.
fn windows(idxs: &[usize]) -> String {
    let mut ranges: Vec<String> = Vec::new();
    let mut start = idxs[0];
    let mut prev = idxs[0];
    for &v in &idxs[1..] {
        if v == prev + 1 {
            prev = v;
        } else {
            ranges.push(format!("[{}, {}]", start, prev));
            start = v;
            prev = v;
        }
    }
    ranges.push(format!("[{}, {}]", start, prev));
    ranges.join(", ")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut opts = Options::new();
    opts.optopt("d", "dir", "brawl dir", "DIR");
    opts.optopt("m", "mod", "mod dir", "DIR");
    opts.optopt("f", "fighter", "fighter", "NAME");
    opts.optopt("a", "subaction", "subaction", "NAME");
    let matches = opts.parse(&args[1..]).unwrap();

    let brawl_path = PathBuf::from(matches.opt_str("d").expect("need -d <brawl dir>"));
    let mod_path = matches.opt_str("m").map(PathBuf::from);
    let ff = matches.opt_str("f").expect("need -f <fighter>");
    let sf = matches.opt_str("a").expect("need -a <subaction>");

    let bm = BrawlMod::new(&brawl_path, mod_path.as_deref());
    let fighters = bm.load_fighters(true).expect("failed to load brawl mod");
    for fighter in fighters {
        if fighter.cased_name.to_lowercase() != ff.to_lowercase() {
            continue;
        }
        let hl = HighLevelFighter::new(&fighter);
        for sub in hl.subactions {
            if sub.name.to_lowercase() != sf.to_lowercase() {
                continue;
            }

            let n = sub.frames.len();
            let mut frames_json: Vec<String> = Vec::new();
            // hitbox_id -> the frame indices on which it is active (built in frame order,
            // so already sorted; a hitbox appears once per frame it's live).
            let mut active: BTreeMap<u8, Vec<usize>> = BTreeMap::new();

            for (i, frame) in sub.frames.iter().enumerate() {
                let mut boxes_json: Vec<String> = Vec::new();
                for hb in &frame.hit_boxes {
                    active.entry(hb.hitbox_id).or_default().push(i);
                    let (dmg, ang) = match &hb.next_values {
                        CollisionBoxValues::Hit(v) => (num(v.damage), format!("{}", v.trajectory)),
                        CollisionBoxValues::Grab(_) => ("null".to_string(), "null".to_string()),
                    };
                    let p = hb.next_pos;
                    boxes_json.push(format!(
                        "{{\"hitbox_id\": {}, \"size\": {}, \"pos\": [{}, {}, {}], \
                         \"damage\": {}, \"angle\": {}}}",
                        hb.hitbox_id,
                        num(hb.next_size),
                        num(p.x),
                        num(p.y),
                        num(p.z),
                        dmg,
                        ang
                    ));
                }
                frames_json.push(format!(
                    "    {{\"index\": {}, \"boxes\": [{}]}}",
                    i,
                    boxes_json.join(", ")
                ));
            }

            let mut windows_json: Vec<String> = Vec::new();
            for (id, idxs) in &active {
                windows_json.push(format!("\"{}\": [{}]", id, windows(idxs)));
            }
            let count = active.len();

            println!("{{");
            println!("  \"schema\": \"pycats.datamine.hitboxes/v1\",");
            println!("  \"fighter\": \"{}\",", fighter.cased_name);
            println!("  \"subaction\": \"{}\",", sub.name);
            println!("  \"frame_count\": {},", n);
            println!(
                "  \"summary\": {{\"count\": {}, \"windows\": {{{}}}}},",
                count,
                windows_json.join(", ")
            );
            println!("  \"frames\": [");
            println!("{}", frames_json.join(",\n"));
            println!("  ]");
            println!("}}");
            return;
        }
    }
    eprintln!("no match for fighter={} subaction={}", ff, sf);
    std::process::exit(1);
}
