# pycats-editor → ReactJS web app — rewrite findings (#1235)

**Date:** 2026-08-07 · **Ticket:** #1235 (`RESEARCH: convert pycats-editor to a ReactJS web app`) · **Agent:** banana
**Refs:** #792 (editor tracker) · #1191 (box-authoring epic) · #1197 (harness/replay) · #1206/#1220 (datamine ghost-assist) · ADR-0008 (WYSIWYG editor) · #913 (E4 frame-major model) · #924 (E5 save/collapse) · repo `avidrucker/pycats-editor`.

**Status:** findings only. This doc scopes and answers the question; it does **not** decide the rewrite or pick a stack. The decision is a downstream ARC/decision ticket with a human. Ends with a recommendation + option space to rule on.

Grounded in a read of both repos: the editor (`pycats-editor/src/pycats_editor/`, 5,097 LOC / 20 modules) and the shared combat contract (`pycats/combat/geometry.py`, `collapse.py`, `data.py`, 1,314 LOC) plus the drift-guard tests.

---

## 0. The one finding that dominates everything

The editor's whole value is that it emits `<character>.json` the live sim loads **unchanged**, with geometry and hit-tests **byte-identical** to the game. It gets that for free today because it is one Python codebase: it `import`s `pycats.combat.geometry.resolve_circle` (render + hit-test ground truth), `pycats.combat.collapse.collapse` (the save fold), and `pycats.combat.data` (the `Circle`/`Hitbox`/`FighterData` types + JSON (de)serializer).

**A JS/React app cannot `import pycats.combat`.** So every question below — effort, rendering, testing, distribution, coexistence — is downstream of one choice: **how does the web app honor the same geometry/collapse/serialize contract across the Python↔JS boundary?** That choice (§3) is the effort multiplier; the rest is comparatively mechanical.

---

## 1. Pros / cons / tradeoffs — desktop pygame vs React web

| Dimension | Desktop `pygame-ce` (today) | React web app | Net |
|---|---|---|---|
| **Distribution / install** | `pip install -e` pycats + editor, needs a Python env; `python -m pycats_editor`. | Open a URL (if static) or serve a page. No Python on the user's box. | **Web wins** — but the authoring audience is tiny (§6), so the win is modest. |
| **Cross-platform reach** | Wherever Python+SDL run (Linux/mac/Win desktop). | Any modern browser, incl. tablets. | Web wins on breadth; desktop already covers the maintainers. |
| **Rendering** | Immediate-mode: redraw the whole 640×360 base every frame, blit circles. Simple, but no retained scene / no per-element events. | Retained DOM/SVG *or* canvas 2D *or* WebGL (§5). Retained model gives free per-element hit-testing + accessibility. | Web is a better fit for an interactive editor; pygame's redraw-everything loop is the thing being replaced. |
| **Input / interaction** | Hand-rolled mouse/keyboard dispatch in a 1,850-LOC `__main__.py` loop. | Browser events + React state; drag/select/handles become DOM/SVG events. | Web wins on ergonomics; the dispatch code is discarded either way. |
| **Dev velocity** | Small dep surface, direct debugging, but every widget is hand-drawn. | Rich component/UI ecosystem, hot reload, devtools — but a build toolchain + a large initial rewrite. | Web wins *after* the port; the port itself is the cost. |
| **Testing** | Headless SDL (`SDL_VIDEODRIVER=dummy`), deterministic `run_frames`/`on_frame` seam, `Scenario` BDD harness, semantic `targets` registry. 62 files / ~7,938 LOC. | Playwright (already available) + React Testing Library; `targets` maps ~1:1 onto `getByRole`/`data-testid`. | Roughly a wash on capability; the pycats round-trip tests are the hard port (§7). |
| **Shared-Python coupling** | **Free and exact** — one codebase, `resolve_circle`/`collapse`/serializer are the same objects the sim uses. Drift is impossible by construction. | **Not free** — must reimplement in TS (new cross-language drift surface) or reach Python over WASM/HTTP (§3). | **Desktop wins decisively.** This is the coupling the current architecture exists to guarantee. |

---

## 2. Stack mapping — reusable vs rewrite

Each editor piece, and how it maps to a React stack. "Reusable-as-logic" = the algorithm ports near-mechanically to TS; "rewrite" = paradigm-bound to pygame and discarded; "contract" = must match Python exactly or files diverge.

| Current piece | File(s) | Maps to | Verdict |
|---|---|---|---|
| Frame-major working model (`WorkingMove`/`FrameBox`, box CRUD, letters, priority, extend, reverse-collapse) | `working.py` (813) | TS state model / reducer | **Reusable-as-logic** — pure over plain data. |
| Undo/redo snapshot stack + dirty tracking | `history.py` (118) | TS reducer + immutable snapshots | **Reusable-as-logic** — trivial. |
| Inspector field model (editable fields, nudge) | `inspector.py` (142) | React form/controlled inputs | **Reusable-as-logic**. |
| Per-move doc diff | `doc_diff.py` (216) | TS pure functions | **Reusable-as-logic** — no pygame/pycats. |
| Playhead/playback | `playback.py` (72) | TS + `requestAnimationFrame` | **Reusable-as-logic**. |
| Character/move navigation | `navigation.py` (68) | TS; reads roster + fighter data | **Reusable-as-logic** (needs the data loader, §4). |
| Keybinding table + help sections | `keybindings.py` (132) | TS data + a keydown handler | **Reusable-as-logic**. |
| Persisted prefs | `settings.py` (164) | `localStorage`/IndexedDB | **Rewrite** (thin) — swap the storage backend. |
| Button/target hit-test registries | `buttons.py` (53), `targets.py` (100) | DOM elements + `data-testid`/`getByRole` | **Reusable-as-concept** — the semantic registry is the *least* disruptive piece; DOM gives hit-testing for free. |
| Author-px↔display-px scale seam | `vis.py` (73) | SVG `transform` / canvas scale about origin | **Reusable-as-logic** — `scale_resolved` is a scale-about-origin; see §5. |
| Windowed zoom (1×/1.5×/2×) | `zoom.py` (71) | CSS/canvas zoom | **Rewrite** — currently delegates to `pycats.shell.display`; becomes browser zoom. |
| Canvas draw (resolve+draw hit/hurt circles) | `canvas.py` (158) | SVG `<circle>` / canvas `arc()` | **Rewrite the draw**, reuse the resolve step (contract, §3). |
| Timeline frame-strip (px/frame math + draw) | `timeline.py` (143) | TS math + React/SVG strip | **Split** — math reusable, `draw_timeline` rewritten. |
| Reference-GIF decode + compare (Pillow) | `gifcompare.py` (300), `gif_map.py` (204) | `<img>`/canvas + `<gif>` decode; JSON map reused | **Rewrite the decode/blit**, reuse the map + transform math. |
| **The combat contract**: `resolve_circle`, `collapse`, `fighter_to_json`/`_fighter_from_json`, `Circle`/`Hitbox`/`Hurtbox`/`MoveData`/`FighterData` | `pycats/combat/*` via imports | TS reimpl **or** WASM/HTTP (§3) | **Contract** — the crux; must match Python exactly. |
| The immediate-mode app loop + all draw dispatch | `__main__.py` (1,850) | React components + render loop | **Rewrite** — discarded and rebuilt. |

**Rough split:** ~2,500 LOC of portable app/UI logic (reusable-as-logic), ~2,300 LOC of pygame-bound loop/draw (discarded, rebuilt as React), and a thin contract layer that every geometry/save path routes through.

---

## 3. Key question — geometry/collapse/serialize fidelity across the language boundary

This is the dominant tradeoff. Three ways to honor the contract:

### Option A — reimplement in TypeScript + a cross-language drift-guard
Port `resolve_circle`, `collapse`, and the `<character>.json` (de)serializer to TS.

- **Portability of the math** (measured): `resolve_circle` is ~6 LOC of **integer** arithmetic — the one detail that must be exact is the facing-left mirror `cx = origin_x + width - dx` (mirror about the *body centre*, not the left edge; the #64 fix). `collapse` is ~75 LOC of pure, deterministic grouping/run-length/sort logic. The type layer is plain frozen dataclasses → trivial TS interfaces. The sim is **integer-pixel by design** (#80), so there is no float drift in the render/hit-test path.
- **The two byte-identity risks:** (1) the serializer's "omit == default" rule (a field equal to its default is dropped) — must match field-by-field or saves stop being golden-safe; (2) `u() = round(x * 5.4)` derived speeds use Python **banker's rounding**, which differs from JS `Math.round` on `.5` ties — a concrete cross-language gotcha if the editor derives speeds.
- **The new cost this creates:** today the lockstep guarantee is *intra-Python* — `tests/test_drift_guard.py` (R7, #863) recompiles each shipped fighter's provenance through the game's own `collapse` and asserts it reproduces the committed `hitboxes`; `test_geometry.py` / `test_collapse.py` pin the numeric oracles. A TS reimpl **breaks this loop** — the guard can't import TS. You'd need a **cross-language drift-guard**: run the TS `collapse`/`resolve_circle` over the same fixtures (`_JAB_FRAMES`, the shipped `<character>.json` corpus) and assert equality against a Python-emitted golden. The existing fixtures are directly reusable as the shared corpus.
- **Verdict:** pure client app, offline, no server, fast. But it **sacrifices the exact-by-construction coupling** and replaces it with two implementations kept in lockstep forever behind a cross-language test — the very drift the one-codebase architecture exists to prevent.

### Option B — Python backend / API
The web UI calls a Python service for resolve/collapse/save; the service `import`s `pycats.combat` directly.

- **Pro:** single source of truth preserved — zero drift, no reimplementation.
- **Con:** needs a running server (hosting, latency per interaction, offline breaks). It undercuts the main distribution win — "just open a URL" becomes "open a URL backed by a live Python service." Heaviest deploy of the three.

### Option C — Pyodide / Python-in-WASM
Run the pure `pycats.combat` modules in-browser via Pyodide.

- **Pro:** single Python source, no server, offline-capable, zero drift — the lockstep guarantee survives.
- **Key enabler (measured):** `geometry.py`/`collapse.py`/`data.py` are **pure Python, dependency-light — no pygame, no NumPy.** They load into Pyodide cleanly. (We do *not* need pygame-ce in the browser; only the combat modules.)
- **Con:** Pyodide's initial download (~several MB) + startup latency; a build/bundling step to ship the combat package into the WASM runtime; keeping the vendored Python subset in sync with the game (a package-pin, not a code reimplementation).
- **Verdict:** the option that preserves exact fidelity *and* the static-URL distribution win. The dependency-light combat modules make it viable where a full pygame port would not be.

**Summary:** A is the smallest runtime but adds a permanent cross-language drift surface. B and C preserve the exact contract; C keeps the "open a URL" win, B does not. The fidelity choice, not the UI, is where the effort and the architectural risk live.

---

## 4. Key question — rendering model (your framing: canvas / DOM / WebGL / WASM / other)

What the editor draws: a fighter body rect, a handful of hit circles + hurt circles per frame, a selection ring + drag handles, a timeline frame-strip, an optional reference-GIF raster underlay, and chrome (buttons/labels). The scene is **small** — single-digit-to-low-dozens of primitives at 640×360 (×`VIS_SCALE` 1.5). That smallness is decisive.

| Approach | Fit for this editor | Notes |
|---|---|---|
| **HTML Canvas 2D** | Good for the raster layer | Closest to pygame's immediate-mode: redraw per frame, `ctx.arc()` for circles — a near-direct port of `canvas.py`'s draw. But it's *not* retained: you re-implement hit-testing (reuse the `resolve_circle` + point-in-circle test the editor already has) and get no free per-element events/accessibility. Best for the **GIF reference underlay** and any pixel-exact overlay. |
| **DOM / SVG (retained)** | **Best fit for the interactive layer** | Each hit/hurt circle is an `<svg><circle>`; React reconciles them from state. Free per-element pointer events (select/drag handles become element handlers), free accessibility, and the semantic `targets` registry collapses into `data-testid`/`getByRole` — which the test model (§7) already mirrors. The usual SVG downside (perf at thousands of nodes) does not apply here; the element count is tiny. `vis.scale_resolved` (scale a resolved circle about the fighter origin) becomes an SVG `transform`. |
| **WebGL** (regl / PixiJS / three) | **Unjustified** | GPU rendering solves a perf problem this editor does not have (a few circles). It adds a shader/scene-graph layer, complicates hit-testing and testing, and buys nothing at this scale. Only worth revisiting if the editor grows a many-particle or full-game-render preview. |
| **Pyodide / WASM** | Not a *rendering* choice | WASM is a **fidelity/runtime** option (§3 Option C), not a draw surface. It answers "where does the geometry math run," not "how are pixels put on screen." It composes with any of the three above. |

**Rendering recommendation (for the downstream decision):** a **hybrid** — SVG/DOM for the interactive box layer (React-native, free events + accessibility, mirrors the `targets`/getByRole test model, right for the low element count) with a **Canvas 2D** layer underneath for the reference-GIF raster and any pixel-exact overlay comparison. WebGL is not warranted.

---

## 5. Key question — the `vis.py` scale seam translation

Two independent scalings today, and a port must keep them independent:

1. **`VIS_SCALE = 1.5`** (`vis.py`) — a *display-only* magnification so boxes are big enough to author. **Author data is never multiplied** — a `Circle`'s px stay 1×, so saved JSON is byte-identical (the #1013 acceptance gate). `scale_resolved((cx,cy,r), origin, k)` magnifies a resolved circle *about the fighter origin*: `(ox + (cx-ox)*k, oy + (cy-oy)*k, r*k)`. Draw and hit-test call it with the **same** `k`, so the drawn circle and the clickable region are one geometry.
2. **Windowed zoom** (`zoom.py`, 1×/1.5×/2×) — a separate nearest-neighbour magnification of the whole base surface, delegated to `pycats.shell.display`.

**In a web stack:** `VIS_SCALE` about-origin scaling is a natural SVG `transform="translate(ox,oy) scale(k) translate(-ox,-oy)"` (or a canvas `translate/scale`); windowed zoom becomes browser/CSS zoom or a viewport transform. The write path reverses only the `vis` layer (`unscale` a drag delta back to author px before the model records it) — the same inverse must exist in TS. Keeping author data at 1× is the invariant that keeps saves golden-safe regardless of render scale.

---

## 6. Key question — distribution & audience

- **Who runs it today:** effectively the maintainer + any contributor authoring hitbox/hurtbox data. It's an **internal authoring tool**, not an end-user product. Launch is `python -m pycats_editor` after an editable install of pycats + the editor.
- **What a browser app changes:** removes the Python/SDL install barrier and opens authoring to non-Python contributors and tablets. But against a small authoring audience, the reach win is **modest** — it does not, by itself, justify a large rewrite. It matters more if box-authoring is meant to open up (cf. #1191 box-authoring epic, #1206/#1220 ghost-assist) to a wider pool of contributors; that is a product-direction question for the human.

---

## 7. Key question — test / harness parity

The current substrate (well-developed — 62 files, ~7,938 LOC, ~1.5× the app):

- **Headless render:** `SDL_VIDEODRIVER=dummy` boots pygame with no display.
- **Deterministic stepping:** `main(run_frames=N, on_frame=cb)` renders exactly N frames and calls back per frame with the composited surface — the #1197 snapshot/capture seam.
- **BDD harness** (`tests/scenario.py`, #1130): chainable `.press/.click/.click_target/.add_box/.scrub/.save/.idle`, `.snapshot(path)` (PNG per step), `.run(capture_each=dir)`, `.replay(fps=)` (visible-window replay for eyeball review).
- **Semantic targets** (`targets.py`): `.click_target("add-box")`, `("frame", i)` — the getByRole analog, living in `src/` so tests and the future assist loop share one addressability source.

**Parity in a web stack:**

| Current mechanism | Web equivalent | Difficulty |
|---|---|---|
| Semantic `targets` registry | `data-testid` / `getByRole` | **Easy** — near 1:1; the least disruptive piece. |
| `pygame.event.get` monkeypatch queue | React Testing Library `fireEvent` / synthetic DOM events, one "frame" per step | **Easy–moderate**. |
| `run_frames` + `on_frame(index, surface)` | Controlled render loop + per-commit observer, or Playwright screenshot per step | **Moderate** — reproducing deterministic frame-stepping in React. |
| `.snapshot` / `.replay` (PNG + visible replay) | Playwright screenshots (already available) + a headed run | **Moderate**. |
| pycats round-trip tests (author→`collapse`→`fighter_to_json`→reload) | Depends on §3: a WASM/subprocess Python oracle (B/C) **or** a TS port diffed against a Python golden (A) | **Hard** — the port everything rides on; this is the drift-guard, restated for the web. |

Playwright covers the interaction/snapshot layer well. The hard test work is the same as the §3 crux: proving the web app's saves match Python.

---

## 8. Feature-parity inventory — the "build out in full" checklist

A full rewrite must reproduce:

1. **Canvas render** of a fighter's hit/hurt circles for one frame, pixel-faithful to the game overlay (same colors/line-width constants).
2. **Selection** — click a base-space point → pick a box id (resolve + point-in-circle).
3. **Frame-major working model** — per-frame boxes with cross-frame id identity + stable letter labels; box CRUD, priority, extend-across-frames, reverse-collapse from a fighter/provenance.
4. **Inspector** — edit a selected box's fields (damage/angle/knockback/…) and move timing (startup/active/recovery), with nudge.
5. **Timeline** — frame-strip with phase coloring, playhead, click-to-scrub.
6. **Playback** — play/pause + speed control advancing the playhead.
7. **Undo/redo** + dirty tracking + reset-to-baseline.
8. **Save/collapse** — fold the frame-major trace into canonical windowed hitboxes; write the thin-mirror `<character>.json` + `provenance.frames`; default-omission byte-identity; live-vs-scratch destinations with an overwrite prompt.
9. **Reopen** — exact inverse from provenance (preferred) or lossy reverse-collapse from committed hitboxes.
10. **Navigation** — cycle characters/moves.
11. **Zoom** — windowed magnification independent of author data.
12. **Reference-GIF compare** — decode source-animation GIFs, overlay/side-by-side, per-character move→subaction map.
13. **Keybindings** + help modal (single-source table).
14. **Doc diff** — per-move diff between two character docs.
15. **Test harness** — driveable/observable, named targets, step→screenshot, visible replay (the #1197 substrate).
16. **The combat contract** (§3) underpinning 1, 2, 8, 9 — the non-negotiable.

---

## 9. Phased effort estimate

T-shirt sizes, with the caveat that the §3 fidelity choice is the multiplier (A adds the cross-language drift-guard build; C adds Pyodide bundling; B adds a service).

| Phase | Scope | Rough size |
|---|---|---|
| **P0 — Contract spike** | Stand up the chosen §3 path end-to-end: resolve+collapse+serialize a known move and prove byte-identity against a Python golden over the shared corpus. De-risks the whole project. | **M** (A/C), **S–M** (B) |
| **P1 — MVP** | Render one fighter/one frame (SVG+canvas), select a box, edit inspector fields, save a scratch file that round-trips. Ports: `working` (subset), `inspector`, `selection`, `vis` math, `save` orchestration. | **L** |
| **P2 — Parity** | Full working model (multi-frame, letters, priority, extend, reopen), timeline+playback, undo/redo, navigation, zoom, keybindings, doc diff, GIF compare, live-save with overwrite prompt. | **XL** |
| **P3 — Harness parity** | Playwright + RTL substrate, semantic targets → `getByRole`, deterministic stepping, snapshot/replay, and the cross-language save round-trip suite. | **L** |
| **P4 — Assist features** | The current in-flight investments (#1197 harness extensions, #1206/#1220 datamine ghost-assist) re-landed on the web substrate. | **M–L**, ongoing |

**Overall:** a full parity rewrite is a **large, multi-phase effort (L→XL)** — roughly on the order of rebuilding the ~2,300 LOC pygame layer as React plus re-validating the contract, on top of porting ~2,500 LOC of logic. The logic port is the *easy* bulk; the contract + its cross-language proof is the risk and the long pole.

---

## 10. Recommendation + option space (for the human to rule)

Three options, framed for the downstream ARC/decision ticket:

| Option | What it is | Buys | Costs | Best when |
|---|---|---|---|---|
| **1 — Keep pygame** | Continue the desktop editor; harvest specific web wins (if any) incrementally. | Zero rewrite; the exact-by-construction combat coupling stays free; ongoing #1206/#1220 investment continues uninterrupted. | No browser reach; install barrier persists. | The authoring audience stays small and the coupling guarantee is prized. |
| **2 — Incremental web** | A thin web surface for a *narrow* slice (e.g. a read-only viewer or a single-move authoring page) backed by Python (§3-B) or Pyodide (§3-C), pygame remains primary. | Tests the browser value with a small bet; preserves exact fidelity; coexists via the shared `<character>.json`. | Two editors to maintain during overlap; partial feature set. | You want evidence the web reach matters before committing to XL. |
| **3 — Full React rewrite** | Rebuild to parity on the web, retire pygame. | Best UX/distribution ceiling; single modern stack. | L→XL effort; a new cross-language drift surface (if §3-A) or a Pyodide/service dependency (§3-C/B); re-homing all in-flight editor work. | Box-authoring is meant to open to a wider contributor pool (cf. #1191) and the org will fund the rewrite. |

**Lowest-regret lean (a recommendation, not a decision):** **Option 1 by default**, with **Option 2 as the way to buy information** if the web reach is thought to matter. The distribution/UX wins are meaningful but modest against a small authoring audience (§6), while the cost is large and — critically — a JS reimplementation (§3-A) *manufactures* the exact drift the one-codebase architecture was built to prevent. If a web path is pursued, **prefer §3-C (Pyodide) over §3-A**: it keeps the lockstep guarantee *and* the "open a URL" win, enabled by the combat modules being pure, dependency-light Python. Rendering, if built, should be the **SVG+Canvas hybrid** of §4, not WebGL.

**Coexistence note:** because both editors read/write the same thin-mirror `<character>.json`, a web editor is **not a hard cutover** — under §3-B/C (where Python owns the serializer) it can run side-by-side with the pygame editor/game on the same data files during any transition. Under §3-A that only holds while the TS serializer stays byte-identical.

---

*No code, no prototype, no stack chosen — those are downstream of the decision this doc informs.*
