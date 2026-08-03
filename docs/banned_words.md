# Banned words

Words to avoid in tickets, docs, commit messages, and agent replies for this repo.
Most are vague filler or unearned jargon; some are wrong-workflow vocabulary — a term
for a process this repo doesn't use. Either way, replace with concrete, plain wording.

These are a **hard ban, not soft defaults**: do not use them in tickets, docs, commit
messages, or agent replies unless the maintainer explicitly permits the word in that
context. Reach for the concrete alternative every time; if you believe a banned word is
really the only right one, ask first rather than using it.

| Word | Why it's banned | Prefer instead |
|---|---|---|
| crisp | Vague praise-filler ("a crisp spec", "crisp repro") — says "good" without saying what's actually good. | State the concrete property: "specific", "unambiguous", "has exact repro steps", "machine-verifiable". |
| honest / honesty / honestly | Over-used throat-clearing ("to be honest", "the honest move", "honestly, …"). Implies the rest might not be, and adds no information. | Just state the thing plainly. If you mean a specific quality, name it: "accurate", "direct", "faithful to the facts". If you really need a word for truth-telling, ask the maintainer first. |
| candid / candidly / candor | Same throat-clearing as "honest" ("to be candid", "candidly, …", "full candor") — self-characterizes the reply instead of adding information, and implies the rest might not be. | State the fact plainly. If you mean a specific quality, name it: "accurate", "direct", "clear", "up-front" — or just say the thing. |
| genuine / genuinely / genuineness | Filler intensifier ("a genuine bug", "genuinely broken", "genuine improvement") — adds emphasis, not information; the claim stands or falls on its own. | Drop it, or name the property concretely: "real", "actual", "specific", "reproducible", "confirmed". |
| load-bearing | Over-used metaphor ("a load-bearing guard/comment/import") — dresses up "required" without saying what actually breaks without it. | Say what depends on it concretely: "required", "the test fails without it", "removing it breaks X", "the only thing setting Y". |
| neuter | Odd, slightly-off metaphor for disabling code ("neuter the check", "neutered the fix" during a revert-check). | "disable", "stub out", "comment out", "temporarily remove". |
| silent / silently | Hides whether something was observed ("fails silently", "silently skipped") — states an absence without saying what is or isn't seen. | Name what is or isn't observed: "with no error", "no log line is written", "the check is skipped and nothing is printed". |
| You're right | Reflexive agreement token that concedes nothing concrete — reads as filler before the real reply. | State the specific thing being conceded: "The probe was the ticket's work, not filing." |
| I apologize / I'm sorry | Reflexive apology token that adds no information and delays the correction. | Name what went wrong and the fix, with no apology word: "That probe scoped the ticket instead of filing it — filing now." |
| PR / pull request | Wrong-workflow vocabulary. This repo has **no pull-request workflow** — work merges to `main` via `pmtools` race-safe direct-push (or an attended, in-session `git merge` + push a human authorizes). Writing "PR" assumes a flow the project doesn't have and steers agents toward a PR-gated mental model. | Say what you mean: "the change", "the branch", "the merge", "the ticket" (whichever the sentence is about). |
