// pycats #988 (RESEARCH): dump a PM 3.6 fighter subaction's SCRIPT (not hitboxes) so we can
// read, from PM-primary move data, whether an up-special's move script (a) enters special-fall
// and (b) writes the JumpsUsed counter. Debug-prints script_main/other; caller greps the text.
//
// Usage (from the brawllib_rs clone, after `. ~/.cargo/env`):
//   cargo run --release --example script_dump -- -d <brawl> -m <mod> -f Kirby            # list subaction names
//   cargo run --release --example script_dump -- -d <brawl> -m <mod> -f Kirby -a SpecialAirHi
use brawllib_rs::brawl_mod::BrawlMod;
use brawllib_rs::high_level_fighter::HighLevelFighter;
use getopts::Options;
use std::env;
use std::path::PathBuf;

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
    let sf = matches.opt_str("a");

    let bm = BrawlMod::new(&brawl_path, mod_path.as_deref());
    let fighters = bm.load_fighters(true).expect("failed to load brawl mod");
    for fighter in fighters {
        if fighter.cased_name.to_lowercase() != ff.to_lowercase() {
            continue;
        }
        let hl = HighLevelFighter::new(&fighter);
        match &sf {
            None => {
                println!("# subactions for {}", fighter.cased_name);
                for sub in &hl.subactions {
                    println!("{}", sub.name);
                }
                return;
            }
            Some(target) => {
                for sub in &hl.subactions {
                    if sub.name.to_lowercase() != target.to_lowercase() {
                        continue;
                    }
                    println!("# fighter={} subaction={}", fighter.cased_name, sub.name);
                    println!("# iasa={:?} landing_lag={:?} frames={}", sub.iasa, sub.landing_lag, sub.frames.len());
                    println!("## script_main");
                    println!("{:#?}", sub.scripts.script_main);
                    println!("## script_other");
                    println!("{:#?}", sub.scripts.script_other);
                    return;
                }
                eprintln!("no subaction {} for {}", target, ff);
                std::process::exit(1);
            }
        }
    }
    eprintln!("no fighter {}", ff);
    std::process::exit(1);
}
