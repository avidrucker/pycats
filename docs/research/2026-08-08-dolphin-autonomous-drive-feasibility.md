# Can an agent drive Dolphin autonomously (Playwright-style)? — feasibility findings (#1326)

> Research findings (#1326, parent #638, relates #1250). **Survey only — no harness
> built, no campaign value read.** Asks whether an agent can boot PM 3.6, inject
> inputs, and read emulated RAM without a human at the GUI, so the #638 live-read
> campaign (#1250) stops needing a human clicking Dolphin.
>
> Date: 2026-08-08. Agent: CHERRY. Area: `area:cross-cutting`.
> Primary sources cited inline; local-machine facts probed on this machine on the date above.

## TL;DR — **Yes.** An autonomous "trigger-a-move → read-a-RAM-value" loop is buildable on this exact stack.

Every primitive exists in a primary-sourced, **game-agnostic** form. The only
Melee-coupled piece (libmelee's state layer) is not on the critical path — its
address-based memory alternative is generic and Wii-aware. On *this* machine the two
Flatpak worries that could have blocked it are already resolved: `ptrace_scope=0` and
`filesystems=host`.

**The one thing none of these tools give you: the PM 3.6 memory map.** They move bytes
at addresses you supply; they do not know game structures. Producing the address list
for the values #1250 wants (e.g. `escapeair_force`, the fireball article block) is the
work that remains — and it is the same work a manual RAM session would need. Automation
removes the human-at-the-GUI, not the address-finding.

## Local machine — the stack this verdict is against

Probed 2026-08-08:

| Fact | Value | Why it matters |
|---|---|---|
| Flatpak Dolphin | `org.DolphinEmu.dolphin-emu` branch `stable`, version **2606**, x86_64 | The env #639 staged; GUI build (no `dolphin-emu-nogui`). |
| `filesystems` | includes **`host`** (read/write to the app's own data tree regardless) | A FIFO in the app data dir is one shared inode host↔sandbox — the input half needs no extra permission. |
| `shared` | `network;ipc` | — |
| `kernel.yama.ptrace_scope` | **0** (permissive) | A same-uid host process may `process_vm_readv` Dolphin with **no** sysctl change and **no** `setcap`. The memory-read half works out of the box here. |
| python3 | 3.12.3 | `pip install dolphin-memory-engine` (manylinux x86_64 wheels). |
| ISOs | `~/Downloads/Project M 3.6.iso`, `~/Downloads/Super Smash Bros. Brawl (USA) (Rev 2).iso` | Both present; Dolphin has scanned `RSBE01`. |

## Mechanism survey (6)

### 1. Memory read/write from outside the emulator — **WORKS (game-agnostic)**

`aldelaro5/Dolphin-memory-engine` attaches to a running Dolphin and reads/writes
emulated MEM1/MEM2 by address. Explicitly generic ("Open Dolphin and start a game, then
run this program"), and it detects Wii MEM2 — which RSBE01 (a Wii title) uses. Linux
path needs `CAP_SYS_PTRACE` (README: `setcap cap_sys_ptrace=eip`) or a relaxed Yama
scope. Source: <https://github.com/aldelaro5/Dolphin-memory-engine>

Python binding: `dolphin-memory-engine` on PyPI (maintained by the Randovania org —
`randovania/py-dolphin-memory-engine` — a reimplementation of the hook technique, not a
wrapper). "Hooks into the memory of a running Dolphin process," general-purpose,
x86_64-Linux manylinux wheels. Sources:
<https://pypi.org/project/dolphin-memory-engine/> ·
<https://github.com/henriquegemignani/py-dolphin-memory-engine>

**On this machine:** `ptrace_scope=0` already grants the attach; no `setcap` needed for a
host-side reader. You supply RSBE01/PM-3.6 addresses — the tool is address-agnostic.

### 2. Input injection — **WORKS (named pipe, mainline); DTM is the wrong tool for a reactive loop**

Dolphin Linux "Pipe Input": `mkfifo pipe1` in the Dolphin user folder, bind it via
`Config/GCPadNew.ini` with `Device = Pipe/0/pipe1`, and write text commands —
`PRESS <button>`, `RELEASE <button>`, `SET <MAIN|C> X Y` (axes 0–1). UNIX-only, Dolphin
≥ 4.0-8065 (long in mainline). Source:
<https://wiki.dolphin-emu.org/index.php?title=Pipe_Input>

TAS `.dtm` movies do deterministic *replay*, not live per-frame reaction, so they are
the wrong primitive for a trigger→react agent — pipe input is the one to use. (The wiki
Movies/TAS page 404'd at survey time; nothing here depends on the DTM claim.)

### 3. Headless / batch boot — **PARTIAL**

`-b/--batch` boots without the game-list UI and exits when emulation ends; it requires
`-e/--exec=<file>`. `-u/--user=<dir>` sets the session user dir. Sources:
<https://us.dolphin-emu.org/docs/guides/controlling-global-user-directory/> ·
<https://man.archlinux.org/man/dolphin-emu-nogui.6.en>

A true no-GUI build exists (`dolphin-emu-nogui`, CMake `-DENABLE_HEADLESS`,
`--platform=headless`), but the standard GUI binary under `--batch --exec` still opens an
X11/EGL render surface, so on a display-less server you wrap it in `xvfb-run`. The
Flathub package ships the **GUI** app (`--socket=x11`), not `dolphin-emu-nogui`. Sources:
<https://github.com/dolphin-emu/dolphin/wiki/Building-for-Linux> · man page above.

**On this machine:** there is an X11 display (`QT_QPA_PLATFORM=xcb`), so
`flatpak run … -b -e <iso>` boots directly — Xvfb is only needed for a true headless/CI box.

### 4. Scripting forks (in-process memory) — **WORKS via Felk's Python fork (generic); Lua forks DEAD-END; Slippi is Melee-specific**

- **Felk/dolphin** (mainline Python-scripting-preview lineage): embeds a Python API —
  `from dolphin import memory`, `event.frameadvance()`, controller/GUI modules — with
  in-process memory access, generic to any GC/Wii game; scripts run via `--script`. This
  collapses input+read+frame-advance into one process, no ptrace/FIFO plumbing. Cost:
  you compile the fork and give up the Flatpak. Mainline PR #7064 has been stalled since
  2022, so it lives only in the fork. Source: <https://github.com/Felk/dolphin>
- **SwareJonge/Dolphin-Lua-Core**: generic `ReadValue*`/`WriteValue*` API but archived
  read-only (Sep 2022) → treat as dead. Source:
  <https://github.com/SwareJonge/Dolphin-Lua-Core/blob/master/Readme.md>
- **project-slippi/Ishiiruka**: state exposure is built around Melee (Slippi), not a
  generic game-state API. Source: <https://github.com/project-slippi/Ishiiruka>

### 5. libmelee — **DEAD-END as-is for RSBE01; its input+external-read *pattern* is reusable**

Architecture: inputs go through Dolphin's **named-pipe controller** (same primitive as
§2); state does **not** come from address reads — it consumes **Slippi-Dolphin's EXI
output**, produced by Melee-specific **Slippi Gecko codes** keyed to GALE01. Its
`GameState`/`Action` model encodes Melee specifics. RSBE01 has no equivalent Slippi EXI
stream, so libmelee's state layer receives nothing — only the input half is
game-neutral. Sources: <https://github.com/altf4/libmelee> ·
<https://libmelee.readthedocs.io/en/latest/>

**Takeaway:** don't adapt libmelee's state layer; reuse only its input idea (already
covered by §2) paired with a §1 address read.

### 6. Flatpak sandbox constraints — **PARTIAL, and already solved on this machine**

Flathub Dolphin finish-args (manifest): `--device=all`, `--filesystem=host:ro`,
`--socket=x11`, `--socket=pulseaudio`, `--share=network`, `--share=ipc`,
`--allow=bluetooth`, plus Discord/gamescope `xdg-run` entries. Source:
<https://github.com/flathub/org.DolphinEmu.dolphin-emu>

Two boundaries:

- **ptrace / `process_vm_readv`.** Flatpak's default seccomp blocks `ptrace()` for the
  *sandboxed app* (`--allow=devel` re-enables it), but that filter governs syscalls the
  *app* makes — it does **not** stop a **host** process from tracing the sandboxed
  Dolphin. Bubblewrap unshares the PID namespace, but the host is the parent namespace
  and still sees Dolphin under a host PID, so a host-side reader with `CAP_SYS_PTRACE`
  (or permissive Yama) can `process_vm_readv` it. Running the reader *inside* the sandbox
  instead would need `flatpak override --allow=devel org.DolphinEmu.dolphin-emu`. Sources:
  <https://docs.flatpak.org/en/latest/sandbox-permissions.html> ·
  <https://docs.flatpak.org/en/latest/flatpak-command-reference.html>
- **FIFO across the boundary.** The app always has read/write to its own
  `~/.var/app/org.DolphinEmu.dolphin-emu/` tree, a real host path writable from the host.
  `mkfifo` there yields one FIFO both sides share — no extra permission for the input half.

**On this machine:** `ptrace_scope=0` means the host-side reader path needs no `setcap`
and no `--allow=devel`; `filesystems=host` covers the FIFO. Both worries are already
resolved by the local config.

## Recommended path (no fork, keeps the Flatpak)

1. **Boot** — `flatpak run org.DolphinEmu.dolphin-emu -b -e "<PM 3.6 / RSBE01 iso>"`
   (add `xvfb-run` only on a display-less box; not needed here). [§3]
2. **Input** — a FIFO under `~/.var/app/org.DolphinEmu.dolphin-emu/…`, bound with
   `Device = Pipe/0/pipe1` in GCPadNew.ini; the agent appends `PRESS/RELEASE/SET` lines
   to trigger the move. [§2, §6]
3. **State** — `dolphin-memory-engine` (PyPI) on the **host**, reading PM-3.6 addresses
   via `process_vm_readv`. On this machine `ptrace_scope=0` means it attaches with no
   privilege change. [§1, §6]

**Fallback:** **Felk's Python-scripting fork** [§4] collapses all three into one
in-process script and removes the ptrace/FIFO plumbing — at the cost of compiling a fork
and dropping the Flatpak. Prefer the host-reader path first (stands up on the existing
Flatpak in an afternoon); keep Felk's fork in reserve if Flatpak ptrace/display friction
proves annoying.

## Follow-up DEV harness — what it would involve

**Where it lives: [`pm36-dolphin-harness`](https://github.com/avidrucker/pm36-dolphin-harness),
not pycats.** That sibling repo already owns this scope (bootstrapped from pycats #1026,
2026-08-04) with its own tracker, a settled two-mode spec, and a verified `dolphin-memory-engine`
attach probe. pycats stays deterministic pure-Python game code; the emulator-attaching,
subprocess-driving driver — and its gitignored copyrighted-RAM artifacts — belong in the harness
repo. So the follow-up DEV ticket below is filed on the **harness** tracker, and pycats research
tickets *cite* its findings. The survey in this doc folds into that repo's spec.

A DEV ticket (only if the campaign wants the automated loop) would deliver a small Python
driver:

- **Deps:** `dolphin-memory-engine` (PyPI); stdlib for the FIFO writer. No compilation on
  the recommended path.
- **Config changes:** one `GCPadNew.ini` `Pipe/0/…` stanza; `mkfifo` in the app data dir.
  No `setcap`, no `--allow=devel`, no sysctl change **on this machine** (all covered by
  `ptrace_scope=0` + `filesystems=host`) — but the harness should *check* those two facts
  at startup and print the one-line fix if a different machine has them locked down.
- **Boot:** `flatpak run … -b -e <iso>`; wrap in `xvfb-run` for a CI/headless box.
- **The gating input it still needs:** the **PM 3.6 address map** for the target values.
  That is not automatable from these tools — it is the datamine/RAM-map work #1250 needs
  regardless of whether a human or an agent drives the GUI. Automation de-manualizes the
  *operation*, not the *address discovery*.

**Provenance note:** a value read this way is citable as a live retail/PM RAM read, which
is exactly the primary #1250 wants (versus the SECONDARY meleelight proxy for
`escapeair_force`). MD5-verify-against-Redump of the ISO stays #638/#215 hygiene, out of
this ticket.

## Evidence caveats

- The official `dolphin-emu.org/docs` command-line page is Cloudflare-gated (403 to
  fetchers); `--batch`/`--exec`/`--user` semantics are sourced from the Dolphin man page
  and the user-directory guide instead.
- The Dolphin wiki Movies/TAS page 404'd at survey time; the recommendation steers to
  pipe input (fully primary-sourced), so nothing here rests on the DTM claim.

## Refs

#638 (epic — the live-read capability this automates) · #1250 (the manual RAM-read this
de-manualizes) · #639/#640 (Dolphin + codeset env, done) ·
[`pm36-dolphin-harness`](https://github.com/avidrucker/pm36-dolphin-harness) (the sibling repo
that owns the follow-up DEV driver; this survey folds into its spec) ·
`docs/pm-reference/pm-globals-dump-setup.md` · memory `rukaidata-engine-hardcoded-limit`
(why the values need a live read at all).
