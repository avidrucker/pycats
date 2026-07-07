# TIL 2026-07-07 — GRAPE

**Context:** Drove the #672 decomplect epic (skin/character/selection → DDD + hexagonal)
through Phases 1a–2a as sequenced children — #680 (pure `pycats/domain/`), #686 (rewire the
two Player constructors through the `build_fighter` port), #692 (the 3-seam `PlayerIdentity` +
retiring the `char_name` overload), #695 (record each fighter's `Character.key` in the golden
snapshot). Four lessons crystallised, mostly around the golden-snapshot machinery.

---

## 1. Append to a serialized golden tuple — never insert mid-way

**What happened:** #695 (DP2) added a `character` field to `PlayerSnap`, the per-player golden
snapshot namedtuple. The ratified design preview showed it **after `name`**, so I put it at
index 1, regenerated all four goldens, and ran the suite — **22 failures**. The insert shifted
every later field by one. Production `sim/battle_log.py` reads parts by hard-coded index
(`_STATE, _PERCENT, _LIVES = 1, 7, 9`), and ~9 test files index snapshot rows positionally
(`p[1]` for state, `[9]` for lives, `[2]` for rect_x). All of them silently read the wrong
slot. I reverted and **appended `character` last** instead: zero existing indices move,
production + every positional reader stay valid, and the semantic decision (slot stays the
row-key, character rides alongside) is unchanged. Logged as error id=130.

**What I learned:** A namedtuple that gets *serialized* (goldens, wire formats, on-disk
snapshots) has two consumer classes: name-based readers (`PlayerSnap(*row).state`) that don't
care about order, and **positional** readers that encode the order as constants. Inserting
mid-tuple is invisible to the first and catastrophic to the second. The DP2 preview's "after
name" was a *presentation* preference; honouring it literally would have shipped a live bug.

**The rule:** **Before repositioning a field in a serialized/golden tuple, grep for positional
readers (production AND tests); default to appending at the end.** (Backed by error id=130.)

---

## 2. Prove byte-identity mechanically — don't eyeball the golden

**What happened:** Phases 1a–1c and the 2a schema-add were all meant to be byte-identical or
pure-additions. Rather than trust "the suite is green," I proved it: `git diff tests/golden/`
must be empty for the golden-neutral phases, and for #695 I wrote a throwaway script that loaded
the pre-commit and post-commit `.json`, stripped the appended field from each row, and asserted
the remainder (plus attacks/phase/winner) was byte-identical across all 600+ frames of all four
scenarios. Only then did I trust the `.summary.json` digest.

**What I learned:** "Green suite" and "byte-identical" are different claims. A regen makes the
suite trivially green against *itself*; it says nothing about whether the change was the one you
intended. The strip-and-compare proof turns "I think only the field changed" into "the machine
confirms only the field changed."

**The rule:** **For a golden-neutral or pure-additive change, prove it with a diff the machine
computes (`git diff tests/golden/` empty, or a strip-the-delta comparison) — not by reading the
digest and hoping.**

---

## 3. A golden *flip* is gated by the review, not the green suite — hold the close

**What happened:** #695 regenerated the goldens, so post-regen the suite is green by
construction. Per `tests/golden/REGEN_PROTOCOL.md` and the DP2 ruling, I committed but did **not**
close — I posted the `.summary.json` digest, flagged the one design deviation (append-last), and
held the close until the game-designer signed off. Only then did `pmtools close 695` run.

**What I learned:** The author of a golden regen can't be its reviewer — "I regenerated it, so it
matches" is circular. The digest review is the *only* real gate, and it belongs to a second
party. Building the "commit → post digest → request sign-off → hold close" flow into the phase
made the gate concrete instead of aspirational.

**The rule:** **On any golden-*flipping* change, hold the close: post the `.summary.json` digest
and get a second party's sign-off before `pmtools close`.** (Already in RULES → Closing work /
`REGEN_PROTOCOL.md`; this session confirmed the flow.)

---

## 4. Render-cache proxies duck-type your entities — scope them out separately

**What happened:** #692 split `char_name` into three seams and repointed its consumers. I scoped
it as "byte-identical, no test change." Wrong: `slot_accent_color` and `draw_player_name` are
also called with a `_CatShim` — a slots-based render-cache proxy built inside `render_battle` to
key the cached cat-body composite — which carries `char_name`/`nickname` but has **no**
`identity` seam. Repointing those two onto `identity` would have needed the seam plumbed through
the shim. I decoupled the win-attribution overload (real Players + test doubles) and **deferred**
the render-accent repoint to a dedicated render slice (#672 child "1d"). Two win-screen test
doubles also had to grow the seam. Logged as error id=128.

**What I learned:** An attribute isn't only read off the real object. Render caches build
lightweight proxies, and tests build duck-typed doubles — both mimic the *old* surface. "Repoint
this attribute" quietly means "repoint it everywhere it's duck-typed too."

**The rule:** **Before scoping an entity-attribute repoint as 'byte-identical, no test change',
grep for render-cache proxies and duck-typed test doubles of that entity — they carry the old
surface and set the true blast radius.** (Backed by error id=128; deferral filed as #672 "1d".)

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/domain/` | New pure DDD package: `Skin`/`Character`/`Selection`/`PlayerIdentity` + resolvers + `build_fighter` port (#680) |
| `pycats/sim/runner.py`, `pycats/battle_screen.py` | Both Player constructors build through the port (#686); `PlayerSnap` gains an appended `character` field (#695) |
| `pycats/entities/player.py` | `PlayerIdentity` seam; `char_name` → read-only alias; carries its `Character` (#692, #695) |
| `pycats/stats_print.py`, `pycats/sim/presenters.py` | Win-attribution + labels repointed onto the seams (#692) |
| `tests/golden/*.json` (×4 + sidecars) | Regenerated: each row now records `character` (#695) |

## Open threads

- **#696** (Phase 2b) — first real named-cat mechanics flip (default → Nalio vs Nalio); filed, teed up.
- **#672 "1d"** — repoint `slot_accent_color`/`draw_player_name` through `_CatShim` (deferred render slice).
- **#672 "R"** — placeholder flat-gray + black feature outlines (DP1); ready scope, not yet filed.

## Related artifacts

- Epic + phase checklist: issue **#672**
- Design spec: `docs/research-spec-675-skin-char-model.md`
- Findings: `docs/research/2026-07-06-skin-char-decomplect.md`
- Errors: id=128 (render-proxy blast radius), id=130 (golden field placement)
