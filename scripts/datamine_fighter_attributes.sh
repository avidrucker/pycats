#!/usr/bin/env bash
# Datamine the full PM 3.6 roster's per-fighter movement attributes to a CSV (#1136).
#
# Emits one row per fighter with the raw PM units read straight from each fighter's
# FighterAttributes: walk/dash/run max, gravity, base + fast-fall terminal, full- and
# short-hop jump velocity, double-jump multiplier, jump count, weight. These are the
# authored-value source of record behind docs/research/pm36-fighter-attributes.csv, so
# the correct per-character values never require re-running the datamine by hand.
#
# Companion to scripts/datamine_stage_bounds.py. Reads the brawllib_rs env (#614/#794):
#   clone  ~/Documents/Study/Rust/brawllib_rs   (rukai/brawllib_rs @ e8dc833)
#   .pac   ~/Documents/Study/Rust/pm-data/{brawl-dump/DATA/files, pm36-sd}
# Needs cargo (rustup, `. ~/.cargo/env`). Uses only the clone's stock examples
# (movement_attrs for the roster list, high_level_frame_data for the attribute dump) —
# no clone modification, no new dependency. ~15 min for the full 44-fighter roster.
#
# Usage:  scripts/datamine_fighter_attributes.sh <out.csv>
set -u
. ~/.cargo/env
CLONE=~/Documents/Study/Rust/brawllib_rs
D=~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files
M=~/Documents/Study/Rust/pm-data/pm36-sd
OUT="${1:?usage: datamine_fighter_attributes.sh <out.csv>}"
cd "$CLONE" || { echo "brawllib_rs clone not found at $CLONE" >&2; exit 1; }

# internal codename -> display name (only the ones that differ)
declare -A DISP=(
  [Captain]="Captain Falcon" [Dedede]="King Dedede" [Diddy]="Diddy Kong"
  [Donkey]="Donkey Kong" [GKoopa]="Giga Bowser" [GameWatch]="Mr. Game & Watch"
  [Ganon]="Ganondorf" [Koopa]="Bowser" [Metaknight]="Meta Knight"
  [Purin]="Jigglypuff" [Popo]="Ice Climbers" [Robot]="R.O.B."
  [SZerosuit]="Zero Suit Samus" [PokeFushigisou]="Ivysaur"
  [PokeLizardon]="Charizard" [PokeZenigame]="Squirtle" [PokeTrainer]="Pokemon Trainer"
  [ToonLink]="Toon Link" [WarioMan]="Wario-Man" [Pikmin]="Olimar"
)

# roster codenames (from the movement_attrs example), pre-sorted
NAMES=$(cargo run --release --example movement_attrs -- -d "$D" -m "$M" 2>/dev/null | tail -n +2 | cut -f1)

# extract one FighterAttributes field from a {:#?} dump; anchor on leading indent +
# exact `field:` so term_vel does not match air_x_term_vel / dash_run_term_vel etc.
field() { grep -m1 -E "^[[:space:]]+$2:" "$1" | sed -E "s/^[[:space:]]+$2:[[:space:]]*//; s/,[[:space:]]*\$//" ; }

echo "fighter,codename,walk_max_vel,dash_init_vel,dash_run_term_vel,gravity,term_vel_base_fall,fastfall_velocity,jump_y_init_vel,jump_y_init_vel_short,air_jump_y_mult,num_jumps,weight" > "$OUT"

while IFS= read -r cn; do
  [ -z "$cn" ] && continue
  disp="${DISP[$cn]:-$cn}"
  tmp="$(mktemp)"
  cargo run --release --example high_level_frame_data -- -d "$D" -m "$M" -f "$cn" -l fighter 2>/dev/null > "$tmp"
  walk=$(field "$tmp" walk_max_vel); dash=$(field "$tmp" dash_init_vel); run=$(field "$tmp" dash_run_term_vel)
  grav=$(field "$tmp" gravity); term=$(field "$tmp" term_vel); ff=$(field "$tmp" fastfall_velocity)
  jmp=$(field "$tmp" jump_y_init_vel); sh=$(field "$tmp" jump_y_init_vel_short); ajm=$(field "$tmp" air_jump_y_mult)
  nj=$(field "$tmp" num_jumps); wt=$(field "$tmp" weight)
  rm -f "$tmp"
  echo "\"$disp\",$cn,$walk,$dash,$run,$grav,$term,$ff,$jmp,$sh,$ajm,$nj,$wt" >> "$OUT"
  echo "done: $disp ($cn)" >&2
done <<< "$NAMES"
echo "CSV written: $OUT" >&2
