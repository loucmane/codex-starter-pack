#!/usr/bin/env python3
"""Regression tests for scanner CLI safety and default scan scope."""

import subprocess
import sys
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parent


def ensure_scanner_import_path() -> None:
    scanner_path = str(SCANNER_DIR)
    if scanner_path not in sys.path:
        sys.path.insert(0, scanner_path)


def run_help(script_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER_DIR / script_name), "--help"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


@pytest.mark.parametrize(
    "script_name",
    [
        "scanner.py",
        "analyze_references.py",
        "find_duplicates.py",
        "run_all_scanners.py",
    ],
)
def test_help_commands_print_usage_without_executing_scanners(script_name: str):
    result = run_help(script_name)

    combined_output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "usage:" in combined_output
    assert "Traceback" not in combined_output
    assert "Template SSOT Scanner Suite - Full Analysis" not in combined_output
    assert "Running:" not in combined_output


def test_run_all_scanners_defaults_to_no_checkpoints_in_runner_help():
    result = run_help("run_all_scanners.py")

    assert "--with-checkpoints" in result.stdout
    assert "Run all scanners without checkpoints" in result.stdout


def test_scanner_excludes_codex_runtime_paths_by_default(tmp_path, monkeypatch):
    ensure_scanner_import_path()
    from scanner import TemplateScanner

    repo_root = tmp_path / "repo"
    (repo_root / "templates").mkdir(parents=True)
    (repo_root / ".codex" / "cache").mkdir(parents=True)
    (repo_root / ".codex" / "plugins" / "cache").mkdir(parents=True)
    (repo_root / ".codex" / "sessions").mkdir(parents=True)

    (repo_root / "templates" / "keeper.md").write_text("# Keeper\n", encoding="utf-8")
    (repo_root / ".codex" / "AGENTS.md").write_text("# Project Agent\n", encoding="utf-8")
    (repo_root / ".codex" / "cache" / "generated.json").write_text("{}", encoding="utf-8")
    (repo_root / ".codex" / "plugins" / "cache" / "plugin.md").write_text(
        "# Generated Plugin\n",
        encoding="utf-8",
    )
    (repo_root / ".codex" / "sessions" / "session.md").write_text(
        "# Runtime Session\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    results = TemplateScanner(repo_root, checkpoint_interval=0).scan()

    assert "templates/keeper.md" in results["files"]
    assert ".codex/AGENTS.md" in results["files"]
    assert ".codex/cache/generated.json" not in results["files"]
    assert ".codex/plugins/cache/plugin.md" not in results["files"]
    assert ".codex/sessions/session.md" not in results["files"]


def test_migration_status_consumers_unwrap_metadata_format(tmp_path, monkeypatch):
    ensure_scanner_import_path()
    from analyze_references import ReferenceAnalyzer
    from find_duplicates import DuplicateFinder
    from scan_metadata import save_with_metadata

    migration_status = {
        "templates/WORKFLOWS.md": {
            "status": "FULLY_MIGRATED",
            "markers": ["Migration Complete"],
            "link_ratio": 0.8,
            "nonempty_lines": 40,
            "modular_files": 20,
        }
    }
    output_file = tmp_path / "output" / "data" / "migration_status.json"
    save_with_metadata(
        data=migration_status,
        output_file=output_file,
        scanner_name="migration_detector",
        version="1.0.0",
    )

    monkeypatch.chdir(tmp_path)

    assert ReferenceAnalyzer()._load_migration_status() == migration_status
    assert DuplicateFinder()._load_migration_status() == migration_status


def test_validation_interface_serializes_findings():
    ensure_scanner_import_path()
    from validation_interface import (
        ValidationFinding,
        load_validation_rules,
        threshold_severity,
    )

    finding = ValidationFinding(
        category="references",
        severity=threshold_severity(3, 1),
        message="Broken references exceed threshold",
        source_file="templates/example.md",
        target_file="templates/missing.md",
        details={"count": 3, "threshold": 1},
    )

    assert finding.to_dict() == {
        "category": "references",
        "severity": "error",
        "message": "Broken references exceed threshold",
        "source_file": "templates/example.md",
        "target_file": "templates/missing.md",
        "details": {"count": 3, "threshold": 1},
    }
    assert threshold_severity(1, 1) == "info"
    assert threshold_severity(1, None) == "info"

    rules = load_validation_rules(SCANNER_DIR / "scanner_config.yaml")
    assert rules["broken_references"].severity == "error"
    assert rules["broken_references"].threshold == 0
    assert rules["circular_dependencies"].severity == "warning"
