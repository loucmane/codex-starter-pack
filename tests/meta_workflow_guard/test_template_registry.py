from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_registry import CompatibilityMap, CompatibilityMapError, TemplateNotFound, TemplateRegistry, parse_frontmatter


def _write_repo_config(repo: Path, templates_root: str = "custom_templates") -> None:
    config_dir = repo / ".codex"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[repo_structure]\n"
        f'templates_root = "{templates_root}"\n'
        'sessions_root = "sessions"\n'
        'plans_root = "plans"\n'
        'plan_state_dir = ".plan_state"\n'
        'taskmaster_root = ".taskmaster"\n'
        'work_tracking_root = "docs/ai/work-tracking"\n'
        'reports_root = "reports"\n',
        encoding="utf-8",
    )


def _write_template(path: Path, frontmatter: str, heading: str = "Example") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter.strip()}\n---\n\n# {heading}\n", encoding="utf-8")


def _write_registry(repo: Path, templates_root: str, entries: list[dict[str, object]]) -> None:
    registry_path = repo / templates_root / "registry" / "index.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def _write_compatibility_map(repo: Path, templates_root: str, mappings: list[dict[str, str]]) -> None:
    compatibility_path = repo / templates_root / "registry" / "compatibility-map.json"
    compatibility_path.parent.mkdir(parents=True, exist_ok=True)
    compatibility_path.write_text(
        json.dumps(
            {
                "schema": "template-compatibility-map.v1",
                "version": "test",
                "mappings": mappings,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_parse_frontmatter_supports_scalar_and_list_values() -> None:
    metadata = parse_frontmatter(
        """---
id: session-start
title: Session Start
type: orchestrator
tags:
  - session
  - start
enabled: true
---

# Session Start
"""
    )

    assert metadata["id"] == "session-start"
    assert metadata["title"] == "Session Start"
    assert metadata["type"] == "orchestrator"
    assert metadata["tags"] == ["session", "start"]
    assert metadata["enabled"] is True


def test_registry_discovers_portable_root_and_searches_metadata(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_template(
        tmp_path / "custom_templates" / "handlers" / "session-start.md",
        """
id: session-start
title: Session Start
type: orchestrator
status: stable
category: session
tags:
  - session
  - kickoff
""",
        "Session Start",
    )
    _write_registry(
        tmp_path,
        "custom_templates",
        [
            {
                "id": "session-start",
                "path": "custom_templates/handlers/session-start.md",
                "tags": ["session", "start"],
                "goodFirstHandler": True,
            }
        ],
    )

    registry = TemplateRegistry(repo_root=tmp_path)
    record = registry.get("session-start")

    assert record is not None
    assert record.source == "modular"
    assert record.path == "custom_templates/handlers/session-start.md"
    assert record.type == "orchestrator"
    assert record.category == "session"
    assert record.good_first_handler is True
    assert registry.search(type="orchestrator", category="session", tags=["session"]) == [record]


def test_resolve_follows_modular_compatibility_legacy_serena_error_order(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_template(
        tmp_path / "custom_templates" / "registry" / "index.md",
        """
id: registry-index
title: Registry Index
type: registry-component
status: stable
""",
        "Registry Index",
    )
    _write_template(
        tmp_path / "custom_templates" / "REGISTRY.md",
        """
id: legacy-registry
title: Legacy Registry
type: legacy
status: archived
""",
        "Legacy Registry",
    )
    _write_template(
        tmp_path / "custom_templates" / "LEGACY-ONLY.md",
        """
id: legacy-only
title: Legacy Only
type: legacy
status: archived
""",
        "Legacy Only",
    )
    _write_registry(
        tmp_path,
        "custom_templates",
        [
            {
                "id": "registry-index",
                "path": "custom_templates/registry/index.md",
                "tags": ["registry"],
                "goodFirstHandler": False,
            }
        ],
    )
    _write_compatibility_map(
        tmp_path,
        "custom_templates",
        [
            {
                "legacy": "templates/REGISTRY.md",
                "current": "templates/registry/index.md",
                "reason": "test redirect",
            }
        ],
    )

    registry = TemplateRegistry(repo_root=tmp_path)

    modular = registry.resolve("registry-index")
    assert modular.status == "found"
    assert modular.source == "modular"

    compatibility = registry.resolve("custom_templates/REGISTRY.md")
    assert compatibility.status == "redirect"
    assert compatibility.source == "compatibility"
    assert compatibility.path == "custom_templates/registry/index.md"
    assert compatibility.record is not None
    assert compatibility.record.id == "registry-index"

    legacy = registry.resolve("custom_templates/LEGACY-ONLY.md")
    assert legacy.status == "found"
    assert legacy.source == "legacy"

    serena = registry.resolve("not-local")
    assert serena.status == "fallback"
    assert serena.source == "serena"
    assert serena.fallback_action == "serena_search"

    with pytest.raises(TemplateNotFound):
        registry.resolve("not-local", allow_serena=False, strict=True)


def test_compatibility_map_supports_bidirectional_lookup_and_target_validation(tmp_path: Path) -> None:
    target = tmp_path / "templates" / "registry" / "index.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Registry\n", encoding="utf-8")

    compatibility = CompatibilityMap.from_mapping(
        {"templates/REGISTRY.md": "templates/registry/index.md"},
        version="test",
    )

    assert compatibility.version == "test"
    assert compatibility.target_for("templates/REGISTRY.md") == "templates/registry/index.md"
    assert compatibility.target_for("./templates/registry.md") == "templates/registry/index.md"
    assert compatibility.legacy_for("templates/registry/index.md") == "templates/REGISTRY.md"
    assert compatibility.validate_targets(tmp_path) == []


def test_compatibility_map_rejects_conflicting_entries() -> None:
    with pytest.raises(CompatibilityMapError, match="Duplicate legacy compatibility key"):
        CompatibilityMap.from_mapping(
            {
                "templates/REGISTRY.md": "templates/registry/index.md",
                "./templates/REGISTRY.md": "templates/registry/other.md",
            }
        )

    with pytest.raises(CompatibilityMapError, match="Duplicate current compatibility target"):
        CompatibilityMap.from_mapping(
            {
                "templates/REGISTRY.md": "templates/registry/index.md",
                "templates/REGISTRY-OLD.md": "./templates/registry/index.md",
            }
        )


def test_real_compatibility_map_targets_exist() -> None:
    registry = TemplateRegistry(repo_root=REPO_ROOT)
    issues = registry.compatibility_map.validate_targets(REPO_ROOT)
    assert issues == []


def test_registry_cache_uses_ttl_and_explicit_invalidation(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_template(
        tmp_path / "custom_templates" / "a.md",
        """
id: alpha
title: Alpha
type: guide
status: stable
""",
    )
    _write_registry(tmp_path, "custom_templates", [{"id": "alpha", "path": "custom_templates/a.md", "tags": []}])

    now = [100.0]
    registry = TemplateRegistry(repo_root=tmp_path, ttl_seconds=10.0, glob_patterns=(), clock=lambda: now[0])

    assert registry.get("alpha") is not None

    _write_template(
        tmp_path / "custom_templates" / "b.md",
        """
id: beta
title: Beta
type: guide
status: stable
""",
    )
    _write_registry(tmp_path, "custom_templates", [{"id": "beta", "path": "custom_templates/b.md", "tags": []}])

    assert registry.get("beta") is None
    now[0] = 111.0
    assert registry.get("beta") is not None

    _write_registry(tmp_path, "custom_templates", [{"id": "alpha", "path": "custom_templates/a.md", "tags": []}])
    assert registry.get("alpha") is None
    registry.invalidate_cache()
    assert registry.get("alpha") is not None


def test_real_registry_warm_lookup_and_text_read_are_cached() -> None:
    registry = TemplateRegistry(repo_root=REPO_ROOT)
    first = registry.resolve("engine-core-session-resolver")
    second = registry.resolve("engine-core-session-resolver")

    assert first.ok
    assert second.ok
    assert first.record == second.record
    assert registry.search(category="engine", tags=["core"])
    assert "Session Resolution Engine" in registry.read_text("engine-core-session-resolver")
