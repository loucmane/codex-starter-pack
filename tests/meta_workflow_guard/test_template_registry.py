from __future__ import annotations

from collections import Counter
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_registry import (
    CompatibilityMap,
    CompatibilityMapError,
    TemplateDiscoveryAPI,
    TemplateNotFound,
    TemplateRegistry,
    parse_frontmatter,
)


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


def test_registry_resolves_frontmatter_id_and_explicit_aliases_for_modular_records(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_template(
        tmp_path / "custom_templates" / "handlers" / "triggers" / "development" / "start-new-work.md",
        """
id: start-new-work
title: Start New Work
type: trigger
status: stable
category: development
""",
        "Start New Work",
    )
    _write_registry(
        tmp_path,
        "custom_templates",
        [
            {
                "id": "handlers-triggers-development-start-new-work",
                "path": "custom_templates/handlers/triggers/development/start-new-work.md",
                "aliases": ["begin-work"],
                "tags": ["handlers", "triggers", "development", "start-new-work"],
            }
        ],
    )

    registry = TemplateRegistry(repo_root=tmp_path)

    frontmatter_alias = registry.resolve("start-new-work", allow_serena=False)
    assert frontmatter_alias.status == "found"
    assert frontmatter_alias.source == "modular"
    assert frontmatter_alias.record is not None
    assert frontmatter_alias.record.id == "handlers-triggers-development-start-new-work"
    assert frontmatter_alias.path == "custom_templates/handlers/triggers/development/start-new-work.md"

    explicit_alias = registry.resolve("begin-work", allow_serena=False)
    assert explicit_alias.status == "found"
    assert explicit_alias.source == "modular"
    assert explicit_alias.record is not None
    assert explicit_alias.record.id == "handlers-triggers-development-start-new-work"


def test_registry_skips_modular_paths_during_markdown_discovery(tmp_path: Path, monkeypatch) -> None:
    _write_repo_config(tmp_path)
    modular_path = tmp_path / "custom_templates" / "guides" / "alpha.md"
    loose_path = tmp_path / "custom_templates" / "guides" / "loose.md"
    _write_template(
        modular_path,
        """
id: alpha
title: Alpha
type: guide
status: stable
category: docs
""",
        "Alpha",
    )
    _write_template(
        loose_path,
        """
id: loose
title: Loose
type: guide
status: stable
category: docs
""",
        "Loose",
    )
    _write_registry(
        tmp_path,
        "custom_templates",
        [
            {
                "id": "alpha",
                "path": "custom_templates/guides/alpha.md",
                "tags": ["docs"],
            }
        ],
    )

    calls: list[Path] = []
    original = TemplateRegistry._frontmatter_for_path

    def counted_frontmatter(self: TemplateRegistry, path: Path) -> dict[str, object]:
        calls.append(path.resolve())
        return original(self, path)

    monkeypatch.setattr(TemplateRegistry, "_frontmatter_for_path", counted_frontmatter)

    registry = TemplateRegistry(repo_root=tmp_path)
    assert {record.id for record in registry.records()} == {"alpha", "loose"}

    counts = Counter(calls)
    assert counts[modular_path.resolve()] == 1
    assert counts[loose_path.resolve()] == 1


def test_template_discovery_api_returns_serializable_lookup_search_pagination_and_dependencies(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_template(
        tmp_path / "custom_templates" / "guides" / "alpha.md",
        """
id: alpha
title: Alpha Guide
type: guide
status: stable
category: docs
version: 1.0.0
tags:
  - docs
  - onboarding
dependencies:
  - beta
""",
        "Alpha Guide",
    )
    _write_template(
        tmp_path / "custom_templates" / "guides" / "beta.md",
        """
id: beta
title: Beta Guide
type: guide
status: stable
category: docs
version: 1.0.0
tags:
  - docs
  - support
dependencies: []
""",
        "Beta Guide",
    )
    _write_template(
        tmp_path / "custom_templates" / "guides" / "gamma.md",
        """
id: gamma
title: Gamma Draft
type: guide
status: draft
category: docs
version: 0.2.0
tags:
  - docs
  - draft
dependencies: [missing-template]
""",
        "Gamma Draft",
    )
    _write_registry(
        tmp_path,
        "custom_templates",
        [
            {"id": "alpha", "path": "custom_templates/guides/alpha.md", "tags": ["docs", "onboarding"]},
            {"id": "beta", "path": "custom_templates/guides/beta.md", "tags": ["docs", "support"]},
            {"id": "gamma", "path": "custom_templates/guides/gamma.md", "tags": ["docs", "draft"]},
        ],
    )

    api = TemplateDiscoveryAPI(registry=TemplateRegistry(repo_root=tmp_path))

    alpha = api.get_template("alpha")
    assert alpha == {
        "id": "alpha",
        "path": "custom_templates/guides/alpha.md",
        "title": "Alpha Guide",
        "type": "guide",
        "category": "docs",
        "status": "stable",
        "version": "1.0.0",
        "tags": ["docs", "onboarding"],
        "dependencies": ["beta"],
        "source": "modular",
        "good_first_handler": False,
        "good_first_workflow": False,
        "metadata": {
            "id": "alpha",
            "title": "Alpha Guide",
            "type": "guide",
            "status": "stable",
            "category": "docs",
            "version": "1.0.0",
            "tags": ["docs", "onboarding"],
            "dependencies": ["beta"],
        },
    }
    assert "absolute_path" not in alpha

    first_page = api.search_templates(
        query="guide",
        category="docs",
        type="guide",
        status="stable",
        version="1.0.0",
        tags=["docs"],
        limit=1,
        offset=0,
    )
    assert [item["id"] for item in first_page["items"]] == ["alpha"]
    assert first_page["pagination"] == {
        "total": 2,
        "limit": 1,
        "offset": 0,
        "count": 1,
        "has_more": True,
    }

    second_page = api.search_templates(
        query="guide",
        category="docs",
        type="guide",
        status="stable",
        version="1.0.0",
        tags=["docs"],
        limit=1,
        offset=1,
    )
    assert [item["id"] for item in second_page["items"]] == ["beta"]
    assert second_page["pagination"]["has_more"] is False

    category = api.list_by_category("docs", status="draft")
    assert [item["id"] for item in category["items"]] == ["gamma"]

    dependencies = api.get_dependencies("alpha")
    assert dependencies == {
        "id": "alpha",
        "path": "custom_templates/guides/alpha.md",
        "dependencies": ["beta"],
        "resolved": [
            {
                "query": "beta",
                "id": "beta",
                "path": "custom_templates/guides/beta.md",
                "source": "modular",
                "status": "found",
            }
        ],
        "missing": [],
    }

    missing_dependencies = api.get_dependencies("gamma")
    assert missing_dependencies is not None
    assert missing_dependencies["missing"] == ["missing-template"]
    assert api.get_template("missing-template") is None
    assert api.get_dependencies("missing-template") is None


def test_template_discovery_api_rejects_invalid_pagination(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_registry(tmp_path, "custom_templates", [])
    api = TemplateDiscoveryAPI(registry=TemplateRegistry(repo_root=tmp_path))

    with pytest.raises(ValueError, match="limit must be greater than zero"):
        api.search_templates(limit=0)

    with pytest.raises(ValueError, match="offset must be greater than or equal to zero"):
        api.search_templates(offset=-1)


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
    assert modular.trace == ("modular_id:hit",)

    compatibility = registry.resolve("custom_templates/REGISTRY.md")
    assert compatibility.status == "redirect"
    assert compatibility.source == "compatibility"
    assert compatibility.path == "custom_templates/registry/index.md"
    assert compatibility.record is not None
    assert compatibility.record.id == "registry-index"
    assert compatibility.trace[-1] == "compatibility:hit"

    legacy = registry.resolve("custom_templates/LEGACY-ONLY.md")
    assert legacy.status == "found"
    assert legacy.source == "legacy"
    assert legacy.trace[-1] == "legacy_index:hit"

    serena = registry.resolve("not-local")
    assert serena.status == "fallback"
    assert serena.source == "serena"
    assert serena.fallback_action == "serena_search"
    assert serena.trace[-1] == "serena:fallback"

    with pytest.raises(TemplateNotFound):
        registry.resolve("not-local", allow_serena=False, strict=True)

    assert registry.discovery_metrics() == {
        "modular": 1,
        "compatibility": 1,
        "legacy": 1,
        "serena": 1,
        "error": 1,
    }


def test_registry_cache_warming_and_miss_suggestions_are_deterministic(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_template(
        tmp_path / "custom_templates" / "registry" / "index.md",
        """
id: registry-index
title: Registry Index
type: registry-component
status: stable
tags:
  - registry
  - discovery
""",
        "Registry Index",
    )
    _write_registry(
        tmp_path,
        "custom_templates",
        [
            {
                "id": "registry-index",
                "path": "custom_templates/registry/index.md",
                "tags": ["registry", "discovery"],
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
    warm = registry.warm_cache(["registry-index", "regstry-index"], allow_serena=False)

    assert warm.success_count == 1
    assert warm.failure_count == 1
    assert [entry.status for entry in warm.entries] == ["found", "error"]
    assert warm.entries[1].message == "Template not found: regstry-index. Suggestions: registry-index"

    miss = registry.resolve("custom_templates/REGISTRY-OLD.md", allow_serena=False)
    assert miss.status == "error"
    assert miss.suggestions == ("custom_templates/registry/index.md", "registry-index")
    assert "custom_templates/registry/index.md" in miss.message

    registry.reset_discovery_metrics()
    assert registry.discovery_metrics() == {
        "modular": 0,
        "compatibility": 0,
        "legacy": 0,
        "serena": 0,
        "error": 0,
    }


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


def test_real_patterns_compatibility_redirect_resolves_to_index_record() -> None:
    registry = TemplateRegistry(repo_root=REPO_ROOT)
    result = registry.resolve("templates/PATTERNS.md", allow_serena=False)

    assert result.status == "redirect"
    assert result.source == "compatibility"
    assert result.path == "templates/patterns/index.md"
    assert result.record is not None
    assert result.record.id == "patterns-index"
    assert result.record.source == "modular"


def test_real_handlers_compatibility_redirect_resolves_to_index_record() -> None:
    registry = TemplateRegistry(repo_root=REPO_ROOT)
    result = registry.resolve("templates/HANDLERS.md", allow_serena=False)

    assert result.status == "redirect"
    assert result.source == "compatibility"
    assert result.path == "templates/handlers/index.md"
    assert result.record is not None
    assert result.record.id == "handlers-index"
    assert result.record.source == "modular"


def test_real_critical_handler_queries_resolve() -> None:
    registry = TemplateRegistry(repo_root=REPO_ROOT)
    expected = {
        "start-new-work": "templates/handlers/triggers/development/start-new-work.md",
        "fix-bug": "templates/handlers/triggers/debug/fix-bug.md",
        "fix-problem": "templates/handlers/triggers/debug/fix-bug.md",
        "create-test-checkpoint": "templates/handlers/triggers/test/create-test-checkpoint.md",
        "test-implementation": "templates/handlers/triggers/test/create-test-checkpoint.md",
        "validate-changes": "templates/handlers/triggers/test/validate-changes.md",
    }

    for query, path in expected.items():
        result = registry.resolve(query, allow_serena=False)
        assert result.status == "found", query
        assert result.source == "modular", query
        assert result.path == path, query
        assert result.record is not None, query


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


def test_registry_cache_stats_track_hits_misses_rebuilds_and_invalidations(tmp_path: Path) -> None:
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

    cold = registry.cache_stats()["index"]
    assert cold == {
        "cached": False,
        "ttl_seconds": 10.0,
        "age_seconds": None,
        "ttl_remaining_seconds": None,
        "record_count": 0,
        "hits": 0,
        "misses": 0,
        "rebuilds": 0,
        "invalidations": 0,
    }

    assert registry.get("alpha") is not None
    after_cold_lookup = registry.cache_stats()["index"]
    assert after_cold_lookup["cached"] is True
    assert after_cold_lookup["record_count"] == 1
    assert after_cold_lookup["age_seconds"] == 0.0
    assert after_cold_lookup["ttl_remaining_seconds"] == 10.0
    assert after_cold_lookup["hits"] == 0
    assert after_cold_lookup["misses"] == 1
    assert after_cold_lookup["rebuilds"] == 1
    assert after_cold_lookup["invalidations"] == 0

    now[0] = 105.0
    assert registry.get("alpha") is not None
    after_warm_lookup = registry.cache_stats()["index"]
    assert after_warm_lookup["age_seconds"] == 5.0
    assert after_warm_lookup["ttl_remaining_seconds"] == 5.0
    assert after_warm_lookup["hits"] == 1
    assert after_warm_lookup["misses"] == 1
    assert after_warm_lookup["rebuilds"] == 1

    now[0] = 111.0
    assert registry.get("alpha") is not None
    after_ttl_rebuild = registry.cache_stats()["index"]
    assert after_ttl_rebuild["age_seconds"] == 0.0
    assert after_ttl_rebuild["ttl_remaining_seconds"] == 10.0
    assert after_ttl_rebuild["hits"] == 1
    assert after_ttl_rebuild["misses"] == 2
    assert after_ttl_rebuild["rebuilds"] == 2

    registry.invalidate_cache()
    after_invalidation = registry.cache_stats()["index"]
    assert after_invalidation["cached"] is False
    assert after_invalidation["record_count"] == 0
    assert after_invalidation["invalidations"] == 1

    registry.reset_cache_stats()
    after_reset = registry.cache_stats()["index"]
    assert after_reset["hits"] == 0
    assert after_reset["misses"] == 0
    assert after_reset["rebuilds"] == 0
    assert after_reset["invalidations"] == 0


def test_registry_cache_stats_include_cached_template_text_reads(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_template(
        tmp_path / "custom_templates" / "a.md",
        """
id: alpha
title: Alpha
type: guide
status: stable
""",
        "Alpha",
    )
    _write_registry(tmp_path, "custom_templates", [{"id": "alpha", "path": "custom_templates/a.md", "tags": []}])

    registry = TemplateRegistry(repo_root=tmp_path, glob_patterns=())
    registry.reset_cache_stats(clear_text_cache=True)

    assert registry.cache_stats()["read_text"]["currsize"] == 0
    first = registry.read_text("alpha")
    second = registry.read_text("alpha")

    assert first == second
    text_stats = registry.cache_stats()["read_text"]
    assert text_stats["hits"] == 1
    assert text_stats["misses"] == 1
    assert text_stats["maxsize"] == 512
    assert text_stats["currsize"] == 1

    registry.reset_cache_stats(clear_text_cache=True)
    assert registry.cache_stats()["read_text"]["hits"] == 0
    assert registry.cache_stats()["read_text"]["misses"] == 0
    assert registry.cache_stats()["read_text"]["currsize"] == 0


def test_real_registry_warm_lookup_and_text_read_are_cached() -> None:
    registry = TemplateRegistry(repo_root=REPO_ROOT)
    first = registry.resolve("engine-core-session-resolver")
    second = registry.resolve("engine-core-session-resolver")

    assert first.ok
    assert second.ok
    assert first.record == second.record
    assert registry.search(category="engine", tags=["core"])
    assert "Session Resolution Engine" in registry.read_text("engine-core-session-resolver")
