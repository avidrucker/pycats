"""#859: `scripts/run_cmd.py` resolves a worktree/branch/issue -> the mistake-proof
run block (`cd <worktree> && make run`), so nobody hand-assembles a WT=/PY= block
against `main` for code that lives on a worktree branch (errors DB rows 164, 221).

Pure resolution is unit-tested off a fixed porcelain sample; the CLI + the venv-
resolution guard run against this live worktree's real `git worktree list`.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_cmd.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_cmd", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run_cmd = _load()


SAMPLE = """worktree /home/x/pycats
HEAD aaaa
branch refs/heads/main

worktree /home/x/pycats/.claude/worktrees/wt-fig-pycats-882
HEAD bbbb
branch refs/heads/br-fig/pycats-882-dev-e0-child-of-792

worktree /home/x/pycats/.claude/worktrees/wt-elderberry-pycats-859
HEAD cccc
branch refs/heads/br-elderberry/pycats-859-dev-run-command-helper-derive
"""

WT_ELDER = "/home/x/pycats/.claude/worktrees/wt-elderberry-pycats-859"
WT_FIG = "/home/x/pycats/.claude/worktrees/wt-fig-pycats-882"


# ---- pure parse/resolve --------------------------------------------------


def test_parse_worktrees_yields_path_and_branch():
    entries = run_cmd.parse_worktrees(SAMPLE)
    assert entries[0] == {"path": "/home/x/pycats", "branch": "refs/heads/main"}
    assert {"path": WT_ELDER, "branch": "refs/heads/br-elderberry/pycats-859-dev-run-command-helper-derive"} in entries
    assert len(entries) == 3


def test_resolve_by_issue_number():
    entries = run_cmd.parse_worktrees(SAMPLE)
    assert run_cmd.resolve_worktree(entries, "859") == WT_ELDER
    assert run_cmd.resolve_worktree(entries, "882") == WT_FIG


def test_resolve_by_full_branch_name():
    entries = run_cmd.parse_worktrees(SAMPLE)
    got = run_cmd.resolve_worktree(entries, "br-elderberry/pycats-859-dev-run-command-helper-derive")
    assert got == WT_ELDER


def test_resolve_by_exact_worktree_path():
    entries = run_cmd.parse_worktrees(SAMPLE)
    assert run_cmd.resolve_worktree(entries, WT_ELDER) == WT_ELDER


def test_issue_number_does_not_partial_match_a_longer_number():
    # "85" must NOT resolve to the pycats-859 worktree (delimited match only).
    entries = run_cmd.parse_worktrees(SAMPLE)
    with pytest.raises(run_cmd.RunCmdError):
        run_cmd.resolve_worktree(entries, "85")


def test_not_found_raises_loudly_and_never_returns_main():
    entries = run_cmd.parse_worktrees(SAMPLE)
    with pytest.raises(run_cmd.RunCmdError):
        run_cmd.resolve_worktree(entries, "99999")


def test_ambiguous_query_raises():
    dup = SAMPLE + (
        "\nworktree /home/x/pycats/.claude/worktrees/wt-grape-pycats-859\n"
        "HEAD dddd\nbranch refs/heads/br-grape/pycats-859-something-else\n"
    )
    entries = run_cmd.parse_worktrees(dup)
    with pytest.raises(run_cmd.RunCmdError):
        run_cmd.resolve_worktree(entries, "859")


def test_run_block_is_copy_paste_cd_make_run():
    block = run_cmd.run_block(WT_ELDER)
    assert f"cd '{WT_ELDER}' && make run" in block


# ---- CLI end-to-end against this live worktree ---------------------------


def test_cli_resolves_this_worktree_from_its_issue_number():
    # This test file lives on the #859 worktree, so issue 859 must resolve to REPO.
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "859"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert out.returncode == 0, out.stderr
    assert f"cd '{REPO}' && make run" in out.stdout


def test_cli_unknown_issue_exits_nonzero_without_falling_back_to_main():
    main_root = (
        subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
        )
        .stdout.strip()
        .removesuffix("/.git")
    )
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "99999"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert out.returncode != 0
    assert "99999" in out.stderr
    # Must NOT print the main checkout as the run target — no fallback to main.
    assert f"cd '{main_root}' && make run" not in out.stdout


def test_emitted_make_run_uses_the_main_repo_venv():
    # Guards the GIT_COMMON resolution the emitted `cd <wt> && make run` relies on:
    # from a worktree cwd, `make run`'s interpreter must be MAIN's .venv, not a
    # (nonexistent) worktree .venv.
    import os
    import shlex

    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    ).stdout.strip()
    expected_py = os.path.normpath(str(Path(common).parent / ".venv" / "bin" / "python"))
    dry = subprocess.run(
        ["make", "-n", "run"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert dry.returncode == 0, dry.stderr
    # The Makefile emits `<main>/.git/../.venv/...` (unnormalized but correct);
    # normalize each token before comparing so `.git/..` collapses to `<main>`.
    tokens = [os.path.normpath(t) for t in shlex.split(dry.stdout) if ".venv" in t]
    assert expected_py in tokens, dry.stdout
