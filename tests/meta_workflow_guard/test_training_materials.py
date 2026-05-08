from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE_INDEX = REPO_ROOT / "templates" / "guides" / "index.md"
TRAINING_GUIDE = REPO_ROOT / "templates" / "guides" / "training" / "foundation-onboarding.md"
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _local_markdown_links(path: Path) -> list[Path]:
    links: list[Path] = []
    text = path.read_text(encoding="utf-8")
    for raw_target in MARKDOWN_LINK_RE.findall(text):
        target = raw_target.strip()
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target_without_anchor = target.split("#", 1)[0]
        if not target_without_anchor:
            continue
        links.append((path.parent / target_without_anchor).resolve())
    return links


def test_guide_index_links_resolve_to_existing_files() -> None:
    missing = [
        link.relative_to(REPO_ROOT).as_posix()
        for link in _local_markdown_links(GUIDE_INDEX)
        if not link.exists()
    ]

    assert missing == []


def test_foundation_onboarding_links_resolve_to_existing_files() -> None:
    missing = [
        link.relative_to(REPO_ROOT).as_posix()
        for link in _local_markdown_links(TRAINING_GUIDE)
        if not link.exists()
    ]

    assert missing == []


def test_foundation_onboarding_contains_required_training_sections() -> None:
    text = TRAINING_GUIDE.read_text(encoding="utf-8")

    for heading in (
        "## Learning Path",
        "## Evidence And Gates",
        "## Hands-On Exercises",
        "## Completion Checklist",
        "## Feedback Notes",
    ):
        assert heading in text

    for command in (
        "python3 scripts/codex-task wizard kickoff",
        "python3 scripts/codex-task plan sync",
        "python3 scripts/codex-guard validate --include-untracked",
        "python3 scripts/codex-task work-tracking archive",
    ):
        assert command in text


def test_foundation_onboarding_frontmatter_is_training_guide() -> None:
    text = TRAINING_GUIDE.read_text(encoding="utf-8")

    assert text.startswith("---\n")
    assert "id: foundation-onboarding-training" in text
    assert "type: user-guide" in text
    assert "status: stable" in text
    assert "audience: maintainers" in text
