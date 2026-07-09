# TIL 2026-07-08 — GRAPE

**Context:** Shipped #550 (HUD visual hierarchy — emphasize Damage %/Lives in the bottom
corners). Its new tests reordered the deterministic test collection just enough to surface a
latent test-isolation bug in the *menu* tests, which I fixed inline. That led to a decision
session (`guide-human-decision` + `yegor-personas`) on how to handle refactor-exposed test
failures, a follow-up hardening ticket (#709), and a font-usage guide (#711).

---

## 1. A monkeypatched factory can leak its fake through a *shared cache*

**What happened:** #550's new tests shifted collection order, and suddenly `test_menu_button`
reddened with `AttributeError: '_DummyFont' object has no attribute 'get_ascent'` — in a file
my diff never touched. The culprit was `test_main_menu_title`, which does
`monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **k: _DummyFont())`. The `monkeypatch`
was *correct* — `SysFont` was restored at teardown. But `TextRenderer._get_font` had already
**cached the `_DummyFont` in the shared `text_renderer.font_cache` singleton**, and the cache
holds the object, not the patched function. So the fake outlived the patch and poisoned the
next test that composed mixed text.

**What I learned:** Our existing rule ("use `monkeypatch`, never hand-restore a global") did
*not* cover this — the patch was used properly; the leak was one layer downstream, in a cache.
Patching a *factory* whose products are memoized in a process-global is a distinct trap: the
revert restores the factory, not the already-cached product.

**The rule:** **When you monkeypatch a font/factory whose output is cached in a shared
singleton, flush the downstream cache in your own teardown — the patch revert won't.** (Now
RULES.md's "cached-fake variant" of the leaked-global rule; #550/#709.)

---

## 2. A red gate is not a PDD puzzle — you can't `@todo` your way past it

**What happened:** The user asked the sharp question: wouldn't strict Yegor "file a bug TODO
and move on"? I ran it through the personas. PDD (puzzle-driven dev) defers *scope* — a stub,
a missing corner. But #550's own tests made the suite red-on-reorder, so merging #550 as
authored would break trunk. **Merge-gate / zero-tolerance (never merge red) sit *above* PDD on
the authority ladder.** You cannot leave a `@todo` for a broken gate; that routes to
`yegor-stuck` (cheapest legitimate rung to green), not `yegor-pdd`.

**What I learned:** The "file it and move on" instinct is right about *tracking* (the leak
became #709) but wrong about *sequencing* when the exposed bug reddens your own merge. The
orthodox path is **B**: stop, file the bug (its independent repro is the complaint), fix it
first as its own reviewed unit, rebase the feature — available because the leak reproduced
without #550 (`pytest test_main_menu_title.py test_menu_button.py` reds on pristine main). What
I actually did — **A**, a ~6-line inline root-fix + tracking ticket — is the sanctioned
carve-out for a trivial fix.

**The rule:** **A refactor that exposes a pre-existing, unrelated red test → root-fix only
(never skip/quarantine/dodge); A: trivial (≤~10 lines) rides the commit + a tracking ticket;
B: non-trivial → stop, file, fix-first, rebase.** (Ratified 2026-07-07; now in RULES.md, #709.)

---

## 3. A leak-detector that *evicts* beats one that only asserts

**What happened:** For #709 I added an autouse guard (`_no_fake_fonts_leaked`) that checks the
shared `font_cache` on teardown. My first cut only *asserted* the cache was clean. But an
assert-only guard names the polluter yet leaves the fake in place — so downstream victims still
crash, and you get a cascade of red across files. I changed it to **evict then assert**: on a
leak it clears the cache (protecting later tests) *and* fails the polluting test by name.

**What I learned:** I proved it able-to-fail by disabling #550's teardown flush and running the
full suite: the guard fired on `test_main_menu_title` naming the leaked
`_DummyFont` at `[('dejavusans', 36), ('sys', None, 20)]`, and the menu victims **stayed
green** — exactly one failure, at the source. (A fixture-teardown assertion reports as an
`error`, not a `failed`, but still reds the run and names the test.)

**The rule:** **A cross-test pollution guard should evict the bad state as well as assert on
it — turn a mystifying downstream cascade into one pointed failure at the source.**

---

## 4. `git checkout <file>` during a revert-check wipes uncommitted edits (again)

**What happened:** Proving #550's size constant was able-to-fail, I `sed`-edited
`config.py` to equalize the size, ran the test, then `git checkout pycats/config.py` to
"restore" it. But my new `HUD_EMPHASIS_SIZE` line was *uncommitted* — `git checkout` reverts to
HEAD, so it silently wiped the addition. I had to re-add it. (Logged as error id=137.)

**What I learned:** This is the same footgun I've hit before: `git checkout <file>` is "restore
to HEAD," not "undo my last edit." For a revert-check on an *uncommitted* file, edit in place
(change the value, then change it back) — never round-trip through `git checkout`.

**The rule:** **Never `git checkout <file>` to undo a revert-check edit when the file has
uncommitted changes — it reverts to HEAD and eats them; edit in place instead.**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/render_battle.py`, `config.py` | HUD Damage %/Lives emphasized in the bottom corners; `HUD_EMPHASIS_SIZE` (#550) |
| `tests/conftest.py` | `_no_fake_fonts_leaked` autouse guard — evict + fail-by-name (#709) |
| `RULES.md` | cached-fake variant of the leaked-global rule + the refactor-exposed-failure A/B protocol (#709) |
| `docs/pygame-fonts.md` | contributor guide to the font/text stack (#711) |

## Related artifacts

- Issues #550, #709, #711 (the HUD feature → the leak guard → the font guide)
- RULES.md → "Never restore a monkeypatched global by hand in a test" (cached-fake variant)
- Prior footgun sightings: the leaked-global class bit at #345 and #453 before this
