"""Unit tests for meta workflow guard registration artifacts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

ORCHESTRATOR_PATH = REPO_ROOT / "templates" / "handlers" / "orchestrators" / "meta-workflow-authoring.md"
PATTERN_PATH = REPO_ROOT / "templates" / "patterns" / "integration" / "workflow-gap-detection.md"
ORCHESTRATOR_REGISTRY_PATH = REPO_ROOT / "templates" / "registry" / "handlers" / "orchestrators-registry.md"
PATTERN_REGISTRY_PATH = REPO_ROOT / "templates" / "registry" / "patterns" / "meta-routing.md"
WORKFLOW_GUARDS_PATH = REPO_ROOT / "templates" / "metadata" / "workflow-guards.json"


def _parse_front_matter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise AssertionError(f"{path} does not start with front matter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise AssertionError(f"{path} missing closing front matter delimiter")
    front_matter = parts[1]
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in front_matter.strip().splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and ":" in raw_line:
            key, value = raw_line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if value:
                data[key] = value
                current_key = None
            else:
                data[key] = []
                current_key = key
            continue
        if raw_line.strip().startswith("-") and current_key:
            item = raw_line.strip()[1:].strip().strip('"')
            assert isinstance(data[current_key], list)
            data[current_key].append(item)
            continue
    return data


class MetaWorkflowRegistrationTests(unittest.TestCase):
    def test_orchestrator_front_matter_registration(self) -> None:
        details = _parse_front_matter(ORCHESTRATOR_PATH)
        self.assertEqual(details.get("id"), "meta-workflow-authoring", "Orchestrator id mismatch")
        self.assertEqual(details.get("role"), "orchestrator", "Orchestrator role must be 'orchestrator'")
        dependencies = details.get("dependencies")
        self.assertIsInstance(dependencies, list, "Orchestrator dependencies should be a list")
        expected = {
            "templates/workflows/processes/meta-workflow-authoring.md",
            "templates/patterns/integration/workflow-gap-detection.md",
            "templates/behaviors/planning/plan-compliance.md",
        }
        missing = expected.difference(dependencies)
        self.assertFalse(missing, f"Orchestrator missing dependencies: {sorted(missing)}")

    def test_pattern_front_matter_registration(self) -> None:
        details = _parse_front_matter(PATTERN_PATH)
        self.assertEqual(details.get("id"), "workflow-gap-detection", "Pattern id mismatch")
        self.assertEqual(details.get("type"), "pattern", "Pattern type must be 'pattern'")
        dependencies = details.get("dependencies")
        self.assertIsInstance(dependencies, list, "Pattern dependencies should be a list")
        self.assertIn(
            "templates/handlers/orchestrators/meta-workflow-authoring.md",
            dependencies,
            "Pattern should depend on meta workflow orchestrator",
        )

    def test_orchestrator_registry_entry(self) -> None:
        text = ORCHESTRATOR_REGISTRY_PATH.read_text(encoding="utf-8")
        self.assertIn("`meta-workflow-authoring`", text, "Orchestrator registry entry missing anchor")
        self.assertIn(
            "handlers/orchestrators/meta-workflow-authoring.md",
            text,
            "Orchestrator registry should reference orchestrator location",
        )

    def test_pattern_registry_entry(self) -> None:
        text = PATTERN_REGISTRY_PATH.read_text(encoding="utf-8")
        self.assertIn("`workflow-gap-detection`", text, "Pattern registry entry missing anchor")
        self.assertIn(
            "handlers/orchestrators/meta-workflow-authoring.md",
            text,
            "Pattern registry must route to meta workflow orchestrator",
        )

    def test_workflow_guard_metadata_includes_meta_workflow_files(self) -> None:
        data = json.loads(WORKFLOW_GUARDS_PATH.read_text(encoding="utf-8"))
        self.assertIsInstance(data, list, "workflow-guards.json should contain a list")
        entry = next((item for item in data if item.get("name") == "workflow-authoring"), None)
        self.assertIsNotNone(entry, "workflow-authoring entry missing in workflow-guards metadata")
        assert entry is not None  # hint for type checkers
        requires = entry.get("requires")
        self.assertIsInstance(requires, list, "workflow-authoring requires should be a list")
        expected = {
            "templates/workflows/processes/meta-workflow-authoring.md",
            "templates/handlers/orchestrators/meta-workflow-authoring.md",
            "templates/patterns/integration/workflow-gap-detection.md",
        }
        missing = expected.difference(requires)
        self.assertFalse(
            missing,
            f"workflow-authoring metadata missing required artifacts: {sorted(missing)}",
        )


if __name__ == "__main__":
    unittest.main()
