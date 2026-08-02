# Banned words

Words to avoid in tickets, docs, commit messages, and agent replies for this repo.
They tend to be vague filler or unearned jargon — replace with concrete, plain wording.

These are a **hard ban, not soft defaults**: do not use them in tickets, docs, commit
messages, or agent replies unless the maintainer explicitly permits the word in that
context. Reach for the concrete alternative every time; if you believe a banned word is
genuinely the only right one, ask first rather than using it.

| Word | Why it's banned | Prefer instead |
|---|---|---|
| crisp | Vague praise-filler ("a crisp spec", "crisp repro") — says "good" without saying what's actually good. | State the concrete property: "specific", "unambiguous", "has exact repro steps", "machine-verifiable". |
| honest / honesty / honestly | Over-used throat-clearing ("to be honest", "the honest move", "honestly, …"). Implies the rest might not be, and adds no information. | Just state the thing plainly. If you mean a specific quality, name it: "accurate", "direct", "candid", "faithful to the facts". If you genuinely need it to describe honesty/candor, ask the maintainer first. |
| load-bearing | Over-used metaphor ("a load-bearing guard/comment/import") — dresses up "required" without saying what actually breaks without it. | Say what depends on it concretely: "required", "the test fails without it", "removing it breaks X", "the only thing setting Y". |
| neuter | Odd, slightly-off metaphor for disabling code ("neuter the check", "neutered the fix" during a revert-check). | "disable", "stub out", "comment out", "temporarily remove". |
| silent / silently | Hides whether something was observed ("fails silently", "silently skipped") — states an absence without saying what is or isn't seen. | Name what is or isn't observed: "with no error", "no log line is written", "the check is skipped and nothing is printed". |
