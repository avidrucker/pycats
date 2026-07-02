# ADR-0001 — Record architecture decisions as ADRs

- **Status:** Accepted
- **Date:** 2026-06-29

## Context

pycats makes recurring architecture/design decisions (e.g. the consolidated
Options-screen divergence in #122, and the deferred decisions tracked under epic
#168). Their rationale has lived only in issue comments and commit messages, where
it is hard to discover later — so the *why* gets rediscovered the hard way. The
#56 architecture review recommended seeding a decision log.

## Decision

We record significant architecture/design decisions as **ADRs** (Architecture
Decision Records) under `docs/adr/`, one Markdown file per decision, using the
Nygard format in [`0000-template.md`](./0000-template.md) (Status / Context /
Decision / Consequences). Files are numbered sequentially (`NNNN-kebab-title.md`)
and never edited to reverse a decision — a reversal is a new ADR that supersedes
the old one (which is marked `Superseded by ADR-MMMM`).

## Consequences

- New decisions get a durable, discoverable home; the rationale outlives the ticket.
- This is the *mechanism only*. Past decisions are **not** back-filled — #122's
  rationale stays in its ticket. The first substantive ADRs come from epic #168's
  three deferred decisions (dual-backend endgame, input-port split, pygame.math).
- A small upkeep cost: a decision isn't "done" until its ADR is written.
