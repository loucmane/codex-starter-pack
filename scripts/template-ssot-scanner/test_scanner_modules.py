#!/usr/bin/env python3
"""Focused module tests for scanner-suite core behavior."""

import sys
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parent
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from analyze_references import ReferenceAnalyzer
from baseline_summary import build_baseline_summary, write_baseline_summary
from generate_fixes import FixGenerator
from migration_detector import MigrationDetector
from report_generator import save_scanner_report
from safe_reorganize import SafeReorganizer
from scan_metadata import load_with_metadata, save_with_metadata, validate_output_file


def test_migration_detector_classifies_migrated_and_unmigrated_files(tmp_path):
    templates_dir = tmp_path / "templates"
    (templates_dir / "workflows").mkdir(parents=True)
    (templates_dir / "WORKFLOWS.md").write_text(
        "# WORKFLOWS MODULARIZED\n\nMigration Complete\n\n- [Start](workflows/start.md)\n",
        encoding="utf-8",
    )
    (templates_dir / "workflows" / "start.md").write_text("# Start\n", encoding="utf-8")
    (templates_dir / "PROJECT-BLOG.md").write_text(
        "# Project Blog\n\nLong-form project notes without modular migration markers.\n",
        encoding="utf-8",
    )

    detector = MigrationDetector(tmp_path)
    statuses = detector.detect_all()

    assert statuses["templates/WORKFLOWS.md"]["status"] == "FULLY_MIGRATED"
    assert statuses["templates/WORKFLOWS.md"]["modular_files"] == 1
    assert statuses["templates/PROJECT-BLOG.md"]["status"] == "NOT_MIGRATED"


def test_reference_analyzer_emits_configured_validation_findings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output" / "data"
    output_dir.mkdir(parents=True)

    scan_results = {
        "scan_metadata": {"base_path": str(tmp_path)},
        "files": {
            "templates/source.md": {
                "references": ["templates/CONVENTIONS.md"],
                "metadata": {},
                "line_count": 1,
            },
            "templates/CONVENTIONS.md": {
                "references": [],
                "metadata": {},
                "line_count": 1,
            },
        },
    }
    save_with_metadata(
        data=scan_results,
        output_file=output_dir / "template_scan_results.json",
        scanner_name="template_scanner",
        version="1.1.0",
    )
    save_with_metadata(
        data={
            "templates/CONVENTIONS.md": {
                "status": "FULLY_MIGRATED",
                "modular_files": 22,
            }
        },
        output_file=output_dir / "migration_status.json",
        scanner_name="migration_detector",
        version="1.0.0",
    )

    analyzer = ReferenceAnalyzer(
        "output/data/template_scan_results.json",
        str(SCANNER_DIR / "scanner_config.yaml"),
    )
    analysis = analyzer.analyze()

    assert analysis["monolith_reference_after_migration"] == [
        {
            "source_file": "templates/source.md",
            "target_file": "templates/CONVENTIONS.md",
            "reference": "templates/CONVENTIONS.md",
            "migration_status": "FULLY_MIGRATED",
            "modular_files": 22,
        }
    ]
    assert {
        "category": "migration",
        "severity": "error",
        "message": "References to fully migrated monoliths detected",
        "details": {"count": 1, "threshold": 0},
    } in analysis["validation_findings"]


def test_report_generator_saves_schema_valid_metadata(tmp_path):
    output_file = tmp_path / "report.json"

    save_scanner_report(
        data={"result": "ok"},
        output_file=output_file,
        scanner_name="unit_test_scanner",
        version="1.0.0",
        stats={"items": 1},
        duration_seconds=0.01,
    )

    validate_output_file(output_file)
    data, metadata = load_with_metadata(output_file)

    assert data == {"result": "ok"}
    assert metadata["scanner"] == "unit_test_scanner"
    assert metadata["stats"] == {"items": 1}


def test_baseline_summary_aggregates_scanner_output_metrics(tmp_path):
    output_dir = tmp_path / "output" / "data"
    output_dir.mkdir(parents=True)

    save_with_metadata(
        data={"templates/WORKFLOWS.md": {"status": "FULLY_MIGRATED"}},
        output_file=output_dir / "migration_status.json",
        scanner_name="migration_detector",
        version="1.0.0",
        stats={
            "files_scanned": 4,
            "fully_migrated": 1,
            "partially_migrated": 2,
            "not_migrated": 1,
            "pending_migration": 3,
        },
    )
    save_with_metadata(
        data={
            "scan_metadata": {
                "total_files": 9,
                "total_lines": 120,
                "checkpoints_saved": 0,
            }
        },
        output_file=output_dir / "template_scan_results.json",
        scanner_name="template_scanner",
        version="1.1.0",
    )
    save_with_metadata(
        data={
            "reference_stats": {
                "total_references": 14,
                "unique_references": 10,
                "files_with_references": 5,
                "broken_reference_count": 2,
                "circular_dependency_count": 1,
                "orphaned_file_count": 3,
            },
            "broken_references": [{"source_file": "templates/a.md"}],
        },
        output_file=output_dir / "reference_analysis.json",
        scanner_name="reference_analyzer",
        version="1.1.0",
    )
    save_with_metadata(
        data={
            "content_duplicates": [{"files": ["a", "b"]}],
            "partial_duplicates": [{"files": ["c", "d"]}],
            "statistics": {
                "files_with_duplicates": 4,
                "exact_duplicate_groups": 1,
                "partial_duplicate_pairs": 1,
                "overall_migration_percentage": 62.5,
                "monolithic_files": 4,
                "modular_files": 5,
            },
        },
        output_file=output_dir / "duplicate_analysis.json",
        scanner_name="duplicate_finder",
        version="1.1.0",
    )
    save_with_metadata(
        data={"recommendations": [{"priority": "high"}]},
        output_file=output_dir / "fix_recommendations.json",
        scanner_name="fix_generator",
        version="1.1.0",
        stats={
            "total_fixes": 6,
            "broken_references_to_fix": 2,
            "duplicates_to_remove": 4,
            "recommendations_count": 1,
        },
    )

    summary = build_baseline_summary(output_dir, generated_at="2026-05-04T18:45:00")

    assert summary["generated_at"] == "2026-05-04T18:45:00"
    assert summary["output_format_version"] == "2.0.0"
    assert summary["metrics"] == {
        "total_files": 9,
        "total_lines": 120,
        "checkpoints_saved": 0,
        "total_references": 14,
        "unique_references": 10,
        "files_with_references": 5,
        "broken_references": 2,
        "circular_dependencies": 1,
        "orphaned_files": 3,
        "duplicate_count": 4,
        "exact_duplicate_groups": 1,
        "partial_duplicate_pairs": 1,
        "migration_percentage": 62.5,
        "monolithic_files": 4,
        "modular_files": 5,
        "total_fixes": 6,
        "broken_reference_fixes": 2,
        "duplicate_removals": 4,
        "recommendations": 1,
        "migration_files_scanned": 4,
        "fully_migrated": 1,
        "partially_migrated": 2,
        "not_migrated": 1,
        "pending_migration": 3,
    }
    assert summary["outputs"]["migration_status"]["scanner"] == "migration_detector"


def test_baseline_summary_writes_metadata_wrapped_output(tmp_path):
    output_dir = tmp_path / "output" / "data"
    output_dir.mkdir(parents=True)

    for filename, scanner in [
        ("migration_status.json", "migration_detector"),
        ("template_scan_results.json", "template_scanner"),
        ("reference_analysis.json", "reference_analyzer"),
        ("duplicate_analysis.json", "duplicate_finder"),
        ("fix_recommendations.json", "fix_generator"),
    ]:
        save_with_metadata(
            data={},
            output_file=output_dir / filename,
            scanner_name=scanner,
            version="1.0.0",
        )

    output_file = output_dir / "baseline_summary.json"
    write_baseline_summary(output_dir, output_file, generated_at="2026-05-04T18:45:00")
    validate_output_file(output_file)
    data, metadata = load_with_metadata(output_file)

    assert data["baseline_summary_version"] == "1.0.0"
    assert metadata["scanner"] == "baseline_summary"
    assert metadata["output_format_version"] == "2.0.0"


def test_baseline_summary_requires_all_scanner_outputs(tmp_path):
    output_dir = tmp_path / "output" / "data"
    output_dir.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="migration_status.json"):
        build_baseline_summary(output_dir)


def test_safe_reorganizer_loads_wrapped_scanner_outputs(tmp_path):
    output_dir = tmp_path / "scripts" / "template-ssot-scanner" / "output" / "data"
    output_dir.mkdir(parents=True)

    save_with_metadata(
        data={"templates/CONVENTIONS.md": {"status": "FULLY_MIGRATED"}},
        output_file=output_dir / "migration_status.json",
        scanner_name="migration_detector",
        version="1.0.0",
    )
    save_with_metadata(
        data={"files": {"templates/CONVENTIONS.md": {"references": []}}},
        output_file=output_dir / "template_scan_results.json",
        scanner_name="template_scanner",
        version="1.1.0",
    )

    reorganizer = SafeReorganizer(str(tmp_path))
    reorganizer.load_data()

    assert reorganizer.migration_status["templates/CONVENTIONS.md"]["status"] == "FULLY_MIGRATED"
    assert "templates/CONVENTIONS.md" in reorganizer.scan_results["files"]


def test_fix_generator_loads_wrapped_analysis_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output" / "data"
    output_dir.mkdir(parents=True)

    save_with_metadata(
        data={"files": {"templates/source.md": {"references": []}}},
        output_file=output_dir / "template_scan_results.json",
        scanner_name="template_scanner",
        version="1.1.0",
    )
    save_with_metadata(
        data={"broken_references": [], "monolith_reference_after_migration": []},
        output_file=output_dir / "reference_analysis.json",
        scanner_name="reference_analyzer",
        version="1.1.0",
    )
    save_with_metadata(
        data={"content_duplicates": [], "migration_status": {}},
        output_file=output_dir / "duplicate_analysis.json",
        scanner_name="duplicate_finder",
        version="1.1.0",
    )
    save_with_metadata(
        data={"templates/CONVENTIONS.md": {"status": "FULLY_MIGRATED"}},
        output_file=output_dir / "migration_status.json",
        scanner_name="migration_detector",
        version="1.0.0",
    )

    generator = FixGenerator()

    assert generator.load_analyses()
    assert generator.scan_results["files"]
    assert generator.reference_analysis["broken_references"] == []
    assert generator.duplicate_analysis["content_duplicates"] == []
    assert generator.migration_status["templates/CONVENTIONS.md"]["status"] == "FULLY_MIGRATED"
