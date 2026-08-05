# WYSIWYG hit/hurtbox + animation editor — approaches, serialization seam, prior art, compare needs

**Ticket:** #793 (RESEARCH · `area:combat` · **child of #792**). **Produces:** this findings doc.
**Explicitly no decision** — this maps the option space and constraints so the next
(human-gated) **decision** child can choose. Design/DEV children follow one-at-a-time downstream.

**Grounding note.** In-repo claims are cited to file + symbol (verified for this ticket).
External prior-art / toolkit claims cite the tool's own docs/repo where possible; community
write-ups (forums/wikis) and anything read via mirror are flagged as such.

---

## TL;DR

- **pycats already has the "visualize half."** `render_hitbox_overlay()` (+ `resolve_circle` +
  `_active_hurtbox`) already draws the real hit/hurt circles over the live fighter, gated by a
  persisted toggle. An in-game editor inherits rendering, frame-stepping, and box-drawing for free.
- **The real work is the *write* half.** Box data is **hand-written frozen-dataclass Python
  literals** loaded by an import switch — **there is no serializer, no data-file format, no write
  path anywhere in the repo.** The editor must author the first one.
- **The determinism boundary is firm and already established (#768).** A box's `dx/dy/r` feed
  `resolve_circle` → hit resolution → the `snapshot()` golden bytes, so edits are **sim-affecting**.
  The only safe pattern is **edit → serialize → reload → replay** (a new frozen `FighterData` per
  match); live-mutating a running match is both structurally forbidden (frozen dataclasses) and a
  determinism/golden violation.
- **Option space:** **(A)** in-game dev-mode overlay, **(B)** standalone side-program, **(C)** adapt
  an existing tool. C is weak (no mature pygame hitbox editor exists; rukaidata is read-only; the
  only rich analog is the wrong stack). A and B are the real candidates; the pivotal *sub*-decision
  underneath both is **whether to extract box geometry out of Python literals into a JSON/TOML data
  file** — it de-risks A's ugly write-back and is effectively required for B.
- **Prior art gives a ready-made UX template** (rukaidata's viewer + Aseprite's per-frame keyed
  slices + the engine collider drag-handles + PM/Melee's color-by-type + swept overlay). The
  differentiator no existing tool offers: **visual drag-placement AND per-frame authoring in one**
  (BrawlBox edits blind-numeric; rukaidata visualizes read-only).

---

## 1. What pycats already has (the head start)

| Asset | Where | Editor reuse |
|---|---|---|
| **Box visualizer** — outline circles, red hitboxes / cyan hurtboxes | `render_hitbox_overlay(surface, players, attacks)` in `pycats/render_battle.py` | The WYSIWYG box layer already exists; the editor re-renders exactly this. |
| **Box→screen resolver** | `resolve_circle(circle, origin_x, origin_y, facing_right, width)` in `pycats/combat/geometry.py` | px ↔ `Circle(dx,dy,r)` mapping (incl. facing mirror) is already written. |
| **Active-hurtbox selector** (stand/crouch/prone) | `_active_hurtbox(p)` in `render_battle.py` | Editor knows which hurtbox is live per state. |
| **Toggle plumbing** | `runtime_settings.show_hitbox_overlay()` / `options_menu.py` / `settings.py` | Pattern for a dev-mode flag; a second `show_dev_info()` HUD flag exists too. |
| **Screen/mode FSM** | `ScreenStateManager` (`pycats/screen_manager.py`) + `make_screen_engine` (`pycats/systems/screen_engine.py`) + `BattleScreen` (`pycats/battle_screen.py`) | Where a new editor/sandbox state hooks in. #691 (in-game CPU mode) is the sibling "add a new selectable mode" precedent. |
| **Fighter render** | `render_battle(...)` in `render_battle.py` | The fighter sprite the boxes overlay; frame-stepping already drives it. |
| **#777 Mario reference** | committed manifest `docs/pm-reference/mario-gif-index.md`; GIFs in gitignored `repros/mario-gifs/` | Drive an action picker from the manifest without shipping frames; GIFs are the visual reference. |
| **#778 sandbox (OPEN, unstarted)** | issue #778 | Shares the exact new-screen-state wiring **and** the #777 manifest — an editor and #778 overlap heavily. |

**What does NOT exist yet:** no free camera, no dedicated dev/editor mode, no hitbox F-key toggle
(only `K_F11`/`K_F10` in `app.py`), and — the big one — **no write path for box data** (§2).

---

## 2. The serialization seam (the real work)

### 2.1 — Data is Python literals with no emitter

`load_fighter_data(character)` (`pycats/combat/data.py`) is a **pure import switch** —
`if character == "nalio": from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA`. Fighter
definitions are module-level `*_FIGHTER_DATA = FighterData(...)` built from `Circle(...)` /
`Hitbox(...)` / `MoveData(...)` **literals** with dense inline provenance comments (datamine tables,
`⚠ playtest starting point` markers). The data.py docstring's "Phase 1+ will branch per character to
TOML/JSON files" **never happened** — it is all Python. The only JSON in `pycats/` is unrelated
runtime config (`settings.json`, `profiles/*.json`, `characters/palettes.json` = color skins, no
boxes).

**There is no serializer / codegen / emitter** — a grep for `asdict|to_dict|serialize|dump|emit|
write.*fighter` across `pycats/combat` + `pycats/characters` returns empty. Data flows **one way**:
literal → frozen dataclass → consumers. **The editor introduces the first write path for box data
that exists in the repo.**

### 2.2 — The determinism / golden boundary (#768)

The chain: `Circle.dx/dy/r` (int) → `geometry.resolve_circle(...)` → overlap tests in
`combat.process_hits` (decide hits) **and** the resolved circle becomes `a.hit_cx/hit_cy/hit_r` in
`pycats/sim/runner.py` `snapshot()`, which **is** the golden digest. So **any change to a hitbox
`dx/dy/r` changes hit resolution and the golden bytes** — exactly the #768 rule (issue **#768 is
open**; body: "moving the hurtbox must live in the deterministic sim … the sim digest now
includes the offset, so `sim/runner` snapshots shift … must stay deterministic — frame-counter
driven, no wall-clock / no RNG").

- **UNSAFE — live-mutate a running match:** frozen dataclasses forbid it structurally (can't
  reassign `circle.dx`); even swapping whole objects mid-match diverges from goldens and, if driven
  by mouse/wall-clock, breaks determinism/replay.
- **SAFE — edit-then-reload:** edit out-of-match, serialize, then `load_fighter_data` yields a **new**
  frozen `FighterData` for the next match/replay. Determinism holds (sim still reads static frozen
  data per match); only that fighter's goldens need the reviewed regen. Note the sim/golden path
  loads `"P1"/"P2"` → `default_cat`, so editing `nalio`/`birky`/`narz` doesn't touch default-cat
  goldens at all.

### 2.3 — Two emitter shapes (the pivotal sub-decision)

1. **Regenerate Python source** (AST/region rewrite of `*_cat.py`). Keeps the current data location,
   but is **fragile**: the files carry dense provenance comments that a naive re-emit destroys, so it
   needs surgical region editing, not a full rewrite.
2. **Extract box geometry into a data file** (the abandoned "Phase 1" plan) — per-fighter **JSON**
   (stdlib `json`, no new dep, diff-friendly, already used for settings/palettes) or **TOML** (nicer
   for hand-annotated values, but `tomllib` is **read-only**; *writing* TOML needs a gated dep like
   `tomli-w`/`tomlkit`). Add a parser to `load_fighter_data`, and emit that.

**This extraction question is the hinge of the whole feature:** it cleanly enables a decoupled
side-program (B *needs* a neutral interchange file) **and** removes A's ugliest part (writing Python
source back out). It is the first thing the decision child should settle. *(Not decided here.)*

### 2.4 — Dependency flags (pycats gates every new dep)

- **No new dep:** stdlib **JSON** interchange; **raw-pygame** in-game editor (A); **tkinter**
  side-program (B).
- **New dep, tool-only (never enters the game binary):** Dear PyGui / PySide6 / Pillow — in a
  side-program (B) these live in the editor's own env, a real advantage under pycats' policy.
- **New dep entering the game binary (gated):** `pygame_gui` / `thorpy` / Pillow, if A adopts them.
- **Correction to a common assumption:** **Pillow is NOT a declared pycats dependency** (runtime =
  `pygame-ce` + `statecharts`; dev adds `imageio` + `imageio-ffmpeg`, `pytest`, `ruff`). GIF frame
  decode should use the existing **`imageio`** (dev dep) rather than assume Pillow; relying on Pillow
  in shipped code is a gated add. *(Pillow happens to be importable in the local `.venv` as a
  transitive package, but it is undeclared — not something to depend on without declaring it.)*

---

## 3. The A / B / C option space (tradeoffs — no pick)

| | **A — in-game dev-mode overlay** | **B — standalone side-program** | **C — adapt existing tool** |
|---|---|---|---|
| **Render** | Reuses `render_battle` + `render_hitbox_overlay` + frame-stepping — **no second renderer** | **Re-implements** the fighter render in a second framework | n/a — no adaptable tool renders a pycats fighter |
| **Data read** | Imports character modules directly | Needs a neutral interchange file (→ §2.3 extraction) | n/a |
| **Data write** | Python-source codegen (fragile) **unless** boxes extracted to a file | Reads/writes the interchange file (clean) | n/a |
| **New game deps** | Zero (raw pygame) or gated (`pygame_gui`) | **None enter the game binary** (tool-only deps) | n/a |
| **UI toolkit** | raw pygame (hand-roll widgets) or `pygame_gui` (MIT, maintained, has slider/text-entry/file-dialog) | tkinter (stdlib) / Dear PyGui (MIT, GPU canvas) / PySide6 (LGPL, `QGraphicsView` movable items) | n/a |
| **Shares #778 wiring** | **Yes** — same new-screen-state plumbing + #777 manifest | Partly (consumes #777 manifest; separate app) | No |
| **Effort (first usable)** | **Low–Med** (raw pygame) / Med (`pygame_gui`) | Med (tkinter / Dear PyGui) / Med–High (PySide6) | High-and-wrong-stack / n/a |
| **Downsides** | Editor code ships in game binary (gate behind dev flag / lazy import); adds a mode to the statechart FSM; codegen write-back is the weak spot | Second renderer to build + maintain; cross-process data marshaling; diverges from the live game view | See below |

**On C specifically:** there is **no mature dedicated pygame/Python WYSIWYG hitbox editor** to fork
(the search surfaces only hand-coded-rect tutorials — a genuine gap). The closest rich analogs are
**rukaidata** (read-only viewer, Rust+wgpu→wasm — wrong stack to embed, and it visualizes but can't
author) and **BrawlBox/BrawlCrate** (edits hitboxes as **blind numeric fields**, no overlay on its
3-D preview, and operates on `.pac` not pycats data). So "adapt existing" collapses to "port ideas,"
which is really options A/B informed by §4 — **C is not a standalone path.**

**Toolkit notes for the decision child** (sources in §7): `pygame_gui` v0.6.14 (MIT, maintained, has
`UIHorizontalSlider`/`UITextEntryLine`/`UIFileDialog`) is the in-engine upgrade over raw pygame;
**tkinter** is the zero-dependency side-program answer (Canvas `create_oval` + drag is a standard
pattern, native file dialogs, stdlib) with GIF being its only gap (needs a decoder); **Dear PyGui**
(MIT, GPU drawlist + widgets in one wheel) is the nicest canvas; **PySide6** (LGPL) `QGraphicsView`
gives movable items/selection/`QMovie` GIF essentially free but the highest ramp. **Prefer PySide6
over PyQt6** (GPL) on licensing.

---

## 4. Prior-art UX patterns that transfer

The strongest template is **rukaidata's move viewer** (the closest analog to the goal), rounded out
by **Aseprite slices** (per-frame keyed regions), the **engine collider editors** (drag-handles), and
**PM/Melee debug mode** (color + swept overlay).

| Pattern | Why adopt | Source | Type |
|---|---|---|---|
| Numbered per-frame scrubber + Play + Prev/Next step | core navigation loop | rukaidata (observed) | live tool |
| Frame-halt + single-step advance | inspect one frame's boxes | PM/Melee debug | community wiki |
| Bubble-type filter checkboxes (Hit/Grab/Hurt/Invuln) | declutter, isolate a class | rukaidata (observed) | live tool |
| **Color-by-type legend** (red hit, yellow hurt, magenta grab, green/blue invuln) | de-facto Smash standard → instantly legible (pycats already uses red hit / cyan hurt) | PM/Melee debug | wiki + community |
| **"Current + prior frame" swept overlay** | shows true active area + travel (ties to the #782 sweep gap) | rukaidata **and** PM debug | official + community |
| Data table locked beside the visual, keyed to current frame | numbers + picture in one glance | rukaidata (observed) | live tool |
| **Facing-flip (Left/Right) toggle** | 2-D data mirrors by facing | rukaidata (observed) | live tool |
| **Drag-handle resize on primitive shapes** (circle radius / center) | the core WYSIWYG gesture | Unity / Godot collider editors | official docs |
| Explicit **Edit-mode toggle** | separates "move object" from "edit shape" | Unity | official docs |
| Double-click → numeric Bounds/Pivot dialog | exact values behind the handle | Aseprite slices | official docs |
| **Per-frame KEYED boxes with interpolation between keys** | a box persists but moves/resizes per frame — matches hitbox lifetimes (see §6) | Aseprite slice `keys[]` | official docs |
| Bone/anchor-relative offset + numeric fields | box follows a body part, edited by drag AND number | BrawlBox/PSA event; rukaidata bone+offset | community + official |
| Copy-box-across-frames / event-list keyframing | author "active frames 4–8" once | BrawlBox subaction events; Aseprite keys | community + official |
| **Length-proportional phase strips** (startup/active/recovery) + fixed-column numeric table | visual duration diff + exact frames | Dustloop / FAT frame-data tools | community |
| Non-uniform-scale warning (scale the shape's extents, not the node) | avoids distorted boxes | Unity/Godot | official docs |

**The differentiator (a real gap):** BrawlBox edits hitboxes **blind** (numeric offsets, no overlay);
rukaidata **visualizes but is read-only**. No tool combines **visual drag-placement + per-frame
authoring**. And no standard tool shows **two 2-D animations synchronized side-by-side with a
frame/duration diff** — which is precisely the #792 goal (§5).

---

## 5. Compare-workflow requirements (every Nalio move vs its Mario animation)

The #792 goal is to verify each Nalio move has roughly the **same duration** and **same box
placement** as its Mario reference. Concretely that needs:

1. **A synchronized scrubber driving two panes** — Nalio (live) on one side, the Mario reference on
   the other, both stepping to the same frame index. (No existing tool does this for 2-D — it's the
   novel piece.)
2. **Duration diff** — render each move's phases (startup / active / recovery) as **length-
   proportional strips** so total length and active-window overlap diff by eye; exact frames in a
   table beneath. pycats already stores `startup/active/recovery` per `MoveData`.
3. **#777 reference display** — decode the Mario GIF's frames (via existing **`imageio`**) to
   per-frame surfaces indexed by the scrubber, **scaled to a common body height** (the reference is a
   hurtbox-capsule/skeleton render, not skin — so compare *motion + box*, not appearance). Drive the
   action picker from the committed `mario-gif-index.md` manifest (subaction → GIF → frame count).
4. **Body-relative circle placement** — place/drag circles in `Circle(dx,dy,r)` coords via the
   existing `resolve_circle` mapping; anchor `dy` with `zone_dy` fractions (#309) so placement is
   body-height-relative; support the facing mirror.

This overlaps #778 (the side-by-side sandbox) so heavily that the decision child should explicitly
consider **whether the editor and #778 are one feature or two** (the editor = #778's compare view +
a drag-to-edit-and-save layer).

---

## 6. A data-model question the editor surfaces (flag for decision/design)

pycats' `Circle` today is **static per move** — one `dx/dy/r` for the box across its whole active
window. PM boxes **move every frame** (bone-driven; the #782 finding). A WYSIWYG editor that authors
boxes *per frame* (the Aseprite-`keys[]` pattern) implies a **richer data model than pycats has
today** (keyed positions + interpolation — the swept-capsule gap #782 flagged). The alternative is an
editor that authors only the current static-per-move circles (simpler, matches today's model, but
can't express per-frame motion). **Which target the editor aims at is a design fork**, tied to the
#782 interpolation gap — surfaced here, decided downstream.

---

## Open questions for the (human-gated) decision child

1. **A vs B** — in-game overlay (reuses everything, shares #778 wiring, code in game binary) vs
   standalone (decoupled, tool-only deps, second renderer).
2. **Extract box geometry to a JSON/TOML data file, or keep Python literals + codegen?** (§2.3 — the
   hinge; enables B, de-risks A.)
3. **UI toolkit** — raw pygame / `pygame_gui` (A); tkinter / Dear PyGui / PySide6 (B).
4. **GIF decode** — existing `imageio` (dev dep) vs gated Pillow.
5. **Static-per-move vs per-frame keyed boxes** (§6) — how faithful to PM's per-frame motion.
6. **Editor vs #778** — one feature or two (§5).

## 7. Sources

**In-repo (verified):** `pycats/combat/data.py` (`load_fighter_data` import switch; the frozen
schema), `pycats/combat/geometry.py` (`resolve_circle`), `pycats/render_battle.py`
(`render_hitbox_overlay`, `_active_hurtbox`, `render_battle`), `pycats/sim/runner.py` (`snapshot()`),
`pycats/runtime_settings.py` / `options_menu.py` / `settings.py` (toggle plumbing),
`pycats/screen_manager.py` / `pycats/systems/screen_engine.py` / `pycats/battle_screen.py` (screen
FSM), `pycats/characters/{nalio,default,birky,narz}_cat.py` (literal data), `docs/pm-reference/mario-gif-index.md`
(#777 manifest), `requirements.txt` / `requirements-dev.txt` (deps). Tickets: #768 (open, sim-affecting
rule), #778 (open, side-by-side sandbox), #691 (new-mode precedent), #309 (`zone_dy`), #782
(hit/hurtbox model + interpolation gap).

**External — official docs/repos:** rukaidata writeup <https://github.com/rukai/rukaidata/blob/main/docs/writeup.md>
+ live viewer <https://rukaidata.com/Brawl/Pit/subactions/ThrowF.html> (direct observation of its
control set); BrawlCrate <https://github.com/soopercool101/BrawlCrate>; Unity 2D collider
<https://docs.unity3d.com/Manual/2d-physics/collider/edit-collider-geometry.html>; Godot CollisionShape2D
<https://docs.godotengine.org/en/stable/tutorials/physics/collision_shapes_2d.html>; Aseprite slices
<https://www.aseprite.org/docs/slices/>. Toolkits: pygame_gui <https://pypi.org/project/pygame-gui/>
(MIT), Dear PyGui <https://pypi.org/project/dearpygui/> (MIT), PySide6 <https://pypi.org/project/PySide6/>
(LGPL), PyQt6 <https://pypi.org/project/PyQt6/> (GPL), thorpy <https://pypi.org/project/thorpy/> (MIT).

**External — community / mirror (flagged, not official):** PM v3.5 debug-mode blogpost (body 403,
read via index) <https://smashboards.com/threads/project-m-v3-5-blogpost-4-debug-mode-revealed.364223/>;
SmashWiki Hitbox <https://www.ssbwiki.com/Hitbox>; OpenSA Subactions
<http://opensa.dantarion.com/wiki/Subactions_(Brawl)>; Dustloop frame-data
<https://www.dustloop.com/w/Using_Frame_Data>; FAT (Frame Assistant Tool) store listing. The BrawlBox
"no hitbox overlay in preview" point is community consensus (its wiki/mirror were unreachable).
