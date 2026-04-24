"""Reusable cross-project repository-shape fixtures for Task 101."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class RepoShape:
    name: str
    roots: Dict[str, str]
    governed_markdown: str
    session_dir: str
    work_tracking_root: str
    reports_root: str


REPO_SHAPES = {
    "product-web": RepoShape(
        name="product-web",
        roots={
            "templates_root": "ops/templates",
            "sessions_root": "ops/state/sessions",
            "plans_root": "ops/state/plans",
            "plan_state_dir": "ops/state/plan-sync",
            "taskmaster_root": "ops/taskmaster",
            "work_tracking_root": "ops/work-tracking",
            "reports_root": "ops/reports",
        },
        governed_markdown="ops/templates/engine/core/product-web-foundation.md",
        session_dir="ops/state/sessions",
        work_tracking_root="ops/work-tracking",
        reports_root="ops/reports",
    ),
    "game-tool": RepoShape(
        name="game-tool",
        roots={
            "templates_root": "pipeline/templates",
            "sessions_root": "pipeline/runtime/sessions",
            "plans_root": "pipeline/runtime/plans",
            "plan_state_dir": "pipeline/runtime/plan-state",
            "taskmaster_root": "pipeline/taskmaster",
            "work_tracking_root": "pipeline/work-tracking",
            "reports_root": "pipeline/reports",
        },
        governed_markdown="pipeline/templates/engine/core/game-tool-foundation.md",
        session_dir="pipeline/runtime/sessions",
        work_tracking_root="pipeline/work-tracking",
        reports_root="pipeline/reports",
    ),
    "docs-heavy": RepoShape(
        name="docs-heavy",
        roots={
            "templates_root": "docs/templates",
            "sessions_root": "docs/ops/sessions",
            "plans_root": "docs/ops/plans",
            "plan_state_dir": "docs/ops/plan-state",
            "taskmaster_root": "docs/ops/taskmaster",
            "work_tracking_root": "docs/ops/work-tracking",
            "reports_root": "docs/ops/reports",
        },
        governed_markdown="docs/templates/engine/core/docs-foundation.md",
        session_dir="docs/ops/sessions",
        work_tracking_root="docs/ops/work-tracking",
        reports_root="docs/ops/reports",
    ),
    "utility-library": RepoShape(
        name="utility-library",
        roots={
            "templates_root": "workflow/templates",
            "sessions_root": "workflow/sessions",
            "plans_root": "workflow/plans",
            "plan_state_dir": "workflow/plan-state",
            "taskmaster_root": "workflow/taskmaster",
            "work_tracking_root": "workflow/work-tracking",
            "reports_root": "workflow/reports",
        },
        governed_markdown="workflow/templates/engine/core/utility-foundation.md",
        session_dir="workflow/sessions",
        work_tracking_root="workflow/work-tracking",
        reports_root="workflow/reports",
    ),
}


def write_repo_config(repo_root: Path, shape: RepoShape) -> Path:
    config_path = repo_root / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["[repo_structure]"]
    for key, value in shape.roots.items():
        lines.append(f'{key} = "{value}"')
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def write_metadata_policy(repo_root: Path, shape: RepoShape) -> Path:
    policy_path = repo_root / shape.roots["templates_root"] / "metadata" / "template-metadata-policy.json"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    relative_dir = Path(shape.governed_markdown).parent.as_posix()
    policy_path.write_text(
        (
            "{\n"
            '  "version": "1.0.0",\n'
            '  "description": "Fixture policy",\n'
            '  "defaults": {"required_keys": ["title", "type", "status"], "frontmatter": "required"},\n'
            '  "rules": [\n'
            "    {\n"
            '      "name": "fixture-engine",\n'
            '      "enforce": true,\n'
            f'      "include": ["{relative_dir}/*.md"]\n'
            "    }\n"
            "  ],\n"
            '  "exemptions": []\n'
            "}\n"
        ),
        encoding="utf-8",
    )
    return policy_path


def write_governed_markdown(repo_root: Path, shape: RepoShape, *, with_metadata: bool) -> Path:
    markdown_path = repo_root / shape.governed_markdown
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    if with_metadata:
        content = (
            "---\n"
            "title: Fixture Doc\n"
            "type: engine-component\n"
            "status: draft\n"
            "---\n\n"
            "# Fixture\n"
        )
    else:
        content = "# Missing metadata fixture\n"
    markdown_path.write_text(content, encoding="utf-8")
    return markdown_path


def seed_workflow_state(repo_root: Path, shape: RepoShape) -> None:
    sessions_dir = repo_root / shape.session_dir
    work_tracking_root = repo_root / shape.work_tracking_root
    reports_root = repo_root / shape.reports_root

    (sessions_dir / "2026" / "04").mkdir(parents=True, exist_ok=True)
    (work_tracking_root / "active" / "20260424-task-fixture-ACTIVE").mkdir(parents=True, exist_ok=True)
    (work_tracking_root / "archive" / "20260423-task-fixture-COMPLETED").mkdir(parents=True, exist_ok=True)
    (reports_root / "template-drift").mkdir(parents=True, exist_ok=True)
    (reports_root / "template-metrics").mkdir(parents=True, exist_ok=True)
    (reports_root / "session-continuation").mkdir(parents=True, exist_ok=True)

    session_path = sessions_dir / "2026" / "04" / "2026-04-24-001-task-fixture.md"
    session_path.write_text(
        (
            "---\n"
            "session_id: 2026-04-24-001\n"
            "date: 2026-04-24\n"
            "---\n\n"
            "Task kickoff via wizard kickoff.\n"
        ),
        encoding="utf-8",
    )

    tracker_path = work_tracking_root / "active" / "20260424-task-fixture-ACTIVE" / "TRACKER.md"
    tracker_path.write_text(
        (
            "# Tracker\n\n"
            "**Status**: ACTIVE\n"
        ),
        encoding="utf-8",
    )
