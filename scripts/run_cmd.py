#!/usr/bin/env python3
"""Emit the mistake-proof run block for an UNMERGED (worktree) change (#859).

Given a worktree path, a branch name, or an issue number, resolve the matching
git worktree and print

    cd '<worktree>' && make run

`make run` already resolves the MAIN repo's venv from a worktree cwd
(Makefile: VENV := $(GIT_COMMON)/../.venv/bin), so `cd <worktree> && make run`
is the canonical, mistake-proof form — no hand-typed WT=/PY= to get wrong. This
replaces hand-assembling the WT=/PY= block, which repeatedly pointed at `main`
and launched the pre-change build (errors DB rows 164, 221, ...).

Fails loudly (non-zero exit, message on stderr) when nothing matches — it never
falls back to the main checkout.

Usage:
    scripts/run_cmd.py <issue-number | branch-name | worktree-path>

See RULES.md -> "Surfacing run/sim commands".
"""

from __future__ import annotations

import re
import subprocess
import sys


class RunCmdError(Exception):
    """No single worktree matched the query (not found, or ambiguous)."""


def parse_worktrees(porcelain: str) -> list[dict]:
    """Parse `git worktree list --porcelain` into [{"path", "branch"}, ...].

    A worktree with no branch (detached HEAD) gets branch "" rather than a key
    that isn't there.
    """
    entries: list[dict] = []
    cur: dict = {}
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            if cur:
                entries.append(cur)
            cur = {"path": line[len("worktree ") :], "branch": ""}
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch ") :]
    if cur:
        entries.append(cur)
    return entries


def _branch_name(ref: str) -> str:
    """refs/heads/br-elderberry/pycats-859-... -> br-elderberry/pycats-859-..."""
    return ref[len("refs/heads/") :] if ref.startswith("refs/heads/") else ref


def _matches(entry: dict, query: str) -> bool:
    branch = _branch_name(entry["branch"])
    path = entry["path"]
    # Exact worktree path or exact/basename branch.
    if query == path or query == branch:
        return True
    if branch and branch.rsplit("/", 1)[-1] == query:
        return True
    # Pure-digit query = issue number: match the `pycats-<N>` token or a
    # delimited <N> in the branch or the path, so "85" never matches "859".
    if query.isdigit():
        n = re.escape(query)
        token = re.compile(rf"(?:^|[-/])(?:pycats-)?{n}(?:[-/]|$)")
        return bool(token.search(branch) or token.search(path))
    return False


def resolve_worktree(entries: list[dict], query: str) -> str:
    """Return the single worktree path matching `query`, else raise RunCmdError."""
    hits = [e for e in entries if _matches(e, query)]
    if not hits:
        raise RunCmdError(
            f"no worktree matches {query!r} — not a live worktree path, branch, "
            f"or issue number (see `git worktree list`). Refusing to fall back "
            f"to the main checkout."
        )
    if len(hits) > 1:
        paths = "\n  ".join(e["path"] for e in hits)
        raise RunCmdError(
            f"{query!r} is ambiguous — matches {len(hits)} worktrees:\n  {paths}\n"
            f"Re-run with the exact branch name or worktree path."
        )
    return hits[0]["path"]


def run_block(path: str) -> str:
    """The copy-paste run instruction for the change living at `path`."""
    return f"cd '{path}' && make run"


def _git_worktrees() -> str:
    return subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(
            "usage: run_cmd.py <issue-number | branch-name | worktree-path>",
            file=sys.stderr,
        )
        return 2
    query = argv[0]
    try:
        entries = parse_worktrees(_git_worktrees())
        path = resolve_worktree(entries, query)
    except RunCmdError as exc:
        print(f"run-cmd: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"run-cmd: git worktree list failed: {exc}", file=sys.stderr)
        return 1
    print(run_block(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
