#!/usr/bin/env bash
# Datamine one fighter subaction's HIT boxes to JSON (#1207, I.1a of #1206).
#
# The version-controlled dumper source is scripts/brawllib/hitbox_dump.rs. This wrapper
# copies it into the brawllib_rs clone's examples/ (the clone keeps pycats examples as
# UNTRACKED files) and runs it against the PM 3.6 .pac data — so the clone edit is a
# transient copy and the source of record stays here.
#
# Env (see docs/tooling-brawllib-rs-datamine-recipe.md — "Prerequisites"):
#   clone  ~/Documents/Study/Rust/brawllib_rs
#   .pac   ~/Documents/Study/Rust/pm-data/{brawl-dump/DATA/files (-d), pm36-sd (-m)}
#   cargo  via ~/.cargo/env  (not on the non-login PATH)
# Adds NO new dependency (hitbox_dump.rs hand-formats JSON; no serde_json).
#
# Subaction names (recipe §2): Jab=Attack11, U-tilt=AttackHi3, F-smash release=AttackS4S, ...
#
# Usage:  scripts/datamine_hitboxes.sh <Fighter> <Subaction> [out.json]
#   scripts/datamine_hitboxes.sh Mario Attack11 tests/fixtures/datamine/mario_attack11_hitboxes.json
#   scripts/datamine_hitboxes.sh Mario Attack11            # no out => print to stdout
set -euo pipefail
. ~/.cargo/env
HERE="$(cd "$(dirname "$0")/.." && pwd)"
CLONE=~/Documents/Study/Rust/brawllib_rs
D=~/Documents/Study/Rust/pm-data/brawl-dump/DATA/files
M=~/Documents/Study/Rust/pm-data/pm36-sd
F="${1:?usage: datamine_hitboxes.sh <Fighter> <Subaction> [out.json]}"
A="${2:?usage: datamine_hitboxes.sh <Fighter> <Subaction> [out.json]}"
OUT="${3:-}"

[ -d "$CLONE" ] || { echo "brawllib_rs clone not found at $CLONE" >&2; exit 1; }
cp "$HERE/scripts/brawllib/hitbox_dump.rs" "$CLONE/examples/hitbox_dump.rs"
cd "$CLONE"

if [ -n "$OUT" ]; then
  mkdir -p "$HERE/$(dirname "$OUT")"
  cargo run --release --example hitbox_dump -- -d "$D" -m "$M" -f "$F" -a "$A" > "$HERE/$OUT"
  echo "wrote $OUT" >&2
else
  cargo run --release --example hitbox_dump -- -d "$D" -m "$M" -f "$F" -a "$A"
fi
