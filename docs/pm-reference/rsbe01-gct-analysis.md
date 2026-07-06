# RSBE01.gct — structure, contents, and what it can (and can't) verify

Findings distilled from **#649** (the smash-charge GCT disassembly attempt), promoted into a
reusable reference because the lesson generalizes to **every** PM value we might try to verify from
the codeset. It is the launch doc for **#652** (the methodology/viability spike) — which extends
the "Open questions" section below into a verdict.

**One-line takeaway:** `RSBE01.gct` is a **patch/diff over Brawl's `main.dol`**, not a snapshot of
engine state, and it carries **no symbol names** — so a naive "search the codeset for the value"
does **not** work, and #649's smash-charge hunt came up empty for exactly that reason.

---

## 1. What the file is

- The compiled **Gecko codeset** for vanilla PM 3.6, staged (MD5-verified) by #640 at
  `repros/pm36-codeset/extracted/codes/RSBE01.gct`.
- **64,352 bytes = 8,044 Gecko codes** (8 bytes each), framed by the standard header
  `00d0c0de 00d0c0de` and terminator `f0000000 00000000`.
- Codetype histogram (first byte of each code) — the shape of the codeset:

  | Codetype | Count | Meaning |
  |---|---|---|
  | `0x00` | 1803 | 8-bit write / part of data blocks |
  | `0x04` | 735 | **32-bit RAM write** (address → value) |
  | `0x02` | 341 | 16-bit write |
  | `0x2c`, `0x06`, … | 319, 300 | conditional / write-block |
  | `0xC2` | 278 | **insert PPC ASM** at an address (a code hook) |
  | `0x40/41/7c/80/…` | — | pointer/offset/conditional ops |

  (`0x04` direct writes and `0xC2` ASM hooks are the two that carry "values".)

## 2. Method tried in #649

1. Parsed the GCT into its 8,044 codes; classified by codetype (histogram above).
2. Byte-scanned the file (and the **whole** extracted build) for the charge constants as float32
   big-endian: `1.3671` (`3faefd22`), `0.3671` (`3ebbf488`), `0.3671/60` (`3bc87c4d`), `1.4`
   (`3fb33333`).
3. Whole-file 4-byte float-window scan for any value in a charge-plausible range.
4. Inspected `pf/module/*.rel` (per-fighter / per-stage modules).

## 3. What #649 found

- **`1.3671` and `0.3671` are absent** — from the GCT and from every file in the build.
- **Brawl's `1.4` (`3fb33333`) is present**, but only inside an **unidentified embedded multiplier
  table** (~byte 45,836: `…3fb33333…3fb33333…3faaaaab…` = 1.4, 1.4, 1.333, among 0.91/1.167/1.579).
  It cannot be tied to smash-charge without a symbol map.
- **`59`/`60`** are too low-signal to locate in ASM without symbols.
- The float-window scan is dominated by **false positives** — `3bc0…`/`3bbd…`/`3fb3…` byte runs are
  PPC instruction encodings (`li`/`addi`), not float constants.
- Per-fighter `ft_*.rel` modules hold **no global charge logic** (charge is global engine behavior).

Tooling note: pure `grep -aP` on a byte pattern is unreliable on this binary (it reported 0 hits
for `3fb33333` that a Python byte-scan found present) — use a Python byte-scan, not grep, as the
authority (logged as error #97).

## 4. The structural lesson (why naive search fails)

`RSBE01.gct` is a set of **Gecko codes that patch/hook `main.dol` at load** — it is a **diff**, not
a full engine image. Consequences for value verification:

- **Only PM's *changes* are present.** A value PM left at Brawl's default does **not** appear in the
  GCT at all — so absence proves nothing about the base value.
- **`0x04` writes** are `address → value`: readable **iff** we can say *which engine variable* that
  address is. The GCT has **no symbol names**, so an address alone is opaque.
- **`0xC2` hooks** inject PPC assembly — the value may be *computed*, not stored as a literal; reading
  it means **disassembling the injected ASM**.
- Therefore the GCT can answer *"did PM change variable X, and (for a simple write) to what?"* — but
  **not** *"what is the base/engine value"* nor *"what is a value PM didn't touch"*. Smash charge
  (#649) landed in the worst case: no literal present, so either PM didn't change it via a stored
  constant, or the change is ASM in `main.dol` — neither extractable from the GCT alone.

## 5. Open questions (owned by #652 — do not answer here)

To make GCT-based verification **effective and consistent**, we'd need to resolve:

1. **Address → symbol mapping** — `doldecomp/brawl` (names `main.dol` functions/data), a documented
   Brawl RAM/data map, or PMDT's own annotated code list? Which is authoritative + offline?
2. **C2 disassembly tooling** — a Gecko/PPC disassembler; does it need a *new dependency* (gated —
   propose, don't install) or can `objdump`/Python do it?
3. **A repeatable pipeline** — parse → filter by target address → classify → read/disassemble — reusable
   for #192/#271/#243/#536; or a reasoned "not achievable from the GCT alone".
4. **Verdict** — can we verify values from the GCT **now**, **now-with-X**, or **not at all** — and
   does it help the 59/1.3671 charge case, or must that go via `main.dol`+`doldecomp/brawl` / a live
   RAM read.

## Refs

Source investigation **#649** (`smash-charge-ramp-provenance.md` → "Update (#649)") · methodology
spike **#652** (extends §5) · epic **#638** · codeset provenance `pm-globals-dump-setup.md` (#640) ·
motivating **#626 / #637** · the `doldecomp/brawl` lead (#626 thread).
