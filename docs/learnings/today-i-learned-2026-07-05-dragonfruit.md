# TIL 2026-07-05 — DRAGONFRUIT

**Context:** A session that started from a stale status line ("why does it still show the
deleted worktree?") and turned into a pmtools close-discipline arc — filing + reviewing
pmtools#104/#105, flipping pycats' close instructions to the from-main form (#519→#526),
a PM fall-physics research (#528), and an error-logging reckoning (#533 + a backfill).
The connective tissue: fix the *shape* of the problem, and verify before you write it down.

---

## 1. A child process can't chdir its parent — so *avoid* the bad state, don't *repair* it

**What happened:** `pmtools close` deletes the worktree you're standing in, stranding the
shell in a removed cwd (`getcwd: cannot access parent directories`) with a stale branch in
the status line. The tempting fix is "have pmtools move me back to main afterward." It
can't: a child process cannot change its parent shell's directory. The durable fix
(pmtools#104) is to make `close` runnable *from the main checkout* (it resolves the worktree
by issue #), so the shell is **never inside the doomed dir** to begin with.

**What I learned:** When a component structurally can't repair a caller's state, the answer
is usually to redesign so the bad state never occurs, not to bolt on a recovery step.
"Run from a stable cwd" beats "return to a stable cwd."

**The rule:** If a fix would require a child to mutate its parent (cwd, env, shell), don't —
restructure so the parent is never in the state that needs mutating.

---

## 2. A deferred "follow-up mechanism" can evaporate once the primary fix reframes the problem

**What happened:** Filing pmtools#104 I wrote that it "deferred the auto-return mechanism to
pmtools#105" — implying #105 was needed. The user pushed back: *"I don't want to close from
inside a worktree — do I even need #105?"* Walking both of #105's prongs against "always
close from main" showed each only fires when you close *from inside the worktree* — the case
#104 + a one-line convention removes. #105 was closed as unneeded.

**What I learned:** "I'll defer X to a follow-up" can quietly assert X is necessary. Once the
primary fix changes the shape of the problem, re-derive whether the follow-up still has a job
— don't build it on the inertia of having named it.

**The rule:** Before implementing a deferred follow-up, re-check that the primary fix didn't
dissolve its reason to exist.

---

## 3. Never document a form that doesn't work yet — verify the dependency actually landed

**What happened:** Asked to "update RULES to the new form," the clean
`cd <main> && pmtools close <N>` only works *after* pmtools#104 lands. Writing it prematurely
would ship an instruction that fails. So #519 documented the works-today workaround, and I
only flipped RULES+CLAUDE to the clean form in #526 **after confirming #104 was CLOSED and
reading the merged `close.py`** (it chdirs its own process back to root before teardown → the
old exit-1 was a getcwd artifact, gone from main).

**What I learned:** "The user says it landed" is a premise to verify, not a fact — the same
verify-before-asserting rule that bit me on specials-scripting (#429) applies to
dependencies. Docs must describe what works *now*; a not-yet-true instruction is a landmine.

**The rule:** Gate new-form docs on the dependency being verified landed (state + code), and
document the works-today form until then.

---

## 4. Dogfood a workflow fix on its own close — observe the result, don't assert it

**What happened:** #526 changed how we close tickets, so I closed #526 itself via the new
`cd <main> && pmtools close 526` and captured the live result: **exit 0, cwd stayed at the
main checkout, branch main, worktree gone** — no strand. Same on #528. I'd documented "exits
0" from *reading* the code first, then the dogfood *confirmed* it (the ticket's acceptance
demanded observed, not assumed).

**What I learned:** When a change is about a workflow, its own close is a free, real
end-to-end test of that workflow — and the closing comment is where the observed exit
code/output belongs.

**The rule:** Exercise a workflow change on the change's own close; record the *observed*
behaviour, don't paste an assumed one.

---

## 5. The pre-close error self-audit is a silent-failure backstop — run it every close

**What happened:** I hit two WebFetch `NETWORK_FAIL`s (#528), a close rebase-conflict
(`GIT_FAIL`, #511), and a probe `StopIteration` (wrong `PYTHONPATH`, #432) — and logged
**none** of them, because I skipped the log-error skill's pre-close self-audit on every close.
A human asking "did you log those?" was the backstop, late. Backfilled as errors rows 46-50
(50 = the compliance miss itself); filed #533 to mandate an `error self-audit: …` line in
every closing comment. Bonus meta-misfire: an apostrophe in "session's" broke the
single-quoted `pmtools error log` arg — reworded apostrophe-free, noted in the row.

**What I learned:** A clean session and a forgotten log look identical unless the close states
the audit outcome. "Log at the moment of failure" is ideal but forgettable; the explicit
per-close statement turns silence into a checkable claim.

**The rule:** At every close, run the self-audit and put `error self-audit: N row(s) logged`
/ `no loggable errors this session` in the closing comment (per the log-error skill; #533
codifies it).

---

## 6. Research corrects the ticket's own framing — value questions need the attribute model

**What happened:** #528 asked "should Nalio (Mario) and Birky (Kirby) fall at the same rate?"
The intuitive framing ("Kirby's floaty, so he falls slower") is wrong on the specifics: their
*normal* terminal fall speeds are close (~1.28 vs ~1.2). The real divergence is **gravity**
(fall accel) and — decisively — **fast-fall** (Kirby has ≈none; Mario strong), which pycats
can't even represent (no fast-fall mechanic). And **weight (100 vs 70) is knockback, not
fall** — the conflation dispelled. Surprise upside: Birky's #229 "guess" *ratios* were already
near-faithful to Brawl's Kirby/Mario ratios.

**What I learned:** A "what value should X be?" question is really a "which independent
attribute, in which model?" question. Answering at the level of the four-attribute model
(weight / gravity / fall speed / fast-fall) turned a yes/no into an actionable gap analysis.

**The rule:** Ground a value question in the mechanic's attribute model before sourcing a
number — the intuitive one-axis framing usually hides the axis that actually differs.

---

## 7. "Research + update a value" straddles DEV and ARCHITECT — surface the ambiguity, don't label past it

**What happened:** #528 proposed "a **DEV** to source/pin Nalio's + Birky's fall values." The
user flagged that this isn't obviously DEV — *finding/deciding* the canonical number is a
research/judgment act; *swapping a constant* is mechanical. Rather than pick a label, I filed
#530 to resolve the classification through the yegor lenses (architect-vs-courier, bdd,
microtasks).

**What I learned:** When a follow-up's *discipline* (DEV vs ARC vs research-split) is genuinely
unclear, that ambiguity is itself a decision worth a ticket — a mislabel silently routes the
work to the wrong role.

**The rule:** If you can't confidently name a ticket's role, the classification is a finding —
file it, don't guess the label.

---

## What landed / what's open
See `/tmp/pycats-handoff-2026-07-05.md` (session handoff) for the full ready-to-take list.
Shipped: RULES+CLAUDE from-main close (#526), fall-physics findings
(`docs/research/2026-07-04-pm-fall-physics.md`, #528), errors backfill (rows 46-50). Filed:
#533 (self-audit mandate — READY, tweaks applied), #530 (Yegor role classification). Upstream:
pmtools#104 landed, #105 closed.

## Related artifacts
- [TIL 2026-07-04 DRAGONFRUIT](./today-i-learned-2026-07-04-dragonfruit.md) — the prior day's
  verify-the-premise / ground-research arc this continues.
- `RULES.md` "Closing work" + `CLAUDE.md` (from-main close, #526); log-error skill (§5).
- Issues #526, #528, #530, #533; pmtools#104, pmtools#105.
