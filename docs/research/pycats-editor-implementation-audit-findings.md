# pycats-editor implementation audit — planned E6/E7/E8 vs shipped

**Ticket:** #1121 (RESEARCH, child of #792) · **Agent:** ELDERBERRY · **Date:** 2026-08-02
**Repo audited (read-only):** `avidrucker/pycats-editor` (private) — `src/pycats_editor/`, `tests/`
**Basis:** the slice plan in `docs/pycats-editor-scope.md` (from SCOPE #826), design #809.

Findings only — **no code change, no decision, no new slice filed.** Any follow-up DEV is
downstream, filed one-at-a-time after a human reads this.

---

## TL;DR

- **Planned E7 (GIF compare)** — the capability that motivated the whole editor — is
  **fully SHIPPED** (all five sub-capabilities), plus extras (auto-map, combo cycling,
  GIF-view undo). It just lives on-disk under the **E9** slice file, not E7.
- **Planned E6 (open / restore per-frame state)** is **PARTIAL**: the reverse-collapse
  restore works, but there is **no open-a-file path** and **no `provenance.frames`-preferred
  restore** — the editor only re-reads the canonical committed `<character>.json` through
  pycats.
- **Planned E8 (chrome)** is **PARTIAL**: the duration read-out is shipped and on-screen
  action buttons exist, but **play/pause auto-advance is entirely MISSING**, layer/mode
  toggles are keyboard-only, and file handling is an in-app modal prompt (no OS dialog, no
  Open prompt).
- **The on-disk `test_eN` numbering is a sequential build log, not the plan's capability
  labels** — E6/E7/E8 on disk are labels/display-polish/selection, unrelated to the plan's
  open-restore/gif-compare/chrome. Reconciliation table in §4.

Whether these E6/E8 gaps block "V1 done" (and therefore #918's post-V1 gate) is a **human
call** — this doc surfaces the gaps, §5, it does not rule on them.

---

## 1. Planned E6 — open / restore per-frame state — **PARTIAL**

Planned (scope doc §E6): read a saved `<character>.json` back in; prefer a `provenance.frames`
trace to restore exact per-frame state, else reverse-collapse canonical windows.

| Sub-capability | Verdict | Evidence (symbol · module) | Covering test |
|---|---|---|---|
| Open a saved `<character>.json` back into working state | **PARTIAL** | `main()` → `load_fighter_data(character)` → `working.working_move_from_fighter(...)` (`__main__.py`); same builder on move/char switch via nested `_reload`. Reads only the **canonical committed** file through pycats; **no** open-arbitrary-file / open-dialog path, and it does **not** read the editor-written `provenance` block. | `test_e0_boot.py` (data-path coupling); load-into-working exercised throughout `test_e4_per_frame.py` |
| Reverse-collapse fallback (replicate each box across its active window) | **SHIPPED** | `working.working_move_from_fighter` + `_box_window` (`working.py`) — replicates each frozen hitbox across its window as one `FrameBox`/frame under a stable `id` (docstring cites design §2.4) | `test_e4_per_frame.py::test_seed_replicates_each_hit_box_across_its_window`, `::test_seed_frame_rows_are_identical_across_the_window`, `::test_seed_mirrors_the_loaded_hitbox_values` |
| Prefer a `provenance.frames` trace on restore | **MISSING** | No reader for `doc["provenance"][move]["frames"]`. Grep finds only the **writer** (`save.provenance_frames` / `save.save_document`) and `doc_diff` which **strips** provenance. No reader exists anywhere in `src/`. | **None found** (looked in `test_e4_per_frame.py`, `test_save_e5.py`, `test_1056_load_report.py`; grepped all of `src/` + `tests/`) |
| Open→edit-nothing→save is byte-stable (no-op round-trip) | **PARTIAL** | The fighter body serializes byte-identically for an untouched move (`save.updated_fighter` / `fighter_to_json`). But Save always **enriches** the doc with a `provenance` block + per-hitbox labels the lean on-disk file lacks (`save.save_document`), so an unedited Save is **not** doc-identical to disk — the #1022 finding. Only the **semantic** no-op (provenance-excluded `doc_diff.diff_saves`) is pinned. | `test_save_e5.py::test_untouched_move_serializes_byte_identical`; semantic no-op: `test_989_save_diff.py::test_save_without_an_edit_prints_no_diff`, `test_1022_no_change_prompt.py::test_unedited_save_prints_no_changes_detected`, `test_save_prompt_983.py::test_doc_matches_disk_true_when_equal` |

**Read:** the *restore-a-move-into-per-frame-rows* mechanic (reverse-collapse) is done and
well-tested — that was the hard part and it shipped inside on-disk slice E4 (#913). What's
absent is the **"open a file the user chooses"** surface and the **provenance-preferred**
high-fidelity restore that would make open→save a true byte-level no-op. In practice the
editor opens exactly one thing: the committed character it was launched with.

---

## 2. Planned E7 — GIF compare — **SHIPPED (all five)**

Planned (scope doc §E7): Pillow-decode the reference Mario GIF; toggle hit/hurt/GIF layers
independently; draw fighter OVER the GIF (trace) or BESIDE it (compare); scale + translate
the GIF view-only (never saved); a duration read-out (fighter total-frames vs GIF frames).

Implemented as a clean pure-seam module `src/pycats_editor/gifcompare.py` (its own docstring
self-labels it "scope slice **E7**", ticket #976) and wired into `main()`.

| Sub-capability | Verdict | Evidence (symbol · `gifcompare.py`) | Covering test (`test_e9_gifcompare.py`) |
|---|---|---|---|
| Pillow-decode reference GIF | **SHIPPED** | `decode_gif` / `gif_frame_count` (`from PIL import Image`); wired via `_resolve_gif_frames` in `__main__.py` | `::test_decode_gif_returns_one_surface_per_frame`, `::test_gif_frame_count_reads_the_frame_count` |
| Toggle hit/hurt/GIF layers independently | **SHIPPED** | `Layers` + `toggle_layer` + `filtered_scene`; keys 1/2/3 wired in `main()` | `::test_toggle_layer_flips_exactly_one_flag`, `::test_filtered_scene_hides_only_the_toggled_layer`, `::test_gif_layer_key_is_wired` |
| Draw fighter OVER (trace) or BESIDE (compare) | **SHIPPED** | `OVERLAY`/`SIDE_BY_SIDE`, `toggle_mode`, `gif_dest`; key M wired | `::test_gif_dest_overlay_is_origin_plus_offset`, `::test_gif_dest_side_by_side_anchors_to_the_right_margin`, `::test_mode_key_is_wired` |
| Scale + translate GIF, view-only (never saved) | **SHIPPED** | `GifView`, `zoom_view`, `pan_view`, `cycle_preset_x`, `scaled_frame`, `resize_view_to_cursor`; PgUp/PgDn / Shift-arrows / P / mouse-drag wired; never an input to Save | `::test_gif_view_transform_never_changes_saved_bytes` (the never-saved guarantee) + zoom/pan/resize/drag tests |
| Duration read-out (move frames vs GIF frames) | **SHIPPED** | `duration_readout`; drawn on-screen in `main()` | `::test_duration_readout_names_move_and_gif_frames_and_positive_delta`, `::test_duration_readout_negative_delta` (pure-fn; no test asserts it is *drawn*) |

**Beyond the planned five:** per-character move→subaction GIF **auto-map** (`gif_map.py`,
`test_e10_gif_map.py`, #986); combo sub-animation cycling (`test_984_combo_display.py`, #984);
GIF-view **undo** history (`test_1054_gif_history.py`, #1054).

**Read:** E7 is complete and then some. The one thin spot is coverage-shape, not capability:
the duration/view read-outs have pure-function tests but nothing asserts they're actually
blitted in `main()` (same gap noted for E8's readout below).

---

## 3. Planned E8 — chrome — **PARTIAL**

Planned (scope doc §E8): play/pause loop; on-screen toggle controls; file dialogs; a duration
read-out surface.

| Sub-capability | Verdict | Evidence | Covering test |
|---|---|---|---|
| Play/pause animation loop | **MISSING** | No auto-advance anywhere. `current_frame` changes only via ←/→ keys and timeline click/drag in `main()`. `clock.tick(60)` is an FPS cap, not a playhead. Grep for play/pause/autoplay/loop finds only `timeline.PLAYHEAD_COLOR` + doc comments. | **None found** (looked in `test_e2_timeline.py`, `test_e7_display_polish.py`; grepped src) |
| On-screen toggle controls | **PARTIAL** | An on-screen clickable-button registry exists — `buttons.Button` / `button_at` (`buttons.py`) — with three **action** buttons RESET / RELETTER / ADD_BOX, drawn by `_draw_buttons` and click-dispatched in `main()`. But the layer/mode **toggles** (hit/hurt/gif/mode/preset) are **keyboard-only** (1/2/3/M/P), not on-screen. | Action buttons: `test_1032_reset.py`, `test_1031_add_box_button_wiring.py`, `test_1035_reletter_wiring.py`. No on-screen toggle-button test |
| File dialogs (open / save destination) | **PARTIAL** | Save-destination is an **in-app modal keyboard prompt** (O/S/B/N) — `_save_prompt_title` / `_draw_save_prompt`, backed by `save.resolve_save_path` / `next_scratch_path` / `write_document` / `doc_matches_disk`. **No OS file dialog** (no `tkinter`/`filedialog` anywhere) and **no Open prompt at all** — open is fixed to the launched character file. | `test_save_prompt_983.py` (all fns), `test_1022_no_change_prompt.py`, `test_989_save_diff.py` |
| Duration read-out surface | **SHIPPED** | On-screen readout column in `main()`: char/move (`navigation.readout`), used-letters (`working.used_letter_readout`), GIF duration (`gifcompare.duration_readout`), GIF `view_readout` | Used-letter readout drawn-in-loop: `test_1034_used_letter_indicator.py::test_render_loop_calls_the_readout`. Duration/view: pure-fn only |

**Read:** E8 never landed as a coherent "chrome" slice. Its pieces arrived ad-hoc: the
read-out surface is done; on-screen buttons exist but only for actions, not toggles; saving
is a keyboard modal rather than a dialog and there's no Open counterpart; **play/pause is the
one wholesale-missing capability across all of E6/E7/E8.**

---

## 4. On-disk `test_eN` numbering vs planned slices (reconciliation)

The on-disk `test_eN` files are a **sequential build log** (E0 boot → E10 gif-map). They do
**not** align with the plan's capability labels. Actual coverage per file:

| On-disk file | Ticket | Actually covers | Plan label it maps to |
|---|---|---|---|
| `test_e0_boot.py` | #882 | Boot: pycats data-path coupling + pygame-ce boot | E0 |
| `test_e1_canvas.py` | #891 | Canvas draws fighter + hit/hurt circles for one frame | E1 |
| `test_e2_timeline.py` | #901 | Frame timeline + scrub drives the box set | E2 |
| `test_e3_inspector.py` | #909 | Inspector: select a box, edit geometry/scalars + timing | E3 |
| `test_e4_per_frame.py` | #913 | Per-frame authoring + stable `id`; **reverse-collapse seed** | E4 **+ the only realized piece of planned E6** |
| `test_save_e5.py` | #924 | Save: collapse per-frame trace → windows, write JSON + provenance | E5 |
| `test_e6_labels.py` | #964 | Per-box letter + 0-indexed frame-ordinal **label overlay** | **not** planned-E6 (open-restore) |
| `test_e7_display_polish.py` | #965 | **Display polish**: phase colours, 0-indexed cells, note word-wrap | **not** planned-E7 (gif-compare) |
| `test_e8_selection.py` | #972 | Keyboard-cycle **pickers** for character/move | **not** planned-E8 (chrome) |
| `test_e9_gifcompare.py` | #976 | **GIF compare** (self-labeled "scope slice E7") | **= planned E7** |
| `test_e10_gif_map.py` | #986 | Per-character move→subaction GIF **auto-map** | extension of planned E7 |

**Punchline:** planned **E7 (gif-compare)** shipped, but under on-disk file **E9**. Planned
**E6 (open-restore)** has **no dedicated slice** — only its reverse-collapse piece shipped,
inside on-disk **E4**. Planned **E8 (chrome)** has **no dedicated slice** — its pieces are
scattered across #1031/#1032/#1035 (buttons) and #983 (save prompt), and on-disk `test_e8`
is an unrelated capability (selection pickers).

---

## 5. Gap list — what is still missing for a "V1-done" editor

Surfaced, not ruled. Each is a candidate downstream DEV slice (file one-at-a-time, human-gated):

1. **Play/pause animation loop** (planned E8) — wholesale missing. No auto-advance playhead;
   frames only step by ←/→ or timeline click. *Biggest single gap.*
2. **Open-a-file surface** (planned E6) — the editor can only open the character it was
   launched with; there is no "open a different/arbitrary character file" path or prompt.
3. **`provenance.frames`-preferred restore** (planned E6) — a writer exists, no reader; a
   saved provenance trace is never read back, so open→save is only a *semantic* no-op, not a
   byte-level one (interacts with #1022, and is the exact fidelity #918 would want when it
   extends the save-collapse to hurt).
4. **On-screen toggle controls** (planned E8) — layer/mode toggles are keyboard-only; only
   action buttons (reset/reletter/add-box) are on-screen. (Arguably cosmetic — E8 chrome was
   always "pygame_gui *or* hand-rolled, decide at slice time".)
5. **Coverage-shape nit (not a capability gap):** the duration/GIF-view read-outs have
   pure-function tests but nothing asserts they are actually blitted in `main()`
   (the used-letter readout is the only readout with a drawn-in-loop test).

**Not gaps** (shipped): the entire GIF-compare feature set (planned E7), per-frame authoring
+ reverse-collapse restore, save-collapse-to-windows, the duration read-out surface,
undo/redo, help modal, on-screen action buttons.

**Bearing on #918 (post-V1, per-frame hurt authoring):** #918's own dependencies (E4 #913,
E5 #924) are closed, and the save-collapse path it extends is shipped. The open question its
"post-V1" gate raises is whether gaps 1–2 above must close first — **a human call**, not
settled here.

---

## 6. Refs

- **Plan / design:** `docs/pycats-editor-scope.md` (E6/E7/E8 defs) · #826 (SCOPE) · #809 (design) · #792 (tracker).
- **Ad-hoc editor tickets reconciled here:** #964 (labels) · #965 (display polish) · #972 (selection) · #976 (gif-compare / planned E7) · #986 (gif auto-map) · #983 (save prompt) · #984 (combo cycle) · #1022 (no-change prompt) · #1031/#1032/#1034/#1035 (buttons/reset/readout/reletter) · #1054 (gif-view undo) · #1007 (help modal).
- **Editor repo:** `avidrucker/pycats-editor` — `src/pycats_editor/{__main__,working,save,gifcompare,gif_map,buttons,doc_diff}.py`, `tests/`.
- **Sibling research:** #1122 (BDD-options survey for the editor).
