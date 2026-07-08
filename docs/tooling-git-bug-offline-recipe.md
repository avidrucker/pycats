# git-bug as an offline issue mirror — findings & adoption recipe

**Ticket:** #654 (RESEARCH spike) · **Role:** RESEARCH · **Status:** findings — no install executed (dependency-gated).
**Recommendation (TL;DR):** **Adopt git-bug as a read/edit offline *mirror*, with GitHub remaining canonical.** Install it via the **dotfiles repo** (pinned release binary), configure the GitHub bridge for pycats, and pair it with a **local bare git remote** so pmtools push/claim keeps working during a GitHub egress block. Roll out across three repos, one agent each. See the caveat in Q4 — the bridge cannot sync *during* an outage; its value is the pre-imported replica plus offline editing that reconciles on reconnect.

---

## Context (why this spike exists)

Work tracking is GitHub issues (single source of truth; RULES → Work tracking). On **2026-07-06** this machine hit a **GitHub-specific egress block**: general web was up (`example.com` → 200) but *every* GitHub host — `api.github.com` **and** `githubstatus.com` — returned "no route to host." During it, local git worked (commits, worktrees, `Closes #N`); only `gh` and pmtools' push/claim-ref operations were blocked. We have **no offline replica** of the issue data, so filing/claiming/closing stalls even though git itself is fully local.

---

## What git-bug is (grounded, 2026-07)

- **Distributed, offline-first bug tracker embedded in git.** Issues, comments, labels, etc. are stored **as git objects** (in dedicated refs), not as working-tree files — so they travel with the repo and push/pull to one or more remotes like any other git data. (Upstream: `github.com/git-bug/git-bug`, README.)
- **Interfaces:** CLI (`git bug …`), a TUI, and a local web UI. Upstream recommends the TUI/web UI for daily use and the CLI for scripting.
- **Bridges** to third-party platforms — **GitHub**, GitLab, Jira, Launchpad — described upstream as *"bi-directional, incremental, and speedy."* The GitHub bridge imports existing issues and pushes local changes back.
- **Maturity:** latest release **v0.10.1** (2025-05-19); ~9.9k stars, actively maintained (14 releases, 2.6k commits). Written in Go. Suitable to depend on.

---

## Q1 — Fit with our pmtools + fleet workflow

**Fit: good as a mirror, with clear boundaries.**

- The issues-as-git-refs model is a natural fit: the replica lives *in the pycats repo's git*, needs **no server**, and reconciles through the same remotes we already push to.
- git-bug **does not** and should not replace pmtools. pmtools owns the fleet mechanics that git-bug has no concept of: **claim-refs** (`refs/claims/issue-N`), **race-safe close** (serialized push + worktree teardown), and the **velocity / error SQLite logs**. Those are orthogonal to git-bug's issue store.
- Therefore the recommended shape is a **parallel offline replica**: GitHub stays canonical; git-bug is a local read/edit cache of the issue *content* (title/body/comments/labels/state), reconciled via the bridge. pmtools continues to own claiming and closing.

## Q2 — Install channel (Linux Mint) → dotfiles repo

Upstream `INSTALLATION.md` offers: AUR (Arch), Nixpkgs (`nix profile install nixpkgs#git-bug`), FreeBSD pkg, Homebrew (`brew install git-bug`), Scoop (Windows), build-from-source (`make install`, needs Git+Go+Make), and **pre-compiled release binaries**. **There is no apt/Debian/Ubuntu package** listed — so on Mint the reproducible, lowest-friction path is:

- **Recommended: pinned release binary.** Download the `v0.10.1` (or later, pinned) Linux amd64 binary from the releases page, `chmod +x`, rename to `git-bug`, drop into `~/.local/bin` (already on PATH). **No Go toolchain required.** git auto-exposes it as the `git bug` subcommand once `git-bug` is on PATH.
- **Fallback: build-from-source** (`make install`) if a binary pin becomes unavailable — this *does* pull in a Go toolchain, which is the heavier dependency and should be its own dotfiles decision (mirrors the Rust-toolchain precedent, `linux-mint-setup#2`).

**Install home = the dotfiles repo** (`linux-mint-setup`): add a `git-bug` section to `install.sh` (idempotent, PATH-checked, version-pinned), landing the dependency-approval gate there — **not** in pycats.

## Q3 — Bridge / import procedure (pycats repo)

Grounded from upstream `doc/usage/third-party.md`:

```bash
# One-time, from within the pycats repo:
git bug bridge new          # wizard: pick GitHub → name it → repo URL → GitHub access token (PAT)

# Import GitHub issues into the local git-bug store:
git bug bridge pull [NAME]  # bi-directional, incremental — only new/changed since last sync

# After editing issues locally, push changes back to GitHub:
git bug bridge push [NAME]
```

- **Auth:** the GitHub bridge needs a **personal access token** (interactive creation or supply an existing one). This token is what the bridge uses to reach `api.github.com`.
- **Incremental:** `pull`/`push` sync only deltas, so a periodic `pull` keeps the replica warm cheaply.
- The git-bug data lands in git refs in the pycats repo; pushing those refs to our remote (or the local bare remote below) replicates the issue store alongside the code.

## Q4 — Offline runbook ("GitHub is unreachable")

**Critical caveat (load-bearing):** `git bug bridge pull/push` talks to `api.github.com`. During a GitHub egress block it is **just as blocked as `gh`.** git-bug does **not** give you live GitHub sync through an outage. What it gives you:

1. A **pre-imported local replica** you can *read and edit* offline (the whole point — import *before/periodically*, not during).
2. **Local git still works**, so coding continues in worktrees with `Closes #N` as today.

Runbook during an outage:

1. **Keep coding** in worktrees; commit with `Closes #N` in the body as usual.
2. **Keep pmtools working via a local bare remote** — `git init --bare ~/git-mirrors/pycats.git` (pure git, **no new dependency**), added as an extra remote. pmtools' push + claim-refs target the local bare remote so claiming/closing keep functioning locally; re-push to GitHub `origin` when it returns. *(This bare-remote fallback is independent of git-bug and worth having regardless.)*
3. **Track issue changes in git-bug locally** — edit titles/bodies/comments/state in the replica so nothing is lost.
4. **Reconcile on reconnect** — `git bug bridge pull` then `git bug bridge push` to sync the issue edits back to canonical GitHub; push the bare-remote commits to `origin`; let pmtools resolve claim-refs against GitHub.

**Prerequisite for this to help:** a **scheduled/periodic `git bug bridge pull`** while GitHub *is* reachable, so the replica is current when an outage hits. A stale replica is a stale mirror (retrieval-trust: the source must actually be the source).

## Q5 — Coexistence with pmtools / fleet + the interface coordination point

- **git-bug does not replace pmtools.** Split of responsibility:
  - **git-bug** — mirrors issue *content* (title/body/comments/labels/state) and reconciles it via the GitHub bridge.
  - **pmtools** — owns claim-refs, race-safe close, and velocity/error logs. These are git-bug-invisible.
- **What reconciles automatically:** issue content edited in the git-bug replica → back to GitHub via `bridge push`.
- **What does NOT reconcile automatically:** pmtools claim-refs (`refs/claims/issue-N`), close bookkeeping, and the SQLite velocity/error stores. Those stay pmtools' job and are pushed via the (local-bare-then-GitHub) git remote, not the bridge.
- **⚠ Interface coordination point (must be agreed with the pmtools owner *before* the pmtools slice is filed):** does pmtools need to become **git-bug-aware** so that, after an offline stint, the two replicas reconcile without conflict? Open questions for that handshake:
  1. Do git-bug's issue refs and pmtools' claim-refs ever collide on push (different ref namespaces — expected safe, but confirm)?
  2. Should `pmtools close`/`claim` optionally trigger a `git bug bridge pull` to keep the replica warm, or stay fully decoupled?
  3. On reconnect, what is the canonical **reconciliation order** (bridge push issue edits → pmtools resolve claim-refs → GitHub), and who documents it?
  This is **scoped here** but **built by the pmtools agent** in the pmtools tracker.

---

## Recommendation

**Adopt git-bug as an offline *mirror*, GitHub stays canonical.** It cleanly solves "I can't read/edit the issue data while GitHub is blocked" without touching pmtools' fleet mechanics. Pair it with the local-bare-remote fallback (which independently keeps pmtools push/claim alive offline) and a periodic warm-pull. Do **not** treat git-bug as the new source of truth, and do **not** auto-wire it into pmtools in this pass.

Net: two independent resilience wins — (a) git-bug = offline *issue* replica; (b) local bare remote = offline *git push/claim* — that together cover the 2026-07-06 failure mode.

---

## Rollout plan — three repos, three agents, one at a time

Filed downstream of this doc; each finishes before the next where a dependency exists.

| # | Track | Repo | Agent | Deliverable | Depends on |
|---|-------|------|-------|-------------|-----------|
| 1 | **Install** | `linux-mint-setup` (dotfiles) | dotfiles agent | Idempotent `install.sh` `git-bug` section, pinned release binary → `~/.local/bin`, PATH-checked; the **dependency-approval gate lands here**. | this doc + human approval |
| 2 | **Bridge + runbook** | pycats | pycats agent | `git bug bridge new` config for pycats; the local-bare-remote fallback; periodic warm-pull; the offline runbook wired into project docs. | Track 1 (git-bug installed) |
| 3 | **pmtools interface** | pmtools tracker | pmtools agent | Resolve the Q5 coordination handshake; any claim-ref / close / reconcile awareness pmtools needs. | Q5 agreement + Track 1 |

**Ordering:** Track 1 (install) is the root dependency. Track 2 (pycats bridge/runbook) needs the binary present. Track 3 (pmtools) needs both the binary and the Q5 interface agreement — file it **after** the cross-repo handshake is settled, not speculatively.

---

## Sources

- git-bug upstream repo — https://github.com/git-bug/git-bug
- Bridges / third-party usage — https://github.com/git-bug/git-bug/blob/master/doc/usage/third-party.md
- Installation methods — https://github.com/git-bug/git-bug/blob/master/INSTALLATION.md
- Releases (v0.10.1, 2025-05-19) — https://github.com/git-bug/git-bug/releases
- The 2026-07-06 GitHub egress incident (this machine); `linux-mint-setup#2` (Rust-toolchain dotfiles-provisioning precedent).
