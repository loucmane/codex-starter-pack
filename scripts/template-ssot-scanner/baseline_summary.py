#!/usr/bin/env python3
"""Generate an aggregate baseline summary from Template SSOT scanner outputs."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping

from scan_metadata import OUTPUT_FORMAT_VERSION, load_with_metadata, save_with_metadata

BASELINE_SUMMARY_VERSION = "1.0.0"

REQUIRED_OUTPUTS: Dict[str, str] = {
    "migration_status": "migration_status.json",
    "template_scan_results": "template_scan_results.json",
    "reference_analysis": "reference_analysis.json",
    "duplicate_analysis": "duplicate_analysis.json",
    "fix_recommendations": "fix_recommendations.json",
}


def _load_required_outputs(data_dir: Path) -> Dict[str, Dict[str, Any]]:
    outputs: Dict[str, Dict[str, Any]] = {}
    missing: list[str] = []

    for key, filename in REQUIRED_OUTPUTS.items():
        path = data_dir / filename
        if not path.exists():
            missing.append(filename)
            continue

        data, metadata = load_with_metadata(path)
        if data is None or metadata is None:
            raise ValueError(f"{filename} must use the scanner metadata wrapper")

        outputs[key] = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "metadata": metadata,
            "data": data,
        }

    if missing:
        missing_list = ", ".join(missing)
        raise FileNotFoundError(f"Missing required scanner outputs: {missing_list}")

    return outputs


def _metric(mapping: Mapping[str, Any], key: str, default: Any = 0) -> Any:
    value = mapping.get(key, default)
    return default if value is None else value


def _reference_metrics(reference_data: Mapping[str, Any]) -> Dict[str, Any]:
    stats = reference_data.get("reference_stats", {})
    if not isinstance(stats, Mapping):
        stats = {}

    total_references = _metric(stats, "total_references")
    if not total_references:
        dependency_graph = reference_data.get("dependency_graph", {})
        if isinstance(dependency_graph, Mapping):
            total_references = sum(
                len(refs) for refs in dependency_graph.values() if isinstance(refs, list)
            )

    broken_references = _metric(stats, "broken_reference_count")
    if not broken_references:
        broken = reference_data.get("broken_references", [])
        broken_references = len(broken) if isinstance(broken, list) else 0

    return {
        "total_references": total_references,
        "unique_references": _metric(stats, "unique_references"),
        "files_with_references": _metric(stats, "files_with_references"),
        "broken_references": broken_references,
        "circular_dependencies": _metric(stats, "circular_dependency_count"),
        "orphaned_files": _metric(stats, "orphaned_file_count"),
    }


def _duplicate_metrics(duplicate_data: Mapping[str, Any]) -> Dict[str, Any]:
    stats = duplicate_data.get("statistics", {})
    if not isinstance(stats, Mapping):
        stats = {}

    content_groups = duplicate_data.get("content_duplicates", [])
    partial_pairs = duplicate_data.get("partial_duplicates", [])

    return {
        "duplicate_count": _metric(stats, "files_with_duplicates"),
        "exact_duplicate_groups": _metric(
            stats,
            "exact_duplicate_groups",
            len(content_groups) if isinstance(content_groups, list) else 0,
        ),
        "partial_duplicate_pairs": _metric(
            stats,
            "partial_duplicate_pairs",
            len(partial_pairs) if isinstance(partial_pairs, list) else 0,
        ),
        "migration_percentage": _metric(stats, "overall_migration_percentage"),
        "monolithic_files": _metric(stats, "monolithic_files"),
        "modular_files": _metric(stats, "modular_files"),
    }


def _scanner_metrics(scan_data: Mapping[str, Any]) -> Dict[str, Any]:
    scan_metadata = scan_data.get("scan_metadata", {})
    if not isinstance(scan_metadata, Mapping):
        scan_metadata = {}

    return {
        "total_files": _metric(scan_metadata, "total_files"),
        "total_lines": _metric(scan_metadata, "total_lines"),
        "checkpoints_saved": _metric(scan_metadata, "checkpoints_saved"),
    }


def _fix_metrics(fix_metadata: Mapping[str, Any]) -> Dict[str, Any]:
    stats = fix_metadata.get("stats", {})
    if not isinstance(stats, Mapping):
        stats = {}

    return {
        "total_fixes": _metric(stats, "total_fixes"),
        "broken_reference_fixes": _metric(stats, "broken_references_to_fix"),
        "duplicate_removals": _metric(stats, "duplicates_to_remove"),
        "recommendations": _metric(stats, "recommendations_count"),
    }


def build_baseline_summary(
    data_dir: Path,
    *,
    generated_at: str | None = None,
) -> Dict[str, Any]:
    """Build the aggregate baseline summary data payload."""
    data_dir = Path(data_dir)
    outputs = _load_required_outputs(data_dir)
    generated_at = generated_at or datetime.now().isoformat()

    migration_metadata = outputs["migration_status"]["metadata"]
    scanner_data = outputs["template_scan_results"]["data"]
    reference_data = outputs["reference_analysis"]["data"]
    duplicate_data = outputs["duplicate_analysis"]["data"]
    fix_metadata = outputs["fix_recommendations"]["metadata"]

    metrics: Dict[str, Any] = {}
    metrics.update(_scanner_metrics(scanner_data))
    metrics.update(_reference_metrics(reference_data))
    metrics.update(_duplicate_metrics(duplicate_data))
    metrics.update(_fix_metrics(fix_metadata))
    migration_stats = migration_metadata.get("stats", {})
    if isinstance(migration_stats, Mapping):
        metrics["migration_files_scanned"] = _metric(migration_stats, "files_scanned")
        metrics["fully_migrated"] = _metric(migration_stats, "fully_migrated")
        metrics["partially_migrated"] = _metric(migration_stats, "partially_migrated")
        metrics["not_migrated"] = _metric(migration_stats, "not_migrated")
        metrics["pending_migration"] = _metric(migration_stats, "pending_migration")

    output_summaries = {}
    for key, output in outputs.items():
        metadata = output["metadata"]
        output_summaries[key] = {
            "path": output["path"],
            "size_bytes": output["size_bytes"],
            "scanner": metadata.get("scanner"),
            "scanner_version": metadata.get("scanner_version"),
            "output_format_version": metadata.get("output_format_version"),
            "scan_timestamp": metadata.get("scan_timestamp"),
        }

    return {
        "generated_at": generated_at,
        "output_format_version": OUTPUT_FORMAT_VERSION,
        "baseline_summary_version": BASELINE_SUMMARY_VERSION,
        "data_dir": str(data_dir),
        "metrics": metrics,
        "outputs": output_summaries,
    }


def write_baseline_summary(
    data_dir: Path,
    output_file: Path | None = None,
    *,
    generated_at: str | None = None,
) -> Dict[str, Any]:
    """Write a metadata-wrapped baseline summary and return its data payload."""
    data_dir = Path(data_dir)
    output_file = output_file or data_dir / "baseline_summary.json"
    summary = build_baseline_summary(data_dir, generated_at=generated_at)

    save_with_metadata(
        data=summary,
        output_file=output_file,
        scanner_name="baseline_summary",
        version=BASELINE_SUMMARY_VERSION,
        stats=summary["metrics"],
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an aggregate baseline summary from scanner outputs.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("output/data"),
        help="Directory containing metadata-wrapped scanner outputs.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output summary path (default: <data-dir>/baseline_summary.json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_file = args.out or args.data_dir / "baseline_summary.json"
    summary = write_baseline_summary(args.data_dir, output_file)
    print(f"Baseline summary saved to: {output_file}")
    print("Key metrics:")
    for key in (
        "total_files",
        "total_references",
        "broken_references",
        "duplicate_count",
        "migration_percentage",
    ):
        print(f"  {key}: {summary['metrics'].get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
