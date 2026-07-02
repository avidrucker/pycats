"""Guard for #169: the README "Project docs" links must resolve to real files.

A dead doc link is a real breakage — onboarding (human or agent) gets sent to a
file that doesn't exist. This is deliberately NOT a heading-presence test (that
guards nothing behavioural and churns on renames); it only fails when a linked
file is actually missing or was renamed without updating the link.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _project_docs_links():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    # The "Project docs" section: from its heading to the next heading (or EOF).
    m = re.search(r"(?ms)^#+\s*Project docs\s*$(.*?)(?=^#|\Z)", readme)
    assert m, "README has no 'Project docs' section"
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", m.group(1))


def test_project_docs_section_links_resolve():
    links = _project_docs_links()
    assert links, "'Project docs' section lists no links"
    for target in links:
        rel = target.split("#", 1)[0].rstrip("/")  # drop anchor / trailing slash
        assert (REPO / rel).exists(), f"README Project-docs link is dead: {target}"


def test_links_cover_context_and_adr():
    targets = {
        t.split("#", 1)[0].rstrip("/").removeprefix("./")
        for t in _project_docs_links()
    }
    assert "CONTEXT.md" in targets, "README must link CONTEXT.md"
    assert "docs/adr" in targets, "README must link docs/adr/"


def test_adr_scaffold_files_exist():
    assert (REPO / "docs/adr/0000-template.md").exists()
    assert (REPO / "docs/adr/0001-record-architecture-decisions.md").exists()
