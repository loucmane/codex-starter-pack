#!/usr/bin/env python3
"""Tests for scanner config dependency-injection integration."""

import copy
import sys
import time
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parent

if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from analyze_references import ReferenceAnalyzer  # noqa: E402
from config.config_loader import ConfigLoader  # noqa: E402
from config.integration import (  # noqa: E402
    create_scanner_config_context,
    scanner_module_examples,
)
from scan_core import ScannerConfig, collect_scannable_files  # noqa: E402
from scan_metadata import save_with_metadata  # noqa: E402
from scanner import TemplateScanner  # noqa: E402
from validation_interface import load_validation_rules  # noqa: E402


@pytest.fixture(autouse=True)
def reset_config_loader_singletons():
    ConfigLoader.reset_instances_for_tests()
    yield
    ConfigLoader.reset_instances_for_tests()


def config_fixture(**overrides):
    config = {
        "schema_version": "1.0.0",
        "metadata": {"name": "integration-test-config"},
        "scan_scope": {
            "include": ["templates/**"],
            "exclude": ["templates/excluded/**"],
            "config_dirs": [".custom"],
            "scannable_suffixes": [".md"],
        },
        "validation_rules": {
            "broken_references": {
                "category": "references",
                "severity": "warning",
                "priority": "critical",
                "threshold": 0,
                "enabled": True,
                "auto_fix": False,
            },
            "duplicate_references": {
                "category": "references",
                "severity": "info",
                "priority": "info",
                "threshold": 0,
                "enabled": False,
                "auto_fix": False,
            },
        },
        "allowlists": {
            "paths": [
                {
                    "pattern": "templates/excluded/allowed.md",
                    "kind": "glob",
                    "rules": ["scan_scope"],
                    "reason": "explicitly included fixture",
                }
            ],
            "references": [],
        },
        "blocklists": {
            "paths": [
                {
                    "pattern": "templates/blocked/**",
                    "kind": "glob",
                    "rules": ["scan_scope"],
                    "reason": "blocked fixture",
                }
            ],
            "references": [],
        },
        "profiles": {},
        "environment_overlays": {},
    }
    config.update(overrides)
    return config


def test_context_builds_file_discovery_config_from_scan_scope_and_patterns(tmp_path):
    templates = tmp_path / "templates"
    (templates / "excluded").mkdir(parents=True)
    (templates / "blocked").mkdir(parents=True)
    (templates / "keep.md").write_text("# Keep\n", encoding="utf-8")
    (templates / "excluded" / "drop.md").write_text("# Drop\n", encoding="utf-8")
    (templates / "excluded" / "allowed.md").write_text("# Allowed\n", encoding="utf-8")
    (templates / "blocked" / "no.md").write_text("# Blocked\n", encoding="utf-8")
    (templates / "data.json").write_text("{}", encoding="utf-8")

    context = create_scanner_config_context(config_data=config_fixture())
    scanner_config = context.file_discovery_config(tmp_path)

    files = {path.relative_to(tmp_path).as_posix() for path in collect_scannable_files(templates, scanner_config)}

    assert files == {
        "templates/keep.md",
        "templates/excluded/allowed.md",
    }
    assert scanner_config.config_dirs == (".custom",)
    assert scanner_config.supported_suffixes == (".md",)


def test_collect_scannable_files_deduplicates_suffixes_and_uses_path_order(tmp_path):
    templates = tmp_path / "templates"
    (templates / "zeta").mkdir(parents=True)
    (templates / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
    (templates / "zeta" / "config.yaml").write_text("name: zeta\n", encoding="utf-8")
    (templates / "zeta" / "ignored.txt").write_text("ignore\n", encoding="utf-8")

    scanner_config = ScannerConfig(
        base_path=tmp_path,
        supported_suffixes=(".yaml", ".md", ".yaml"),
    )

    files = [path.relative_to(tmp_path).as_posix() for path in collect_scannable_files(templates, scanner_config)]

    assert files == [
        "templates/alpha.md",
        "templates/zeta/config.yaml",
    ]


def test_template_scanner_accepts_injected_context_for_config_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    (tmp_path / ".custom").mkdir()
    (tmp_path / ".codex").mkdir()
    (tmp_path / "templates" / "template.md").write_text("# Template\n", encoding="utf-8")
    (tmp_path / ".custom" / "settings.yaml").write_text("name: custom\n", encoding="utf-8")
    (tmp_path / ".codex" / "AGENTS.md").write_text("# Codex\n", encoding="utf-8")

    config = config_fixture(
        scan_scope={
            "include": ["**/*.md", "**/*.yaml"],
            "exclude": [],
            "config_dirs": [".custom"],
            "scannable_suffixes": [".md", ".yaml"],
        }
    )
    context = create_scanner_config_context(config_data=config)

    results = TemplateScanner(tmp_path, checkpoint_interval=0, config_context=context).scan()

    assert "templates/template.md" in results["files"]
    assert ".custom/settings.yaml" in results["files"]
    assert ".codex/AGENTS.md" not in results["files"]
    assert results["scan_metadata"]["config_source"] == "mapping"


def test_template_scanner_profile_mode_records_scan_timings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "first.md").write_text(
        "# First\n\nSee [Second](second.md).\n",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "second.md").write_text("# Second\n", encoding="utf-8")

    results = TemplateScanner(tmp_path, checkpoint_interval=0, profile_scan=True, profile_limit=1).scan()
    profile = results["scan_metadata"]["performance_profile"]

    assert profile["enabled"] is True
    assert profile["profile_limit"] == 1
    assert profile["directories"][0]["category"] == "templates"
    assert profile["directories"][0]["files_discovered"] == 2
    assert profile["directories"][0]["files_processed"] == 2
    assert len(profile["slowest_files"]) == 1
    assert profile["slowest_files"][0]["relative_path"] in {
        "templates/first.md",
        "templates/second.md",
    }
    assert len(profile["largest_files"]) == 1
    assert profile["total_discovery_seconds"] >= 0
    assert profile["total_processing_seconds"] >= 0


def test_reference_analyzer_uses_injected_rule_engine_effective_severity(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output" / "data"
    output_dir.mkdir(parents=True)
    scan_results = {
        "scan_metadata": {"base_path": str(tmp_path)},
        "files": {
            "templates/source.md": {
                "references": ["templates/missing.md"],
                "metadata": {},
                "line_count": 1,
            }
        },
    }
    save_with_metadata(
        data=scan_results,
        output_file=output_dir / "template_scan_results.json",
        scanner_name="template_scanner",
        version="1.1.0",
    )
    context = create_scanner_config_context(config_data=config_fixture())

    analysis = ReferenceAnalyzer(
        "output/data/template_scan_results.json",
        config_context=context,
    ).analyze()

    assert analysis["broken_references"][0]["broken_reference"] == "templates/missing.md"
    assert analysis["validation_findings"] == [
        {
            "category": "references",
            "severity": "error",
            "message": "Broken references detected",
            "details": {"count": 1, "threshold": 0},
        }
    ]


def test_scanner_module_examples_cover_scanner_suite():
    examples = scanner_module_examples()

    assert set(examples) == {
        "scanner.py",
        "analyze_references.py",
        "find_duplicates.py",
        "migration_detector.py",
        "security_validator.py",
        "generate_fixes.py",
        "safe_reorganize.py",
        "run_all_scanners.py",
    }


def test_validation_rule_loading_preserves_legacy_rule_only_configs(tmp_path):
    config_path = tmp_path / "legacy_rules.yaml"
    config_path.write_text(
        """
validation_rules:
  broken_references:
    category: references
    severity: warning
    threshold: 3
""",
        encoding="utf-8",
    )

    rules = load_validation_rules(config_path)

    assert rules["broken_references"].category == "references"
    assert rules["broken_references"].severity == "warning"
    assert rules["broken_references"].threshold == 3


def test_config_context_startup_and_access_performance_is_predictable(tmp_path):
    config = config_fixture()

    start = time.perf_counter()
    context = create_scanner_config_context(config_data=copy.deepcopy(config))
    for _ in range(1000):
        context.validation_rules()
        context.file_discovery_config(tmp_path)
    elapsed = time.perf_counter() - start

    assert context.duration_seconds < 0.25
    assert elapsed < 2.0
