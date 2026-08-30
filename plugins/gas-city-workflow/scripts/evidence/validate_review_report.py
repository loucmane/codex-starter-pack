#!/usr/bin/env python3
"""Validate a report against its frozen run, lane schema, and output boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from validate_evidence_run import (
    EvidenceError,
    REPORT_SCHEMA,
    exact_keys,
    load_json_object,
    validate_manifest,
)


def validate_report(manifest_path: Path, lane_id: str, report_path: Path) -> dict[str, Any]:
    manifest = validate_manifest(manifest_path.resolve())
    lanes = [lane for lane in manifest["lanes"] if lane["id"] == lane_id]
    if len(lanes) != 1:
        raise EvidenceError(f"manifest does not identify lane {lane_id}")
    lane = lanes[0]
    report_path = report_path.resolve()
    report_dir = Path(lane["report_dir"]).resolve()
    try:
        relative = report_path.relative_to(report_dir).as_posix()
    except ValueError as exc:
        raise EvidenceError("report is outside the lane output directory") from exc
    if relative not in lane["allowed_outputs"]:
        raise EvidenceError(f"report is not a declared lane output: {relative}")
    report = load_json_object(report_path, "review report")
    required = {"schema", "run_id", "lane_id", "candidate_id", "status", "summary", "findings"}
    missing = required - set(report)
    if missing:
        raise EvidenceError(f"review report lacks required fields: {sorted(missing)}")
    if report.get("schema") != REPORT_SCHEMA or report.get("status") != "evidence-only":
        raise EvidenceError("review report must be gas-city-evidence-report.v1 evidence-only")
    if report.get("run_id") != manifest["run_id"] or report.get("lane_id") != lane_id:
        raise EvidenceError("review report run/lane identity mismatch")
    if report.get("candidate_id") not in manifest["candidates"]:
        raise EvidenceError("review report candidate is outside the frozen set")
    if not isinstance(report.get("summary"), str) or not isinstance(report.get("findings"), list):
        raise EvidenceError("review report summary/findings have invalid types")
    schema_assets = [
        item for item in manifest["assets"]
        if item["lane_id"] == lane_id and item["kind"] == "report_schema"
    ]
    if len(schema_assets) != 1:
        raise EvidenceError("lane report schema asset is ambiguous")
    schema = load_json_object(Path(schema_assets[0]["path"]), "lane report schema")
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.absolute_path) or "<root>"
        raise EvidenceError(f"lane report schema error at {location}: {first.message}")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate_report(args.manifest, args.lane, args.report)
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"validate-review-report: REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "run_id": report["run_id"], "lane_id": report["lane_id"], "candidate_id": report["candidate_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
