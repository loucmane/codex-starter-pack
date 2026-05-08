#!/usr/bin/env python3
"""Generate a prioritized migration roadmap from scanner outputs."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from scan_metadata import load_with_metadata, save_with_metadata

MIGRATION_ROADMAP_VERSION = "1.0.0"

PRIORITY_RANK = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

PHASES = [
    {
        "id": "phase-1-critical-integrity",
        "title": "Critical integrity",
        "priorities": ["critical"],
        "start_day": 0,
        "duration_days": 2,
    },
    {
        "id": "phase-2-foundation-correctness",
        "title": "Foundation correctness",
        "priorities": ["high"],
        "start_day": 2,
        "duration_days": 3,
    },
    {
        "id": "phase-3-maintenance-risk",
        "title": "Maintenance risk",
        "priorities": ["medium"],
        "start_day": 5,
        "duration_days": 2,
    },
    {
        "id": "phase-4-optimization-backlog",
        "title": "Optimization backlog",
        "priorities": ["low"],
        "start_day": 7,
        "duration_days": 2,
    },
]

REQUIRED_OUTPUTS = {
    "migration_status": "migration_status.json",
    "reference_analysis": "reference_analysis.json",
    "duplicate_analysis": "duplicate_analysis.json",
    "fix_recommendations": "fix_recommendations.json",
}

OPTIONAL_OUTPUTS = {
    "baseline_summary": "baseline_summary.json",
    "security_validation": "security_validation.json",
}


def _load_wrapped_output(data_dir: Path, filename: str, *, required: bool = True) -> Dict[str, Any]:
    path = data_dir / filename
    data, metadata = load_with_metadata(path)
    if data is None:
        if required:
            raise FileNotFoundError(f"Missing scanner output: {filename}")
        return {"path": str(path), "metadata": None, "data": None}
    if metadata is None:
        raise ValueError(f"{filename} must use the scanner metadata wrapper")
    return {"path": str(path), "metadata": metadata, "data": data}


def _load_outputs(data_dir: Path) -> Dict[str, Dict[str, Any]]:
    outputs: Dict[str, Dict[str, Any]] = {}
    for key, filename in REQUIRED_OUTPUTS.items():
        outputs[key] = _load_wrapped_output(data_dir, filename, required=True)
    for key, filename in OPTIONAL_OUTPUTS.items():
        outputs[key] = _load_wrapped_output(data_dir, filename, required=False)
    return outputs


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _estimate_effort(count: int) -> str:
    if count <= 1:
        return "S"
    if count <= 5:
        return "M"
    if count <= 20:
        return "L"
    return "XL"


def _risk_for(priority: str, count: int) -> str:
    if priority == "critical" or count > 20:
        return "high"
    if priority == "high" or count > 5:
        return "medium"
    return "low"


def _item(
    *,
    item_id: str,
    priority: str,
    category: str,
    title: str,
    description: str,
    source_files: Iterable[str] = (),
    count: int = 1,
    evidence: Iterable[Mapping[str, Any]] = (),
    dependencies: Iterable[str] = (),
) -> Dict[str, Any]:
    source_list = sorted({path for path in source_files if path})
    evidence_list = [dict(entry) for entry in evidence]
    effort = _estimate_effort(count)
    risk = _risk_for(priority, count)
    taskmaster_metadata = {
        "roadmap_item_id": item_id,
        "category": category,
        "source_files": source_list,
        "finding_count": count,
        "effort": effort,
        "risk": risk,
    }
    return {
        "id": item_id,
        "priority": priority,
        "category": category,
        "title": title,
        "description": description,
        "source_files": source_list,
        "finding_count": count,
        "effort": effort,
        "risk": risk,
        "dependencies": list(dependencies),
        "evidence": evidence_list[:5],
        "taskmaster": {
            "title": title,
            "description": description,
            "priority": priority,
            "details": _taskmaster_details(category, source_list, count, evidence_list),
            "testStrategy": _test_strategy(category),
            "metadata": taskmaster_metadata,
        },
    }


def _taskmaster_details(
    category: str,
    source_files: list[str],
    count: int,
    evidence: list[Mapping[str, Any]],
) -> str:
    sources = ", ".join(source_files[:5]) if source_files else "scanner output"
    if len(source_files) > 5:
        sources += f", plus {len(source_files) - 5} more"
    sample = ""
    if evidence:
        sample = f" Sample evidence: {json.dumps(evidence[0], sort_keys=True)}"
    return (
        f"Roadmap category: {category}. Finding count: {count}. "
        f"Primary source(s): {sources}.{sample}"
    )


def _test_strategy(category: str) -> str:
    strategies = {
        "references": "Rerun reference analyzer and confirm broken reference count decreases or is documented.",
        "dependencies": "Rerun reference analyzer and confirm circular dependency count decreases.",
        "migration": "Rerun migration detector and fix generator; confirm migration recommendation is resolved or updated.",
        "duplicates": "Rerun duplicate finder and confirm duplicate group no longer appears.",
        "security": "Rerun security validator and confirm finding is resolved or explicitly accepted.",
        "orphaned-files": "Rerun reference analyzer and confirm reviewed files are referenced or intentionally exempted.",
    }
    return strategies.get(category, "Rerun scanner suite and compare baseline summary.")


def _broken_reference_items(reference_data: Mapping[str, Any]) -> list[Dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for finding in _as_list(reference_data.get("broken_references")):
        if isinstance(finding, Mapping):
            grouped[str(finding.get("source_file", "unknown"))].append(finding)

    items = []
    for index, (source_file, findings) in enumerate(sorted(grouped.items()), start=1):
        count = len(findings)
        title = f"Repair {count} broken reference{'s' if count != 1 else ''} in {source_file}"
        items.append(
            _item(
                item_id=f"critical-references-{index:03d}",
                priority="critical",
                category="references",
                title=title,
                description=(
                    "Fix or explicitly document broken template references before migration "
                    "cleanup depends on them."
                ),
                source_files=[source_file],
                count=count,
                evidence=findings,
            )
        )
    return items


def _circular_dependency_items(reference_data: Mapping[str, Any]) -> list[Dict[str, Any]]:
    items = []
    for index, cycle in enumerate(_as_list(reference_data.get("circular_dependencies")), start=1):
        if not isinstance(cycle, Mapping):
            continue
        cycle_files = [str(path) for path in _as_list(cycle.get("cycle"))]
        title = f"Break circular dependency cycle {index}"
        items.append(
            _item(
                item_id=f"high-cycle-{index:03d}",
                priority="high",
                category="dependencies",
                title=title,
                description="Refactor references so template dependencies remain acyclic.",
                source_files=cycle_files,
                count=int(cycle.get("length", len(cycle_files)) or len(cycle_files) or 1),
                evidence=[cycle],
                dependencies=["critical-references"],
            )
        )
    return items


def _content_update_items(fix_data: Mapping[str, Any]) -> list[Dict[str, Any]]:
    items = []
    for index, update in enumerate(_as_list(fix_data.get("content_updates")), start=1):
        if not isinstance(update, Mapping):
            continue
        file_path = str(update.get("file", "unknown"))
        title = f"Complete migration work for {file_path}"
        items.append(
            _item(
                item_id=f"high-migration-{index:03d}",
                priority="high",
                category="migration",
                title=title,
                description=str(update.get("recommendation") or "Complete pending modular migration work."),
                source_files=[file_path],
                count=len(_as_list(update.get("unmigrated_sections"))) or 1,
                evidence=[update],
                dependencies=["critical-references"],
            )
        )
    return items


def _duplicate_items(fix_data: Mapping[str, Any]) -> list[Dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for duplicate in _as_list(fix_data.get("duplicate_removals")):
        if isinstance(duplicate, Mapping):
            grouped[str(duplicate.get("keep", "unknown"))].append(duplicate)

    items = []
    for index, (keep_file, duplicates) in enumerate(sorted(grouped.items()), start=1):
        remove_files = [str(entry.get("remove")) for entry in duplicates if entry.get("remove")]
        title = f"Review duplicate command/template files kept by {keep_file}"
        items.append(
            _item(
                item_id=f"medium-duplicates-{index:03d}",
                priority="medium",
                category="duplicates",
                title=title,
                description="Review duplicate-removal recommendations and archive only after manual confirmation.",
                source_files=[keep_file, *remove_files],
                count=len(duplicates),
                evidence=duplicates,
                dependencies=["critical-references", "high-migration"],
            )
        )
    return items


def _security_items(security_data: Mapping[str, Any] | None) -> list[Dict[str, Any]]:
    if not security_data:
        return []

    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for finding in _as_list(security_data.get("findings")):
        if isinstance(finding, Mapping):
            severity = str(finding.get("severity", "warning"))
            source_file = str(finding.get("source_file", "unknown"))
            grouped[(severity, source_file)].append(finding)

    items = []
    for index, ((severity, source_file), findings) in enumerate(sorted(grouped.items()), start=1):
        priority = "critical" if severity == "error" else "medium"
        title = f"Review {severity} security finding in {source_file}"
        items.append(
            _item(
                item_id=f"{priority}-security-{index:03d}",
                priority=priority,
                category="security",
                title=title,
                description="Review scanner security finding against current repository state.",
                source_files=[source_file],
                count=len(findings),
                evidence=findings,
            )
        )
    return items


def _orphan_review_item(reference_data: Mapping[str, Any]) -> list[Dict[str, Any]]:
    orphaned = [str(path) for path in _as_list(reference_data.get("orphaned_files"))]
    if not orphaned:
        return []

    return [
        _item(
            item_id="low-orphaned-files-001",
            priority="low",
            category="orphaned-files",
            title=f"Review {len(orphaned)} orphaned scanner files",
            description="Review orphaned files after higher-priority reference and migration work is complete.",
            source_files=orphaned[:20],
            count=len(orphaned),
            evidence=[{"sample": orphaned[:10], "total": len(orphaned)}],
            dependencies=["critical-references", "high-migration", "medium-duplicates"],
        )
    ]


def _summary_metrics(outputs: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    baseline = outputs.get("baseline_summary", {}).get("data")
    if isinstance(baseline, Mapping) and isinstance(baseline.get("metrics"), Mapping):
        return dict(baseline["metrics"])

    reference_data = outputs["reference_analysis"]["data"]
    duplicate_data = outputs["duplicate_analysis"]["data"]
    fix_metadata = outputs["fix_recommendations"].get("metadata") or {}
    migration_metadata = outputs["migration_status"].get("metadata") or {}

    reference_stats = reference_data.get("reference_stats", {}) if isinstance(reference_data, Mapping) else {}
    duplicate_stats = duplicate_data.get("statistics", {}) if isinstance(duplicate_data, Mapping) else {}
    fix_stats = fix_metadata.get("stats", {}) if isinstance(fix_metadata, Mapping) else {}
    migration_stats = migration_metadata.get("stats", {}) if isinstance(migration_metadata, Mapping) else {}

    return {
        "broken_references": reference_stats.get("broken_reference_count", 0),
        "circular_dependencies": reference_stats.get("circular_dependency_count", 0),
        "orphaned_files": reference_stats.get("orphaned_file_count", 0),
        "duplicate_count": duplicate_stats.get("files_with_duplicates", 0),
        "migration_percentage": duplicate_stats.get("overall_migration_percentage", 0),
        "total_fixes": fix_stats.get("total_fixes", 0),
        "pending_migration": migration_stats.get("pending_migration", 0),
    }


def _taskmaster_export(items: list[Dict[str, Any]]) -> Dict[str, Any]:
    tasks = []
    for item in items:
        task = dict(item["taskmaster"])
        tasks.append(task)
    return {
        "format": "taskmaster-compatible-draft",
        "note": "Review before importing. This export must not mutate Taskmaster automatically.",
        "tasks": tasks,
    }


def build_migration_roadmap(
    data_dir: Path,
    *,
    generated_at: str | None = None,
) -> Dict[str, Any]:
    """Build a prioritized migration roadmap from scanner outputs."""
    data_dir = Path(data_dir)
    outputs = _load_outputs(data_dir)
    generated_at = generated_at or datetime.now().isoformat()

    reference_data = outputs["reference_analysis"]["data"]
    duplicate_data = outputs["duplicate_analysis"]["data"]
    fix_data = outputs["fix_recommendations"]["data"]
    security_data = outputs.get("security_validation", {}).get("data")

    if not isinstance(reference_data, Mapping):
        raise ValueError("reference_analysis.json data must be a mapping")
    if not isinstance(duplicate_data, Mapping):
        raise ValueError("duplicate_analysis.json data must be a mapping")
    if not isinstance(fix_data, Mapping):
        raise ValueError("fix_recommendations.json data must be a mapping")
    if security_data is not None and not isinstance(security_data, Mapping):
        raise ValueError("security_validation.json data must be a mapping when present")

    items: list[Dict[str, Any]] = []
    items.extend(_broken_reference_items(reference_data))
    items.extend(_security_items(security_data))
    items.extend(_circular_dependency_items(reference_data))
    items.extend(_content_update_items(fix_data))
    items.extend(_duplicate_items(fix_data))
    items.extend(_orphan_review_item(reference_data))

    items.sort(key=lambda item: (PRIORITY_RANK[item["priority"]], item["category"], item["title"]))
    priority_counts = Counter(item["priority"] for item in items)
    category_counts = Counter(item["category"] for item in items)

    output_summaries = {}
    for key, output in outputs.items():
        metadata = output.get("metadata")
        if metadata:
            output_summaries[key] = {
                "path": output["path"],
                "scanner": metadata.get("scanner"),
                "scan_timestamp": metadata.get("scan_timestamp"),
                "scanner_version": metadata.get("scanner_version"),
            }

    return {
        "generated_at": generated_at,
        "migration_roadmap_version": MIGRATION_ROADMAP_VERSION,
        "data_dir": str(data_dir),
        "summary_metrics": _summary_metrics(outputs),
        "priority_counts": dict(priority_counts),
        "category_counts": dict(category_counts),
        "phases": PHASES,
        "items": items,
        "taskmaster_export": _taskmaster_export(items),
        "source_outputs": output_summaries,
    }


def render_markdown_roadmap(roadmap: Mapping[str, Any]) -> str:
    """Render roadmap data to a deterministic markdown report."""
    metrics = roadmap.get("summary_metrics", {})
    lines = [
        "# Migration Roadmap",
        "",
        f"Generated: {roadmap.get('generated_at')}",
        f"Roadmap version: {roadmap.get('migration_roadmap_version')}",
        "",
        "## Summary Metrics",
        "",
    ]

    if isinstance(metrics, Mapping) and metrics:
        for key in sorted(metrics):
            lines.append(f"- **{key}**: {metrics[key]}")
    else:
        lines.append("- No summary metrics available.")

    lines.extend(["", "## Phase Plan", ""])
    lines.append("| Phase | Priorities | Start Day | Duration |")
    lines.append("|-------|------------|-----------|----------|")
    for phase in roadmap.get("phases", []):
        if not isinstance(phase, Mapping):
            continue
        priorities = ", ".join(str(priority) for priority in phase.get("priorities", []))
        lines.append(
            f"| {phase.get('title')} | {priorities} | {phase.get('start_day')} | "
            f"{phase.get('duration_days')} days |"
        )

    lines.extend(["", "## Prioritized Items", ""])
    lines.append("| Priority | Category | Effort | Risk | Findings | Title |")
    lines.append("|----------|----------|--------|------|----------|-------|")
    for item in roadmap.get("items", []):
        if not isinstance(item, Mapping):
            continue
        lines.append(
            f"| {item['priority']} | {item['category']} | {item['effort']} | "
            f"{item['risk']} | {item['finding_count']} | {item['title']} |"
        )

    lines.extend(["", "## Taskmaster Export Guidance", ""])
    taskmaster = roadmap.get("taskmaster_export", {})
    tasks = taskmaster.get("tasks", []) if isinstance(taskmaster, Mapping) else []
    lines.append(
        f"This roadmap contains {len(tasks)} Taskmaster-compatible draft task entries. "
        "Review the JSON export before importing or creating tasks."
    )
    lines.append("")
    lines.append("The generator does not mutate Taskmaster or apply fixes.")
    lines.append("")
    return "\n".join(lines)


def write_migration_roadmap(
    data_dir: Path,
    json_out: Path,
    markdown_out: Path | None = None,
    *,
    generated_at: str | None = None,
) -> Dict[str, Any]:
    """Write JSON and optional markdown roadmap outputs."""
    start = time.perf_counter()
    roadmap = build_migration_roadmap(data_dir, generated_at=generated_at)
    duration = time.perf_counter() - start
    stats = {
        "roadmap_items": len(roadmap["items"]),
        "taskmaster_items": len(roadmap["taskmaster_export"]["tasks"]),
        **{f"priority_{key}": value for key, value in roadmap["priority_counts"].items()},
    }
    save_with_metadata(
        data=roadmap,
        output_file=json_out,
        scanner_name="migration_roadmap",
        version=MIGRATION_ROADMAP_VERSION,
        stats=stats,
        duration_seconds=duration,
    )
    if markdown_out:
        markdown_out = Path(markdown_out)
        markdown_out.parent.mkdir(parents=True, exist_ok=True)
        markdown_out.write_text(render_markdown_roadmap(roadmap), encoding="utf-8")
    return roadmap


def build_parser() -> argparse.ArgumentParser:
    scanner_dir = Path(__file__).resolve().parent
    default_data_dir = scanner_dir / "output" / "data"
    parser = argparse.ArgumentParser(
        description="Generate a prioritized migration roadmap from scanner outputs.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir,
        help="Directory containing metadata-wrapped scanner outputs.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Roadmap JSON output path (default: <data-dir>/migration_roadmap.json).",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=None,
        help="Markdown roadmap output path (default: scanner output/reports/migration_roadmap.md).",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Optional deterministic generated_at timestamp for tests/reproducibility.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_dir = Path(args.data_dir)
    json_out = args.json_out or data_dir / "migration_roadmap.json"
    markdown_out = args.markdown_out
    if markdown_out is None:
        markdown_out = Path(__file__).resolve().parent / "output" / "reports" / "migration_roadmap.md"

    roadmap = write_migration_roadmap(
        data_dir=data_dir,
        json_out=json_out,
        markdown_out=markdown_out,
        generated_at=args.generated_at,
    )
    print(f"Migration roadmap JSON saved to: {json_out}")
    print(f"Migration roadmap markdown saved to: {markdown_out}")
    print(f"Roadmap items: {len(roadmap['items'])}")
    for priority in ("critical", "high", "medium", "low"):
        count = roadmap["priority_counts"].get(priority, 0)
        print(f"  {priority}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
