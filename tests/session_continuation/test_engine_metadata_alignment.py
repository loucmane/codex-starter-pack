from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_INDEX_PATH = REPO_ROOT / "templates" / "registry" / "index.json"
OVERVIEW_PATH = REPO_ROOT / "templates" / "metadata" / "template-overview.md"
SUMMARY_PATH = REPO_ROOT / "templates" / "metadata" / "template-summary.csv"
INVENTORY_PATH = REPO_ROOT / "templates" / "metadata" / "template-inventory.txt"


def _registry_paths() -> set[str]:
    data = json.loads(REGISTRY_INDEX_PATH.read_text(encoding="utf-8"))
    return {entry["path"] for entry in data if entry.get("path", "").startswith("templates/engine/")}


def _inventory_paths() -> set[str]:
    return {
        line.strip()
        for line in INVENTORY_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("templates/engine/")
    }


def _summary_lines() -> dict[str, str]:
    lines: dict[str, str] = {}
    for raw_line in SUMMARY_PATH.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("templates/engine/"):
            lines[raw_line.split(",", 1)[0]] = raw_line
    return lines


def test_engine_readme_metadata_uses_current_heading() -> None:
    overview = OVERVIEW_PATH.read_text(encoding="utf-8")
    summary = SUMMARY_PATH.read_text(encoding="utf-8")

    assert "`templates/engine/README.md` — heading: Codex Execution Engine" in overview
    assert "templates/engine/README.md,,,,,Codex Execution Engine,no" in summary
    assert "Claude Execution Engine - Modular Components" not in overview
    assert "Claude Execution Engine - Modular Components" not in summary


def test_engine_enforcement_docs_are_listed_in_metadata_surfaces() -> None:
    inventory = _inventory_paths()
    overview = OVERVIEW_PATH.read_text(encoding="utf-8")
    summary_lines = _summary_lines()

    expected = {
        "templates/engine/enforcement/meta-workflow-guard-ci-plan.md": (
            "title: meta-workflow-guard-ci-plan; type: enforcement-plan; "
            "heading: Meta Workflow Guard – CI & Pre-commit Wiring Plan"
        ),
        "templates/engine/enforcement/meta-workflow-guard-remediation.md": (
            "heading: Meta Workflow Guard Remediation Guidance"
        ),
    }

    for path, overview_fragment in expected.items():
        assert path in inventory, f"{path} missing from template inventory"
        assert path in summary_lines, f"{path} missing from template summary"
        assert path in overview, f"{path} missing from template overview"
        assert overview_fragment in overview, f"{path} overview metadata is stale"


def test_engine_registry_includes_operationally_referenced_docs() -> None:
    registry_paths = _registry_paths()

    expected_paths = {
        "templates/engine/core/codex-readiness.md",
        "templates/engine/enforcement/meta-workflow-guard-ci-plan.md",
        "templates/engine/enforcement/meta-workflow-guard-remediation.md",
    }

    missing = expected_paths - registry_paths
    assert not missing, f"Engine registry missing discoverability entries: {sorted(missing)}"
