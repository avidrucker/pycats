# Web-based pycats-editor — plain-English summary (#1235)

A short, jargon-light companion to the full findings doc
[`docs/research/pycats-editor-react-rewrite-findings.md`](research/pycats-editor-react-rewrite-findings.md).
Same conclusions, fewer terms. This summarizes; the findings doc has the evidence.

**In one line:** a web editor would be easier to hand out and nicer to build UI for — but the main
danger is that a JavaScript version could start drawing hitboxes differently from the game, which is
the exact problem the current setup avoids.

## Main pros of going web-based

- **No install.** Today you need Python set up to run the editor. A web version is just a link you
  open — usable by anyone, even on a tablet.
- **Wider reach.** More people (including folks who don't know Python) could help author hitbox data.
- **Better tools for building the UI.** The web has a large toolkit for buttons, forms,
  drag-and-drop, and live reload. Right now every widget is hand-drawn in a big loop.
- **Interaction comes for free.** On the web, each circle on screen can be its own clickable element,
  so selecting and dragging boxes is simpler than the current "work out what you clicked by hand".
- **Testing tool already here.** Playwright (a browser-testing tool) is available, and the editor's
  current "click the add-box button by name" test style maps almost one-to-one onto web tests.

## Main risks / cons

- **The big one — drift.** The editor and the game must agree *exactly* on where hitboxes go and how
  save files look. Today that is guaranteed because they share the same Python code. A JavaScript
  rewrite means a *second copy* of that math — and two copies tend to drift apart over time. That is
  the very problem the current single-codebase design was built to prevent.
- **Save files must match to the byte.** The game loads the editor's files directly. If the web
  version formats a saved file even slightly differently, the game breaks. There is even a subtle
  trap: Python and JavaScript round `.5` values differently.
- **A whole safety net has to be rebuilt.** A test catches the editor and game disagreeing; it only
  works because both are Python. A web version needs a new, harder cross-language version of it.
- **It is a big rebuild.** Large effort — the display half of the editor is thrown away and rebuilt,
  plus all the shared math has to be re-proven correct.
- **The payoff may be small.** Only a handful of people author this data, so "easier to hand out"
  does not buy much if almost nobody new will use it.

## The way to dodge the biggest risk

You can *keep* one shared copy of the math instead of writing a second one — either run the Python on
a server the web page calls, or run the Python **inside the browser** (via a tool called Pyodide).
The in-browser option is appealing because the math files are small, plain Python (no pygame, no
NumPy), so they load into the browser cleanly — you get the "just open a link" benefit *and* keep the
game and editor perfectly in sync.

## Advice (a lean, not a decision)

- **Default: keep the pygame editor.** The reach/UX wins are meaningful but modest against a small
  authoring audience, and the cost is large.
- **If you want to test the web idea, do a narrow slice first** (e.g. a read-only viewer or a
  single-move page) rather than a full rewrite.
- **If you go web at all, do not rewrite the math in JavaScript** — run the same Python in the
  browser (Pyodide) so the game and editor stay perfectly in sync — one copy of the math, not two.
- **Rendering:** the scene is tiny (a few circles), so use plain browser drawing (SVG for the
  interactive boxes + a canvas layer for the reference GIF). A heavyweight GPU option (WebGL) is not
  warranted here.

*The decision itself — rewrite or not — is a separate follow-on ticket with a human.*
