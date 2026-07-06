# Reading Project M engine globals — dump-environment setup

The extraction environment for the #638 primary-source verification pass: run a real PM 3.6
build in Dolphin and read its **engine-hardcoded globals** (e.g. the smash charge-frame cap that
#626 could not confirm from any offline primary) via the emulator's memory tools.

Status by piece:

| Piece | Ticket | State |
|---|---|---|
| Dolphin + Riivolution | **#639** | ✅ **done** (this doc) |
| PM 3.6 codeset | **#640** | ✅ **done** (acquired + MD5-verified, staged) |
| Clean NTSC-U Brawl ISO | (your own legal dump) | ⏳ your action — MD5-verify vs Redump |
| Extract the charge-cap global | (later #638 child) | ⏳ pending — unblocks #637 |

---

## #639 — Dolphin + Riivolution (done)

### Install / update (via dotfiles)

Dolphin is an **opt-in** section in `~/dotfiles/install.sh` — it does **not** auto-install on a
bare `./install.sh` pass:

```bash
cd ~/dotfiles
./install.sh dolphin                 # install (system flatpak; falls back to per-user without sudo)
REFRESH_DOLPHIN=1 ./install.sh dolphin   # update to the latest Flathub build
./install.sh verify                  # lists it under [ Flatpaks ]
```

- Source: **Flathub**, `org.DolphinEmu.dolphin-emu`. Flathub ships a current build.
- **Installed at setup:** build **2606** (user installation) — far past the **5.0-15407**
  threshold at which Riivolution became built in.
- On a machine without passwordless sudo the section installs **per-user** (`flatpak --user`);
  where sudo is available it installs system-wide (repo convention).

### Riivolution — no separate install

Riivolution is **built into Dolphin** (≥ 5.0-15407), which is exactly why we use Dolphin: there
is **no separate `riivolution` package** and **no ISO patching**. Standalone Riivolution is a
*real-hardware* Wii homebrew app — not needed for the emulator path.

- In Dolphin: **right-click the game in the list → "Start with Riivolution Patches…"**, point it
  at the PM 3.6 file set (#640), and it patches Brawl **at load** over a clean, unmodified ISO.

### Reading memory (where the globals are)

- **View → Memory** opens the memory viewer; the debugger's **RAM Watch** / search tools locate a
  value and watch it live while charging a smash.
- The smash charge cap is an **engine global** (not per-move subaction script data — confirmed in
  #626: brawllib_rs exposes no such constant), so it is read here, from RAM, not from
  rukaidata/brawllib_rs.

### Flatpak sandbox caveat

The sandboxed build may not see your ISO / SD-card directory by default. Grant access with
**Flatseal**, or:

```bash
flatpak override --user --filesystem=host org.DolphinEmu.dolphin-emu
```

---

## #640 — PM 3.6 codeset (done)

The **vanilla** PM 3.6 Homebrew Full Set — the mod half. **PM 3.6 specifically** (per
`pm36-canonical-reference`), **not** the `3.6+mf` fork that pmunofficial.com currently serves and
**not** Project+; either would silently diverge our baseline.

### Provenance (recorded)

| Field | Value |
|---|---|
| Package | vanilla PM 3.6 — Homebrew Full Set (`homebrew3.6.zip`, 596 MB) |
| Source | `https://projectmirror.no-ip.org/pm/3.6/homebrew3.6.zip` (GDrive alt id `0B5jcSvlgawOQaGJ4MW0wd0pleEk`) |
| Published MD5 | `bd13675fcae680ced0d8abc18410f05c` |
| Published SHA256 | `f200d44c59c42f836e08355c05fd640efe31469a35cd43d0dc33b7fba3e29799` |
| Downloaded MD5 | `bd13675fcae680ced0d8abc18410f05c` ✅ **matches published** |

The mirror publishes its own checksum (`…/homebrew3.6.zip.checksums`), and our download matches
it — so this is not the single-unverified-source weakness #626 warned about.

### Staged (gitignored)

```
repros/pm36-codeset/
  homebrew3.6.zip              # the verified archive
  extracted/
    codes/RSBE01.gct           # THE codeset — 63 KB, dated 2015-08-15 (PM 3.6 build date)
    projectm/pf/               # file patches (assets/.rel/.pac)
    apps/projectm/boot.elf     # launcher
```

`repros/` is gitignored — the codeset is **not** committed (it's PM's own redistributable mod
files, kept local as reference material, not repo content).

### Note — `RSBE01.gct` is itself a candidate primary

The 63 KB `codes/RSBE01.gct` is the compiled Gecko codeset. If PM changed the smash charge ramp,
that change is a Gecko code (a RAM-write/hook) **inside this file** — so disassembling the `.gct`
offline could read the value directly, no Brawl ISO / emulator boot required. Deferred: the
extraction approach (disassemble-`.gct` vs live RAM-dump) is a later #638 child, not #640.

---

## Next (remaining for the extraction)

1. **Your own Brawl ISO** — dump your legally-owned disc; **MD5-verify against Redump**
   (`RSBE01`, NTSC-U; Rev 2 is fine — its only downside is netplay desync, and we do not run
   networked multiplayer). Never redistribute an ISO.
2. **Extract** — either **disassemble `RSBE01.gct`** (offline; likely sufficient for an engine
   global) **or** boot PM 3.6 over the ISO in Dolphin/Riivolution and read the charge-cap global
   from RAM — record it with provenance → flips **#637**'s `⚠ primary-unconfirmed` to a primary
   `FOUND` (or corrects it). Approach TBD (a later #638 child).

## Refs

Epic **#638** (verification pass) · sibling **#640** (codeset) · motivating **#626 / #637** ·
legal/version hygiene settled in the #626 discussion · memories `pm36-canonical-reference`,
`rukaidata-engine-hardcoded-limit`.
