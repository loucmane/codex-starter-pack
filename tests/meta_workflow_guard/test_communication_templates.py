from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE_INDEX = REPO_ROOT / "templates" / "guides" / "index.md"
COMMUNICATION_GUIDE = (
    REPO_ROOT
    / "templates"
    / "guides"
    / "communication"
    / "foundation-communication-templates.md"
)
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


def test_guide_index_links_to_communication_templates() -> None:
    text = GUIDE_INDEX.read_text(encoding="utf-8")

    assert "communication/foundation-communication-templates.md" in text
    assert "Foundation communication templates" in text


def test_communication_guide_links_resolve_to_existing_files() -> None:
    missing = [
        link.relative_to(REPO_ROOT).as_posix()
        for link in _local_markdown_links(COMMUNICATION_GUIDE)
        if not link.exists()
    ]

    assert missing == []


def test_communication_guide_frontmatter_is_governed_guide() -> None:
    text = COMMUNICATION_GUIDE.read_text(encoding="utf-8")

    assert text.startswith("---\n")
    assert "id: foundation-communication-templates" in text
    assert "type: user-guide" in text
    assert "status: stable" in text
    assert "audience: maintainers" in text


def test_communication_guide_contains_required_template_sections() -> None:
    text = COMMUNICATION_GUIDE.read_text(encoding="utf-8")

    for heading in (
        "## Communication Rules",
        "## Pull Request Description",
        "## Task Completion Update",
        "## Breaking Change Notice",
        "## Incident Or Regression Notice",
        "## Milestone Announcement",
        "## Feedback And Follow-Up Capture",
        "## Evidence Checklist",
    ):
        assert heading in text


def test_communication_guide_requires_current_workflow_evidence() -> None:
    text = COMMUNICATION_GUIDE.read_text(encoding="utf-8")

    for required in (
        "Taskmaster Task",
        "Work tracking:",
        "S:W:H:E",
        "direct-git-execution",
        "python3 scripts/codex-task plan sync",
        "python3 scripts/codex-task work-tracking audit",
        "python3 scripts/codex-task taskmaster health",
        "python3 scripts/codex-guard validate --include-untracked",
        "git diff --check",
    ):
        assert required in text


def test_communication_guide_keeps_gac_explicit_only() -> None:
    text = COMMUNICATION_GUIDE.read_text(encoding="utf-8")

    assert 'user explicitly asks for "the gac"' in text
    assert "Mention `gac` only" in text
