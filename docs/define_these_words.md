# Define these words

Terms used in this repo's docs/tickets that need a plain, shared definition so
everyone reads them the same way. When a term here appears in writing, it carries
the meaning recorded below.

| Term | Plain meaning (in this repo's context) |
|---|---|
| stochastic | **Involves randomness.** A stochastic decision is one where the same situation can produce different actions because a random number ("dice roll") is involved. In the CPU-AI context (see `docs/research/2026-06-25-npc-behaviors-and-dual-controller.md`), "Smash CPU AI is stochastic" means its choices depend on RNG — e.g. it follows through on an action only with some *probability*, or shields "at random times". This is exactly why we can't copy it directly: pycats controllers must be **RNG-free / deterministic** (same inputs → same outputs every frame, for golden/parity safety). So here, **stochastic ≈ "uses RNG"**. The opposite is **deterministic**. |
