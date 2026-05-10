#!/usr/bin/env python3
"""Regression tests for scanner CLI safety and default scan scope."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parent
REFERENCE_RUNNER = SCANNER_DIR / "apply_reference_fixes.py"


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


def write_reference_fixture(repo_root: Path, *, file_name: str = "templates/example.md") -> Path:
    ensure_scanner_import_path()
    from scan_metadata import save_with_metadata

    target = repo_root / file_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("See [Old](old.md) and `old.md`.\n", encoding="utf-8")

    fixes_file = repo_root / "output" / "data" / "fix_recommendations.json"
    save_with_metadata(
        data={
            "broken_references": [
                {
                    "file": file_name,
                    "old_reference": "old.md",
                    "suggested_fix": "templates/new.md",
                    "action": "update_reference",
                }
            ]
        },
        output_file=fixes_file,
        scanner_name="test_fix_generator",
        version="1.0.0",
    )
    return fixes_file


def run_reference_runner(repo_root: Path, fixes_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REFERENCE_RUNNER),
            "--repo-root",
            str(repo_root),
            "--fixes-file",
            str(fixes_file),
            *args,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=10,
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


def test_scanner_cli_reports_actual_stats_and_optional_profile(tmp_path):
    repo_root = tmp_path / "repo"
    output_file = tmp_path / "template_scan_results.json"
    (repo_root / "templates").mkdir(parents=True)
    (repo_root / "templates" / "handler.md").write_text(
        "# Handler\n\n## Trigger\n\nSee [Other](other.md).\n",
        encoding="utf-8",
    )
    (repo_root / "templates" / "other.md").write_text("# Other\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCANNER_DIR / "scanner.py"),
            "--base",
            str(repo_root),
            "--out",
            str(output_file),
            "--no-checkpoints",
            "--profile-scan",
            "--profile-limit",
            "1",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
    output = json.loads(output_file.read_text(encoding="utf-8"))
    stats = output["metadata"]["stats"]
    scan_metadata = output["data"]["scan_metadata"]

    assert stats["files_scanned"] == 2
    assert stats["total_lines"] == scan_metadata["total_lines"]
    assert stats["references_found"] == 1
    assert stats["profile_enabled"] is True
    assert scan_metadata["performance_profile"]["profile_limit"] == 1


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


def test_reference_fix_runner_defaults_to_dry_run(tmp_path):
    repo_root = tmp_path / "repo"
    fixes_file = write_reference_fixture(repo_root)
    target = repo_root / "templates" / "example.md"

    result = run_reference_runner(repo_root, fixes_file)

    assert result.returncode == 0
    assert "Reference fix mode: dry-run" in result.stdout
    assert "would-change" in result.stdout
    assert target.read_text(encoding="utf-8") == "See [Old](old.md) and `old.md`.\n"


def test_reference_fix_runner_apply_writes_backup(tmp_path):
    repo_root = tmp_path / "repo"
    fixes_file = write_reference_fixture(repo_root)
    target = repo_root / "templates" / "example.md"
    backup_dir = repo_root / "backup"

    result = run_reference_runner(repo_root, fixes_file, "--apply", "--backup-dir", str(backup_dir))

    assert result.returncode == 0
    assert "Reference fix mode: apply" in result.stdout
    assert "changed" in result.stdout
    assert target.read_text(encoding="utf-8") == "See [Old](new.md) and `templates/new.md`.\n"
    assert (backup_dir / "templates" / "example.md").read_text(encoding="utf-8") == "See [Old](old.md) and `old.md`.\n"


def test_reference_fix_runner_keeps_nested_markdown_links_relative(tmp_path):
    repo_root = tmp_path / "repo"
    fixes_file = write_reference_fixture(repo_root, file_name="templates/guides/index.md")
    target = repo_root / "templates" / "guides" / "index.md"
    (repo_root / "templates" / "new.md").parent.mkdir(parents=True, exist_ok=True)
    (repo_root / "templates" / "new.md").write_text("new\n", encoding="utf-8")

    result = run_reference_runner(repo_root, fixes_file, "--apply")

    assert result.returncode == 0
    assert target.read_text(encoding="utf-8") == "See [Old](../new.md) and `templates/new.md`.\n"


def test_reference_fix_runner_rolls_back_with_git_restore(tmp_path):
    repo_root = tmp_path / "repo"
    fixes_file = write_reference_fixture(repo_root)
    target = repo_root / "templates" / "example.md"

    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "templates/example.md"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            "commit",
            "-m",
            "test: seed fixture",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    apply_result = run_reference_runner(repo_root, fixes_file, "--apply")
    rollback_result = run_reference_runner(repo_root, fixes_file, "--rollback", "--apply")

    assert apply_result.returncode == 0
    assert rollback_result.returncode == 0
    assert "rolled-back" in rollback_result.stdout
    assert target.read_text(encoding="utf-8") == "See [Old](old.md) and `old.md`.\n"


def test_reference_fix_runner_skips_symlink_by_default(tmp_path):
    ensure_scanner_import_path()
    from scan_metadata import save_with_metadata

    repo_root = tmp_path / "repo"
    real_target = repo_root / "templates" / "real.md"
    real_target.parent.mkdir(parents=True, exist_ok=True)
    real_target.write_text("See old.md.\n", encoding="utf-8")
    symlink_target = repo_root / "templates" / "link.md"
    symlink_target.symlink_to(real_target)
    fixes_file = repo_root / "output" / "data" / "fix_recommendations.json"
    save_with_metadata(
        data={
            "broken_references": [
                {
                    "file": "templates/link.md",
                    "old_reference": "old.md",
                    "suggested_fix": "templates/new.md",
                    "action": "update_reference",
                }
            ]
        },
        output_file=fixes_file,
        scanner_name="test_fix_generator",
        version="1.0.0",
    )

    result = run_reference_runner(repo_root, fixes_file, "--apply")

    assert result.returncode == 0
    assert "skipped" in result.stdout
    assert real_target.read_text(encoding="utf-8") == "See old.md.\n"


def test_generate_fixes_emits_safe_reference_wrapper(tmp_path, monkeypatch):
    ensure_scanner_import_path()
    from generate_fixes import FixGenerator

    monkeypatch.chdir(tmp_path)
    generator = FixGenerator()
    generator.fixes = {
        "broken_references": [
            {
                "file": "templates/example.md",
                "old_reference": "old.md",
                "suggested_fix": "templates/new.md",
                "action": "update_reference",
            }
        ],
        "duplicate_removals": [],
        "file_moves": [],
        "content_updates": [],
        "recommendations": [],
        "statistics": {
            "broken_references_to_fix": 1,
            "duplicates_to_remove": 0,
            "files_to_move": 0,
        },
    }

    generator._generate_shell_scripts()

    wrapper = (tmp_path / "output" / "scripts" / "apply_reference_fixes.py").read_text(encoding="utf-8")
    apply_all = (tmp_path / "output" / "scripts" / "apply_all_fixes.sh").read_text(encoding="utf-8")

    assert "Generated wrapper for the tracked safe reference-fix runner" in wrapper
    assert "apply_reference_fixes.py" in wrapper
    assert '"template-ssot-scanner"' in wrapper
    assert "--fixes-file" in wrapper
    assert "DRY_RUN=1" in apply_all
    assert "--apply) DRY_RUN=0" in apply_all
