# TIL 2026-06-30 — GRAPE

**Context:** A long session under the #264 "architecture re-review follow-ups" epic — the 3-tier re-review itself (#252 → doc `architecture-review-2026-06b.md`), then landing its follow-ups one at a time: the Fighter↔Player decoupling chain (S1–S6: #273/#283/#286/#289/#293/#298/#304), the rendering-port finish (#317/#326/#330), F3 (#321), B-b (#322), and two paired architect decisions (#320→ADR-0004, #318) plus the boundary guard (#339). Everything was behaviour-neutral.

---

## 1. Review to 15/15 *before* claiming — batch-filed tickets go stale

**What happened:** After the re-review I mass-filed #264's follow-ups (#317–#322) in one go — against the tracker's own "do NOT mass-create" note. It bit exactly where predicted: by the time I reached **F3 (#321)**, its stated approach ("derive `done_attacking` off `MoveClock` *on the Fighter*") was **impossible** — an earlier slice, **S6 (#304)**, had removed the Fighter→Player back-reference, so the Fighter could no longer see the clock. Running `/issue-review-skill` on it first scored it NEEDS WORK; I re-scoped it (derive on *Player*, which owns the clock) before claiming. Separately, **H-b (#317)** as filed bundled three independent entity extractions → NEEDS WORK; I sliced it to one (Platform) and filed Attack/Tail as they came up.

**What I learned:** A batch-filed ticket freezes a premise that later work invalidates. The review gate is cheap and catches it before you waste an implementation. Re-scoping a ticket to a single clean deliverable *is* the work of getting it to 15/15.

**The rule:** **Run `/issue-review-skill` on the ticket right before claiming; if a prior slice changed its premise, re-scope to 15/15 first — and prefer filing follow-ups one-at-a-time when about to work over batch-filing.**

---

## 2. The byte-identical oracle proves equivalence — but know *which* oracle covers what

**What happened:** Every refactor this session leaned on "goldens byte-identical, no regen" as the equivalence gate: the `done_attacking` latch ≡ `attack_timer == 0` (#321), a `PlayerSnap` namedtuple serialising identically to the old tuple (#322), the `_ko`/`force_prone` return-intent inversion (#298). The gotcha: **the render-parity test `test_battle_screen_render` renders players (hence tails/attacks), so a "render-only" change can flip it even though the *sim* goldens are render-free.** The #239 default-overlay-ON change flipped it; the #330 tail-Surface extraction *relied* on it to prove pixel-identical output.

**What I learned:** "Behaviour-neutral" needs the right oracle. Sim goldens (`tests/golden/*`) cover the deterministic snapshot; the render-parity test covers pixels. A change can be sim-neutral but render-visible, or vice-versa.

**The rule:** **Pin behaviour-neutrality to byte-identical goldens AND, for anything the renderer touches, the render-parity test — they cover different surfaces.**

---

## 3. Slice when implementation surfaces frame-ordering entanglement

**What happened:** Several slices shrank once I read the actual per-frame control flow. **S1 (#273)** moved the "stateless" timer decrements — but `hitlag_timer` is bound to a freeze early-`return`, so it stayed inline. **S4 (#289)**: the getup timers are *set inside the prone-expiry block and decremented by their own block in the same frame*, so moving their decrement to a top-of-frame `tick()` would drop that same-frame tick — an off-by-one; only `prone`/`dodge` were cleanly movable. Investigating the code *before* writing the ticket is what made these scopes correct.

**What I learned:** Timer/flag decrements that look uniform are often welded to their read site by same-frame ordering. You can't see it from a grep; you see it by tracing the frame.

**The rule:** **Trace the per-frame ordering before scoping a "move the decrement" refactor — set-and-ticked-in-the-same-frame state cannot move to a top-of-frame tick without an off-by-one.**

---

## 4. A guard written to a rule red-catches the first real violation

**What happened:** #339 added an AST guard enforcing ADR-0004 (the rules core uses pygame only for `Vector2`/`Rect`, never the framework). On its very first run it went red — `core/physics.py` typed `solve_vertical`'s `drop_platform` as `pg.sprite.Sprite`. Physics only reads `.rect`, so I replaced it with a local structural `Protocol` (`_DropThrough`), making the core genuinely Sprite-free. The guard's red *was* the red-green; a revert-check (inject `pg.event`) confirmed able-to-fail.

**What I learned:** A boundary you just decided is almost never already perfectly held. Writing the enforcement guard is how you find the last violation — landing it green usually means fixing one real thing.

**The rule:** **When you codify a boundary as a guard, expect it to red-catch a live violation; fixing that violation is part of landing the guard, not a separate ticket.**

---

## 5. Architect-then-courier for decisions; a ruling isn't done until it's an ADR

**What happened:** The two decision tickets went through `/guide-human-decision` + `AskUserQuestion` as paired sessions (labelled `pair-work`). For **#320** (sanction `pygame.math` value types) I locked the ruling as **ADR-0004** + a `CONTEXT.md` fix *before* any code; for **#318** (split `core/input.py`) the ruling authorised a *separate* DEV ticket (#342) rather than inline redesign. Decisions #9/#10 + the #339 guard formed a closed loop: ADR-0004 set the boundary, #339 enforces it, #342 will fix the last violator.

**What I learned:** The design decision and its implementation are different modes. Keeping the ruling in an ADR/ticket (not chat) is what makes it survive the session, and it lets a courier implement without re-litigating.

**The rule:** **Record a design ruling as an ADR/ticket comment before writing code; implement in a separate courier step — never redesign mid-implementation.**

---

## 6. Decomplect a latched shadow into a derived value

**What happened:** `done_attacking` (#321) was a hand-latched boolean maintained at three sites to shadow the move clock — the codebase's own `move_clock.py:8` called it a "shim … hand-kept in sync." I deleted the field + all three writes and made it a derived `Player.done_attacking` property (`attack_timer == 0`). Same story, larger: S6 (#304) deleted the `Fighter.owner` back-reference entirely once S2/S3/S5 had inverted the reaches (state-label passed in, `force_prone`/`engine.force("ko")` returned as intent, #298).

**What I learned:** State that merely mirrors another source is `value ⊗ time` complecting — deleting it and reading the source removes the whole sync burden. The `/decomplect` lens named it precisely.

**The rule:** **A flag kept in sync with a computable value is a shadow — delete it and derive from the single source.**

---

## What landed

| Artifact | Change |
|---|---|
| `docs/adr/0004-*.md` | Sanction `pygame.math` value types in the core (decision #10) |
| `tests/test_core_pygame_boundary.py` | AST guard: core uses no pygame framework (#339) |
| `pycats/render_battle.py` + entities | Rendering port finished — Platform/Attack/Tail hold data, adapter composites (#317/#326/#330); Tail is now pygame-free |
| `pycats/entities/{fighter,player}.py` | Fighter↔Player dependency is one-way; `done_attacking` derived; `owner` back-ref deleted (S1–S6, #321) |
| `pycats/sim/runner.py` | `PlayerSnap` namedtuple — golden snapshot self-describing (#322) |

## Open threads

- **#342** — split `core/input.py` (last unblocked #264 code item; handoff written).
- **#319 / B-a** — blocked on **#226** (ADR-0003 sign-off).

## Related artifacts

- Epic #264; re-review doc `docs/research/architecture-review-2026-06b.md`; ADR-0004.
