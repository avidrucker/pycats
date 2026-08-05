# Analysis: three ways to label PM-parity status (council + pre-mortem)

> Design-of-record for how pycats should mark Project M parity/confidence. Evaluates
> three labeling schemes through the yegor-personas council, then stress-tests the
> survivor with a murphy-jutsu pre-mortem. Feeds the labeling umbrella tracker + the
> human-facing legend doc.
>
> Date: 2026-07-01. Agent: DRAGONFRUIT. Ticket #448.
> Siblings: **#408** (3-marker legend research, blocked by #410), **#233** (provenance
> registry). Parity docs: #189, #99. PM canon = Project M 3.6.

## The fork

Three ways to label PM-parity status. Which is valuable, can they coexist without
emoji-collision, and how does each fail?

- **Scheme A — #408 open-work flags** (inline, greppable): `⚠` guessed · `🔬`
  needs-research · `❓` open-question. Flags **only the unresolved**; a confirmed value
  is left unmarked (absence = "presumed fine").
- **Scheme B — #233 provenance registry** (machine-tracked, drift-guarded): `FOUND` /
  `GUESS` / `TUNED` / `DIVERGENCE`, but only over the ~34 `config.py` scalars.
- **Scheme C — proposed 🟢/🟡/🔴 traffic-light**: positively marks confirmed-good,
  spanning the full valid→invalid spectrum (🟢 valid+checked · 🟡 inferred/good-enough ·
  🔴 unchecked/invalid).

## Council of Decision (yegor-personas)

**Convergence:** **A and B are both valuable and already earn their keep; C is valuable
only as a _derived report view_, never as hand-typed inline markers.** A is the low-noise
inline signal (flag exceptions, leave the good unmarked). B is the authoritative
machine-tracked truth. C's green light should be **rendered from B's registry**, so
"confirmed parity" always traces to a cited source and can't be hand-stamped or rot
silently. **Authority: architect (rung 5), backed by `nohelp` (single source of truth)
and REQ (the #233 registry is the de-facto parity spec).**

Readings that drove it:

```
nohelp — Truth lives in ONE place; #233's registry is it. A green glyph re-asserting
         "confirmed" inline is a second source that WILL drift from the first.
  BECAUSE: docs/registry are source of truth; a duplicated status is a lie waiting to happen.
  STANDING: advisory, strong on "where does the answer live."

review — A "🟢 verified" marker with no proving mechanism is a rubber stamp — bullshit signal.
  BECAUSE: hunts the claim with no test behind it; "checked" must mean something checked it.
  STANDING: advisory on signal quality.

velocity — Green is self-awardable. Whatever is cheap to type and looks like progress gets gamed.
  BECAUSE: hunts the metric you can grant yourself; 🟢 with no source cite is a gamed green.
  STANDING: advisory (anti-gaming).

REQ — There's no formal parity spec; #233's registry is the closest thing to one. Parity
      STATUS belongs there (sourced, enforced), not scattered across comment glyphs.
  BECAUSE: the spec settles the fork; if it's silent, the registry is the spec-of-record.
  STANDING: rung-1 mouthpiece — points at #233 as the authority.

architect — Keep three AXES, one home each: A inline (open-work), B registry (status of
            record), C a derived report. Don't let C become a fourth hand-maintained inline system.
  BECAUSE: modes/systems don't mix; coexistence must be designed, not accreted.
  STANDING: tie-breaker on the design call (rung 5).
```

**Which single scheme is _most_ valuable? A (#408).** Its polarity is the right signal
design: absence of a marker means "presumed fine," so you only maintain annotations on
the exceptions — low-maintenance and grep-complete. B is valuable as *infrastructure*
(the enforced truth), not as a glyph you read. C is the one to handle with most care — as
literally proposed (hand-stamped inline circles) it is the *least* valuable and the most
dangerous (see pre-mortem risk #1).

## De-conflicted emoji design (if all three coexist)

The real collision: yellow-circle "inferred" (C) means nearly the same as `⚠` "guessed"
(A), and red-circle "unchecked" (C) rhymes with `🔬`/`❓`. The fix is **one emoji family
per axis, and reserve the colored circles for the derived report only** — never inline.

| Axis | Home | Glyphs (kept distinct) | Meaning |
|---|---|---|---|
| **A — open work** | inline in source, greppable | `⚠` · `🔬` · `❓` | guessed · needs-research · open-question |
| **B — provenance** | #233 registry (text, machine-tracked) | text `FOUND`/`TUNED`/`DIVERGENCE` (or `📌`·`🔧`·`🔀` if a glyph is wanted) | pinned-to-source · deliberately tuned · intentional departure |
| **C — parity light** | **generated report only** (e.g. a `parity-status.md` rendered from B) | `🟢` · `🟡` · `🔴` | valid+checked · inferred/good-enough · unchecked/invalid |

Rules that keep them from conflating:
1. **Colored circles never appear in source.** If you see `🟢` it came from the
   generator, not a human. This alone removes most of the overlap risk.
2. **No GUESS glyph in B** — `GUESS` maps to A's `⚠`, so the two axes don't both invent a
   "unconfirmed" symbol.
3. **C is a projection of B:** `FOUND` → 🟢, `TUNED`/`GUESS` → 🟡, `DIVERGENCE` or absent → 🔴.
   Green is *computed*, never typed.
4. Circles (round) vs warning/tool/question glyphs (A) vs pins/wrenches (B) are distinct
   *shapes*, not just colors — survives colorblindness and monochrome terminals.

## Pre-mortem (murphy-jutsu)

*It's six months out. The parity-labeling effort failed — the codebase now lies about
what's PM-accurate. What happened?*

### 🔴 High (act before proceeding)
- **Green rot — the stale-🟢 lie** — likelihood: **H**, blast radius: **H**
  - How it happens: a value hand-stamped `🟢` (correct vs PM 3.6 *at stamp time*) is later
    edited, or PM understanding is revised (cf. #426 revisiting #328), but the circle isn't
    updated. The code now actively asserts "verified parity" on a wrong number — *worse than
    no marker*, because it suppresses the scrutiny `⚠` would have invited.
  - Warning signs: 🟢 next to a value with no source cite; `git blame` on the circle older
    than the last edit of the value.
  - Mitigation: **derive 🟢 from #233's registry (with its drift-guard); never hand-stamp
    inline.** This is the whole reason C must be report-only.

- **Marker soup — three systems, one value** — likelihood: **H**, blast radius: **M**
  - How it happens: a constant ends up carrying `⚠` + `GUESS` + `🟡` from three axes;
    contributors don't know which is canonical; `grep ⚠`, the registry, and the report disagree.
  - Warning signs: any value with 2+ markers from different axes; PRs adding circles inline.
  - Mitigation: one-home-per-axis (table above); the single documented legend (the follow-up
    doc); extend #408's optional lint to reject inline circles.

### 🟡 Medium (mitigate or schedule)
- **Rubber-stamp green** — L/M × H: someone self-awards 🟢 by eyeballing ("looks right").
  Mitigation: 🟢 requires a `FOUND` registry row citing a source — same guard, restated as policy.
- **The one-shot audit that never re-runs** — M/M: the initial sweep is a snapshot; nobody
  re-audits, markers decay. Mitigation: derive from the registry (auto-fresh) or file a
  recurring re-audit; don't rely on human upkeep.
- **Emoji encoding/grep breakage** — M/L: `🟢` (U+1F7E2) and friends are multi-byte, newer
  Unicode; some terminals/editors/`grep` mishandle them, git diffs get noisy, review renders
  boxes. Mitigation: keep circles out of source (report-only); if B wants glyphs, ASCII-
  greppable text (`FOUND`) beats pictographs.

### 🟢 Low (monitor / accept)
- **Golden/parity-test churn from a mass sweep** — L/L: comment-only, goldens stay
  byte-identical (#408 already asserts this); only cost is review burden on a big diff.

### Accepted risks
- **A/B stay non-ASCII** (`⚠`/`🔬`/`❓`) — accepted; already 50+ in-tree and greppable,
  owner = #408.

## Recommendation summary

1. Adopt **three axes, one home each** (table above). A = inline greppable (own by #408),
   B = machine registry (extend #233), C = generated report **derived from B**.
2. **Colored circles are report-only.** Never hand-stamped in source. Green is computed
   from a cited `FOUND` registry row.
3. Sequence the rollout as three passes (one per axis) under the labeling umbrella tracker,
   with a human-facing legend/key doc as the shared reference.
