#!/usr/bin/env python3
"""Datamine a Brawl / Project M stage .pac for its boundary bones.

Reads a stage `.pac` (a raw `ARC` archive), LZ10-decompresses each ARC child,
walks the decompressed nested ARC for MDL0 bone headers, and prints the
authored (local) translate + the composed world-matrix translation for the
named boundary bones:

  Dead0N / Dead1N          death / blast (KO) boundary corners
  CamLimit0N / CamLimit1N  camera pan-limit corners
  Player1N..Player4N       player spawn points
  Rebirth1N..Rebirth4N     respawn-platform points

Corner convention (matches BrawlBox / libmelee): `*0N` = top-left (min x, max y),
`*1N` = bottom-right (max x, min y). So the blast quadruple is
`(Dead0N.x, Dead1N.x, Dead0N.y, Dead1N.y)` = (left, right, top, bottom).

Pure stdlib — no brawllib_rs needed. brawllib_rs *cannot* do this: its
`arc::arc()` assumes ARC-child-0 is a fighter `Sakurai` moveset block and never
LZ10-decompresses ARC *children* (only a whole-file top-level compression), so
it reads a garbage offset and panics on any stage pac (backtrace at
`sakurai::arc_sakurai`). See docs/research/2026-07-31-pm-fd-blast-zone-floats.md.

Bone-header byte layout (big-endian) is taken verbatim from brawllib_rs
`src/mdl0/bones.rs`:
  +0x00 u32 header_len (0xD0 for a standard MDL0 bone)
  +0x08 i32 string_offset  (name char-data offset, relative to the bone header)
  +0x20 3x f32 scale
  +0x38 3x f32 local translate
  +0x7c/+0x8c/+0x9c f32  translation column of the precomputed world matrix

Usage:
  python3 scripts/datamine_stage_bounds.py <stage.pac> [<stage.pac> ...]

The `.pac` files are copyrighted game data and are never committed; point this at
a local extracted dump (e.g. repros/pm36-codeset/.../STGFINAL.pac or a Brawl ISO
dump). See docs/research/2026-07-31-pm-fd-blast-zone-floats.md for the paths used.
"""

from __future__ import annotations

import re
import struct
import sys

ARC_HEADER_SIZE = 0x40
ARC_CHILD_HEADER_SIZE = 0x20
BONE_HEADER_LEN = 0xD0

BOUNDARY_BONES = [
    b"CamLimit0N",
    b"CamLimit1N",
    b"Dead0N",
    b"Dead1N",
    b"Player1N",
    b"Player2N",
    b"Player3N",
    b"Player4N",
    b"Rebirth1N",
    b"Rebirth2N",
    b"Rebirth3N",
    b"Rebirth4N",
]


def _u16(d: bytes, o: int) -> int:
    return struct.unpack_from(">H", d, o)[0]


def _i32(d: bytes, o: int) -> int:
    return struct.unpack_from(">i", d, o)[0]


def _u32(d: bytes, o: int) -> int:
    return struct.unpack_from(">I", d, o)[0]


def _f32(d: bytes, o: int) -> float:
    return struct.unpack_from(">f", d, o)[0]


def lz10_decompress(data: bytes) -> bytes:
    """Nintendo LZ77 type 0x10: 4-byte header (0x10 + 24-bit LE size), then
    flag-byte-driven literal / back-reference tokens."""
    if not data or data[0] != 0x10:
        raise ValueError(f"not LZ10-compressed (first byte {data[0:1].hex()})")
    size = data[1] | (data[2] << 8) | (data[3] << 16)
    out = bytearray()
    pos = 4
    while len(out) < size and pos < len(data):
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b0, b1 = data[pos], data[pos + 1]
                pos += 2
                length = ((b0 >> 4) & 0xF) + 3
                disp = (((b0 & 0xF) << 8) | b1) + 1
                start = len(out) - disp
                for _ in range(length):
                    out.append(out[start])
                    start += 1
            else:
                out.append(data[pos])
                pos += 1
    return bytes(out)


def arc_children(data: bytes) -> list[bytes]:
    """Return the raw bytes of each top-level ARC child."""
    count = _u16(data, 6)
    children = []
    hi = ARC_HEADER_SIZE
    for _ in range(count):
        if hi + ARC_CHILD_HEADER_SIZE > len(data):
            break
        size = _i32(data, hi + 4)
        doff = hi + ARC_CHILD_HEADER_SIZE
        children.append(data[doff : doff + size])
        hi += ARC_CHILD_HEADER_SIZE + size
        pad = hi % ARC_CHILD_HEADER_SIZE
        if pad:
            hi += ARC_CHILD_HEADER_SIZE - pad
    return children


def find_bone_header(blob: bytes, name_off: int) -> int | None:
    """Given the file offset of a bone's name char-data, locate the bone header:
    header_len == 0xD0 and string_offset (header+0x08) == name_off - header."""
    lo = max(0, name_off - 0x20000)
    for b in range(name_off, lo, -1):
        if b + BONE_HEADER_LEN > len(blob):
            continue
        if _u32(blob, b) != BONE_HEADER_LEN:
            continue
        if _i32(blob, b + 0x08) == name_off - b:
            return b
    return None


def extract(pac_path: str) -> None:
    data = open(pac_path, "rb").read()
    intern = data[0x10:0x30].split(b"\x00")[0].decode(errors="replace")
    print(f"=== {pac_path}  (internal name: {intern}, {len(data)} bytes) ===")
    # Decompress every child; the boundary bones live in the big model child.
    blobs = []
    for child in arc_children(data):
        if child[:1] == b"\x10":
            try:
                blobs.append(lz10_decompress(child))
            except ValueError:
                blobs.append(child)
        else:
            blobs.append(child)
    header = f"  {'bone':11}{'local x':>10}{'local y':>10}{'local z':>9}   {'world x':>10}{'world y':>10}{'world z':>9}"
    print(header)
    for name in BOUNDARY_BONES:
        hit = None
        for blob in blobs:
            m = re.search(re.escape(name) + b"\x00", blob)
            if m:
                b = find_bone_header(blob, m.start())
                if b is not None:
                    hit = (blob, b)
                    break
        if hit is None:
            print(f"  {name.decode():11}(not found)")
            continue
        blob, b = hit
        lx, ly, lz = _f32(blob, b + 0x38), _f32(blob, b + 0x3C), _f32(blob, b + 0x40)
        wx, wy, wz = _f32(blob, b + 0x7C), _f32(blob, b + 0x8C), _f32(blob, b + 0x9C)
        print(f"  {name.decode():11}{lx:10.2f}{ly:10.2f}{lz:9.2f}   {wx:10.2f}{wy:10.2f}{wz:9.2f}")
    print()


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        print("error: pass at least one stage .pac path", file=sys.stderr)
        return 2
    for pac in argv[1:]:
        extract(pac)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
