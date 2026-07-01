# Banned words

Words to avoid in tickets, docs, commit messages, and agent replies for this repo.
They tend to be vague filler or unearned jargon — replace with concrete, plain wording.

These are **defaults, not hard prohibitions**: if there is no suitable alternative and
the word is genuinely the right one, use it. The goal is to curb over-use, not to forbid
the underlying concept.

| Word | Why it's banned | Prefer instead |
|---|---|---|
| crisp | Vague praise-filler ("a crisp spec", "crisp repro") — says "good" without saying what's actually good. | State the concrete property: "specific", "unambiguous", "has exact repro steps", "machine-verifiable". |
| honest / honesty / honestly | Over-used throat-clearing ("to be honest", "the honest move", "honestly, …"). Implies the rest might not be, and adds no information. | Just state the thing plainly. If you mean a specific quality, name it: "accurate", "direct", "candid", "faithful to the facts". Fine when genuinely describing honesty/candor with no fitting substitute. |
| load-bearing | Over-used metaphor ("a load-bearing guard/comment/import") — dresses up "required" without saying what actually breaks without it. | Say what depends on it concretely: "required", "the test fails without it", "removing it breaks X", "the only thing setting Y". |
| neuter | Odd, slightly-off metaphor for disabling code ("neuter the check", "neutered the fix" during a revert-check). | "disable", "stub out", "comment out", "temporarily remove". |
